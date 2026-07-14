# Changelog

All notable changes to this specification repository are documented in
this file. Versioning here tracks the public draft/release status of the
specification repository itself; see
[docs/compatibility.md](docs/compatibility.md) for individual profile
(`profile_version`) versioning.

## [Unreleased] - target 0.2.0

- Defines the required Profile 4 bootstrap intent-state model: absent intent yields a valid observation-only artifact and deterministic inactive candidate, valid intent retains the existing structural/conformance workflow, and invalid activated intent remains fail closed.
- Separates semantically binary network protocol values from textual `encodedValue` fields. IP, route, neighbor, tunnel-endpoint, and link-layer address octets now have one normative canonical-unpadded-base64url representation even when the bytes are valid UTF-8; textual fields retain mandatory UTF-8 preference.

Draft integration of the Edge Network Topology Phase 0 specification lock:

- Closes three deterministic implementation gaps without changing the Profile
  4.0.0 profile identifier: defines closed bridge, VLAN, tunnel, and logical
  interface observation state; defines the exact interface observation-subject
  YOZI-TID descriptor; and assigns tunnel parameters to tags 134 through 136
  by one mandatory mapping. These corrections unblock interoperable runtime
  observation, subject correlation, and tunnel semantic-ID reproduction.
- Updates the normative schemas, registries, algorithms, examples, conformance
  vectors, semantic validator, and independent tests together. Profile 3
  schemas, bytes, fingerprints, and validation behavior are unchanged.

- Records operator approval of the remediated Phase 0 package as the locked
  engineering baseline.
- Pins the independent RFC 8785 truth source to Cyberphone
  `json-canonicalization` commit
  `19d51d7fe467d4706a3ff08adf8a748f29fc21e0` and its Apache-2.0 corpus.
- Defines `sources[].content_fingerprint` over the RFC 8785 source-declared
  content projection, excluding the fingerprint and provenance wrappers, and
  adds independent positive and negative vectors.

- Adds the exact frozen Profile 3 legacy compatibility specification and
  algorithm without changing its schema, examples, bytes, or fingerprints.
- Adds the Edge Network Topology Profile 4.0.0 normative pre-implementation
  draft, registries, algorithms, closed schemas, and synthetic vectors.
- Adds the complete architecture plan as an informative design record.
- Extends validator dispatch to profile ID plus profile version while
  retaining Profile 3 compatibility.
- Packages supported schemas for the installed `tbom-validate` script.
- Adds schema, vector, URI, Markdown, and Profile 3 preservation coverage.
- Resolves independent-review blockers B1 through B8: deterministic encoded
  values, total set/array ordering, parent set semantics, complete parameter
  registries, machine-readable disclosure profiles, tuple-based dispatch,
  modern offline schema referencing, and broad independently reconstructed
  byte/negative vectors.
- Scopes historical non-JCS serialization to Profile 3, defines delegation
  depth, removes normative decision-register dependencies and dangling policy
  references, permits foreign federation trust-domain HTTPS URIs, and adds an
  informative RFC 8342 relationship section.

This entry does not claim publication, Profile 4 producer implementation,
or Profile 4 runtime conformance.

## [0.1.0] - 2026-07-12

Initial public draft release.

This release publishes the InvarOS Topology Bill of Materials (TBoM)
specification as a public draft, containing:

- **SPECIFICATION.md** — the normative specification, using RFC 2119
  terminology, covering the TBoM artifact model, profile identification
  and versioning, canonical serialization and fingerprint expectations,
  explicit non-claims, security and forbidden-metadata requirements,
  validation requirements, and extension rules.
- **Two implemented profiles**:
  - InvarOS Agentic Topology TBoM Profile
    (`invaros.tbom.profile.agentic_topology`, `profile_version 3.0.0`).
  - InvarOS Edge Network Topology TBoM Profile
    (`invaros.tbom.profile.edge_network_topology`, `profile_version
    3.0.0`).
- **JSON Schemas** for both profiles under `schemas/`.
- **Example artifacts** for both profiles under `examples/`.
- **A reference validator** (`validator/validate_examples.py` and the
  `tbom-validate` console script) that dispatches schema validation by
  `profile_id`.
- **Supporting documentation** under `docs/`: profile comparison
  (`profiles.md`), security model (`security.md`), and compatibility
  policy (`compatibility.md`).
- **A pytest suite** covering example validation, missing/unknown
  `profile_id` handling, invalid-artifact rejection, profile dispatch, and
  CLI exit codes.
- **A GitHub Actions workflow** (`.github/workflows/validate.yml`) running
  the test suite and example validator on push and pull request.

This is a draft specification. Both profiles are documented as they exist
today in their reference implementations; no fields were invented for
this release, and no proprietary orchestration, policy, or solver
internals from either reference implementation are represented in the
published schemas. See [SPECIFICATION.md § Explicit non-claims](SPECIFICATION.md#9-explicit-non-claims)
and [§ Explicit scope limitations](SPECIFICATION.md#17-explicit-scope-limitations)
for the boundaries of what this specification does and does not claim.
