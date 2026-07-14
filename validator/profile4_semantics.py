"""Semantic checks that JSON Schema alone cannot express for Profile 4."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import struct
import sys
from pathlib import Path

from jsonschema import ValidationError

from .validate_examples import ROOT


def _registry_path() -> Path:
    checkout = ROOT / "registries/edge-network/disclosure-profiles/1/registry.json"
    if checkout.is_file():
        return checkout
    installed = (
        Path(sys.prefix)
        / "share/invaros-tbom-spec/registries/edge-network/disclosure-profiles/1/registry.json"
    )
    if installed.is_file():
        return installed
    raise RuntimeError("Profile 4 disclosure-profile registry is unavailable")


def disclosure_profiles() -> dict[str, dict]:
    data = json.loads(_registry_path().read_text(encoding="utf-8"))
    return {profile["profile_uri"]: profile for profile in data["profiles"]}


def _decode_unpadded_base64url(value: str) -> bytes:
    try:
        raw = base64.b64decode(
            value + "=" * (-len(value) % 4),
            altchars=b"-_",
            validate=True,
        )
    except (ValueError, binascii.Error) as exc:
        raise ValidationError("encodedValue contains invalid unpadded base64url") from exc
    if base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=") != value:
        raise ValidationError("encodedValue base64url form is not canonical")
    return raw


def validate_encoded_values(value: object, path: tuple[object, ...] = ()) -> None:
    if isinstance(value, dict):
        if set(value) == {"encoding", "value"} and value.get("encoding") in {
            "utf-8",
            "base64url",
        }:
            if value["encoding"] == "utf-8":
                # A JSON string is Unicode and its UTF-8 encoding is therefore valid.
                value["value"].encode("utf-8")
            else:
                raw = _decode_unpadded_base64url(value["value"])
                try:
                    raw.decode("utf-8")
                except UnicodeDecodeError:
                    pass
                else:
                    raise ValidationError(
                        "encodedValue MUST use utf-8 when the original bytes are valid UTF-8",
                        path=path,
                    )
        for key, child in value.items():
            validate_encoded_values(child, path + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_encoded_values(child, path + (index,))


def _validate_object_fields(
    item: dict,
    rules: dict,
    path: tuple[object, ...],
) -> None:
    missing = sorted(set(rules["required"]) - set(item))
    forbidden = sorted(set(rules["forbidden"]) & set(item))
    allowed = set(rules["required"]) | set(rules["optional"])
    unexpected = sorted(set(item) - allowed - set(rules["forbidden"]))
    if missing:
        raise ValidationError(
            f"disclosure profile requires fields: {', '.join(missing)}", path=path
        )
    if forbidden:
        raise ValidationError(
            f"disclosure profile forbids fields: {', '.join(forbidden)}", path=path
        )
    if unexpected:
        raise ValidationError(
            f"disclosure profile does not define fields: {', '.join(unexpected)}",
            path=path,
        )


def validate_disclosure_projection(observation: dict) -> None:
    profiles = disclosure_profiles()
    profile_uri = observation["disclosure_profile_id"]
    if profile_uri not in profiles:
        raise ValidationError(f"unsupported disclosure_profile_id: {profile_uri!r}")
    profile = profiles[profile_uri]
    for collection in ("interfaces", "neighbors", "routes", "conformance"):
        rule = profile["collections"][collection]
        values = observation[collection]
        if not rule["non_empty_allowed"] and values:
            raise ValidationError(
                f"disclosure profile requires {collection} to be empty",
                path=(collection,),
            )
    for index, interface in enumerate(observation["interfaces"]):
        _validate_object_fields(
            interface, profile["interface_fields"], ("interfaces", index)
        )
        _validate_interface_observation(interface, ("interfaces", index))


_OBSERVATION_SUBJECT_DOMAIN = (
    "https://tbom.yozi.systems/domain/edge-network-topology/4.0.0/observation/subject"
)


def _tid_field(tag: int, value_type: int, value: bytes) -> bytes:
    return struct.pack(">HBBI", tag, value_type, 0, len(value)) + value


def _encoded_value_bytes(value: dict) -> bytes:
    if value["encoding"] == "utf-8":
        return value["value"].encode("utf-8")
    return _decode_unpadded_base64url(value["value"])


def interface_observation_subject_id(interface: dict) -> str:
    """Reproduce the normative Profile 4 interface observation locator."""
    kind = interface["interface_kind_observed"]
    fields = [
        _tid_field(1, 1, b"4.0.0"),
        _tid_field(2, 1, b"interface"),
        _tid_field(3, 1, interface["namespace_key"].encode("utf-8")),
        _tid_field(
            4,
            1 if interface["interface_name_observed"]["encoding"] == "utf-8" else 2,
            _encoded_value_bytes(interface["interface_name_observed"]),
        ),
        _tid_field(5, 0 if kind is None else 1, b"" if kind is None else kind.encode("utf-8")),
    ]
    body = struct.pack(">H", len(fields)) + b"".join(fields)
    domain = _OBSERVATION_SUBJECT_DOMAIN.encode("ascii")
    record = b"YOZI-TID" + struct.pack(">HH", 1, len(domain)) + domain + struct.pack(">I", len(body)) + body
    return "sha256:" + hashlib.sha256(record).hexdigest()


def _validate_interface_observation(interface: dict, path: tuple[object, ...]) -> None:
    kind = interface.get("interface_kind_observed")
    if kind is not None and kind != kind.lower():
        raise ValidationError("interface_kind_observed is not lowercase", path=path + ("interface_kind_observed",))
    # The public-minimal disclosure removes the observed name after this identifier
    # is constructed. All other profiles permit independent reproduction.
    if "interface_name_observed" in interface and "interface_kind_observed" in interface:
        expected = interface_observation_subject_id(interface)
        if interface["observation_subject_id"] != expected:
            raise ValidationError("interface observation_subject_id does not match its normative descriptor", path=path + ("observation_subject_id",))
    state = interface.get("kind_state")
    expected_state_kind = {
        "bridge": "bridge", "vlan": "vlan", "vxlan": "tunnel",
        "gre": "tunnel", "gre6": "tunnel", "wireguard": "tunnel",
        "vrf": "logical", "dummy": "logical", "loopback": "logical",
    }.get(kind)
    if state is not None and state["kind"] != expected_state_kind:
        raise ValidationError("kind_state does not match interface_kind_observed", path=path + ("kind_state",))
    if expected_state_kind is not None and state is None:
        raise ValidationError("modeled interface kind requires non-null kind_state", path=path + ("kind_state",))


def _parameter_key(item: dict) -> tuple[bytes, bytes]:
    return (
        item["parameter_id"].encode("ascii"),
        json.dumps(item["value"], ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8"),
    )


def _endpoint_key(item: dict) -> tuple:
    encoded = item["address"]
    address = (
        encoded["value"].encode("utf-8")
        if encoded["encoding"] == "utf-8"
        else _decode_unpadded_base64url(encoded["value"])
    )
    transport_order = {None: 0, "tcp": 1, "udp": 2}
    port = item["port"]
    return (item["family"], address, transport_order[item["transport"]], -1 if port is None else port)


def validate_structural_order(projection: dict) -> None:
    nodes = projection["nodes"]
    if nodes != sorted(nodes, key=lambda item: item["semantic_id"].encode("ascii")):
        raise ValidationError("structural nodes are not in canonical semantic-ID order")
    relation_key = lambda item: (
        item["relation_type"].encode("ascii"), item["source"].encode("ascii"),
        item["target"].encode("ascii"),
        json.dumps(item["parameters"], ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8"),
    )
    if projection["relations"] != sorted(projection["relations"], key=relation_key):
        raise ValidationError("structural relations are not in canonical order")
    node_types = {item["semantic_id"]: item["node_type"].rsplit("/", 1)[-1] for item in nodes}
    interface_types = {"physical", "bridge", "vlan", "tunnel", "logical"}
    for relation in projection["relations"]:
        source_type = node_types.get(relation["source"])
        target_type = node_types.get(relation["target"])
        if source_type is None or target_type is None:
            raise ValidationError("relation contains an unresolved structural reference")
        kind = relation["relation_type"].rsplit("/", 1)[-1]
        valid_pair = {
            "bridge-member": source_type in interface_types and target_type == "bridge",
            "vlan-parent": source_type == "vlan" and target_type in interface_types,
            "tunnel-parent": source_type == "tunnel" and target_type in interface_types,
            "logical-parent": source_type == "logical",
            "tunnel-peer": source_type == "tunnel" and target_type == "declared-federation-peer",
            "federation-pathway": source_type in interface_types and target_type == "declared-federation-peer",
            "declared-handshake-peer": source_type in interface_types and target_type == "declared-federation-peer",
        }.get(kind, False)
        if not valid_pair:
            raise ValidationError("relation type is not valid for its source/target node types")
    for item in nodes + projection["relations"]:
        parameters = item.get("parameters")
        if parameters is not None:
            ids = [parameter["parameter_id"] for parameter in parameters]
            if len(ids) != len(set(ids)):
                raise ValidationError("duplicate parameter_id in set-valued parameters")
            if parameters != sorted(parameters, key=_parameter_key):
                raise ValidationError("parameters are not in canonical order")
        if item.get("node_type", "").endswith("/tunnel"):
            _validate_tunnel_parameters(item)
        parents = item.get("parent_semantic_ids")
        if parents is not None and parents != sorted(parents, key=lambda value: bytes.fromhex(value[7:])):
            raise ValidationError("parent_semantic_ids are not in canonical digest order")
        endpoints = item.get("endpoints")
        if endpoints is not None and endpoints != sorted(endpoints, key=_endpoint_key):
            raise ValidationError("federation endpoints are not in canonical order")


def _validate_tunnel_parameters(item: dict) -> None:
    base = "https://tbom.yozi.systems/registries/edge-network/tunnel-parameters/1/"
    identity_by_kind = {
        "vxlan": base + "vxlan-vni",
        "gre": base + "gre-key-id",
        "gre6": base + "gre-key-id",
        "wireguard": base + "wireguard-public-key-id",
    }
    kind = item["interface_kind"].rsplit("/", 1)[-1]
    parameters = item["parameters"]
    identity = [p for p in parameters if p["parameter_id"] in set(identity_by_kind.values())]
    if len(identity) > 1:
        raise ValidationError("tunnel has more than one identity parameter")
    if identity and identity[0]["parameter_id"] != identity_by_kind.get(kind):
        raise ValidationError("tunnel identity parameter does not match interface kind")


def _source_content_projection(manifest: dict, source_id: str) -> dict:
    def without_source_key(item: dict) -> dict:
        return {key: value for key, value in item.items() if key != "source_key"}

    namespaces = [
        without_source_key(item)
        for item in manifest["namespaces"]
        if item["source_key"] == source_id
    ]
    nodes = [
        without_source_key(item)
        for item in manifest["nodes"]
        if item["source_key"] == source_id
    ]
    relations = [
        without_source_key(item)
        for item in manifest["relations"]
        if item["source_key"] == source_id
    ]
    namespaces.sort(key=lambda item: item["namespace_key"].encode("utf-8"))
    nodes.sort(key=lambda item: item["declaration_key"].encode("utf-8"))
    relations.sort(
        key=lambda item: (
            item["relation_type"].encode("ascii"),
            item["source_declaration_key"].encode("utf-8"),
            item["target_declaration_key"].encode("utf-8"),
            json.dumps(
                item["parameters"],
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8"),
        )
    )
    return {
        "manifest_version": manifest["manifest_version"],
        "namespaces": namespaces,
        "nodes": nodes,
        "relations": relations,
    }


def validate_source_content_fingerprints(manifest: dict) -> None:
    sources = manifest["sources"]
    source_ids = [source["source_id"] for source in sources]
    if len(source_ids) != len(set(source_ids)):
        raise ValidationError("duplicate declared-intent source_id")
    known = set(source_ids)
    for collection in ("namespaces", "nodes", "relations"):
        for index, declaration in enumerate(manifest[collection]):
            if declaration["source_key"] not in known:
                raise ValidationError(
                    "declared content refers to an unknown source_id",
                    path=(collection, index, "source_key"),
                )
    for index, source in enumerate(sources):
        projection = _source_content_projection(manifest, source["source_id"])
        canonical = json.dumps(
            projection,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        expected = "sha256:" + hashlib.sha256(canonical).hexdigest()
        if source["content_fingerprint"] != expected:
            raise ValidationError(
                "declared-intent content_fingerprint does not match declared content",
                path=("sources", index, "content_fingerprint"),
            )


def _projection_fingerprint(kind: str, projection: dict) -> str:
    canonical = json.dumps(
        projection, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    domain = (
        "https://tbom.yozi.systems/domain/edge-network-topology/"
        f"4.0.0/fingerprint/{kind}"
    ).encode("ascii")
    envelope = (
        b"YOZI-FP\0" + struct.pack(">HH", 1, len(domain)) + domain +
        b"\x01" + struct.pack(">Q", len(canonical)) + canonical
    )
    return "sha256:" + hashlib.sha256(envelope).hexdigest()


def validate_artifact_fingerprints(payload: dict) -> None:
    for name, projection_key in (
        ("topology", "structural_topology"), ("observation", "observation")
    ):
        fingerprint = payload["fingerprints"][name]
        projection = payload.get(projection_key)
        if fingerprint["availability"] == "available":
            if projection is None:
                raise ValidationError(f"available {name} fingerprint has no projection")
            expected = _projection_fingerprint(name, projection)
            if fingerprint["value"] != expected:
                raise ValidationError(f"{name} fingerprint does not match projection")


def validate_profile4_semantics(payload: dict) -> None:
    validate_encoded_values(payload)
    validate_artifact_fingerprints(payload)
    manifest = payload.get("declared_intent")
    if manifest is not None:
        validate_source_content_fingerprints(manifest)
        for node in manifest["nodes"]:
            if node["node_type"].endswith("/tunnel"):
                _validate_tunnel_parameters(node)
    structural = payload.get("structural_topology")
    if structural is not None:
        validate_structural_order(structural)
    observation = payload.get("observation")
    if observation is not None:
        validate_disclosure_projection(observation)
    intent_status = payload.get("intent_status")
    conformance = payload.get("intent_conformance")
    candidate = payload.get("candidate_intent")
    absent_reason = (
        "https://tbom.yozi.systems/registries/edge-network/"
        "reason-codes/1/declared_intent_absent"
    )
    if intent_status == "absent":
        if payload.get("declared_intent") is not None or payload.get("structural_topology") is not None:
            raise ValidationError("absent intent cannot contain declared structure")
        if conformance != {"reason_codes": [absent_reason], "status": "not-evaluated"}:
            raise ValidationError("absent intent requires not-evaluated conformance")
        if observation is not None and observation.get("conformance"):
            raise ValidationError("absent intent cannot contain conformance records")
        candidate_fields_available = (
            observation is not None and
            not observation["disclosure_profile_id"].endswith("/public-minimal") and all(
            all(key in interface for key in (
                "interface_kind_observed", "interface_name_observed", "kind_state",
                "master_observed", "parent_observed",
            ))
            for interface in observation["interfaces"])
        )
        if candidate_fields_available and candidate is None:
            raise ValidationError("bootstrap observation requires candidate_intent")
        if candidate is not None:
            expected = [
                {
                    key: interface[key]
                    for key in (
                        "interface_kind_observed", "interface_name_observed",
                        "kind_state", "master_observed", "namespace_key",
                        "observation_subject_id", "parent_observed",
                    )
                }
                for interface in observation["interfaces"]
            ]
            if candidate["interfaces"] != expected:
                raise ValidationError("candidate_intent is not the deterministic observation projection")
            fingerprint = payload["fingerprints"]["observation"]
            expected_fingerprint = fingerprint["value"] if fingerprint["availability"] == "available" else None
            if candidate["source_observation_fingerprint"] != expected_fingerprint:
                raise ValidationError("candidate_intent observation fingerprint mismatch")
    elif intent_status == "valid":
        if payload.get("declared_intent") is None or candidate is not None:
            raise ValidationError("valid intent requires declared_intent and forbids candidate_intent")
        if conformance != {"reason_codes": [], "status": "evaluated"}:
            raise ValidationError("valid intent requires evaluated conformance")
