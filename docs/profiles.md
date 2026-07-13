# Profile Comparison: Agentic Topology and Edge Network Topology

This informative document compares Agentic Profile 3, frozen Edge Network
Profile 3, and draft Edge Network Profile 4. Edge-specific versioned
documents under [`docs/specifications/`](specifications/) govern over the
historical umbrella [SPECIFICATION.md](../SPECIFICATION.md).

## Relationship

The InvarOS Agentic Topology TBoM Profile and the InvarOS Edge Network
Topology TBoM Profile are **independent, sibling profiles** of the same
TBoM artifact model. They:

- share the same top-level artifact concept (a single deterministic,
  metadata-only JSON document describing declared or observed topology,
  with a structural fingerprint over it),
- share the `profile_id` / `profile_name` / `profile_version`
  identification mechanism (SPECIFICATION.md § 5),
- share the general canonical-JSON serialization rules
  (SPECIFICATION.md § 8),

but otherwise describe **completely different kinds of topology**, have
**different required fields**, and use **different fingerprint field names
and formats**. A consumer MUST NOT assume that a field name, enum value,
or fingerprint format from one profile applies to the other. Consumers
dispatch on `profile_id` and `profile_version`; algorithm URIs identify exact
fingerprint behavior.

They happen to both carry a legacy version marker equal to the `3.0.0`
generation (`schema_version: tbom-v3.0` for Agentic, `tbom_version: 3.0.0`
for Edge Network) because both originated from the same overall artifact
generation effort — not because they are the same profile. See
[compatibility.md](compatibility.md) for why this legacy coincidence must
not be relied upon.

## What each profile describes

- **Agentic Topology** describes a **pre-execution declaration**: the
  agents, tools, and other participants in an agentic AI system, and the
  pathways declared between them, before (or independent of) any
  execution. It is produced by a serializer, not by observing a running
  system.
- **Edge Network Topology 3.0.0** describes an **observation**: the network
  interfaces present on a host (physical, bridge, VLAN, tunnel, logical),
  their addressing, and their parent/membership relationships, plus
  directly observed link-layer neighbors, as discovered at a point in
  time. It is frozen legacy compatibility behavior.
- **Edge Network Topology 4.0.0** describes declared structural intent and
  separately disclosed operational observation. It is a Phase 0 draft and
  has no current producer implementation or conformance claim.

Put differently: Agentic Topology answers "what topology was declared for
this agentic system," while Edge Network Topology answers "what network
topology does this host currently have."

## Comparison table

The two Edge revisions are intentionally separate:

| | Agentic 3 | Edge 3 legacy | Edge 4 draft |
| --- | --- | --- | --- |
| `profile_id` | `invaros.tbom.profile.agentic_topology` | `invaros.tbom.profile.edge_network_topology` | `invaros.tbom.profile.edge_network_topology` |
| `profile_version` | `3.0.0` | `3.0.0` | `4.0.0` |
| Structure source | Declared | Observed Linux state | Complete, valid declared intent only |
| Mutable observation | Out of scope | Mixed into graph | Separate observation projection |
| Status | Existing draft | Frozen compatibility | Design/schema/vector draft only |

The detailed comparison below is grounded strictly in the two existing
Profile 3 schemas
([`schemas/agentic/`](../schemas/agentic/), [`schemas/edge-network/`](../schemas/edge-network/)):

| | Agentic Topology 3 | Edge Network Topology 3 |
| --- | --- | --- |
| `profile_id` | `invaros.tbom.profile.agentic_topology` | `invaros.tbom.profile.edge_network_topology` |
| `profile_version` | `3.0.0` | `3.0.0` |
| Legacy version field | `schema_version: "tbom-v3.0"` | `tbom_version: "3.0.0"` |
| Nature of content | Declared, pre-execution structure | Observed host state |
| Structural fingerprint field | `structural_fingerprint` | `topology_fingerprint` |
| Fingerprint format | `sha256:` + 64 lowercase hex | 64 lowercase hex, no prefix |
| Fingerprint scope | `{topology_type, spec}` only (identifiers/timestamps excluded) | `graph` (`nodes` + `edges`) only |
| Graph container | `spec.nodes` / `spec.edges`, nested inside one of 4 spec shapes | `graph.nodes` / `graph.edges`, flat |
| Node identity | `node_id` — free-text string | `id` — 64-hex-character content identifier |
| Node type vocabulary | Free text (`node_type` field, no enum) | Fixed enum: `node_bridge`, `node_logical`, `node_neighbor`, `node_physical`, `node_tunnel`, `node_vlan` |
| Edge/relation type vocabulary | Free text (`edge_type` field, no enum) | Fixed enum: `bridge_member`, `logical_parent`, `tunnel_parent`, `vlan_parent` |
| Topology shape variants | 4: `AcyclicWorkflow`, `DelegationTree`, `MarkovNetwork`, `CyclicCollaboration` | 1 (flat graph; no shape variants) |
| Open-ended `metadata` field | Yes, at artifact/spec/node/edge level, subject to forbidden-key rule | No — schema is fully closed, no free-text annotation surface |
| Explicit non-claims field | Yes — `non_claims` (array of strings) | No |
| Provenance fields | `source_framework`, `source_system`, `created_at_utc`, `tbom_id` | `subsystem_identity` (`host_fingerprint`, `observed_at_epoch`) |
| Cycle handling | Depends on shape: forbidden in `AcyclicWorkflowSpec`/`DelegationTreeSpec`, permitted in `MarkovNetworkSpec`, explicitly declared and checked in `CyclicCollaborationSpec` | N/A — graph has no cycle concept in schema |
| Structural graph invariants | Enforced by the reference implementation's validators, not by JSON Schema (SPECIFICATION.md § 11.4) | Node/edge sort order enforced by the reference implementation for fingerprint stability, not expressed in JSON Schema |

## Interoperability

- The two profiles do not reference or embed one another. An Agentic
  Topology artifact does not contain an Edge Network Topology artifact or
  vice versa, and this specification defines no wrapper format that would
  combine them.
- A system that needs both — for example, to describe both the agentic
  topology of a multi-agent system and the network topology of the hosts
  it runs on — MUST treat the two as separate artifacts, each separately
  validated against its own schema via (`profile_id`, `profile_version`), and MAY correlate
  them out-of-band (for example, by timestamp or by a shared external
  identifier), but this specification does not define a correlation
  mechanism.
- Consumers that accept multiple revisions MUST dispatch on (`profile_id`,
  `profile_version`) before
  attempting to interpret any other field, since field names collide in
  meaning only coincidentally, if at all (e.g., both profiles have a
  `graph`-adjacent node/edge concept, but the Agentic profile's node/edge
  objects are structurally and semantically unrelated to the Edge Network
  profile's).
