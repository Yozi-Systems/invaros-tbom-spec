"""Regression coverage for the first-live Profile 4 ordering defect."""

from __future__ import annotations

import copy
import pytest
import jsonschema
from jsonschema import ValidationError

from validator.profile4_semantics import (
    _projection_fingerprint,
    validate_observation_order,
    validate_profile4_semantics,
)
from validator.validate_examples import (
    PROFILE_SCHEMAS, ROOT, load_json, profile_key, schema_registry,
)


def _projection() -> dict:
    digest = lambda value: "sha256:" + value * 64
    dataset = lambda name: {"attempts": 1, "dataset": name, "namespace_key": "root", "reason_codes": [], "records_emitted": 2, "records_seen": 2, "status": "complete"}
    interface = lambda declared, subject, addresses: {"addresses": addresses, "carrier": True, "current_link_address": None, "declared_semantic_id": declared, "interface_kind_observed": None, "interface_name_observed": {"encoding": "utf-8", "value": subject}, "kind_state": None, "link_status": "up", "master_observed": None, "mtu": 1500, "namespace_key": "root", "observation_subject_id": digest(subject), "parent_observed": None}
    address = lambda raw: {"address": {"encoding": "base64url", "value": raw}, "family": 4, "flags": [], "peer_address": None, "prefix_length": 24, "scope": "0"}
    return {
        "collection_consistency": "generation_validated_sequential",
        "conformance": [
            {"declared_semantic_id": digest("1"), "observation_subject_id": digest("a"), "reason_codes": [], "status": "conformant"},
            {"declared_semantic_id": None, "observation_subject_id": digest("b"), "reason_codes": [], "status": "not-declared"},
        ],
        "datasets": [dataset("addresses"), dataset("links"), dataset("neighbors"), dataset("routes")],
        "disclosure_profile_id": "https://tbom.yozi.systems/registries/edge-network/disclosure-profiles/1/internal-full",
        "interfaces": [
            interface(digest("1"), "a", [address("AQ"), address("Ag")]),
            interface(None, "b", []),
        ],
        "neighbors": [
            {"address": {"encoding": "base64url", "value": "AQ"}, "family": 4, "interface_semantic_id": digest("1"), "interface_subject_id": digest("a"), "link_address": None, "namespace_key": "root", "observation_subject_id": digest("c"), "state": "1"},
            {"address": {"encoding": "base64url", "value": "Ag"}, "family": 4, "interface_semantic_id": None, "interface_subject_id": digest("b"), "link_address": None, "namespace_key": "root", "observation_subject_id": digest("d"), "state": "2"},
        ],
        "projection_id": "https://tbom.yozi.systems/projections/edge-network-topology/4.0.0/observation",
        "routes": [
            {"destination": {"encoding": "base64url", "value": "AQ"}, "family": 4, "gateway": None, "metric": 1, "output_interface_semantic_id": digest("1"), "output_interface_subject_id": digest("a"), "prefix_length": 24, "protocol": "1", "route_type": "1", "scope": "0", "table": 100},
            {"destination": {"encoding": "base64url", "value": "Ag"}, "family": 4, "gateway": None, "metric": 2, "output_interface_semantic_id": None, "output_interface_subject_id": digest("b"), "prefix_length": 24, "protocol": "1", "route_type": "1", "scope": "0", "table": 200},
        ],
        "structural_topology_fingerprint": digest("1"),
    }


def test_multi_element_observation_total_orders_and_shuffle_invariance() -> None:
    canonical = _projection()
    validate_observation_order(canonical)
    expected = _projection_fingerprint("observation", canonical)
    for collection in ("datasets", "interfaces", "neighbors", "routes", "conformance"):
        shuffled = copy.deepcopy(canonical)
        shuffled[collection].reverse()
        with pytest.raises(ValidationError, match="canonical order"):
            validate_observation_order(shuffled)
        shuffled[collection].reverse()
        assert _projection_fingerprint("observation", shuffled) == expected
    shuffled = copy.deepcopy(canonical)
    shuffled["interfaces"][0]["addresses"].reverse()
    with pytest.raises(ValidationError, match="addresses are not in canonical order"):
        validate_observation_order(shuffled)
    shuffled = copy.deepcopy(canonical)
    shuffled["interfaces"][0]["addresses"][0]["flags"] = ["temporary", "deprecated"]
    with pytest.raises(ValidationError, match="flags are not in canonical ASCII order"):
        validate_observation_order(shuffled)


def test_mixed_bound_unbound_neighbor_uses_two_independent_reference_keys() -> None:
    projection = _projection()
    digest = lambda value: "sha256:" + value * 64
    projection["routes"] = []
    projection["neighbors"] = [
        {"address": {"encoding": "base64url", "value": "AQ"}, "family": 4, "interface_semantic_id": digest("f"), "interface_subject_id": None, "link_address": None, "namespace_key": "root", "observation_subject_id": digest("a"), "state": "1"},
        {"address": {"encoding": "base64url", "value": "AQ"}, "family": 4, "interface_semantic_id": None, "interface_subject_id": digest("0"), "link_address": None, "namespace_key": "root", "observation_subject_id": digest("b"), "state": "1"},
    ]
    vectors = load_json(ROOT / "conformance/edge-network-topology/4.0.0/observation-order-vectors.json")
    vector = next(case for case in vectors["cases"] if case["case_id"] == "mixed-bound-unbound-neighbors-two-level-key")
    validate_observation_order(projection)
    assert _projection_fingerprint("observation", projection) == vector["expected_observation_fingerprint"]
    competing = copy.deepcopy(projection)
    competing["neighbors"].reverse()
    assert _projection_fingerprint("observation", competing) == vector["competing_noncanonical_fingerprint"]
    with pytest.raises(ValidationError, match="observation neighbors are not in canonical order"):
        validate_observation_order(competing)


def test_mixed_bound_unbound_route_uses_two_independent_reference_keys() -> None:
    projection = _projection()
    digest = lambda value: "sha256:" + value * 64
    projection["neighbors"] = []
    projection["routes"] = [
        {"destination": {"encoding": "base64url", "value": "AQ"}, "family": 4, "gateway": None, "metric": 1, "output_interface_semantic_id": digest("f"), "output_interface_subject_id": None, "prefix_length": 24, "protocol": "1", "route_type": "1", "scope": "0", "table": 100},
        {"destination": {"encoding": "base64url", "value": "AQ"}, "family": 4, "gateway": None, "metric": 1, "output_interface_semantic_id": None, "output_interface_subject_id": digest("0"), "prefix_length": 24, "protocol": "1", "route_type": "1", "scope": "0", "table": 100},
    ]
    vectors = load_json(ROOT / "conformance/edge-network-topology/4.0.0/observation-order-vectors.json")
    vector = next(case for case in vectors["cases"] if case["case_id"] == "mixed-bound-unbound-routes-two-level-key")
    validate_observation_order(projection)
    assert _projection_fingerprint("observation", projection) == vector["expected_observation_fingerprint"]
    competing = copy.deepcopy(projection)
    competing["routes"].reverse()
    assert _projection_fingerprint("observation", competing) == vector["competing_noncanonical_fingerprint"]
    with pytest.raises(ValidationError, match="observation routes are not in canonical order"):
        validate_observation_order(competing)


def test_synthetic_noncanonical_artifact_is_schema_valid_but_semantically_nonconformant() -> None:
    # This synthetic fixture models the historical ordering defect without
    # incorporating any private live-device evidence.
    path = ROOT / "tests/fixtures/profile4/noncanonical-observation-order.json"
    artifact = load_json(path)
    schema = load_json(PROFILE_SCHEMAS[profile_key(artifact)])
    jsonschema.validators.validator_for(schema)(
        schema, registry=schema_registry(), format_checker=jsonschema.FormatChecker()
    ).validate(artifact)
    with pytest.raises(ValidationError, match="observation datasets are not in canonical order"):
        validate_profile4_semantics(artifact)
