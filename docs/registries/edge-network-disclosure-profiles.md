# Edge Network Disclosure Profile Registry, Version 1

Registry URI: `https://tbom.yozi.systems/registries/edge-network/disclosure-profiles/1`  
Owner: Yozi Systems

Observation fingerprints bind only the selected profile's disclosed projection.
The normative machine-readable registry is
[`registries/edge-network/disclosure-profiles/1/registry.json`](../../registries/edge-network/disclosure-profiles/1/registry.json),
validated by its adjacent `schema.json`. Its required, optional, and forbidden
interface fields and non-empty collection permissions are normative. All
profiles include collection consistency, dataset completeness, the profile URI,
and the structural topology fingerprint or null.

| Entry | Permanent URI | Required disclosure | Excluded disclosure |
|---|---|---|---|
| Public minimal | `https://tbom.yozi.systems/registries/edge-network/disclosure-profiles/1/public-minimal` | namespace-scoped observation subject | names, observed kinds, kind state, addresses, routes, neighbors, MACs, detailed link state, conformance records |
| Structural conformance | `https://tbom.yozi.systems/registries/edge-network/disclosure-profiles/1/structural-conformance` | observed bindings and declared-intent conformance | addresses, routes, neighbors, current/permanent MACs, counters |
| Network operations | `https://tbom.yozi.systems/registries/edge-network/disclosure-profiles/1/network-operations` | link state, addresses, routes, neighbors, conformance | permanent link address and hardware evidence unless separately authorized |
| Internal full | `https://tbom.yozi.systems/registries/edge-network/disclosure-profiles/1/internal-full` | all schema-defined non-secret observation fields supported by producer | secret material always excluded |

A producer MUST fail explicitly if it cannot satisfy required fields. It MUST
NOT add forbidden fields. `public-minimal` permits a non-empty `interfaces`
array using only its machine-readable field set, so it is not restricted to an
empty observation. Scope-specific instance aliases are disclosed outside the
observation fingerprint.

`interface_kind_observed` and `kind_state` are both forbidden by public-minimal. A producer MUST NOT disclose a modeled kind without its governing state. Both fields are required by structural-conformance, network-operations, and internal-full; physical or otherwise unmodeled interfaces use null state. Non-null bridge, VLAN, tunnel, and logical forms are closed by the observation schema.
