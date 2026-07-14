"""Independent reconstruction of normative synthetic Phase 0 vectors."""

from __future__ import annotations

import base64
import hashlib
import json
import struct
from typing import Optional

import pytest
from jsonschema import ValidationError

from validator.validate_examples import ROOT, load_json
from validator.profile4_semantics import (
    interface_observation_subject_id,
    validate_disclosure_projection,
    validate_encoded_values,
    validate_source_content_fingerprints,
    validate_structural_order,
)

VECTOR_ROOT = ROOT / "conformance/edge-network-topology/4.0.0"
TYPE_CODES = {"null": 0, "utf-8": 1, "bytes": 2, "uint64": 3, "boolean": 4, "digest": 5, "array": 6, "record": 7}


def _value(type_name: str, value: object, declaration: Optional[dict] = None) -> bytes:
    if type_name == "null":
        assert value is None
        return b""
    if type_name == "utf-8":
        return str(value).encode("utf-8")
    if type_name == "bytes":
        return bytes.fromhex(declaration["value_hex"])
    if type_name == "uint64":
        return struct.pack(">Q", int(value))
    if type_name == "boolean":
        return b"\x01" if value else b"\x00"
    if type_name == "digest":
        return bytes.fromhex(str(value).removeprefix("sha256:"))
    if type_name == "record":
        fields = b"".join(_field(field) for field in value)
        return struct.pack(">H", len(value)) + fields
    if type_name == "array":
        elements = []
        for element in value:
            encoded = _value(element["type"], element.get("value"), element)
            elements.append(struct.pack(">BBI", TYPE_CODES[element["type"]], 0, len(encoded)) + encoded)
        if declaration.get("set_semantics"):
            elements.sort()
            assert len(elements) == len(set(elements))
        return struct.pack(">I", len(elements)) + b"".join(elements)
    raise AssertionError(f"unsupported test-vector type {type_name}")


def _field(field: dict) -> bytes:
    value = _value(field["type"], field.get("value"), field)
    return struct.pack(">HBBI", field["tag"], TYPE_CODES[field["type"]], 0, len(value)) + value


def _tid_record(vector: dict) -> bytes:
    encoded_fields = [_field(field) for field in vector["fields"]]
    body = struct.pack(">H", len(encoded_fields)) + b"".join(encoded_fields)
    domain = vector["domain"].encode("ascii")
    return b"YOZI-TID" + struct.pack(">HH", 1, len(domain)) + domain + struct.pack(">I", len(body)) + body


def _restricted_jcs(value: object) -> bytes:
    # Phase 0 vectors use only values for which this encoding equals RFC 8785.
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _fp_envelope(domain_text: str, payload: bytes) -> bytes:
    domain = domain_text.encode("ascii")
    return b"YOZI-FP\0" + struct.pack(">HH", 1, len(domain)) + domain + b"\x01" + struct.pack(">Q", len(payload)) + payload


def test_semantic_identity_vectors_reproduce_exact_bytes_and_digest() -> None:
    vectors = load_json(VECTOR_ROOT / "semantic-identity-vectors.json")
    for vector in vectors["vectors"]:
        record = _tid_record(vector)
        assert len(record) == vector["expected_record_length_octets"]
        assert record.hex() == vector["expected_record_hex"]
        assert "sha256:" + hashlib.sha256(record).hexdigest() == vector["expected_semantic_id"]


def test_semantic_vectors_cover_every_type_and_node_domain() -> None:
    vectors = load_json(VECTOR_ROOT / "semantic-identity-vectors.json")["vectors"]
    seen_types: set[str] = set()

    def collect(items: list[dict]) -> None:
        for item in items:
            seen_types.add(item["type"])
            if item["type"] in {"array", "record"}:
                collect(item["value"])

    for vector in vectors:
        collect(vector["fields"])
    assert seen_types == set(TYPE_CODES)
    assert {vector["domain"].rsplit("/", 1)[-1] for vector in vectors} == {
        "physical", "bridge", "vlan", "tunnel", "logical",
        "declared-federation-peer", "subject"
    }
    interface = next(vector for vector in vectors if vector["vector_id"] == "tid-observation-interface")
    assert [(field["tag"], field["type"]) for field in interface["fields"]] == [
        (1, "utf-8"), (2, "utf-8"), (3, "utf-8"),
        (4, "utf-8"), (5, "utf-8")
    ]
    tunnel = next(vector for vector in vectors if vector["vector_id"].startswith("tid-tunnel"))
    assert [field["tag"] for field in tunnel["fields"]][-3:] == [134, 135, 136]


def test_fingerprint_vectors_reproduce_bytes_envelopes_and_digests() -> None:
    vectors = load_json(VECTOR_ROOT / "fingerprint-vectors.json")
    for group in ("topology_vectors", "observation_vectors"):
        for vector in vectors[group]:
            payload = _restricted_jcs(vector["projection"])
            assert payload.decode("utf-8") == vector["canonical_utf8"]
            envelope = _fp_envelope(vector["domain"], payload)
            if "expected_envelope_hex" in vector:
                assert envelope.hex() == vector["expected_envelope_hex"]
            assert "sha256:" + hashlib.sha256(envelope).hexdigest() == vector["expected_fingerprint"]


def test_interface_observation_subject_id_matches_independent_vector() -> None:
    vector = next(
        item for item in load_json(VECTOR_ROOT / "semantic-identity-vectors.json")["vectors"]
        if item["vector_id"] == "tid-observation-interface"
    )
    interface = {
        "namespace_key": "root",
        "interface_name_observed": {"encoding": "utf-8", "value": "br-lan"},
        "interface_kind_observed": "bridge",
    }
    assert interface_observation_subject_id(interface) == vector["expected_semantic_id"]


def test_source_content_fingerprint_vectors_reproduce_exact_bytes() -> None:
    vectors = load_json(VECTOR_ROOT / "source-content-fingerprint-vectors.json")
    for vector in vectors["vectors"]:
        payload = _restricted_jcs(vector["content_projection"])
        assert payload.decode("utf-8") == vector["canonical_utf8"]
        assert "sha256:" + hashlib.sha256(payload).hexdigest() == vector["expected_fingerprint"]

    artifact = load_json(VECTOR_ROOT / "representative-examples.json")["complete_host_artifact"]
    validate_source_content_fingerprints(artifact["declared_intent"])
    bad = json.loads(json.dumps(artifact["declared_intent"]))
    bad["nodes"][0]["operator_role"] = "changed"
    with pytest.raises(ValidationError, match="does not match declared content"):
        validate_source_content_fingerprints(bad)


def test_validation_vector_inventory_and_modified_decisions() -> None:
    cases = {c["case_id"]: c for c in load_json(VECTOR_ROOT / "validation-vectors.json")["cases"]}
    assert set(cases) == {
        "null-structural-fingerprint-incomplete-intent",
        "exact-duplicates-coalesce",
        "conflicting-records-fail-closed",
        "invalid-utf8-preserved-wrapper",
        "unknown-declared-kind-fail-closed",
        "declared-federation-peer-is-structural-neighbor-is-not",
        "stable-sequential-observation",
        "unstable-sequential-observation",
    }
    assert cases["null-structural-fingerprint-incomplete-intent"]["expected"]["topology_fingerprint"]["value"] is None
    federation = cases["declared-federation-peer-is-structural-neighbor-is-not"]["expected"]
    assert federation["runtime_neighbor_in_structural_projection"] is False
    unstable = cases["unstable-sequential-observation"]["expected"]
    assert unstable["observation_fingerprint"]["value"] is None
    assert unstable["topology_fingerprint"]["availability"] == "available"


def test_duplicate_conflict_and_invalid_utf8_vector_semantics() -> None:
    cases = {c["case_id"]: c for c in load_json(VECTOR_ROOT / "validation-vectors.json")["cases"]}
    exact = cases["exact-duplicates-coalesce"]
    assert len({r["normalized_record"] for r in exact["input_records"]}) == 1
    conflict = cases["conflicting-records-fail-closed"]
    assert len({r["normalized_record"] for r in conflict["input_records"]}) == 2
    invalid = cases["invalid-utf8-preserved-wrapper"]
    encoded = invalid["normalized"]["value"]
    decoded = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
    assert decoded.hex() == invalid["input_bytes_hex"] == invalid["expected"]["decoded_bytes_hex"]


def test_encoded_value_vectors_reproduce_bytes_and_outcomes() -> None:
    cases = load_json(VECTOR_ROOT / "encoded-value-vectors.json")["cases"]
    for case in cases:
        encoded = case.get("encoded")
        if encoded is None:
            assert bytes.fromhex(case["input_bytes_hex"]).decode("utf-8", errors="ignore") == ""
            continue
        if case["valid"]:
            validate_encoded_values(encoded, tuple(case.get("path", ())))
        else:
            with pytest.raises(ValidationError):
                validate_encoded_values(encoded, tuple(case.get("path", ())))
        if encoded["encoding"] == "utf-8":
            raw = encoded["value"].encode("utf-8")
        else:
            raw = base64.urlsafe_b64decode(encoded["value"] + "=" * (-len(encoded["value"]) % 4))
        assert raw.hex() == case["input_bytes_hex"]


def test_every_disclosure_profile_vector_has_expected_outcome() -> None:
    cases = load_json(VECTOR_ROOT / "disclosure-profile-vectors.json")["cases"]
    assert len({case["observation"]["disclosure_profile_id"] for case in cases}) == 4
    for case in cases:
        if case["valid"]:
            validate_disclosure_projection(case["observation"])
            validate_encoded_values(case["observation"])
        else:
            with pytest.raises(ValidationError):
                validate_disclosure_projection(case["observation"])


def test_set_ordering_duplicate_and_multi_node_vectors() -> None:
    cases = {case["case_id"]: case for case in load_json(VECTOR_ROOT / "canonicalization-vectors.json")["cases"]}
    parents = cases["parent-set-sort"]
    assert sorted(parents["input"], key=lambda item: bytes.fromhex(item[7:])) == parents["expected"]
    duplicate_parents = cases["parent-set-duplicate-rejected"]["input"]
    assert len(duplicate_parents) != len(set(duplicate_parents))
    duplicate_parameters = cases["parameter-duplicate-rejected"]["input"]
    parameter_bytes = [_restricted_jcs(item) for item in duplicate_parameters]
    assert len(parameter_bytes) != len(set(parameter_bytes))
    multi = cases["multi-node-and-relation-order"]
    assert sorted(multi["input_node_ids"]) == multi["expected_node_ids"]
    assert multi["input_relations"] and multi["input_relations"][0]["parameters"]

    projection = load_json(VECTOR_ROOT / "fingerprint-vectors.json")["topology_vectors"][1]["projection"]
    validate_structural_order(projection)
    reversed_projection = json.loads(json.dumps(projection))
    reversed_projection["nodes"].reverse()
    with pytest.raises(ValidationError, match="canonical semantic-ID order"):
        validate_structural_order(reversed_projection)


def test_duplicate_parameter_identifier_is_rejected_semantically() -> None:
    projection = load_json(VECTOR_ROOT / "fingerprint-vectors.json")["topology_vectors"][1]["projection"]
    duplicate = json.loads(json.dumps(projection))
    parameters = duplicate["relations"][0]["parameters"]
    parameters.append({"parameter_id": parameters[0]["parameter_id"], "value": False})
    with pytest.raises(ValidationError, match="duplicate parameter_id"):
        validate_structural_order(duplicate)


def test_tunnel_identity_parameter_kind_mismatch_is_rejected() -> None:
    fragments = load_json(VECTOR_ROOT / "representative-examples.json")["representative_fragments"]
    projection = {"nodes": [json.loads(json.dumps(fragments["tunnel"]))], "relations": []}
    projection["nodes"][0]["parameters"] = [{
        "parameter_id": "https://tbom.yozi.systems/registries/edge-network/tunnel-parameters/1/vxlan-vni",
        "value": 10,
    }]
    with pytest.raises(ValidationError, match="does not match interface kind"):
        validate_structural_order(projection)
