# InvarOS Edge Network Topology Identity Review and Profile 4 Architecture Plan

> **Informative design record — not normative specification text.** The
> normative pre-implementation drafts are under `docs/specifications/`,
> `docs/algorithms/`, `docs/registries/`, and `schemas/`.

> **2026-07-13 deterministic-draft correction.** The locked Profile 4.0.0
> draft now normatively defines the four Version 1 interface observation-state
> forms, the interface observation-subject YOZI-TID descriptor, and the single
> tunnel-parameter mapping for tags 134 through 136. These minimal corrections
> remove the observation serialization, subject-correlation, and tunnel-ID
> interoperability blockers; they add no Version 1 capability and do not alter
> Profile 3.

Status: final implementation architecture with Phase 0 normative draft package; production implementation not started  
Review date: 2026-07-13  
Repository: `/home/yozi/invarosd`  
Specification owner and change controller: Yozi Systems  
Intended public specification and schema authority: `https://tbom.yozi.systems/`

This document preserves the complete reverse-engineering analysis of Edge Network Topology Profile 3.0.0 and defines the operator-approved implementation architecture for Profile 4.0.0. It remains a pre-production-implementation review artifact. Phase 0 has created draft normative specifications, registries, algorithm definitions, closed JSON Schemas, and synthetic conformance vectors. No production C code, running topology plugin behavior, Profile 3 output, Profile 3 golden artifact, or deployed fingerprint algorithm has been changed.

The terms MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY in the Profile 4 portion express requirements for the implementation and forthcoming normative specification. Publication by Yozi Systems remains the act that establishes the public standard.

The governing architectural philosophy is:

> Structure is defined by declared intent, not by observed behavior.

Accordingly, governance artifacts never infer structural truth from runtime activity. Observations are evidence about runtime state and possible conformance to declared intent; they do not create, remove, or rewrite declared topology.

## 1. Executive conclusion

The current Profile 3 implementation is byte-deterministic only for an identical, already-populated in-memory snapshot. End-to-end discovery is not reliably deterministic across independent implementations, reboots, or some valid Linux enumeration orders.

The interoperability defect is broader than the missing public node-ID definition:

- The emitted field is `graph.nodes[].id`; there is no Edge TBoM field named `node_id`.
- Node identity, host identity, graph canonicalization, and normalization are defined only in implementation code and a non-normative R&D plan.
- `topology_fingerprint` covers mutable operational observations, including status, addresses, MTU, current MAC addresses, and neighbor-cache contents, rather than structural topology alone.
- Parent-dependent interface IDs can incorporate ephemeral Linux `ifindex` values and can depend on Netlink dump order.
- Several normalization rules claimed in the R&D plan are not implemented.
- The current schema constrains shape and digest syntax but does not define derivation, canonicalization, ordering, uniqueness, completeness, or identity semantics.

The accepted direction is a dual-plane Profile 4 architecture:

1. Persistent, disclosure-scoped instance identity tracks managed objects and intentionally depends on local persisted state.
2. Stateless semantic identity descriptors are independently reproducible.
3. Structural topology is derived exclusively from valid declared intent and is separated from operational observation state.
4. A structural topology fingerprint identifies only normalized structural facts.
5. A separate observation fingerprint identifies normalized disclosed runtime state.
6. Host identity uses a portable random persisted fallback and does not require hardware identifiers.
7. Profile 3.0.0 remains frozen as an explicitly named legacy compatibility profile.
8. Profile 3 and Profile 4 will both be published; existing Profile 3 topology fingerprints must not silently change.
9. All D-01 through D-30 decisions are approved, including the modified D-15, D-18, and D-20 decisions.
10. Fail-closed behavior, explicit uncertainty, explicit incompleteness, versioned evolution, and portability are normative design constraints.

## 2. Profile 3 source inventory

### 2.1 Runtime execution path

- `src/main.c` loads the plugin, resolves `invaros_topology_entry`, and wires discovery into ubus.
- `src/plugin_loader.c` performs `dlopen` and `dlsym` plugin loading.
- `src/daemon.c` runs the uloop event loop.
- `src/ubus.c` handles `invaros.topology discover`, invokes the plugin, and returns the TBoM as an escaped JSON string in the ubus `tbom` field.
- `include/invarosd/topology.h` defines the topology extension API.
- `include/invarosd/ubus.h` defines ubus discovery wiring.

### 2.2 Discovery and identifier implementation

- `plugins/topology/topology_plugin.c` allocates the snapshot, runs discovery, and serializes it.
- `plugins/topology/netlink_discover.h` defines the fixed-size snapshot model and limits.
- `plugins/topology/netlink_discover.c` implements Netlink parsing, normalization, classification, and interface and neighbor IDs.
- `plugins/topology/tbom.h` defines the serializer API.
- `plugins/topology/tbom.c` constructs and orders the graph, computes host and topology fingerprints, and emits JSON.
- `plugins/topology/CMakeLists.txt` links the implementation and mbedTLS SHA-256 dependency.

### 2.3 Specification and design material

- `docs/tbom-profiles.md` defines public profile identity but no identifier derivation.
- `schemas/topology_tbom.v1.schema.json` defines the structural schema.
- `r_and_d/INV-008_IMPLEMENTATION_PLAN.md` contains detailed but non-normative derivation notes; several claims do not match code.
- `docs/linux-edge-target.md` states an operational consecutive-call stability expectation.

### 2.4 Tests and golden evidence

- `tests/test_topology_tbom_golden.c`
- `tests/test_topology_plugin.c`
- `tests/regen_golden.c`
- `tests/CMakeLists.txt`
- `tests/golden/tbom_loopback_only.json`
- `tests/golden/tbom_physical_vlan.json`
- `tests/golden/tbom_bridge_members.json`
- `packaging/validate_linux_edge.sh`

The unrelated `node_id` occurrence in `src/contract_event.c` belongs to ContractEvent metadata, not the Edge topology profile.

## 3. Complete current execution path

```text
ubus: invaros.topology discover
    -> src/ubus.c:send_discover()
    -> function pointer installed by src/main.c
    -> plugins/topology/topology_plugin.c:topology_discover()
    -> calloc zeroed topo_snapshot_t
    -> plugins/topology/netlink_discover.c:netlink_discover()
       -> time(NULL)
       -> RTM_GETLINK
       -> RTM_GETADDR
       -> RTM_GETROUTE
       -> RTM_GETNEIGH
       -> topo_compute_canonical_ids()
    -> plugins/topology/tbom.c:tbom_serialize()
       -> classify nodes
       -> sort nodes
       -> construct and sort edges
       -> serialize graph
       -> SHA-256(graph bytes) -> topology_fingerprint
       -> hash physical IDs -> host_fingerprint
       -> serialize root document
    -> ubus response: {"tbom":"<escaped JSON string>"}
```

The four Netlink dumps are sequential, not an atomic kernel snapshot.

## 4. Current node ID derivation

The output calls the field `graph.nodes[].id`; internally it is `canonical_id`. All hashes use SHA-256 and lowercase 64-character hexadecimal output.

### 4.1 Classification used for identity

An interface is considered physical when:

```text
kind is empty AND mac is non-empty
```

This is a heuristic, not hardware-backed classification.

### 4.2 Physical interface

```text
id = SHA-256(name + ":" + mac)
```

Inputs:

- `IFLA_IFNAME`, stored in the Linux `IFNAMSIZ`-sized field.
- `IFLA_ADDRESS`, only when exactly six bytes.
- MAC formatted as lowercase `xx:xx:xx:xx:xx:xx`.

Not included:

- `ifindex`
- hardware bus path
- permanent versus current MAC
- driver or device identity
- network namespace
- master or bridge membership
- interface flags

### 4.3 Non-physical interface with `IFLA_LINK` parent

Normal form:

```text
id = SHA-256(kind + ":" + name + ":" + parent_id)
```

Fallback:

```text
id = SHA-256(kind + ":" + name + ":" + decimal(parent_ifindex))
```

The fallback is used not only when the parent is absent, but also when the parent exists and its ID has not yet been computed. The fallback ID is immediately stored and later passes do not recompute it. Netlink enumeration order can therefore decide whether the ID contains a parent hash or an ephemeral `ifindex`.

### 4.4 Non-physical interface without parent

```text
id = SHA-256(kind + ":" + name)
```

Consequences:

- A bridge ID is normally derived from `bridge:<name>`.
- A VLAN ID does not directly include its VLAN tag.
- A virtual interface's own MAC does not participate.
- Unknown virtual kinds use the same generic construction.

### 4.5 Neighbor

```text
id = SHA-256("neigh:" + mac + ":" + ip)
```

Inputs are a six-byte neighbor MAC and the textual IPv4 or IPv6 result from `inet_ntop`.

Not included:

- containing interface
- address family as a typed field
- neighbor state
- network namespace

The same IP/MAC pair observed on two interfaces receives the same ID and may be emitted twice.

### 4.6 Preimage ambiguity

The Profile 3 hash inputs use untyped delimiter concatenation. They have no algorithm version, domain separator, length prefix, or typed missing-value representation. Names containing delimiter characters can create semantic ambiguity even though SHA-256 itself remains collision-resistant.

## 5. Current host fingerprint derivation

```text
physical_ids = IDs of every interface classified as node_physical
sort physical_ids lexicographically
host_fingerprint = SHA-256(concatenation of their 64-byte hex strings)
```

If no interface is classified physical:

```text
host_fingerprint = SHA-256(empty string)
```

Because every physical ID contains the interface name and current MAC, this is not solely a hardware fingerprint. An ordinary physical-interface rename changes it. Fixed 64-byte components make the concatenation boundaries unambiguous, but the underlying physical classification and inputs remain unstable.

## 6. Current topology fingerprint derivation

The serializer first produces exactly:

```json
{"edges":[],"nodes":[]}
```

It then computes:

```text
topology_fingerprint = SHA-256(exact graph JSON bytes)
```

### 6.1 Interface-node inputs

- canonical ID
- node type
- sorted IPv4 strings
- sorted IPv6 strings
- current MAC
- MTU
- interface name
- normalized status
- VLAN tag when greater than zero

### 6.2 Neighbor-node inputs

- canonical ID
- IP address
- MAC address
- neighbor node type

### 6.3 Edge inputs

- source ID
- target ID
- relation type

The topology fingerprint changes with interface rename, current MAC change, assigned-address change, MTU change, link status change, VLAN tag change, membership or parent change, neighbor-cache churn, or any node-ID change.

It excludes the observation timestamp, profile metadata, host fingerprint, discovered routes, address prefix lengths and scopes, neighbor NUD state after admission, and interface flags other than their derived status.

## 7. Current interface identity and relationship behavior

Node classification:

- `bridge` -> `node_bridge`
- `vlan` -> `node_vlan`
- selected tunnel kinds -> `node_tunnel`
- empty kind plus non-empty MAC -> `node_physical`
- everything else -> `node_logical`
- neighbor records -> `node_neighbor`

Relationship construction:

1. If `master_ifindex` is set, emit `bridge_member`.
2. Else, if `parent_ifindex` is set, emit `vlan_parent`, `tunnel_parent`, or `logical_parent`.

Because this is `if ... else if`, a link having both relevant relationships emits only its master relationship. Neighbor nodes have no edge to the interface on which they were observed even though the snapshot records their `ifindex`. Routes are parsed but never represented or hashed.

## 8. Current ordering and normalization

### 8.1 Ordering

- Nodes: lexicographic comparison of 64 ID bytes.
- Edges: source, target, relation.
- IPv4 and IPv6 arrays: textual `strcmp`.
- Object keys: manually emitted in lexicographic order.
- Root fields: manually emitted in lexicographic order.
- No insignificant whitespace.

This is a custom implementation layout, not an identified canonicalization standard.

### 8.2 Normalization implemented

- MAC: lowercase colon-separated, only for six-byte addresses.
- IPv4 and IPv6: host `inet_ntop` result.
- Status priority: `IFF_TESTING`, `IFF_DORMANT`, `IFF_UP && IFF_LOWER_UP`, `IFF_UP`, otherwise `UNKNOWN`.
- Integers: normal `snprintf` decimal formatting.
- Addresses: sorted textual strings.
- Hashes: lowercase hexadecimal.

### 8.3 Claimed but not implemented

The R&D plan says all-zero MACs become empty, names are percent-escaped, Netlink sender PID is verified, capacity truncation emits warnings, schema validation occurs, and key ordering is comprehensively tested. The code instead:

- emits `00:00:00:00:00:00` as a non-empty MAC;
- does not perform JSON escaping or percent-escaping;
- does not validate received Netlink kernel origin;
- silently ignores records after fixed capacity;
- does not load the schema in the golden test;
- only spot-checks key presence rather than all object-key ordering.

## 9. Determinism assessment

`tbom_serialize()` is deterministic for an identical, valid snapshot whose IDs have already been computed. The three golden tests establish this narrow property.

Discovery-to-fingerprint reproducibility is not guaranteed because:

- four Netlink dumps are not atomic;
- neighbor cache and link status can change during or between dumps;
- dump order can select parent-ID versus `ifindex` fallback;
- fixed capacities preserve whichever records arrive first;
- dump interruption is not handled through `NLM_F_DUMP_INTR`;
- current network namespace is implicit and unidentified;
- `inet_ntop` is treated as the cross-platform IPv6 canonicalization algorithm;
- raw JSON strings are not escaped;
- equal or colliding IDs have no normative uniqueness or conflict rule.

The accurate claim is: the serializer is deterministic for identical internal inputs; discovery is not guaranteed to construct identical inputs for an unchanged conceptual topology.

## 10. Identifier survival matrix

| Change | Node ID | Host fingerprint | Topology fingerprint |
|---|---|---|---|
| Reboot | Conditional; stable fields usually reproduce, but parent `ifindex`, enumeration order, names, and virtual recreation may differ | Conditional on physical names, MACs, and classification | Not guaranteed because addresses, status, neighbors, and virtual devices may differ |
| Physical-interface rename | Changes | Changes | Changes |
| Logical-interface rename | Changes; descendant IDs may change | Normally unchanged | Changes |
| Physical MAC change | Changes | Changes | Changes |
| Virtual, bridge, or VLAN MAC change | Usually unchanged | Normally unchanged | Changes because MAC is a node property |
| Hardware replacement | Changes when current MAC or name changes; survives if both are cloned | Same behavior in aggregate | Usually changes |
| Virtual-interface recreation | Survives only if kind, name, parent identity, and fallback behavior reproduce | Normally unaffected | Conditional |
| Bridge creation | New `bridge:<name>`-based ID | Normally unchanged | Changes through node and membership edges |
| VLAN creation | New kind/name/parent-based ID; tag absent from ID | Normally unchanged | Changes |
| VLAN tag change without rename | VLAN ID stays the same | Unchanged | Changes |
| Neighbor-cache churn | Same MAC/IP reproduces neighbor ID | Unchanged | Changes as nodes appear or disappear |

## 11. Profile 3 defects and gaps

### 11.1 Implementation defects

1. Order-dependent parent IDs use `ifindex` when a present parent is not yet identified.
2. JSON strings are interpolated without correct escaping.
3. Physical-interface classification is a weak kind/MAC heuristic.
4. All-zero MAC behavior contradicts the design note.
5. Fixed-size truncation is silent.
6. The snapshot is non-atomic across four dumps.
7. Routes are collected but discarded.
8. `IFA_LOCAL` is ignored, producing incorrect point-to-point IPv4 semantics.
9. Neighbor identity lacks interface scope.
10. Master membership suppresses a simultaneous parent edge.
11. Hash preimages are untyped and unversioned.
12. Cryptographic return values are ignored.
13. Address prefix length and scope are captured but not emitted.
14. Neighbor state is used to admit/drop records but not represented.
15. Netlink dump interruption and malformed sender handling are incomplete.

### 11.2 Interoperability defects

- No normative algorithm identifier or version.
- No normative hash-preimage byte representation.
- No standard canonicalization identifier.
- No normative definition of physical, logical, parent, permanent MAC, or current MAC.
- No rule for unavailable inputs, conflicts, or truncation.
- No network-namespace identity.
- No uniqueness or duplicate rules.
- Linux `ifindex`, kernel kind strings, flags, and library address formatting leak into identity.
- An independent producer cannot know which reference quirks are compatibility requirements.

### 11.3 Specification gaps

The public profile document defines only metadata. The schema:

- restricts IDs to lowercase 64-hex strings but not their meaning;
- does not require all emitted profile identity fields;
- does not define array ordering or canonical JSON;
- does not require unique node IDs;
- cannot enforce edge referential integrity;
- does not distinguish structural and operational properties;
- does not define fingerprint inclusion or exclusion;
- does not define completeness or truncation;
- is named `v1` while the profile and legacy TBoM version are `3.0.0`.

### 11.4 Privacy implications

- MAC addresses and common interface names are enumerable despite hashing.
- `host_fingerprint` is a persistent cross-report correlator.
- Raw local and neighbor IP/MAC data exposes network inventory and third-party devices.
- `topology_fingerprint` can identify a recognizable network state.
- Unsalted hashes permit offline guessing and correlation.
- Neighbor cache inclusion leaks recent communication context.
- There is no data-minimization profile, scope salt, identity rotation, or disclosure policy.

### 11.5 Linux/OpenWrt assumptions

- Linux RTNETLINK and Linux UAPI structures.
- Linux `IFLA_LINKINFO` kind strings, `ifindex`, `IFF_*`, NUD, routing, and namespace semantics.
- Six-byte Ethernet MACs.
- Linux `IFNAMSIZ`.
- mbedTLS SHA-256.
- ubus/libubox delivery.
- One current network namespace.
- OpenWrt/router-sized capacity limits.
- A `long` representation suitable for `time_t` emission.

Other operating systems, non-Ethernet links, multi-namespace containers, and dense hosts cannot directly reproduce this discovery model.

## 12. Candidate architectures evaluated

### 12.1 Candidate 1: normatively freeze the current algorithm

Publish the existing formulas, Linux mappings, serializer layout, ordering, fallback behavior, and quirks as a versioned legacy algorithm.

| Criterion | Assessment |
|---|---|
| Determinism | Medium; identical captured inputs reproduce, but discovery and order defects remain |
| Portability | Low; Linux/RTNETLINK-specific |
| Privacy | Low |
| Reproducibility | High only when every quirk and Linux input is reproduced |
| Complexity | Low implementation cost; high specification burden |
| Backward compatibility | Excellent |
| Long-lived specification | Poor |

This is suitable only as a legacy compatibility profile.

### 12.2 Candidate 2: stateless typed content-addressed identity

Define a versioned, platform-neutral identity descriptor for every node type and hash a deterministic, domain-separated, typed encoding. Stable structural inputs participate in node identity; status, addresses, MTU, and neighbor state do not. A standardized canonical graph projection defines the topology fingerprint.

| Criterion | Assessment |
|---|---|
| Determinism | High for equal normalized descriptor sets |
| Portability | Medium to high with platform adapters |
| Privacy | Low to medium; stateless reproduction generally exposes correlatable identity inputs |
| Reproducibility | High |
| Complexity | Medium |
| Backward compatibility | Breaking IDs; dual emission required |
| Long-lived specification | Good if stability classes are explicit |

No stateless observed identifier can simultaneously survive rename, MAC change, and hardware abstraction while remaining portable and independently reproducible.

### 12.3 Candidate 3: dual-plane identity and fingerprint architecture

Separate:

1. Persistent instance identity for object continuity.
2. Semantic identity descriptor for reproducible meaning.
3. Structural topology projection for graph equivalence.
4. Operational observation projection for mutable state.
5. Scoped host identity independent of hardware.

| Criterion | Assessment |
|---|---|
| Determinism | High for semantic and fingerprint planes; instance continuity depends on state |
| Portability | High at the data-model level |
| Privacy | Best; scoped, rotatable instance aliases are possible |
| Reproducibility | High for semantic IDs and fingerprints; opaque instance IDs intentionally differ |
| Complexity | Highest |
| Backward compatibility | Manageable through separate dual publication |
| Long-lived specification | Best |

### 12.4 Recommendation

Candidate 3 is accepted. One stateless hash cannot satisfy all desired properties:

- a name-derived ID cannot survive rename;
- a current-MAC-derived ID cannot survive MAC change;
- a hardware-derived ID cannot be both portable and privacy-preserving;
- a persisted opaque ID cannot be independently reconstructed without shared state;
- a graph fingerprint containing status, addresses, and neighbors cannot represent stable structure.

Profile 3 is retained under Candidate 1 as frozen compatibility behavior. Profile 4 adopts Candidate 3.

## 13. Profile 4 identity and governance

### 13.1 Approved identifier taxonomy

```text
profile_id:
  invaros.tbom.profile.edge_network_topology

profile_version:
  4.0.0

specification_uri:
  https://tbom.yozi.systems/specifications/edge-network-topology/4.0.0

schema_uri:
  https://tbom.yozi.systems/schemas/edge-network-topology/4.0.0/schema.json
```

The three identifier classes are distinct and MUST NOT be conflated:

- `profile_id` identifies the specification family and remains `invaros.tbom.profile.edge_network_topology` across Profile 3 and Profile 4.
- `profile_version` identifies the normative revision within that family.
- Permanent algorithm URIs identify the exact identity or fingerprint algorithm.

All specifications, schemas, registries, and algorithms use permanent HTTPS URIs under the Yozi Systems-controlled `https://tbom.yozi.systems/` authority. Versioned resources are immutable after publication; corrections that change normative behavior require a new versioned URI. Network retrieval is never required to validate an artifact when the referenced definition is already available locally.

Approved Profile 4 algorithm URIs:

```text
https://tbom.yozi.systems/algorithms/edge-network-topology/4.0.0/semantic-id-yozi-tid-v1-sha256
https://tbom.yozi.systems/algorithms/edge-network-topology/4.0.0/topology-fingerprint-yozi-fp-v1-jcs-sha256
https://tbom.yozi.systems/algorithms/edge-network-topology/4.0.0/observation-fingerprint-yozi-fp-v1-jcs-sha256
```

Approved registry roots:

```text
https://tbom.yozi.systems/registries/edge-network/node-types/1
https://tbom.yozi.systems/registries/edge-network/relation-types/1
https://tbom.yozi.systems/registries/edge-network/interface-kinds/1
https://tbom.yozi.systems/registries/edge-network/federation-mechanisms/1
https://tbom.yozi.systems/registries/edge-network/tunnel-parameters/1
https://tbom.yozi.systems/registries/edge-network/reason-codes/1
https://tbom.yozi.systems/registries/edge-network/error-codes/1
https://tbom.yozi.systems/registries/edge-network/disclosure-profiles/1
https://tbom.yozi.systems/registries/edge-network/intent-source-types/1
https://tbom.yozi.systems/registries/edge-network/algorithms/1
```

Yozi Systems is the authoritative owner and change controller for the specification, schemas, registries, algorithm definitions, conformance vectors, errata, and release lifecycle.

### 13.2 Governing invariants

1. Persistent and semantic identity are separate.
2. Persistent IDs are scoped, opaque, stateful, and intentionally not independently derivable.
3. Semantic IDs are stateless and independently reproducible.
4. Topology fingerprints cover structural configuration only.
5. Observation fingerprints cover disclosed mutable runtime state.
6. Host identity does not require hardware.
7. Incomplete projections never receive apparently complete fingerprints.
8. Profile 3 behavior and golden values remain frozen.
9. Consumers dispatch using profile and algorithm identifiers.
10. Declared intent is the only source of structural facts.
11. Observation can support a conformance attestation but cannot alter structural identity or fingerprint availability.

## 14. Artifact-plane definitions

| Plane | Purpose | Persistence | Independently reproducible |
|---|---|---:|---:|
| Persistent instance identity | Tracks a managed object through mutable attributes | Local persisted state | No, intentionally |
| Semantic identity descriptor | Reproducible semantic locator and node type | Stateless | Yes |
| Structural topology | Declared-intent node types and relationships | Derived from a validated declaration | Yes |
| Operational observation | Mutable runtime state | Derived per observation | Yes, for the same disclosed state |
| Host identity | Scoped identity of the producer | Local persisted state | No, intentionally |
| Topology fingerprint | Digest of normalized structural projection | Stateless | Yes |
| Observation fingerprint | Digest of normalized disclosed observation projection | Stateless | Yes |

Persistent instance IDs, host identity, timestamps, evidence, diagnostics, and compatibility fields are excluded from the reproducible fingerprint projections unless a future specification explicitly says otherwise.

### 14.1 Declared-intent authority

The structural plane MUST be built from an explicit declaration supplied by an operator, configuration authority, or deterministic adapter for an authoritative configuration system. RTNETLINK, neighbor caches, routes, packet flow, carrier state, and other observed behavior MUST NOT create structural facts.

Each structural artifact records an `intent_source` containing a permanent source-type registry URI, a non-secret source revision or content fingerprint, and declaration validation status. The source may be a native Profile 4 intent manifest, an OpenWrt UCI configuration translated by a registered adapter, or another registered configuration authority. A translation is acceptable only when it is deterministic, lossless for all identity-affecting fields, and identifies its adapter algorithm URI.

If no complete, valid declaration is available, the producer may still emit identity and observation evidence, but `structural_topology` is unavailable and the topology fingerprint is null. It MUST NOT reconstruct intent from observed links.

### 14.2 Intent-versus-runtime conformance

Conformance is evidence comparing a declared structural node or relationship with observations. Its outcomes are `conformant`, `nonconformant`, `unknown`, and `not_observed`, with reason codes. Conformance results are excluded from the topology fingerprint and included in the applicable disclosure-specific observation projection. A runtime mismatch never changes the declared semantic ID or structural topology fingerprint.

## 15. Persistent identity semantics

### 15.1 Instance identifiers

Every node has a disclosure-scoped `instance_id` represented as a lowercase RFC 9562 UUIDv4. It is generated by a cryptographically secure random source and stored in a producer registry. UUIDv7, counters, timestamps, hardware-derived UUIDs, and content-derived UUIDs are prohibited for canonical instance identity.

Properties:

- stable only within the declared disclosure scope and rotation generation;
- never included in topology or observation fingerprints;
- not expected to match between independent producers;
- never reused for a different object;
- if persistence is unavailable, emitted as ephemeral with no continuity claim.

A producer MUST maintain a private internal registry identity and separate UUIDv4 wire aliases for each disclosure scope so identifiers disclosed to different tenants, organizations, federation contexts, or public contexts are not directly correlatable. An alias record binds the internal identity, disclosure profile, scope identifier, rotation generation, and wire UUID. Scope aliases are excluded from every reproducible fingerprint.

### 15.2 Reconciliation order

1. Authoritative operator or configuration-manager identifier from declared intent.
2. Stable platform object identifier.
3. Persistent device-path or hardware evidence.
4. Tracked runtime lineage such as a rename or namespace move.
5. Conservative composite matching.
6. Otherwise allocate a new instance ID.

If evidence is ambiguous or conflicting, the producer must not guess.

Continuity values:

```text
confirmed
probable
ambiguous
new
ephemeral
```

## 16. Typed, length-delimited semantic preimage

### 16.1 Formula

```text
semantic_id =
  "sha256:" + lowercase_hex(SHA-256(YOZI-TID-v1 record))
```

Every semantic identity is accompanied by:

```text
algorithm = https://tbom.yozi.systems/algorithms/edge-network-topology/4.0.0/semantic-id-yozi-tid-v1-sha256
```

The digest string alone is not an algorithm-dispatch mechanism.

Cryptographic failure produces no semantic ID and invalidates every projection requiring the node.

### 16.2 Binary record

All multibyte integers are unsigned big-endian.

```text
magic             8 octets  ASCII "YOZI-TID"
format_version    uint16    1
domain_length     uint16
domain            domain_length ASCII octets
record_length     uint32
field_count       uint16
fields            field_count fields
```

Each field:

```text
tag               uint16
value_type        uint8
flags             uint8      0 in version 1
value_length      uint32
value             value_length octets
```

Fields occur exactly once in ascending tag order.

| Code | Type | Encoding |
|---:|---|---|
| `0x00` | null | zero length |
| `0x01` | UTF-8 | valid UTF-8 octets |
| `0x02` | bytes | uninterpreted octets |
| `0x03` | uint64 | eight big-endian octets |
| `0x04` | boolean | one octet, `00` or `01` |
| `0x05` | digest | 32 raw digest octets |
| `0x06` | array | count plus typed length-delimited elements |
| `0x07` | record | recursively encoded field record |

Arrays used as sets are sorted by complete encoded element bytes.

### 16.3 Domain separation

```text
https://tbom.yozi.systems/domain/edge-network-topology/4.0.0/node/physical
https://tbom.yozi.systems/domain/edge-network-topology/4.0.0/node/bridge
https://tbom.yozi.systems/domain/edge-network-topology/4.0.0/node/vlan
https://tbom.yozi.systems/domain/edge-network-topology/4.0.0/node/tunnel
https://tbom.yozi.systems/domain/edge-network-topology/4.0.0/node/logical
https://tbom.yozi.systems/domain/edge-network-topology/4.0.0/node/declared-federation-peer
https://tbom.yozi.systems/domain/edge-network-topology/4.0.0/observation/subject
```

### 16.4 Common tags

| Tag | Field | Type |
|---:|---|---|
| 1 | descriptor version `4.0.0` | UTF-8 |
| 2 | node type | UTF-8 |
| 3 | normalized namespace key | UTF-8 |
| 4 | interface name | UTF-8, bytes, or null |
| 5 | semantic type registry value | UTF-8 |

Every declared descriptor field is present. Unavailable optional values use typed null; empty string is not missing. Structural semantic descriptors are encoded only from validated declaration fields. Observation subject descriptors use the separate observation domain and can never be promoted to structural semantic IDs merely because their fields happen to match.

## 17. Node identity by type

For structural node types, every identity-affecting input below MUST come from validated declared intent. Observed values may be attached as conformance evidence but MUST NOT fill missing declaration fields. Missing required declaration fields make the structural projection unavailable under D-18.

### 17.1 Physical

Declared semantic fields:

- tag 100: registered media type: initially `ethernet`, `ieee80211`, `cellular`, or `infiniband`; an unknown type cannot be encoded as generic `other` under D-23;
- tag 101: optional operator/configuration role.

Excluded: current/permanent MAC, bus path, serial, driver, `ifindex`, MTU, addresses, and status.

- Rename: instance ID should survive; semantic ID changes.
- Reboot: instance ID survives if registry reconciliation succeeds.
- MAC change: instance and semantic ID normally survive.
- Replacement: new instance ID when authoritative evidence changes; absent such evidence continuity is probable or new.
- Namespace move: semantic ID changes; tracked instance continuity may survive.
- Privacy: semantic descriptor reveals name/type/namespace but no MAC or serial.

### 17.2 Bridge

Declared fields:

- tag 110: bridge technology, initially `ieee8021-bridge`;
- tag 111: registered structural parameters record.

Membership is represented by edges. Rename changes semantic identity. Membership change preserves bridge semantic identity but changes the topology fingerprint. Recreation continuity requires registry or configuration evidence.

### 17.3 VLAN

Declared fields:

- tag 120: VLAN ID, range `0..4094`;
- tag 121: VLAN protocol EtherType, initially `0x8100` or `0x88a8`;
- tag 122: parent semantic ID as raw 32-byte digest.

Tag, protocol, parent, or rename changes semantic identity. Current VLAN MAC is observation-only. Persistent identity may survive an authoritative reconfiguration; without lineage, structural reconfiguration should create a new instance.

### 17.4 Tunnel

Declared fields:

- tag 130: tunnel kind registry value;
- tag 131: sorted parent/lower-layer semantic IDs;
- tag 132: normalized local configured tunnel endpoint or null;
- tag 133: normalized remote configured tunnel endpoint or null;
- tag 134: non-secret configured key identifier, VNI, or session identifier or null;
- tag 135: destination UDP port or null;
- tag 136: kind-specific registered structural parameters.

Initial registered kinds: `tun`, `tap`, `wireguard`, `gre`, `gre6`, `sit`, `ip6tnl`, `vxlan`, `geneve`, `l2tp`.

Configured encapsulation endpoints are structural and distinct from ordinary assigned interface addresses. Unknown identity-affecting parameters make the topology projection incomplete. Private keys, session keys, preshared secrets, credentials, and raw secret material MUST NOT appear in any descriptor, artifact, or fingerprint preimage. A registered tunnel kind may use a public key or a digest of a disclosed public key as a non-secret configured identifier. WireGuard declared peers use a registered tunnel-parameter extension; handshake timestamps, learned endpoints, counters, reachability, and session state remain observations.

### 17.5 Logical

Declared fields:

- tag 140: logical-kind registry value;
- tag 141: sorted parent semantic-ID array;
- tag 142: registered structural parameters.

Initial registered kinds: `loopback`, `bond`, `team`, `veth`, `dummy`, `macvlan`, `ipvlan`, `vrf`, `dsa-port`.

Bridge, VLAN, and tunnel use dedicated types. Rename, parent, or registered parameter change changes semantic identity. A veth peer relation should be represented when both namespaces are in scope.

### 17.6 Neighbor

Additional fields:

- tag 150: typed attached-subject reference containing either a declared interface semantic ID or an interface observation-subject ID;
- tag 151: address family, 4 or 6;
- tag 152: raw four- or sixteen-byte address;
- tag 153: link-layer bytes or null.

Neighbor identity is interface-scoped. Runtime-discovered neighbors are observation nodes and do not participate in structural topology or its fingerprint. Their IDs use the observation subject domain, not a structural-node domain. When attachment to declared intent is unavailable, the neighboring interface's observation-subject ID provides scope; the producer must not invent a structural semantic ID. Address or MAC change changes the observation subject identity. Persistent neighbor continuity requires explicit management evidence; otherwise a changed locator represents a new observation subject. Neighbor information is highly privacy-sensitive.

### 17.7 Declared federation peer

A declared federation peer is an explicitly configured trusted external system or governance boundary. It is not inferred from ARP, NDP, routing, tunnel handshakes, traffic, DNS, or any other observed behavior.

Declared fields:

- tag 160: permanent federation-mechanism registry URI;
- tag 161: operator-assigned peer key unique within the namespace and declaration authority;
- tag 162: declared trust-domain or federation identifier;
- tag 163: sorted disclosed public endpoint descriptors, which may be empty;
- tag 164: disclosed public-key identifier or certificate fingerprint, or null;
- tag 165: registered non-secret governance parameters.

Allowed structural relations initially include `https://tbom.yozi.systems/registries/edge-network/relation-types/1/federation-pathway` and `https://tbom.yozi.systems/registries/edge-network/relation-types/1/declared-handshake-peer`. These relations express permitted intent, not proof of connectivity or trust establishment. Credentials, private keys, bearer tokens, session keys, and live handshake results are prohibited. Live peer reachability, negotiated identity, certificate validation results, and handshake state are observation/evidence fields.

Rename of the operator peer key changes semantic identity; scope-alias instance continuity may survive an authorized rename. Replacement of the configured trust anchor creates a new semantic identity and normally a new persistent instance unless an authoritative rotation record explicitly links them. Declared peer descriptors are privacy-sensitive and are disclosed only under an authorized structural disclosure policy; a producer lacking required disclosed structural fields MUST emit no topology fingerprint rather than hash undisclosed state.

## 18. Host identity model

Profile 4 must work without CPU, memory, motherboard, MAC, firmware, TPM, or device serial identifiers.

Required portable default:

```text
cryptographically random UUIDv4 persisted locally, with scope-specific UUIDv4 aliases
```

Identity source classes:

| Class | Meaning | Observer reproduction |
|---|---|---:|
| `generated_local` | Random persisted identity | No |
| `operator_provisioned` | Assigned by management authority | Only via shared authority |
| `attested_key` | Bound to cryptographic key evidence | Only if same public evidence is disclosed |
| `hardware_evidence_supported` | Generated/provisioned identity with optional evidence | Host ID itself: no |

Hardware evidence is optional evidence about an identity, never a mandatory identity input. Processor, memory, motherboard, firmware, MAC, machine-id, TPM, secure-element, device-certificate, and serial values MUST NOT define the canonical host identity. Where disclosed, evidence includes its evidence-type registry URI, collection status, verification status, privacy class, and digest or public assertion; secret material is prohibited.

Disclosure scopes:

```text
local
tenant
organization
federation
public
```

Producers MUST maintain unlinkable persisted aliases per scope. Rotation creates a new scoped UUIDv4, increments generation, and discloses a `supersedes` relationship only when policy authorizes correlation. Host rotation never changes topology or observation fingerprints.

Privacy classes:

```text
local_secret
scope_correlatable
public_correlatable
hardware_correlatable
```

Independent observers are not expected to reproduce host identity.

## 19. Structural topology projection

### 19.1 Included

- declared semantic nodes for physical, bridge, VLAN, tunnel, logical, and declared federation-peer entities;
- declared namespace key;
- declared interface name;
- declared interface and node type;
- declared VLAN tag and protocol;
- declared registered tunnel kind, configured endpoints, non-secret identifiers, and structural parameters;
- declared parent relationships;
- declared bridge membership;
- declared tunnel/lower-layer relationships;
- declared veth or other structural peer relationships;
- declared federation pathways and handshake relationships.

Edges reference semantic IDs, never instance IDs.

Intent-source type, source-content fingerprint, adapter algorithm, signatures, and source revision are provenance outside the structural projection. Two independent producers that normalize semantically equivalent valid declarations MUST produce the same topology fingerprint even if their source formats or configuration authorities differ.

### 19.2 Property decisions

| Property | Structural | Reason |
|---|---:|---|
| Interface names | Yes, when declared | Operator-visible structural locator and namespace-local disambiguator; observed current name is evidence |
| Interface types | Yes | Fundamental semantic structure |
| Parent relationships | Yes | Fundamental graph structure |
| Bridge membership | Yes | Fundamental graph structure |
| VLAN tag/protocol | Yes | Segmentation configuration |
| Tunnel relationships | Yes | Overlay structure |
| Registered tunnel endpoints/non-secret key identifiers | Yes | Define configured tunnel; secrets are always prohibited |
| Network namespace | Yes | Same name in another namespace is distinct |
| Runtime neighbors | No | Transient cache-derived state |
| Declared federation peers | Yes | Explicit governance intent, never inferred from discovery |
| Routes | No | Observed forwarding state; intent requires future plane |
| Interface addresses | No | Mutable assignment state |
| Current/permanent MAC | No | Mutable, hardware-specific, privacy-sensitive |
| MTU | No | Mutable parameter, not graph identity |
| Link status | No | Transient runtime state |

A rename intentionally changes semantic identity and topology fingerprint. Persistent instance identity supplies continuity across rename.

The word “declared” is normative. A current interface name, kind, parent, master, VLAN tag, tunnel endpoint, or membership learned only from RTNETLINK belongs to observation and conformance evidence. It cannot be copied into the structural projection in the absence of a valid declaration.

### 19.3 Availability conditions

The topology fingerprint is available only if the complete declared scope is available, the intent declaration and any deterministic translation validate, all declared structural relations resolve, every declared structural node has a semantic ID, no unsupported identity-affecting declared type remains, and structural consistency validation succeeds. Runtime inventory completeness and runtime conformance do not control topology-fingerprint availability.

Required unavailable representation:

```json
{
  "algorithm": "https://tbom.yozi.systems/algorithms/edge-network-topology/4.0.0/topology-fingerprint-yozi-fp-v1-jcs-sha256",
  "availability": "unavailable",
  "error_code": "https://tbom.yozi.systems/registries/edge-network/error-codes/1/structural-projection-unavailable",
  "reason_codes": ["https://tbom.yozi.systems/registries/edge-network/reason-codes/1/declared-intent-incomplete"],
  "value": null
}
```

`reason_codes` is a non-empty, deduplicated, ASCII-sorted array from the permanent reason-code registry. Producers MUST NOT hash partial structural projections.

## 20. Observation projection

### 20.1 Interface state

- current observed interface name and kind;
- observed parent and master relationships;
- observed VLAN and tunnel attributes used only for conformance evidence;
- current link-layer address;
- disclosed permanent link-layer address;
- administrative status;
- operational status;
- carrier state;
- MTU;
- normalized assigned addresses;
- prefix length, scope, flags, and peer address;
- registered mutable adapter state.

Packet/byte counters, temperatures, queue statistics, and uptime are excluded from core 4.0.0 because they cause high-frequency churn without topology-governance value.

### 20.2 Neighbors

- attached interface semantic ID;
- IP family and address;
- link-layer address or null;
- normalized NUD state;
- supported flags and type.

### 20.3 Routes

- family and table;
- destination/prefix;
- gateway or null;
- output interface semantic ID or null;
- metric/priority;
- protocol, scope, and route type;
- preferred source when disclosed;
- canonical multipath next hops.

### 20.4 Binding and disclosure

The observation projection includes the structural topology fingerprint value when available or an explicit null structural binding when unavailable, a permanent `disclosure_profile_id` URI, collection consistency, observation-subject IDs, declared-semantic-ID bindings where established, and intent-versus-runtime conformance results. Timestamps, host identity, persistent instance IDs, retry counts, undisclosed properties, and the producer's fuller private state are excluded. A missing structural fingerprint does not by itself prevent a complete disclosure-scoped observation fingerprint.

An observed object that cannot be unambiguously bound to declared intent receives an `observation_subject_id` derived with the separate YOZI-TID observation domain from its disclosed normalized runtime locator. It does not receive or create a structural semantic ID. Ambiguous bindings are reported and never guessed.

The observation fingerprint binds exactly and only the state disclosed under the named disclosure profile. The `disclosure_profile_id` is inside the hashed projection. Fingerprints generated under different disclosure profiles are not comparable, even when their visible values happen to match. A producer MUST NOT fingerprint undisclosed full state and present the result to a recipient who cannot inspect that state.

Observation-fingerprint availability requires every dataset required by the named disclosure profile to be complete or explicitly permitted as known-empty by that profile. A partial required dataset yields `value: null`, `availability: unavailable`, `error_code: observation_projection_unavailable`, and sorted reason codes.

## 21. Canonicalization and fingerprint envelopes

### 21.1 RFC 8785

Projection objects use RFC 8785 JSON Canonicalization Scheme. Input must be I-JSON-compatible, duplicate object names are invalid, object properties are recursively sorted, invalid Unicode is rejected, and array order is preserved. Profile 4 therefore defines array order before JCS.

### 21.2 Fingerprint formula

```text
fingerprint =
  "sha256:" + lowercase_hex(SHA-256(YOZI-FP-v1 envelope))
```

The artifact carries the applicable permanent algorithm URI next to the value. Topology and observation use different URIs and domains even though both use SHA-256, YOZI-FP-v1, and JCS.

Envelope:

```text
magic             8 octets ASCII "YOZI-FP" followed by 0x00
format_version    uint16, value 1
domain_length     uint16
domain            ASCII
payload_type      uint8, 1 for RFC 8785 UTF-8 JSON
payload_length    uint64
payload           canonical UTF-8 projection bytes
```

Domains:

```text
https://tbom.yozi.systems/domain/edge-network-topology/4.0.0/fingerprint/topology
https://tbom.yozi.systems/domain/edge-network-topology/4.0.0/fingerprint/observation
```

### 21.3 Array ordering

- Structural nodes: semantic ID.
- Structural edges: relation type, source, target.
- Declared federation peers: semantic ID.
- Identity nodes: instance ID.
- Namespaces: namespace key, then namespace instance ID.
- Interface observations: subject semantic ID.
- Addresses: family, raw address, prefix, scope, peer.
- Neighbors: interface semantic ID, family, raw IP, link address, state.
- Routes: table, family, destination, prefix, metric, gateway, output semantic ID.
- Next hops: output semantic ID, gateway, weight.
- Conformance results: declared semantic ID, observation subject ID, check registry URI.
- Set-valued parameters: complete encoded element bytes.

### 21.4 Identifier comparison

UUIDs, algorithm URIs, registry values, and `sha256:` identifiers use lowercase ASCII wire forms. Identifier sorting is unsigned bytewise ASCII comparison.

### 21.5 Address normalization

- IPv4 is held as four bytes and rendered as dotted decimal without leading zeros.
- IPv6 is held as sixteen bytes and rendered under RFC 5952: lowercase, maximal zero compression, first longest run on ties.
- Prefix length is separate.
- IPv6 zone is never embedded as `%zone`; interface/zone scope is separate.
- IPv4-mapped IPv6 remains family 6.
- Duplicates are identified by family, raw address, prefix, scope, and peer.

### 21.6 Link-layer normalization

- EUI-48: six lowercase two-digit hex octets separated by colons.
- EUI-64: eight lowercase two-digit hex octets separated by colons.
- Other addresses: explicit type and lowercase colon-separated octets.
- All-zero address is missing, not identity.
- Current and permanent addresses are distinct.

### 21.7 Namespace normalization

The primary capture namespace has semantic key `root`. Additional namespaces require a unique operator/configuration-supplied portable key. Linux inode, device, path, `ifindex`, and relative namespace ID do not participate in semantic identity. An unnamed namespace lacking a portable key makes the relevant topology projection partial.

### 21.8 Missing and invalid values

- Declared nullable fields appear as JSON `null`.
- Empty arrays mean known empty.
- `null` means unavailable or not applicable and uses a reason where required.
- Empty string is a real value.
- Invalid UTF-8 source bytes are preserved with an unpadded base64url wrapper; they are never replaced or silently discarded.

```json
{"encoding":"base64url","value":"<original bytes>"}
```

Valid text uses:

```json
{"encoding":"utf-8","value":"eth0"}
```

### 21.9 Integers and duplicates

JSON integers are limited to the exact interoperable range `-9007199254740991..9007199254740991`, with narrower field ranges where defined.

- Duplicate JSON property: invalid artifact.
- Exact duplicate normalized record: coalesce only after all field normalization; raw arrival bytes and order are irrelevant.
- Conflicting records with the same normalized identity key: affected projection invalid and fingerprint unavailable.
- Duplicate instance ID: identity failure.
- Different preimages with same semantic digest: cryptographic collision failure.
- Duplicate structural semantic ID: topology fingerprint unavailable.
- Arrival order never resolves conflict.

For source strings, valid UTF-8 is preserved exactly after rejecting non-shortest encodings, surrogate code points, and invalid scalar values. Invalid byte strings are represented by the base64url wrapper before JCS. Unicode normalization such as NFC or NFKC MUST NOT be applied implicitly because it would change original identifiers; configuration authorities that impose normalization must identify that rule in their adapter algorithm.

## 22. Discovery completeness

Dataset statuses:

```text
complete
partial
unsupported
inaccessible
failed
```

Overall statuses:

```text
complete
partial
failed
```

Consistency values:

```text
atomic
generation_validated_sequential
sequential_non_atomic
unknown
```

### 22.1 Required failure treatment

| Condition | Treatment |
|---|---|
| Capacity truncation | Dataset partial with `capacity_truncation`; fingerprint for the affected plane null |
| `NLM_F_DUMP_INTR` | Discard and retry; partial if exhausted |
| `ENOBUFS` or overrun | Discard affected dump and retry; partial if exhausted |
| Partial observed namespace | Observation fingerprint null when required by its disclosure profile; declared topology unaffected |
| Requested inaccessible observed namespace | `inaccessible`; observation fingerprint null when required; declared topology unaffected |
| Incomplete or inaccessible declared-intent namespace | Structural projection unavailable and topology fingerprint null |
| Unsupported type in declared intent | Structural projection partial; topology fingerprint null until a lossless registered mapping exists |
| Unknown observed link kind | Observation diagnostic/partial as required by the disclosure profile; it does not become generic structure or alter a valid declared topology fingerprint |
| Address/route/neighbor failure | Observation fingerprint null; topology may remain valid |
| Observed link-dump failure | Observation fingerprint null; declared topology fingerprint remains available when its declaration is complete and valid |
| Intent-source or declaration validation failure | Topology fingerprint null; observation may remain available |
| Non-atomic collection | Explicit consistency; never claim atomicity |
| SHA/JCS failure | Relevant fingerprint null with reason |
| Semantic-ID failure | Affected projection invalid |
| Invalid UTF-8 | Preserve bytes through wrapper |
| Conflicting records | Partial with `conflicting_records` |

Unavailable fingerprints use `value: null`, `availability: unavailable`, one stable `error_code`, and one or more sorted machine-readable `reason_codes`. `availability` is `available` or `unavailable`; it never implies completeness by omission.

### 22.2 Sequential validation

The Linux/OpenWrt reference producer SHOULD dump links, then addresses/routes/neighbors, then links again. It compares the two normalized observed link views. A match supports `generation_validated_sequential`; it does not claim an atomic operational snapshot. A mismatch yields `sequential_non_atomic`, marks the runtime observation unstable, suppresses the observation fingerprint when the disclosure profile requires stable links, and qualifies any intent-versus-runtime conformance attestation.

The second link dump MUST NOT suppress, invalidate, or change a structural fingerprint derived from complete, valid declared intent. A mismatch means the runtime observation changed; the declared topology continues to exist unchanged.

No incomplete artifact may silently present itself as complete.

## 23. Platform-neutral model and Linux/OpenWrt adapter

The Profile 4 model is platform-neutral. The Linux/OpenWrt producer has two separate adapter paths:

1. An intent adapter reads an explicit Profile 4 intent manifest or deterministically translates a supported authoritative configuration source into declared structure.
2. An observation adapter reads RTNETLINK and other runtime evidence without creating structural facts.

Linux `ifindex`, Netlink attribute numbers, sysfs paths, namespace inodes, kernel flags, and raw kind strings are observation or reconciliation inputs, not structural semantic-identity inputs.

### 23.1 Declared-intent mapping

The normative portable input is a closed Profile 4 intent-manifest object validated against its versioned schema. The manifest declares scope, namespace keys, nodes, structural fields, relationships, federation peers, source revision, and adapter provenance.

The OpenWrt reference intent adapter may translate explicit UCI `network` configuration into that manifest. It MUST:

- identify its permanent translation algorithm URI;
- consume only committed configuration, never inferred traffic or neighbor state;
- map explicitly configured devices, interface names, bridge membership, VLAN IDs/protocols, parents, and tunnel configuration;
- preserve unknown identity-affecting options as an unsupported declaration and suppress the topology fingerprint;
- reject ambiguous or conflicting section resolution;
- never infer missing intent from RTNETLINK;
- emit a normalized source-content fingerprint so the translation is auditable.

Other Linux configuration systems require separately registered deterministic adapters. If multiple authorities claim the same structural key and disagree, the declaration is conflicting and no topology fingerprint is emitted. Runtime-only, DHCP-learned, RA-learned, kernel-created, or application-created state remains observation unless an authoritative declaration explicitly adopts it.

### 23.2 Observed link mapping

| Neutral field | Linux/OpenWrt source |
|---|---|
| Runtime link key | `ifinfomsg.ifi_index`, adapter-internal only |
| Name | `IFLA_IFNAME` raw bytes |
| Current link address | `IFLA_ADDRESS` |
| Permanent link address | `IFLA_PERM_ADDRESS` when present |
| MTU | `IFLA_MTU` |
| Administrative status | `IFF_UP` |
| Operational status | `IFLA_OPERSTATE`, documented fallback |
| Carrier | `IFLA_CARRIER`, documented fallback |
| Parent link | `IFLA_LINK` |
| Master | `IFLA_MASTER` |
| Kind | `IFLA_LINKINFO / IFLA_INFO_KIND` |
| VLAN ID | `IFLA_INFO_DATA / IFLA_VLAN_ID` |
| VLAN protocol | `IFLA_INFO_DATA / IFLA_VLAN_PROTOCOL` |
| Namespace peer | `IFLA_LINK_NETNSID`, only through in-scope namespace map |

`IFLA_PERM_ADDRESS` must not be synthesized from `IFLA_ADDRESS`.

### 23.3 Observed physical classification and declaration binding

1. The validated intent declaration determines structural node type.
2. Observation may bind a runtime interface to that declaration using authoritative configuration lineage or unambiguous reconciliation evidence.
3. A device-backed interface with no recognized virtual kind may be classified as observed physical evidence, but that classification does not create a structural physical node.
4. Permanent address is evidence, not proof.
5. Empty kind plus current MAC is insufficient.
6. Uncertain observed links use an observation-only unknown kind and warning; they are not forced into `logical/other` structure.
7. Observed loopback maps to the observation kind corresponding to `logical/loopback` for conformance comparison.

Sysfs path and hardware evidence may reconcile local instance identity but do not enter semantic identity.

### 23.4 Observed kind mapping

| Linux kind | Profile type |
|---|---|
| `bridge` | bridge |
| `vlan` | VLAN |
| `tun`, `tap`, `wireguard`, `gre`, `gre6`, `sit`, `ip6tnl`, `vxlan`, `geneve` | tunnel |
| `bond`, `team`, `veth`, `dummy`, `macvlan`, `ipvlan`, `vrf` | logical |
| unknown | observation-only unknown kind plus unsupported diagnostic; never guessed as generic structure |

Yozi Systems controls the normative registries.

### 23.5 Observed parent and master

`IFLA_LINK` and `IFLA_MASTER` are independent. The observation adapter emits both applicable observed relationships. Missing referenced links make the observation partial. These relationships are compared with declared relationships for conformance but do not replace them. `ifindex` is never an identity fallback.

### 23.6 Addresses

- Local address is `IFA_LOCAL` when present, otherwise `IFA_ADDRESS`.
- When both exist and differ, `IFA_ADDRESS` is the peer address.
- Prefix comes from `ifa_prefixlen`.
- Scope comes from `ifa_scope`.
- Flags combine `ifa_flags` and `IFA_FLAGS` when available.
- Raw bytes are normalized by Profile 4, not by treating host-library rendering as normative.

### 23.7 Neighbors

- Attachment is `ndm_ifindex` resolved to a declared interface semantic ID when unambiguously bound, otherwise to an interface observation-subject ID.
- Address is `NDA_DST`.
- Link address is `NDA_LLADDR` or null.
- State comes from normalized `ndm_state`.
- Flags and type are observation fields.
- Incomplete/failed entries may be represented, not silently discarded.
- Unresolved attachment makes observation partial.

### 23.8 Routes

Map `rtm_family`, `rtm_table`/`RTA_TABLE`, `RTA_DST`, `rtm_dst_len`, `RTA_GATEWAY`, `RTA_OIF`, `RTA_PRIORITY`, `RTA_PREFSRC`, `rtm_protocol`, `rtm_scope`, `rtm_type`, and `RTA_MULTIPATH`. Output links reference declared semantic IDs when bound and observation-subject IDs otherwise. Unresolved output links make observation partial.

### 23.9 Namespaces

- Open one socket inside each requested namespace.
- Primary socket namespace maps to `root`.
- Additional declared namespaces require configured portable keys; observed namespaces use those keys only after unambiguous binding.
- nsfs `(st_dev, st_ino)` may reconcile runtime instances but is not semantic or reboot-stable.
- `IFLA_LINK_NETNSID` resolves only against the producer's scope map.
- Unrequested namespaces are outside declared scope.
- Requested inaccessible observed namespaces report `inaccessible` without invalidating valid declared structure.

### 23.10 Netlink integrity

The adapter must:

- use `recvmsg`;
- validate source `sockaddr_nl.nl_pid == 0` for kernel-origin replies;
- match sequence numbers;
- reject unrelated multicast/messages;
- validate every header and attribute length;
- parse `NLMSG_ERROR`;
- inspect `NLM_F_DUMP_INTR` on every message, including `NLMSG_DONE`;
- treat overrun, `ENOBUFS`, truncation, or malformed messages as failed attempts;
- retry whole datasets, never continue a partly discarded dump;
- perform the approved second link dump by default unless a documented platform limitation prevents it;
- apply the comparison result only to observation consistency and conformance evidence, never to declared structural fingerprint validity.

The response header's `nlmsg_pid` is a Netlink port ID and is not sufficient sender authentication.

## 24. Approved Profile 4 high-level JSON structure

Phase 0 locks the normative wire shape in `schemas/edge-network-topology/4.0.0/schema.json` and the schema-valid complete host example in `conformance/edge-network-topology/4.0.0/representative-examples.json`. Those files control implementation. The older nested conceptual illustrations retained in sections 24.2 through 24.7 record design evolution only; their short type names and pre-lock field groupings are superseded and MUST NOT be implemented as the Profile 4 wire format.

### 24.1 High-level

```json
{
  "artifact_id": "132cf8a0-d4c8-461d-a26f-61fb199834bc",
  "collection": {},
  "compatibility": {},
  "declared_intent": {},
  "fingerprints": {},
  "generated_at": "2026-07-13T12:00:01Z",
  "host_identity": {},
  "identity_plane": {"nodes": []},
  "observation": {},
  "profile_id": "invaros.tbom.profile.edge_network_topology",
  "profile_version": "4.0.0",
  "schema_uri": "https://tbom.yozi.systems/schemas/edge-network-topology/4.0.0/schema.json",
  "specification_uri": "https://tbom.yozi.systems/specifications/edge-network-topology/4.0.0",
  "structural_topology": {}
}
```

Objects are closed. Extensions require registered extension points or a profile revision.

### 24.2 Superseded conceptual physical example

```json
{
  "continuity": "confirmed",
  "continuity_basis": "platform_device_binding",
  "instance_id": "8fc0f88e-1780-4aac-9d03-bca7f01d163c",
  "persistence": "persistent",
  "semantic_descriptor": {
    "descriptor_version": "4.0.0",
    "interface_name": {"encoding": "utf-8", "value": "eth0"},
    "media_type": "ethernet",
    "namespace_key": "root",
    "node_type": "physical",
    "operator_role": null
  },
  "semantic_id_algorithm": "https://tbom.yozi.systems/algorithms/edge-network-topology/4.0.0/semantic-id-yozi-tid-v1-sha256",
  "semantic_id": "sha256:1111111111111111111111111111111111111111111111111111111111111111"
}
```

### 24.3 Superseded conceptual bridge example

```json
{
  "continuity": "confirmed",
  "continuity_basis": "operator_identifier",
  "instance_id": "011b61f2-dc62-4b80-b9ed-782fb9657cb8",
  "persistence": "persistent",
  "semantic_descriptor": {
    "bridge_parameters": {},
    "bridge_technology": "ieee8021-bridge",
    "descriptor_version": "4.0.0",
    "interface_name": {"encoding": "utf-8", "value": "br-lan"},
    "namespace_key": "root",
    "node_type": "bridge"
  },
  "semantic_id_algorithm": "https://tbom.yozi.systems/algorithms/edge-network-topology/4.0.0/semantic-id-yozi-tid-v1-sha256",
  "semantic_id": "sha256:2222222222222222222222222222222222222222222222222222222222222222"
}
```

### 24.4 Superseded conceptual VLAN example

```json
{
  "continuity": "confirmed",
  "continuity_basis": "operator_identifier",
  "instance_id": "d8586b00-66d8-4112-8744-18f01cb36c48",
  "persistence": "persistent",
  "semantic_descriptor": {
    "descriptor_version": "4.0.0",
    "interface_name": {"encoding": "utf-8", "value": "eth0.10"},
    "namespace_key": "root",
    "node_type": "vlan",
    "parent_semantic_id": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
    "vlan_id": 10,
    "vlan_protocol": 33024
  },
  "semantic_id_algorithm": "https://tbom.yozi.systems/algorithms/edge-network-topology/4.0.0/semantic-id-yozi-tid-v1-sha256",
  "semantic_id": "sha256:3333333333333333333333333333333333333333333333333333333333333333"
}
```

### 24.5 Superseded conceptual neighbor example

```json
{
  "continuity": "new",
  "continuity_basis": "observed_locator",
  "instance_id": "b6100250-b6a5-4825-afbb-9b4cdadf94ea",
  "persistence": "ephemeral",
  "observation_subject_descriptor": {
    "address": "192.0.2.8",
    "address_family": 4,
    "attached_interface_semantic_id": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
    "descriptor_version": "4.0.0",
    "link_layer_address": "02:00:5e:10:00:08",
    "namespace_key": "root",
    "subject_type": "neighbor"
  },
  "observation_subject_id_algorithm": "https://tbom.yozi.systems/algorithms/edge-network-topology/4.0.0/semantic-id-yozi-tid-v1-sha256",
  "observation_subject_id": "sha256:4444444444444444444444444444444444444444444444444444444444444444"
}
```

### 24.6 Superseded conceptual declared federation-peer example

```json
{
  "continuity": "confirmed",
  "continuity_basis": "operator_identifier",
  "instance_id": "82d15ffc-7e48-42ad-9ec0-6c5e98cf9787",
  "persistence": "persistent",
  "semantic_descriptor": {
    "descriptor_version": "4.0.0",
    "federation_id": "partner-federation-a",
    "namespace_key": "root",
    "node_type": "declared_federation_peer",
    "peer_endpoints": [{"host": "peer.example", "port": 443, "transport": "tcp"}],
    "peer_key": "partner-edge-a",
    "peer_kind": "https://tbom.yozi.systems/registries/edge-network/node-types/1/declared-federation-peer",
    "public_key_identifier": "sha256:9999999999999999999999999999999999999999999999999999999999999999"
  },
  "semantic_id_algorithm": "https://tbom.yozi.systems/algorithms/edge-network-topology/4.0.0/semantic-id-yozi-tid-v1-sha256",
  "semantic_id": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
```

### 24.7 Superseded conceptual complete artifact

```json
{
  "artifact_id": "132cf8a0-d4c8-461d-a26f-61fb199834bc",
  "collection": {
    "consistency": "generation_validated_sequential",
    "datasets": [
      {"attempts": 1, "dataset": "links", "namespace_key": "root", "reason_codes": [], "records_emitted": 3, "records_seen": 3, "status": "complete"},
      {"attempts": 1, "dataset": "addresses", "namespace_key": "root", "reason_codes": [], "records_emitted": 1, "records_seen": 1, "status": "complete"},
      {"attempts": 1, "dataset": "neighbors", "namespace_key": "root", "reason_codes": [], "records_emitted": 1, "records_seen": 1, "status": "complete"},
      {"attempts": 1, "dataset": "routes", "namespace_key": "root", "reason_codes": [], "records_emitted": 1, "records_seen": 1, "status": "complete"}
    ],
    "finished_at": "2026-07-13T12:00:00Z",
    "overall_status": "complete",
    "scope": {"completed_namespaces": ["root"], "requested_namespaces": ["root"]},
    "started_at": "2026-07-13T11:59:59Z"
  },
  "compatibility": {"legacy_profile_available": true, "legacy_profile_version": "3.0.0"},
  "fingerprints": {
    "observation": {
      "algorithm": "https://tbom.yozi.systems/algorithms/edge-network-topology/4.0.0/observation-fingerprint-yozi-fp-v1-jcs-sha256",
      "availability": "available",
      "error_code": null,
      "reason_codes": [],
      "value": "sha256:6666666666666666666666666666666666666666666666666666666666666666"
    },
    "topology": {
      "algorithm": "https://tbom.yozi.systems/algorithms/edge-network-topology/4.0.0/topology-fingerprint-yozi-fp-v1-jcs-sha256",
      "availability": "available",
      "error_code": null,
      "reason_codes": [],
      "value": "sha256:5555555555555555555555555555555555555555555555555555555555555555"
    }
  },
  "host": {
    "identity": {
      "generation": 1,
      "host_subject_id": "d53452b5-d629-4ceb-a993-ad10d75a37de",
      "persistence": "persistent",
      "privacy_class": "scope_correlatable",
      "scope": "organization:example",
      "source_class": "generated_local"
    },
    "identity_evidence": []
  },
  "identity_plane": {
    "nodes": [
      {"instance_id": "011b61f2-dc62-4b80-b9ed-782fb9657cb8", "persistence": "persistent", "semantic_id": "sha256:2222222222222222222222222222222222222222222222222222222222222222"},
      {"instance_id": "8fc0f88e-1780-4aac-9d03-bca7f01d163c", "persistence": "persistent", "semantic_id": "sha256:1111111111111111111111111111111111111111111111111111111111111111"},
      {"instance_id": "d8586b00-66d8-4112-8744-18f01cb36c48", "persistence": "persistent", "semantic_id": "sha256:3333333333333333333333333333333333333333333333333333333333333333"}
    ]
  },
  "intent_declaration": {
    "source_content_fingerprint": "sha256:7777777777777777777777777777777777777777777777777777777777777777",
    "source_type": "https://tbom.yozi.systems/registries/edge-network/intent-source-types/1/profile4-manifest",
    "status": "valid"
  },
  "namespaces": [
    {"continuity": "confirmed", "namespace_instance_id": "869006b4-3177-423d-98df-444fdf4bfa9a", "namespace_key": "root"}
  ],
  "observation_state": {
    "collection_consistency": "generation_validated_sequential",
    "disclosure_profile_id": "https://tbom.yozi.systems/registries/edge-network/disclosure-profiles/1/internal-full",
    "interfaces": [
      {
        "addresses": [
          {"address": "192.0.2.1", "family": 4, "flags": [], "peer_address": null, "prefix_length": 24, "scope": "global"}
        ],
        "administrative_status": "up",
        "carrier": true,
        "current_link_layer_address": "02:00:5e:10:00:01",
        "mtu": 1500,
        "operational_status": "up",
        "permanent_link_layer_address": null,
        "declared_semantic_id": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
        "observation_subject_id": "sha256:8888888888888888888888888888888888888888888888888888888888888888"
      }
    ],
    "neighbors": [
      {"address": "192.0.2.8", "family": 4, "interface_semantic_id": "sha256:1111111111111111111111111111111111111111111111111111111111111111", "link_layer_address": "02:00:5e:10:00:08", "observation_subject_id": "sha256:4444444444444444444444444444444444444444444444444444444444444444", "state": "reachable"}
    ],
    "conformance": [
      {"declared_semantic_id": "sha256:1111111111111111111111111111111111111111111111111111111111111111", "observation_subject_id": "sha256:8888888888888888888888888888888888888888888888888888888888888888", "reason_codes": [], "status": "conformant"}
    ],
    "routes": [
      {"destination": "0.0.0.0", "family": 4, "gateway": "192.0.2.254", "metric": 100, "output_interface_semantic_id": "sha256:1111111111111111111111111111111111111111111111111111111111111111", "prefix_length": 0, "protocol": "static", "route_type": "unicast", "scope": "global", "table": 254}
    ],
    "structural_topology_fingerprint": "sha256:5555555555555555555555555555555555555555555555555555555555555555"
  },
  "profile": {
    "profile_id": "invaros.tbom.profile.edge_network_topology",
    "profile_version": "4.0.0",
    "schema_uri": "https://tbom.yozi.systems/schemas/edge-network-topology/4.0.0/schema.json",
    "specification_uri": "https://tbom.yozi.systems/specifications/edge-network-topology/4.0.0"
  },
  "structural_topology": {
    "edges": [
      {"relation_type": "bridge_member", "source": "sha256:1111111111111111111111111111111111111111111111111111111111111111", "target": "sha256:2222222222222222222222222222222222222222222222222222222222222222"},
      {"relation_type": "vlan_parent", "source": "sha256:3333333333333333333333333333333333333333333333333333333333333333", "target": "sha256:1111111111111111111111111111111111111111111111111111111111111111"}
    ],
    "nodes": [
      {"interface_name": {"encoding": "utf-8", "value": "eth0"}, "media_type": "ethernet", "namespace_key": "root", "node_type": "physical", "semantic_id": "sha256:1111111111111111111111111111111111111111111111111111111111111111"},
      {"bridge_technology": "ieee8021-bridge", "interface_name": {"encoding": "utf-8", "value": "br-lan"}, "namespace_key": "root", "node_type": "bridge", "semantic_id": "sha256:2222222222222222222222222222222222222222222222222222222222222222"},
      {"interface_name": {"encoding": "utf-8", "value": "eth0.10"}, "namespace_key": "root", "node_type": "vlan", "parent_semantic_id": "sha256:1111111111111111111111111111111111111111111111111111111111111111", "semantic_id": "sha256:3333333333333333333333333333333333333333333333333333333333333333", "vlan_id": 10, "vlan_protocol": 33024}
    ],
    "projection_id": "invaros.edge_network_topology.structural.v4"
  }
}
```

Repeated illustrative digests are placeholders, not conformance values.

## 25. Profile 3 coexistence and migration

### 25.1 Frozen legacy identity

Profile 3 retains its existing profile identity and exact algorithm behavior. Its approved explicit legacy algorithm identifier is:

```text
https://tbom.yozi.systems/algorithms/edge-network-topology/3.0.0/legacy-reference-sha256-v1
```

The legacy specification documents the implementation exactly, including quirks, without changing graph bytes or fingerprint values.

### 25.2 Dual emission

Required migration behavior:

- emit a complete Profile 3 artifact compatible with existing behavior;
- emit a separate Profile 4 artifact;
- do not insert Profile 4 fields into the Profile 3 document;
- do not rename or reinterpret Profile 3 `topology_fingerprint`;
- a transport envelope may carry both while each artifact stays independently parseable.

For the existing ubus API, the initial migration should preserve `tbom` as Profile 3 and add a versioned Profile 4 retrieval mechanism. Replacing `tbom` with Profile 4 would break legacy consumers.

### 25.3 Consumer dispatch

Consumers dispatch on `profile_id`, `profile_version`, and fingerprint algorithm identifier. Digest length and JSON shape are not dispatch mechanisms.

### 25.4 Compatibility fields

Profile 4 may carry an informational reference to the separately emitted legacy artifact, its legacy fingerprint, and availability marker. Compatibility fields are excluded from Profile 4 fingerprints and MUST NOT embed or reinterpret Profile 3 graph fields.

### 25.5 Deprecation policy

- Profile 3 is a frozen, supported legacy compatibility profile with no scheduled removal date.
- No algorithmic fixes occur under `3.0.0`.
- Editorial/security errata may clarify but not change output.
- Deprecation or removal requires demonstrated ecosystem migration, published notice, a separate explicit Yozi Systems governance decision, and at least two supported major-profile generations.
- Profile 3 golden artifacts are permanent conformance assets.

### 25.6 Transition tests

- Existing Profile 3 golden artifacts remain byte-for-byte unchanged.
- Existing Profile 3 topology fingerprints remain unchanged.
- Profile 4 semantic vectors are reproduced independently.
- RFC 8785 conformance vectors pass.
- Cross-language fingerprint tests agree.
- Rename, reboot, MAC, bridge, VLAN, tunnel, and namespace lifecycle cases.
- Truncation, dump interruption, `ENOBUFS`, malformed sender, and conflict cases.
- Profile 3-only, Profile 4-only, and dual-capable consumer dispatch.
- Production default after Profile 4 conformance is dual emission; tests verify this default and the explicit rollback to `legacy_only`.
- No transition test may regenerate or normalize a Profile 3 golden artifact.

## 26. Phased implementation plan

Phase 0 documentation work has started and the complete draft package listed below exists for operator and independent-implementation review. No production implementation phase has started.

### Phase 0: specification lock

- Convert the approved decision register into normative specification text.
- Prepare draft vocabulary for local review without changing the approved semantics or publishing externally.
- Record every permanent specification, schema, registry, domain, disclosure-profile, and algorithm URI under `tbom.yozi.systems` for later authoritative publication.
- Define the closed intent-manifest contract and authority/adapter provenance model.
- Freeze Profile 3 behavior and golden artifacts.
- Define and register disclosure profiles, reason codes, intent-source types, node types, relation types, interface kinds, and structural parameters.
- Produce language-neutral TLV and fingerprint pseudocode.
- Complete threat, privacy, and interoperability review, including tunnel secrets and federation-peer disclosure.

Rollback: no runtime impact.

Phase 0 draft deliverables created on 2026-07-13:

```text
docs/specifications/edge-network-topology-3.0.0-legacy.md
docs/specifications/edge-network-topology-4.0.0.md
docs/registries/edge-network-node-types.md
docs/registries/edge-network-relation-types.md
docs/registries/edge-network-interface-kinds.md
docs/registries/edge-network-federation-mechanisms.md
docs/registries/edge-network-reason-codes.md
docs/registries/edge-network-error-codes.md
docs/registries/edge-network-disclosure-profiles.md
docs/registries/edge-network-intent-source-types.md
docs/registries/edge-network-tunnel-parameters.md
docs/registries/edge-network-algorithms.md
docs/algorithms/edge-network-yozi-tid-v1.md
docs/algorithms/edge-network-topology-fingerprint-yozi-fp-v1.md
docs/algorithms/edge-network-observation-fingerprint-yozi-fp-v1.md
docs/algorithms/edge-network-profile3-legacy-fingerprint.md
schemas/edge-network-topology/4.0.0/schema.json
schemas/edge-network-topology/4.0.0/intent-manifest.schema.json
schemas/edge-network-topology/4.0.0/structural-projection.schema.json
schemas/edge-network-topology/4.0.0/observation-projection.schema.json
schemas/edge-network-topology/4.0.0/conformance.schema.json
conformance/edge-network-topology/4.0.0/README.md
conformance/edge-network-topology/4.0.0/semantic-identity-vectors.json
conformance/edge-network-topology/4.0.0/fingerprint-vectors.json
conformance/edge-network-topology/4.0.0/validation-vectors.json
conformance/edge-network-topology/4.0.0/representative-examples.json
```

The package is a normative pre-implementation draft, not a published standard or conformance claim. It locks exact YOZI-TID-v1 and YOZI-FP-v1 byte layouts, the frozen Profile 3 legacy URI, permanent registry namespaces, closed schema shapes, synthetic positive vectors, and fail-closed negative vectors. Operator review of the draft lock and independent reproduction of the byte vectors are the exit criteria for Phase 0. The next implementation milestone is Phase 1, beginning only after those exit criteria are approved.

### Phase 1: pure foundational modules

Proposed new files:

```text
plugins/topology/typed_preimage.c/.h
plugins/topology/jcs.c/.h
plugins/topology/normalize.c/.h
plugins/topology/crypto_digest.c/.h
plugins/topology/profile_v4_model.c/.h
plugins/topology/intent_manifest.c/.h
plugins/topology/registry_uri.c/.h
```

Tests:

```text
tests/test_topology_tlv.c
tests/test_topology_jcs.c
tests/test_topology_normalize.c
tests/test_topology_intent_manifest.c
tests/test_topology_registry_uri.c
```

Rollback: unused modules; Profile 3 unchanged.

### Phase 2: declared-intent and Linux/OpenWrt observation adapters

Proposed files:

```text
plugins/topology/linux_netlink_v4.c/.h
plugins/topology/linux_namespace.c/.h
plugins/topology/discovery_completeness.c/.h
plugins/topology/openwrt_uci_intent.c/.h
plugins/topology/intent_adapter.c/.h
plugins/topology/conformance_compare.c/.h
```

Implement the native intent manifest first, then the registered OpenWrt UCI-to-intent translation. Keep intent and RTNETLINK data structures separate. Add `recvmsg` sender validation, dataset retries, dump-interruption handling, current/permanent MAC separation, `IFA_LOCAL`, routes, scoped neighbors, namespaces, and the approved second observed-link dump. The before/after comparison qualifies observation consistency and conformance only.

Rollback: disable Profile 4 adapters; Profile 3 remains unchanged.

### Phase 3: identity registry

```text
plugins/topology/identity_store.c/.h
plugins/topology/identity_reconcile.c/.h
```

Requirements include atomic durable storage, corruption detection, restrictive permissions, scope aliases, rotation, factory-reset behavior, and ephemeral fallback.

Tests cover restart, rename continuity, replacement, ambiguity, corrupt/unwritable state, and disclosure-scope separation.

Rollback: explicit ephemeral Profile 4 identity or Profile 4 disabled.

### Phase 4: projections and serializer

```text
plugins/topology/semantic_identity.c/.h
plugins/topology/topology_projection.c/.h
plugins/topology/observation_projection.c/.h
plugins/topology/tbom_v4.c/.h
plugins/topology/disclosure_profile.c/.h
plugins/topology/federation_peer.c/.h
```

Tests cover every node type including declared federation peers, declared-intent-only structural construction, observation-subject binding, inclusion/exclusion matrices, disclosure-specific observation fingerprints, ordering, duplicates, missing values, invalid UTF-8, partial fingerprints, second-link-dump instability, tunnel-secret exclusion, and independent verifier agreement.

Rollback: feature gate remains off.

### Phase 5: schema finalization and publication preparation

```text
schemas/edge-network-topology/4.0.0/schema.json
schemas/edge-network-topology/4.0.0/structural-projection.schema.json
schemas/edge-network-topology/4.0.0/observation-projection.schema.json
schemas/edge-network-topology/4.0.0/intent-manifest.schema.json
schemas/edge-network-topology/4.0.0/conformance.schema.json
docs/specifications/edge-network-topology-4.0.0.md
docs/specifications/edge-network-topology-3.0.0-legacy.md
docs/registries/edge-network-node-types.md
docs/registries/edge-network-relation-types.md
docs/registries/edge-network-tunnel-parameters.md
docs/registries/edge-network-federation-mechanisms.md
docs/registries/edge-network-interface-kinds.md
docs/registries/edge-network-reason-codes.md
docs/registries/edge-network-error-codes.md
docs/registries/edge-network-disclosure-profiles.md
docs/registries/edge-network-intent-source-types.md
docs/registries/edge-network-algorithms.md
docs/algorithms/edge-network-yozi-tid-v1.md
docs/algorithms/edge-network-topology-fingerprint-yozi-fp-v1.md
docs/algorithms/edge-network-observation-fingerprint-yozi-fp-v1.md
docs/algorithms/edge-network-profile3-legacy-fingerprint.md
```

Phase 5 promotes the Phase 0 drafts only after implementation feedback and independent-vector reproduction. Publication authority is `tbom.yozi.systems`. Every `$id` and registry/algorithm reference uses its permanent HTTPS URI. Objects are closed by default. JSON Schema cannot express all referential, declaration-provenance, canonicalization, secret-exclusion, registry-membership, and cryptographic constraints, so a fail-closed semantic validator is also required.

Rollback: keep unpublished drafts.

### Phase 6: dual emission

Potential modifications:

- `plugins/topology/topology_plugin.c`
- `include/invarosd/topology.h`
- `src/main.c`
- `src/ubus.c`
- `include/invarosd/ubus.h`
- CMake/test files
- packaging validation
- Linux/OpenWrt documentation

Feature states are `legacy_only`, `dual`, and `v4_only`. The production default after Profile 4 conformance is `dual`; `legacy_only` is the rollback state. Profile 3 and Profile 4 remain separate complete artifacts in every state.

Rollback: `legacy_only`.

### Phase 7: conformance and release

- Never regenerate Profile 3 goldens as part of Profile 4 work.
- Store Profile 4 fixtures separately from expected artifacts.
- Store TLV bytes, JCS bytes, and digests independently.
- Require at least one non-C implementation to reproduce vectors.
- Publish positive and negative vectors.
- Publish vectors for every algorithm URI, declared node type, declared peer, disclosure profile, unavailable-fingerprint condition, invalid UTF-8 form, duplicate/conflict case, unknown declared kind, and stable/unstable sequential observation.
- Require metamorphic tests proving observed MAC, address, MTU, route, neighbor, status, and link-dump instability cannot change a valid declared topology fingerprint.
- Require tests proving declaration changes to names, namespaces, VLANs, parents, bridge membership, tunnel configuration, or declared federation relationships do change the topology fingerprint.
- Gate release on zero Profile 3 golden changes, independent agreement, schema and semantic validation, privacy/security review, and tested `legacy_only` rollback.

## 27. Final decision register

All D-01 through D-30 decisions are operator-approved and normative implementation inputs. D-15, D-18, and D-20 include the operator modifications recorded below. No decision remains pending.

| ID | Final approved choice | Alternatives considered | Trade-off | Wire consequence | Backward consequence |
|---|---|---|---|---|---|
| D-01 | `profile_id` identifies family; `profile_version` identifies normative revision; algorithm URI identifies exact algorithm | New Profile 4 family ID or conflated version/algorithm | Clear three-level dispatch vs more fields | Same family ID, version 4, explicit algorithm URIs | Profile 3 unchanged |
| D-02 | Permanent HTTPS identifiers rooted at `tbom.yozi.systems` for specifications, schemas, registries, and algorithms | URNs or short tokens | Authority/discoverability vs verbosity | Immutable versioned URI strings | None |
| D-03 | UUIDv4 persistent instance IDs | UUIDv7, counters, hash IDs | Avoids time/hardware leakage; needs CSPRNG | Lowercase UUID | V4 only |
| D-04 | Scope-specific instance aliases | One global ID | Privacy vs registry complexity | Scope/generation fields | None |
| D-05 | Exclude instance IDs from fingerprints | Include them | Independent reproduction vs instance binding | Semantic references in projections | Required for cross-producer equality |
| D-06 | SHA-256 semantic IDs with YOZI-TID-v1 | JCS-only, UUIDv5, SHA-512 | Typed rigor/existing dependency vs encoder complexity | `sha256:` plus algorithm URI | V3 separate |
| D-07 | RFC 8785 projection canonicalization | Custom JSON or deterministic CBOR | Broad support vs number constraints | JCS bytes | Intentional V4 break |
| D-08 | Domain-separated fingerprint envelope | Hash JCS directly | Domain safety vs complexity | YOZI-FP-v1 algorithm | No V3 change |
| D-09 | Include interface name structurally | Exclude it | Reproducible disambiguation vs rename churn | Name in structural projection | V4 rename changes hash |
| D-10 | Exclude MAC structurally | Include permanent MAC | Privacy/portability vs hardware continuity | MAC only in observations/evidence | V4 differs intentionally |
| D-11 | Include namespace key structurally | Ignore or use inode | Correct scope vs labeling requirement | Namespace in every descriptor | None |
| D-12 | Require configured extra-namespace keys | Hash inode/path | Portability vs automatic discovery | Unkeyed namespace makes partial | None |
| D-13 | VLAN tag/protocol/parent in semantic identity | Treat tag as observation | Correct semantics vs reconfiguration identity change | Required VLAN fields | V4 only |
| D-14 | Declared tunnel existence, configured endpoints, public/non-secret identifiers, and registered configuration are structural; runtime state and secrets are not | Observation-only tunnel configuration | Correct declared overlay identity vs disclosure sensitivity | Registered structural tunnel fields; secret material prohibited | V4 only |
| D-15 | Runtime neighbors are observation-only; separately declared federation peers and permitted relationships are structural | Structural runtime neighbors or no peer model | Separates discovery from trust intent | Declared federation-peer node and relation registry entries | V4 topology more stable and expressive |
| D-16 | Routes observation-only | Static or all routes structural | Clear portable rule vs configured intent loss | Routes in observation | Future intent plane possible |
| D-17 | Addresses, MTU, MAC, status observation-only | Configured subset structural | Stable graph vs configuration sensitivity | Separate observation state | V4 only |
| D-18 | Complete required structural data or no topology fingerprint | Hash partial with flag | Prevent false equivalence vs availability | `value:null`, availability, stable error code, and specific reason codes | None |
| D-19 | Permit labeled sequential observation fingerprint | Require atomic or suppress | Utility vs exact-instant semantics | Consistency in projection | None |
| D-20 | Second link dump assesses observed runtime stability and qualifies observation/conformance only; it never suppresses valid declared structure | Single dump or using runtime stability to gate topology | Honest runtime evidence without plane conflation | Observation consistency and reason codes | None |
| D-21 | Preserve invalid name bytes through base64url | Reject or replace | Fidelity vs complexity | Encoding/value object | V4 only |
| D-22 | Coalesce only exact normalized duplicates; conflicting same-key records invalidate the affected projection | First/last wins | Determinism vs availability | Conflict reason and unavailable fingerprint | None |
| D-23 | Unknown identity-affecting declared kinds make structure partial; unknown observed kinds remain explicit observation diagnostics and are never promoted to generic structure | Generic opaque structural kind | Standards integrity vs availability on new systems | Topology null only when declaration cannot be modeled; observation qualification otherwise | None |
| D-24 | Host identity defaults to random persisted UUID | Hardware hash, machine-id, MAC aggregate | Portable/privacy-safe vs non-reproducible | Scoped host identity | V4 replaces v3 concept only |
| D-25 | Hardware identity optional evidence | Mandatory hardware fingerprint | Portability vs stronger attestation | Optional evidence array | None |
| D-26 | Separate exact Profile 3 and Profile 4 artifacts | Hybrid or in-place upgrade | Compatibility vs transport complexity | Dual artifact transport | Preserves V3 hashes/goldens |
| D-27 | Freeze Profile 3 quirks normatively | Repair Profile 3 | Compatibility vs cleanliness | Legacy algorithm URI | Essential for existing hashes |
| D-28 | Dual emission default after conformance | V4 opt-in or V4-only | Migration visibility vs resources | Both artifacts available | Safest transition |
| D-29 | No scheduled Profile 3 removal yet | Fixed sunset | Stability vs cleanup | No immediate wire effect | Avoids premature breakage |
| D-30 | Observation fingerprints bind only exact disclosed state under a permanent named disclosure profile | Hash undisclosed full state | Recipient verifiability vs cross-policy comparison | Disclosure-profile URI is inside the hashed projection | None |

### 27.1 Architecture-review outcome

The complete decision set is internally consistent after the modified D-20 wording. The review produced these mandatory safeguards:

- D-09 applies to declared interface names; an observed current name is evidence and cannot create structure.
- D-14 never permits private keys, session keys, preshared secrets, credentials, or other secret material in topology.
- D-15 distinguishes explicitly declared federation peers from kernel-discovered neighbors and live handshakes.
- D-18 prevents any partial structural projection from receiving a topology fingerprint.
- D-20 confines double-dump stability to observation and conformance evidence.
- D-21 preserves invalid source bytes through typed base64url values without violating JCS Unicode rules.
- D-22 compares normalized canonical records and never resolves conflicts by arrival order.
- D-23 applies fail-closed structural handling to unknown declared kinds while preserving unknown observed kinds as explicit evidence.
- D-30 makes each observation fingerprint inspectable within its disclosure scope and prevents comparison across profiles.

Implementation is feasible in C11 with bounded storage and streaming SHA-256, but JCS, durable alias registries, declaration translation, namespace traversal, and full Netlink retry logic require dedicated modules and conformance vectors. The accepted choices intentionally increase implementation complexity to gain independent reproducibility, privacy boundaries, fail-closed behavior, and standards longevity.

### 27.2 Per-decision architecture review

| ID | Consistency and unintended consequences | Feasibility and interoperability | Security, migration, standards, and maintenance conclusion |
|---|---|---|---|
| D-01 | Consistent once family, revision, and algorithm are separate; consumers must not dispatch on JSON shape | Straightforward explicit dispatch in all languages | Prevents algorithm confusion; Profile 3 remains unchanged; maintain three independent registries |
| D-02 | Consistent with Yozi Systems governance; permanent URLs must be immutable | Ordinary URI handling, with offline cached definitions permitted | Enables durable citation and registry governance; TLS retrieval is distribution, not validation authority |
| D-03 | UUIDv4 fits continuity without semantics; randomness failure must fail closed | Universally implementable with a CSPRNG | Avoids timestamp/hardware leakage; no Profile 3 effect; standard RFC 9562 representation |
| D-04 | Scope aliases complement rather than replace the private registry identity | Requires durable alias tables and rotation tests | Prevents cross-scope correlation; migration never exposes a global wire ID; added registry maintenance |
| D-05 | Necessary separation of local continuity from reproducible projections | Simplifies cross-producer fingerprint equality | Prevents local identifier leakage; Profile 4 deliberately cannot prove instance sameness through its topology hash |
| D-06 | YOZI-TID and SHA-256 are compatible with typed semantic descriptors | Modest binary encoder complexity; golden byte vectors required | Domain/type separation prevents ambiguity; algorithm URI enables future replacement without reinterpretation |
| D-07 | JCS applies to JSON projections, not TID binary identity records | Libraries exist, but the C reference implementation needs strict I-JSON tests | Removes custom JSON drift; bounded integer and Unicode rules must be maintained as normative constraints |
| D-08 | The envelope composes cleanly with JCS and separate domains | Small encoder and verifier cost | Prevents cross-purpose digest reuse; Profile 3 bytes remain untouched |
| D-09 | Consistent only for declared names; observed names cannot backfill intent | Portable byte-wrapper representation supports Linux names | Rename intentionally changes structure while instance continuity survives; may disclose operator naming and requires policy review |
| D-10 | MAC exclusion is consistent with intent-first structure | Improves equality across hosts and adapters | Reduces correlation and spoofing relevance; MAC evidence remains disclosure-controlled observation |
| D-11 | Namespace key is required to prevent otherwise identical node collisions | Simple once declaration supplies a key | Avoids namespace confusion; adds a declaration requirement but no platform identifier leakage |
| D-12 | Operator keys align with portability; automatic inode/path identity would contradict it | Requires configuration for non-root namespaces | Stable across reboot and platforms; missing keys fail closed instead of guessing |
| D-13 | VLAN tag, protocol, and parent are intrinsic declared semantics | Directly implementable in manifest and UCI adapter | Reconfiguration changes semantic identity predictably; no legacy impact |
| D-14 | Consistent when limited to declared non-secret configuration | Kind-specific registries are feasible but require careful extensions | Private/session keys are prohibited; configured public identifiers and endpoints may be sensitive and require authorized structural disclosure |
| D-15 | Declared peers express intent while runtime neighbors remain evidence | Requires a new node and relation registry plus validators | Prevents discovery from implying trust; migration is Profile 4-only; peer trust results remain evidence |
| D-16 | Excluding routes from core structure avoids confusing kernel state with intent | Route observation mapping is already available on Linux | A future routing-intent extension can version independently; no guessing from route tables |
| D-17 | Operational attributes can be declared configuration yet remain outside core structural equivalence | Simple inclusion/exclusion rules and metamorphic tests | Produces stable topology hashes; observation retains auditable values; later intent extensions require new algorithms |
| D-18 | Directly enforces fail-closed and explicit incompleteness | Requires error and reason registries plus validator checks | Prevents false equivalence; migration consumers must handle null values rather than assume a digest |
| D-19 | Honest sequential evidence is compatible with non-atomic Linux collection | Practical and portable with a consistency enum | Prevents false atomicity claims; disclosure profile determines required datasets |
| D-20 | Modified decision removes the only plane contradiction | Second link dump is feasible with bounded retry/cost policy | Runtime instability affects observation/conformance only; declared topology remains deterministic and maintainable |
| D-21 | Byte wrappers preserve reality while JCS still sees valid Unicode JSON | Requires raw-byte capture and base64url tests | Prevents lossy replacement and cross-language drift; wrappers slightly enlarge wire format |
| D-22 | Normalized exact coalescing is deterministic; conflict selection is prohibited | Requires stable identity keys and canonical-record comparison | Prevents attacker/order-controlled winner selection; reduced availability is intentional fail-closed behavior |
| D-23 | Consistent when declared and observed unknowns are separated | Registry additions are routine; old implementations fail explicitly | Avoids false generic structure and silent standards drift; observed unknowns do not erase declared intent |
| D-24 | Random host identity is distinct from hardware evidence and topology | Same UUIDv4 registry machinery as nodes | Portable across hardware replacement and virtualization; independent observers are intentionally not expected to reproduce it |
| D-25 | Optional evidence strengthens provenance without becoming identity | Extensible evidence array and verifier registry | Avoids mandatory sensitive hardware collection; evidence verification evolves independently |
| D-26 | Separate artifacts prevent mixed semantics | Transport/API work is required but formats remain independently parseable | Preserves every Profile 3 fingerprint; avoids hybrid downgrade and parser ambiguity |
| D-27 | Freezing Profile 3 is consistent with reproducibility despite known defects | Lowest-risk legacy maintenance path | Security errata may document but never mutate legacy bytes; corrections stay in Profile 4 |
| D-28 | Dual default follows directly from separate-artifact migration | Higher CPU/bandwidth/storage cost is bounded and observable | Avoids a flag day; `legacy_only` provides rollback; no silent replacement |
| D-29 | No fixed sunset supports infrastructure stability | Requires long-term regression ownership | Removal remains possible only through explicit evidence-based governance; goldens remain permanent |
| D-30 | Disclosure-specific observation hashes are inspectable and purpose-bound | Requires registered profiles and projection filtering before hashing | Prevents commitments to hidden state and cross-scope comparison; adding a profile never redefines an existing one |

No reviewed decision violates correctness, interoperability, determinism, security, or long-term standards viability with these safeguards. No operator approval remains outstanding.

### 27.3 Verbatim modified operator decisions

The following controlling text is preserved verbatim so later summaries cannot weaken the approved modifications.

#### D-15 Final Decision (Approved with Modification)

Decision: Runtime-discovered neighbors remain observation-only and MUST NOT participate in the structural topology or structural fingerprint.

Modification: Introduce a separate concept of declared federation peers (or another registered structural node type) for trusted external systems. These are explicitly configured entities that participate in the structural topology and may define permitted federation pathways or handshake relationships.

Rationale: Discovery does not establish trust. A kernel neighbor cache reflects recent communication, not architectural intent. Conversely, an operator-declared federation peer represents an intentional governance boundary and therefore belongs in the structural topology.

#### D-18 Final Decision: Approve with Modification

If required structural data is incomplete, conflicting, or unavailable, the producer MUST NOT emit a structural fingerprint. It must emit value: null with a stable machine-readable error_code, one or more specific reason_codes, and an availability status.

This keeps the system fail-closed while still producing a governed, auditable explanation of why no trustworthy fingerprint exists.

#### D-20 Final Decision: Approve with Modification

The Linux/OpenWrt producer SHOULD perform a second link dump to assess whether observed runtime structure remained stable during collection. That result qualifies the observation fingerprint and any intent-versus-runtime conformance attestation.

It MUST NOT suppress or invalidate a structural fingerprint derived from complete, valid declared intent. A mismatch between the two link dumps means the runtime observation is unstable, not that the declared topology ceases to exist.

That preserves the governing rule:

Structure is defined by declared intent, not by observed behavior.

## 28. Accepted publication and governance decisions

The following publication and governance direction is accepted together with the final D-01 through D-30 register:

- Candidate 3, dual-plane identity and fingerprint architecture, is the accepted direction.
- Edge Network Topology Profile 3.0.0 remains a frozen legacy compatibility profile.
- The corrected architecture is Edge Network Topology Profile 4.0.0.
- Existing Profile 3 topology fingerprints must not silently change.
- Both profiles will ultimately be published.
- Yozi Systems is authoritative specification owner and change controller.
- `tbom.yozi.systems` is the intended public specification and schema authority.
- Permanent HTTPS URIs under `tbom.yozi.systems` identify specifications, schemas, registries, and algorithms.
- D-01 through D-30 are approved as recorded in the final decision register.
- Structure is defined by declared intent, not observed behavior.
- Runtime-discovered neighbors remain observation-only; declared federation peers are structural.
- A second link dump qualifies observation and conformance evidence only.
- Profile 4 remains design/specification-only and is not implemented, published, or conformant.
- The Phase 0 normative draft package now records permanent URIs, the frozen Profile 3 compatibility definition, Profile 4 schemas/registries/algorithms, and synthetic conformance vectors.
- The next milestone is operator review and independent reproduction of the Phase 0 lock, followed—only after approval—by Phase 1 pure foundational implementation modules.

## 29. Current status and explicit non-claims

- Profile 3 implementation remains the code currently present in `invarosd`.
- Profile 4 has draft JSON Schemas and normative synthetic vectors, but no production code, final published schema, conformance implementation, deployed artifact, or verified runtime behavior.
- This document does not claim Profile 4 conformance.
- No Profile 3 algorithm or golden fingerprint has been changed by this architecture review.
- No production code has yet been changed for the Profile 4 architecture; this Phase 0 change is documentation, draft schema, registry, algorithm, and synthetic-vector material only.
- No commit or push is part of this review.
- No operator decisions remain unresolved in this architecture revision.

## 30. Phase 0 review result and remaining engineering questions

The Phase 0 review found no contradiction among D-01 through D-30 after applying the final D-20 modification. No wire-format or operator-policy decision remains open in this package. The following non-normative implementation questions remain for the indicated implementation phases and MUST NOT be answered by changing locked wire semantics implicitly:

1. Select or implement the C RFC 8785 encoder and an independent non-C oracle that reproduce the Phase 0 bytes exactly (Phase 1).
2. Define the on-device atomic storage path, permissions, corruption recovery, factory-reset behavior, and upgrade migration for host/node scope aliases (Phase 3).
3. Write version-specific OpenWrt UCI mapping tables and deterministic source-precedence tests for the OpenWrt releases supported by packaging, without using RTNETLINK to fill missing intent (Phase 2).
4. Define the ubus/C API framing by which two separate complete artifacts are returned in `legacy_only`, `dual`, and `v4_only` modes while preserving the existing Profile 3 response byte-for-byte (Phase 6).

These are engineering selections within the approved architecture, not requests to reopen the operator decision register.
