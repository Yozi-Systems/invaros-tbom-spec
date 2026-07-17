# InvarOS Topology Bill of Materials (TBoM)

A Topology Bill of Materials is a deterministic, metadata-only JSON artifact
describing topology: its participants, declared pathways, and profile-defined
fingerprints. This repository contains specification drafts, JSON Schemas,
registries, algorithms, examples, synthetic conformance vectors, and a
reference validator. It does not contain a TBoM producer or runtime.

TBoM means **Topology** Bill of Materials, never “Trust” Bill of Materials.
A TBoM is not by itself a trust assertion, signature, runtime enforcement
mechanism, or proof of authenticity.

## Governance and permanent authority

Yozi Systems is the specification owner and change controller. Permanent
specification, schema, registry, conformance, and algorithm identifiers are
rooted at `https://tbom.yozi.systems/`.

The remediated Edge Profile 4 material is the locked specification baseline.
The `invarosd` reference producer implements Profile 4 and bootstrap discovery,
and corrected local and live qualification has completed. Exact GL-MT3000 SDK
build provenance has not been independently established and must not be
inferred from successful live-device runtime qualification. The independent
RFC 8785 oracle is [pinned here](docs/conformance/rfc8785-independent-oracle.md).

## Current profiles

| Profile | Version | Status | Authoritative material |
| --- | ---: | --- | --- |
| Agentic Topology | 3.0.0 | Existing public draft with schema, example, and validator support | [SPECIFICATION.md](SPECIFICATION.md), [`schemas/agentic/`](schemas/agentic/) |
| Edge Network Topology | 3.0.0 | Frozen legacy compatibility profile; current implementation and fingerprints remain unchanged | [Legacy specification](docs/specifications/edge-network-topology-3.0.0-legacy.md), [legacy algorithm](docs/algorithms/edge-network-profile3-legacy-fingerprint.md), [`schemas/edge-network/`](schemas/edge-network/) |
| Edge Network Topology | 4.0.0 | Reference producer and bootstrap discovery implemented in `invarosd`; corrected qualification completed locally after independent review found the first-live ordering defect | [Profile 4 specification](docs/specifications/edge-network-topology-4.0.0.md), [`schemas/edge-network-topology/4.0.0/`](schemas/edge-network-topology/4.0.0/), [synthetic vectors](conformance/edge-network-topology/4.0.0/) |

Profile 3 and Profile 4 share the Edge profile family identifier but use
different `profile_version` and algorithm identifiers. Consumers must
dispatch on both profile family and version. Profile 4 follows the governing
rule: **structure is defined by declared intent, not by observed behavior**.

## Repository structure

```text
SPECIFICATION.md             Historical 0.1 umbrella draft; Agentic Profile 3
docs/
  specifications/            Edge Profile 3 frozen and Profile 4 draft specs
  algorithms/                Exact language-neutral fingerprint/identity rules
  registries/                Permanent Edge Network registry drafts
  architecture/              Informative design record; not normative
schemas/
  agentic/                   Agentic Profile 3 schema
  edge-network/              Frozen Edge Profile 3 schema
  edge-network-topology/
    4.0.0/                   Closed Profile 4 draft schemas
examples/                    Existing Agentic and Edge Profile 3 examples
conformance/
  edge-network-topology/
    4.0.0/                   Normative synthetic Phase 0 vectors
validator/                   Offline reference schema validator
tests/                       Schema, vector, preservation, and CLI tests
```

The complete architecture plan is retained at
[`docs/architecture/TBOM_EDGE_PROFILE4_ARCHITECTURE_PLAN.md`](docs/architecture/TBOM_EDGE_PROFILE4_ARCHITECTURE_PLAN.md)
as an informative engineering record. Normative requirements are in
`docs/specifications`, `docs/algorithms`, `docs/registries`, and `schemas`.

## Validation and conformance

```console
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .[test]
python -m pytest -q
python validator/validate_examples.py
tbom-validate examples/agentic/*.json examples/edge-network/*.json
```

The pytest suite parses and meta-validates every schema; validates existing
examples and Profile 4 representative data; reconstructs YOZI-TID-v1 and
YOZI-FP-v1 vectors; checks federation separation, fail-closed incomplete
structure, and sequential-observation behavior; locks
Profile 3 assets and fingerprints; and checks UTF-8, Markdown fences,
permanent URIs, and profile dispatch.

The vectors under `conformance/` are synthetic normative inputs, not runtime
captures. A passing validator test does not establish producer conformance.

Profile 4 defines bootstrap discovery for an unknown device. Intent absence produces observation-only evidence, `intent_status: "absent"`, unavailable intent conformance, and a deterministic inactive candidate for operator review. Activated invalid intent still fails closed; observation is never auto-promoted.

Profile 4 distinguishes textual encoded values from binary network protocol
octets: textual fields prefer UTF-8, while IP, route, neighbor, tunnel, and
link-layer address fields always use canonical unpadded base64url.

## Compatibility

Edge Profile 3 is frozen exactly as implemented. Its schema, examples,
serialization quirks, IDs, and fingerprints must not be repaired in place.
Profile 4 is a separate artifact and intentionally changes identity,
canonicalization, completeness, and fingerprint semantics. The approved
migration model is separate dual emission after a producer becomes
conformant; no current producer is claimed to do so.

See the [compatibility policy](docs/compatibility.md),
[profile comparison](docs/profiles.md), and [security guidance](docs/security.md).

## Scope and non-claims

- TBoM artifacts describe topology; they do not enforce it by themselves.
- Profile 4 observation is evidence, not structure.
- Fingerprints provide deterministic integrity naming, not authenticity,
  replay protection, trusted freshness, or absolute downgrade resistance.
- Receipts, commitments, recognition, and transparency are separate artifact
  families.
- The `invarosd` reference runtime implements Profile 4 and bootstrap discovery.
  Its first live artifacts are preserved as non-conformant historical evidence
  after independent review found non-canonical observation array order.

## License

Apache License 2.0. See [LICENSE](LICENSE).
