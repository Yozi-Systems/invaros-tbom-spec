# Edge Network Interface Kind Registry, Version 1

Registry URI: `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1`  
Owner: Yozi Systems

| Entry | Permanent URI | Node type | Linux/OpenWrt mapping |
|---|---|---|---|
| Ethernet | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/ethernet` | physical | declared Ethernet device; empty `IFLA_INFO_KIND` is only observation evidence |
| IEEE 802.11 | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/ieee80211` | physical | declared wireless interface; wireless subsystem evidence is observation-only |
| Cellular | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/cellular` | physical | declared cellular interface; modem state is observation-only |
| InfiniBand | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/infiniband` | physical | declared InfiniBand interface; link address remains evidence |
| Loopback | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/loopback` | logical | declared loopback; observed ARPHRD loopback evidence |
| Linux bridge | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/linux-bridge` | bridge | UCI bridge intent; observed kind `bridge` |
| IEEE 802.1Q VLAN | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/ieee8021q-vlan` | VLAN | UCI VLAN intent; observed kind `vlan` |
| TUN | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/tun` | tunnel | declared tun; observed kind `tun` |
| TAP | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/tap` | tunnel | declared tap; observed kind `tap` |
| WireGuard | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/wireguard` | tunnel | declared WireGuard; observed kind `wireguard` |
| GRE IPv4 | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/gre` | tunnel | declared GRE; observed kind `gre` |
| GRE IPv6 | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/gre6` | tunnel | declared GRE6; observed kind `gre6` |
| SIT | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/sit` | tunnel | declared SIT; observed kind `sit` |
| IPv6 tunnel | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/ip6tnl` | tunnel | declared IPv6 tunnel; observed kind `ip6tnl` |
| VXLAN | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/vxlan` | tunnel | declared VXLAN; observed kind `vxlan` |
| GENEVE | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/geneve` | tunnel | declared GENEVE; observed kind `geneve` |
| L2TP | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/l2tp` | tunnel | declared L2TP; kind-specific evidence varies by kernel adapter |
| VETH | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/veth` | logical | declared veth endpoint; observed kind `veth` |
| Bond | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/bond` | logical | declared bond; observed kind `bond` |
| Team | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/team` | logical | declared team; observed kind `team` |
| MACVLAN | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/macvlan` | logical | declared macvlan; observed kind `macvlan` |
| IPVLAN | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/ipvlan` | logical | declared ipvlan; observed kind `ipvlan` |
| VRF | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/vrf` | logical | declared VRF; observed kind `vrf` |
| DSA port | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/dsa-port` | logical | declared switch port; observed mapping is adapter-specific |
| Dummy | `https://tbom.yozi.systems/registries/edge-network/interface-kinds/1/dummy` | logical | declared dummy; observed kind `dummy` |

The mapping column is adapter guidance, not a rule that observed kind creates structure. Unknown observed kinds may be preserved as evidence. Unknown declared identity-affecting kinds fail closed pending registry evolution.
