"""tbom-validate CLI exit codes and PASS/FAIL/ERROR reporting."""

from __future__ import annotations

import json

import pytest
from referencing.exceptions import Unresolvable

from validator.cli import main
from validator.validate_examples import ROOT, load_json

AGENTIC_EXAMPLE = next((ROOT / "examples" / "agentic").glob("*.json"))
EDGE_EXAMPLE = next((ROOT / "examples" / "edge-network").glob("*.json"))


def _write(tmp_path, name: str, payload: dict):
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_cli_exits_zero_for_valid_files(capsys) -> None:
    exit_code = main([str(AGENTIC_EXAMPLE), str(EDGE_EXAMPLE)])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert f"PASS {AGENTIC_EXAMPLE}" in out
    assert f"PASS {EDGE_EXAMPLE}" in out


def test_cli_exits_zero_for_profile4_complete_artifact(tmp_path, capsys) -> None:
    vectors = load_json(
        ROOT / "conformance/edge-network-topology/4.0.0/representative-examples.json"
    )
    path = _write(tmp_path, "edge4.json", vectors["complete_host_artifact"])
    assert main([str(path)]) == 0
    assert f"PASS {path}" in capsys.readouterr().out


def test_cli_exits_nonzero_for_missing_file(tmp_path, capsys) -> None:
    missing = tmp_path / "does-not-exist.json"
    exit_code = main([str(missing)])
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "file not found" in err


def test_cli_exits_nonzero_for_invalid_json(tmp_path, capsys) -> None:
    path = tmp_path / "not-json.json"
    path.write_text("{not valid json", encoding="utf-8")
    exit_code = main([str(path)])
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "invalid JSON" in err


def test_cli_exits_nonzero_for_unknown_profile_id(tmp_path, capsys) -> None:
    payload = load_json(AGENTIC_EXAMPLE)
    payload["profile_id"] = "invaros.tbom.profile.does_not_exist"
    path = _write(tmp_path, "unknown-profile.json", payload)

    exit_code = main([str(path)])
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "unsupported or missing profile_id" in err


def test_cli_exits_nonzero_for_schema_invalid_artifact(tmp_path, capsys) -> None:
    payload = load_json(AGENTIC_EXAMPLE)
    del payload["tbom_id"]
    path = _write(tmp_path, "invalid.json", payload)

    exit_code = main([str(path)])
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "schema validation error" in err


def test_cli_mixed_results_exit_nonzero(tmp_path, capsys) -> None:
    payload = load_json(AGENTIC_EXAMPLE)
    payload["profile_id"] = "invaros.tbom.profile.does_not_exist"
    bad_path = _write(tmp_path, "bad.json", payload)

    exit_code = main([str(AGENTIC_EXAMPLE), str(bad_path)])
    assert exit_code == 1
    out = capsys.readouterr().out
    assert f"PASS {AGENTIC_EXAMPLE}" in out


def test_cli_requires_at_least_one_file() -> None:
    with pytest.raises(SystemExit):
        main([])


def test_cli_reports_schema_resolution_failure_cleanly(monkeypatch, capsys) -> None:
    def fail(_payload):
        raise Unresolvable(ref="https://missing.invalid/schema.json")

    monkeypatch.setattr("validator.cli.validate_payload", fail)
    assert main([str(AGENTIC_EXAMPLE)]) == 1
    err = capsys.readouterr().err
    assert "schema resolution error" in err
    assert "Traceback" not in err
