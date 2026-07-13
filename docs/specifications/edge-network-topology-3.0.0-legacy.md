# InvarOS Edge Network Topology Profile 3.0.0 — Frozen Legacy Compatibility Specification

Status: normative draft describing the existing reference implementation exactly  
Specification URI: `https://tbom.yozi.systems/specifications/edge-network-topology/3.0.0-legacy`  
Legacy algorithm URI: `https://tbom.yozi.systems/algorithms/edge-network-topology/3.0.0/legacy-reference-sha256-v1`  
Owner and change controller: Yozi Systems  
Reference implementation context: `invarosd` commit `5cfb2a848d06e267112f207822e0df5c4711df30`, including the uncommitted Profile 3 profile-metadata additions reviewed on 2026-07-13

## 1. Scope and compatibility rule

This document freezes the behavior implemented by `plugins/topology/netlink_discover.c`, `plugins/topology/tbom.c`, and their data structures. It does not repair, reinterpret, or generalize that behavior. A conforming legacy implementation reproduces the byte-level formulas and quirks below. Existing artifacts, golden files, node IDs, `host_fingerprint` values, and `topology_fingerprint` values MUST NOT change.

Profile 3 is Linux-specific observed-state output. It is not a portable declared-intent topology model. Its identifiers are not asserted to be privacy-preserving, persistent instance identifiers, globally unique, collision-free at the descriptor level, or independently meaningful outside this exact algorithm.

Normative words in this document describe compatibility requirements only. They do not endorse the design for new implementations.

## 2. Emitted top-level object

The serializer emits one compact JSON object in this exact member order:

1. `graph`
2. `profile_id` with value `invaros.tbom.profile.edge_network_topology`
3. `profile_name` with value `InvarOS Edge Network Topology TBoM Profile`
4. `profile_version` with value `3.0.0`
5. `subsystem_identity`
6. `tbom_version` with value `3.0.0`
7. `topology_fingerprint`

`subsystem_identity` contains `host_fingerprint` and `observed_at_epoch`, in that order. The graph contains `edges` and then `nodes`.

## 3. Discovery inputs

The producer opens one `AF_NETLINK/SOCK_RAW/NETLINK_ROUTE` socket, requests a 1 MiB receive buffer, and performs these dumps sequentially on the initial network namespace only:

1. `RTM_GETLINK`, sequence 1;
2. `RTM_GETADDR`, sequence 2;
3. `RTM_GETROUTE`, sequence 3;
4. `RTM_GETNEIGH`, sequence 4.

The implementation accepts messages with the expected sequence number and expected message type. It does not validate the sender `sockaddr_nl`, `nlmsg_pid`, `NLM_F_DUMP_INTR`, or dump consistency. `NLMSG_ERROR` fails the operation. `ENOBUFS` causes one complete retry; other errors fail. Fixed capacities are 64 interfaces, 128 addresses, 64 routes, and 128 neighbors. Capacity overflow silently drops later records.

Routes are collected but are not serialized or fingerprinted.

## 4. Link parsing and normalization

For each accepted `RTM_NEWLINK`, Profile 3 uses:

- `ifinfomsg.ifi_index` as the process-local `ifindex`;
- `ifinfomsg.ifi_flags` to derive status;
- `IFLA_IFNAME`, copied into 16 bytes with truncation to 15 bytes and no JSON escaping;
- `IFLA_ADDRESS` only when its payload is exactly six bytes, formatted as lowercase colon-separated hex; other link-layer addresses become the empty string;
- `IFLA_MASTER` as `master_ifindex`;
- `IFLA_LINK` as `parent_ifindex`;
- `IFLA_MTU` as an unsigned 32-bit integer;
- `IFLA_LINKINFO/IFLA_INFO_KIND`, copied into 32 bytes with truncation to 31 bytes;
- `IFLA_LINKINFO/IFLA_INFO_DATA/IFLA_VLAN_ID` as a native-endian `uint16_t` VLAN ID.

Status precedence is:

1. `IFF_TESTING` -> `TESTING`;
2. `IFF_DORMANT` -> `DORMANT`;
3. both `IFF_UP` and `IFF_LOWER_UP` -> `UP`;
4. `IFF_UP` alone -> `DOWN`;
5. otherwise -> `UNKNOWN`.

No Unicode normalization, JSON escaping, duplicate detection, permanent-address lookup, namespace qualification, or all-zero-MAC suppression is performed.

## 5. Address and neighbor parsing

Addresses accept IPv4 and IPv6 only. The implementation reads `IFA_ADDRESS` and ignores `IFA_LOCAL`. The first usable `IFA_ADDRESS` is formatted with `inet_ntop`; prefix and scope are stored but not emitted. Thus point-to-point IPv4 local/peer semantics may be reversed or incomplete.

Neighbors accept IPv4 and IPv6 only, require both `NDA_DST` and an exactly six-byte `NDA_LLADDR`, and reject entries whose NUD state contains `NUD_INCOMPLETE`, `NUD_FAILED`, or `NUD_NOARP`. The NUD state and neighbor interface index are stored but omitted from JSON. A neighbor is therefore graph-global rather than interface-scoped on the wire.

## 6. Exact node-ID derivation

Every formula below hashes the raw bytes of the displayed C string using SHA-256 and emits 64 lowercase hexadecimal characters without a `sha256:` prefix. The colon is an unescaped delimiter. Inputs are truncated C buffers as described above.

### 6.1 Physical interface

An interface is physical for identity purposes iff `kind` is empty and the current six-byte MAC string is non-empty.

```text
node_id = hex_lower(SHA-256(name || ":" || current_mac))
```

### 6.2 Interface with a parent

If `parent_ifindex != 0` and a matching parent exists whose ID is already non-empty:

```text
node_id = hex_lower(SHA-256(kind || ":" || name || ":" || parent_node_id))
```

If the parent is missing or has no computed ID:

```text
node_id = hex_lower(SHA-256(kind || ":" || name || ":" || decimal_parent_ifindex))
```

### 6.3 Interface without a parent

```text
node_id = hex_lower(SHA-256(kind || ":" || name))
```

This includes bridges, loopback, unparented tunnels, and generic logical interfaces. A physical-looking interface without an exactly six-byte current address falls into this formula with an empty `kind`, producing SHA-256 of `":" || name`.

### 6.4 Neighbor

```text
node_id = hex_lower(SHA-256("neigh:" || current_mac || ":" || textual_ip))
```

The attached interface is not an input, so identical IP/MAC pairs on different interfaces collide.

### 6.5 Dependency evaluation

Physical IDs are computed first. The implementation then performs four passes over all remaining interfaces. Each remaining interface is computed on the first pass even if its parent's ID is unavailable, so enumeration order can select the `parent_ifindex` fallback. Later passes do not revise a non-empty ID.

## 7. Node type and relation classification

Node type mapping is exact string comparison:

- `bridge` -> `node_bridge`;
- `vlan` -> `node_vlan`;
- `tun`, `tap`, `wireguard`, `gre`, `gre6`, `sit`, `ip6tnl` -> `node_tunnel`;
- empty kind plus non-empty six-byte MAC string -> `node_physical`;
- everything else -> `node_logical`;
- admitted neighbor -> `node_neighbor`.

At most one edge is emitted per interface. `IFLA_MASTER` wins over `IFLA_LINK`. A resolved master creates `bridge_member`. Otherwise a resolved parent creates `vlan_parent` for kind `vlan`, `tunnel_parent` for the listed tunnel kinds, and `logical_parent` for every other kind. Unresolved relationships are silently omitted.

## 8. Graph ordering and serialization

Nodes are sorted by `memcmp` over the first 64 ASCII bytes of their hexadecimal IDs. Edges are sorted by source ID, then target ID using the same comparison, then by C `strcmp` on `relation_type`. IPv4 and IPv6 strings for each interface are independently sorted with C `strcmp`. Exact duplicates are retained.

The serializer is a hand-written compact emitter, not RFC 8785. It emits no insignificant whitespace and uses these fixed key orders:

- graph: `edges`, `nodes`;
- edge: `relation_type`, `source`, `target`;
- node: `id`, `properties`, `type`;
- interface properties: `ipv4_addresses`, `ipv6_addresses`, `mac_address`, `mtu`, `name`, `status`, optional `vlan_tag`;
- neighbor properties: `ipv4_addresses`, `ipv6_addresses`, `mac_address`.

Strings are inserted with `%s` without JSON escaping. A quote, reverse solidus, control byte, or invalid UTF-8 in a kernel-provided name or kind can produce invalid JSON. `vlan_tag` is emitted only when greater than zero. Empty addresses and MACs are emitted as empty strings where applicable.

## 9. Exact topology-fingerprint derivation

Let `graph_bytes` be exactly the compact bytes beginning with `{"edges":` and ending after the graph's closing `}` as produced by the serializer above. It includes every serialized node property and every emitted edge.

```text
topology_fingerprint = hex_lower(SHA-256(graph_bytes))
```

The value has no `sha256:` prefix. It includes names, current MAC addresses, assigned addresses, MTU, derived status, positive VLAN tags, runtime neighbors, node IDs, node types, and relationships. It excludes the timestamp, profile metadata, host fingerprint, routes, address prefix/scope, neighbor NUD state, and neighbor interface index.

## 10. Exact host-fingerprint derivation

The serializer reclassifies all interfaces and selects those classified `node_physical`. It sorts their 64-byte node IDs using C `strcmp`, concatenates the 64 ASCII bytes of each ID with no delimiter, and hashes the result:

```text
host_fingerprint = hex_lower(SHA-256(sorted_physical_node_id_1 || ... || sorted_physical_node_id_n))
```

When no physical interface exists, it is SHA-256 of the empty byte string (`e3b0c442...b855`). The value has no `sha256:` prefix.

## 11. Determinism boundary

For an identical valid in-memory snapshot with precomputed IDs, the serializer is deterministic. End-to-end discovery is not guaranteed deterministic because collection is sequential and non-atomic; capacity loss is silent; relationship fallback can depend on interface enumeration order and transient `ifindex`; neighbor/address state is mutable; and address formatting depends on `inet_ntop`.

## 12. Known defects and non-claims

Profile 3 intentionally preserves these defects:

- delimiter-ambiguous, untyped preimages without domain/version separation;
- current rather than permanent MAC in physical identity;
- interface name in physical and virtual identity;
- parent fallback dependent on Linux `ifindex` and enumeration order;
- VLAN ID absent from node identity;
- tunnel parameters/endpoints absent from identity and graph;
- neighbor identity not interface-scoped;
- no network-namespace model;
- runtime observations called topology and included in the topology fingerprint;
- hardware-dependent host correlation with an identical constant on hosts with no physical node;
- silent fixed-capacity truncation;
- no `NLM_F_DUMP_INTR` handling or kernel-sender validation;
- incomplete `IFA_LOCAL` handling;
- no JSON string escaping or invalid-byte representation;
- no duplicate/conflict policy;
- unknown kinds coerced to logical;
- cryptographic return values ignored;
- schema permits some combinations the serializer never emits and does not require all node properties.

Profile 3 does not claim cross-platform portability, independent reproducibility from a public semantic model, stable identity across rename/MAC change/replacement, atomic observation, complete discovery, privacy protection, namespace uniqueness, declared-intent structure, or Profile 4 conformance.

## 13. Freeze policy

Profile 3 remains a separately emitted legacy compatibility artifact. Corrections belong only to Profile 4. Golden artifacts are immutable preservation vectors. Any change that alters Profile 3 bytes or fingerprints requires a new legacy algorithm identifier and an explicit governance decision; it MUST NOT be published as this algorithm.
