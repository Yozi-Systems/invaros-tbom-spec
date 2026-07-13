# YOZI-TID-v1 Semantic Identity Algorithm

Algorithm URI: `https://tbom.yozi.systems/algorithms/edge-network-topology/4.0.0/semantic-id-yozi-tid-v1-sha256`  
Status: normative Phase 0 draft  
Owner: Yozi Systems

## 1. Output

```text
semantic_id = "sha256:" || lowercase_hex(SHA-256(record_bytes))
```

The algorithm URI MUST accompany the output. A SHA-256 failure produces no ID and the reason code `https://tbom.yozi.systems/registries/edge-network/reason-codes/1/cryptographic-failure`.

## 2. Primitive encodings

All integers are unsigned big-endian. Lengths count octets. No padding or terminator is present unless explicitly stated.

### 2.1 Top-level record

| Offset | Size | Field |
|---:|---:|---|
| 0 | 8 | ASCII `YOZI-TID` (`59 4f 5a 49 2d 54 49 44`) |
| 8 | 2 | format version, `00 01` |
| 10 | 2 | domain length `D` |
| 12 | D | domain ASCII octets |
| 12+D | 4 | record length `R` |
| 16+D | 2 | field count `N` |
| 18+D | R-2 | `N` encoded fields |

`R` is the exact number of octets from the first octet of `field_count` through the final field, so `R = 2 + sum(encoded_field_lengths)`. The input MUST end exactly after the last field. `D` MUST be nonzero. Domain bytes MUST be ASCII and match one registered domain exactly.

### 2.2 Field

| Size | Field |
|---:|---|
| 2 | tag |
| 1 | value type |
| 1 | flags, exactly `00` |
| 4 | value length `L` |
| L | value |

Tags are strictly ascending, unique, and nonzero. Every descriptor-defined field is encoded exactly once, including optional fields as typed null.

### 2.3 Value types

| Code | Type | Value bytes |
|---:|---|---|
| `00` | null | zero octets only |
| `01` | UTF-8 | valid shortest-form UTF-8, no BOM; no normalization |
| `02` | bytes | uninterpreted octets |
| `03` | uint64 | exactly 8 octets |
| `04` | boolean | exactly one octet, `00` or `01` |
| `05` | SHA-256 digest | exactly 32 raw octets; textual `sha256:` is decoded first |
| `06` | array | array encoding below |
| `07` | nested record | nested-record encoding below |

Invalid length/type combinations are errors.

### 2.4 Array

```text
element_count       uint32
repeat element_count times:
  element_type      uint8
  element_flags     uint8, exactly 0
  element_length    uint32
  element_value     element_length octets
```

An element uses the same value encoding as a field but cannot itself have type null unless the descriptor permits it. Arrays defined as sets MUST be sorted by unsigned lexicographic comparison of the complete bytes `element_type || element_flags || element_length || element_value` and MUST contain no duplicate encoded elements. Ordered arrays preserve descriptor-defined order.

### 2.5 Nested record

```text
nested_field_count  uint16
nested_fields       encoded fields in strictly ascending tag order
```

A nested record has no magic, version, domain, or record-length member because its enclosing field already supplies type and length. Its value MUST end exactly after the declared fields.

## 3. String and byte rules

No NFC/NFD normalization, case folding, trimming, locale transformation, or
line-ending rewrite is allowed. An original byte sequence uses type `01` if and
only if it is valid UTF-8. It uses type `02` if and only if it is not valid
UTF-8; its JSON representation uses canonical unpadded base64url. A validator
MUST reject base64url whose decoded bytes are valid UTF-8, invalid UTF-8 JSON
strings, padding, non-alphabet characters, and non-canonical base64url. Thus one
byte sequence has exactly one valid representation. Two distinct byte sequences
never normalize to the same value.

Permanent URIs are encoded exactly as lowercase-scheme/host ASCII strings published by this package. UUIDs do not occur in semantic records. IP endpoints use raw network-order address bytes, never presentation text. A missing endpoint is typed null, not an all-zero address.

Although the binary `uint64` primitive can represent 0 through 2^64-1, every
Profile 4 value sourced through its I-JSON manifest is limited to 0 through
9007199254740991, or a narrower registry/schema bound. A future non-JSON
descriptor may use the wider primitive only under a new explicitly specified
descriptor; producers MUST NOT infer such permission from the primitive alone.

## 4. Domains

Structural nodes use:

```text
https://tbom.yozi.systems/domain/edge-network-topology/4.0.0/node/physical
https://tbom.yozi.systems/domain/edge-network-topology/4.0.0/node/bridge
https://tbom.yozi.systems/domain/edge-network-topology/4.0.0/node/vlan
https://tbom.yozi.systems/domain/edge-network-topology/4.0.0/node/tunnel
https://tbom.yozi.systems/domain/edge-network-topology/4.0.0/node/logical
https://tbom.yozi.systems/domain/edge-network-topology/4.0.0/node/declared-federation-peer
```

Observation subjects use:

```text
https://tbom.yozi.systems/domain/edge-network-topology/4.0.0/observation/subject
```

The formerly proposed structural-neighbor domain is reserved and MUST NOT be
used. Runtime neighbors are observation-only; a separately declared federation
peer uses the structural federation-peer domain.

## 5. Field tags

Common structural tags:

| Tag | Type | Meaning |
|---:|---|---|
| 1 | UTF-8 | descriptor version, exactly `4.0.0` |
| 2 | UTF-8 | node-type permanent URI |
| 3 | UTF-8 | namespace key |
| 4 | UTF-8 or bytes | exact declared interface name; null only for federation peer |
| 5 | UTF-8 | interface-kind URI; for a federation peer, repeat the node-type URI as its non-interface semantic kind |

Type-specific tags:

| Type | Tags |
|---|---|
| Physical | 100 media type UTF-8; 101 operator role UTF-8 or null |
| Bridge | 110 technology UTF-8; 111 registered parameter array |
| VLAN | 120 VLAN ID uint64; 121 protocol uint64; 122 parent SHA-256 digest |
| Tunnel | 130 tunnel-kind URI; 131 set of parent digests; 132 local endpoint record/null; 133 remote endpoint record/null; 134 kind-specific identity-parameter record/null; 135 UDP destination port uint64/null; 136 remaining registered parameter array |
| Logical | 140 logical-kind URI; 141 set of parent digests; 142 registered parameter array |
| Federation peer | 160 federation-mechanism registry URI; 161 operator peer key UTF-8; 162 trust-domain URI UTF-8; 163 set of endpoint records; 164 public-key/certificate digest or null; 165 governance parameter array |
| Observation neighbor subject | 150 attachment record; 151 address family uint64 (`4` or `6`); 152 raw address bytes; 153 link-layer bytes or null |

Endpoint nested record tags are: 1 address family uint64; 2 raw address bytes; 3 transport UTF-8 (`udp` or `tcp`) or null; 4 port uint64 or null. Parameter arrays contain nested records with tag 1 parameter registry URI UTF-8 and tag 2 a descriptor-defined typed value. Attachment records contain tag 1 reference class UTF-8 (`declared-semantic-id` or `observation-subject-id`) and tag 2 digest.

### 5.1 Interface observation-subject descriptor

Every observed interface has an `observation_subject_id` in the observation-subject domain. Its descriptor contains exactly these five fields:

| Tag | Type | Value |
|---:|---|---|
| 1 | UTF-8 | descriptor version, exactly `4.0.0` |
| 2 | UTF-8 | subject class, exactly `interface` |
| 3 | UTF-8 | operator-assigned namespace key |
| 4 | UTF-8 or bytes | exact observed interface-name bytes |
| 5 | UTF-8 or null | observed interface-kind value; null when the kernel supplies no kind |

The name uses the encoded-value rule in Section 3 without trimming, case folding, or normalization. A present kind is the exact lowercase kernel kind mapped by the Version 1 adapter; an absent kind is typed null. `ifindex`, namespace inode, MAC addresses, MTU, status, addresses, parents, masters, and timestamps are excluded. The record uses the observation-subject domain, standard YOZI-TID framing, and SHA-256 formatting from Sections 1 and 2. All producers given the same namespace key, exact name bytes, and observed kind MUST emit identical record bytes and `observation_subject_id`.

### 5.2 Normative tunnel parameter mapping

Tunnel parameters have exactly one mapping to tags 134–136:

- Tag 134 is typed null when the kind-specific identity parameter is absent. Otherwise it is a nested record with tag 1 equal to the parameter URI and tag 2 equal to its typed value. The only permitted pairs are `vxlan` with `vxlan-vni`/uint64, `gre` or `gre6` with `gre-key-id`/uint64, and `wireguard` with `wireguard-public-key-id`/digest. More than one tag-134 candidate or a candidate on another tunnel kind is invalid.
- Tag 135 is the uint64 value of the single `udp-destination-port` parameter, or typed null when absent.
- Tag 136 is a set-sorted array of parameter records containing only `hop-limit`. Each record uses tag 1 for the parameter URI and tag 2 for its uint64 value. The array is encoded even when empty.

`local-endpoint` and `remote-endpoint` are represented only by the dedicated manifest members and tags 132 and 133. They MUST NOT occur in `parameters`. Every tunnel descriptor encodes tags 134, 135, and 136 exactly once. Duplicate parameter identifiers are invalid.

## 6. Validation sequence

1. Validate the declared manifest and registered type.
2. Normalize every value using the rules above.
3. Resolve structural references to semantic digest bytes; dependency cycles that cannot be resolved are invalid.
4. Construct all required fields.
5. Sort field tags and set-like arrays; reject duplicates.
6. Encode nested values, then fields, then top-level record.
7. Verify all lengths fit their unsigned fields and no trailing bytes exist.
8. Hash the complete top-level record and format the result.

## 7. Language-neutral pseudocode

```text
function encode_value(type, value):
    switch type:
      null:   require value is missing; return empty_bytes
      utf8:   require valid_utf8(value); return exact_utf8_bytes(value)
      bytes:  return exact_bytes(value)
      uint64: require 0 <= value <= 2^64-1; return be_u64(value)
      bool:   return 0x01 if value else 0x00
      digest: require 32 bytes; return value
      array:
        elements = [type(e)||0x00||be_u32(len(enc(e)))||enc(e) for e]
        if set_semantics: sort_unsigned_lex(elements); reject_duplicates(elements)
        return be_u32(count(elements)) || concat(elements)
      record:
        fields = encode_fields(value.fields)
        return be_u16(count(fields)) || concat(fields)

function encode_field(field):
    v = encode_value(field.type, field.value)
    return be_u16(field.tag) || u8(field.type) || 0x00 || be_u32(len(v)) || v

function semantic_id(domain, fields):
    require strictly_ascending_unique_tags(fields)
    body = be_u16(count(fields)) || concat(map(encode_field, fields))
    record = ascii("YOZI-TID") || be_u16(1) || be_u16(len(ascii(domain))) ||
             ascii(domain) || be_u32(len(body)) || body
    return "sha256:" || hex_lower(SHA256(record))
```

## 8. Evolution

Any change to bytes, tags, normalization, ordering, domains, digest, or failure behavior requires a new algorithm URI. Unknown flags or value types are errors in version 1.
