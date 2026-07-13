# Edge Network Tunnel Parameter Registry, Version 1

Registry URI: `https://tbom.yozi.systems/registries/edge-network/tunnel-parameters/1`  
Owner: Yozi Systems

Each entry states whether it affects semantic identity. Values are normalized as defined by the relevant algorithm: integers as unsigned integers, addresses as family plus raw bytes, identifiers as permanent URIs or lowercase `sha256:` digests.

| Entry | Permanent URI | Type | Identity-affecting | Notes |
|---|---|---|---|---|
| VXLAN VNI | `https://tbom.yozi.systems/registries/edge-network/tunnel-parameters/1/vxlan-vni` | uint64, 0..16777215 | yes | declared VNI |
| GRE key identifier | `https://tbom.yozi.systems/registries/edge-network/tunnel-parameters/1/gre-key-id` | uint64, 0..4294967295 | yes | non-secret configured key identifier |
| WireGuard public key identifier | `https://tbom.yozi.systems/registries/edge-network/tunnel-parameters/1/wireguard-public-key-id` | SHA-256 digest | yes | digest of disclosed public key; never private/preshared key |
| UDP destination port | `https://tbom.yozi.systems/registries/edge-network/tunnel-parameters/1/udp-destination-port` | uint64, 0..65535 | yes | configured port |
| Hop limit | `https://tbom.yozi.systems/registries/edge-network/tunnel-parameters/1/hop-limit` | uint64, 0..255 | yes | only when explicitly configured |

Handshake time, learned endpoint, session key, preshared key, counters, reachability, and packet state are prohibited structural parameters. A new identity-affecting parameter requires a registry addition before certification.

Configured local and remote endpoints are not parameter entries. They use the dedicated `local_endpoint` and `remote_endpoint` manifest members and YOZI-TID tags 132 and 133.

The mapping is mandatory and unique: the kind-specific VNI, GRE key, or WireGuard public-key identifier maps to tag 134 as a URI/value record; UDP destination port maps to tag 135; and hop limit maps to the tag-136 parameter-record array. No entry may be encoded under another tag.
