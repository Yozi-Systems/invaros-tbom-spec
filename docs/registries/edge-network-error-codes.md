# Edge Network Error Code Registry, Version 1

Registry URI: `https://tbom.yozi.systems/registries/edge-network/error-codes/1`  
Owner: Yozi Systems

| Entry | Permanent URI | Applies to |
|---|---|---|
| Structural projection unavailable | `https://tbom.yozi.systems/registries/edge-network/error-codes/1/structural-projection-unavailable` | structural projection/topology fingerprint |
| Observation projection unavailable | `https://tbom.yozi.systems/registries/edge-network/error-codes/1/observation-projection-unavailable` | observation projection/fingerprint |
| Semantic identity unavailable | `https://tbom.yozi.systems/registries/edge-network/error-codes/1/semantic-identity-unavailable` | node identity |
| Intent validation failed | `https://tbom.yozi.systems/registries/edge-network/error-codes/1/intent-validation-failed` | declared intent |
| Canonicalization failed | `https://tbom.yozi.systems/registries/edge-network/error-codes/1/canonicalization-failed` | any fingerprint |
| Cryptographic operation failed | `https://tbom.yozi.systems/registries/edge-network/error-codes/1/cryptographic-operation-failed` | any digest/identity operation |
| Artifact invalid | `https://tbom.yozi.systems/registries/edge-network/error-codes/1/artifact-invalid` | whole artifact |
| Disclosure unavailable | `https://tbom.yozi.systems/registries/edge-network/error-codes/1/disclosure-unavailable` | requested disclosure profile |

An unavailable fingerprint has exactly one primary error code and one or more reason codes. Error codes classify the failure; reason codes give stable detail. Prose diagnostics are optional and never fingerprint inputs unless the schema explicitly includes them.
