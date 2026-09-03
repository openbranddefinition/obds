"""OBDS 2.0.0 normative cases.

Three defects were reported against 1.1.6 by an outreach gate. Two are
specification defects and one is a conformance-evidence defect. The evidence
defect is the reason most of this file exists: the release gate accepted a list
of case names without resolving them, and four of the fourteen section 26.2
requirements named prose rather than a case at all. The tests here are the
evidence those requirements now point at, so each one asserts the expected
content of a governed decision rather than a relative property between two runs.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from obds_ref.canonical import manifest_content_hash, sha256_id
from obds_ref.governed_io import _resolve_plain_scalar
from obds_ref.compiler import (
    ValidationFailure,
    build_target,
    load_data,
    validate_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT.parents[1]
def _release() -> str:
    """The release this package is, read from the specification it ships.

    Naming `OBDS-2.0.0.md` here made this test a document that has to be edited
    at every release, which is the drift class the release gate was built for.
    The package carries exactly one `OBDS-<x.y.z>.md`, so the release is derived
    from it.
    """
    import re as _release_re

    names = sorted(
        path.name for path in PACKAGE_ROOT.glob("OBDS-*.md")
        if _release_re.fullmatch(r"OBDS-\d+\.\d+\.\d+\.md", path.name)
    )
    assert len(names) == 1, f"expected one normative specification, found {names}"
    return names[0][len("OBDS-"):-len(".md")]


RELEASE = _release()


def example(name):
    base = PACKAGE_ROOT / "examples" / name
    return load_data(base / "manifest.yaml"), load_data(base / "build-plan.yaml")


def reseal(manifest):
    manifest["approval"].pop("contentHash", None)
    manifest["approval"]["contentHash"] = manifest_content_hash(manifest)
    return manifest


def bind(manifest, plan):
    plan["manifestRef"]["contentHash"] = manifest["approval"]["contentHash"]
    return plan


def build(manifest, plan, **target_overrides):
    plan = copy.deepcopy(bind(manifest, plan))
    target = plan["targets"][0]
    target.update(copy.deepcopy(target_overrides))
    return build_target(manifest, plan, target)


# --- G-A: section 28.1, governed YAML scalar resolution ---------------------

def load_scalar(tmp_path, text, suffix):
    path = tmp_path / f"probe{suffix}"
    path.write_text('{"a": %s}\n' % text, encoding="utf-8")
    return load_data(path)


@pytest.mark.parametrize("text,expected", [
    ("true", True),
    ("false", False),
    ("null", None),
    ("0", 0),
    ("-0", 0),
    ("17", 17),
    ("1.0", 1.0),
    ("1e3", 1000.0),
    ("1.0e3", 1000.0),
    ('"1e3"', "1e3"),
    ('"2026-09-01"', "2026-09-01"),
])
def test_the_same_bytes_mean_the_same_thing_as_json_and_as_yaml(tmp_path, text, expected):
    """Section 28.1. The canonical hash of a document is not its filename.

    Before 2.0.0 the loader inherited PyYAML's YAML 1.1 implicit resolvers, so
    `{"a": 1e3}` was the number 1000 read as JSON and the string "1e3" read as
    YAML: one byte sequence, two governed values, two canonical hashes.
    """
    as_json = load_scalar(tmp_path, text, ".json")
    as_yaml = load_scalar(tmp_path, text, ".yaml")

    assert as_json == {"a": expected}
    assert as_yaml == {"a": expected}
    assert sha256_id(as_json) == sha256_id(as_yaml)


@pytest.mark.parametrize("text,why", [
    ("017", "leading-zero integer"),
    ("+017", "signed leading-zero integer"),
    ("1_000", "digit separator"),
    ("12:30", "sexagesimal"),
    ("1:2:3", "sexagesimal"),
    ("2026-09-01", "date shaped"),
    ("2026-9-1T00:00:00Z", "date shaped, short fields with a time"),
    ("0x1f", "hexadecimal"),
    ("0b1010", "binary"),
    ("0o17", "octal"),
    ("~", "YAML 1.1 null shorthand"),
    (".inf", "non-finite"),
    (".nan", "non-finite"),
])
def test_ambiguous_plain_scalars_are_rejected_not_guessed(tmp_path, text, why):
    """Section 28.1: a form two YAML versions read differently is refused.

    Resolving it either way would make an accepted document's meaning depend on
    which YAML version the reader carries, which is the defect. Quoting it, or
    writing it in a form JSON also accepts, is always available.
    """
    path = tmp_path / "probe.yaml"
    path.write_text("a: %s\n" % text, encoding="utf-8")
    with pytest.raises(Exception) as excinfo:
        load_data(path)
    assert "ambiguous plain scalar" in str(excinfo.value), why


@pytest.mark.parametrize("text,expected", [
    ("yes", "yes"),
    ("no", "no"),
    ("NO", "NO"),
    ("on", "on"),
    ("off", "off"),
    ("y", "y"),
    ("N", "N"),
    ("Null", None),
    ("TRUE", True),
    ("plain text", "plain text"),
])
def test_plain_scalars_resolve_under_the_core_schema(tmp_path, text, expected):
    path = tmp_path / "probe.yaml"
    path.write_text("a: %s\n" % text, encoding="utf-8")
    assert load_data(path) == {"a": expected}


# --- G-C: section 14.3a, conflicts and the governed result hash -------------

def _two_elements_on_one_subject(*, second_element, second_out_of_scope=False):
    """Two incomparable elements on one subject, optionally only one of them.

    Deliberately CONTEXT rather than RULES: a defined RULES element must carry a
    valueContractRef, so a rules-based fixture would be a manifest no conforming
    implementation may accept, and a governed behaviour asserted on an invalid
    document proves nothing. This one validates clean.
    """
    manifest, plan = example("foundation-minimal")
    template = copy.deepcopy(manifest["elements"][0])
    elements = [manifest["elements"][0]]
    for index in range(2 if second_element else 1):
        element = copy.deepcopy(template)
        element.update({
            "id": f"context.tone.{index}",
            "subject": "subject:tone",
            "family": "context",
            "kind": "guidance",
            "nature": "knowledge",
            "state": "defined",
            "scope": (
                {"locales": ["en"]}
                if index == 0
                else ({"locales": ["de"]} if second_out_of_scope else {"outputTypes": ["brand-query"]})
            ),
            "validity": {"from": None, "to": None},
            "value": {"text": f"tone {index}"},
        })
        element.pop("valueContractRef", None)
        elements.append(element)
    manifest["elements"] = elements
    reseal(manifest)
    assert validate_manifest(manifest) == [], "the fixture manifest must be valid"
    return manifest, plan


NO_PROJECTION = {
    "styleTexture": {"mode": "none", "elementIds": []},
    "stateMap": {"mode": "none", "kinds": []},
}


def test_a_decision_relevant_conflict_has_no_governed_result_hash():
    """Case A. Section 14.3a, first bullet."""
    manifest, plan = _two_elements_on_one_subject(second_element=True)
    result = build(manifest, plan, **{
        "styleTexture": {"mode": "all", "elementIds": []},
        "stateMap": {"mode": "none", "kinds": []},
    })

    assert result.status == "failed"
    assert "OBDS-BUILD-SUBJECT-CONFLICT" in [error.code for error in result.errors]
    assert result.artefact is None
    assert [conflict["decisionRelevant"] for conflict in result.conflicts] == [True]


def test_an_applicable_conflict_has_no_governed_result_whatever_the_projection():
    """Case B, inverted in 3.0.0.

    This asserted that a target reading neither candidate through its
    projections still produced a governed result. Section 14.3a's own MUST is
    that a projection policy must not change `selection`; deciding whether a
    `selection` exists at all is that prohibition violated more severely. Both
    candidates are applicable, so the conflict is decision-relevant and the
    target fails — with the conflict reported, as before.
    """
    manifest, plan = _two_elements_on_one_subject(second_element=True)
    result = build(manifest, plan, **NO_PROJECTION)

    assert result.status == "failed"
    assert "OBDS-BUILD-SUBJECT-CONFLICT" in [error.code for error in result.errors]
    assert result.artefact is None
    assert [conflict["decisionRelevant"] for conflict in result.conflicts] == [True]
    assert result.conflicts[0]["subject"] == "subject:tone"


def test_a_preserved_irrelevant_conflict_and_an_absent_subject_share_the_hash():
    """Cases B and C, restated in 3.0.0 on the class that actually survives.

    The preserved-irrelevance class is non-empty and principled: a subject whose
    incomparable maximal elements are not all in `applicable(T)` — here because
    the second candidate's scope does not match the target — cannot change this
    target's governed result, because at most one of them is applicable at all.
    Such a conflict must still appear in `conflicts[]`, marked, which is what
    section 10.2a says and what the 2.0.0 reference did the opposite of: it
    reported only the conflicts that *were* applicable and silently discarded
    exactly the class the paragraph exists for.

    `governedResultHash` identifies the governed result, not the diagnostic
    history that produced it, so both builds must hash the same.
    """
    conflicted, plan_b = _two_elements_on_one_subject(second_element=True, second_out_of_scope=True)
    absent, plan_c = _two_elements_on_one_subject(second_element=False)

    result_b = build(conflicted, plan_b, **NO_PROJECTION)
    result_c = build(absent, plan_c, **NO_PROJECTION)

    assert result_b.status == "ready", [error.code for error in result_b.errors]
    assert result_c.status == "ready", [error.code for error in result_c.errors]
    assert result_b.artefact["governedResultHash"] == result_c.artefact["governedResultHash"]
    assert [conflict["decisionRelevant"] for conflict in result_b.conflicts] == [False]
    assert not result_c.conflicts


# --- G-B: section 26.2 evidence that names these cases ----------------------

def test_exact_build_plans_bind_one_manifest():
    """Section 26.2: exact Build Plans."""
    manifest, plan = example("foundation-minimal")
    ok = build(manifest, plan)
    assert ok.status == "ready", [error.code for error in ok.errors]

    wrong = copy.deepcopy(bind(manifest, plan))
    wrong["manifestRef"]["contentHash"] = "sha256:" + "0" * 64
    failed = build_target(manifest, wrong, wrong["targets"][0])
    assert failed.status == "failed"
    assert [error.code for error in failed.errors] == ["OBDS-BUILD-MANIFEST-REF"]
    assert failed.artefact is None


def _manifest_with_three_kinds():
    """One defined fact, one defined knowledge element, two knowledge gaps."""
    manifest, plan = example("foundation-minimal")
    template = copy.deepcopy(manifest["elements"][0])
    elements = [manifest["elements"][0]]

    guidance = copy.deepcopy(template)
    guidance.update({
        "id": "context.voice", "subject": "context.voice", "family": "context",
        "kind": "guidance", "nature": "knowledge", "state": "defined",
        "scope": {}, "validity": {"from": None, "to": None},
        "value": {"text": "Warm and precise."},
    })
    elements.append(guidance)

    for kind in ("note", "guidance"):
        gap = copy.deepcopy(template)
        gap.update({
            "id": f"context.gap.{kind}", "subject": f"context.gap.{kind}",
            "family": "context", "kind": kind, "nature": "knowledge",
            "state": "unknown", "scope": {}, "validity": {"from": None, "to": None},
        })
        gap.pop("value", None)
        gap.pop("valueContractRef", None)
        elements.append(gap)

    manifest["elements"] = elements
    reseal(manifest)
    return manifest, plan


def test_explicit_context_selection_decides_slot_contents():
    """Section 26.2: explicit context selection.

    Asserted as contents, not as a relative property. The evidence this
    requirement previously named was prose, and four separate single-line
    inversions of the projection logic survived the whole suite: styleTexture
    `none` failing to clear the slot, `selected` failing to filter, stateMap
    `kinds` ignoring its filter, and STATE_MAP always coming out empty.
    """
    manifest, plan = _manifest_with_three_kinds()

    every = build(manifest, plan, **{
        "styleTexture": {"mode": "all", "elementIds": []},
        "stateMap": {"mode": "all_applicable", "kinds": []},
    })
    assert every.status == "ready", [error.code for error in every.errors]
    assert "context.voice" in every.artefact["slots"]["styleTexture"]
    assert every.artefact["stateMapEntryCount"] == 2
    assert "context.gap.note" in every.artefact["slots"]["stateMap"]
    assert "context.gap.guidance" in every.artefact["slots"]["stateMap"]

    cleared = build(manifest, plan, **{
        "styleTexture": {"mode": "none", "elementIds": []},
        "stateMap": {"mode": "none", "kinds": []},
    })
    assert cleared.artefact["slots"]["styleTexture"] == ""
    assert cleared.artefact["slots"]["stateMap"] == ""
    assert cleared.artefact["stateMapEntryCount"] == 0
    assert "context.voice" not in cleared.artefact["includedElementIds"]

    selected = build(manifest, plan, **{
        "styleTexture": {"mode": "selected", "elementIds": ["context.voice"]},
        "stateMap": {"mode": "kinds", "kinds": ["note"]},
    })
    assert "context.voice" in selected.artefact["slots"]["styleTexture"]
    assert selected.artefact["stateMapEntryCount"] == 1
    assert "context.gap.note" in selected.artefact["slots"]["stateMap"]
    assert "context.gap.guidance" not in selected.artefact["slots"]["stateMap"]


def test_foundation_check_registry_v1_compiles_and_refuses():
    """Section 26.2: Foundation Check Registry v1."""
    from obds_ref.checks import SUPPORTED_PRIMITIVES, validate_check

    manifest, plan = example("foundation-minimal")
    template = copy.deepcopy(manifest["elements"][0])
    rule = copy.deepcopy(template)
    rule.update({
        "id": "rules.disclaimer", "subject": "rules.disclaimer", "family": "rules",
        "kind": "rule", "nature": "knowledge", "state": "defined", "scope": {},
        "validity": {"from": None, "to": None},
        "value": {
            "statement": "Output must carry the disclaimer.",
            "obligation": "require", "enforcement": "block",
            "validationMode": "deterministic",
            "checks": [{
                "primitive": "literal_required", "phase": "postflight",
                "params": {"literal": "APPROVED", "match": "exact", "appliesTo": "output"},
            }],
            "condition": {}, "requirement": {}, "references": [],
        },
    })
    rule.pop("valueContractRef", None)
    manifest["elements"] = [manifest["elements"][0], rule]
    reseal(manifest)

    result = build(manifest, plan)
    assert result.status == "ready", [error.code for error in result.errors]
    compiled = result.artefact["compiledChecks"]
    assert [item["primitive"] for item in compiled] == ["literal_required"]
    assert compiled[0]["params"]["literal"] == "APPROVED"
    assert compiled[0]["enforcement"] == "block"

    assert "literal_required" in SUPPORTED_PRIMITIVES
    assert validate_check({"primitive": "no_such_primitive", "phase": "postflight", "params": {}})

    manifest["elements"][1]["value"]["checks"][0]["primitive"] = "no_such_primitive"
    reseal(manifest)
    refused = build(manifest, plan)
    assert refused.status == "failed"
    assert "OBDS-CHECK-INVALID" in [error.code for error in refused.errors]
    assert refused.artefact is None


def test_per_slot_token_reporting_is_the_sum_of_its_slots():
    """Section 26.2: per-slot token reporting."""
    manifest, plan = _manifest_with_three_kinds()
    result = build(manifest, plan, **{
        "styleTexture": {"mode": "all", "elementIds": []},
        "stateMap": {"mode": "all_applicable", "kinds": []},
    })
    assert result.status == "ready", [error.code for error in result.errors]

    counts = result.token_counts
    slots = result.artefact["slots"]
    for name in ("hardBoundaries", "factGrounding", "stateMap", "styleTexture"):
        expected = len(slots[name].split())
        assert counts[name] == expected, name
    assert counts["total"] == sum(
        counts[name] for name in ("hardBoundaries", "factGrounding", "stateMap", "styleTexture")
    )
    assert counts["max"] == plan["targets"][0]["maxTokens"]
    assert result.artefact["tokenBudget"]["actual"] == counts["total"]
    assert result.artefact["tokenBudget"]["max"] == counts["max"]


def test_canonical_json_artefacts_are_written_canonically(tmp_path):
    """Section 26.2: canonical JSON artefacts.

    The case this requirement previously named compared canonical_json_bytes
    with itself and never built or read an artefact. This one builds, reads the
    bytes off disk, and checks they are the canonical form of the artefact.
    """
    from obds_ref.canonical import artefact_hash, canonical_json_bytes
    from obds_ref.compiler import build_all

    manifest, plan = example("foundation-minimal")
    out = tmp_path / "out"
    build_all(manifest, bind(manifest, plan), output_dir=out)

    written = sorted(out.glob("*.context.json"))
    assert len(written) == 1, [item.name for item in written]

    on_disk = load_data(written[0])
    # The file is readable JSON; what must be canonical is the data model it
    # carries. Reading it back and canonicalising it has to reproduce the hash
    # the artefact carries, or the artefact does not identify itself.
    assert on_disk["artifactHash"] == artefact_hash(on_disk)
    assert canonical_json_bytes(on_disk) == canonical_json_bytes(load_data(written[0]))
    assert b"\r" not in written[0].read_bytes()


def test_exact_target_loading_builds_only_the_named_target(tmp_path):
    """Section 26.2: exact target loading.

    The case this requirement previously named exercised artefact-hash refusal,
    which is a different rule. This one puts three targets in one plan and
    checks that each build produces exactly its own artefact.
    """
    from obds_ref.compiler import build_all

    manifest, plan = example("foundation-minimal")
    plan = copy.deepcopy(bind(manifest, plan))
    first = plan["targets"][0]
    for suffix in ("second", "third"):
        extra = copy.deepcopy(first)
        extra["id"] = f"{first['id']}-{suffix}"
        plan["targets"].append(extra)

    out = tmp_path / "out"
    report = build_all(manifest, plan, output_dir=out)

    built = sorted(path.name for path in out.glob("*.context.json"))
    assert built == sorted(f"{target['id']}.context.json" for target in plan["targets"])
    for entry in report["targets"]:
        assert entry["status"] == "ready", entry["targetId"]
        assert entry["artifactRef"] == f"{entry['targetId']}.context.json"


@pytest.mark.parametrize("name,character", [
    ("U+0085 NEXT LINE", "\u0085"),
    ("U+2028 LINE SEPARATOR", "\u2028"),
    ("U+2029 PARAGRAPH SEPARATOR", "\u2029"),
])
def test_raw_version_sensitive_line_breaks_are_rejected(tmp_path, name, character):
    """Section 28.1 pins the YAML version, not only the scalar rules.

    YAML 1.1 counts these three as line breaks and YAML 1.2 does not. PyYAML
    turns a raw U+0085 inside a double-quoted scalar into a space; a YAML 1.2
    parser keeps the character. Same bytes, two governed strings, two hashes.
    """
    path = tmp_path / "probe.yaml"
    path.write_text('a: "x%sy"\n' % character, encoding="utf-8")
    with pytest.raises(Exception) as excinfo:
        load_data(path)
    assert "raw" in str(excinfo.value) and name.split()[0] in str(excinfo.value)


def test_the_same_characters_written_as_escapes_are_accepted(tmp_path):
    """They are governed content, not forbidden content."""
    path = tmp_path / "probe.yaml"
    path.write_text('a: "x\\u0085y"\n', encoding="utf-8")
    assert load_data(path) == {"a": "x\u0085y"}


def test_anchors_and_aliases_stay_available(tmp_path):
    """An alias expands to the same node in every YAML version.

    An earlier draft of this release refused them, which made a Build Plan this
    project ships invalid. Only the merge key is refused, because `<<` is a
    YAML 1.1 construct that other readers expand and this one would not.
    """
    path = tmp_path / "probe.yaml"
    path.write_text("b: &shared {p: 1}\nc: *shared\n", encoding="utf-8")
    assert load_data(path) == {"b": {"p": 1}, "c": {"p": 1}}

    merged = tmp_path / "merge.yaml"
    merged.write_text("b: {p: 1}\nc:\n  <<: {p: 1}\n", encoding="utf-8")
    with pytest.raises(Exception) as excinfo:
        load_data(merged)
    assert "merge key" in str(excinfo.value)


def test_the_shipped_governed_documents_all_load(tmp_path):
    """The rule may not invalidate a document this release ships."""
    roots = sorted(
        path for path in PACKAGE_ROOT.rglob("*.yaml")
        if "answers" not in path.parts and "spec" not in path.parts
        and "__pycache__" not in path.parts and ".venv" not in str(path)
        # `fixtures/governed-input/` is the official section 28.1 conformance
        # corpus: every document in it exists to be refused, and the suite
        # asserts the refusal. Loading them here would assert the opposite.
        and "governed-input" not in path.parts
    )
    assert len(roots) >= 25, len(roots)
    for path in roots:
        load_data(path)


def test_an_explicit_tag_is_refused_including_the_non_specific_one(tmp_path):
    for source in ('a: !!str 1e3\n', 'a: ! 1e3\n', 'a: !!int 017\n'):
        path = tmp_path / "probe.yaml"
        path.write_text(source, encoding="utf-8")
        with pytest.raises(Exception) as excinfo:
            load_data(path)
        assert "explicit tag" in str(excinfo.value), source


@pytest.mark.parametrize("text,expected", [
    ("+abc", "+abc"),
    ("+", "+"),
    ("3 apples", "3 apples"),
    ("1e3 apples", "1e3 apples"),
])
def test_the_rejection_table_is_closed(tmp_path, text, expected):
    """Only the listed forms are refused; everything else falls through.

    An earlier draft rejected any scalar beginning with a plus, which the table
    does not say and which refused ordinary strings.
    """
    path = tmp_path / "probe.yaml"
    path.write_text("a: %s\n" % text, encoding="utf-8")
    assert load_data(path) == {"a": expected}


# --- what the second independent review found, and what closes it ------------

@pytest.mark.parametrize("text", [
    "+42abc", "+.5abc", "0bface", "0b2", "0oabc", "0o9", "0x", "017abc",
])
def test_the_rejection_patterns_are_anchored(tmp_path, text):
    """Section 28.1: "anything else is a string" means anything else.

    The first draft matched a leading plus with no end condition and allowed
    hexadecimal digits for every base, so ordinary strings were refused.
    """
    path = tmp_path / "probe.yaml"
    path.write_text("a: %s\n" % text, encoding="utf-8")
    assert load_data(path) == {"a": text}


@pytest.mark.parametrize("text", [
    "017", "+42", "+1.5", "1.", ".5", "1_000", "12:30", "1:2:3",
    "0x1f", "0o17", "0b1010", "~", "2026-09-01",
])
def test_the_rejection_table_still_refuses_every_listed_form(tmp_path, text):
    path = tmp_path / "probe.yaml"
    path.write_text("a: %s\n" % text, encoding="utf-8")
    with pytest.raises(Exception):
        load_data(path)


def test_a_plain_integer_is_not_a_digit_separator(tmp_path):
    """The separator pattern must require a separator.

    Anchoring the table in one pass dropped the underscore requirement, which
    would have refused every plain integer. The suite caught it; this pins it.
    """
    path = tmp_path / "probe.yaml"
    path.write_text("a: 1\nb: 42\nc: -7\n", encoding="utf-8")
    assert load_data(path) == {"a": 1, "b": 42, "c": -7}


@pytest.mark.parametrize("value", [
    {"a": "x\u0085y"},
    {"a": "x\u2028y"},
    {"a": "x\u2029y"},
    {"<<": 1, "b": 2},
    {"a": "1e3", "b": "017", "c": "12:30", "d": "~"},
    {"a": "plain", "b": 1000.0, "c": True, "d": None},
])
def test_the_writer_emits_only_what_the_reader_accepts(tmp_path, value):
    """Section 28.1 binds the writer as much as the reader.

    An earlier draft emitted a raw U+2028 in a single-quoted scalar and a plain
    `<<` key, then refused both on the way back in. A writer and a reader that
    disagree are the same defect in the other direction.
    """
    from obds_ref.compiler import save_yaml

    path = tmp_path / "roundtrip.yaml"
    save_yaml(path, value)
    assert load_data(path) == value


def test_a_quoted_merge_shaped_key_is_an_ordinary_string_key(tmp_path):
    """`<<` is a merge key only when written plain."""
    plain = tmp_path / "plain.yaml"
    plain.write_text("b: {p: 1}\nc:\n  <<: {p: 1}\n", encoding="utf-8")
    with pytest.raises(Exception) as excinfo:
        load_data(plain)
    assert "merge key" in str(excinfo.value)

    quoted = tmp_path / "quoted.yaml"
    quoted.write_text("'<<': 1\nb: 2\n", encoding="utf-8")
    assert load_data(quoted) == {"<<": 1, "b": 2}


def test_aliases_cannot_hide_a_duplicate_key(tmp_path):
    """Anchors and aliases are permitted, and change nothing else.

    An alias expands to the same node in every YAML version, so it produces one
    data model; the duplicate-key rules apply to the expansion like anything
    else, and a recursive alias is refused.
    """
    duplicate = tmp_path / "dup.yaml"
    duplicate.write_text("a: &k name\nm:\n  name: 1\n  *k : 2\n", encoding="utf-8")
    with pytest.raises(Exception) as excinfo:
        load_data(duplicate)
    assert "duplicate mapping key" in str(excinfo.value)

    nfc = tmp_path / "nfc.yaml"
    nfc.write_text('a: &k "caf\\u00e9"\nm:\n  "cafe\\u0301": 1\n  *k : 2\n', encoding="utf-8")
    with pytest.raises(Exception) as excinfo:
        load_data(nfc)
    assert "duplicate mapping key" in str(excinfo.value)

    recursive = tmp_path / "cycle.yaml"
    recursive.write_text("a: &x\n  self: *x\n", encoding="utf-8")
    with pytest.raises(Exception):
        load_data(recursive)

    ok = tmp_path / "ok.yaml"
    ok.write_text("b: &s {p: 1}\nc: *s\nd: *s\n", encoding="utf-8")
    assert load_data(ok) == {"b": {"p": 1}, "c": {"p": 1}, "d": {"p": 1}}


# --- G-A: the closed subset has to stay closed ------------------------------

@pytest.mark.parametrize("text", [
    "1.e3",     # a YAML 1.2 core float, no digits after the point
    "1.E-3",
    "-2.e5",
    "017e3",    # a leading-zero number carrying an exponent
    "017.5",
])
def test_the_rejection_table_covers_the_exponent_variants(tmp_path, text):
    """Section 28.1. `1.` and `017` were rejected; `1.e3` and `017e3` were not.

    Both are YAML 1.2 core floats and neither is a JSON number, so falling
    through to the string rule made the same bytes mean 1000.0 to a YAML 1.2
    reader and "1.e3" here: the one defect this section exists to close.
    """
    path = tmp_path / "probe.yaml"
    path.write_text(f"a: {text}\n", encoding="utf-8")
    with pytest.raises(Exception) as excinfo:
        load_data(path)
    assert "ambiguous plain scalar" in str(excinfo.value)


@pytest.mark.parametrize("text,expected", [
    ("0", 0),
    ("0.5", 0.5),
    ("0e-3", 0.0),
    ("-0", 0),
    ("1.0", 1.0),
])
def test_the_exponent_variants_do_not_reject_ordinary_numbers(tmp_path, text, expected):
    """The widened patterns must not reach a leading zero that is just zero."""
    path = tmp_path / "probe.yaml"
    path.write_text(f"a: {text}\n", encoding="utf-8")
    assert load_data(path)["a"] == expected


def test_alias_expansion_is_bounded(tmp_path):
    """Section 28.1. A closed subset has to say where the expansion stops.

    Eight aliases per level over nine levels is 425 bytes of governed YAML and
    175,304,795 nodes expanded. Aliases stay permitted; the bound is on
    the size of what they expand to.
    """
    def nested(depth):
        lines = ["a0: &x0 [k, k, k, k, k, k, k, k]"]
        for level in range(1, depth):
            fan = ", ".join([f"*x{level - 1}"] * 8)
            lines.append(f"a{level}: &x{level} [{fan}]")
        return "\n".join(lines) + "\n"

    small = tmp_path / "small.yaml"
    small.write_text(nested(5), encoding="utf-8")
    assert load_data(small)["a4"][0][0][0][0][0] == "k"

    large = tmp_path / "large.yaml"
    large.write_text(nested(9), encoding="utf-8")
    with pytest.raises(ValidationFailure) as excinfo:
        load_data(large)
    assert "alias expansion exceeds" in str(excinfo.value)


@pytest.mark.parametrize("shape,text", [
    ("mapping", "a: &x\n  self: *x\n"),
    ("sequence", "a: &x\n  - *x\n"),
])
def test_a_recursive_alias_is_rejected_as_a_validation_failure(tmp_path, shape, text):
    """A recursive sequence alias used to escape as a bare RecursionError.

    Section 28.1 requires rejection. A crash rejects the document but not in a
    form a caller can report, and the two shapes have to behave the same way.
    """
    path = tmp_path / f"{shape}.yaml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValidationFailure) as excinfo:
        load_data(path)
    assert "recursive alias" in str(excinfo.value)


def test_every_yaml_block_in_the_specification_obeys_section_28_1():
    """Section 28.1 governs the document that defines it.

    The 2.0.0 candidate swept the examples for quoted timestamps and left 15
    blocks whose keys carry no value, which its own rejection table refuses.
    Section 28.1 now names that spelling as shape-sketch notation, so a block is
    conforming when it loads, or when the only thing stopping it is an empty
    plain scalar. Anything else is the specification contradicting itself.
    """
    spec = (PACKAGE_ROOT / f"OBDS-{RELEASE}.md").read_text(encoding="utf-8")
    blocks, current = [], None
    for number, line in enumerate(spec.split("\n"), 1):
        if current is None and line.strip().startswith("```yaml"):
            current = (number, [])
        elif current is not None and line.strip() == "```":
            blocks.append((current[0], "\n".join(current[1])))
            current = None
        elif current is not None:
            current[1].append(line)
    assert len(blocks) >= 30

    import re
    import tempfile

    def fill_sketch_placeholders(block):
        """Give every empty plain scalar a value, so nothing hides behind it.

        Refusing at the first empty scalar would let a real violation later in
        the same block go unseen. A key is a placeholder only when nothing is
        nested under it, which is what separates `reportRef:` from `curation:`.
        """
        lines = block.split("\n")
        for index, line in enumerate(lines):
            match = re.match(r"^(\s*(?:- )?[A-Za-z_][\w]*:)\s*(#.*)?$", line)
            if match is None:
                continue
            # For `- key:` the sibling keys sit at the key's column, not the
            # dash's, so nesting is measured from where the key starts.
            indent = len(match.group(1)) - len(match.group(1).lstrip("- "))
            nested = False
            for following in lines[index + 1:]:
                if not following.strip():
                    continue
                nested = len(following) - len(following.lstrip()) > indent
                break
            if not nested:
                lines[index] = f"{match.group(1)} null" + (
                    f"  {match.group(2)}" if match.group(2) else ""
                )
        return "\n".join(lines)

    offenders = []
    for number, block in blocks:
        path = Path(tempfile.mkdtemp()) / "block.yaml"
        path.write_text(fill_sketch_placeholders(block) + "\n", encoding="utf-8")
        try:
            load_data(path)
        except Exception as exc:                      # noqa: BLE001 - any refusal counts
            offenders.append((number, str(exc)[:160]))
    assert not offenders, f"spec YAML blocks refused by section 28.1: {offenders}"


def test_the_release_notes_state_the_release_kind_they_actually_are():
    """The published conformance artefact states the release kind it is.

    The generator hardcoded "maintenance release. No normative contract
    change", which is what 1.1.0 shipped by copying 1.0.4, and it survived into
    a MAJOR release that exists precisely because it breaks a contract.

    The expected word is read off the version here rather than pinned, because a
    pinned word is the same defect one file over: 3.0.1 is a PATCH and the pin
    still said MAJOR. Semantic Versioning decides which word it is, and the notes
    have to carry that one.
    """
    major, minor, patch = (int(part) for part in RELEASE.split("."))
    expected = "MAJOR" if (minor, patch) == (0, 0) else "MINOR" if patch == 0 else "PATCH"
    unexpected = {"MAJOR", "MINOR", "PATCH"} - {expected}

    result = json.loads(
        (PACKAGE_ROOT / f"OBDS-{RELEASE}-TEST-RESULT.json").read_text(encoding="utf-8")
    )
    notes = " ".join(result["notes"])
    assert f"{expected} release" in notes, notes
    for wrong in sorted(unexpected):
        assert f"{wrong} release" not in notes, notes
    assert "maintenance release" not in notes


@pytest.mark.parametrize("text", [
    "1_000.0",   # 1000.0 in YAML 1.1, a string here: a value that moved silently
    "1_0.5",
    ".5_0",
    "0.0_",
    "1_0:30",    # 630 in YAML 1.1
    "40_:3",
    "4_:1:2",
])
def test_yaml_11_numbers_the_rejection_rows_enumerated_one_spelling_at_a_time(tmp_path, text):
    """Section 28.1. The rows named `1_000` and `12:30`; the class is larger.

    A digit separator combined with a decimal point or a sexagesimal colon was a
    number to a YAML 1.1 reader and a string here, with nothing reported. That
    is the same defect as `1e3`, in the direction no validator can see, so the
    table now rejects on the class rather than on the spellings someone thought
    of.
    """
    path = tmp_path / "probe.yaml"
    path.write_text(f"a: {text}\n", encoding="utf-8")
    with pytest.raises(Exception) as excinfo:
        load_data(path)
    assert "ambiguous plain scalar" in str(excinfo.value)


@pytest.mark.parametrize("text", [
    "2026-09-01 00:00:00Z",
    "2026-09-01 00:00:00 Z",
    "2026-09-01 00:00:00 +02:00",
    "2026-09-01 00:00:00.5 +2",
    "2026-09-01T00:00:00Z",
    "2026-09-01",
])
def test_a_timestamp_with_a_space_before_its_zone_is_still_a_timestamp(tmp_path, text):
    """Section 28.1. The row's character class had no room for a space.

    YAML 1.1 separates the date, the time and the zone with spaces as readily as
    with `T`, so `2026-09-01 00:00:00 Z` is a datetime there and was a string
    here. 1.1.6 refused it outright as an unrepresentable value; accepting it as
    a string would have been a newly accepted form nothing documented.
    """
    path = tmp_path / "probe.yaml"
    path.write_text(f"a: {text}\n", encoding="utf-8")
    with pytest.raises(Exception) as excinfo:
        load_data(path)
    assert "ambiguous plain scalar" in str(excinfo.value)


@pytest.mark.parametrize("text,expected", [
    ("1.0", 1.0),
    ("0.5", 0.5),
    ("1000.0", 1000.0),
    ("10.5", 10.5),
    ("0.0", 0.0),
    ("2403", 2403),
    ("42", 42),
    ("-0", 0),
    ("0e-3", 0.0),
])
def test_the_class_rejection_leaves_ordinary_numbers_alone(tmp_path, text, expected):
    """The rewrite the migration table asks for must itself be accepted."""
    path = tmp_path / "probe.yaml"
    path.write_text(f"a: {text}\n", encoding="utf-8")
    assert load_data(path)["a"] == expected


def test_an_alias_refusal_names_the_file_like_every_other_refusal(tmp_path):
    """A ValidationFailure raised inside the reader lost the path prefix."""
    path = tmp_path / "cycle.yaml"
    path.write_text("a: &x\n  self: *x\n", encoding="utf-8")
    with pytest.raises(ValidationFailure) as excinfo:
        load_data(path)
    assert "cycle.yaml: parse error:" in excinfo.value.errors[0]


@pytest.mark.parametrize("text", [
    "._5",                    # `\.[0-9][0-9_]*` in YAML 1.1: `._5` is not a float
    "._",
    "2026-9-1",               # the date-only YAML 1.1 timestamp needs two-digit fields
    "2026-09-01T00:00:00z",   # the YAML 1.1 zone is `Z`, not `z`
    "0__8",                   # neither a YAML 1.1 int nor an octal
    "0:07",                   # YAML 1.1 sexagesimal starts at 1-9
    "-0:2",
    "+0o7",                   # the YAML 1.2 octal takes no sign
    "0O7",
    "0X1f",
    "0B1010",
    "-.nan",                  # only `inf` takes a sign in either YAML version
    "+.nan",
    "-.NaN",
    "+.NAN",
    "-.NAN",
    "+.NaN",
])
def test_the_rejection_table_refuses_nothing_every_yaml_version_calls_a_string(tmp_path, text):
    """Section 28.1: "a form not listed and not matching the resolution table is a string".

    Closing the table on a hand-written grammar made it over-reach: these are
    strings under YAML 1.1 and under YAML 1.2, and rejecting them would make the
    reference implementation, which is the section 26.2 oracle, disagree with
    any implementation that read the closed table literally.
    """
    path = tmp_path / "probe.yaml"
    path.write_text(f"a: {text}\n", encoding="utf-8")
    assert load_data(path)["a"] == text


@pytest.mark.parametrize("suffix,template", [
    (".yaml", "a: {open}1{close}\n"),
    (".json", '{{"a": {open}1{close}}}'),
])
@pytest.mark.parametrize("depth,accepted", [(1, True), (50, True), (99, True), (100, False), (400, False)])
def test_nesting_is_bounded_and_the_two_formats_agree(tmp_path, suffix, template, depth, accepted):
    """Section 28.1. Unstated, the nesting limit is the reader's call stack.

    1.1.6 read 491 levels, the 2.0.0 candidate read 327, and past that both
    crashed with a RecursionError rather than refusing. A bound two
    implementations can agree on has to be a number in the specification, and it
    has to be over the data model, or JSON and YAML disagree about which
    documents are governable.
    """
    path = tmp_path / f"deep{suffix}"
    path.write_text(template.format(open="[" * depth, close="]" * depth), encoding="utf-8")
    if accepted:
        assert load_data(path) is not None
    else:
        with pytest.raises(ValidationFailure) as excinfo:
            load_data(path)
        assert "nesting exceeds 100 levels" in excinfo.value.errors[0]
        assert str(path) in excinfo.value.errors[0]


def test_the_rejection_table_is_closed_against_the_real_yaml_resolvers():
    """Section 28.1: "The table is closed".

    Three reviews found the table over-reaching on hand-written grammar —
    `._5`, `0__8`, `0:07`, `+0o7`, `-.nan` are strings to every YAML reader and
    were being refused — and the reference implementation is the section 26.2
    oracle, so an implementation reading the table literally would disagree with
    it. This holds the claim rather than restating it: over every short string
    on a numeric alphabet, a form is rejected exactly when some YAML version
    reads it as a value the JSON grammar does not produce.
    """
    import itertools
    import re as _re

    import yaml as _yaml

    resolver = _yaml.resolver.Resolver()
    json_number = _re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?$")
    json_literal = _re.compile(r"^(?:null|Null|NULL|true|True|TRUE|false|False|FALSE)$")
    # The YAML 1.2 core schema, written out rather than imported.
    core = [
        _re.compile(r"^(?:null|Null|NULL|~|)$"),
        _re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
        _re.compile(r"^(?:[-+]?[0-9]+|0o[0-7]+|0x[0-9a-fA-F]+)$"),
        _re.compile(
            r"^(?:[-+]?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?)(?:[eE][-+]?[0-9]+)?"
            r"|[-+]?\.(?:inf|Inf|INF)|\.(?:nan|NaN|NAN))$"
        ),
    ]
    # Section 28.1 keeps these strings, as OBDS 1.0 already required, and says so.
    carve_out = {"yes", "Yes", "YES", "no", "No", "NO", "on", "On", "ON",
                 "off", "Off", "OFF", "y", "Y", "n", "N"}

    def some_yaml_version_reads_a_value(text):
        if resolver.resolve(_yaml.ScalarNode, text, (True, False)) != "tag:yaml.org,2002:str":
            return True
        return any(pattern.match(text) for pattern in core)

    alphabet = "019._-+:eExXoObBZTtiInNfFaA~"
    candidates = set()
    for length in (1, 2, 3):
        candidates.update("".join(c) for c in itertools.product(alphabet, repeat=length))
    for head in ("2026-09-01", "2026-9-1", "017", "1_0", ".5", "1.", "0x1f", "0o17", "0b1", "0"):
        for tail in ("", "T00:00:00Z", "t00:00:00z", " 00:00:00 Z", "e3", "e+3",
                     "_5", ":30", ".0", "Z", "__8", ":07"):
            candidates.add(head + tail)
    for sign in ("", "-", "+"):
        for word in ("inf", "Inf", "INF", "nan", "NaN", "NAN"):
            candidates.add(sign + "." + word)
        # The alternative bases and the exponent forms are four characters at
        # their shortest, so the length sweep above never reaches them and a
        # row that over-reached on a sign went unnoticed.
        for base in ("0o7", "0O7", "0b1", "0B1", "0x1f", "0X1f", "0o1_7", "0b1_0"):
            candidates.add(sign + base)
        for number in ("1e3", "1E3", "1.e3", ".5e3", "017e3", "1_000.0", "1_0:30", "0.0_", "._5"):
            candidates.add(sign + number)

    over_reach, under_reach, disagreeing_value = [], [], []
    for text in candidates:
        if text in carve_out:
            continue
        try:
            value = _resolve_plain_scalar(text)
            rejected = False
        except Exception:                                # noqa: BLE001 - any refusal counts
            rejected = True
        reader_dependent = some_yaml_version_reads_a_value(text) and not (
            json_number.match(text) or json_literal.match(text)
        )
        if rejected and not reader_dependent:
            over_reach.append(text)
        if not rejected and reader_dependent:
            under_reach.append(text)
        if not rejected and json_number.match(text) and not isinstance(value, (int, float)):
            disagreeing_value.append(text)

    assert len(candidates) > 20000
    assert not over_reach, f"rejected though every YAML version reads a string: {sorted(over_reach)[:20]}"
    assert not under_reach, f"accepted though a YAML version reads a value: {sorted(under_reach)[:20]}"
    assert not disagreeing_value, f"JSON number not read as a number: {disagreeing_value[:20]}"
