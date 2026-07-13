"""Profile dispatch, and rejection of missing/unknown profile_id and invalid artifacts."""

from __future__ import annotations

import json

import jsonschema
import pytest

from validator.validate_examples import (
    ROOT,
    PROFILE_SCHEMAS,
    load_json,
    profile_key,
    validate_example,
)

AGENTIC_EXAMPLE = next((ROOT / "examples" / "agentic").glob("*.json"))


def _write(tmp_path, name: str, payload: dict):
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_known_profile_ids_are_dispatched() -> None:
    assert set(PROFILE_SCHEMAS) == {
        ("invaros.tbom.profile.agentic_topology", "3.0.0"),
        ("invaros.tbom.profile.edge_network_topology", "3.0.0"),
        ("invaros.tbom.profile.edge_network_topology", "4.0.0"),
    }
    for (profile_id, profile_version), schema_path in PROFILE_SCHEMAS.items():
        schema = load_json(schema_path)
        assert schema.get("properties", {}).get("profile_id", {}).get("const") == profile_id
        expected = schema.get("properties", {}).get("profile_version", {}).get("const")
        if expected is not None:
            assert expected == profile_version


def test_correct_profile_dispatch(tmp_path) -> None:
    agentic_payload = load_json(AGENTIC_EXAMPLE)
    path = _write(tmp_path, "agentic.json", agentic_payload)
    # Must not raise: dispatches to the agentic schema via profile_id.
    validate_example(path)


def test_missing_profile_id_fails(tmp_path) -> None:
    payload = load_json(AGENTIC_EXAMPLE)
    payload.pop("profile_id", None)
    path = _write(tmp_path, "no-profile-id.json", payload)

    with pytest.raises(ValueError, match="unsupported or missing profile_id"):
        validate_example(path)


def test_unknown_profile_id_fails(tmp_path) -> None:
    payload = load_json(AGENTIC_EXAMPLE)
    payload["profile_id"] = "invaros.tbom.profile.does_not_exist"
    path = _write(tmp_path, "unknown-profile-id.json", payload)

    with pytest.raises(ValueError, match="unsupported or missing profile_id"):
        validate_example(path)


def test_unknown_profile_version_fails(tmp_path) -> None:
    payload = load_json(AGENTIC_EXAMPLE)
    payload["profile_version"] = "99.0.0"
    path = _write(tmp_path, "unknown-profile-version.json", payload)

    with pytest.raises(ValueError, match="unsupported profile_id/profile_version"):
        validate_example(path)


def test_legacy_missing_version_uses_profile3() -> None:
    payload = load_json(AGENTIC_EXAMPLE)
    payload.pop("profile_version")
    assert profile_key(payload) == (
        "invaros.tbom.profile.agentic_topology",
        "3.0.0",
    )


def test_invalid_artifact_fails_schema_validation(tmp_path) -> None:
    payload = load_json(AGENTIC_EXAMPLE)
    # Break the artifact structurally while keeping profile_id intact so it
    # dispatches to the agentic schema and fails schema validation, not
    # profile lookup.
    del payload["tbom_id"]
    path = _write(tmp_path, "invalid.json", payload)

    with pytest.raises(jsonschema.exceptions.ValidationError):
        validate_example(path)
