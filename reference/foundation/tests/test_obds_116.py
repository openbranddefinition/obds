"""OBDS 1.1.6 normative cases.

Five defects were reported against 1.1.5 by an outreach gate. Each is closed
here, and each test below is written so that it fails on 1.1.5 and passes on
1.1.6. Where a test pins a boundary, it calls the implementation at that exact
instant rather than comparing fixture constants to one another: the 1.1.5 test
this file replaces asserted only that three timestamps in a fixture agreed with
each other, so four separate wrong comparisons survived the whole suite.
"""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from obds_ref.canonical import (
    UNICODE_PIN_VERSION,
    artefact_hash,
    canonical_json_bytes,
    identity_key,
    manifest_content_hash,
)
from obds_ref.compiler import (
    _parse_timestamp,
    _valid_at,
    build_target,
    load_data,
    validate_manifest,
)
from obds_ref.runtime import _artifact_valid_at, run_with_model

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT.parents[1]


def example(name):
    base = PACKAGE_ROOT / "examples" / name
    return load_data(base / "manifest.yaml"), load_data(base / "build-plan.yaml")


def reseal(manifest):
    """Recompute the approval hash after editing a manifest in a test."""
    manifest["approval"].pop("contentHash", None)
    manifest["approval"]["contentHash"] = manifest_content_hash(manifest)
    return manifest


def bind(manifest, plan):
    plan["manifestRef"]["contentHash"] = manifest["approval"]["contentHash"]
    return plan


# --- G-01: section 14.3c, the Unicode version is pinned ---------------------

# U+0897 ARABIC PEPET is unassigned in Unicode 15.1.0 and is a non-zero
# combining class mark from 16.0.0 onward. Under 15.1.0 it does not reorder
# against U+0323 COMBINING DOT BELOW; from 16.0.0 it does. That single code
# point moved canonical bytes, manifestContentHash and governedResultHash
# between two runtimes running byte-identical code.
UNASSIGNED_IN_PIN = "\u0897"


def test_pinned_unicode_version_is_declared():
    assert UNICODE_PIN_VERSION == "15.1.0"


def test_code_point_outside_the_pinned_version_is_rejected_in_a_value():
    with pytest.raises(ValueError) as excinfo:
        canonical_json_bytes({"s": f"a{UNASSIGNED_IN_PIN}\u0323z"})
    assert "U+0897" in str(excinfo.value)
    assert UNICODE_PIN_VERSION in str(excinfo.value)


def test_code_point_outside_the_pinned_version_is_rejected_in_a_key():
    with pytest.raises(ValueError) as excinfo:
        canonical_json_bytes({f"k{UNASSIGNED_IN_PIN}": 1})
    assert "U+0897" in str(excinfo.value)


def test_keys_that_only_collide_under_a_later_unicode_version_are_rejected():
    """The two orderings of U+0897 and U+0323 are one key from 16.0.0 on.

    A 15.1.0 runtime saw two distinct keys and canonicalised both; a 16.0.0
    runtime rejected the same document as a duplicate key. Two conforming
    implementations disagreed on whether a document was valid at all. Pinned,
    both refuse it for the same reason, before the question can arise.
    """
    document = {
        f"a{UNASSIGNED_IN_PIN}\u0323": 1,
        f"a\u0323{UNASSIGNED_IN_PIN}": 2,
    }
    with pytest.raises(ValueError) as excinfo:
        canonical_json_bytes(document)
    assert "U+0897" in str(excinfo.value)


@pytest.mark.parametrize("text", [
    "plain ascii",
    "caf\u00e9",           # NFC
    "cafe\u0301",          # NFD, normalises to the line above
    "\U0001F600",          # astral, assigned long before the pin
    "\uffff",              # permanent noncharacter, never assignable
    "\ufdd0",              # permanent noncharacter
    "\u2028\u2029",  # escaped by section 14.3b, still assigned
])
def test_assigned_and_noncharacter_code_points_stay_accepted(text):
    canonical_json_bytes({"s": text})


def test_every_pinned_range_endpoint_is_admitted():
    """Both ends of every range are inclusive.

    The first implementation of the guard located a code point by the parity of
    a single bisect over the flattened bounds, which is right inside a range and
    wrong on its upper endpoint: all 715 upper endpoints, U+10FFFF among them,
    were rejected as unassigned. No vector and no example used one, so nothing
    else in the suite noticed. This walks the table.
    """
    from obds_ref.canonical import _UNICODE_PIN_ENDS, _UNICODE_PIN_STARTS, _assigned_in_pinned_unicode

    assert len(_UNICODE_PIN_STARTS) == len(_UNICODE_PIN_ENDS) == 715
    for start, end in zip(_UNICODE_PIN_STARTS, _UNICODE_PIN_ENDS):
        assert _assigned_in_pinned_unicode(start), hex(start)
        assert _assigned_in_pinned_unicode(end), hex(end)
        if start > 0:
            assert not _assigned_in_pinned_unicode(start - 1), hex(start - 1)
        if end < 0x10FFFF:
            assert not _assigned_in_pinned_unicode(end + 1), hex(end + 1)


def test_pin_table_identity_is_fixed():
    """The shipped table is the contract, so its identity is pinned here.

    Deliberately host-independent: it asserts the table, not the runtime's own
    Unicode database, so it runs and passes on every supported host rather than
    skipping on a newer one. A test that skips is not evidence.
    """
    from obds_ref.canonical import _UNICODE_PIN_ENDS, _UNICODE_PIN_STARTS, _assigned_in_pinned_unicode

    assert len(_UNICODE_PIN_STARTS) == 715
    admitted = sum(end - start + 1 for start, end in zip(_UNICODE_PIN_STARTS, _UNICODE_PIN_ENDS))
    assert admitted == 287412

    # Sorted and disjoint, which the loader also enforces.
    for index in range(1, len(_UNICODE_PIN_STARTS)):
        assert _UNICODE_PIN_STARTS[index] > _UNICODE_PIN_ENDS[index - 1]

    # Surrogates are never a character. Python rejects them when encoding UTF-8
    # and JavaScript would emit a \uXXXX escape, so admitting them was a
    # cross-language divergence with no valid document behind it.
    for code_point in range(0xD800, 0xE000):
        assert not _assigned_in_pinned_unicode(code_point), hex(code_point)

    # All 66 permanent noncharacters are admitted.
    noncharacters = list(range(0xFDD0, 0xFDF0)) + [
        plane * 0x10000 + offset for plane in range(17) for offset in (0xFFFE, 0xFFFF)
    ]
    assert len(noncharacters) == 66
    for code_point in noncharacters:
        assert _assigned_in_pinned_unicode(code_point), hex(code_point)

    # Assigned in 15.1.0 or earlier, so admitted. U+11F41 and U+10EFD arrived in
    # 15.0 and are exactly the characters an older Unicode 14 host would
    # normalise differently, which is why canonical.py refuses to import there.
    for code_point in (0x41, 0xE9, 0x377, 0x38C, 0x1F600, 0x11F41, 0x10EFD):
        assert _assigned_in_pinned_unicode(code_point), hex(code_point)
    # Assigned only after the pin, or never.
    for code_point in (0x897, 0x105C0, 0x16D40, 0x11BC0):
        assert not _assigned_in_pinned_unicode(code_point), hex(code_point)


def test_the_host_unicode_database_is_at_or_after_the_pin():
    import unicodedata

    host = tuple(int(part) for part in unicodedata.unidata_version.split("."))
    pinned = tuple(int(part) for part in UNICODE_PIN_VERSION.split("."))
    assert host >= pinned, (
        "section 14.3c requires a Unicode database at or after the pinned version; "
        "canonical.py refuses to import otherwise"
    )


def test_noncharacters_are_admitted_because_unicode_can_never_assign_them():
    """U+FFFF appears in the published canonical vectors and must keep working.

    Noncharacters are permanently unassigned by Unicode policy, so their
    combining class and decomposition can never change and they are
    normalisation-stable in every version. Excluding them would have broken a
    frozen vector for no determinism gain.
    """
    assert canonical_json_bytes({"k": "\uffff"}) == b'{"k":"\xef\xbf\xbf"}'


# --- G-02: section 8.0a, canonical identity ---------------------------------

NFC_SUBJECT = "design.prim\u00e4rfarbe"
NFD_SUBJECT = "design.prima\u0308rfarbe"


def _two_elements_on_one_subject(manifest, subject_broad, subject_narrow):
    template = copy.deepcopy(manifest["elements"][0])
    broad = copy.deepcopy(template)
    broad.update({
        "id": "design.pf.global",
        "subject": subject_broad,
        "scope": {},
        "value": {"name": "global colour"},
    })
    narrow = copy.deepcopy(template)
    narrow.update({
        "id": "design.pf.at",
        "subject": subject_narrow,
        "scope": {"markets": ["at"]},
        "value": {"name": "austrian colour"},
    })
    manifest["elements"] = [manifest["elements"][0], broad, narrow]
    return reseal(manifest)


def _governed(manifest, plan, *, market="at"):
    target = copy.deepcopy(plan["targets"][0])
    target["scope"] = {"locales": ["en"], "outputTypes": ["brand-query"], "markets": [market]}
    result = build_target(manifest, bind(manifest, plan), target)
    assert result.status == "ready", [error.code for error in result.errors]
    return result.artefact


def test_canonically_equivalent_subjects_are_one_semantic_subject():
    """One approved manifest must not produce two governed results.

    `contentHash` is computed over canonical bytes, which are NFC, so an NFD and
    an NFC spelling of the same subject are the same approved snapshot. Until
    1.1.6 subject grouping compared raw document bytes, so the NFD document
    resolved to two subjects: the broad value and the narrow override that was
    supposed to replace it both survived as governed truth.
    """
    manifest_nfd, plan_nfd = example("foundation-minimal")
    manifest_nfc, plan_nfc = example("foundation-minimal")
    mixed = _two_elements_on_one_subject(manifest_nfd, NFD_SUBJECT, NFC_SUBJECT)
    same = _two_elements_on_one_subject(manifest_nfc, NFC_SUBJECT, NFC_SUBJECT)

    assert mixed["approval"]["contentHash"] == same["approval"]["contentHash"]

    mixed_artefact = _governed(mixed, plan_nfd)
    same_artefact = _governed(same, plan_nfc)

    assert mixed_artefact["governedResultHash"] == same_artefact["governedResultHash"]
    assert mixed_artefact["availableElementIds"] == same_artefact["availableElementIds"]
    assert "design.pf.global" not in mixed_artefact["availableElementIds"]


def test_canonically_equivalent_element_ids_are_a_duplicate():
    manifest, _ = example("foundation-minimal")
    template = copy.deepcopy(manifest["elements"][0])
    first = copy.deepcopy(template)
    first["id"] = "context.caf\u00e9"
    second = copy.deepcopy(template)
    second["id"] = "context.cafe\u0301"
    manifest["elements"] = [manifest["elements"][0], first, second]
    reseal(manifest)

    errors = validate_manifest(manifest)
    assert any("duplicate element id" in error for error in errors), errors


def test_requirements_resolve_across_normalisation_forms():
    manifest, plan = example("foundation-minimal")
    template = copy.deepcopy(manifest["elements"][0])
    element = copy.deepcopy(template)
    element["id"] = "context.caf\u00e9"
    element["subject"] = "context.caf\u00e9"
    element["value"] = {"name": "cafe"}
    manifest["elements"] = [manifest["elements"][0], element]
    reseal(manifest)

    target = copy.deepcopy(plan["targets"][0])
    target["requiresDefined"] = ["structure.brand", "context.cafe\u0301"]
    result = build_target(manifest, bind(manifest, plan), target)

    assert result.status == "ready", [error.code for error in result.errors]


def test_identity_key_is_the_canonical_form():
    assert identity_key("context.cafe\u0301") == identity_key("context.caf\u00e9")


# --- G-03: section 11.5, elementValueRef binds the governed winner ---------

def _manifest_with_value_ref(*, referenced_state="defined", validity=None, scope=None,
                             extra_elements=()):
    manifest, plan = example("foundation-minimal")
    template = copy.deepcopy(manifest["elements"][0])

    disclaimer = copy.deepcopy(template)
    disclaimer.update({
        "id": "ctx.disclaimer",
        "subject": "ctx.disclaimer",
        "family": "context",
        "kind": "note",
        "nature": "knowledge",
        "state": referenced_state,
        "scope": copy.deepcopy(scope) if scope is not None else {},
        "validity": copy.deepcopy(validity) if validity else {"from": None, "to": None},
        "value": {"text": "APPROVED DISCLAIMER"},
    })
    if referenced_state != "defined":
        disclaimer.pop("value", None)
        disclaimer.pop("valueContractRef", None)

    rule = copy.deepcopy(template)
    rule.update({
        "id": "rule.lit",
        "subject": "rule.lit",
        "family": "rules",
        "kind": "rule",
        "nature": "fact",
        "state": "defined",
        "scope": {},
        "validity": {"from": None, "to": None},
        "value": {
            "statement": "Output must carry the approved disclaimer.",
            "obligation": "require",
            "enforcement": "block",
            "validationMode": "deterministic",
            "checks": [{
                "primitive": "literal_required",
                "phase": "postflight",
                "params": {
                    "elementValueRef": {"elementId": "ctx.disclaimer", "path": "text"},
                    "match": "exact",
                    "appliesTo": "output",
                    "literal": "PLACEHOLDER",
                },
            }],
            "condition": {},
            "requirement": {},
            "references": [],
        },
    })
    from obds_ref.canonical import sha256_id, value_shape_hash
    schema = load_data(ROOT / "value-schemas/3.0.0/rule.schema.json")
    rule["valueContractRef"] = "vc.rule.literal"
    manifest["valueContracts"].append({"id":"vc.rule.literal", "family":"rules", "kind":"rule",
        "schemaRef":schema["$id"], "schemaHash":sha256_id(schema), "shapeHash":value_shape_hash(rule["value"])})

    manifest["elements"] = [manifest["elements"][0], disclaimer, rule, *copy.deepcopy(list(extra_elements))]
    reseal(manifest)
    return manifest, bind(manifest, plan)


def _build_default(manifest, plan, *, as_of=None, target_scope=None):
    plan = copy.deepcopy(plan)
    if as_of:
        plan["asOf"] = as_of
    target = copy.deepcopy(plan["targets"][0])
    if target_scope is not None:
        target["scope"] = copy.deepcopy(target_scope)
    return build_target(manifest, plan, target)


def test_element_value_ref_binds_the_current_governed_value():
    manifest, plan = _manifest_with_value_ref()
    result = _build_default(manifest, plan)
    assert result.status == "ready", [error.code for error in result.errors]
    checks = result.artefact["compiledChecks"]
    assert [check["params"]["literal"] for check in checks] == ["APPROVED DISCLAIMER"]


@pytest.mark.parametrize("case,kwargs,build_kwargs,expected_code", [
    (
        "expired",
        {"validity": {"from": None, "to": "2026-06-01T00:00:00Z"}},
        {},
        "OBDS-BUILD-REQUIRED-EXPIRED",
    ),
    (
        "future",
        {"validity": {"from": "2027-01-01T00:00:00Z", "to": None}},
        {},
        "OBDS-BUILD-REQUIRED-EXPIRED",
    ),
    (
        "out-of-scope",
        {"scope": {"markets": ["de"]}},
        {"target_scope": {"locales": ["en"], "outputTypes": ["brand-query"], "markets": ["at"]}},
        "OBDS-BUILD-REQUIRED-OUT-OF-SCOPE",
    ),
    (
        "unknown",
        {"referenced_state": "unknown"},
        {},
        "OBDS-BUILD-REQUIRED-NOT-DEFINED",
    ),
    (
        "not_defined",
        {"referenced_state": "not_defined"},
        {},
        "OBDS-BUILD-REQUIRED-NOT-DEFINED",
    ),
    (
        "not_applicable",
        {"referenced_state": "not_applicable"},
        {},
        "OBDS-BUILD-REQUIRED-NOT-DEFINED",
    ),
])
def test_element_value_ref_fails_closed_on_ungoverned_truth(case, kwargs, build_kwargs, expected_code):
    """A check may only bind truth that is governed for this target and asOf.

    Until 1.1.6 the reference resolved against the raw manifest snapshot and
    tested `state` alone, so a value that had expired, did not apply to the
    target, or had lost its subject was still compiled into an active blocking
    check. Time alone was enough to trigger it: no authoring error required.
    """
    manifest, plan = _manifest_with_value_ref(**kwargs)
    result = _build_default(manifest, plan, **build_kwargs)

    assert result.status == "failed", case
    codes = [error.code for error in result.errors]
    assert expected_code in codes, f"{case}: {codes}"
    assert result.artefact is None, case


def test_element_value_ref_cannot_bind_a_subject_loser():
    """The narrow override wins the subject, so the broad value must not bind."""
    manifest, plan = example("foundation-minimal")
    manifest, plan = _manifest_with_value_ref()
    template = copy.deepcopy(manifest["elements"][0])
    override = copy.deepcopy(template)
    override.update({
        "id": "ctx.disclaimer.at",
        "subject": "ctx.disclaimer",
        "family": "context",
        "kind": "note",
        "nature": "knowledge",
        "state": "defined",
        "scope": {"markets": ["at"]},
        "validity": {"from": None, "to": None},
        "value": {"text": "AUSTRIAN DISCLAIMER"},
    })
    manifest["elements"].append(override)
    reseal(manifest)
    plan = bind(manifest, plan)

    result = _build_default(
        manifest, plan,
        target_scope={"locales": ["en"], "outputTypes": ["brand-query"], "markets": ["at"]},
    )

    # The reference names ctx.disclaimer, which lost its subject to the override.
    assert result.status == "failed"
    assert "OBDS-BUILD-REQUIRED-NOT-DEFINED" in [error.code for error in result.errors]
    assert result.artefact is None


def test_element_value_ref_in_an_unresolved_conflict_fails_closed():
    manifest, plan = _manifest_with_value_ref()
    template = copy.deepcopy(manifest["elements"][0])
    rival = copy.deepcopy(template)
    rival.update({
        "id": "ctx.disclaimer.social",
        "subject": "ctx.disclaimer",
        "family": "context",
        "kind": "note",
        "nature": "knowledge",
        "state": "defined",
        "scope": {"outputTypes": ["brand-query"]},
        "validity": {"from": None, "to": None},
        "value": {"text": "RIVAL DISCLAIMER"},
    })
    other = copy.deepcopy(template)
    other.update({
        "id": "ctx.disclaimer.en",
        "subject": "ctx.disclaimer",
        "family": "context",
        "kind": "note",
        "nature": "knowledge",
        "state": "defined",
        "scope": {"locales": ["en"]},
        "validity": {"from": None, "to": None},
        "value": {"text": "OTHER DISCLAIMER"},
    })
    manifest["elements"] += [rival, other]
    reseal(manifest)
    plan = bind(manifest, plan)

    result = _build_default(manifest, plan)

    assert result.status == "failed"
    assert "OBDS-BUILD-SUBJECT-CONFLICT" in [error.code for error in result.errors]
    assert result.artefact is None


# --- G-04: section 10.2a, conflict relevance --------------------------------

def _conflicting_rules(first_value, second_value, *, requires=None):
    """Two RULES on one subject with incomparable scopes."""
    manifest, plan = example("foundation-minimal")
    template = copy.deepcopy(manifest["elements"][0])
    elements = [manifest["elements"][0]]

    for index, value in enumerate(v for v in (first_value, second_value) if v is not None):
        rule = copy.deepcopy(template)
        rule.update({
            "id": f"rules.tone.{index}",
            "subject": "subject:tone",
            "family": "rules",
            "kind": "rule",
            "nature": "knowledge",
            "state": "defined",
            "scope": {"locales": ["en"]} if index == 0 else {"outputTypes": ["brand-query"]},
            "validity": {"from": None, "to": None},
            "value": copy.deepcopy(value),
        })
        rule.pop("valueContractRef", None)
        elements.append(rule)

    if requires is not None:
        dependency = copy.deepcopy(template)
        dependency.update({
            "id": "context.efficacy-claim",
            "subject": "context.efficacy-claim",
            "family": "context",
            "kind": "guidance",
            "nature": "knowledge",
            "state": requires,
            "scope": {},
            "validity": {"from": None, "to": None},
        })
        if requires == "defined":
            dependency["value"] = {"text": "claim"}
        else:
            dependency.pop("value", None)
            dependency.pop("valueContractRef", None)
        elements.append(dependency)

    manifest["elements"] = elements
    reseal(manifest)
    return manifest, bind(manifest, plan)


def _rule_value(**overrides):
    value = {
        "statement": "placeholder",
        "obligation": "require",
        "enforcement": "inform",
        "validationMode": "advisory",
        "condition": {},
        "requirement": {},
        "references": [],
    }
    value.update(overrides)
    return value


def _relevance(manifest, plan):
    result = _build_default(manifest, plan)
    flags = [conflict.get("decisionRelevant") for conflict in result.conflicts]
    return result, flags


def test_conflict_is_relevant_when_the_requiring_rule_is_in_it():
    """Repairing a manifest must never turn a passing build into a failing one.

    One of the two incomparable RULES declares a dependency that is `unknown`.
    On 1.1.5 the conflict was judged irrelevant, the RULE never bound, and the
    target built. Deleting the rival RULE let the surviving RULE bind, and the
    same target then failed. The defect made the manifest defect protective.
    """
    manifest, plan = _conflicting_rules(
        _rule_value(requiresDefinedRefs=["context.efficacy-claim"]),
        _rule_value(),
        requires="unknown",
    )
    result, flags = _relevance(manifest, plan)

    assert flags == [True]
    assert result.status == "failed"
    assert "OBDS-BUILD-SUBJECT-CONFLICT" in [error.code for error in result.errors]
    assert result.artefact is None


def test_conflict_is_relevant_when_only_one_winner_contributes_a_check():
    manifest, plan = _conflicting_rules(
        _rule_value(
            validationMode="deterministic",
            checks=[{
                "primitive": "literal_required",
                "phase": "postflight",
                "params": {"literal": "REQUIRED TEXT", "match": "exact", "appliesTo": "output"},
            }],
        ),
        _rule_value(),
    )
    result, flags = _relevance(manifest, plan)

    assert flags == [True]
    assert result.status == "failed"


def test_conflict_is_relevant_when_only_one_winner_is_a_hard_boundary():
    manifest, plan = _conflicting_rules(
        _rule_value(enforcement="block"),
        _rule_value(),
    )
    result, flags = _relevance(manifest, plan)

    assert flags == [True]
    assert result.status == "failed"


def test_conflict_is_relevant_when_only_one_winner_prohibits():
    manifest, plan = _conflicting_rules(
        _rule_value(obligation="prohibit"),
        _rule_value(),
    )
    result, flags = _relevance(manifest, plan)

    assert flags == [True]
    assert result.status == "failed"


def test_conflict_that_changes_nothing_stays_non_blocking():
    """Not every conflict is a blocker. It must still be reported.

    Two advisory RULES with no dependency, no check and no prohibition change
    nothing this target reads, so section 10.2a still allows the build. The
    conflict is recorded so a manifest defect is never silently discarded.

    3.0.0 inverted this and 3.0.2 restores it. Neither of these rules enters
    HARD_BOUNDARIES — section 14.1 admits a RULE there on `block`,
    `require_approval` or `obligation: prohibit`, and these carry none — neither
    contributes a compiled check, and neither declares a dependency. With both
    projections `none` there is no slot they reach. A conflict this target
    cannot observe must not fail it; the four tests above prove the other side
    of the same boundary.
    """
    manifest, plan = _conflicting_rules(_rule_value(), _rule_value())
    plan = copy.deepcopy(plan)
    plan["targets"][0]["styleTexture"] = {"mode": "none", "elementIds": []}
    plan["targets"][0]["stateMap"] = {"mode": "none", "kinds": []}
    result, flags = _relevance(manifest, plan)

    assert flags == [False]
    assert result.status == "ready", [error.code for error in result.errors]
    assert result.conflicts, "an irrelevant conflict must still be reported"


# --- G-05: section 10.1, the half-open validity interval --------------------

FROM = "2026-06-01T00:00:00Z"
TO = "2026-12-01T00:00:00Z"
SECOND = timedelta(seconds=1)


def _instant(raw):
    return _parse_timestamp(raw, field_name="test")


BOUNDARY_ELEMENT = {"validity": {"from": FROM, "to": TO}}


@pytest.mark.parametrize("label,as_of,expected", [
    ("from minus one second", _instant(FROM) - SECOND, False),
    ("from exactly", _instant(FROM), True),
    ("to minus one second", _instant(TO) - SECOND, True),
    ("to exactly", _instant(TO), False),
])
def test_compiler_validity_interval_is_half_open(label, as_of, expected):
    """`from` is inclusive, `to` is exclusive, executed at the exact instants.

    Four single-character mutations in `_valid_at` — `<` to `<=` and `>=` to `>`
    on either bound — survived the entire 1.1.5 suite, because the test that
    claimed to pin this compared three fixture timestamps to one another and
    never called the function.
    """
    element = {"id": "structure.brand", **copy.deepcopy(BOUNDARY_ELEMENT)}
    assert _valid_at(element, as_of) is expected, label


@pytest.mark.parametrize("label,as_of,expected", [
    ("from as a +02:00 offset", "2026-06-01T02:00:00+02:00", True),
    ("one second before from, offset form", "2026-06-01T01:59:59+02:00", False),
    ("to as a +02:00 offset", "2026-12-01T02:00:00+02:00", False),
    ("one second before to, offset form", "2026-12-01T01:59:59+02:00", True),
    ("from with fractional seconds", "2026-06-01T00:00:00.000Z", True),
    ("just under from, fractional", "2026-05-31T23:59:59.999Z", False),
    ("just under to, fractional", "2026-11-30T23:59:59.999Z", True),
    ("to with fractional seconds", "2026-12-01T00:00:00.000Z", False),
])
def test_compiler_validity_boundary_is_instant_not_spelling(label, as_of, expected):
    element = {"id": "structure.brand", **copy.deepcopy(BOUNDARY_ELEMENT)}
    assert _valid_at(element, _instant(as_of)) is expected, label


@pytest.mark.parametrize("label,as_of,expected_status", [
    ("one second before from", "2026-05-31T23:59:59Z", "failed"),
    ("from exactly", FROM, "ready"),
    ("one second before to", "2026-11-30T23:59:59Z", "ready"),
    ("to exactly", TO, "failed"),
])
def test_build_target_applies_the_half_open_interval(label, as_of, expected_status):
    """The same four instants through the whole build, not just the predicate."""
    manifest, plan = example("foundation-minimal")
    manifest["elements"][0]["validity"] = {"from": FROM, "to": TO}
    reseal(manifest)
    result = _build_default(manifest, bind(manifest, plan), as_of=as_of)

    assert result.status == expected_status, label
    if expected_status == "failed":
        assert "OBDS-BUILD-REQUIRED-EXPIRED" in [error.code for error in result.errors], label
        assert result.artefact is None, label


def _artefact_with_window():
    manifest, plan = example("foundation-minimal")
    manifest["elements"][0]["validity"] = {"from": FROM, "to": TO}
    reseal(manifest)
    result = _build_default(manifest, bind(manifest, plan), as_of="2026-08-28T00:00:00Z")
    assert result.status == "ready", [error.code for error in result.errors]
    artefact = result.artefact
    assert artefact["validFrom"] == FROM
    assert artefact["validTo"] == TO
    return artefact


@pytest.mark.parametrize("label,runtime_at,expected", [
    ("one second before validFrom", _instant(FROM) - SECOND, False),
    ("validFrom exactly", _instant(FROM), True),
    ("one second before validTo", _instant(TO) - SECOND, True),
    ("validTo exactly", _instant(TO), False),
])
def test_runtime_artifact_validity_is_half_open(label, runtime_at, expected):
    artefact = _artefact_with_window()
    assert _artifact_valid_at(artefact, runtime_at) is expected, label


@pytest.mark.parametrize("label,runtime_at,expect_release", [
    ("one second before validFrom", _instant(FROM) - SECOND, False),
    ("validFrom exactly", _instant(FROM), True),
    ("one second before validTo", _instant(TO) - SECOND, True),
    ("validTo exactly", _instant(TO), False),
])
def test_run_with_model_refuses_outside_the_half_open_window(label, runtime_at, expect_release):
    """End to end: the runtime must not call a model outside the window."""
    artefact = _artefact_with_window()
    calls = []

    def model(prompt):
        calls.append(prompt)
        return "output"

    record = run_with_model(
        artefact,
        task_input="task",
        model=model,
        target_id=artefact["targetId"],
        runtime_at=runtime_at,
    )

    if expect_release:
        assert record["decision"] != "no_valid_artifact", label
        assert calls, label
    else:
        assert record["decision"] == "no_valid_artifact", label
        assert not calls, label


def test_artefact_hash_still_covers_the_window():
    artefact = _artefact_with_window()
    assert artefact["artifactHash"] == artefact_hash(artefact)


# --- 1.1.6 review findings, closed before release ---------------------------

def test_surrogates_are_rejected_by_the_pin_before_encoding():
    """A surrogate is not a character, and the two runtimes disagreed on it.

    Python refused it when encoding UTF-8; JavaScript emitted a \\uD800 escape.
    Excluding the range from the pin makes both refuse it in the same place, for
    the same stated reason, before normalisation.
    """
    with pytest.raises(ValueError) as excinfo:
        canonical_json_bytes({"s": "a\ud800b"})
    assert "U+D800" in str(excinfo.value)


def test_canonically_equivalent_identities_do_not_move_the_artifact_hash():
    """Slot order is an identity ordering too.

    The first 1.1.6 candidate normalised the governed selection but still sorted
    the four rendered slots and the compiled checks on raw bytes, so two
    canonically equivalent manifests agreed on governedResultHash and disagreed
    on artifactHash: the same truth, rendered in a different order.
    """
    nfd_manifest, nfd_plan = example("foundation-minimal")
    nfc_manifest, nfc_plan = example("foundation-minimal")

    def with_two_facts(manifest, first_id):
        template = copy.deepcopy(manifest["elements"][0])
        first = copy.deepcopy(template)
        first.update({"id": first_id, "subject": first_id, "value": {"name": "one"}})
        second = copy.deepcopy(template)
        second.update({"id": "context.caff", "subject": "context.caff", "value": {"name": "two"}})
        manifest["elements"] = [manifest["elements"][0], first, second]
        return reseal(manifest)

    # Stored NFD, "context.cafe" + U+0301 sorts before "context.caff" on raw
    # UTF-16 and after it on the canonical form, so the two spellings would
    # order the slots differently.
    mixed = with_two_facts(nfd_manifest, "context.cafe\u0301")
    same = with_two_facts(nfc_manifest, "context.caf\u00e9")
    assert mixed["approval"]["contentHash"] == same["approval"]["contentHash"]

    mixed_artefact = _build_default(mixed, bind(mixed, nfd_plan)).artefact
    same_artefact = _build_default(same, bind(same, nfc_plan)).artefact

    assert mixed_artefact["governedResultHash"] == same_artefact["governedResultHash"]
    assert mixed_artefact["slots"] == same_artefact["slots"]
    assert mixed_artefact["artifactHash"] == same_artefact["artifactHash"]


def test_state_map_kinds_match_across_normalisation_forms():
    """A governed vocabulary comparison is an NFC comparison.

    Comparing `stateMap.kinds` to an element `kind` on raw bytes dropped an
    element out of STATE_MAP silently, with no error anywhere.
    """
    counts = []
    for manifest_kind, target_kind in (("hinw\u00e9is", "hinw\u00e9is"), ("hinwe\u0301is", "hinw\u00e9is")):
        manifest, plan = example("foundation-minimal")
        template = copy.deepcopy(manifest["elements"][0])
        gap = copy.deepcopy(template)
        gap.update({
            "id": "context.gap",
            "subject": "context.gap",
            "family": "context",
            "kind": manifest_kind,
            "nature": "knowledge",
            "state": "unknown",
        })
        gap.pop("value", None)
        gap.pop("valueContractRef", None)
        manifest["elements"] = [manifest["elements"][0], gap]
        reseal(manifest)
        plan = copy.deepcopy(bind(manifest, plan))
        plan["targets"][0]["stateMap"] = {"mode": "kinds", "kinds": [target_kind]}
        result = _build_default(manifest, plan)
        assert result.status == "ready", [error.code for error in result.errors]
        counts.append(result.artefact["stateMapEntryCount"])

    assert counts == [1, 1], counts


def test_canonically_equivalent_value_contract_ids_are_a_duplicate():
    manifest, _ = example("foundation-minimal")
    base = copy.deepcopy(manifest["valueContracts"][0])
    first = copy.deepcopy(base)
    first["id"] = base["id"] + ".caf\u00e9"
    second = copy.deepcopy(base)
    second["id"] = base["id"] + ".cafe\u0301"
    manifest["valueContracts"] = [base, first, second]
    reseal(manifest)

    errors = validate_manifest(manifest)
    assert any("duplicate value contract id" in error for error in errors), errors


def test_conflict_on_eligible_guidance_is_decision_relevant():
    """A target that declares guidance eligible reads that subject.

    Otherwise the artefact declares eligible guidance that is not in
    availableElementIds, and Context Assembly refuses it downstream.
    """
    manifest, plan = _conflicting_rules(_rule_value(), _rule_value())
    plan = copy.deepcopy(plan)
    target = plan["targets"][0]
    target["styleTexture"] = {"mode": "none", "elementIds": []}
    target["stateMap"] = {"mode": "none", "kinds": []}
    target["contextAssembly"] = {"eligibleGuidanceIds": ["rules.tone.0"]}
    result = _build_default(manifest, plan)

    assert [c.get("decisionRelevant") for c in result.conflicts] == [True]
    assert result.status == "failed"
    assert result.artefact is None


def test_an_applicable_prohibition_reaches_hard_boundaries():
    """Section 14.1: hardBoundaries carries applicable prohibitions.

    The slot was filtered on enforcement alone, so an applicable
    `obligation: prohibit` RULE with advisory enforcement appeared nowhere in
    the artefact. Section 14.1 lists prohibitions and blocking rules as two
    separate reasons to be in the slot, and says so twice.
    """
    manifest, plan = _conflicting_rules(_rule_value(obligation="prohibit"), None)
    plan = copy.deepcopy(plan)
    plan["targets"][0]["styleTexture"] = {"mode": "none", "elementIds": []}
    plan["targets"][0]["stateMap"] = {"mode": "none", "kinds": []}

    result = _build_default(manifest, plan)

    assert result.status == "ready", [error.code for error in result.errors]
    assert "rules.tone.0" in result.artefact["slots"]["hardBoundaries"]


def test_a_conflict_over_a_prohibition_is_decision_relevant():
    """Because section 14.1 puts it in every target's compiled context."""
    manifest, plan = _conflicting_rules(
        _rule_value(obligation="prohibit"),
        _rule_value(),
    )
    plan = copy.deepcopy(plan)
    plan["targets"][0]["styleTexture"] = {"mode": "none", "elementIds": []}
    plan["targets"][0]["stateMap"] = {"mode": "none", "kinds": []}

    result = _build_default(manifest, plan)

    assert [c.get("decisionRelevant") for c in result.conflicts] == [True]
    assert result.status == "failed"
    assert result.artefact is None



@pytest.mark.parametrize("old_form,new_form", [
    ("caf\u00e9", "cafe\u0301"),
    ("cafe\u0301", "caf\u00e9"),
])
def test_a_canonically_equivalent_contract_id_is_not_a_contract_change(old_form, new_form):
    """Section 8.0a: a respelling is not a change.

    manifest_change_report compared value contract ids and valueContractRef as
    raw bytes, so an NFC/NFD respelling plus an annotation-only edit reported
    changeKinds ["annotations", "contract", "metadata"] and refused a PATCH.
    Both directions are run, so dropping the normalisation on either side of the
    comparison is caught.
    """
    from obds_ref.compiler import manifest_change_report

    old_manifest, _ = example("foundation-minimal")
    contract_id = old_manifest["valueContracts"][0]["id"] + "." + old_form
    old_manifest["valueContracts"][0]["id"] = contract_id
    old_manifest["elements"][0]["valueContractRef"] = contract_id
    reseal(old_manifest)

    new_manifest, _ = example("foundation-minimal")
    twin_id = new_manifest["valueContracts"][0]["id"] + "." + new_form
    new_manifest["valueContracts"][0]["id"] = twin_id
    new_manifest["elements"][0]["valueContractRef"] = twin_id
    new_manifest["elements"][0]["annotations"] = ["a note"]
    new_manifest["version"] = "1.0.1"
    reseal(new_manifest)

    report = manifest_change_report(old_manifest, new_manifest)
    changed = report["changed"]
    assert len(changed) == 1, report
    assert changed[0]["changeKinds"] == ["annotations"], changed[0]["changeKinds"]


def test_conflict_element_ids_are_ordered_on_the_canonical_identity():
    """One approved snapshot must not report its conflict two ways."""
    orders = []
    for first_id in ("rules.cafe\u0301", "rules.caf\u00e9"):
        manifest, plan = _conflicting_rules(_rule_value(), _rule_value())
        for element in manifest["elements"]:
            if element["id"] == "rules.tone.0":
                element["id"] = first_id
            elif element["id"] == "rules.tone.1":
                element["id"] = "rules.caff"
        reseal(manifest)
        plan = copy.deepcopy(bind(manifest, plan))
        plan["targets"][0]["styleTexture"] = {"mode": "none", "elementIds": []}
        plan["targets"][0]["stateMap"] = {"mode": "none", "kinds": []}
        result = _build_default(manifest, plan)
        assert result.conflicts, "the conflict must be reported"
        orders.append(result.conflicts[0]["elementIds"])

    assert orders[0] == orders[1], orders


def test_identity_equality_is_nfc_only_and_line_separators_are_not_identities():
    """Section 8.0a as corrected in 3.0.0.

    This test previously asserted that `a\rb` and `a\nb` are two identities,
    which is what 2.0.0 shipped and what section 8.0a said. It is inverted here
    rather than deleted, because the old expectation was the defect: the
    canonical form is structurally incapable of carrying that distinction —
    section 14.3b says `\r` cannot occur in canonical output — so a manifest
    declaring both canonicalised to a manifest declaring one, with the
    `contentHash` unchanged and the CR element's value surviving under the LF
    identity. Two documents, one `approval.contentHash`, two governed truths.

    Section 14.3 already rejects that collision for object keys. Identity
    strings behave as keys, so they inherit the rule. NFC equality is unchanged
    and still the whole of identity equality for every admissible string.
    """
    assert identity_key("context.caf\u0065\u0301") == identity_key("context.caf\u00e9")
    for separator in ("\r", "\n"):
        with pytest.raises(ValueError):
            identity_key(f"context.a{separator}b")
    # And no wider. Step 2 does not touch these, they survive canonicalisation,
    # and no collision was demonstrated for them.
    for preserved in ("\u0085", "\u2028", "\u2029"):
        assert identity_key(f"context.a{preserved}b") == f"context.a{preserved}b"

    manifest, _ = example("foundation-minimal")
    template = copy.deepcopy(manifest["elements"][0])
    first = copy.deepcopy(template)
    first["id"] = "context.a\rb"
    second = copy.deepcopy(template)
    second["id"] = "context.a\nb"
    manifest["elements"] = [manifest["elements"][0], first, second]

    errors = validate_manifest(manifest, verify_hash=False)
    assert any("CARRIAGE RETURN" in error for error in errors), errors
    assert any("LINE FEED" in error for error in errors), errors
    assert not any("duplicate element id" in error for error in errors), errors
