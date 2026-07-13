# Edge Network Federation Mechanism Registry, Version 1

Registry URI: `https://tbom.yozi.systems/registries/edge-network/federation-mechanisms/1`  
Owner: Yozi Systems

| Entry | Permanent URI | Structural meaning |
|---|---|---|
| WireGuard | `https://tbom.yozi.systems/registries/edge-network/federation-mechanisms/1/wireguard` | A declared peer whose permitted pathway uses configured WireGuard identity/endpoints |
| TLS | `https://tbom.yozi.systems/registries/edge-network/federation-mechanisms/1/tls` | A declared peer whose governance relationship names a TLS trust anchor |
| IPsec | `https://tbom.yozi.systems/registries/edge-network/federation-mechanisms/1/ipsec` | A declared peer whose permitted pathway uses configured IPsec identity/endpoints |

The mechanism records declared intent only. A live handshake, certificate result, negotiated key, reachability result, or session is observation/evidence and cannot establish structural trust. New mechanisms require immutable registered semantics and non-secret identity inputs.
