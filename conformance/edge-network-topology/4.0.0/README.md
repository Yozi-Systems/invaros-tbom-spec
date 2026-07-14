# Edge Network Topology Profile 4 Conformance Vectors

`bootstrap-vectors.json` normatively distinguishes absent, valid, and invalid intent inputs, including complete and partial observation bootstrap outcomes. Invalid activated intent emits no artifact.

Status: normative synthetic Phase 0 vectors  
Vector-set URI: `https://tbom.yozi.systems/conformance/edge-network-topology/4.0.0/phase0`

These files are deliberately synthetic, language-neutral inputs. They are not runtime captures and are not evidence that the current producer implements or conforms to Profile 4.

- `semantic-identity-vectors.json` locks YOZI-TID-v1 bytes and SHA-256 output.
- `fingerprint-vectors.json` locks RFC 8785 payload bytes, YOZI-FP-v1 envelope bytes, and topology/observation digests.
- `source-content-fingerprint-vectors.json` locks the self-reference-free
  declared-content projection, RFC 8785 bytes, and direct SHA-256 digest.
- `validation-vectors.json` locks fail-closed semantic outcomes, duplicate/conflict behavior, byte wrappers, federation separation, and sequential-observation behavior.
- `representative-examples.json` supplies physical, bridge, VLAN, runtime-neighbor, federation-peer, and complete-artifact examples.
- `observation-order-vectors.json` locks every observation collection order,
  including divergent mixed bound/unbound neighbor and route cases that prove
  the two nullable interface references are separate ordering levels.

An implementation test harness MUST parse the JSON without rewriting strings, decode hex/base64url exactly, independently reconstruct preimages, and compare every expected byte/digest. Semantic-validation vectors may contain intentionally schema-valid but semantically invalid controlled values; their `expected` object is normative.
