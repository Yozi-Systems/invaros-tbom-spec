#!/usr/bin/env python3
"""Regenerate normative YOZI-TID vectors from readable field declarations."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "conformance/edge-network-topology/4.0.0/semantic-identity-vectors.json"
TYPES = {"null": 0, "utf-8": 1, "bytes": 2, "uint64": 3, "boolean": 4, "digest": 5, "array": 6, "record": 7}
BASE = "https://tbom.yozi.systems"


def value_bytes(item: dict) -> bytes:
    kind, value = item["type"], item.get("value")
    if kind == "null":
        return b""
    if kind == "utf-8":
        return value.encode("utf-8")
    if kind == "bytes":
        return bytes.fromhex(item["value_hex"])
    if kind == "uint64":
        return struct.pack(">Q", value)
    if kind == "boolean":
        return bytes([value])
    if kind == "digest":
        return bytes.fromhex(value.removeprefix("sha256:"))
    if kind == "record":
        fields = b"".join(field_bytes(field) for field in value)
        return struct.pack(">H", len(value)) + fields
    if kind == "array":
        elements = []
        for element in value:
            encoded = value_bytes(element)
            elements.append(struct.pack(">BBI", TYPES[element["type"]], 0, len(encoded)) + encoded)
        if item.get("set_semantics"):
            elements.sort()
            assert len(elements) == len(set(elements))
        return struct.pack(">I", len(elements)) + b"".join(elements)
    raise AssertionError(kind)


def field_bytes(field: dict) -> bytes:
    encoded = value_bytes(field)
    return struct.pack(">HBBI", field["tag"], TYPES[field["type"]], 0, len(encoded)) + encoded


def vector(vector_id: str, node: str, fields: list[dict], description: str) -> dict:
    domain = f"{BASE}/domain/edge-network-topology/4.0.0/node/{node}"
    body = struct.pack(">H", len(fields)) + b"".join(field_bytes(field) for field in fields)
    record = b"YOZI-TID" + struct.pack(">HH", 1, len(domain)) + domain.encode("ascii") + struct.pack(">I", len(body)) + body
    return {
        "vector_id": vector_id,
        "description": description,
        "domain": domain,
        "fields": fields,
        "expected_record_length_octets": len(record),
        "expected_record_hex": record.hex(),
        "expected_semantic_id": "sha256:" + hashlib.sha256(record).hexdigest(),
    }


def common(node: str, name: dict, kind: str) -> list[dict]:
    return [
        {"tag": 1, "type": "utf-8", "value": "4.0.0"},
        {"tag": 2, "type": "utf-8", "value": f"{BASE}/registries/edge-network/node-types/1/{node}"},
        {"tag": 3, "type": "utf-8", "value": "root"},
        {"tag": 4, **name},
        {"tag": 5, "type": "utf-8", "value": kind},
    ]


def main() -> None:
    d1 = "sha256:" + "11" * 32
    d2 = "sha256:" + "22" * 32
    vectors = [
        vector("tid-physical-all-primitives", "physical", common("physical", {"type": "utf-8", "value": "eth0"}, f"{BASE}/registries/edge-network/interface-kinds/1/ethernet") + [{"tag": 100, "type": "utf-8", "value": "ethernet"}, {"tag": 101, "type": "null", "value": None}], "Physical node covers UTF-8 and typed null."),
        vector("tid-bridge-parameter-record", "bridge", common("bridge", {"type": "utf-8", "value": "br0"}, f"{BASE}/registries/edge-network/interface-kinds/1/linux-bridge") + [{"tag": 110, "type": "utf-8", "value": "ieee8021-bridge"}, {"tag": 111, "type": "array", "set_semantics": True, "value": [{"type": "record", "value": [{"tag": 1, "type": "utf-8", "value": f"{BASE}/registries/edge-network/bridge-parameters/1/stp-enabled"}, {"tag": 2, "type": "boolean", "value": True}]}]}], "Bridge node covers array, nested record, and boolean."),
        vector("tid-vlan-uint64-digest", "vlan", common("vlan", {"type": "utf-8", "value": "eth0.10"}, f"{BASE}/registries/edge-network/interface-kinds/1/ieee8021q-vlan") + [{"tag": 120, "type": "uint64", "value": 10}, {"tag": 121, "type": "uint64", "value": 33024}, {"tag": 122, "type": "digest", "value": d1}], "VLAN node covers uint64 and digest."),
        vector("tid-tunnel-invalid-utf8-bytes-set", "tunnel", common("tunnel", {"type": "bytes", "value_hex": "ff8041"}, f"{BASE}/registries/edge-network/interface-kinds/1/wireguard") + [{"tag": 130, "type": "utf-8", "value": f"{BASE}/registries/edge-network/interface-kinds/1/wireguard"}, {"tag": 131, "type": "array", "set_semantics": True, "value": [{"type": "digest", "value": d2}, {"type": "digest", "value": d1}]}, {"tag": 132, "type": "record", "value": [{"tag": 1, "type": "uint64", "value": 4}, {"tag": 2, "type": "bytes", "value_hex": "c0000208"}, {"tag": 3, "type": "utf-8", "value": "udp"}, {"tag": 4, "type": "uint64", "value": 51820}]}, {"tag": 133, "type": "null", "value": None}], "Tunnel node covers invalid-UTF-8 bytes, sorted set, and endpoint record."),
        vector("tid-logical-parent-set", "logical", common("logical", {"type": "utf-8", "value": "vrf-blue"}, f"{BASE}/registries/edge-network/interface-kinds/1/vrf") + [{"tag": 140, "type": "utf-8", "value": f"{BASE}/registries/edge-network/interface-kinds/1/vrf"}, {"tag": 141, "type": "array", "set_semantics": True, "value": [{"type": "digest", "value": d2}, {"type": "digest", "value": d1}]}, {"tag": 142, "type": "array", "set_semantics": True, "value": []}], "Logical node proves parent set normalization."),
        vector("tid-federation-endpoint-set", "declared-federation-peer", common("declared-federation-peer", {"type": "null", "value": None}, f"{BASE}/registries/edge-network/node-types/1/declared-federation-peer") + [{"tag": 160, "type": "utf-8", "value": f"{BASE}/registries/edge-network/federation-mechanisms/1/wireguard"}, {"tag": 161, "type": "utf-8", "value": "site-b"}, {"tag": 162, "type": "utf-8", "value": "https://example.test/trust/site-b"}, {"tag": 163, "type": "array", "set_semantics": True, "value": [{"type": "record", "value": [{"tag": 1, "type": "uint64", "value": 4}, {"tag": 2, "type": "bytes", "value_hex": "c0000208"}, {"tag": 3, "type": "utf-8", "value": "udp"}, {"tag": 4, "type": "uint64", "value": 51820}]}]}, {"tag": 164, "type": "digest", "value": d2}, {"tag": 165, "type": "array", "set_semantics": True, "value": []}], "Federation node covers a set of nested endpoint records."),
    ]
    document = {"algorithm": f"{BASE}/algorithms/edge-network-topology/4.0.0/semantic-id-yozi-tid-v1-sha256", "status": "normative-synthetic", "vectors": vectors, "vector_set": f"{BASE}/conformance/edge-network-topology/4.0.0/phase0/semantic-identity"}
    OUTPUT.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
