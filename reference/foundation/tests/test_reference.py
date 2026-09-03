from __future__ import annotations

import copy
import json
from pathlib import Path

import yaml
import jsonschema

from obds_ref.canonical import artefact_hash, canonical_json_bytes, sha256_id, value_shape_hash
from obds_ref.compiler import build_all, load_data, read_governed_text, validate_manifest, manifest_change_report
from obds_ref.runtime import run_with_model, assembly_failed_record


ROOT = Path(__file__).resolve().parents[1]


def load_example(name: str):
    manifest = load_data(ROOT / "examples" / name / "manifest.yaml")
    plan = load_data(ROOT / "examples" / name / "build-plan.yaml")
    return manifest, plan


def test_canonical_json_normalises_nfc_and_line_endings():
    composed = {"text": "Café\nLine"}
    decomposed = {"text": "Cafe\u0301\r\nLine"}
    assert canonical_json_bytes(composed) == canonical_json_bytes(decomposed)


def test_simple_target_builds_and_hash_is_reproducible(tmp_path):
    manifest, plan = load_example("simple")
    report_a = build_all(manifest, plan, output_dir=tmp_path / "a")
    report_b = build_all(manifest, plan, output_dir=tmp_path / "b")

    target_a = report_a["targets"][0]
    target_b = report_b["targets"][0]
    assert target_a["status"] == "ready"
    assert target_a["artifactHash"] == target_b["artifactHash"]

    artefact = load_data(tmp_path / "a" / target_a["artifactRef"])
    assert artefact["artifactHash"] == artefact_hash(artefact)


def test_required_unknown_fails_and_emits_no_artefact(tmp_path):
    manifest, plan = load_example("scoped")
    report = build_all(manifest, plan, output_dir=tmp_path)

    results = {item["targetId"]: item for item in report["targets"]}
    assert results["brand-query-global-en"]["status"] == "ready"
    assert results["social-copy-gb-en"]["status"] == "failed"
    assert results["social-copy-gb-en"]["artifactRef"] is None
    assert not (tmp_path / "social-copy-gb-en.context.json").exists()

    failures = {
        item["elementId"]: item
        for item in results["social-copy-gb-en"]["requirements"]
        if item["result"] == "fail"
    }
    assert failures["product.availability"]["actualState"] == "unknown"
    assert failures["claims.approved"]["actualState"] == "unknown"


def test_failed_build_means_no_model_call():
    calls = []

    def model(prompt: str) -> str:
        calls.append(prompt)
        return "should not happen"

    record = run_with_model(None, task_input="Create output", model=model)
    assert record["decision"] == "build_failed"
    assert record["modelCall"]["called"] is False
    assert calls == []


def test_blocking_preflight_means_no_model_call():
    artefact = {
        "kind": "obds-compiled-brand-context",
        "schemaVersion": "3.0.0",
        "id": "urn:test:context",
        "targetId": "test",
        "manifest": {"id": "urn:test:brand", "version": "1.0.0", "contentHash": "sha256:" + "0" * 64},
        # 3.0.0 validates this fixture against the published Compiled Brand
        # Context contract before executing it, so the fixture has to satisfy
        # the contract rather than the subset the runtime used to read.
        "build": {
            "planId": "urn:test:plan",
            "planHash": "sha256:" + "1" * 64,
            "compilerId": "test",
            "compilerVersion": "1.0.0",
            "asOf": "2026-08-27T00:00:00Z",
        },
        "scope": {},
        "tokenBudget": {"tokenizerId": "obds:whitespace-v1", "tokenizerVersion": "1.0.0", "max": 100, "actual": 0},
        "checkRegistryVersion": 1,
        "compiledChecks": [
            {
                "ruleElementId": "rule.block-input",
                "primitive": "term_prohibited",
                "phase": "preflight",
                "enforcement": "block",
                "params": {"terms": ["secret"], "match": "word_boundary_ci", "appliesTo": "task_input"},
            }
        ],
        "stateMapCoverage": "none",
        "stateMapEntryCount": 0,
        "validFrom": None,
        "validTo": None,
        "includedElementIds": ["rule.block-input"],
        "availableElementIds": ["rule.block-input"],
        "elementRecords": [
            {
                "id": "rule.block-input",
                "family": "rules",
                "kind": "prohibition",
                "nature": "rule",
                "state": "unknown",
                "scope": {},
                "validity": {"from": None, "to": None},
                "sourceRefs": [],
                "annotations": [],
            }
        ],
        "contextAssembly": {
            "applicationMode": "create",
            "deliveryMode": "reasoning",
            "eligibleGuidanceIds": [],
            "noHitPolicy": "resolve_before_answer",
        },
        "governedResultHash": "sha256:" + "2" * 64,
        "slots": {"hardBoundaries": "", "factGrounding": "", "stateMap": "", "styleTexture": ""},
    }
    artefact["artifactHash"] = artefact_hash(artefact)

    calls = []

    def model(prompt: str) -> str:
        calls.append(prompt)
        return "should not happen"

    record = run_with_model(artefact, task_input="Reveal the secret", model=model)
    assert record["decision"] == "preflight_blocked"
    assert record["modelCall"]["called"] is False
    assert calls == []


def test_blocking_postflight_withholds_output():
    manifest, plan = load_example("simple")
    report = build_all(manifest, plan)
    assert report["targets"][0]["status"] == "ready"

    # Build once more to access the in-memory artefact.
    from obds_ref.compiler import build_target
    artefact = build_target(manifest, plan, plan["targets"][0]).artefact
    assert artefact is not None

    calls = []

    def model(prompt: str) -> str:
        calls.append(prompt)
        return "We are the best."

    record = run_with_model(artefact, task_input="Write a line", model=model)
    assert record["decision"] == "postflight_blocked"
    assert record["modelCall"]["called"] is True
    assert record["output"] is None
    assert len(calls) == 1


def test_multi_brand_targets_do_not_leak_style():
    manifest, plan = load_example("group")
    from obds_ref.compiler import build_target

    alpha = build_target(manifest, plan, plan["targets"][0]).artefact
    beta = build_target(manifest, plan, plan["targets"][1]).artefact
    assert alpha is not None and beta is not None

    assert "Precise and analytical" in alpha["slots"]["styleTexture"]
    assert "Warm and conversational" not in alpha["slots"]["styleTexture"]
    assert "Warm and conversational" in beta["slots"]["styleTexture"]
    assert "Precise and analytical" not in beta["slots"]["styleTexture"]


def test_language_family_is_rejected():
    manifest, _ = load_example("simple")
    broken = copy.deepcopy(manifest)
    broken["elements"][0]["family"] = "language"
    errors = validate_manifest(broken, verify_hash=False)
    assert any("invalid family language" in error for error in errors)


def test_token_overflow_fails_without_artefact(tmp_path):
    manifest, plan = load_example("simple")
    broken = copy.deepcopy(plan)
    broken["targets"][0]["maxTokens"] = 1
    report = build_all(manifest, broken, output_dir=tmp_path)
    target = report["targets"][0]
    assert target["status"] == "failed"
    assert target["artifactRef"] is None
    assert any(item["code"] == "OBDS-BUILD-TOKEN-OVERFLOW" for item in target["errors"])


def test_duplicate_element_id_is_a_conflict():
    manifest, _ = load_example("simple")
    broken = copy.deepcopy(manifest)
    broken["elements"].append(copy.deepcopy(broken["elements"][0]))
    errors = validate_manifest(broken, verify_hash=False)
    assert any("duplicate element id" in error for error in errors)


def test_dead_rule_reference_fails():
    errors=validate_manifest(load_data(ROOT/"fixtures"/"invalid-dead-rule-reference.yaml"),verify_hash=False)
    assert any("internal element reference not found" in x for x in errors)

def test_dead_check_reference_fails():
    errors=validate_manifest(load_data(ROOT/"fixtures"/"invalid-dead-check-reference.yaml"),verify_hash=False)
    assert any("internal element reference not found" in x for x in errors)

def test_dead_build_plan_reference_fails():
    manifest,_=load_example("simple"); plan=load_data(ROOT/"fixtures"/"invalid-dead-build-plan-reference.yaml")
    from obds_ref.compiler import ValidationFailure
    try: build_all(manifest,plan)
    except ValidationFailure as err: assert any("requiresDefined reference not found" in x for x in err.errors)
    else: raise AssertionError("expected failure")

def test_colour_mismatch_fails():
    errors=validate_manifest(load_data(ROOT/"fixtures"/"invalid-colour-mismatch.yaml"),verify_hash=False)
    assert any("different sRGB values" in x for x in errors)

def test_supersedes_rejected():
    errors=validate_manifest(load_data(ROOT/"fixtures"/"invalid-foundation-supersedes.yaml"),verify_hash=False)
    assert any("supersedes is not part" in x for x in errors)

def test_manifest_diff_deterministic():
    old=load_data(ROOT/"fixtures"/"diff-old-manifest.yaml"); new=load_data(ROOT/"fixtures"/"diff-new-manifest.yaml"); a=manifest_change_report(old,new); b=manifest_change_report(old,new); assert a==b; assert [x["elementId"] for x in a["added"]]==["identity.purpose"]; assert [x["elementId"] for x in a["changed"]]==["identity.voice"]; assert [x["elementId"] for x in a["removed"]]==["rule.no-best"]

def test_runtime_record_ndjson(tmp_path):
    manifest, plan = load_example("simple")
    from obds_ref.compiler import build_target
    artefact = build_target(manifest, plan, plan["targets"][0]).artefact
    path = tmp_path / "runtime.ndjson"
    record = run_with_model(
        artefact,
        task_input="Write",
        model=lambda prompt: ("Useful.", "req-1"),
        provider="test",
        model_id="model",
        record_path=path,
    )
    assert record["decision"] == "released"
    assert record["modelCall"]["requestId"] == "req-1"
    assert record["assemblyHash"] is None
    assert record["modelInputHash"] is None
    # Section 28.1: a Runtime Decision Record is governed evidence, one NDJSON
    # line at a time.
    persisted = read_governed_text(path.read_text().splitlines()[0], is_json=True)
    assert "output" not in persisted
    schema = load_data(ROOT / "schemas" / "runtime-decision-record.schema.json")
    jsonschema.validate(persisted, schema)


def test_assembly_failed_runtime_record_is_schema_valid():
    record = assembly_failed_record(
        target_id="example",
        artefact=None,
        task_input="Test",
    )
    payload = {key: value for key, value in record.items() if key != "output"}
    schema = load_data(ROOT / "schemas" / "runtime-decision-record.schema.json")
    jsonschema.validate(payload, schema)
    assert payload["decision"] == "assembly_failed"
    assert payload["assemblyHash"] is None
    assert payload["modelInputHash"] is None

def test_invalid_hash_no_call():
    calls=[]; record=run_with_model({"kind":"obds-compiled-brand-context","artifactHash":"sha256:"+"0"*64},task_input="Test",model=lambda p:calls.append(p) or "never",target_id="test"); assert record["decision"]=="no_valid_artifact"; assert not record["modelCall"]["called"]; assert calls==[]


def _schema_contract(manifest_id, *, contract_id, family, kind, value, schema_name, validator_ref=None):
    schema = json.loads((ROOT / "value-schemas" / schema_name).read_text(encoding="utf-8"))
    return {
        "id": contract_id,
        "family": family,
        "kind": kind,
        "shapeHash": value_shape_hash(value),
        "schemaRef": schema["$id"],
        "schemaHash": sha256_id(schema),
        "validatorRef": validator_ref,
    }


def test_value_shape_contract_rejects_string_to_object_mutation():
    old_value = "#F66300"
    contract_id = "urn:obds:brand:shape-test#value-contract:design:colour:v1"
    manifest = {
        "id": "urn:obds:brand:shape-test",
        "kind": "brand-manifest",
        "name": "Shape Test",
        "schemaVersion": "1.0.0",
        "version": "1.0.0",
        "status": "draft",
        "owner": "Test",
        "profiles": ["obds-foundation"],
        "valueContracts": [
            _schema_contract(
                "urn:obds:brand:shape-test",
                contract_id=contract_id,
                family="design",
                kind="colour",
                value=old_value,
                schema_name="colour-hex.schema.json",
            )
        ],
        "elements": [
            {
                "id": "design.orange",
                "family": "design",
                "kind": "colour",
                "nature": "fact",
                "state": "defined",
                "value": {
                    "name": "Orange",
                    "hex": "#F66300",
                    "rgb": [246, 99, 0],
                    "cmyk": [0, 75, 100, 0],
                    "pantone": "021 C",
                },
                "valueContractRef": contract_id,
            }
        ],
    }
    errors = validate_manifest(manifest, verify_hash=False)
    assert any("value shape mismatch" in error for error in errors)


def test_value_contract_semantic_schema_rejects_invalid_colour():
    value = {"name": "Orange", "hex": "F66300", "rgb": [246, 99, 999]}
    contract_id = "urn:obds:brand:schema-test#value-contract:design:colour:v1"
    manifest = {
        "id": "urn:obds:brand:schema-test",
        "kind": "brand-manifest",
        "name": "Schema Test",
        "schemaVersion": "1.0.0",
        "version": "1.0.0",
        "status": "draft",
        "owner": "Test",
        "profiles": ["obds-foundation"],
        "valueContracts": [
            _schema_contract(
                "urn:obds:brand:schema-test",
                contract_id=contract_id,
                family="design",
                kind="colour",
                value=value,
                schema_name="colour.schema.json",
                validator_ref="obds:validator:colour-consistency-v1",
            )
        ],
        "elements": [
            {
                "id": "design.orange",
                "family": "design",
                "kind": "colour",
                "nature": "fact",
                "state": "defined",
                "value": value,
                "valueContractRef": contract_id,
            }
        ],
    }
    errors = validate_manifest(manifest, verify_hash=False)
    assert any("fails contract schema" in error for error in errors)


def test_semantic_boundary_contract_is_structured_knowledge():
    value = {
        "subject": "voice",
        "quality": "confident",
        "is": ["clear", "specific", "decisive", "grounded"],
        "isNot": ["aggressive", "boastful", "absolute_without_evidence"],
        "tieBreaker": {"prefer": "precise", "over": "forceful"},
    }
    contract_id = "urn:obds:brand:boundary#value-contract:stance:semantic-boundary:v1"
    manifest = {
        "id": "urn:obds:brand:boundary",
        "kind": "brand-manifest",
        "name": "Boundary Test",
        "schemaVersion": "1.0.0",
        "version": "1.0.0",
        "status": "draft",
        "owner": "Test",
        "profiles": ["obds-foundation"],
        "valueContracts": [
            _schema_contract(
                "urn:obds:brand:boundary",
                contract_id=contract_id,
                family="stance",
                kind="semantic-boundary",
                value=value,
                schema_name="semantic-boundary.schema.json",
            )
        ],
        "elements": [
            {
                "id": "stance.voice.confidence",
                "family": "stance",
                "kind": "semantic-boundary",
                "nature": "knowledge",
                "state": "defined",
                "value": value,
                "valueContractRef": contract_id,
            }
        ],
    }
    assert validate_manifest(manifest, verify_hash=False) == []


def test_manifest_change_report_separates_shape_from_source_rotation():
    old_value = "#F66300"
    old_contract_id = "urn:obds:brand:shape-diff#value-contract:design:colour:v1"
    old = {
        "id": "urn:obds:brand:shape-diff",
        "kind": "brand-manifest",
        "name": "Shape Diff",
        "schemaVersion": "1.0.0",
        "version": "1.0.0",
        "status": "draft",
        "owner": "Test",
        "profiles": ["obds-foundation"],
        "valueContracts": [
            _schema_contract(
                "urn:obds:brand:shape-diff",
                contract_id=old_contract_id,
                family="design",
                kind="colour",
                value=old_value,
                schema_name="colour-hex.schema.json",
            )
        ],
        "elements": [
            {
                "id": "design.orange",
                "family": "design",
                "kind": "colour",
                "nature": "fact",
                "state": "defined",
                "value": old_value,
                "valueContractRef": old_contract_id,
                "sourceRefs": ["dossier#sha256:old"],
            },
            {
                "id": "identity.voice",
                "family": "identity",
                "kind": "voice-system",
                "nature": "knowledge",
                "state": "defined",
                "value": "Warm expert",
                "sourceRefs": ["dossier#sha256:old"],
            },
        ],
    }
    new = copy.deepcopy(old)
    new["version"] = "1.1.0"
    new_value = {
        "name": "Orange",
        "hex": "#F66300",
        "rgb": [246, 99, 0],
        "cmyk": [0, 75, 100, 0],
        "pantone": "021 C",
    }
    new_contract_id = "urn:obds:brand:shape-diff#value-contract:design:colour:v2"
    new["valueContracts"] = [
        _schema_contract(
            "urn:obds:brand:shape-diff",
            contract_id=new_contract_id,
            family="design",
            kind="colour",
            value=new_value,
            schema_name="colour.schema.json",
            validator_ref="obds:validator:colour-consistency-v1",
        )
    ]
    new["elements"][0]["value"] = new_value
    new["elements"][0]["valueContractRef"] = new_contract_id
    for element in new["elements"]:
        element["sourceRefs"] = ["dossier#sha256:new"]

    report = manifest_change_report(old, new)
    by_id = {item["elementId"]: item for item in report["changed"]}
    assert {"value_shape", "contract", "sources"}.issubset(by_id["design.orange"]["changeKinds"])
    assert by_id["identity.voice"]["changeKinds"] == ["sources"]
    assert report["compatibility"]["patchEligible"] is False


def test_patch_transition_rejects_shape_change_even_when_contract_is_updated():
    from obds_ref.compiler import validate_manifest_version_transition
    old_value = "#F66300"
    old_contract_id = "urn:obds:brand:patch-shape#value-contract:design:colour:v1"
    old = {
        "id": "urn:obds:brand:patch-shape",
        "kind": "brand-manifest",
        "name": "Patch Shape",
        "schemaVersion": "1.0.0",
        "version": "1.2.3",
        "status": "draft",
        "owner": "Test",
        "profiles": ["obds-foundation"],
        "valueContracts": [
            _schema_contract(
                "urn:obds:brand:patch-shape",
                contract_id=old_contract_id,
                family="design",
                kind="colour",
                value=old_value,
                schema_name="colour-hex.schema.json",
            )
        ],
        "elements": [
            {
                "id": "design.orange",
                "family": "design",
                "kind": "colour",
                "nature": "fact",
                "state": "defined",
                "value": old_value,
                "valueContractRef": old_contract_id,
            }
        ],
    }
    new = copy.deepcopy(old)
    new["version"] = "1.2.4"
    new_value = {"name": "Orange", "hex": "#F66300"}
    new_contract_id = "urn:obds:brand:patch-shape#value-contract:design:colour:v2"
    new["valueContracts"] = [
        _schema_contract(
            "urn:obds:brand:patch-shape",
            contract_id=new_contract_id,
            family="design",
            kind="colour",
            value=new_value,
            schema_name="colour.schema.json",
            validator_ref="obds:validator:colour-consistency-v1",
        )
    ]
    new["elements"][0]["value"] = new_value
    new["elements"][0]["valueContractRef"] = new_contract_id
    errors = validate_manifest_version_transition(old, new)
    assert any("PATCH manifest transition" in error for error in errors)


def test_patch_transition_allows_source_only_rotation():
    from obds_ref.compiler import validate_manifest_version_transition
    value = {"name": "Orange", "hex": "#F66300"}
    contract_id = "urn:obds:brand:patch-source#value-contract:design:colour:v1"
    old = {
        "id": "urn:obds:brand:patch-source",
        "kind": "brand-manifest",
        "name": "Patch Source",
        "schemaVersion": "1.0.0",
        "version": "1.2.3",
        "status": "draft",
        "owner": "Test",
        "profiles": ["obds-foundation"],
        "valueContracts": [
            _schema_contract(
                "urn:obds:brand:patch-source",
                contract_id=contract_id,
                family="design",
                kind="colour",
                value=value,
                schema_name="colour.schema.json",
                validator_ref="obds:validator:colour-consistency-v1",
            )
        ],
        "elements": [
            {
                "id": "design.orange",
                "family": "design",
                "kind": "colour",
                "nature": "fact",
                "state": "defined",
                "value": value,
                "valueContractRef": contract_id,
                "sourceRefs": ["dossier#sha256:old"],
            }
        ],
    }
    new = copy.deepcopy(old)
    new["version"] = "1.2.4"
    new["elements"][0]["sourceRefs"] = ["dossier#sha256:new"]
    assert validate_manifest_version_transition(old, new) == []

