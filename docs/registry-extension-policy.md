# Registry extension and offline resolution

Yozi Systems currently maintains the registries. Existing permanent entries do
not change meaning. An extension proposal must define one non-overlapping
semantic, compatibility and disclosure effects, schema changes, and positive
and negative vectors. External HTTPS namespaces remain under their owners;
support is explicit and fail-closed, never inferred from URI shape.

Validators and air-gapped deployments resolve the exact registry/schema bundle
shipped with the supported specification release. They do not require live DNS
or HTTP resolution. Operators should pin the release artifact and its SHA-256
manifest; unknown identifiers or unavailable pinned resources fail closed.
