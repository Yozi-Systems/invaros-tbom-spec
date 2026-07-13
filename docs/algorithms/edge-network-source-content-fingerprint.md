# Declared-Intent Source Content Fingerprint

Algorithm URI: `https://tbom.yozi.systems/algorithms/edge-network-topology/4.0.0/source-content-fingerprint-rfc8785-sha256`  
Status: normative and locked for Profile 4.0.0  
Owner: Yozi Systems

## 1. Output

```text
content_fingerprint = "sha256:" || lowercase_hex(SHA-256(content_bytes))
```

`content_bytes` are the RFC 8785 canonical UTF-8 bytes of the source content
projection defined below. No YOZI-FP envelope is used. A hashing or
canonicalization failure makes the declared-intent source invalid.

## 2. Source content projection

For a source record whose `source_id` is `S`, construct exactly this closed
object:

```json
{
  "manifest_version": "4.0.0",
  "namespaces": [],
  "nodes": [],
  "relations": []
}
```

The arrays contain only manifest declarations whose `source_key` equals `S`.
Copy each declaration after removing its `source_key` member. Do not include
the `sources` array or any source-record field, including `authority`,
`collected_at`, `content_fingerprint`, `precedence`, `revision`, `source_id`,
or `source_type`. Do not include an artifact, transport, adapter, signature,
or provenance wrapper. This exclusion prevents self-reference and makes the
same declared payload independently reproducible across transports.

Before RFC 8785 serialization:

- sort `namespaces` by unsigned lexicographic comparison of exact UTF-8
  `namespace_key` octets;
- sort `nodes` by unsigned lexicographic comparison of exact UTF-8
  `declaration_key` octets;
- sort `relations` by relation-type ASCII octets, source declaration-key UTF-8
  octets, target declaration-key UTF-8 octets, then RFC 8785 bytes of the
  already canonically ordered `parameters` array;
- apply every nested set order, duplicate rule, encoded-value rule, and closed
  field rule from the Profile 4 specification before hashing.

Duplicate source identifiers, declarations referring to an unknown source,
invalid UTF-8, non-canonical encoded values, duplicate set elements, or a
source whose declared content cannot be normalized are errors. A source MAY
have empty arrays; the closed object above is still hashed.

## 3. Verification sequence

1. Validate the manifest schema and Profile 4 semantic rules other than the
   source content digest comparison.
2. Require every declaration `source_key` to match exactly one `source_id`.
3. Build and sort the closed source content projection.
4. Serialize it using RFC 8785.
5. SHA-256 the exact UTF-8 bytes and format the lowercase prefixed digest.
6. Compare the complete 71-byte ASCII value with `content_fingerprint`.

No producer- or adapter-specific canonical form may replace this algorithm for
a Profile 4.0.0 manifest. Any byte-affecting change requires a new algorithm
URI and profile revision.
