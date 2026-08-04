"""Criteria manifest gate for the custodian copy of the Profile 4 criteria.

Qualification Evidence WP-00.1, test V7 — custodian side.

This repository is the criteria custodian: the Profile 4 conformance vectors are
authored here and mirrored into `invaros-runtime`. `MANIFEST.sha256` is what
makes those mirrors checkable, so it has to be verified where the criteria are
*authored* and not only where they are consumed. A manifest that only the
consumer checks silently stops describing the source the moment the source
changes.

The manifest deliberately covers `*.json` only. `README.md` is repository prose,
differs legitimately between the custodian and its mirrors, and is not criteria.
"""

from __future__ import annotations

import hashlib

from validator.validate_examples import ROOT

CRITERIA = ROOT / "conformance/edge-network-topology/4.0.0"
MANIFEST = CRITERIA / "MANIFEST.sha256"


def _manifest_entries() -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        digest, _, name = line.partition("  ")
        assert len(digest) == 64 and name, f"malformed manifest line: {line!r}"
        assert name not in entries, f"duplicate manifest entry: {name}"
        entries[name] = digest
    return entries


def test_manifest_lists_every_criteria_file() -> None:
    """An uncovered criteria file is the defect the Runtime mirror actually had.

    Its former manifest omitted `observation-order-vectors.json` entirely, so a
    check against it would have passed while leaving the file — the one carrying
    the specification §8 ordering prohibition — completely unguarded.
    """
    on_disk = {path.name for path in CRITERIA.glob("*.json")}
    listed = set(_manifest_entries())
    assert on_disk, "no criteria files found"
    assert on_disk == listed, (
        f"manifest does not match the criteria tree: "
        f"unlisted={sorted(on_disk - listed)}, missing={sorted(listed - on_disk)}")


def test_manifest_digests_match() -> None:
    for name, expected in sorted(_manifest_entries().items()):
        path = CRITERIA / name
        assert path.is_file(), f"criteria file listed in the manifest is missing: {path}"
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == expected, (
            f"criteria digest mismatch\n"
            f"  path    : {path}\n"
            f"  expected: {expected}\n"
            f"  actual  : {actual}")
