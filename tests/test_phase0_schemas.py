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
    assert len(SCHEMAS) == 7
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
        "interface_kind_observed", "interface_name_observed", "link_status",
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


def test_profile4_projections_and_manifest_validate() -> None:
    artifact = load_json(PHASE0 / "representative-examples.json")["complete_host_artifact"]
    store = schema_store()
    for schema_id, value in (
        ("https://tbom.yozi.systems/schemas/edge-network-topology/4.0.0/intent-manifest.schema.json", artifact["declared_intent"]),
        ("https://tbom.yozi.systems/schemas/edge-network-topology/4.0.0/structural-projection.schema.json", artifact["structural_topology"]),
        ("https://tbom.yozi.systems/schemas/edge-network-topology/4.0.0/observation-projection.schema.json", artifact["observation"]),
    ):
        _validate(store[schema_id], value)


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
