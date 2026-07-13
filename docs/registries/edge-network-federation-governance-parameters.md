# Edge-network federation-governance parameter registry, version 1

## Status and identifier policy

This is the complete version-1 registry. An identifier is
`https://tbom.yozi.systems/registries/edge-network/federation-governance-parameters/1/<name>`,
where `<name>` matches `[a-z][a-z0-9-]*`. Identifiers and meanings are
immutable. New entries require a specification change, a conformance vector,
and expert review for stable cross-operator meaning. Entries are never reused;
withdrawn entries remain reserved.

## Entries

| Name | Value | Meaning |
| --- | --- | --- |
| `require-mutual-authentication` | boolean | Whether the declaration requires both federation peers to authenticate. |

An empty `parameters` array is valid and means that no registered federation
governance parameter was declared. Unknown identifiers are invalid in version 1.
