# Edge Network Tunnel Parameter Registry, Version 1

Registry URI: `https://tbom.yozi.systems/registries/edge-network/tunnel-parameters/1`  
Owner: Yozi Systems

Each entry states whether it affects semantic identity. Values are normalized as defined by the relevant algorithm: integers as unsigned integers, addresses as family plus raw bytes, identifiers as permanent URIs or lowercase `sha256:` digests.

| Entry | Permanent URI | Type | Identity-affecting | Notes |
|---|---|---|---|---|
| Local endpoint | `https://tbom.yozi.systems/registries/edge-network/tunnel-parameters/1/local-endpoint` | endpoint record or null | yes | configured endpoint, not learned address |
| Remote endpoint | `https://tbom.yozi.systems/registries/edge-network/tunnel-parameters/1/remote-endpoint` | endpoint record or null | yes | configured endpoint |
| VXLAN VNI | `https://tbom.yozi.systems/registries/edge-network/tunnel-parameters/1/vxlan-vni` | uint64, 0..16777215 | yes | declared VNI |
| GRE key identifier | `https://tbom.yozi.systems/registries/edge-network/tunnel-parameters/1/gre-key-id` | uint64, 0..4294967295 | yes | non-secret configured key identifier |
| WireGuard public key identifier | `https://tbom.yozi.systems/registries/edge-network/tunnel-parameters/1/wireguard-public-key-id` | SHA-256 digest | yes | digest of disclosed public key; never private/preshared key |
| UDP destination port | `https://tbom.yozi.systems/registries/edge-network/tunnel-parameters/1/udp-destination-port` | uint64, 0..65535 | yes | configured port |
| Hop limit | `https://tbom.yozi.systems/registries/edge-network/tunnel-parameters/1/hop-limit` | uint64, 0..255 | yes | only when explicitly configured |

Handshake time, learned endpoint, session key, preshared key, counters, reachability, and packet state are prohibited structural parameters. A new identity-affecting parameter requires a registry addition before certification.
