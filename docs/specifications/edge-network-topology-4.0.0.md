# InvarOS Edge Network Topology Profile 4.0.0 — Locked Normative Specification

Status: normative pre-publication draft; `invarosd` reference producer and bootstrap discovery implemented; corrected qualification completed locally after remediation of the first-live canonical-ordering defect
Specification URI: `https://tbom.yozi.systems/specifications/edge-network-topology/4.0.0`  
Profile family identifier: `invaros.tbom.profile.edge_network_topology`  
Normative revision: `4.0.0`  
Owner and change controller: Yozi Systems

## 1. Governing rule

**Structure is defined by declared intent, not by observed behavior.**

RTNETLINK, operating-system inventory, neighbor caches, routes, addresses, status, and counters are evidence of runtime state. They MUST NOT create, remove, or mutate a structural fact. A producer MAY compare observation to declared intent, but observation can only qualify the observation fingerprint and conformance result. It cannot suppress a structural fingerprint derived from complete, valid declared intent.

This specification uses the key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT, RECOMMENDED, NOT RECOMMENDED, MAY, and OPTIONAL as described by BCP 14 when they appear in uppercase.

## 2. Identifier classes

`profile_id` identifies the specification family. `profile_version` identifies this normative revision. Permanent HTTPS URIs identify exact specifications, schemas, registries, registry entries, and algorithms. These concepts MUST NOT be conflated.

All permanent identifiers are rooted at `https://tbom.yozi.systems/`. Redirectable publication locations MAY exist, but the permanent identifier value MUST remain unchanged.

## 3. Artifact planes

### 3.1 Persistent instance identity

An instance identity provides producer-local continuity. Hosts and nodes use cryptographically random lowercase RFC 9562 UUIDv4 values. A producer MUST persist them in a registry and MUST create a distinct alias for each disclosure scope. Instance IDs MUST NOT enter semantic-ID, topology-fingerprint, or observation-fingerprint preimages. They are intentionally not independently reproducible.

Renaming or changing a semantic descriptor keeps an instance ID when the producer can prove continuity from its persisted registry. Replacement creates a new instance ID. Ambiguous continuity MUST create a new ID and a reason-coded event; a producer MUST NOT guess.

### 3.2 Semantic identity descriptor

A semantic descriptor is a closed, typed description of declared structural meaning. Its semantic ID is independently reproducible from the normalized descriptor using YOZI-TID-v1. It excludes runtime evidence and instance identity.

### 3.3 Structural topology

Structural topology is the closed projection of complete, valid declared intent. It contains semantic nodes and declared relationships only. Its fingerprint is independently reproducible.

### 3.4 Operational observation state

Observation state is disclosed runtime evidence gathered under a named disclosure profile. It is mutable, may be sequential/non-atomic, and has a separate fingerprint. Runtime neighbors and routes exist only here.

### 3.5 Host identity

Canonical host identity is a scope-specific persistent UUIDv4 alias. It is not independently reproducible. Optional hardware, certificate, TPM, permanent-MAC, firmware, or platform evidence is separate and MUST NOT define canonical host identity.

### 3.6 Fingerprints

The topology fingerprint binds exactly the structural projection. The observation fingerprint binds exactly the disclosed observation projection and its `disclosure_profile_id`. Both use RFC 8785 plus a domain-separated YOZI-FP-v1 envelope. A fingerprint value is available only when the corresponding projection is complete and valid under this specification.

## 4. Declared intent

A structural projection MUST be sourced from one or more explicit declared-intent manifests conforming to the intent-manifest schema. Registered source types include local manifest, OpenWrt UCI, systemd-networkd, NetworkManager keyfile, declarative orchestration, and operator API. A platform adapter MUST preserve provenance and map source semantics; it MUST NOT infer structural intent from observed kernel behavior.

Each source record includes its source type URI, source identifier, revision,
collection time, and SHA-256 content fingerprint. The content fingerprint MUST
be computed with the registered source-content fingerprint algorithm. It binds
only the declared content attributed to that source, excludes the source record
itself and every provenance/transport wrapper field, and therefore cannot refer
to itself. A validator MUST recompute it before accepting the source. Multiple
sources require deterministic precedence declared in the manifest. Lower
numeric precedence has higher authority. Equal-precedence conflicting
declarations affecting the same structural fact invalidate the affected
structural projection. Arrival order MUST NOT resolve a conflict. Absence of
declared intent yields no structural fingerprint.

Names, namespace keys, link kinds, parentage, bridge membership, VLAN configuration, tunnel configuration, logical relationships, and federation peers are structural only when declared. A runtime object with no declaration may be reported as an unbound observation; it MUST NOT be promoted into structure.

## 5. Semantic nodes

Every node has a `node_type` registry URI, `namespace_key`, typed interface or peer name where applicable, type-specific closed parameters, semantic-ID algorithm URI, and semantic ID. Missing required input invalidates that node and therefore the structural projection. Optional missing values are represented by explicit nulls in YOZI-TID records and by JSON `null` only where the schema permits it; empty strings MUST NOT stand for missing values.

### 5.1 Common normalization

- `namespace_key` is a non-empty operator-assigned UTF-8 string; `root` is the default namespace key.
- Interface names preserve exact declared bytes as an encoded-value object. The encoding MUST be `utf-8` if and only if the original bytes are valid UTF-8; otherwise it MUST be canonical unpadded `base64url`. A base64url wrapper for valid UTF-8 bytes is invalid.
- IP addresses, route destinations and gateways, neighbor protocol addresses, tunnel endpoint addresses, and link-layer addresses are semantically binary protocol octets, not text. They MUST use the `binaryValue` shape and canonical unpadded `base64url` regardless of whether their octets happen to form valid UTF-8. Producers and validators MUST NOT apply textual UTF-8 preference to these fields. Textual presentation forms such as dotted-decimal IPv4, colon-form IPv6, and colon-delimited MAC addresses are not wire representations for these members.
- No Unicode normalization, case folding, trimming, or locale-sensitive transform is permitted.
- Registry values and algorithm identifiers are exact permanent HTTPS URIs.
- Integers are unsigned and bounded by their field definition.
- Arrays in semantic descriptors use the total orders in Section 9 and contain no duplicates wherever set semantics apply.

### 5.2 Physical interface

Inputs: node type, namespace key, declared interface name, registered interface kind, declared media type, and optional operator role. Current/permanent MAC, bus path, serial, driver, `ifindex`, MTU, addresses, and status are excluded. Rename changes the semantic ID but not a proven persistent instance. Reboot does not change identity when declaration is unchanged. Replacement changes instance identity; semantic identity may remain equal if declared structural role remains equal. Privacy class: organization-sensitive because names and roles may reveal design.

### 5.3 Bridge

Inputs: common fields, bridge technology, and registered identity-affecting declared bridge parameters. Bridge membership is represented as relations rather than duplicated in the node descriptor. Rename changes semantic ID. Runtime membership never changes structure. Privacy class: organization-sensitive.

### 5.4 VLAN

Inputs: common fields, VLAN ID 0..4094 as permitted by the declared adapter policy, VLAN protocol as its unsigned 16-bit EtherType, and parent semantic ID. Parent, tag, or protocol change creates a different semantic ID. Runtime `IFLA_LINK` does not define the parent. Privacy class: organization-sensitive.

### 5.5 Tunnel

Inputs: common fields; registered tunnel kind; a set of declared parent semantic IDs; normalized configured local and remote endpoints; and registered identity-affecting non-secret tunnel parameters. Secrets, private keys, preshared keys, session keys, credentials, and secret-derived reversible values are prohibited. Handshakes, learned endpoints, counters, reachability, and session state are observations. Privacy class: restricted because endpoints and public identifiers can expose connectivity.

The tunnel parameter mapping is singular. Tag 134 is a URI/value record for the one kind-specific identity parameter (`vxlan-vni`, `gre-key-id`, or `wireguard-public-key-id`) or null. Tag 135 is `udp-destination-port` or null. Tag 136 is the set-sorted array containing only remaining `hop-limit` parameter records. Endpoints occur only in tags 132 and 133. All three tags are always encoded, including null and empty forms.

### 5.6 Logical node

Inputs: common fields, registered logical kind, a set of parent semantic IDs, and registered identity-affecting non-secret parameters. Unknown identity-affecting kinds invalidate certification; `unknown` is not a generic structural type. Privacy class: organization-sensitive.

### 5.7 Declared federation peer

A declared federation peer is a structural node distinct from a runtime neighbor. Inputs: namespace key, operator peer key, a URI from `https://tbom.yozi.systems/registries/edge-network/federation-mechanisms/1`, trust-domain URI, normalized declared endpoint descriptors, optional disclosed public-key identifier digest, and registered non-secret parameters. It denotes intentional governance connectivity, not discovered trust. Privacy class: restricted.

### 5.8 Runtime neighbor

A runtime neighbor is not a structural node. Its observation subject ID uses a separate YOZI-TID domain and includes attached declared semantic ID or explicit unbound locator, address family, raw IP bytes, link-layer bytes or null, and namespace key. It is ephemeral, disclosure-sensitive evidence.

## 6. Namespace behavior

Every semantic node includes an operator-assigned namespace key. Linux namespace inode numbers, process paths, file-descriptor identities, and `ifindex` values MUST NOT be semantic inputs. An adapter MAY record them as observation evidence. If a namespace containing required declared intent has no stable operator key, the structural projection is unavailable. Inaccessible namespaces are explicitly reason-coded.

## 7. Structural projection

The structural projection contains exactly:

- `projection_id`;
- normalized semantic nodes;
- declared relations.

Included structural facts are declared interface names and kinds, declared namespace keys, parent relationships, bridge membership, VLAN tags/protocol/parent, configured tunnel relationships/endpoints/non-secret identity parameters, logical relationships, and declared federation peers.

Excluded facts are current/permanent MAC addresses, hardware serials, assigned IP addresses, runtime MTU, link status, carrier, counters, runtime neighbors, kernel routes, learned tunnel endpoints, handshakes, reachability, and timestamps.

Relations use permanent registry URIs. Nodes sort by semantic ID. Relations sort by relation URI, source semantic ID, target semantic ID, then canonical parameter bytes. Exact normalized duplicates coalesce. Conflicting records invalidate the projection; selection by arrival order is prohibited.

## 8. Observation projection

An observation projection binds only values disclosed under its `disclosure_profile_id`. It MAY contain:

- observed link locator, kind, parent/master relationships, current/permanent link address, MTU, flags, status, carrier and counters;
- assigned addresses with family, raw address, prefix, scope, flags, and peer;
- runtime neighbors with attached interface scope and NUD state;
- routes with table, family, raw destination/prefix, type, scope, protocol, priority, output interface, gateway and canonical multipath next hops;
- tunnel runtime evidence;
- intent-versus-runtime conformance results;
- dataset completeness and collection consistency.

Each interface observation carries `kind_state` when required by its disclosure profile. It is null for physical or otherwise unmodeled interfaces. Version 1 has exactly four non-null forms:

- bridge: `kind:"bridge"`, observed STP mode `0..2` or null, and VLAN-filtering boolean or null;
- VLAN: `kind:"vlan"`, VLAN ID `0..4094`, and protocol EtherType `33024` or `34984`;
- tunnel: `kind:"tunnel"` and observed local and remote endpoint records or null;
- logical: `kind:"logical"`, registered logical-kind URI, and VRF table `0..4294967295` or null.

Unknown or incomplete identity-affecting kind state makes a required observation dataset partial; it never changes declared structure.

Every interface `observation_subject_id` is YOZI-TID over the observation-subject domain with exactly: tag 1 `4.0.0`, tag 2 `interface`, tag 3 namespace key, tag 4 exact observed name bytes, and tag 5 exact observed kind or typed null. The ID is computed from the producer's full normalized observation before disclosure filtering. No runtime index or mutable link property enters this ID.

The projection MUST include the structural topology fingerprint or null, collection consistency, and disclosure profile URI. Arrays use the ordering in the observation algorithm document. A disclosure profile determines allowed and required fields. Undisclosed state MUST NOT influence the fingerprint.

## 9. Canonicalization and fingerprinting

All fingerprinted JSON MUST satisfy I-JSON and RFC 8785. Objects are closed by schema. Duplicate JSON member names are invalid. Arrays are pre-sorted according to this specification; RFC 8785 does not sort arrays. Floating-point values are prohibited. Integers are restricted to 0..9007199254740991 unless a narrower schema bound applies.

The Profile 4 RFC 8785 input domain is normatively restricted to JSON null,
Boolean, string, array, object, and integer values in the exact interoperable
range. Fractional and exponent lexical forms, non-finite values, values outside
the exact range, and lexical negative zero are invalid Profile 4 inputs.

Canonical value rules are:

- identifier strings compare by unsigned lexicographic comparison of their exact ASCII octets;
- structural nodes sort by semantic ID; relations sort by relation URI, source ID, target ID, then canonical parameter bytes;
- parent semantic-ID arrays are sets sorted by decoded 32-byte digest;
- parameter arrays are sets sorted by parameter-ID ASCII bytes, then RFC 8785 bytes of the scalar value;
- federation endpoint arrays are sets sorted by family, raw address bytes, transport (`null`, `tcp`, `udp`), then port (`null` before integers);
- nested-record arrays sort by complete YOZI-TID element encoding unless a registered descriptor states a more specific total order; version 1 has no additional nested-record array type;
- observation arrays use the exact keys and null ordering in the observation algorithm document;
- valid UTF-8 is preserved byte-for-byte without Unicode normalization; other source bytes use canonical unpadded base64url wrappers and are decoded to raw bytes before typed identity encoding;
- IPv4 and IPv6 values are family plus exactly four or sixteen network-order octets; text presentation is not an ordering or identity input;
- link-layer addresses are an explicit address type plus raw octets; textual presentation, if separately rendered, is lowercase two-digit colon-separated octets;
- an all-zero link-layer address is missing and represented by `null`; current and permanent addresses are distinct observation fields;
- namespace keys preserve exact valid UTF-8, are case-sensitive, and are never derived from Linux inode, path, process, or `ifindex` values;
- required missing values invalidate the affected projection; permitted optional missing values are JSON `null` and typed null; empty string, zero, empty object, and all-zero bytes MUST NOT substitute for missing;
- exact normalized records coalesce only when every canonical byte matches; conflicting logical duplicates invalidate the affected projection.

Semantic IDs use `https://tbom.yozi.systems/algorithms/edge-network-topology/4.0.0/semantic-id-yozi-tid-v1-sha256`. Topology and observation fingerprints use their respective YOZI-FP-v1 algorithm URIs. Algorithm documents define exact bytes.

Declared-intent source content fingerprints use
`https://tbom.yozi.systems/algorithms/edge-network-topology/4.0.0/source-content-fingerprint-rfc8785-sha256`.

## 10. Completeness, availability, and failure

### 10.1 Bootstrap intent state

Before projection, a producer evaluates governed declared sources into exactly one of three states: `absent`, `valid`, or `invalid`. A missing governed source and a governed source containing no declarations are `absent`. Merely installed vendor configuration is not operator adoption unless an adapter explicitly activates it as a governed source. Once any governed source is activated, malformed syntax, contradictory equal-precedence facts, unsupported identity-affecting constructs, ambiguity, incompleteness, or failed validation makes the state `invalid`.

A successful artifact carries `intent_status`, whose values are exactly `absent` and `valid`. The third evaluation state, `invalid`, is a terminal `declared-intent-invalid`/`intent-validation-failed` discovery error and therefore never appears in a successful artifact.

For `intent_status:"absent"`, `declared_intent` and `structural_topology` are null, the topology fingerprint is unavailable for reason `declared_intent_absent`, `intent_conformance.status` is `not-evaluated` with exactly that reason, and observation conformance records are empty. Observation remains an independent operational projection and does not become declared structure.

For `intent_status:"valid"`, the existing declared-intent structural projection, topology fingerprint, binding, conformance, and drift rules apply unchanged. `intent_conformance.status` is `evaluated`, its reason list is empty, and `candidate_intent` is null.

An absent-intent artifact whose disclosure profile exposes the candidate fields contains `candidate_intent`; `public-minimal` uses null and the operator requests `structural-conformance`, `network-operations`, or `internal-full` for the adoption workflow. It is a deterministic, non-authoritative projection of observed interface name, kind, kind state, namespace, parent/master observation-subject references, and observation-subject ID. It has `status:"candidate-not-active"` and `activation:"operator-action-required"`. Its interface order is the observation interface order, and `source_observation_fingerprint` is the available observation fingerprint or null. It excludes addresses, neighbors, routes, secrets, declared semantic IDs, and operator roles. It cannot be consumed as active intent. Activation requires an operator to review and translate or edit it into a valid governed manifest or overlay and explicitly install that source.

If observation is partial, the artifact remains valid with collection status `partial`, unavailable observation fingerprint, candidate completeness `partial`, and a null candidate source fingerprint. If observation is unavailable, observation and candidate are null. Absence never repairs collection failure, and observation never repairs invalid intent.

No incomplete artifact may present itself as complete. The artifact and each dataset carry `status`, record counts, attempts, and reason-code URIs. Structural and observation fingerprints use an availability object.

If required structural data is incomplete, conflicting, unavailable, unsupported, or invalid, the structural projection MUST be null and the topology fingerprint MUST have `availability: "unavailable"`, `value: null`, one stable error-code URI, and one or more reason-code URIs. A producer MAY still emit governed observation evidence.

Unknown identity-affecting declared kinds, unresolved structural references, conflicting normalized records, missing namespace keys, invalid intent, canonicalization failure, or cryptographic failure are fail-closed structural failures. Exact duplicates coalesce.

An interrupted Netlink dump, capacity truncation, inaccessible observation namespace, malformed message, sender-validation failure, or dataset failure makes the affected observation dataset partial or failed. It cannot invalidate complete declared structure. Cryptographic failure suppresses only the fingerprint requiring that operation and is reported explicitly.

## 11. Sequential collection

Linux generally cannot provide an atomic snapshot across link, address, route, and neighbor dumps. A validated sequential observation is permitted. The reference producer SHOULD dump links, collect other datasets, and dump links again. Matching normalized link views permit `generation_validated_sequential`. A mismatch means runtime observation is unstable, qualifies conformance, and suppresses an observation fingerprint when the disclosure profile requires stable links.

The second link dump MUST NOT suppress or invalidate a structural fingerprint derived from complete, valid declared intent.

## 12. Disclosure profiles

Observation fingerprints are disclosure-profile-specific. The profile URI is part of the fingerprinted projection. Producers MUST NOT hash undisclosed state. Initial registered profiles are public-minimal, structural-conformance, network-operations, and internal-full. Their machine-readable required, optional, forbidden, and collection rules are normative. Schema validation plus semantic profile validation is required. A consumer compares observation fingerprints only when algorithm URI and disclosure profile URI are identical.

`public-minimal` discloses each interface only as `namespace_key` plus `observation_subject_id`. It forbids both `interface_kind_observed` and `kind_state`: a modeled kind without its state is semantically incomplete, while disclosing the state would exceed the profile's minimal public boundary. Other profiles disclose the two fields together according to their registry rules.

`public-minimal` still discloses dataset accounting and therefore reveals
interface, address, route, and neighbor cardinality even where contents are
redacted. Operators MUST include topology scale in their disclosure threat model.

Instance aliases are also disclosure-scoped, but excluded from fingerprints. Disclosure of a stable alias is a correlatability decision.

## 13. Linux/OpenWrt reference adapter

The platform-neutral model above is normative. This section maps Linux/OpenWrt evidence and declared configuration into it.

### 13.1 Kernel transport requirements

The adapter MUST validate Netlink sender provenance (`sockaddr_nl.nl_pid == 0`), expected sequence, message bounds/alignment, `NLMSG_ERROR`, `NLMSG_OVERRUN`, and `NLM_F_DUMP_INTR` on `NLMSG_DONE`. Interrupted dumps are never complete. Capacity limits MUST produce explicit truncation. Retries MUST be recorded.

### 13.2 Link mapping

- observed name: `IFLA_IFNAME` exact bytes;
- current link address: `IFLA_ADDRESS`;
- permanent link address: `IFLA_PERM_ADDRESS` when present;
- master: `IFLA_MASTER`;
- observed parent: `IFLA_LINK`;
- MTU: `IFLA_MTU`;
- kind: `IFLA_LINKINFO/IFLA_INFO_KIND` plus registered kind-specific data;
- VLAN: `IFLA_VLAN_ID` and `IFLA_VLAN_PROTOCOL`;
- status evidence: flags and operational-state attributes.

Current and permanent addresses are distinct evidence. An all-zero link address is missing (`null`), not identity. Non-six-byte link addresses use lowercase colon-separated octets with an explicit link-layer type. Kernel kind strings map through the interface-kind registry; unknown identity-affecting declared kinds make structure unavailable, while unknown observed kinds remain explicit observation evidence.

### 13.3 Address mapping

Local address is `IFA_LOCAL` when present, otherwise `IFA_ADDRESS`. When both exist and differ, `IFA_ADDRESS` is the peer address. Family, raw address, prefix, scope, and flags are retained. Text is presentation only; sorting and identity use raw bytes.

### 13.4 Relationship mapping

Declared UCI or other intent defines parent/master/membership. `IFLA_LINK` and `IFLA_MASTER` are observed evidence used for conformance only. OpenWrt bridge membership and device sections MUST be mapped from declared UCI semantics, not inferred from runtime membership.

### 13.5 Namespace mapping

The initial namespace uses declared key `root`. Additional namespaces require operator-assigned keys and explicit collection authorization. Namespace inode/path is observation evidence only. An inaccessible required declared namespace is reason-coded and prevents structural certification.

### 13.6 Neighbor scope

Every neighbor observation includes namespace key and attached interface semantic ID, or an explicit unbound observed-interface locator if no declared binding exists. A neighbor cache entry never becomes a federation peer.

## 14. Host identity and evidence

The default host identity source class is `generated-persistent`. The producer generates a CSPRNG UUIDv4 and persists one alias per disclosure scope. Rotation is explicit, reason-coded, and creates a new identity. Loss of registry state creates a new identity and MUST NOT be represented as continuity.

Optional evidence source classes include platform assertion, device certificate, TPM/secure element, firmware assertion, processor assertion, storage assertion, and link-address assertion. Evidence records state collection and verification status, privacy class, and disclosed digest/assertion. No such evidence is mandatory. Independent observers are not expected to reproduce host identity.

## 15. Security and privacy

Names, topology, VLANs, tunnel endpoints, federation relationships, MACs, IPs, routes, and stable aliases may be sensitive. Producers MUST apply an explicit disclosure profile, minimize disclosure, and prevent cross-scope alias reuse. Semantic IDs and fingerprints are pseudonymous correlators, not anonymization. Low-entropy descriptors may be enumerable.

Secret material is forbidden from all manifests, descriptors, projections, evidence, and preimages. Closed parameter registries and schemas enforce this structurally; implementations MUST NOT claim reliable secret detection by guessing from arbitrary byte content. A structurally prohibited field or unregistered parameter causes fail-closed rejection. SHA-256 provides integrity naming, not authenticity. Artifact signing and attestation are separate layers.

Fingerprints alone provide neither replay protection nor trusted freshness.
Algorithm identifiers prevent silent substitution only when a consumer applies
an external allow-list; they do not provide absolute downgrade resistance or
prevent wholesale replacement of an unsigned artifact.

Observation resources are bounded to the reference edge deployment envelope:
16 namespaces / 64 dataset reports, 512 interfaces and conformance records,
2,048 addresses, and 4,096 routes and neighbors. These match the reference
producer's fixed capacities and 8 MiB collection budget. Producers fail closed
with `capacity-truncation`. Consumers SHOULD check canonical order first and MAY
validate uniqueness in linear time by adjacent comparison.

Consumers MUST validate schema, algorithm URI, registry versions, completeness, canonicalization, fingerprints, and referential integrity before relying on an artifact. Unknown permanent identifiers fail closed. A future extension is recognized only through an explicitly supported profile revision and its published schema, registry, algorithm URI, and vectors.

## 16. Relationship to RFC 8342 (NMDA)

The declared-intent and operational-observation planes align conceptually with NMDA intended and operational datastore distinctions. This specification does not define a NETCONF/RESTCONF datastore, origin metadata, or an NMDA mapping, and it does not claim that a TBoM artifact is an NMDA datastore snapshot. The relationship is explanatory only: observed state cannot create declared structure, and adapters must preserve provenance when importing configuration.

## 17. Migration and dual emission

Profile 3 and Profile 4 are separate complete artifacts. A producer MUST NOT mix Profile 4 fields into Profile 3 or silently reinterpret a Profile 3 fingerprint. During migration and after Profile 4 production readiness, dual emission is the default. Profile 3 has no scheduled removal; deprecation requires evidence of ecosystem migration, published notice, and an explicit Yozi Systems governance decision.

Consumers dispatch by `profile_id`, `profile_version`, specification URI, and algorithm URI. Profile 3 goldens remain immutable. Transition tests MUST prove unchanged Profile 3 bytes and fingerprints, independent Profile 4 validation, and failure isolation between emissions.

## 18. Conformance status

This Phase 0 package defines a draft normative target and synthetic vectors. No current production producer claims Profile 4 implementation or conformance. Runtime captures and implementation-generated conformance artifacts are future milestones.
