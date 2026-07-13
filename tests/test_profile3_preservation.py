"""Freeze exact Profile 3 assets and reproduce legacy fingerprints."""

from __future__ import annotations

import hashlib
import json

from validator.validate_examples import ROOT, load_json

EXPECTED_FILE_HASHES = {
    "schemas/edge-network/invaros-edge-network-topology-tbom-profile.schema.json": "c281c680dbc3879805cae7137581bd2380fd8dfa818a5acd05c0b02c2a532c61",
    "examples/edge-network/bridge-members.json": "096ca9a344206e344ce56dfd81db48af3c3189c907a011b5c69b5fbc34d9a1f8",
    "examples/edge-network/loopback-only.json": "eeafdf8bc66704002ce71bd11bd2cfed51856e534a631c603c98f835ce5aa2c3",
    "examples/edge-network/physical-vlan.json": "934af78bb72cd8227e08deecae11b704bfb444e55a5ad8d20097bbb02eae3b12",
}


def _compact_sorted(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("ascii")


def test_profile3_files_are_byte_frozen() -> None:
    for relative, expected in EXPECTED_FILE_HASHES.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected


def test_profile3_topology_and_host_fingerprints_reproduce() -> None:
    for path in sorted((ROOT / "examples/edge-network").glob("*.json")):
        artifact = load_json(path)
        assert hashlib.sha256(_compact_sorted(artifact["graph"])).hexdigest() == artifact["topology_fingerprint"]
        physical_ids = sorted(
            node["id"] for node in artifact["graph"]["nodes"] if node["type"] == "node_physical"
        )
        assert hashlib.sha256("".join(physical_ids).encode("ascii")).hexdigest() == artifact["subsystem_identity"]["host_fingerprint"]
