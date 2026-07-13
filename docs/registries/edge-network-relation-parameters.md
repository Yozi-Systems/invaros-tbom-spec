# Edge-network relation parameter registry, version 1

## Status and identifier policy

This is the complete version-1 registry. An identifier is
`https://tbom.yozi.systems/registries/edge-network/relation-parameters/1/<name>`,
where `<name>` matches `[a-z][a-z0-9-]*`. Identifiers and meanings are
immutable. New entries require a specification change, a conformance vector,
and expert review for stable cross-platform meaning. Entries are never reused;
withdrawn entries remain reserved.

## Entries

| Name | Value | Meaning |
| --- | --- | --- |
| `required` | boolean | Whether the declared relation is required for intent conformance. |

An empty `parameters` array is valid and means that no registered relation
parameter was declared. Unknown identifiers are invalid in version 1.
