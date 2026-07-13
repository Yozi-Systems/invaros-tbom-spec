# Edge Network Intent Source Type Registry, Version 1

Registry URI: `https://tbom.yozi.systems/registries/edge-network/intent-source-types/1`  
Owner: Yozi Systems

| Entry | Permanent URI | Required provenance |
|---|---|---|
| Profile 4 manifest | `https://tbom.yozi.systems/registries/edge-network/intent-source-types/1/profile4-manifest` | manifest URI/path identifier, revision, content fingerprint |
| OpenWrt UCI | `https://tbom.yozi.systems/registries/edge-network/intent-source-types/1/openwrt-uci` | package/config identifier, export revision, content fingerprint |
| systemd-networkd | `https://tbom.yozi.systems/registries/edge-network/intent-source-types/1/systemd-networkd` | ordered unit-set identifier, revision, content fingerprint |
| NetworkManager keyfile | `https://tbom.yozi.systems/registries/edge-network/intent-source-types/1/networkmanager-keyfile` | ordered connection-set identifier, revision, content fingerprint |
| Declarative orchestration | `https://tbom.yozi.systems/registries/edge-network/intent-source-types/1/declarative-orchestration` | controller namespace/object revision and content fingerprint |
| Operator API | `https://tbom.yozi.systems/registries/edge-network/intent-source-types/1/operator-api` | authority, revision/token identifier, content fingerprint |

Source adapters MUST define deterministic precedence and mapping semantics. Shell commands, kernel inventory, Netlink dumps, and neighbor caches are observation sources and are not registered intent sources.
