# Profile 3 Legacy Reference SHA-256 Algorithm

Algorithm URI: `https://tbom.yozi.systems/algorithms/edge-network-topology/3.0.0/legacy-reference-sha256-v1`  
Status: frozen normative compatibility definition

This algorithm is the exact aggregate of the node-ID, host-fingerprint, graph serializer, and topology-fingerprint behavior in the frozen Profile 3 specification. It has no binary envelope, no domain separation, no RFC 8785 step, and no `sha256:` output prefix.

## 1. Node IDs

```text
physical: SHA256_HEX(name || ":" || current_six_byte_mac_text)
parent-resolved: SHA256_HEX(kind || ":" || name || ":" || parent_id_hex)
parent-fallback: SHA256_HEX(kind || ":" || name || ":" || decimal_parent_ifindex)
unparented: SHA256_HEX(kind || ":" || name)
neighbor: SHA256_HEX("neigh:" || mac_text || ":" || inet_ntop_ip_text)
```

`SHA256_HEX` is lowercase hex of SHA-256 over exact C-string bytes. No delimiter escaping occurs. Physical means empty kind and non-empty exactly-six-byte current MAC text. Parent fallback and dependency order are implementation-defined by the frozen four-pass traversal described in the legacy specification.

## 2. Host fingerprint

```text
ids = node IDs of interfaces classified node_physical
sort ids with bytewise C strcmp
preimage = concatenation of exactly 64 ASCII bytes per ID, no delimiter
host_fingerprint = SHA256_HEX(preimage)
```

For no physical nodes, the preimage is empty.

## 3. Graph bytes

Nodes sort by the 64 ASCII ID bytes. Edges sort by source, target, relation. Address text arrays sort with C `strcmp`. The exact compact member order and optional VLAN behavior are defined in `docs/specifications/edge-network-topology-3.0.0-legacy.md`. Strings are not escaped. The result is a byte string, not a standards-based canonical JSON value.

## 4. Topology fingerprint

```text
topology_fingerprint = SHA256_HEX(exact_compact_graph_bytes)
```

Only the graph object is hashed. Top-level profile fields, timestamp, and host fingerprint are excluded.

## 5. Language-neutral compatibility pseudocode

```text
function legacy_emit(snapshot):
    compute_physical_ids(snapshot.in_discovery_order)
    repeat 4 times:
        for interface in snapshot.in_discovery_order:
            if interface.id is empty: compute_id_once_with_possible_ifindex_fallback(interface)
    nodes = interfaces + admitted_neighbors
    sort(nodes, first_64_ascii_id_bytes)
    edges = at_most_one_resolved_master_else_parent_edge_per_interface
    sort(edges, source_id, target_id, relation_ascii)
    graph_bytes = emit_fixed_order_compact_graph_without_string_escaping(nodes, edges)
    topology = SHA256_HEX(graph_bytes)
    physical_ids = sort(ids(reclassified_physical_interfaces), ascii)
    host = SHA256_HEX(concat_64_ascii_bytes(physical_ids))
    return emit_fixed_order_full_object(graph_bytes, host, observed_epoch, topology)
```

## 6. Freeze requirement

Implementers MUST reproduce quirks rather than correcting them. Any correction changes the algorithm and cannot use this URI. Profile 4 is the correction path.
