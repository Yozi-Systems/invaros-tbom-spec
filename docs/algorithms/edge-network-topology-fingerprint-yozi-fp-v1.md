# YOZI-FP-v1 Structural Topology Fingerprint

Algorithm URI: `https://tbom.yozi.systems/algorithms/edge-network-topology/4.0.0/topology-fingerprint-yozi-fp-v1-jcs-sha256`  
Status: normative Phase 0 draft

## 1. Projection

The input is a schema-valid structural projection derived solely from complete, valid declared intent. It contains `projection_id`, semantic nodes, and declared relations. It contains no instance IDs, host aliases, timestamps, observations, MAC addresses, assigned addresses, routes, runtime neighbors, MTU, status, or discovery metadata.

Before canonicalization:

- nodes sort by unsigned ASCII comparison of `semantic_id`;
- relations sort by `relation_type`, then `source`, then `target`, then RFC 8785 bytes of the canonically ordered `parameters` array;
- every `parent_semantic_ids` array has set semantics and sorts by decoded
  digest bytes; duplicate parents are invalid;
- every `parameters` array has set semantics and sorts by parameter-ID ASCII
  bytes, then RFC 8785 bytes of `value`; duplicate records are invalid;
- federation `endpoints` has set semantics and sorts by family, raw address
  bytes, transport (`null`, `tcp`, `udp`), then port (`null` before integers);
  duplicate endpoints are invalid;
- arrays inside a registered nested record use the ordering declared by that
  registry entry; version 1 defines no such additional nested-record arrays;
- normalized exact duplicates coalesce;
- conflicting logical records, duplicate semantic IDs with unequal descriptors, unresolved references, unknown types, or invalid parameters make the projection unavailable.

## 2. Envelope

All integers are unsigned big-endian.

| Offset | Size | Field |
|---:|---:|---|
| 0 | 8 | `59 4f 5a 49 2d 46 50 00` (ASCII `YOZI-FP` plus NUL) |
| 8 | 2 | format version `00 01` |
| 10 | 2 | domain length `D` |
| 12 | D | ASCII domain |
| 12+D | 1 | payload type `01` (RFC 8785 UTF-8 JSON) |
| 13+D | 8 | payload length `P` |
| 21+D | P | canonical payload bytes |

Domain:

```text
https://tbom.yozi.systems/domain/edge-network-topology/4.0.0/fingerprint/topology
```

No terminator or trailing byte follows the payload.

## 3. Formula

```text
payload = RFC8785(structural_projection)
envelope = magic || be_u16(1) || be_u16(len(domain)) || domain ||
           0x01 || be_u64(len(payload)) || payload
fingerprint = "sha256:" || lowercase_hex(SHA-256(envelope))
```

The projection MUST satisfy I-JSON, contain no duplicate member names, contain no floating-point number, use integers no larger than 9007199254740991, and have arrays in the required order before RFC 8785. RFC 8785 sorts object properties but never arrays.

## 4. Failure

If declared intent, normalization, registry resolution, referential integrity, canonicalization, or hashing fails, the producer emits no projection and no fingerprint value. It emits an unavailable fingerprint object with the registered primary error and sorted reason-code URIs. Runtime observation failure cannot cause this outcome when declared intent remains complete and valid.

## 5. Pseudocode

```text
function topology_fingerprint(projection):
    validate_closed_structural_schema(projection)
    validate_declared_intent_provenance(projection)
    normalize_and_sort(projection)
    coalesce_exact_duplicates(projection)
    reject_conflicts_and_unresolved_references(projection)
    payload = RFC8785_UTF8(projection)
    domain = ASCII(topology_domain)
    envelope = HEX("594f5a492d465000") || BE16(1) || BE16(len(domain)) || domain ||
               HEX("01") || BE64(len(payload)) || payload
    return "sha256:" || HEX_LOWER(SHA256(envelope))
```
