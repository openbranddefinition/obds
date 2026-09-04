"""OBDS 3.0.0 Classes E and D, and the six cross-class seams.

Class E — conflict relevance. One normative rule, used by the compiler, the
projections and the runtime, so all three reach the same governed decision.

Class D — build configuration defaults. Implemented after E, because E removes
both projection policies from the relevance predicate and thereby turns D's
`styleTexture` default from a governance decision into a rendering choice. The
other order would have entrenched a default in a predicate E deletes.

The seam tests exist because a class is not closed if its seam behaviour is
still inconsistent. Each names the two classes it joins.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from obds_ref.canonical import artefact_hash, manifest_content_hash, sha256_id
from obds_ref.runtime import run_with_model
from obds_ref.compiler import (
    CHECK_PARAM_DEFAULTS,
    build_target,
    load_data,
    validate_plan,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
REFERENCE = PACKAGE_ROOT / "reference"
CA_ROOT = REFERENCE / "context-assembly"


def example(name):
    base = PACKAGE_ROOT / "examples" / name
    return load_data(base / "manifest.yaml"), load_data(base / "build-plan.yaml")


def reseal(manifest):
    manifest["approval"].pop("contentHash", None)
    manifest["approval"]["contentHash"] = manifest_content_hash(manifest)
    return manifest


def build(manifest, plan, **target_overrides):
    plan = copy.deepcopy(plan)
    plan["manifestRef"]["contentHash"] = manifest["approval"]["contentHash"]
    target = plan["targets"][0]
    target.update(copy.deepcopy(target_overrides))
    return build_target(manifest, plan, target)


def _flat_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if str(path.parent) not in sys.path:
        sys.path.insert(0, str(path.parent))
    spec.loader.exec_module(module)
    return module


ALL_PROJECTIONS = [
    {"styleTexture": {"mode": "none", "elementIds": []}, "stateMap": {"mode": "none", "kinds": []}},
    {"styleTexture": {"mode": "all", "elementIds": []}, "stateMap": {"mode": "none", "kinds": []}},
    {"styleTexture": {"mode": "none", "elementIds": []}, "stateMap": {"mode": "all_applicable", "kinds": []}},
    {"styleTexture": {"mode": "none", "elementIds": []}, "stateMap": {"mode": "kinds", "kinds": ["guidance"]}},
]


def _conflicted(*, family="context", nature="knowledge", state="defined",
                second_scope=None, second_validity=None, value=None):
    """Two incomparable maximal elements on one semantic subject.

    CONTEXT rather than RULES by default: a defined RULES element must carry a
    `valueContractRef`, so a rules-based fixture would be a manifest no
    conforming implementation may accept, and a governed behaviour asserted on
    an invalid document proves nothing.
    """
    manifest, plan = example("foundation-minimal")
    manifest = copy.deepcopy(manifest)
    template = copy.deepcopy(manifest["elements"][0])
    elements = [manifest["elements"][0]]
    for index in range(2):
        element = copy.deepcopy(template)
        element.pop("valueContractRef", None)
        element.update(
            {
                "id": f"context.tone.{index}",
                "subject": "subject:tone",
                "family": family,
                "kind": "guidance",
                "nature": nature,
                "state": state,
                "scope": {"locales": ["en"]} if index == 0 else (second_scope or {"outputTypes": ["brand-query"]}),
                "validity": second_validity if (index == 1 and second_validity) else {"from": None, "to": None},
                "value": value or {"text": f"tone {index}"},
            }
        )
        elements.append(element)
    manifest["elements"] = elements
    reseal(manifest)
    return manifest, plan


# --------------------------------------------------------------------------
# Class E — one relevance rule
# --------------------------------------------------------------------------

@pytest.mark.parametrize("projection", ALL_PROJECTIONS, ids=["none-none", "style-all", "state-all", "state-kinds"])
def test_e_an_unconditionally_read_conflict_fails_under_every_projection(projection):
    """§10.2a criteria 1–3 are unconditional: no projection can opt out of them.

    A `defined` non-rules FACT belongs in FACT_GROUNDING, and a target cannot
    declare itself out of its own fact grounding. So this conflict fails under
    every projection policy, which is the half of the boundary a target does not
    control. Criteria 4 and 5 are the half it does — see the matrix below.
    """
    manifest, plan = _conflicted(family="context", nature="fact")
    result = build(manifest, plan, **projection)
    assert result.status == "failed", projection
    assert "OBDS-BUILD-SUBJECT-CONFLICT" in [error.code for error in result.errors]
    assert [conflict["decisionRelevant"] for conflict in result.conflicts] == [True]


def test_e_a_projection_policy_decides_only_what_it_declares_it_reads():
    """§10.2a: a target that selects narrowly is not failed by what it never reads.

    3.0.0 asserted the opposite here — that all four projections must agree —
    and derived it from §14.3a's prohibition on a projection changing
    `selection`. A conflicted subject changes `selection` under no projection at
    all: it contributes no winner, so it is absent from every one of the four.
    What the projection changes is whether this target *reads* the subject, and
    §10.2a makes that, and only that, the relevance question.

    So `defined` KNOWLEDGE fails under `styleTexture: all` and builds under
    `styleTexture: none`, and both are the same rule applied to two different
    declared requests.
    """
    manifest, plan = _conflicted(family="context", nature="knowledge", state="defined")
    outcomes = {
        json.dumps(projection, sort_keys=True): build(manifest, plan, **projection).status
        for projection in ALL_PROJECTIONS
    }
    assert set(outcomes.values()) == {"ready", "failed"}, outcomes
    style_all = json.dumps(ALL_PROJECTIONS[1], sort_keys=True)
    assert outcomes[style_all] == "failed", "styleTexture all reads every defined knowledge element"
    assert outcomes[json.dumps(ALL_PROJECTIONS[0], sort_keys=True)] == "ready"


def test_e_a_clean_manifest_agrees_across_projections_too():
    """The rule must not merely fail everything; it must decide identically.

    §14.3a's MUST is that a projection policy does not change `selection`. It
    does change `governedResultHash`, because §14.3a hashes the target verbatim
    and the projection is part of the target: the hash identifies the governed
    request *as spelled*. That is stated, not an accident, and it is why Class D
    requires presence rather than stating a default — a stated default would
    leave two spellings of one governed request hashing differently.
    """
    manifest, plan = example("foundation-minimal")
    selections = set()
    for projection in ALL_PROJECTIONS:
        result = build(manifest, plan, **projection)
        assert result.status == "ready", [error.code for error in result.errors]
        selections.add(
            json.dumps(
                {
                    "available": result.artefact["availableElementIds"],
                    "conflicts": result.conflicts,
                },
                sort_keys=True,
            )
        )
    assert len(selections) == 1, "a projection policy changed the governed selection"


def test_e_an_out_of_scope_conflict_is_preserved_and_reported():
    """§10.2a: an irrelevant conflict MUST NOT be silently discarded.

    The 2.0.0 reference reported only conflicts that *were* target-applicable
    and discarded exactly the class the paragraph exists for: an out-of-scope
    conflict produced `ready` with `conflicts[]` empty.
    """
    manifest, plan = _conflicted(second_scope={"locales": ["de"]})
    result = build(manifest, plan, **ALL_PROJECTIONS[0])
    assert result.status == "ready", [error.code for error in result.errors]
    assert result.conflicts, "the out-of-scope conflict was silently discarded"
    assert [conflict["decisionRelevant"] for conflict in result.conflicts] == [False]
    assert result.conflicts[0]["subject"] == "subject:tone"


def test_e_an_expired_conflict_is_preserved_and_reported():
    """The other half of the preserved-irrelevance pair."""
    manifest, plan = _conflicted(
        second_validity={"from": "2020-01-01T00:00:00Z", "to": "2020-02-01T00:00:00Z"}
    )
    result = build(manifest, plan, **ALL_PROJECTIONS[0])
    assert result.status == "ready", [error.code for error in result.errors]
    assert result.conflicts, "the expired conflict was silently discarded"
    assert [conflict["decisionRelevant"] for conflict in result.conflicts] == [False]


def test_e_the_irrelevance_class_is_non_empty_and_principled():
    """It collapses to neither "all fail" nor "all build"; both members exist.

    Two ways to be irrelevant, and one way to be relevant, measured side by
    side. Out-of-scope: at most one candidate is in `applicable(T)`. Never read:
    both are, and this target's declared projections reach neither. Read: the
    target declared `styleTexture: all`, so it reads them and must fail.
    """
    out_of_scope = _conflicted(second_scope={"locales": ["de"]})
    never_read = _conflicted(family="context", nature="knowledge", state="defined")
    read = _conflicted(family="context", nature="knowledge", state="defined")

    assert build(*out_of_scope, **ALL_PROJECTIONS[0]).status == "ready"
    assert build(*never_read, **ALL_PROJECTIONS[0]).status == "ready"
    assert build(*read, **ALL_PROJECTIONS[1]).status == "failed"

    for manifest, plan in (out_of_scope, never_read):
        result = build(manifest, plan, **ALL_PROJECTIONS[0])
        assert result.conflicts, "an irrelevant conflict must still be reported"
        assert [c["decisionRelevant"] for c in result.conflicts] == [False]


def test_e_an_irrelevant_conflict_puts_neither_candidate_in_the_artefact():
    """The measurement that retires the 3.0.0 first argument.

    3.0.0 widened relevance because a full-mode assembler was said to rebuild
    FACT_GROUNDING and STATE_MAP from the whole element universe, so a narrow
    projection would not actually keep a losing candidate from the model. It
    cannot: neither candidate is in the artefact to be rebuilt from. A
    conflicted subject contributes no winner to `applicable`, so it appears in
    neither `availableElementIds` nor `elementRecords`, and `assemble` reads
    only those two and refuses manifest access outside `manifest_checked`.
    """
    manifest, plan = _conflicted(family="context", nature="knowledge", state="defined")
    result = build(manifest, plan, **ALL_PROJECTIONS[0])

    assert result.status == "ready", [error.code for error in result.errors]
    conflicted_ids = set(result.conflicts[0]["elementIds"])
    assert conflicted_ids, "the fixture no longer produces a conflict"
    assert conflicted_ids.isdisjoint(result.artefact["availableElementIds"])
    assert conflicted_ids.isdisjoint(result.artefact["includedElementIds"])
    assert conflicted_ids.isdisjoint(
        {record["id"] for record in result.artefact["elementRecords"]}
    )
    for slot in result.artefact["slots"].values():
        for element_id in conflicted_ids:
            assert element_id not in slot, f"{element_id} reached a rendered slot"


E_CHANNELS = [
    pytest.param({"family": "context", "nature": "fact"}, id="defined-fact"),
    pytest.param({"family": "context", "nature": "knowledge"}, id="defined-knowledge"),
    pytest.param({"family": "stance", "nature": "knowledge"}, id="stance"),
    pytest.param({"family": "context", "nature": "knowledge", "state": "unknown"}, id="unknown"),
    pytest.param({"family": "context", "nature": "knowledge", "state": "not_defined"}, id="not-defined"),
    pytest.param({"family": "context", "nature": "knowledge", "state": "not_applicable"}, id="not-applicable"),
    pytest.param({"family": "identity", "nature": "knowledge"}, id="identity-knowledge"),
    pytest.param({"family": "design", "nature": "knowledge"}, id="design-knowledge"),
]


def _expected_relevance(shape, projection):
    """Section 10.2a, read straight from the specification, not from the code.

    Written independently of `_conflict_is_decision_relevant` so the matrix
    below is an oracle rather than a restatement. The fixture never names an
    element in `requiresDefined`, in `eligibleGuidanceIds` or in a RULE
    dependency, and it never builds a RULES element, so criteria 1 and 2 cannot
    fire here and criteria 3, 4 and 5 decide.
    """
    state = shape.get("state", "defined")
    family = shape.get("family", "context")
    nature = shape.get("nature", "knowledge")
    style = projection["styleTexture"]
    state_map = projection["stateMap"]

    # 3. a defined non-rules fact belongs in FACT_GROUNDING, unconditionally.
    if state == "defined" and nature == "fact" and family != "rules":
        return True
    # 4. carried into STATE_MAP by the target's declared policy. Every fixture
    #    element carries `kind: guidance`.
    if state in {"unknown", "not_defined", "not_applicable"}:
        if state_map["mode"] == "all_applicable":
            return True
        if state_map["mode"] == "kinds" and "guidance" in state_map["kinds"]:
            return True
    # 5. carried into STYLE_TEXTURE by the target's declared policy.
    if state == "defined" and (nature == "knowledge" or family == "stance"):
        if style["mode"] == "all":
            return True
        if style["mode"] == "selected" and style["elementIds"]:
            return True
    return False


@pytest.mark.parametrize("shape", E_CHANNELS)
@pytest.mark.parametrize("projection", ALL_PROJECTIONS, ids=["none-none", "style-all", "state-all", "state-kinds"])
def test_e_every_channel_decides_by_the_section_10_2a_rule(shape, projection):
    """One rule, every channel, both answers. 32 combinations, each pinned.

    3.0.0 asserted `failed` for all 32 and thereby tested one branch of the
    predicate. This asserts the section 10.2a outcome for each, against an
    oracle written from the specification text, so a change that widens
    relevance and a change that narrows it both fail here. 5 of the 10
    `return True` branches in the 2.0.0 predicate were never exercised — a
    mutation that disabled them left the suite green. Every branch is reachable
    from this matrix, and so is every `return False`.
    """
    manifest, plan = _conflicted(**shape)
    result = build(manifest, plan, **projection)
    expected = _expected_relevance(shape, projection)

    assert [conflict["decisionRelevant"] for conflict in result.conflicts] == [expected], (
        shape, projection
    )
    assert result.status == ("failed" if expected else "ready"), (shape, projection)
    if expected:
        assert "OBDS-BUILD-SUBJECT-CONFLICT" in [error.code for error in result.errors]
    else:
        assert "OBDS-BUILD-SUBJECT-CONFLICT" not in [error.code for error in result.errors]
    assert result.conflicts, "the conflict must be reported whatever the outcome"


def test_e_the_channel_matrix_exercises_both_answers():
    """A matrix that only ever expects one answer proves one branch.

    3.0.0's version expected `failed` 32 times out of 32. This guards the guard.
    """
    outcomes = [
        _expected_relevance(shape.values[0], projection)
        for shape in E_CHANNELS
        for projection in ALL_PROJECTIONS
    ]
    assert outcomes.count(True) >= 8, outcomes
    assert outcomes.count(False) >= 8, outcomes


def test_e_no_losing_candidate_reaches_the_model():
    """S6, end to end: a conflicted subject produces no artefact to assemble.

    In 2.0.0 the compiler could declare such a build clean while the assembler,
    rebuilding from the whole element universe under `deliveryMode: full`, sent
    the model both losing candidates as active contradictory guidance.
    """
    manifest, plan = _conflicted()
    result = build(manifest, plan, **ALL_PROJECTIONS[1])
    assert result.artefact is None, "a conflicted subject produced an assemblable artefact"


# --------------------------------------------------------------------------
# Class D — build configuration defaults
# --------------------------------------------------------------------------

D1_SPELLINGS = [
    pytest.param("absent", id="key-absent"),
    pytest.param("empty", id="empty-object"),
    pytest.param("list-only", id="list-only"),
]


@pytest.mark.parametrize("spelling", D1_SPELLINGS)
@pytest.mark.parametrize("field", ["styleTexture", "stateMap"])
def test_d1_an_omitted_or_modeless_projection_is_refused(spelling, field):
    """D1, closed by removing the question rather than answering it.

    Four spellings had to agree on status, error codes, `decisionRelevant`,
    `includedElementIds`, `availableElementIds` and `selection`. Three of them
    are now unrepresentable, so there is exactly one spelling per governed
    request and the agreement is structural rather than asserted.
    """
    _, plan = example("foundation-minimal")
    plan = copy.deepcopy(plan)
    target = plan["targets"][0]
    if spelling == "absent":
        target.pop(field)
    elif spelling == "empty":
        target[field] = {}
    else:
        target[field] = {"elementIds": []} if field == "styleTexture" else {"kinds": []}
    errors = validate_plan(plan)
    assert any(f"{field} is required and must declare mode" in error for error in errors), errors


def test_d1_the_explicit_spelling_is_accepted_and_the_corpus_already_uses_it():
    """Measured migration cost of requiring presence: zero."""
    for name in ("foundation-minimal", "fail-closed"):
        _, plan = example(name)
        assert validate_plan(plan) == []
        for target in plan["targets"]:
            assert "mode" in target["styleTexture"]
            assert "mode" in target["stateMap"]


def test_d1_the_shipped_build_plan_contract_is_executed():
    """A published contract that no code executes is a claim, not a check.

    Nothing in 2.0.0 ever ran `build-plan.schema.json`, which is how a missing
    `default` survived a release gate.
    """
    _, plan = example("foundation-minimal")
    plan = copy.deepcopy(plan)
    plan["targets"][0]["maxTokens"] = "not a number"
    errors = validate_plan(plan)
    assert any(error.startswith("build plan schema:") for error in errors), errors


def test_d2_check_parameters_are_materialised_into_the_artefact():
    """D2 / S4. One artefact, one hash, one governed decision.

    `compiler.py` materialised `phase` and copied `params` verbatim, so `match`,
    `appliesTo`, `mode` and `unit` were defaulted at execution time by whichever
    runtime loaded the artefact. On a byte-identical artefact, a runtime
    defaulting `match=case_insensitive` blocked the output and one defaulting
    `match=exact` released it.
    """
    from test_obds_300_class_c import _artefact_with_a_compiled_check

    artefact = _artefact_with_a_compiled_check()
    for entry in artefact["compiledChecks"]:
        expected = CHECK_PARAM_DEFAULTS[entry["primitive"]]
        for name in expected:
            assert name in entry["params"], (
                f"{entry['primitive']}.{name} is left for the runtime to default"
            )


def test_d2_the_runtime_refuses_an_artefact_that_leaves_a_parameter_open():
    """The other half of D2, and the half a compiler test cannot reach.

    The reference compiler always materialises, so no build produces an
    unmaterialised compiled check and no build-driven test exercises the runtime
    side. A conforming *third-party* artefact is exactly what the contract has
    to survive, so this hands the runtime one directly.
    """
    from obds_ref.canonical import artefact_hash as _hash
    from test_obds_300_class_c import _artefact_with_a_compiled_check

    artefact = copy.deepcopy(_artefact_with_a_compiled_check())
    entry = artefact["compiledChecks"][0]
    assert entry["params"].pop("match", None) is not None
    artefact["artifactHash"] = _hash(artefact)

    calls = []
    record = run_with_model(
        artefact,
        task_input="A clean request.",
        model=lambda prompt: calls.append(prompt) or "We are The Best.",
        target_id=artefact["targetId"],
    )
    assert record["decision"] == "no_valid_artifact", record["decision"]
    assert record["modelCall"]["called"] is False
    assert calls == []
    assert any(
        item["primitive"] == "compiled_check_contract" for item in record["checkResults"]
    ), record["checkResults"]


def test_d2_the_published_contract_refuses_it_too():
    """Schema and runtime give one answer, which is the point of publishing it."""
    import jsonschema

    from obds_ref.governed_io import load_data as _load
    from test_obds_300_class_c import _artefact_with_a_compiled_check

    schema = _load(PACKAGE_ROOT / "schemas" / "3.0.0" / "compiled-context.schema.json")
    artefact = copy.deepcopy(_artefact_with_a_compiled_check())
    jsonschema.validate(artefact, schema)
    artefact["compiledChecks"][0]["params"].pop("match")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(artefact, schema)


@pytest.mark.parametrize("enforcement", ["block", "require_approval", "warn", "inform"])
def test_d2_the_enforcement_vocabulary_is_the_same_in_both_contracts(enforcement):
    """The compiler copies the rule's enforcement, so the contracts must share it.

    The published compiled-context contract listed `advise`, which is not an OBDS
    enforcement value, and omitted `warn` and `inform`, which are. An independent
    review reproduced the consequence: a manifest declaring `enforcement: warn`
    validated, built `ready`, produced an artefact the published contract rejects,
    and the runtime executed it anyway. Three surfaces, two answers.
    """
    import jsonschema

    from obds_ref.canonical import manifest_content_hash as _content_hash
    from obds_ref.canonical import value_shape_hash
    from obds_ref.governed_io import load_data as _load

    manifest = copy.deepcopy(load_data(REFERENCE / "foundation" / "examples" / "simple" / "manifest.yaml"))
    plan = copy.deepcopy(load_data(REFERENCE / "foundation" / "examples" / "simple" / "build-plan.yaml"))
    rule = next(
        item for item in manifest["elements"]
        if item.get("family") == "rules" and item.get("state") == "defined"
    )
    rule["value"]["enforcement"] = enforcement
    for contract in manifest["valueContracts"]:
        if contract["id"] == rule.get("valueContractRef"):
            contract["shapeHash"] = value_shape_hash(rule["value"])
    manifest["approval"]["contentHash"] = _content_hash(manifest)
    plan["manifestRef"]["contentHash"] = manifest["approval"]["contentHash"]

    from obds_ref.compiler import validate_manifest

    assert validate_manifest(manifest) == []
    result = build_target(manifest, plan, plan["targets"][0])
    assert result.status == "ready", [error.message for error in result.errors]
    assert any(entry["enforcement"] == enforcement for entry in result.artefact["compiledChecks"])

    schema = _load(PACKAGE_ROOT / "schemas" / "3.0.0" / "compiled-context.schema.json")
    jsonschema.validate(result.artefact, schema)


def test_d2_the_runtime_refuses_an_artefact_that_omits_enforcement():
    """`enforcement` decides whether a failed check withholds the output.

    So it is as decision-bearing as `match`. The compiler materialises it and the
    published contract requires it; the runtime defaulted it to `block`, which
    means an artefact the contract rejects still reached a governed decision.
    """
    from obds_ref.canonical import artefact_hash as _hash
    from test_obds_300_class_c import _artefact_with_a_compiled_check

    artefact = copy.deepcopy(_artefact_with_a_compiled_check())
    assert artefact["compiledChecks"][0].pop("enforcement", None) is not None
    artefact["artifactHash"] = _hash(artefact)

    calls = []
    record = run_with_model(
        artefact,
        task_input="A clean request.",
        model=lambda prompt: calls.append(prompt) or "We are The Best.",
        target_id=artefact["targetId"],
    )
    assert record["decision"] == "no_valid_artifact"
    assert record["modelCall"]["called"] is False
    assert calls == []


def test_d2_an_invented_enforcement_value_is_refused_by_both():
    import jsonschema

    from obds_ref.governed_io import load_data as _load
    from test_obds_300_class_c import _artefact_with_a_compiled_check

    artefact = copy.deepcopy(_artefact_with_a_compiled_check())
    artefact["compiledChecks"][0]["enforcement"] = "advise"
    schema = _load(PACKAGE_ROOT / "schemas" / "3.0.0" / "compiled-context.schema.json")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(artefact, schema)


def test_d2_every_registry_primitive_declares_its_materialised_parameters():
    from obds_ref.checks import SUPPORTED_PRIMITIVES

    assert set(CHECK_PARAM_DEFAULTS) == SUPPORTED_PRIMITIVES
    for primitive, defaults in CHECK_PARAM_DEFAULTS.items():
        assert "appliesTo" in defaults, primitive


def test_d2_the_postflight_finding_matches_the_materialised_parameter():
    """The artefact decides; the runtime does not get a second opinion."""
    from obds_ref.checks import execute_checks
    from test_obds_300_class_c import _artefact_with_a_compiled_check

    artefact = _artefact_with_a_compiled_check()
    findings = execute_checks(artefact["compiledChecks"], phase="postflight", text="We are The Best.")
    assert findings and not findings[0].passed, (
        "the materialised match mode did not decide the finding"
    )


# --------------------------------------------------------------------------
# Cross-class seams
# --------------------------------------------------------------------------

def test_s1_class_a_derivation_does_not_corrupt_class_b_measurement():
    """S1: the process-global PyYAML mutation changed what Class B measured.

    Covered in full by A4; asserted here from the Class B side, because the
    Class B auditor hit this blind and a repair aimed at the resolver list
    rather than the derivation would leave it open.
    """
    import yaml

    from obds_ref.compiler import save_yaml

    before = repr(yaml.safe_load("a: true"))
    for package in ("context-assembly", "context-delivery"):
        path = REFERENCE / package / "build_views.py"
        spec = importlib.util.spec_from_file_location(f"seam_{package.replace('-', '_')}", path)
        module = importlib.util.module_from_spec(spec)
        if str(path.parent) not in sys.path:
            sys.path.insert(0, str(path.parent))
        spec.loader.exec_module(module)
    assert repr(yaml.safe_load("a: true")) == before


def test_s2_class_a_and_class_b_share_one_canonical_module():
    """S2: the pin reader is a governed JSON reader *and* Class B's root table."""
    digests = {
        sha256_id({"text": path.read_text(encoding="utf-8")})
        for path in [
            REFERENCE / "foundation" / "src" / "obds_ref" / "canonical.py",
            REFERENCE / "context-assembly" / "canonical.py",
            REFERENCE / "context-delivery" / "canonical.py",
            REFERENCE / "design-space" / "canonical.py",
        ]
    }
    assert len(digests) == 1, "canonical.py has diverged across packages"
    governed = {
        sha256_id({"text": path.read_text(encoding="utf-8")})
        for path in [
            REFERENCE / "foundation" / "src" / "obds_ref" / "governed_io.py",
            REFERENCE / "context-assembly" / "governed_io.py",
            REFERENCE / "context-delivery" / "governed_io.py",
            REFERENCE / "design-space" / "governed_io.py",
        ]
    }
    assert len(governed) == 1, "governed_io.py has diverged across packages"


def test_s3_one_admissibility_rule_at_both_layers():
    """S3: Class B admits governed strings; C5 admits runtime check input.

    Both are "state which code points may enter, then reject before
    normalising". Doing one and not the other leaves the asymmetry Class C
    documents, where the term is gated and the output is not.
    """
    from obds_ref.canonical import assert_pinned_code_points
    from obds_ref.checks import assert_check_input_admissible

    probe = "aࢗb"
    with pytest.raises(ValueError):
        assert_pinned_code_points(probe)
    with pytest.raises(ValueError):
        assert_check_input_admissible(probe, where="seam")


def test_s4_the_new_mode_is_materialised_like_every_other_parameter():
    """S4: a folding mode that is still runtime-defaultable closes nothing.

    Driven through a real build rather than through the defaults table: the
    author states only the mode, and the artefact must carry the parameters the
    author left implicit. Asserting the table instead would pass with
    materialisation switched off.
    """
    from test_obds_300_class_c import _deterministic_rule, _plan_for, _rule_manifest

    manifest = _rule_manifest(
        _deterministic_rule(
            checks=[
                {
                    "primitive": "term_prohibited",
                    "phase": "postflight",
                    "params": {"terms": ["the best"], "match": "normalized_whitespace_ci"},
                }
            ]
        )
    )
    plan = _plan_for(manifest)
    result = build_target(manifest, plan, plan["targets"][0])
    assert result.status == "ready", [error.message for error in result.errors]
    entry = next(item for item in result.artefact["compiledChecks"] if item["primitive"] == "term_prohibited")
    assert entry["params"]["match"] == "normalized_whitespace_ci"
    assert entry["params"]["appliesTo"] == "output", (
        "the artefact left `appliesTo` for a runtime to invent"
    )


def test_s5_class_e_answers_class_d_s_governance_question():
    """S5: `styleTexture` is a governance input, which is why D1 requires it.

    Section 10.2a criterion 5 makes the projection policy part of the relevance
    decision, so an *omitted* policy would be a governance decision nobody
    stated. D1 answers that by refusing the omission rather than defaulting it:
    there is exactly one spelling of a governed request, and it is explicit.
    3.0.0 answered it by deleting the policy from the predicate instead, which
    contradicted section 10.2a; 3.0.2 restores the predicate and keeps D1, which
    is the answer that needs no default.

    A clean manifest still resolves identically under every projection —
    §14.3a's actual MUST, that a projection does not change `selection`.
    """
    clean_manifest, plan = example("foundation-minimal")

    clean = [build(clean_manifest, plan, **projection) for projection in ALL_PROJECTIONS]
    assert {result.status for result in clean} == {"ready"}
    assert len({tuple(result.artefact["availableElementIds"]) for result in clean}) == 1

    # And the conflicted manifest resolves identically too: the conflicted
    # subject is in no selection under any projection. Only whether this target
    # reads it differs, which is the whole of section 10.2a.
    conflicted_manifest, conflicted_plan = _conflicted(nature="knowledge", state="defined")
    conflicted = [
        build(conflicted_manifest, conflicted_plan, **projection)
        for projection in ALL_PROJECTIONS
    ]
    assert {result.status for result in conflicted} == {"ready", "failed"}
    available = {
        tuple(result.artefact["availableElementIds"])
        for result in conflicted
        if result.artefact is not None
    }
    assert len(available) == 1, "a projection policy changed the governed selection"


def test_s6_the_assembly_boundary_re_checks_the_artefact_s_declarations():
    """S6: the compiled artefact's declarations, re-checked where they are used.

    E found that full-mode assembly ignored the projection policies; C found
    that the assembled runtime checked a string nobody verified against the
    package. Both are the same structural gap.

    Driven by an actual assembly of an element outside the declared universe,
    not by grepping the source for a message: a source-text assertion passes
    with the rejection removed.
    """
    spec = importlib.util.spec_from_file_location("seam_assembler", CA_ROOT / "assemble_context.py")
    module = importlib.util.module_from_spec(spec)
    if str(CA_ROOT) not in sys.path:
        sys.path.insert(0, str(CA_ROOT))
    spec.loader.exec_module(module)

    compiled = load_data(CA_ROOT / "examples" / "compiled-social-copy-global-en.json")
    index = load_data(CA_ROOT / "examples" / "search-index.json")
    chapters = load_data(CA_ROOT / "examples" / "reasoning-chapters.json")
    request = load_data(CA_ROOT / "examples" / "assembly-request-create.yaml")

    # The honest path assembles, and every rendered element is declared.
    package, _ = module.assemble(compiled, index, chapters, request)
    declared = set(compiled["availableElementIds"])
    for key in ("hardBoundaryElementIds", "factElementIds", "gapElementIds", "activeGuidanceElementIds"):
        assert set(package["selection"][key]) <= declared, key

    # The slot side of the seam holds by construction: every rendered element is
    # looked up in `elementRecords`, and the artefact is refused unless that
    # index equals `availableElementIds`. That equality is the enforcement, so
    # it is what this asserts — an assertion further downstream could not fail
    # and would be evidence of nothing.
    smuggled = copy.deepcopy(compiled)
    victim = package["selection"]["factElementIds"][0]
    smuggled["availableElementIds"] = [item for item in smuggled["availableElementIds"] if item != victim]
    smuggled["artifactHash"] = artefact_hash(smuggled)
    with pytest.raises(ValueError) as caught:
        module.assemble(smuggled, index, chapters, request)
    assert "availableElementIds" in str(caught.value)


def test_s6_a_chapter_block_outside_the_universe_is_filtered_even_when_declared_cleanly():
    """The block filter, exercised on its own.

    The declaration check above fires first for any chapter built by the
    reference generator, because that generator derives `elementIds` and
    `content` from the same source and they therefore agree. A chapter set is
    input, not output: a hand-built one can declare only admissible elements and
    still carry a block for an element the artefact never declared. That is the
    case the block filter exists for, and it is the case an independent review
    found unprotected — removing the filter left the whole suite green.
    """
    spec = importlib.util.spec_from_file_location("seam_assembler3", CA_ROOT / "assemble_context.py")
    assembler = importlib.util.module_from_spec(spec)
    if str(CA_ROOT) not in sys.path:
        sys.path.insert(0, str(CA_ROOT))
    spec.loader.exec_module(assembler)

    compiled = load_data(CA_ROOT / "examples" / "compiled-social-copy-global-en.json")
    index = load_data(CA_ROOT / "examples" / "search-index.json")
    chapters = copy.deepcopy(load_data(CA_ROOT / "examples" / "reasoning-chapters.json"))
    request = load_data(CA_ROOT / "examples" / "assembly-request-create.yaml")

    chapter = next(
        item for item in chapters["chapters"]
        if item["id"] in request["selection"]["reasoningChapterIds"]
    )
    assert set(chapter["elementIds"]) <= set(compiled["availableElementIds"]), (
        "the fixture chapter already declares something outside the universe"
    )
    chapter["content"] = (
        chapter["content"]
        + "\n\n## identity.value.smuggled [identity/core-value/defined]\n"
        + '{"description":"SENTINEL-BLOCK-MARKER","name":"Smuggled"}'
    )
    # Re-seal the view, so this exercises the block filter rather than the
    # derived-view integrity check. A chapter set whose hashes do not reproduce
    # is refused earlier, and is tested separately.
    chapter.pop("chapterHash", None)
    chapter["chapterHash"] = sha256_id(chapter)
    chapters.pop("chapterSetHash", None)
    chapters["chapterSetHash"] = sha256_id(chapters)

    package, model_input = assembler.assemble(compiled, index, chapters, request)
    assert "SENTINEL-BLOCK-MARKER" not in model_input, (
        "a chapter block for an undeclared element reached the model input"
    )
    assert "identity.value.smuggled" not in model_input


def test_s6_a_derived_view_must_reproduce_its_own_hashes():
    """The compiled artefact is checked against its hash; the views were not.

    So a Reasoning Chapter could be edited after generation and still assembled,
    with the stale `chapterHash` and `chapterSetHash` carried into the Model
    Input Package as if they described what was sent. If the forged block's
    heading named an available element, arbitrary text reached the model.
    """
    assembler = _flat_module("seam_assembler_integrity", CA_ROOT / "assemble_context.py")

    compiled = load_data(CA_ROOT / "examples" / "compiled-social-copy-global-en.json")
    index = load_data(CA_ROOT / "examples" / "search-index.json")
    request = load_data(CA_ROOT / "examples" / "assembly-request-create.yaml")

    # A chapter edited in place, its hashes left as generated.
    chapters = copy.deepcopy(load_data(CA_ROOT / "examples" / "reasoning-chapters.json"))
    chapter = next(
        item for item in chapters["chapters"]
        if item["id"] in request["selection"]["reasoningChapterIds"]
    )
    lines = chapter["content"].splitlines()
    chapter["content"] = lines[0] + "\nUNAVAILABLE-SENTINEL-TRUTH\n\n" + "\n".join(lines[2:])
    with pytest.raises(ValueError) as caught:
        assembler.assemble(compiled, index, chapters, request)
    assert "chapterHash" in str(caught.value)

    # And the same for a Search Card, and for the set hashes themselves.
    cards = copy.deepcopy(load_data(CA_ROOT / "examples" / "search-index.json"))
    cards["cards"][0]["label"] = "tampered"
    honest_chapters = load_data(CA_ROOT / "examples" / "reasoning-chapters.json")
    with pytest.raises(ValueError) as caught:
        assembler.assemble(compiled, cards, honest_chapters, request)
    assert "cardHash" in str(caught.value)

    set_level = copy.deepcopy(load_data(CA_ROOT / "examples" / "reasoning-chapters.json"))
    set_level["chapterSetHash"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError) as caught:
        assembler.assemble(compiled, index, set_level, request)
    assert "chapterSetHash" in str(caught.value)

    # The shipped corpus reproduces its own hashes.
    package, _ = assembler.assemble(compiled, index, honest_chapters, request)
    assert package["sources"]["chapterSetHash"] == honest_chapters["chapterSetHash"]


def test_s6_full_delivery_re_checks_the_chapters_the_expansion_produced():
    """Full mode is an expansion, so the universe check has to run on its output.

    The declaration check ran once, on the chapters the *request* selected, and
    `deliveryMode: full` then replaced that selection with every chapter in the
    set. An independent review reproduced the consequence: a chapter the request
    never named carried an element outside `availableElementIds` straight into
    model input.
    """
    from obds_ref.canonical import manifest_content_hash as _content_hash

    builder = _flat_module("seam_builder_full", CA_ROOT / "build_views.py")
    assembler = _flat_module("seam_assembler_full", CA_ROOT / "assemble_context.py")

    manifest = copy.deepcopy(load_data(CA_ROOT / "examples" / "manifest.yaml"))
    plan = copy.deepcopy(load_data(CA_ROOT / "examples" / "build-plan.yaml"))
    chapter_map = copy.deepcopy(load_data(CA_ROOT / "examples" / "chapter-map.yaml"))
    request = copy.deepcopy(load_data(CA_ROOT / "examples" / "assembly-request-create.yaml"))

    smuggled = copy.deepcopy(
        next(item for item in manifest["elements"] if item["id"] == "identity.value.innovation")
    )
    smuggled.update({
        # A valid identity that *contains a space*. The heading parser read only
        # the first whitespace-delimited token, so this was attributed to
        # `identity.value.innovation`, which is in the universe, and kept.
        "id": "identity.value.innovation smuggled",
        "subject": "subject:smuggled",
        "scope": {"locales": ["de"]},
        "value": {"name": "Smuggled", "description": "FULL-MODE-UNIVERSE-LEAK"},
    })
    manifest["elements"].append(smuggled)
    manifest["approval"]["contentHash"] = _content_hash(manifest)
    plan["manifestRef"]["contentHash"] = manifest["approval"]["contentHash"]
    chapter_map["chapters"].append({
        "id": "chapter.smuggled",
        "title": "Smuggled",
        "elementIds": ["identity.value.innovation smuggled"],
    })

    target = next(item for item in plan["targets"] if item["id"] == request["targetId"])
    target["contextAssembly"]["deliveryMode"] = "full"
    request["deliveryMode"] = "full"

    result = build_target(manifest, plan, target)
    assert result.status == "ready", [error.message for error in result.errors]
    assert "identity.value.innovation smuggled" not in result.artefact["availableElementIds"]

    index, chapters = builder.build_views(manifest, chapter_map)
    with pytest.raises(ValueError) as caught:
        assembler.assemble(result.artefact, index, chapters, request)
    assert "declared universe" in str(caught.value)


def test_s6_a_chapter_heading_names_exactly_one_element():
    """The heading parser attributes a block, so it may not attribute it loosely."""
    assembler = _flat_module("seam_assembler_heading", CA_ROOT / "assemble_context.py")

    chapter = {
        "id": "chapter.probe",
        "renderer": {"id": "org.openbranddefinition.reference-chapter-renderer", "version": "1.0.0"},
        "content": (
            "## identity.value.simplicity [identity/core-value/defined]\n"
            '{"name":"Simplicity"}\n\n'
            "## identity.value.simplicity smuggled [identity/core-value/defined]\n"
            '{"description":"HEADING-LEAK"}'
        ),
    }
    universe = {"identity.value.simplicity"}
    content = assembler._filtered_reference_chapter_content(chapter, set(), universe)
    assert "HEADING-LEAK" not in content
    assert "identity.value.simplicity smuggled" not in content


def test_s6_a_reasoning_chapter_cannot_smuggle_an_undeclared_element():
    """The chapter path, which the first correction left open.

    Chapter content was filtered against the elements already rendered into
    other slots, so a block for an element the artefact never declared was not
    in that set and was therefore kept. An out-of-scope element reached the
    model through a Reasoning Chapter while `availableElementIds` never named
    it.
    """
    from obds_ref.canonical import manifest_content_hash as _content_hash

    builder_spec = importlib.util.spec_from_file_location("seam_builder", CA_ROOT / "build_views.py")
    builder = importlib.util.module_from_spec(builder_spec)
    if str(CA_ROOT) not in sys.path:
        sys.path.insert(0, str(CA_ROOT))
    builder_spec.loader.exec_module(builder)
    asm_spec = importlib.util.spec_from_file_location("seam_assembler2", CA_ROOT / "assemble_context.py")
    assembler = importlib.util.module_from_spec(asm_spec)
    asm_spec.loader.exec_module(assembler)

    manifest = copy.deepcopy(load_data(CA_ROOT / "examples" / "manifest.yaml"))
    plan = copy.deepcopy(load_data(CA_ROOT / "examples" / "build-plan.yaml"))
    chapter_map = copy.deepcopy(load_data(CA_ROOT / "examples" / "chapter-map.yaml"))
    request = copy.deepcopy(load_data(CA_ROOT / "examples" / "assembly-request-create.yaml"))

    template = copy.deepcopy(
        next(item for item in manifest["elements"] if item["id"] == "identity.value.simplicity")
    )
    template.update({
        "id": "identity.value.sentinel",
        "subject": "subject:sentinel",
        "scope": {"locales": ["de"]},
        "value": {"name": "Sentinel", "description": "SENTINEL-LEAK-MARKER"},
    })
    manifest["elements"].append(template)
    manifest["approval"]["contentHash"] = _content_hash(manifest)
    plan["manifestRef"]["contentHash"] = manifest["approval"]["contentHash"]
    chapter = next(item for item in chapter_map["chapters"] if item["id"] == "chapter.brand-expression")
    chapter["elementIds"].append("identity.value.sentinel")

    target = next(item for item in plan["targets"] if item["id"] == request["targetId"])
    result = build_target(manifest, plan, target)
    assert result.status == "ready", [error.message for error in result.errors]
    assert "identity.value.sentinel" not in result.artefact["availableElementIds"]

    index, chapters = builder.build_views(manifest, chapter_map)
    with pytest.raises(ValueError) as caught:
        assembler.assemble(result.artefact, index, chapters, request)
    assert "declared universe" in str(caught.value)
