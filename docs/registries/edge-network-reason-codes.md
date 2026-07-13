# Edge Network Reason Code Registry, Version 1

Registry URI: `https://tbom.yozi.systems/registries/edge-network/reason-codes/1`  
Owner: Yozi Systems

Reason codes are stable facts that qualify a status or error; they are not prose substitutes.

| Permanent URI | Meaning |
|---|---|
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/declared-intent-missing` | no declared intent was available |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/declared-intent-incomplete` | a required declaration is absent |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/declared-intent-invalid` | intent failed schema or semantic validation |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/declared-intent-conflicting` | equal-precedence declarations conflict |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/namespace-key-missing` | a required stable namespace key is absent |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/namespace-inaccessible` | an observation namespace could not be entered/read |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/unsupported-declared-kind` | an identity-affecting declared kind is unregistered |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/unresolved-structural-reference` | a declared node/relation target cannot be resolved |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/duplicate-semantic-id` | distinct normalized descriptors produced one semantic ID |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/conflicting-records` | records with the same logical key differ after normalization |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/capacity-truncation` | a bounded collector omitted records |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/dump-interrupted` | a kernel marked a dump interrupted |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/netlink-overrun` | ENOBUFS or NLMSG_OVERRUN occurred |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/dataset-failed` | a requested dataset could not be collected |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/dataset-partial` | only part of a requested dataset is available |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/sender-validation-failed` | kernel sender provenance validation failed |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/malformed-netlink` | message bounds, alignment, or attributes are invalid |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/link-dump-mismatch` | first and second normalized link views differ |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/observation-unstable` | runtime state changed during sequential collection |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/ambiguous-binding` | observed object cannot be uniquely bound to declared intent |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/observation-subject-unresolved` | no declared semantic subject or stable unbound locator exists |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/required-field-unavailable` | required model input cannot be represented |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/invalid-byte-wrapper` | encoded-byte wrapper is malformed or non-canonical |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/canonicalization-failure` | RFC 8785 canonical bytes could not be produced |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/cryptographic-failure` | required digest operation failed |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/secret-material-detected` | prohibited secret material was found |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/disclosure-profile-unsupported` | producer cannot satisfy the named disclosure profile |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/instance-registry-lost` | persisted instance continuity state was lost |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/instance-continuity-ambiguous` | producer cannot prove which prior instance corresponds |
| `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/operator-rotation` | an operator explicitly rotated a persistent alias |

Unknown reason codes are not silently ignored by strict consumers. New entries require governance review and immutable semantics.
