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
OBSERVATION_DOMAIN = "https://tbom.yozi.systems/domain/edge-network-topology/4.0.0/fingerprint/observation"


def fingerprint_vector(vector_id: str, algorithm: str, domain_text: str, projection: dict) -> dict:
    payload = json.dumps(projection, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    domain = domain_text.encode("ascii")
    envelope = b"YOZI-FP\0" + struct.pack(">HH", 1, len(domain)) + domain + b"\x01" + struct.pack(">Q", len(payload)) + payload
    return {
        "algorithm": algorithm,
        "canonical_utf8": payload.decode("utf-8"),
        "domain": domain_text,
        "expected_envelope_hex": envelope.hex(),
        "expected_fingerprint": "sha256:" + hashlib.sha256(envelope).hexdigest(),
        "projection": projection,
        "vector_id": vector_id,
    }


def main() -> None:
    document = json.loads(VECTOR.read_text(encoding="utf-8"))
    fragments = json.loads(EXAMPLES.read_text(encoding="utf-8"))["representative_fragments"]
    nodes = sorted([fragments["physical_interface"], fragments["logical"]], key=lambda item: item["semantic_id"])
    projection = {
        "nodes": nodes,
        "projection_id": "https://tbom.yozi.systems/projections/edge-network-topology/4.0.0/structural",
        "relations": [fragments["relation"]],
    }
    generated = fingerprint_vector(
        "topology-multi-node-relation-parameters-002",
        "https://tbom.yozi.systems/algorithms/edge-network-topology/4.0.0/topology-fingerprint-yozi-fp-v1-jcs-sha256",
        DOMAIN, projection,
    )
    document["topology_vectors"] = [item for item in document["topology_vectors"] if item["vector_id"] != generated["vector_id"]] + [generated]
    observation = {
        "collection_consistency": "generation_validated_sequential",
        "conformance": [],
        "datasets": [{"attempts": 1, "dataset": "links", "namespace_key": "root", "reason_codes": [], "records_emitted": 1, "records_seen": 1, "status": "complete"}],
        "disclosure_profile_id": "https://tbom.yozi.systems/registries/edge-network/disclosure-profiles/1/structural-conformance",
        "interfaces": [{
            "declared_semantic_id": None, "interface_kind_observed": "bridge",
            "interface_name_observed": {"encoding": "utf-8", "value": "br-lan"},
            "kind_state": fragments["bridge_observation_kind_state"], "link_status": "up",
            "master_observed": None, "namespace_key": "root",
            "observation_subject_id": "sha256:c0d12711141e1fa61a4fcbe19a5025c7b467af1d8f056750a232fd9161a26e84",
            "parent_observed": None,
        }],
        "neighbors": [], "projection_id": "https://tbom.yozi.systems/projections/edge-network-topology/4.0.0/observation",
        "routes": [], "structural_topology_fingerprint": None,
    }
    observation_vector = fingerprint_vector(
        "observation-bridge-kind-state-002",
        "https://tbom.yozi.systems/algorithms/edge-network-topology/4.0.0/observation-fingerprint-yozi-fp-v1-jcs-sha256",
        OBSERVATION_DOMAIN, observation,
    )
    document["observation_vectors"] = [item for item in document["observation_vectors"] if item["vector_id"] != observation_vector["vector_id"]] + [observation_vector]
    bootstrap = {
        "collection_consistency": "generation_validated_sequential",
        "conformance": [],
        "datasets": [{"attempts": 1, "dataset": "links", "namespace_key": "root", "reason_codes": [], "records_emitted": 0, "records_seen": 0, "status": "complete"}],
        "disclosure_profile_id": "https://tbom.yozi.systems/registries/edge-network/disclosure-profiles/1/structural-conformance",
        "interfaces": [], "neighbors": [],
        "projection_id": "https://tbom.yozi.systems/projections/edge-network-topology/4.0.0/observation",
        "routes": [], "structural_topology_fingerprint": None,
    }
    bootstrap_vector = fingerprint_vector(
        "observation-bootstrap-no-intent-003",
        "https://tbom.yozi.systems/algorithms/edge-network-topology/4.0.0/observation-fingerprint-yozi-fp-v1-jcs-sha256",
        OBSERVATION_DOMAIN, bootstrap,
    )
    document["observation_vectors"] = [item for item in document["observation_vectors"] if item["vector_id"] != bootstrap_vector["vector_id"]] + [bootstrap_vector]
    VECTOR.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
