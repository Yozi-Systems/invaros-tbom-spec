# Security Model

This document describes what TBoM schema validation and structural
fingerprints do and do not guarantee. It is a companion to
[SPECIFICATION.md § 10](../SPECIFICATION.md#10-security-and-forbidden-metadata-requirements)
and is informative; where this document and SPECIFICATION.md disagree,
SPECIFICATION.md governs.

## Forbidden metadata

The Agentic Topology profile's schema forbids the following key names in
every `metadata` object in an artifact — at the artifact level, and inside
every spec, node, and edge that carries its own `metadata` — at any
nesting depth:

```
Q, q, matrix, matrix_values, initial_distribution, distribution,
solver_output, solver_output_vector, edge_list, raw_payload,
private_key, private_key_pem, secret, token, credential,
raw_signature, signature
```

This list is enforced structurally in
[`schemas/agentic/invaros-agentic-topology-tbom-profile.schema.json`](../schemas/agentic/invaros-agentic-topology-tbom-profile.schema.json)
via a `propertyNames` / `not` constraint on every `metadataObject`
definition, so JSON Schema validation alone rejects an artifact that
includes any of these keys anywhere a `metadata` object is permitted.

The Edge Network Topology profile has no `metadata` field at all — its
schema closes every object with `additionalProperties: false` and
enumerates every permitted property explicitly. There is no forbidden-key
list for that profile because there is no open-ended field for forbidden
data to occupy in the first place.

## Why these keys, specifically

The forbidden list falls into two categories:

- **Raw computational/solver internals** (`Q`, `q`, `matrix`,
  `matrix_values`, `initial_distribution`, `distribution`,
  `solver_output`, `solver_output_vector`, `edge_list`, `raw_payload`): a
  TBoM is a structural description, not a computation trace. Allowing
  raw solver state into a TBoM's metadata would turn a small, stable,
  metadata-only artifact into a vector for leaking internal computational
  representations that have no place in a public or semi-public topology
  declaration.
- **Secrets and credentials** (`private_key`, `private_key_pem`, `secret`,
  `token`, `credential`, `raw_signature`, `signature`): a TBoM is not a
  place to carry key material, bearer tokens, or signatures over other
  data. A TBoM MAY be referenced by a separate signing or receipt
  mechanism, but that mechanism's key material and signatures belong in
  that mechanism's own artifact, not embedded in the TBoM's `metadata`.

## Secret exclusion is structural, not a scanning step

The forbidden-key rule is enforced by the schema's shape, not by content
inspection or pattern matching over string values. This means:

- A conformant artifact cannot carry a value *under a forbidden key name*,
  regardless of what that value contains.
- The rule does **not** scan arbitrary string values for secret-shaped
  content (for example, a metadata value that happens to look like a
  token string, but is stored under a non-forbidden key, will still pass
  schema validation). Producers are responsible for not placing sensitive
  data in `metadata` at all, under any key name; the forbidden-key list is
  a floor, not a complete secret-detection system.

## Raw solver-output exclusion

Consistent with [SPECIFICATION.md § 17](../SPECIFICATION.md#17-explicit-scope-limitations),
this specification defines a metadata-only artifact. Neither profile's
schema has any field intended to carry a solver's raw internal output,
intermediate computation state, or any other non-structural computational
artifact. The forbidden-key list above is the explicit enforcement of this
for the Agentic profile's open `metadata` field; the Edge Network
profile's fully closed schema enforces the same property by construction.

## Schema validation

The Agentic Profile 3 schema uses JSON Schema 2020-12, Edge Network Profile
3 uses draft-07, and Edge Network Profile 4 uses 2020-12. These are frozen
per-revision schema choices; consumers select the exact schema by
(`profile_id`, `profile_version`). Schema
validation checks:

- presence of every required field,
- absence of any field not explicitly enumerated (`additionalProperties: false`
  throughout both schemas),
- type, `enum`, `const`, and `pattern` conformance for every field,
- the forbidden-key rule for the Agentic profile's `metadata` objects.

## Structural fingerprints

Bootstrap discovery does not authorize observed state. `candidate_intent` is review material, is explicitly inactive, excludes operational addresses, routes, neighbors, and secret material, and cannot create a structural fingerprint. Only a separately installed, validated governed source can activate declared structure.

Both profiles include a structural fingerprint
(`structural_fingerprint` for Agentic, `topology_fingerprint` for Edge
Network — see [SPECIFICATION.md § 7](../SPECIFICATION.md#7-fingerprint-expectations)
for the exact computation and format of each, which differ between
profiles). A fingerprint lets a consumer detect whether the structural
content of an artifact has changed since it was last observed, without
needing to diff the full document.

A fingerprint is **not** a signature. It carries no claim about who
produced the artifact or whether the artifact is authentic; it only
attests that a given byte sequence hashes to a given value. Anyone who can
construct a valid artifact can also compute a valid fingerprint for it —
that is by design, since fingerprints are a structural-identity mechanism,
not an authenticity mechanism.

## Limitations of schema validation

Schema validation is necessary but not sufficient for the guarantees a
consumer might want from a TBoM artifact. In particular, schema validation
does **not**:

- Verify graph-structural invariants such as acyclicity, reachability, or
  cycle-edge presence (SPECIFICATION.md § 11.4). These require walking the
  declared graph, which JSON Schema cannot express. A consumer that needs
  these properties MUST verify them independently of schema validation.
- Verify that a fingerprint field actually matches the structural content
  it claims to fingerprint. The schema only checks that the fingerprint
  field has the right *format* (a regex-matched hex string); it does not
  recompute the hash. A consumer that depends on fingerprint correctness
  MUST recompute it.
- Verify authenticity, provenance, or that the artifact was produced by
  the system named in `source_framework` / `source_system`. Nothing in
  either schema cryptographically binds an artifact to its claimed
  producer.
- Detect sensitive data placed under a non-forbidden key name (see above).
- Verify anything about runtime behavior. Schema validation operates on a
  single static document; it has no visibility into whether any system
  ever consulted, honored, or enforced the topology the document
  describes.

## Why schema existence is not runtime enforcement

A JSON Schema — even a strict, closed, forbidden-key-enforcing one — only
constrains the shape of a document. It says nothing about:

- whether any runtime system reads TBoM artifacts at all,
- whether a runtime system that does read them actually restricts
  behavior based on what they declare,
- whether an artifact was generated before, during, or long after the
  behavior it purports to describe, or
- whether a producer that could construct a schema-valid artifact chose
  to describe its system's topology accurately.

Runtime enforcement, if a system implements it, is a property of that
system's own code — for example, refusing to proceed unless a valid TBoM
naming a given endpoint is present. That kind of enforcement logic is
entirely outside this specification. This specification defines what a
valid TBoM artifact looks like and what it may claim; it does not, and
cannot, guarantee that any system actually gates behavior on it. See
[SPECIFICATION.md § 9](../SPECIFICATION.md#9-explicit-non-claims) and
[§ 17](../SPECIFICATION.md#17-explicit-scope-limitations) for the full
normative statement of this boundary.
