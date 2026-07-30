# Compatibility Policy

This document explains `profile_id` and `profile_version` handling, the
retained legacy version fields, and what counts as a breaking versus
non-breaking change to a profile. It is a companion to
[SPECIFICATION.md §§ 5, 6, 13, 15](../SPECIFICATION.md) and is informative;
where Edge Network behavior differs, the versioned documents under
[`docs/specifications/`](specifications/) govern.

The InvarOS Runtime (`invaros-runtime`) Profile 4 reference producer and bootstrap discovery now exist.
The preserved first-live captures are historical non-conformant evidence after
independent review identified non-canonical observation arrays. Corrected
builds qualify independently; Profile 3 bytes and fingerprints remain frozen.

## Producer naming

The reference producer for the Edge Network Topology profiles is **InvarOS
Runtime**, whose repository, package, and binary identity is
`invaros-runtime`. It was previously named `invarosd`, and the frozen legacy
Profile 3 assets record that earlier name.

| Legacy name | Canonical name |
| --- | --- |
| `invarosd` | InvarOS Runtime (`invaros-runtime`) |
| `invarosd-v2` | InvarOS Authority (`invaros-authority`) |

Producer naming inside frozen assets is **not** rewritten. The Profile 3
schema and golden artifacts are byte-frozen and hash-pinned; their recorded
producer name is the legacy name at time of publication and remains exactly as
published. Documentation, Profile 4 material, and any future profile use the
canonical name. A serialized or fingerprinted producer identity may only change
under a new `profile_version`, per the breaking-change rules below.

## `profile_id`

`profile_id` identifies a profile family. Consumers combine it with
`profile_version`; exact fingerprint behavior is identified by an algorithm
URI.

| Profile | `profile_id` |
| --- | --- |
| Agentic Topology | `invaros.tbom.profile.agentic_topology` |
| Edge Network Topology | `invaros.tbom.profile.edge_network_topology` |

A consumer that supports more than one revision MUST branch on the
(`profile_id`, `profile_version`) tuple before interpreting any other field
and then validate revision-required algorithm URIs. The legacy Profile 3
schemas do not require `profile_id` (see [Retained legacy fields](#retained-legacy-fields)
below), so a consumer in a multi-profile environment MUST have a defined
behavior for artifacts that omit it — this specification recommends
treating omission as "legacy artifact, select schema out-of-band" rather
than as a validation error, per SPECIFICATION.md § 13.

## `profile_version`

`profile_version` is a semantic version (MAJOR.MINOR.PATCH) of the
profile's schema itself, independent of any particular artifact instance.
Agentic is currently at 3.0.0. Edge Network 3.0.0 is frozen as legacy
compatibility behavior, and Edge Network 4.0.0 is a pre-implementation
draft. This is the version field that advances as
profiles evolve; see [Breaking versus non-breaking changes](#breaking-versus-non-breaking-changes)
below for what triggers which kind of bump.

## Retained legacy fields

Each profile retains one legacy version field that predates the
`profile_id` scheme:

| Profile | Legacy field | Constant value |
| --- | --- | --- |
| Agentic Topology | `schema_version` | `"tbom-v3.0"` |
| Edge Network Topology | `tbom_version` | `"3.0.0"` |

These fields exist so that artifacts produced before `profile_id` was
introduced remain structurally valid and recognizable to consumers that
only ever handled one profile. They are **not** intended to distinguish
profiles from one another — both profiles' legacy fields happen to encode
the same `3.0.0`-generation marker despite describing entirely different
topologies. Do not write consumer logic that branches on `schema_version`
or `tbom_version` alone to decide which schema to validate against; use the
(`profile_id`, `profile_version`) tuple for that.

Both legacy fields are pinned by `const` in their respective schemas and
are not expected to change value as part of ordinary profile evolution.
A future change to either legacy field's constant value would itself be a
breaking change (see below), and is not anticipated by this
specification.

## Compatibility expectations

Profile 4 bootstrap discovery is an additive correction to the draft contract. It preserves the meaning and fingerprint bytes of every valid-intent structural and observation projection. Successful artifacts now explicitly distinguish absent from valid intent; invalid intent remains a discovery error and never becomes a successful artifact.

- An artifact valid under a given `profile_version` remains valid under
  that same `profile_version` forever; profile schemas in this repository
  are not modified retroactively except to fix a genuine copying or
  consistency error between the schema and its reference implementation.
- A consumer built against a given MAJOR.MINOR of a profile SHOULD
  continue to accept artifacts of later MINOR/PATCH versions of the same
  profile, since non-breaking changes by definition only add optionality.
- A consumer SHOULD NOT assume forward compatibility across a MAJOR
  version bump without consulting the corresponding CHANGELOG.md entry.
- Profile 3 and Profile 4 Edge artifacts are separate complete artifacts;
  fields or algorithms are never mixed or upgraded in place.
- Profile 3 has no scheduled removal date. Its golden artifacts and
  fingerprints are permanent compatibility assets.

## Extension policy

New, optional fields MAY be added to a profile without a MAJOR version
bump, provided:

- the field is not required,
- the field does not change the meaning of any existing field,
- `additionalProperties: false` is preserved everywhere else in the
  schema (i.e., the new field is explicitly enumerated, not admitted by
  loosening closure elsewhere), and
- the field does not introduce a new way to smuggle forbidden metadata
  (SPECIFICATION.md § 10) — any new open-ended object field MUST itself be
  subject to an equivalent forbidden-key rule.

New profiles are added as entirely new schema files with their own
`profile_id`, following SPECIFICATION.md § 15. Adding a new profile is
never a breaking change to an existing profile.

## Breaking versus non-breaking changes

**Non-breaking** (at most a MINOR `profile_version` bump):

- Adding a new optional field.
- Widening an `enum` to admit new valid values while retaining all
  previously valid ones (for example, adding a new `node_type` value to
  a future Edge Network revision).
- Clarifying documentation or descriptions within the schema (`title`,
  `description` fields) without changing validation behavior.
- Fixing a schema defect where the schema was inconsistent with its
  reference implementation (a genuine copying/consistency error), such
  that the fix only makes the schema accept artifacts the reference
  implementation could already legitimately produce.

**Breaking** (MUST be at least a MAJOR `profile_version` bump, and MUST be
recorded in [CHANGELOG.md](../CHANGELOG.md)):

- Removing or renaming a field.
- Making an optional field required, or vice versa.
- Narrowing an `enum`, `const`, or `pattern` such that a previously valid
  value becomes invalid.
- Changing a fingerprint field's name, format, or computation basis
  (SPECIFICATION.md § 7).
- Changing either legacy version field's constant value
  (`schema_version`, `tbom_version`).
- Changing `profile_id` itself for an existing profile (this would, in
  effect, be introducing a new profile rather than revising the existing
  one).
- Loosening `additionalProperties: false` to admit arbitrary fields.

Any change not clearly covered by the non-breaking list above SHOULD be
treated as breaking by default.
