# InvarOS Qualification Evidence 1.0.0 — Normative Artifact Specification

**Status:** Normative, v1 schemas frozen.
**Schemas:** `schemas/qualification/transcript.v1.schema.json`, `schemas/qualification/attestation.v1.schema.json`
**Criteria:** `conformance/qualification/1.0.0/schema-vectors.json`
**Authority:** Founder decisions QE-D1 to QE-D15; `invaros`/ADR-002.

Key words MUST, MUST NOT, SHOULD, and MAY are to be interpreted as in RFC 2119.

---

## 1. Governing rule

A qualification claim has the form:

> *Implementation I, built as B, was exercised against criteria C, with outcome
> O, under declared limits L.*

**The subject states what it observed. Only an independent verifier states what
that means.** Everything else in this specification follows from that sentence.

---

## 2. Why two artifacts

The platform can prove what a governed system *did*. It could not prove that the
implementation which produced that proof was ever exercised against its
criteria. Qualification Evidence closes that gap, and it does so with **two**
closed artifact classes rather than one:

| Artifact | Producer | Signs |
|---|---|---|
| `invaros.qualification.transcript/v1` | The shipped subject build | Its own build identity and observed outputs |
| `invaros.qualification.attestation/v1` | An independent Qualification Verifier | The derived conclusion and its semantic domain |

A single artifact counter-signed by the verifier was considered and rejected:
counter-signing mutates the artifact, so its digest changes on countersignature,
and anything binding "the attestation digest" would then have two digests for one
object.

### 2.1 The guarantee, stated precisely

> **No signed qualification verdict originates from the subject.** A verdict MAY
> be independently derived by anyone from the transcript and the canonical
> criteria, but **only an authorized independent verifier signs the
> qualification conclusion consumed by governance.**

**This design MUST NOT be described as making a verdict logically inexpressible
by the subject.** The criteria are public and digest-addressed by design, so any
holder of a transcript — the subject included — can obtain the criteria and
compute pass or fail. That derivability is deliberate: it is what makes
third-party re-derivation possible, and third-party re-derivation is this
programme's load-bearing control.

The structural control is narrower, and is what the schema enforces: **the
transcript artifact cannot carry a signed subject-authored verdict.**

---

## 3. Transcript — `invaros.qualification.transcript/v1`

### 3.1 Closure

Every object in the schema sets `additionalProperties: false`. This is
load-bearing in three separate ways:

1. **No status field exists at any level.** A subject cannot emit a signed
   verdict inside the artifact, even by accident.
2. **`expected_echo` does not exist.** The transcript records what the subject
   *observed*, never what it believed it should observe. Removing it removes the
   transcript's only self-scoring surface.
3. **The metadata firewall is enforced by closure.** There is no free-form
   metadata member, so forbidden keys — `solver_output`, `private_key`, `secret`,
   `token`, `Q`, `matrix`, `distribution` — are rejected wherever they are
   placed, not merely where someone remembered to check.

### 3.2 `criteria` — cardinality and granularity

`criteria` is an **object, never an array**. One transcript covers one subject
and one criteria set. Composition across criteria kinds belongs to consumers,
which resolve several attestations and apply their own policy. **No status-rollup
rule across criteria kinds is defined, and none may be introduced without a v2.**

`criteria.manifest_digest` pins the criteria set **per profile, not per unit**. A
change to any unit voids every attestation over that profile, including for units
that did not change. This is accepted deliberately: per-unit granularity would
fracture the claim into a vector of claims and import the status-rollup problem
the design does not otherwise have.

### 3.3 The consumed-bytes rule — NORMATIVE

> **`criteria.manifest_digest` MUST be computed from the criteria bytes the
> harness actually consumed, never from a declared or configured value.**

This cannot be expressed in JSON Schema. It is enforced by qualification test in
the producing repository, which is the same discipline applied to
`subject.build_digest` — computed from the executing artifact at run time, not
from a build-time constant.

Under this rule the digest *is* an expectations digest: a harness fed substituted
expectations in memory produces a digest that will not match the verifier's own.
That was the sole residual purpose `expected_echo` served.

**Recorded honestly: this defends against a *misconfigured* subject, not a
malicious one.** A malicious subject can report whatever it likes. No schema
choice defends against that; against misconfiguration, the digest of what was
actually read is the correct and sufficient control.

### 3.4 Coverage — absence is stated, never inferred

`coverage.units_not_executed` is **required**. Omitting the gap list is not
expressible. Each entry carries a closed `reason_code`:

| `reason_code` | Meaning |
|---|---|
| `not-implemented` | The subject does not implement the section — a **capability** gap in the subject |
| `environment-unavailable` | The execution environment could not support the unit — a **coverage** gap in the qualification apparatus |
| `criteria-unavailable` | The criteria for the unit could not be resolved |
| `out-of-scope` | The unit is outside the declared scope of this qualification |

**The distinction between a subject capability gap and a qualification-apparatus
coverage gap MUST be available to automated consumers without parsing free
text.** That is the operative requirement; the closed enum is its mechanism, and
the optional `detail` string is advisory only.

In the transcript, `reason_code` is the subject's **factual report** of what it
did not execute and why. This is a statement about execution, not a verdict, and
is therefore within what the subject may sign.

---

## 4. Attestation — `invaros.qualification.attestation/v1`

### 4.1 Status

`status` is one of `qualified`, `not-qualified`, `incomplete`, `indeterminate`.

- **`qualified` requires an empty `units_not_executed`.** A run that passed every
  case it executed but skipped a unit is `incomplete`, never `qualified`. The
  verifier computes this from coverage, not from any subject assertion.
- **`incomplete` is a first-class outcome and is this platform's expected steady
  state**, not an edge case.
- **`indeterminate`** covers verifier-side failure: the criteria digest did not
  resolve, the transcript signature was invalid, or the build digest appears in
  no release manifest. It is distinct from `not-qualified`, which is a
  substantive result about the subject.
- **There is no `partial` status**, and unimplemented sections MUST NOT be
  classified as `not-qualified`.

In the attestation, `reason_code` is **verifier-derived** and is what a consumer
binds to. The verifier is not bound by the subject's declaration, and **a
disagreement between the subject's declared reason code and the verifier's
derived one is a reportable finding**, in the same class as a criteria-digest
mismatch.

### 4.2 `claim` is mandatory

An attestation without a `supported_domain` cannot be emitted. The claim block
carries the statement, the supported domain, the assumptions, and what the
attestation does **not** close.

This exists because the platform already learned the lesson in prose: the failure
mode is quotation out of context, and an artifact carrying a bare pass/fail would
be a regression against a discipline the platform already practises.

An attestation is **not** a safety claim, **not** a substitute for its criteria,
**not** durable across builds, and **not** a substitute for independent human
review.

### 4.3 Validity is digest-bound, never time-bounded

An attestation remains valid for the exact subject build digest, criteria
manifest digest, specification digest, and declared environment it names. It is
**voided by a change to those bound identities, not by elapsed time.**

**Prohibited in v1:** `not_valid_after`, advisory expiry, or any other
clock-dependent validity field. Closure is what makes that prohibition
structural.

This preserves offline and air-gapped verification without introducing a
freshness or trusted-clock dependency.

**Declared limit, recorded explicitly:** the v1 design does not resolve verifier
signing-key compromise. Under recency-based resolution with no revocation
mechanism, a compromised verifier key could issue a newer attestation that
supersedes an honest one. **Time-bounding would not solve this.** The answer is
consumer-side pinning of a set of acceptable verifier public keys, rotated out of
band. **Attestation revocation is not introduced**; attestations are voided by
construction, never revoked. **Key rotation cannot retroactively invalidate
attestations already relied upon under a compromised key** — a residue inherent
to refusing revocation, accepted knowingly.

---

## 5. Signing

Both artifacts are signed with **ES256**, reusing the platform's existing signing
substrate.

| Field | Value |
|---|---|
| `signature.algorithm` | `ES256` |
| `signature.profile_id` | `invaros.crypto.es256-p1363-sha256-qualification/v1` |
| `signature.key_id` | `sha256:<64 hex>` — SHA-256 over DER SubjectPublicKeyInfo |
| `signature.value` | 64-octet fixed-width `r \|\| s`, unpadded base64url (86 characters) |

The byte profile is the platform's `invaros.crypto.es256-p1363-sha256/v1` —
P-256, SHA-256 — specialized per purpose in the established manner of
`invaros.crypto.es256-p1363-sha256-runtime-evidence/v1`.

**`ed25519` is not permitted in v1.** Qualification Evidence introduces no new
cryptographic primitive: the subject signs with the substrate it already has.

The subject's key and the verifier's key are **distinct holders**. Compromise of
the subject's key does not forge an attestation, and compromise of the verifier's
key does not forge a transcript. That asymmetry is a structural benefit of the
two-artifact split and MUST be preserved.

`signature.provider_kind` is present on the transcript from v1 so that a
hardware-rooted signer needs no schema change to arrive. It starts at `Software`.

---

## 6. Emission and verification behaviour

1. **Production is a release step, not a test step.** A transcript emitted from a
   development build is valid evidence *about that build* and useless as release
   evidence, because its `build_digest` appears in no release manifest.
2. **Emission MUST NOT fail on a negative result.** The harness exits non-zero
   only on harness malfunction. A criteria mismatch is transcript *content*. If
   mismatch caused a non-zero exit, a producer could suppress an unfavourable
   transcript by failing early, and the absence of an artifact would be
   indistinguishable from a build that was never qualified.
3. **The verifier MUST obtain the criteria independently.** It MUST NOT take
   criteria from the transcript. Doing so would let the subject choose its own
   exam.
4. **The verifier never declines to produce an artifact.** Every failure path
   yields a signed attestation with an explicit status; silence would be
   indistinguishable from absence.
5. **Verification is repeatable.** The same transcript and criteria always yield
   a byte-identical attestation, modulo verifier version and signature.
6. **No revocation.** A later-discovered defect is recorded as a **new**
   attestation against the same build digest with `status: not-qualified`.
   Consumers resolve by recency over
   `(subject_build_digest, criteria_manifest_digest)`.
7. **Publication is unconditional.** `qualified`, `not-qualified`, and
   `incomplete` alike. **Partial publication is prohibited**: if only favourable
   attestations were published, absence would become evidence of failure and
   publication would stop carrying information.

---

## 7. Criteria kinds

`criteria.kind` is the discriminator that makes the artifact family extensible
without a schema change.

| Kind | Subject | Status |
|---|---|---|
| `conformance-vectors` | Implementation vs. normative vectors | **In scope** |
| `differential-equivalence` | Two independent implementations agreeing | Reserved |
| `fault-matrix` | Crash/SIGKILL boundary results | Reserved |
| `shadow-divergence` | Observed vs. predicted divergence counts | Reserved |
| `soak` | Sustained-run results with duration and rates | Reserved |
| `deployment` | Target-specific deployment qualification | Reserved |

**Only `conformance-vectors` is implemented.** The reserved kinds MUST NOT be
implemented until a real second consumer exists; generalizing before then is
speculative scope growth.

---

## 8. Conformance criteria for this specification

The schemas ship with their own conformance vectors, in
`conformance/qualification/1.0.0/schema-vectors.json`, digest-gated by
`MANIFEST.sha256` on the same terms as the Profile 4 criteria.

A qualification architecture that cannot itself be qualified has the defect it
exists to fix. The vector set is deliberately dominated by **negative** cases: a
gate that has never failed has not been shown to test anything.

An implementation claiming conformance to this specification MUST accept every
case marked `"valid": true` and reject every case marked `"valid": false`.

---

## 9. Conformance status

**The schemas are frozen at v1 and their self-conformance criteria pass. No
qualification artifact has yet been produced by any shipped build, and no
implementation claims conformance to this specification.**

Specifically, as of this document:

- **No transcript exists.** The Qualification Harness is not yet implemented in
  any subject repository.
- **No attestation exists.** The Qualification Verifier is not yet implemented.
- **No third-party re-derivation has been performed.**
- **This specification is not evidence that any component is qualified.** It
  defines the artifact class in which such evidence could be expressed.

Do not measure this programme's success by `status: qualified`. A programme
optimizing for green attestations will produce shallow criteria. **Measure
coverage declared and failures surfaced.**
