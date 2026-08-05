"""Qualification artifact schema gates.

Qualification Evidence WP-01.1 — tests V1, V3, V11, V12, V13, V15, V16, plus the
QE-D15 signing-substrate constraint.

These are the anti-theatre controls. The architecture's own risk register names
attestation theatre (QR1) and self-certification collapse (QR2) as its two
highest risks, and the answer to both is that the guarantees are enforced by
schema rather than by convention. That is what this module checks.

Two layers deliberately:

1. `test_schema_vectors_behave_as_declared` drives every case in
   `conformance/qualification/1.0.0/schema-vectors.json`. Those vectors are the
   published criteria — a third party re-deriving our claims uses this file.
2. The remaining tests assert the same constraints *structurally*, against the
   schema documents themselves. A vector file can be edited; asserting the
   constraint twice, once against data and once against structure, means a
   silent relaxation has to be made in two places to go unnoticed.

The second layer exists because of a specific hazard the architecture names:
`invaros`/ADR-002 records that if test V4 is ever relaxed the ADR "is void in
substance while appearing intact." The same is true of these controls, so they
are checked in a form that does not depend on anyone maintaining the vectors.
"""

from __future__ import annotations

import json
import re

import jsonschema
import pytest

from validator.validate_examples import ROOT, SCHEMA_ROOT, load_json

QUALIFICATION_SCHEMAS = SCHEMA_ROOT / "qualification"
VECTORS = ROOT / "conformance/qualification/1.0.0/schema-vectors.json"

TRANSCRIPT = QUALIFICATION_SCHEMAS / "transcript.v1.schema.json"
ATTESTATION = QUALIFICATION_SCHEMAS / "attestation.v1.schema.json"

#: The closed reason-code vocabulary approved by QE-D7. Not a superset, not a
#: subset: the exact set, so that widening it is a visible edit here too.
REASON_CODES = {
    "not-implemented",
    "environment-unavailable",
    "criteria-unavailable",
    "out-of-scope",
}

#: QE-D7 prohibits a separate `partial` status; QE-D10 requires `indeterminate`
#: to remain distinct from `not-qualified`.
STATUSES = {"qualified", "not-qualified", "incomplete", "indeterminate"}


def _schemas() -> dict[str, dict]:
    return {"transcript": load_json(TRANSCRIPT), "attestation": load_json(ATTESTATION)}


def _validator(schema: dict):
    cls = jsonschema.validators.validator_for(schema)
    cls.check_schema(schema)
    return cls(schema)


def _cases() -> list[dict]:
    return json.loads(VECTORS.read_text(encoding="utf-8"))["cases"]


def _walk(node):
    """Yield every subschema object in a schema document."""
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value)


def _objects_with_properties(schema: dict):
    return [node for node in _walk(schema) if "properties" in node]


def _assert_no_member(schema: dict, name: str) -> None:
    """Assert no subschema declares a member called `name`.

    Deliberately structural rather than a substring search over the file. The
    schemas explain in prose why certain members are absent, and a text search
    would trip over the explanation — which would push a future maintainer
    toward deleting the explanation to make the gate pass. That is exactly
    backwards.
    """
    for node in _objects_with_properties(schema):
        assert name not in node["properties"], (
            f"a subschema declares a `{name}` member: {sorted(node['properties'])}")


# --------------------------------------------------------------------------
# Layer 1 — the published criteria
# --------------------------------------------------------------------------

def test_both_schemas_meta_validate() -> None:
    for schema in _schemas().values():
        jsonschema.validators.validator_for(schema).check_schema(schema)


def test_schema_vectors_cover_both_artifacts_and_both_directions() -> None:
    """A vector set that only contains passing cases proves nothing.

    Phase 0 established the discipline: a gate that has never failed has not
    been shown to test anything. The negative cases are the substance here.
    """
    cases = _cases()
    assert cases, "no schema vectors"
    artifacts = {case["artifact"] for case in cases}
    assert artifacts == {"transcript", "attestation"}
    assert any(case["valid"] for case in cases), "no positive case"
    negatives = [case for case in cases if not case["valid"]]
    assert len(negatives) >= 20, f"only {len(negatives)} negative cases"
    ids = [case["case_id"] for case in cases]
    assert len(ids) == len(set(ids)), "duplicate case_id"


@pytest.mark.parametrize("case", _cases(), ids=lambda case: case["case_id"])
def test_schema_vectors_behave_as_declared(case) -> None:
    schema = _schemas()[case["artifact"]]
    errors = list(_validator(schema).iter_errors(case["document"]))
    if case["valid"]:
        assert not errors, f"{case['case_id']} should validate: {errors[:1]}"
    else:
        assert errors, f"{case['case_id']} should be rejected — {case['rationale']}"


# --------------------------------------------------------------------------
# Layer 2 — structural assertions against the schema documents
# --------------------------------------------------------------------------

def test_v1_transcript_defines_no_status_anywhere() -> None:
    """V1, QR2 — the transcript cannot carry a signed subject-authored verdict.

    Stated precisely, per QE-D2 and `invaros`/ADR-002: this does not make a
    verdict logically inexpressible by the subject. The criteria are public by
    design, so anyone — the subject included — can derive one, and that
    derivability is exactly what makes third-party re-derivation possible. The
    structural control is narrower and is what this test checks: the transcript
    *artifact* has nowhere to put a verdict.
    """
    _assert_no_member(load_json(TRANSCRIPT), "status")


def test_v13_transcript_defines_no_expected_echo() -> None:
    """V13, QE-D13 — `expected_echo` is removed, not optional.

    It was the transcript's only self-scoring surface. Its stated purpose is
    served by `criteria.manifest_digest`, which must be computed from the bytes
    the harness actually consumed — a normative requirement no schema can
    express, enforced instead by test V14 in the producing repository.
    """
    _assert_no_member(load_json(TRANSCRIPT), "expected_echo")


def test_every_object_is_closed() -> None:
    """S6 metadata firewall, V12.

    Closure is the firewall's mechanism. There is no free-form metadata member
    in either artifact, so every forbidden key — `solver_output`, `private_key`,
    `secret`, `token` and the rest — is rejected by `additionalProperties:
    false` at whatever level it is smuggled in. An open object anywhere would
    silently reopen the firewall.
    """
    for name, schema in _schemas().items():
        for node in _objects_with_properties(schema):
            assert node.get("additionalProperties") is False, (
                f"{name}: an object with properties is not closed: {sorted(node['properties'])}")


def test_v16_transcript_criteria_is_an_object_never_an_array() -> None:
    """V16, QE-D12 — strict 1:1 between a transcript, a subject, and a criteria set.

    Composition across criteria kinds belongs to consumers. No status-rollup
    rule is defined here and none may be introduced without a v2.
    """
    criteria = load_json(TRANSCRIPT)["$defs"]["criteria"]
    assert criteria["type"] == "object"


def test_v15_reason_code_vocabulary_is_closed_and_identical_in_both_artifacts() -> None:
    """V15, QE-D7.

    The operative requirement is that a consumer can distinguish a *subject
    capability* gap (`not-implemented`) from a *qualification apparatus*
    coverage gap (`environment-unavailable`) without parsing free text. The
    closed enum is the mechanism, and `detail` is advisory only.

    The two artifacts must share the vocabulary exactly: the reason code is the
    subject's factual report in the transcript and verifier-derived in the
    attestation, and a disagreement between them is only reportable if both are
    drawn from the same set.
    """
    for name, schema in _schemas().items():
        assert set(schema["$defs"]["reasonCode"]["enum"]) == REASON_CODES, name
        entry = schema["$defs"]["unexecutedUnit"]
        assert "reason_code" in entry["required"], f"{name}: reason_code is optional"
        assert "detail" not in entry["required"], f"{name}: free text must stay advisory"


def test_p5_transcript_requires_units_not_executed() -> None:
    """P5 — absence is stated, never inferred.

    Omitting the gap list is not expressible, which is what separates a coverage
    map from a marketing claim.
    """
    assert "units_not_executed" in load_json(TRANSCRIPT)["$defs"]["coverage"]["required"]


def test_v11_attestation_requires_a_claim_with_a_supported_domain() -> None:
    """V11, P4, G3 — the semantic domain of a claim travels with the claim.

    The platform already learned this in prose: SESSION_LEVEL2_QUALIFICATION.md
    §5 exists because "the failure mode is quotation out of context." An
    attestation carrying a bare pass/fail would be a regression against a
    discipline the platform already practises.
    """
    schema = load_json(ATTESTATION)
    assert "claim" in schema["required"]
    claim = schema["$defs"]["claim"]
    for member in ("statement", "supported_domain", "assumptions", "does_not_close"):
        assert member in claim["required"], member
    assert claim["properties"]["supported_domain"]["minItems"] >= 1


def test_v16_attestation_validity_admits_no_clock_dependent_field() -> None:
    """V16, QE-D10 — attestations are digest-bound, never time-bounded.

    An attestation is voided by a change to a bound identity, not by elapsed
    time. This is what preserves offline and air-gapped verification without a
    freshness or trusted-clock dependency. `not_valid_after` and advisory expiry
    are prohibited in v1; closure is what makes the prohibition structural
    rather than a documented convention.
    """
    schema = load_json(ATTESTATION)
    validity = schema["$defs"]["validity"]
    assert validity["additionalProperties"] is False
    assert set(validity["properties"]) == {"binds_to", "voided_by"}
    for prohibited in ("not_valid_after", "expires_at", "advisory_expiry", "valid_until"):
        _assert_no_member(schema, prohibited)


def test_attestation_status_vocabulary_is_exact() -> None:
    """QE-D7 prohibits a separate `partial` status.

    `incomplete` is a first-class outcome and — because `qualified` requires an
    empty `units_not_executed` — it is this platform's expected steady state,
    not an edge case.
    """
    schema = load_json(ATTESTATION)
    assert set(schema["$defs"]["result"]["properties"]["status"]["enum"]) == STATUSES
    assert set(schema["$defs"]["perUnit"]["properties"]["status"]["enum"]) == STATUSES


def test_qe_d15_both_artifacts_pin_the_runtime_es256_substrate() -> None:
    """QE-D15 — Qualification Evidence v1 reuses the Runtime's existing substrate.

    Recorded because the alternative was live until 2026-08-04: the architecture
    originally specified ed25519, which the subject cannot produce. The Runtime
    signs ES256 over mbedTLS and links nothing from `atgs-enterprise-core`, so
    ed25519 would have meant introducing a new cryptographic primitive into the
    shipped Runtime — which the architecture's own non-goals forbid. Pinning the
    algorithm and the purpose-specialized profile id here means a later drift
    back is a test failure rather than a review question.
    """
    for name, schema in _schemas().items():
        signature = schema["$defs"]["signature"]
        assert signature["properties"]["algorithm"]["const"] == "ES256", name
        assert signature["properties"]["profile_id"]["const"] == (
            "invaros.crypto.es256-p1363-sha256-qualification/v1"), name
        assert signature["properties"]["key_id"]["$ref"] == "#/$defs/digest", name
        # 64-octet fixed-width r||s, unpadded base64url, is exactly 86 characters.
        assert signature["properties"]["value"]["pattern"] == "^[A-Za-z0-9_-]{86}$", name
        # The constants above already exclude ed25519. Asserting it by name as
        # well is what makes a future edit read as a deliberate reversal of a
        # founder decision rather than a routine schema tweak.
        assert signature["properties"]["algorithm"]["const"] != "ed25519", name


def test_the_two_artifact_classes_are_separate_and_closed() -> None:
    """architecture §7.1 — two artifacts, deliberately.

    A single artifact counter-signed by the verifier was considered and
    rejected: counter-signing mutates the artifact, so its digest changes on
    countersignature, and anything binding "the attestation digest" would then
    have two digests for one object. Neither document may validate as the other.
    """
    transcript, attestation = load_json(TRANSCRIPT), load_json(ATTESTATION)
    assert transcript["properties"]["schema_id"]["const"] == "invaros.qualification.transcript/v1"
    assert attestation["properties"]["schema_id"]["const"] == "invaros.qualification.attestation/v1"
    assert transcript["$id"] != attestation["$id"]


def test_criteria_kind_reserves_the_later_kinds() -> None:
    """architecture §7.5 — only `conformance-vectors` is in Phase 1 scope.

    The other kinds are enumerated so that adding one later is not a schema
    change. They must not be implemented until a real second consumer exists;
    speculative generalization is the architecture's risk R4/QR4.
    """
    kinds = load_json(TRANSCRIPT)["$defs"]["criteria"]["properties"]["kind"]["enum"]
    assert kinds[0] == "conformance-vectors"
    assert set(kinds) == {
        "conformance-vectors", "differential-equivalence", "fault-matrix",
        "shadow-divergence", "soak", "deployment"}


def test_permanent_schema_uris_match_paths() -> None:
    """The same permanent-URI discipline the Profile 4 schemas are held to."""
    for path in sorted(QUALIFICATION_SCHEMAS.glob("*.json")):
        schema = load_json(path)
        assert schema["$id"] == f"https://tbom.yozi.systems/schemas/qualification/{path.name}"


#: The closed absence vocabulary. Exactly this set, for the same reason
#: REASON_CODES is stated exactly: widening it must be a visible edit here too.
ABSENCE_VALUES = {"unavailable:not-supplied"}


def test_qe1_f1_a_missing_specification_is_stated_and_never_substituted() -> None:
    """QE1-F1 — the substituted-digest defect, made unrepresentable.

    Phase 1 execution found the harness copying `criteria.manifest_digest` into
    `specification_digest` when it could not resolve the specification. The
    substitution was invisible in the signed artifact: a reader saw two digests
    and no indication that one was a stand-in, and a consumer cross-checking the
    specification would have been comparing the criteria manifest with itself.

    The repair is structural rather than procedural. `specification_digest` is
    now either a real digest or a value from a closed absence vocabulary, and
    the absence value carries its own cause — **one** self-describing string,
    so a sentinel and its reason cannot drift apart, because there is only one
    field to get wrong.

    Note what this does *not* do. No schema can tell a genuine digest from a
    substituted one; both match the pattern. What it does is remove the
    *motive*: a producer that cannot resolve the specification now has a
    correct, schema-valid thing to say, so substitution stops being the only way
    to emit a valid artifact. Detection of an actual substitution lives in the
    verifier, which reports a specification digest equal to the criteria
    manifest digest as a finding.
    """
    for name, schema in _schemas().items():
        absence = schema["$defs"]["declaredAbsence"]
        assert set(absence["enum"]) == ABSENCE_VALUES, name
        # Every stated absence must say why. A bare sentinel is not admissible.
        for value in absence["enum"]:
            assert ":" in value and value.split(":", 1)[1], (
                f"{name}: absence value {value!r} carries no cause")
        either = schema["$defs"]["digestOrDeclaredAbsence"]
        assert either["oneOf"] == [
            {"$ref": "#/$defs/digest"}, {"$ref": "#/$defs/declaredAbsence"}], name

    transcript, attestation = load_json(TRANSCRIPT), load_json(ATTESTATION)
    assert transcript["$defs"]["criteria"]["properties"]["specification_digest"][
        "$ref"] == "#/$defs/digestOrDeclaredAbsence"
    assert attestation["properties"]["specification_digest"][
        "$ref"] == "#/$defs/digestOrDeclaredAbsence"

    # The two artifacts must spell an absence identically, or a consumer
    # comparing a transcript with its attestation reads a difference where
    # there is none.
    assert (transcript["$defs"]["declaredAbsence"]["enum"]
            == attestation["$defs"]["declaredAbsence"]["enum"])

    # A declared absence must remain impossible to confuse with a digest.
    digest_pattern = transcript["$defs"]["digest"]["pattern"]
    for value in ABSENCE_VALUES:
        assert not re.match(digest_pattern, value)


def test_qe1_f1_the_specification_digest_stays_required() -> None:
    """Absence is stated, never signalled by omission (architecture P5).

    Making the member optional would have been the smaller edit and the wrong
    one: an omitted field is indistinguishable from a producer that forgot, and
    `units_not_executed` is required for exactly the same reason.
    """
    criteria = load_json(TRANSCRIPT)["$defs"]["criteria"]
    assert "specification_digest" in criteria["required"]
    assert "specification_digest" in load_json(ATTESTATION)["required"]


def test_qe1_f1_the_verifier_can_report_the_substitution_it_cannot_prevent() -> None:
    """The finding vocabulary must be able to name both specification states.

    A verifier that noticed a substituted digest and had nowhere to record it
    would be back to silence, which is the condition this finding exists to end.
    """
    kinds = set(load_json(ATTESTATION)["$defs"]["finding"]["properties"]["kind"]["enum"])
    assert {"specification-unavailable", "specification-digest-substituted"} <= kinds


def test_qe1_f2_build_configuration_bound_is_pinned_from_both_sides() -> None:
    """QE1-F2 — the bound the harness could previously overrun.

    The producer, not the schema, was at fault: it accepted a longer value and
    emitted an artifact that failed its own schema. The bound is asserted here
    so that "fixing" the producer by relaxing the schema is itself a test
    failure, and the vectors exercise both 64 and 65 characters.
    """
    subject = load_json(TRANSCRIPT)["$defs"]["subject"]["properties"]
    assert subject["build_configuration"]["maxLength"] == 64
    assert subject["build_configuration"]["minLength"] == 1
