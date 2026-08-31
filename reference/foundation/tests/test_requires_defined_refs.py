from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from obds_ref.canonical import manifest_content_hash, sha256_id, value_shape_hash
from obds_ref.compiler import (
    ValidationFailure,
    build_all,
    build_target,
    load_data,
    validate_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT.parents[1]
RULE_ID = "rule.dependency-policy"


def _example():
    base = PACKAGE_ROOT / "examples" / "foundation-minimal"
    return load_data(base / "manifest.yaml"), load_data(base / "build-plan.yaml")


def _dependency(
    template,
    element_id,
    *,
    state="defined",
    scope=None,
    validity=None,
    subject=None,
):
    element = copy.deepcopy(template)
    element["id"] = element_id
    element["subject"] = subject or element_id
    element["state"] = state
    element["scope"] = copy.deepcopy(scope or {})
    element["validity"] = copy.deepcopy(validity or {"from": None, "to": None})
    if state == "defined":
        element["value"] = {"name": element_id}
    else:
        element.pop("value", None)
        element.pop("valueContractRef", None)
    return element


def _rule(
    rule_id,
    *,
    requires=None,
    references=None,
    scope=None,
    obligation="recommend",
    enforcement="warn",
):
    value = {
        "statement": "Apply this rule only when its explicit dependencies resolve.",
        "obligation": obligation,
        "enforcement": enforcement,
        "validationMode": "deterministic",
        "checks": [{
            "primitive": "term_prohibited",
            "phase": "postflight",
            "params": {
                "terms": ["forbidden dependency test term"],
                "match": "case_insensitive",
                "appliesTo": "output",
            },
        }],
        "condition": {},
        "requirement": {},
        "references": list(references or []),
        "requiresDefinedRefs": list(requires or []),
    }
    return {
        "id": rule_id,
        "family": "rules",
        "kind": "rule",
        "nature": "fact",
        "state": "defined",
        "scope": copy.deepcopy(scope or {}),
        "sourceRefs": [],
        "validity": {"from": None, "to": None},
        "annotations": [],
        "value": value,
        "valueContractRef": f"urn:obds:test#contract:{rule_id}",
    }


def _rule_contract(rule):
    schema = json.loads(
        (ROOT / "value-schemas" / "rule.schema.json").read_text(encoding="utf-8")
    )
    return {
        "id": rule["valueContractRef"],
        "family": "rules",
        "kind": "rule",
        "shapeHash": value_shape_hash(rule["value"]),
        "schemaRef": schema["$id"],
        "schemaHash": sha256_id(schema),
        "validatorRef": None,
    }


def _case_manifest(dependencies, rules):
    manifest, plan = _example()
    manifest = copy.deepcopy(manifest)
    plan = copy.deepcopy(plan)
    manifest["elements"] = [manifest["elements"][0], *dependencies, *rules]
    manifest["valueContracts"].extend(_rule_contract(rule) for rule in rules)
    manifest["approval"].pop("contentHash", None)
    manifest["approval"]["contentHash"] = manifest_content_hash(manifest)
    plan["manifestRef"]["contentHash"] = manifest["approval"]["contentHash"]
    return manifest, plan


def _failing_case(case_id):
    base_manifest, _ = _example()
    template = base_manifest["elements"][0]
    dependency_id = "dep.required"
    dependencies = []
    required_refs = [dependency_id]
    expected_code = "OBDS-BUILD-REQUIRED-NOT-DEFINED"
    expected_actual = None
    rule_options = {}

    if case_id == "missing":
        expected_code = "OBDS-BUILD-REQUIRED-NOT-FOUND"
        expected_actual = "missing"
    elif case_id in {"unknown", "not-defined", "not-applicable"}:
        state = case_id.replace("-", "_")
        dependencies.append(_dependency(template, dependency_id, state=state))
        expected_actual = state
    elif case_id == "out-of-scope":
        dependencies.append(
            _dependency(template, dependency_id, scope={"markets": ["DE"]})
        )
        expected_code = "OBDS-BUILD-REQUIRED-OUT-OF-SCOPE"
        expected_actual = "not_applicable"
    elif case_id == "expired":
        dependencies.append(_dependency(
            template,
            dependency_id,
            validity={"from": None, "to": "2026-01-01T00:00:00Z"},
        ))
        expected_code = "OBDS-BUILD-REQUIRED-EXPIRED"
        expected_actual = "not_applicable"
    elif case_id == "lost-subject":
        dependencies.extend([
            _dependency(template, dependency_id, subject="dep.subject"),
            _dependency(
                template,
                "dep.override",
                subject="dep.subject",
                scope={"locales": ["en"]},
            ),
        ])
        expected_actual = "not_applicable"
    elif case_id == "subject-conflict":
        dependencies.extend([
            _dependency(
                template,
                dependency_id,
                subject="dep.subject",
                scope={"locales": ["en"]},
            ),
            _dependency(
                template,
                "dep.other",
                subject="dep.subject",
                scope={"outputTypes": ["brand-query"]},
            ),
        ])
        expected_code = "OBDS-BUILD-SUBJECT-CONFLICT"
        expected_actual = "not_applicable"
    elif case_id == "several-one-fails":
        dependencies.extend([
            _dependency(template, "dep.valid"),
            _dependency(template, dependency_id, state="unknown"),
        ])
        required_refs = ["dep.valid", dependency_id]
        expected_actual = "unknown"
    elif case_id == "prohibit-block":
        dependencies.append(_dependency(template, dependency_id, state="unknown"))
        expected_actual = "unknown"
        rule_options = {"obligation": "prohibit", "enforcement": "block"}
    else:
        raise AssertionError(f"unknown test case: {case_id}")

    rule = _rule(RULE_ID, requires=required_refs, **rule_options)
    manifest, plan = _case_manifest(dependencies, [rule])
    return manifest, plan, expected_code, expected_actual


@pytest.mark.parametrize(
    "case_id",
    [
        "missing",
        "unknown",
        "not-defined",
        "not-applicable",
        "out-of-scope",
        "expired",
        "lost-subject",
        "subject-conflict",
        "several-one-fails",
        "prohibit-block",
    ],
)
def test_unresolved_rule_dependency_fails_without_artefact(case_id, tmp_path):
    manifest, plan, expected_code, expected_actual = _failing_case(case_id)

    # build_target is deliberately exercised directly so the NOT-FOUND defence
    # remains covered even though normal build_all callers validate first.
    result = build_target(manifest, plan, plan["targets"][0])
    assert result.status == "failed"
    assert result.artefact is None
    assert expected_code in [error.code for error in result.errors]

    failed = [
        requirement
        for requirement in result.requirements
        if requirement.get("requiringRuleElementId") == RULE_ID
        and requirement["result"] == "fail"
    ]
    assert len(failed) == 1
    assert failed[0]["elementId"] == "dep.required"
    assert failed[0]["actualState"] == expected_actual

    output_dir = tmp_path / case_id
    if case_id == "missing":
        with pytest.raises(ValidationFailure):
            build_all(manifest, plan, output_dir=output_dir)
    else:
        report = build_all(manifest, plan, output_dir=output_dir)
        target = report["targets"][0]
        assert target["status"] == "failed"
        assert target["artifactRef"] is None
        assert any(
            requirement.get("requiringRuleElementId") == RULE_ID
            and requirement["elementId"] == "dep.required"
            and requirement["result"] == "fail"
            for requirement in target["requirements"]
        )
        assert expected_code in [error["code"] for error in target["errors"]]
    assert not list(tmp_path.rglob("*.context.json"))

    if case_id == "subject-conflict":
        conflict = next(
            item for item in result.conflicts if item["subject"] == "dep.subject"
        )
        assert conflict["decisionRelevant"] is True
    if case_id == "several-one-fails":
        passed = [
            requirement
            for requirement in result.requirements
            if requirement.get("requiringRuleElementId") == RULE_ID
            and requirement["result"] == "pass"
        ]
        assert [item["elementId"] for item in passed] == ["dep.valid"]
    if case_id == "prohibit-block":
        assert result.artefact is None, "the blocking check must never become usable"


def test_defined_rule_dependency_preserves_ready_build_and_reports_rule(tmp_path):
    base_manifest, _ = _example()
    dependency = _dependency(base_manifest["elements"][0], "dep.defined")
    rule = _rule(RULE_ID, requires=["dep.defined"])
    manifest, plan = _case_manifest([dependency], [rule])

    report = build_all(manifest, plan, output_dir=tmp_path)
    target = report["targets"][0]
    assert target["status"] == "ready"
    assert target["artifactRef"] is not None
    assert (tmp_path / target["artifactRef"]).is_file()
    assert {
        "elementId": "dep.defined",
        "expectedState": "defined",
        "actualState": "defined",
        "result": "pass",
        "requiringRuleElementId": RULE_ID,
    } in target["requirements"]


def test_references_and_non_applicable_rules_do_not_create_prerequisites(tmp_path):
    base_manifest, _ = _example()
    template = base_manifest["elements"][0]
    dependencies = [
        _dependency(template, "dep.defined"),
        _dependency(template, "dep.unresolved", state="unknown"),
    ]
    rules = [
        _rule(RULE_ID, requires=["dep.defined"]),
        _rule("rule.references-only", references=["dep.unresolved"]),
        _rule(
            "rule.out-of-scope",
            requires=["dep.unresolved"],
            scope={"markets": ["DE"]},
        ),
    ]
    manifest, plan = _case_manifest(dependencies, rules)

    report = build_all(manifest, plan, output_dir=tmp_path)
    target = report["targets"][0]
    assert target["status"] == "ready"
    assert (tmp_path / target["artifactRef"]).is_file()
    rule_requirements = [
        item for item in target["requirements"] if "requiringRuleElementId" in item
    ]
    assert [item["requiringRuleElementId"] for item in rule_requirements] == [RULE_ID]
    assert [item["elementId"] for item in rule_requirements] == ["dep.defined"]


def test_requires_defined_refs_are_manifest_internal_references():
    rule = _rule(RULE_ID, requires=["dep.missing"])
    manifest, _ = _case_manifest([], [rule])

    errors = validate_manifest(manifest, verify_hash=False)
    assert any(
        f"{RULE_ID}: internal element reference not found at "
        "value.requiresDefinedRefs[0]: dep.missing" in error
        for error in errors
    )


def test_rule_that_loses_subject_precedence_does_not_bind_dependencies(tmp_path):
    base_manifest, _ = _example()
    dependency = _dependency(
        base_manifest["elements"][0], "dep.losing-rule", state="unknown"
    )
    broader_rule = _rule("rule.broader", requires=[dependency["id"]])
    specific_rule = _rule("rule.specific", scope={"locales": ["en"]})
    broader_rule["subject"] = specific_rule["subject"] = "rule.shared-subject"
    manifest, plan = _case_manifest(
        [dependency], [broader_rule, specific_rule]
    )

    report = build_all(manifest, plan, output_dir=tmp_path)
    target = report["targets"][0]
    assert target["status"] == "ready"
    assert target["artifactRef"] is not None
    assert (tmp_path / target["artifactRef"]).is_file()
    assert target["errors"] == []
    assert all(item["result"] == "pass" for item in target["requirements"])
    assert not any(
        item.get("requiringRuleElementId") == broader_rule["id"]
        or item["elementId"] == dependency["id"]
        for item in target["requirements"]
    )


def test_rule_dependency_makes_subject_conflict_decision_relevant(tmp_path):
    base_manifest, _ = _example()
    template = base_manifest["elements"][0]
    dependencies = [
        _dependency(
            template,
            "dep.required-conflict",
            state="unknown",
            subject="dep.conflicting-subject",
            scope={"locales": ["en"]},
        ),
        _dependency(
            template,
            "dep.other-conflict",
            state="unknown",
            subject="dep.conflicting-subject",
            scope={"outputTypes": ["brand-query"]},
        ),
    ]
    rule = _rule(RULE_ID, requires=["dep.required-conflict"])
    manifest, plan = _case_manifest(dependencies, [rule])
    target = plan["targets"][0]
    target["stateMap"] = {"mode": "none", "kinds": []}
    target["styleTexture"] = {"mode": "none", "elementIds": []}

    report = build_all(manifest, plan, output_dir=tmp_path)
    target_report = report["targets"][0]
    conflict = next(
        item
        for item in target_report["conflicts"]
        if item["subject"] == "dep.conflicting-subject"
    )
    assert conflict["decisionRelevant"] is True
    assert "OBDS-BUILD-SUBJECT-CONFLICT" in [
        error["code"] for error in target_report["errors"]
    ]
