#!/usr/bin/env python3
"""Regenerate the multi-node Profile 4 byte-level fingerprint vector."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VECTOR = ROOT / "conformance/edge-network-topology/4.0.0/fingerprint-vectors.json"
EXAMPLES = ROOT / "conformance/edge-network-topology/4.0.0/representative-examples.json"
DOMAIN = "https://tbom.yozi.systems/domain/edge-network-topology/4.0.0/fingerprint/topology"


def main() -> None:
    document = json.loads(VECTOR.read_text(encoding="utf-8"))
    fragments = json.loads(EXAMPLES.read_text(encoding="utf-8"))["representative_fragments"]
    nodes = sorted([fragments["physical_interface"], fragments["logical"]], key=lambda item: item["semantic_id"])
    projection = {
        "nodes": nodes,
        "projection_id": "https://tbom.yozi.systems/projections/edge-network-topology/4.0.0/structural",
        "relations": [fragments["relation"]],
    }
    payload = json.dumps(projection, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    domain = DOMAIN.encode("ascii")
    envelope = b"YOZI-FP\0" + struct.pack(">HH", 1, len(domain)) + domain + b"\x01" + struct.pack(">Q", len(payload)) + payload
    generated = {
        "algorithm": "https://tbom.yozi.systems/algorithms/edge-network-topology/4.0.0/topology-fingerprint-yozi-fp-v1-jcs-sha256",
        "canonical_utf8": payload.decode("utf-8"),
        "domain": DOMAIN,
        "expected_envelope_hex": envelope.hex(),
        "expected_fingerprint": "sha256:" + hashlib.sha256(envelope).hexdigest(),
        "projection": projection,
        "vector_id": "topology-multi-node-relation-parameters-002",
    }
    document["topology_vectors"] = [item for item in document["topology_vectors"] if item["vector_id"] != generated["vector_id"]] + [generated]
    VECTOR.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
