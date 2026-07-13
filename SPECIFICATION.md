# InvarOS Topology Bill of Materials (TBoM) Specification

Version: 0.1.0 (public draft)
Status: Draft — see [Specification status](#specification-status)

> Historical umbrella draft. It remains the normative draft for the Agentic
> Profile 3 material it contains. For Edge Network Profile 3 byte-compatible
> behavior, the authoritative draft is
> [the frozen legacy specification](docs/specifications/edge-network-topology-3.0.0-legacy.md).
> Edge Network Profile 4 is defined separately by its
> [Phase 0 normative pre-implementation draft](docs/specifications/edge-network-topology-4.0.0.md).

## 1. Purpose

An InvarOS Topology Bill of Materials (TBoM) is a deterministic, metadata-only
artifact that describes the **structure** of a system's declared topology —
the nodes that participate in it and the pathways declared between them — at
a specific point before or independent of execution.

A TBoM exists to answer one question precisely: *what topology was declared,
and what does its structure hash to?* It intentionally does not answer
broader questions such as whether that topology was honored at runtime,
whether the participants are trustworthy, or whether any execution actually
occurred. Those are the concerns of other, separate artifact families (see
[Section 9, Explicit non-claims](#9-explicit-non-claims)).

This document specifies the TBoM artifact model, the conformance
requirements for artifacts and validators, and two profile families:

- the **InvarOS Agentic Topology TBoM Profile**, describing pre-execution
  agentic AI system topology (agents, tools, and their declared pathways),
  and
- the **InvarOS Edge Network Topology TBoM Profile**. Frozen revision 3
  describes its historical observed interface topology. Revision 4 is governed
  by the rule that declared intent alone defines structure; runtime network
  state is a separate observation projection and cannot create, remove, mutate,
  or suppress a structural fact.

## 2. Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in RFC 2119.

- **TBoM artifact**: a single JSON document conforming to one of the
  profiles defined in this specification, or to a future profile that
  conforms to the rules in [Section 15, Extension rules](#15-extension-rules).
- **Profile**: a concrete, versioned JSON Schema that fully determines the
  shape and required fields of a class of TBoM artifacts.
- **Producer**: any software that generates a TBoM artifact.
- **Consumer**: any software that reads, validates, or acts on a TBoM
  artifact.
- **Node**: a declared participant in a topology (an agent, tool, network
  interface, etc.).
- **Edge**: a declared directed pathway between two nodes.
- **Structural fingerprint**: a deterministic hash computed over the
  structural portion of a TBoM artifact, as defined per-profile in
  [Section 7](#7-fingerprint-expectations).
- **Forbidden metadata**: field names that a TBoM artifact MUST NOT contain,
  as defined in [Section 10](#10-security-and-forbidden-metadata-requirements).

## 3. Conformance Language

This specification defines conformance for two roles:

- A **conformant producer** MUST emit TBoM artifacts that validate against
  the JSON Schema of the profile they claim to implement, MUST populate
  every field required by that profile, and MUST NOT include forbidden
  metadata as defined in Section 10.
- A **conformant consumer** MUST validate an artifact against the schema
  identified by (`profile_id`, `profile_version`) and MUST validate required
  algorithm URIs (or, for legacy artifacts
  lacking `profile_id`, a schema selected through the out-of-band means
  described in [Section 13](#13-backward-compatibility)) before relying on
  any field within it. A conformant consumer MUST NOT infer profile
  membership from `schema_version` or `tbom_version` alone, since those are
  legacy per-profile version markers, not cross-profile discriminators (see
  [Section 6](#6-versioning)).

Conformance to this specification is scoped to the TBoM artifact itself. It
says nothing about the conformance of any producer's or consumer's runtime
behavior outside of TBoM emission and validation.

## 4. TBoM Artifact Model

Every TBoM artifact, regardless of profile, is a single self-contained JSON
document with the following properties:

- It MUST be valid JSON.
- It MUST validate against exactly one profile schema.
- It describes topology as declared or observed at a single point in time;
  it is not a stream, log, or time series.
- It is **metadata-only**: it MUST NOT embed raw solver state, executable
  payloads, or secrets (see Section 10).
- It is **deterministic**: re-serializing the same logical topology using
  the canonical serialization rules in [Section 8](#8-canonical-serialization-expectations)
  MUST produce byte-identical output, and therefore an identical structural
  fingerprint.

A TBoM artifact is composed of:

1. **Identification fields** — which profile the artifact belongs to, and
   which legacy/semantic version markers apply (Section 5).
2. **A structural body** — the nodes, edges, and profile-specific structure
   describing the declared topology.
3. **A structural fingerprint** — a hash over the structural body only
   (Section 7).
4. **Provenance and scope fields** — where relevant, when the artifact was
   produced and what system produced it.
5. **Explicit non-claims** — where the profile provides for it, a
   machine-readable list of things the artifact does not assert (Section 9).

This specification does not define a wrapper or envelope format beyond what
each profile's JSON Schema requires. A TBoM artifact is the JSON document
itself, not a container around it.

## 5. Profile Identification

TBoM artifacts identify their profile using three fields, present in both
profiles defined by this specification:

| Field | Type | Purpose |
| --- | --- | --- |
| `profile_id` | string constant | Machine-readable, globally unique profile discriminator. |
| `profile_name` | string constant | Human-readable profile name. |
| `profile_version` | string constant | Semantic version of the profile schema itself. |

The two profiles defined in this specification use the following identity
values:

| Profile | `profile_id` | `profile_version` |
| --- | --- | --- |
| InvarOS Agentic Topology TBoM Profile | `invaros.tbom.profile.agentic_topology` | `3.0.0` |
| InvarOS Edge Network Topology TBoM Profile | `invaros.tbom.profile.edge_network_topology` | `3.0.0` |
| InvarOS Edge Network Topology TBoM Profile | `invaros.tbom.profile.edge_network_topology` | `4.0.0` |

Consumers MUST dispatch on the tuple (`profile_id`, `profile_version`) and
MUST validate the specification and algorithm URIs required by that revision.
`profile_id` alone is never sufficient to select a schema. Consumers MUST NOT assume that
two artifacts sharing a legacy version string (`schema_version` /
`tbom_version`, see Section 6) belong to the same profile.

Each profile's JSON Schema also declares a **legacy version field** that
predates `profile_id` and remains for compatibility with pre-existing
consumers of that profile (Section 6).

Per each profile's JSON Schema, `profile_id`, `profile_name`, and
`profile_version`, where present, MUST take exactly the constant values
shown above for that profile; a producer MUST NOT emit alternate values for
an artifact claiming to be `3.0.0` of either profile.

## 6. Versioning

Each profile in this specification carries two independent version
concepts:

1. **`profile_version`** — a semantic version (MAJOR.MINOR.PATCH) of the
   profile's schema. This is the version consumers SHOULD use for
   compatibility decisions going forward.
2. **A legacy version field**, retained from before the multi-profile
   `profile_id` scheme existed:
   - The Agentic Topology profile retains `schema_version`, with constant
     value `tbom-v3.0`.
   - The Edge Network Topology profile retains `tbom_version`, with
     constant value `3.0.0`.

These legacy fields are **not** cross-profile discriminators. Both profiles
happen to share the `3.0.0`/`tbom-v3.0` generation marker because they
originated from the same overall artifact generation, but their structural
bodies are completely different and MUST NOT be conflated. This is why
the (`profile_id`, `profile_version`) tuple exists and MUST be used for dispatch (Section 5).

A future profile revision that changes required fields, removes fields, or
changes field semantics MUST increment at least the MINOR version of
`profile_version` and SHOULD increment MAJOR for breaking changes, per the
rules in [Section 14, Validation requirements](#14-validation-requirements)
and [docs/compatibility.md](docs/compatibility.md).

## 7. Fingerprint Expectations

Both profiles carry a structural fingerprint field, but the two profiles
use **different fingerprint string formats**. Consumers MUST NOT assume a
uniform fingerprint format across profiles.

### 7.1 Agentic Topology profile — `structural_fingerprint`

- Format: `sha256:` followed by 64 lowercase hexadecimal characters
  (regex `^sha256:[0-9a-f]{64}$`).
- Computed as the SHA-256 digest of the canonical JSON serialization
  (Section 8) of an object containing exactly `topology_type` and `spec`.
- `tbom_id`, `created_at_utc`, `source_framework`, `source_system`, and the
  top-level `metadata` object are explicitly excluded from the fingerprint
  input: two artifacts describing the same topology structure with
  different identifiers or timestamps MUST produce the same
  `structural_fingerprint`.
- Node and edge order within `spec` is preserved as declared and IS
  significant to the fingerprint. Producers that need fingerprint identity
  across independently constructed artifacts MUST supply nodes and edges in
  a canonical order themselves; this specification does not mandate a
  specific canonical ordering of nodes or edges.

### 7.2 Edge Network Topology profile — `topology_fingerprint`

- Format: 64 lowercase hexadecimal characters, with **no** `sha256:`
  prefix (regex `^[0-9a-f]{64}$`).
- Computed as the SHA-256 digest of the canonical JSON serialization of the
  `graph` object (`edges` and `nodes`) only.
- Node and edge lists MUST be produced in a sorted, deterministic order
  (nodes sorted by `id`; edges sorted by `source`, then `target`, then
  `relation_type`) before serialization, so that the fingerprint is stable
  across repeated observation of the same topology regardless of discovery
  order.

### 7.3 Edge Network Topology profile — `subsystem_identity.host_fingerprint`

- Format: 64 lowercase hexadecimal characters, no prefix.
- Identifies the observing host by its set of physical-interface node IDs,
  independent of which interfaces are up, bridged, or tagged at observation
  time. It is not a structural fingerprint of the topology itself and MUST
  NOT be substituted for `topology_fingerprint`.

### 7.4 General fingerprint rules

- A fingerprint MUST be recomputed by a consumer that needs to rely on
  structural identity; a fingerprint present in an artifact is a claim by
  the producer, not something a consumer verifies for free.
- A structural fingerprint attests to **structure only**. It is not a
  cryptographic signature, is not an attestation of authenticity, and MUST
  NOT be treated as proof that the artifact came from a specific producer.
  See [docs/security.md](docs/security.md) for the security scope of
  fingerprints and schema validation.

## 8. Canonical Serialization Expectations

This section defines the historical canonical form only for the Agentic
Topology 3.0.0 and Edge Network Topology 3.0.0 profiles. It MUST NOT be used
for Profile 4, whose normative algorithm documents require RFC 8785.

Where either Profile 3 specification requires "canonical JSON" (as input
to a fingerprint, or as the recommended distribution form of an artifact),
the following rules apply:

- Object keys MUST be sorted lexicographically by their UTF-8 byte
  sequence.
- The serialization MUST use no insignificant whitespace (compact
  separators: `,` and `:`, no trailing spaces or newlines between tokens).
- The serialization MUST be UTF-8 encoded, with non-ASCII characters
  escaped (`ensure_ascii`-equivalent behavior), so that byte-identical
  output does not depend on platform text encoding defaults.
- `NaN` and `Infinity` MUST NOT appear; producers MUST reject or avoid
  values that would require them.
- Numeric and string formatting otherwise follows standard JSON.

A TBoM artifact distributed for human review (such as the examples in this
repository) MAY be pretty-printed with indentation and key ordering that
still matches the canonical (sorted-key) order, for readability. Whenever a
fingerprint is computed or verified, it MUST be computed over the compact
canonical byte form described above, not over any pretty-printed variant,
since indentation and whitespace differences would otherwise change the
hash.

## 9. Explicit Non-Claims

This specification and both profiles it defines make the following
non-claims explicit and normative:

- A TBoM describes **topology and declared pathways**. It does not describe
  runtime behavior, message content, or execution outcomes.
- A TBoM is **not runtime enforcement** by itself. The existence of a valid
  TBoM artifact says nothing about whether any runtime system consulted it,
  honored it, or enforced any policy derived from it. Runtime enforcement,
  if any, is implemented by systems that consume TBoM artifacts as one
  input among others — it is out of scope for this specification.
- **Receipts, commitments, recognition, and transparency artifacts are
  separate artifact families**, not part of the TBoM artifact model. A
  system MAY produce evidence receipts, commitment records, federation
  recognition records, or transparency attestations that reference a TBoM's
  fingerprint, but those artifacts have their own formats, their own
  guarantees, and their own specifications outside this document. This
  specification defines TBoM artifacts only.
- This specification does **not** claim universal proof of impossibility of
  any kind (e.g., that a described topology is the only topology capable of
  producing some outcome, or that undeclared pathways cannot exist). A TBoM
  is a declaration and a structural fingerprint of that declaration, not a
  formal proof over the space of all possible topologies.
- The Agentic Topology profile's `non_claims` field (Section 11.3) lets a
  producer enumerate additional, artifact-specific non-claims (for example,
  that no agent execution occurred while building the artifact). The
  content of that array is producer-supplied and informative; this
  specification does not fix its vocabulary.
- It is the **Topology** Bill of Materials, never the "Trust" Bill of
  Materials. A TBoM is not a trust artifact, does not encode a trust score,
  and does not attest to the trustworthiness of any node it describes.

## 10. Security and Forbidden-Metadata Requirements

- Every producer MUST exclude secrets, private key material, credentials,
  tokens, and raw solver/model internals from any TBoM artifact. In the
  Agentic Topology profile, this is enforced structurally: every
  `metadata` object (at the artifact level, and at every nested spec,
  node, and edge level) MUST NOT contain any of the following forbidden
  keys, at any nesting depth:

  ```
  Q, q, matrix, matrix_values, initial_distribution, distribution,
  solver_output, solver_output_vector, edge_list, raw_payload,
  private_key, private_key_pem, secret, token, credential,
  raw_signature, signature
  ```

  A conformant producer MUST NOT emit an artifact containing these keys
  anywhere a `metadata` object is permitted, and a conformant consumer's
  schema validation MUST reject artifacts that do.
- The Edge Network Topology profile has no open-ended `metadata` field at
  all — its schema is fully closed (`additionalProperties: false` at every
  level, with an enumerated, fixed set of interface properties). This is
  itself a forbidden-metadata control: there is no field in which arbitrary
  or forbidden data could be smuggled into a conformant artifact of that
  profile.
- Schema validation is necessary but not sufficient for security assurance.
  See [docs/security.md](docs/security.md) for the full treatment of what
  schema validation does and does not guarantee, including why the
  existence of a schema is not, by itself, runtime enforcement.
- Producers MUST NOT rely on TBoM `metadata` fields as a general-purpose
  extension mechanism for data that is sensitive, secret, or intended to be
  interpreted at runtime. `metadata` exists for descriptive, non-sensitive,
  structural annotation only.

## 11. InvarOS Agentic Topology TBoM Profile

Schema: [`schemas/agentic/invaros-agentic-topology-tbom-profile.schema.json`](schemas/agentic/invaros-agentic-topology-tbom-profile.schema.json)
Example: [`examples/agentic/minimal-agentic-topology.json`](examples/agentic/minimal-agentic-topology.json)

### 11.1 Purpose

This profile describes **pre-execution** agentic AI system topology: the
set of agents, tools, and other participants ("nodes") and the declared
pathways between them ("edges"), for one of four supported topology
shapes. It is produced independent of, and prior to, any agent execution.

### 11.2 Required top-level fields

An artifact of this profile MUST include: `schema_version`, `tbom_id`,
`topology_type`, `spec`, `structural_fingerprint`, `created_at_utc`,
`source_framework`, `source_system`, `non_claims`, and `metadata`. The
schema is closed (`additionalProperties: false`); no fields beyond those
enumerated in the schema (including the optional `profile_id`,
`profile_name`, `profile_version`) are permitted.

### 11.3 Field semantics

- `tbom_id` — a non-empty string identifying this specific artifact
  instance. It is excluded from the structural fingerprint (Section 7.1).
- `topology_type` — one of `AcyclicWorkflow`, `DelegationTree`,
  `MarkovNetwork`, `CyclicCollaboration`. Determines which spec shape
  `spec` MUST take.
- `spec` — `null`, or one of the four spec objects described below, whose
  `topology_spec_type` MUST correspond to `topology_type`.
- `created_at_utc` — a non-empty string timestamp of artifact creation.
- `source_framework` / `source_system` — strings identifying the
  originating agent framework and system. These are provenance fields, not
  claims of trust.
- `non_claims` — an array of non-empty strings, each a producer-supplied
  statement of something this artifact does not assert (Section 9). A
  producer SHOULD populate this array; this specification does not require
  specific values.
- `metadata` — an object subject to the forbidden-key rule in Section 10,
  for descriptive annotation only.

### 11.4 Topology spec shapes

All four spec shapes share a common `nodes` (array of Agentic Node) and
`edges` (array of Agentic Edge) structure, plus shape-specific fields and
structural invariants:

| Shape | `topology_spec_type` | Required shape-specific fields | Structural invariants |
| --- | --- | --- | --- |
| Acyclic workflow | `AcyclicWorkflowSpec` | `terminal_node_ids` | Graph MUST be acyclic; every `terminal_node_ids` entry MUST reference an existing node. |
| Delegation tree | `DelegationTreeSpec` | `root_node_id`, `max_depth` (integer ≥ 1) | Exactly one root (in-degree 0); every non-root node MUST have exactly one parent (in-degree 1); graph MUST be acyclic; every node MUST be reachable from the root; actual depth MUST NOT exceed `max_depth`. Depth is the number of directed edges on the unique path from the root; the root has depth 0, and actual depth is the maximum node depth. |
| Markov network | `MarkovNetworkSpec` | `terminal_node_ids`, `max_transitions` (integer ≥ 1) | Cycles are explicitly permitted. Every `terminal_node_ids` entry MUST reference an existing node. |
| Cyclic collaboration | `CyclicCollaborationSpec` | `collaboration_mode`, `max_iterations` (integer ≥ 1), `termination_policy`, `declared_cycles` | Each entry in `declared_cycles` MUST contain at least 2 node IDs, each referencing an existing node, and MUST correspond to an unbroken cycle of edges actually present in `edges` (for `[A, B, C]`, edges `A→B`, `B→C`, `C→A` MUST all exist). |

All four shapes additionally require:

- Node IDs unique within `nodes`.
- Edge IDs unique within `edges`.
- Every edge's `source_node_id` and `target_node_id` MUST reference a node
  present in `nodes`.

A conformant producer MUST enforce these invariants before emitting an
artifact; a conformant consumer performing structural validation beyond
schema conformance SHOULD enforce them as well, since JSON Schema alone
cannot express graph-level invariants such as acyclicity or reachability.

### 11.5 Agentic Node

Required fields: `node_id`, `display_name`, `node_type`, `role`,
`capabilities` (array of strings), `trust_boundary`, `endpoint_uri`
(`null` or non-empty string), `metadata`.

`node_type`, `role`, and `trust_boundary` are free-text strings in this
profile; this specification does not fix their vocabulary. Producers
SHOULD use consistent, documented values within a given source system.

### 11.6 Agentic Edge

Required fields: `edge_id`, `source_node_id`, `target_node_id`,
`edge_type`, `condition`, `context_policy`, `metadata`. `condition` and
`context_policy` MAY be empty strings; they are declared pathway
qualifiers, not executable expressions evaluated by this specification.

## 12. InvarOS Edge Network Topology TBoM Profile

Schema: [`schemas/edge-network/invaros-edge-network-topology-tbom-profile.schema.json`](schemas/edge-network/invaros-edge-network-topology-tbom-profile.schema.json)
Examples: [`examples/edge-network/`](examples/edge-network/)

### 12.1 Purpose

This profile describes **observed** local network interface topology on a
single host: physical, bridge, VLAN, tunnel, and logical interfaces, their
addressing, and the parent/membership relationships between them, plus
directly observed link-layer neighbors. Unlike the Agentic Topology
profile, this profile is a discovery output, not a pre-execution
declaration — it is deterministic but reflects a point-in-time
observation of host state.

### 12.2 Required top-level fields

An artifact of this profile MUST include: `graph`, `subsystem_identity`,
`tbom_version`, `topology_fingerprint`. The schema is closed
(`additionalProperties: false`); no fields beyond those enumerated in the
schema (including the optional `profile_id`, `profile_name`,
`profile_version`) are permitted.

### 12.3 Field semantics

- `graph.nodes` — at least one node, each with a 64-hex-character `id`, a
  `type` from `node_bridge`, `node_logical`, `node_neighbor`,
  `node_physical`, `node_tunnel`, `node_vlan`, and a closed `properties`
  object (`ipv4_addresses`, `ipv6_addresses`, `mac_address`, `mtu`, `name`,
  `status` ∈ `DORMANT`/`DOWN`/`TESTING`/`UNKNOWN`/`UP`, and `vlan_tag`
  (1–4094) when applicable).
- `graph.edges` — each with `source` and `target` node IDs and a
  `relation_type` from `bridge_member`, `logical_parent`, `tunnel_parent`,
  `vlan_parent`.
- `subsystem_identity` — `host_fingerprint` (Section 7.3) and
  `observed_at_epoch` (non-negative integer, Unix epoch seconds).
- `topology_fingerprint` — Section 7.2.

This profile has no `metadata` field and no free-text annotation surface;
see Section 10 for why that is itself a security property.

## 13. Backward Compatibility

- `profile_id`, `profile_name`, and `profile_version` are **additive**
  fields in both profiles' JSON Schemas: they are declared as optional,
  const-valued properties, not as required fields. This preserves validity
  of artifacts produced before the multi-profile `profile_id` scheme
  existed, which carry only the legacy version field (`schema_version` or
  `tbom_version`) and are otherwise structurally identical to `3.0.0`
  artifacts.
- New producers MUST include `profile_id`, `profile_name`, and
  `profile_version` in every artifact they emit. The optionality described
  above exists solely to keep already-issued legacy artifacts valid; it is
  not a license for new producers to omit these fields.
- A consumer operating in an environment where only one profile is ever
  produced MAY validate directly against that profile's schema without
  inspecting `profile_id`. A consumer operating in a multi-profile
  environment MUST use (`profile_id`, `profile_version`) for dispatch and MUST treat an artifact
  lacking `profile_id` as a legacy artifact requiring out-of-band profile
  selection (for example, a consumer configured for a single known legacy
  producer), not as an error by default.
- Neither profile's legacy version field (`schema_version: tbom-v3.0`,
  `tbom_version: 3.0.0`) is expected to change as part of ordinary,
  non-breaking profile evolution; `profile_version` is the field that
  advances. See [docs/compatibility.md](docs/compatibility.md) for the
  full breaking-vs-non-breaking policy.

## 14. Validation Requirements

- A conformant consumer MUST validate a TBoM artifact against the full
  JSON Schema of its profile before relying on any field, including
  `additionalProperties: false` closure, required-field presence, enum and
  pattern constraints, and the forbidden-metadata rule (Section 10).
- JSON Schema validation alone does not verify the graph-structural
  invariants listed in Section 11.4 (acyclicity, reachability, depth
  bounds, cycle-edge presence) or profile-appropriate fingerprint
  correctness (Section 7). A consumer that depends on those properties
  MUST verify them independently; this specification does not require a
  JSON Schema alone to express them, and profile schemas in this
  repository intentionally do not attempt to encode them in schema form.
- The reference validator in this repository
  ([`validator/validate_examples.py`](validator/validate_examples.py) and
  the `tbom-validate` console script) performs JSON Schema validation
  dispatched by (`profile_id`, `profile_version`) and is the normative reference implementation
  of profile dispatch for this specification. It does not implement the
  graph-structural invariants of Section 11.4.
- A consumer MUST reject an artifact whose (`profile_id`, `profile_version`)
  tuple does not match a known profile, and MUST reject an artifact that fails
  schema validation against the schema selected by that tuple.

## 15. Extension Rules

- A new profile MUST define its own `profile_id`, distinct from all
  existing profile IDs, and SHOULD follow the dotted-namespace convention
  `invaros.tbom.profile.<name>` used by the two profiles in this
  specification.
- A new profile MUST define its own JSON Schema, MUST specify its own
  fingerprint field name, format, and computation basis (Section 7 is
  profile-specific by design; there is no cross-profile fingerprint
  format), and SHOULD document its relationship to existing profiles in
  [docs/profiles.md](docs/profiles.md).
- A new profile MUST NOT redefine the meaning of `profile_id`,
  `profile_name`, or `profile_version` when it includes them; it MAY omit
  them only under the same backward-compatibility rationale as Section 13,
  and only for artifacts that predate the profile's own `profile_id`
  introduction.
- Within an existing profile, adding a new **optional** field with
  `additionalProperties` still closed at every other level, or loosening a
  `const`/`enum` constraint to admit new valid values while preserving all
  previously valid values, are the only changes this specification
  considers non-breaking without a MAJOR `profile_version` bump. All other
  changes (removing or renarrowing a field, changing fingerprint
  computation, changing a legacy version field's constant value) MUST be
  treated as breaking. See [docs/compatibility.md](docs/compatibility.md).
- Extensions MUST continue to honor the forbidden-metadata rule (Section
  10) for any new open-ended field they introduce.

## 16. Implementation Guidance

- Producers SHOULD compute the structural fingerprint last, after all
  other structural fields are finalized, using the canonical serialization
  rules in Section 8, and SHOULD treat fingerprint computation as a pure
  function of the structural input with no side effects.
- Producers SHOULD prefer emitting compact canonical JSON directly, and
  reserve pretty-printing for artifacts specifically intended for human
  review (as this repository's examples are); a producer that pretty-prints
  by default should not itself compute fingerprints over that pretty-printed
  form.
- Consumers integrating TBoM validation into a build or CI pipeline SHOULD
  fail closed: treat schema validation failure, unknown `profile_id`, and
  missing `profile_id` (in a multi-profile context) as hard failures rather
  than warnings.
- Consumers SHOULD NOT attempt to reconstruct or infer forbidden metadata
  (Section 10) from adjacent fields; the intent of the forbidden-metadata
  rule is that the excluded data is simply not available in the artifact at
  all.
- Implementations MUST use the canonicalization named by their exact profile
  revision and algorithm URI. Profile 4 uses RFC 8785 and MUST NOT reuse the
  incompatible historical Profile 3 serialization in Section 8.

## 17. Explicit Scope Limitations

This specification defines the TBoM artifact model and its two current
profiles only. It explicitly does not define, and implementations MUST NOT
represent it as defining:

- Any runtime enforcement mechanism, policy engine, or orchestration
  behavior that might consume a TBoM.
- Any cryptographic signing, receipt, commitment, custody, or transparency
  format. Those are separate artifact families outside this document's
  scope (Section 9).
- Any solver, math engine, or internal computational method used by any
  producer. TBoM artifacts are metadata-only outputs; this specification
  says nothing about how a producer internally computes or validates the
  topology it declares.
- Any claim about the trustworthiness, authenticity, or provenance
  verification of the system that produced an artifact, beyond the
  informational `source_framework` / `source_system` fields in the Agentic
  profile. Authenticity, where needed, is the concern of a signing or
  receipt mechanism layered on top of, and outside, this specification.
- A universal proof of impossibility of any kind (Section 9).

## Specification Status

This is a **public draft** (version 0.1.0). It documents two profiles that
have corresponding reference implementations, schemas, and examples in
this repository. Sections of this specification may be clarified or
extended in non-breaking ways as described in Section 15; breaking changes
to either profile will be reflected in a MAJOR `profile_version` bump and
recorded in [CHANGELOG.md](CHANGELOG.md).
