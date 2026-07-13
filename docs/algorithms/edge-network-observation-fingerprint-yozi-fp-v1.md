# YOZI-FP-v1 Operational Observation Fingerprint

Algorithm URI: `https://tbom.yozi.systems/algorithms/edge-network-topology/4.0.0/observation-fingerprint-yozi-fp-v1-jcs-sha256`  
Status: normative Phase 0 draft

## 1. Projection and disclosure binding

The input is exactly the observation projection disclosed under its permanent `disclosure_profile_id`. Undisclosed producer state MUST NOT affect any byte. The profile URI, collection consistency, dataset status, and structural topology fingerprint or null are inside the projection.

Observation timestamps are metadata and are excluded from the fingerprinted projection. Dataset completeness and consistency are included because they qualify the meaning of disclosed evidence.

Required ordering:

- datasets: `dataset`, then `namespace_key`;
- interface observations: declared semantic ID (null last), then observation-subject ID;
- addresses: family, raw-address base64url bytes, prefix length, scope, peer bytes (null first);
- neighbors: interface semantic ID or observation locator, family, raw address bytes, link address bytes (null first), state;
- routes: table, family, raw destination bytes, prefix, metric, gateway bytes (null first), output-interface reference;
- conformance results: declared semantic ID (null last), observation-subject ID (null last), then status;
- reason-code arrays: unsigned ASCII URI order.

Exact normalized duplicates coalesce. Conflicting keyed records or missing required disclosed data make the observation fingerprint unavailable.

Interface `kind_state` is part of the projection whenever the disclosure profile includes it and is covered byte-for-byte by JCS and this fingerprint. Interface observation-subject IDs use only the normative interface descriptor in YOZI-TID; `ifindex`, MAC addresses, and producer-local locators MUST NOT replace it.

## 2. Envelope

The byte layout is identical to YOZI-FP-v1 structural layout except for this domain:

```text
https://tbom.yozi.systems/domain/edge-network-topology/4.0.0/fingerprint/observation
```

Formula:

```text
payload = RFC8785(observation_projection)
envelope = 59 4f 5a 49 2d 46 50 00 || be_u16(1) ||
           be_u16(len(domain)) || domain || 01 || be_u64(len(payload)) || payload
fingerprint = "sha256:" || lowercase_hex(SHA-256(envelope))
```

## 3. Sequential observation

An observation may be `generation_validated_sequential` when the adapter's first and second normalized link dumps match and all required datasets are complete. A mismatch yields `sequential_non_atomic`, the reason codes `link-dump-mismatch` and `observation-unstable`, and qualifies conformance. If the selected disclosure profile requires stable link evidence, the observation projection/fingerprint is unavailable. This never suppresses a valid declared-intent topology fingerprint.

## 4. Pseudocode

```text
function observation_fingerprint(projection, disclosure_profile):
    require projection.disclosure_profile_id == disclosure_profile.uri
    validate_closed_observation_schema(projection)
    enforce_required_and_forbidden_fields(disclosure_profile, projection)
    normalize_and_sort(projection)
    coalesce_exact_duplicates(projection)
    reject_conflicts_or_partial_required_datasets(projection)
    payload = RFC8785_UTF8(projection)
    domain = ASCII(observation_domain)
    envelope = HEX("594f5a492d465000") || BE16(1) || BE16(len(domain)) || domain ||
               HEX("01") || BE64(len(payload)) || payload
    return "sha256:" || HEX_LOWER(SHA256(envelope))
```

## 5. Comparison rule

Two observation fingerprints are comparable only when profile family, profile version, algorithm URI, disclosure-profile URI, and projection schema revision are identical. Equality is evidence that the disclosed canonical projections match; it is not proof of atomicity, authenticity, or undisclosed-state equality.
