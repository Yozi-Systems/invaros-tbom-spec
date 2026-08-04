"""Profile 4 schema meta-validation and representative-example coverage."""

from __future__ import annotations

import jsonschema
import pytest
import copy

from validator.validate_examples import (
    ROOT,
    SCHEMA_ROOT,
    load_json,
    schema_store,
    schema_registry,
    validate_payload,
)

PHASE0 = ROOT / "conformance/edge-network-topology/4.0.0"
SCHEMAS = sorted(SCHEMA_ROOT.rglob("*.json"))


def _validate(schema: dict, instance: object) -> None:
    cls = jsonschema.validators.validator_for(schema)
    cls.check_schema(schema)
    cls(schema, registry=schema_registry(), format_checker=jsonschema.FormatChecker()).validate(instance)


def _validate_definition(schema_id: str, definition: str, instance: object) -> None:
    wrapper = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$ref": f"{schema_id}#/$defs/{definition}",
    }
    _validate(wrapper, instance)


def test_all_schemas_parse_and_meta_validate() -> None:
    # 7 Profile 3/4 schemas, plus the 2 qualification artifact schemas added by
    # Qualification Evidence WP-01.1. The count is asserted so that growing the
    # schema tree is a deliberate edit rather than a silent one; it did its job
    # when the qualification schemas landed.
    assert len(SCHEMAS) == 9
    for path in SCHEMAS:
        schema = load_json(path)
        jsonschema.validators.validator_for(schema).check_schema(schema)


def test_disclosure_registry_schema_and_instance_validate() -> None:
    root = ROOT / "registries/edge-network/disclosure-profiles/1"
    schema = load_json(root / "schema.json")
    jsonschema.validators.validator_for(schema).check_schema(schema)
    _validate(schema, load_json(root / "registry.json"))

    interface_fields = {
        "addresses", "carrier", "current_link_address", "declared_semantic_id",
        "interface_kind_observed", "interface_name_observed", "kind_state", "link_status",
        "master_observed", "mtu", "namespace_key", "observation_subject_id",
        "parent_observed", "permanent_link_address",
    }
    for profile in load_json(root / "registry.json")["profiles"]:
        groups = [set(profile["interface_fields"][name]) for name in ("required", "optional", "forbidden")]
        assert groups[0].isdisjoint(groups[1])
        assert groups[0].isdisjoint(groups[2])
        assert groups[1].isdisjoint(groups[2])
        assert set.union(*groups) == interface_fields


def test_complete_profile4_artifact_validates() -> None:
    data = load_json(PHASE0 / "representative-examples.json")
    validate_payload(data["complete_host_artifact"])


def test_bootstrap_artifact_and_candidate_validate_semantically() -> None:
    artifact = copy.deepcopy(
        load_json(PHASE0 / "representative-examples.json")["complete_host_artifact"]
    )
    reason = (
        "https://tbom.yozi.systems/registries/edge-network/"
        "reason-codes/1/declared_intent_absent"
    )
    artifact["declared_intent"] = None
    artifact["structural_topology"] = None
    artifact["identity_plane"]["nodes"] = []
    artifact["intent_status"] = "absent"
    artifact["intent_conformance"] = {
        "reason_codes": [reason], "status": "not-evaluated"
    }
    artifact["fingerprints"]["topology"] = {
        "algorithm": "https://tbom.yozi.systems/algorithms/edge-network-topology/4.0.0/topology-fingerprint-yozi-fp-v1-jcs-sha256",
        "availability": "unavailable",
        "error_code": "https://tbom.yozi.systems/registries/edge-network/error-codes/1/structural-projection-unavailable",
        "reason_codes": [reason],
        "value": None,
    }
    artifact["observation"]["structural_topology_fingerprint"] = None
    artifact["fingerprints"]["observation"]["value"] = (
        "sha256:cf5cfe908280c477f6fa29d396fabdcb781c7508845e2d8ff4e342e35837cd5c"
    )
    artifact["candidate_intent"] = {
        "activation": "operator-action-required",
        "candidate_version": "1",
        "completeness": "complete",
        "interfaces": [],
        "source_observation_fingerprint": artifact["fingerprints"]["observation"]["value"],
        "status": "candidate-not-active",
    }
    validate_payload(artifact)

    activated = copy.deepcopy(artifact)
    activated["candidate_intent"]["status"] = "active"
    with pytest.raises(jsonschema.ValidationError):
        validate_payload(activated)


def test_bootstrap_conformance_vectors_define_all_three_input_states() -> None:
    vectors = load_json(PHASE0 / "bootstrap-vectors.json")["cases"]
    assert {case["case_id"] for case in vectors} == {
        "intent-absent-complete-observation",
        "intent-absent-partial-observation",
        "activated-intent-invalid",
    }
    invalid = next(case for case in vectors if case["case_id"] == "activated-intent-invalid")
    assert invalid["expected"]["artifact_emitted"] is False


def test_profile4_projections_and_manifest_validate() -> None:
    artifact = load_json(PHASE0 / "representative-examples.json")["complete_host_artifact"]
    store = schema_store()
    for schema_id, value in (
        ("https://tbom.yozi.systems/schemas/edge-network-topology/4.0.0/intent-manifest.schema.json", artifact["declared_intent"]),
        ("https://tbom.yozi.systems/schemas/edge-network-topology/4.0.0/structural-projection.schema.json", artifact["structural_topology"]),
        ("https://tbom.yozi.systems/schemas/edge-network-topology/4.0.0/observation-projection.schema.json", artifact["observation"]),
    ):
        _validate(store[schema_id], value)


def test_public_minimal_schema_suppresses_kind_and_kind_state() -> None:
    observation = copy.deepcopy(
        load_json(PHASE0 / "representative-examples.json")["complete_host_artifact"]["observation"]
    )
    observation["disclosure_profile_id"] = (
        "https://tbom.yozi.systems/registries/edge-network/"
        "disclosure-profiles/1/public-minimal"
    )
    observation["interfaces"] = [{
        "namespace_key": "root",
        "observation_subject_id": "sha256:" + "1" * 64,
    }]
    schema = schema_store()[
        "https://tbom.yozi.systems/schemas/edge-network-topology/4.0.0/"
        "observation-projection.schema.json"
    ]
    _validate(schema, observation)
    observation["interfaces"][0]["interface_kind_observed"] = "bridge"
    with pytest.raises(jsonschema.ValidationError):
        _validate(schema, observation)


@pytest.mark.parametrize(
    ("definition", "fragment"),
    [
        ("physical", "physical_interface"),
        ("bridge", "bridge"),
        ("vlan", "vlan"),
        ("federationPeer", "declared_federation_peer"),
        ("registeredTunnel", "tunnel"),
        ("registeredLogical", "logical"),
        ("relation", "relation"),
    ],
)
def test_structural_fragments_validate(definition: str, fragment: str) -> None:
    examples = load_json(PHASE0 / "representative-examples.json")
    _validate_definition(
        "https://tbom.yozi.systems/schemas/edge-network-topology/4.0.0/structural-projection.schema.json",
        definition,
        examples["representative_fragments"][fragment],
    )


def test_runtime_neighbor_and_conformance_validate() -> None:
    examples = load_json(PHASE0 / "representative-examples.json")
    _validate_definition(
        "https://tbom.yozi.systems/schemas/edge-network-topology/4.0.0/observation-projection.schema.json",
        "neighbor",
        examples["representative_fragments"]["runtime_neighbor_observation"],
    )
    for fragment in (
        "bridge_observation_kind_state", "vlan_observation_kind_state",
        "tunnel_observation_kind_state", "logical_observation_kind_state",
    ):
        _validate_definition(
            "https://tbom.yozi.systems/schemas/edge-network-topology/4.0.0/observation-projection.schema.json",
            "kindState",
            examples["representative_fragments"][fragment],
        )
    schema = schema_store()[
        "https://tbom.yozi.systems/schemas/edge-network-topology/4.0.0/conformance.schema.json"
    ]
    _validate(
        schema,
        {
            "declared_semantic_id": None,
            "observation_subject_id": None,
            "reason_codes": [],
            "status": "unknown",
        },
    )


@pytest.mark.parametrize(
    "value",
    ["AAAAAA", "AAAAAAAAAAAAAAAAAAAAAA", "fwAAAQ", "AQBeAAD7", "_wIAAAAAAAAAAAAAAAAAAQ"],
)
def test_binary_network_values_are_always_base64url(value: str) -> None:
    schema_id = (
        "https://tbom.yozi.systems/schemas/edge-network-topology/4.0.0/"
        "observation-projection.schema.json"
    )
    _validate_definition(
        schema_id, "binaryValue", {"encoding": "base64url", "value": value}
    )
    with pytest.raises(jsonschema.ValidationError):
        _validate_definition(
            schema_id,
            "binaryValue",
            {"encoding": "utf-8", "value": "127.0.0.1"},
        )


def test_foreign_trust_domain_is_valid_and_unknown_declared_kind_is_not() -> None:
    examples = load_json(PHASE0 / "representative-examples.json")["representative_fragments"]
    peer = copy.deepcopy(examples["declared_federation_peer"])
    peer["trust_domain"] = "https://operator.example/trust/site-b"
    _validate_definition(
        "https://tbom.yozi.systems/schemas/edge-network-topology/4.0.0/structural-projection.schema.json",
        "federationPeer",
        peer,
    )
    tunnel = copy.deepcopy(examples["tunnel"])
    tunnel["interface_kind"] = "https://tbom.yozi.systems/not-a-registry/anything"
    with pytest.raises(jsonschema.ValidationError):
        _validate_definition(
            "https://tbom.yozi.systems/schemas/edge-network-topology/4.0.0/structural-projection.schema.json",
            "registeredTunnel",
            tunnel,
        )


def test_fingerprint_vector_projections_validate() -> None:
    vectors = load_json(PHASE0 / "fingerprint-vectors.json")
    store = schema_store()
    for vector in vectors["topology_vectors"]:
        _validate(
            store["https://tbom.yozi.systems/schemas/edge-network-topology/4.0.0/structural-projection.schema.json"],
            vector["projection"],
        )
    for vector in vectors["observation_vectors"]:
        _validate(
            store["https://tbom.yozi.systems/schemas/edge-network-topology/4.0.0/observation-projection.schema.json"],
            vector["projection"],
        )
