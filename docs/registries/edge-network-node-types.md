# Edge Network Node Type Registry, Version 1

Registry URI: `https://tbom.yozi.systems/registries/edge-network/node-types/1`  
Owner: Yozi Systems  
Policy: specification required; entries are immutable; semantic changes require a new entry or registry version

| Entry | Permanent URI | Plane | Required semantic inputs |
|---|---|---|---|
| Physical interface | `https://tbom.yozi.systems/registries/edge-network/node-types/1/physical` | structural | namespace, name bytes, interface kind, media type, optional operator role |
| Bridge | `https://tbom.yozi.systems/registries/edge-network/node-types/1/bridge` | structural | namespace, name bytes, interface kind, technology, registered parameters |
| VLAN | `https://tbom.yozi.systems/registries/edge-network/node-types/1/vlan` | structural | namespace, name bytes, interface kind, VLAN ID, protocol, parent semantic ID |
| Tunnel | `https://tbom.yozi.systems/registries/edge-network/node-types/1/tunnel` | structural | namespace, name bytes, interface kind, parent IDs, configured endpoints, registered parameters |
| Logical | `https://tbom.yozi.systems/registries/edge-network/node-types/1/logical` | structural | namespace, name bytes, interface kind, parent IDs, registered parameters |
| Declared federation peer | `https://tbom.yozi.systems/registries/edge-network/node-types/1/declared-federation-peer` | structural | namespace, peer key, mechanism, trust domain, declared endpoints, optional public identifier, parameters |

Runtime neighbors are deliberately absent. They are observation subjects, not structural nodes. An unknown declared node type is not equivalent to `logical`; it makes the structural projection unavailable.
