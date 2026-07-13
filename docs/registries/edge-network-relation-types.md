# Edge Network Relation Type Registry, Version 1

Registry URI: `https://tbom.yozi.systems/registries/edge-network/relation-types/1`  
Owner: Yozi Systems

| Entry | Permanent URI | Source -> target | Meaning |
|---|---|---|---|
| Bridge member | `https://tbom.yozi.systems/registries/edge-network/relation-types/1/bridge-member` | interface -> bridge | Declared membership |
| VLAN parent | `https://tbom.yozi.systems/registries/edge-network/relation-types/1/vlan-parent` | VLAN -> interface | Declared tag attachment |
| Tunnel parent | `https://tbom.yozi.systems/registries/edge-network/relation-types/1/tunnel-parent` | tunnel -> interface | Declared underlay/attachment |
| Logical parent | `https://tbom.yozi.systems/registries/edge-network/relation-types/1/logical-parent` | logical -> node | Declared logical dependency |
| Tunnel peer | `https://tbom.yozi.systems/registries/edge-network/relation-types/1/tunnel-peer` | tunnel -> federation peer | Declared configured peer |
| Federation pathway | `https://tbom.yozi.systems/registries/edge-network/relation-types/1/federation-pathway` | local node -> federation peer | Declared permitted federation path |
| Declared handshake peer | `https://tbom.yozi.systems/registries/edge-network/relation-types/1/declared-handshake-peer` | local node -> federation peer | Declared permission/configuration for a handshake relationship, not evidence that a handshake occurred |

Relations are structural only when present in declared intent. Runtime master/parent state is conformance evidence. Entries are immutable; direction and meaning cannot be revised in place.
