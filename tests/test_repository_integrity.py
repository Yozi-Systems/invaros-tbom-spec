"""UTF-8, Markdown, permanent URI, and decision-lock checks."""

from __future__ import annotations

import json
import re

from validator.validate_examples import ROOT


def test_markdown_is_utf8_and_fences_are_balanced() -> None:
    markdown = sorted(ROOT.rglob("*.md"))
    assert markdown
    for path in markdown:
        text = path.read_text(encoding="utf-8")
        fences = [line for line in text.splitlines() if line.startswith("```")]
        assert len(fences) % 2 == 0, path


def test_json_is_utf8_and_has_no_duplicate_members() -> None:
    def reject_duplicates(pairs):
        result = {}
        for key, value in pairs:
            assert key not in result, f"duplicate JSON member {key!r}"
            result[key] = value
        return result

    roots = [ROOT / "schemas", ROOT / "examples", ROOT / "conformance", ROOT / "registries"]
    for root in roots:
        for path in sorted(root.rglob("*.json")):
            json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)


def test_permanent_schema_uris_match_paths() -> None:
    base = ROOT / "schemas/edge-network-topology/4.0.0"
    for path in sorted(base.glob("*.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        assert schema["$id"] == f"https://tbom.yozi.systems/schemas/edge-network-topology/4.0.0/{path.name}"


def test_no_insecure_permanent_authority() -> None:
    phase0_roots = [
        ROOT / "docs/specifications",
        ROOT / "docs/algorithms",
        ROOT / "docs/registries",
        ROOT / "schemas/edge-network-topology/4.0.0",
        ROOT / "conformance/edge-network-topology/4.0.0",
    ]
    for root in phase0_roots:
        for path in root.rglob("*"):
            if path.is_file():
                assert "http://tbom.yozi.systems/" not in path.read_text(encoding="utf-8")


def test_local_markdown_links_are_not_dangling() -> None:
    link = re.compile(r"(?<!!)\[[^]]*\]\(([^)]+)\)")
    for path in sorted(ROOT.rglob("*.md")):
        for target in link.findall(path.read_text(encoding="utf-8")):
            target = target.strip().split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            assert (path.parent / target).resolve().exists(), f"{path}: {target}"


def test_d01_through_d30_and_modified_text_are_preserved() -> None:
    plan = (ROOT / "docs/architecture/TBOM_EDGE_PROFILE4_ARCHITECTURE_PLAN.md").read_text(encoding="utf-8")
    for number in range(1, 31):
        assert f"D-{number:02d}" in plan
    assert "Runtime-discovered neighbors remain observation-only and MUST NOT participate in the structural topology or structural fingerprint." in plan
    assert "If required structural data is incomplete, conflicting, or unavailable, the producer MUST NOT emit a structural fingerprint." in plan
    assert "It MUST NOT suppress or invalidate a structural fingerprint derived from complete, valid declared intent." in plan
    assert "Structure is defined by declared intent, not by observed behavior." in plan


def test_locked_external_jcs_oracle_provenance_is_immutable() -> None:
    provenance = (ROOT / "docs/algorithms/edge-network-source-content-fingerprint.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "19d51d7fe467d4706a3ff08adf8a748f29fc21e0" in changelog
    assert "RFC 8785" in provenance
