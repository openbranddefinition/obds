from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

import jsonschema
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT.parent


def _schema_dir(root, name):
    """Resolve schemas/ and value-schemas/ in either supported layout: flat in an
    unpacked release archive, under 1.0.0/ in the working repository."""
    flat = root / name
    if any(flat.glob("*.json")):
        return flat
    versioned = flat / "1.0.0"
    if any(versioned.glob("*.json")):
        return versioned
    return flat


VALUE_SCHEMAS = _schema_dir(PACKAGE_ROOT, "value-schemas")
sys.path.insert(0, str(ROOT / "foundation" / "src"))

from obds_ref.canonical import canonical_json_bytes, manifest_content_hash, sha256_id
from obds_ref.checks import validate_check
from obds_ref.compiler import (
    ValidationFailure,
    build_all,
    build_target,
    load_data,
    manifest_change_report,
    validate_manifest,
    validate_manifest_version_transition,
)
from obds_ref.runtime import run_with_model


def load_simple():
    ex = ROOT / "foundation" / "examples" / "simple"
    return load_data(ex / "manifest.yaml"), load_data(ex / "build-plan.yaml")


def approve(manifest):
    manifest["status"] = "approved"
    manifest.setdefault("approval", {})
    manifest["approval"].update({
        "approvedBy": "role:test",
        "approvedAt": "2026-08-27T00:00:00Z",
    })
    manifest["approval"]["contentHash"] = manifest_content_hash(manifest)
    return manifest


def bind(plan, manifest):
    plan["manifestRef"] = {
        "id": manifest["id"],
        "version": manifest["version"],
        "contentHash": manifest_content_hash(manifest),
    }
    return plan


def minimal_manifest(elements):
    return approve({
        "id": "urn:obds:brand:adversarial",
        "kind": "brand-manifest",
        "name": "Adversarial",
        "schemaVersion": "1.0.0",
        "version": "1.0.0",
        "status": "draft",
        "owner": "Test",
        "profiles": ["obds-foundation"],
        "valueContracts": [],
        "elements": elements,
    })


def minimal_plan(manifest, scope):
    return {
        "id": "urn:obds:plan:adversarial",
        "kind": "obds-build-plan",
        "schemaVersion": "1.0.0",
        "asOf": "2026-08-27T00:00:00Z",
        "manifestRef": {
            "id": manifest["id"], "version": manifest["version"],
            "contentHash": manifest_content_hash(manifest),
        },
        "compiler": {"id": "org.openbranddefinition.reference-compiler", "version": "1.0.0"},
        "tokenizer": {"id": "obds:whitespace-v1", "version": "1.0.0"},
        "targets": [{
            "id": "target", "scope": scope, "maxTokens": 5000,
            "requiresDefined": [],
            "styleTexture": {"mode": "all", "elementIds": []},
            "stateMap": {"mode": "all_applicable", "kinds": []},
        }],
    }


def test_b1_asof_is_explicit_and_runtime_rejects_expired_context():
    manifest = minimal_manifest([
        {
            "id": "identity.seasonal",
            "family": "identity", "kind": "seasonal-guidance", "nature": "knowledge",
            "state": "defined", "value": "Summer",
            "scope": {}, "sourceRefs": [],
            "validity": {"from": "2026-08-01T00:00:00Z", "to": "2026-09-30T00:00:00Z"},
        }
    ])
    plan = minimal_plan(manifest, {"outputTypes": ["brand-query"]})
    result = build_target(manifest, plan, plan["targets"][0])
    assert result.status == "ready"
    assert result.artefact["build"]["asOf"] == plan["asOf"]
    assert result.artefact["validTo"] == "2026-09-30T00:00:00Z"
    record = run_with_model(
        result.artefact,
        task_input="test",
        model=lambda prompt: "ok",
        runtime_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
    )
    assert record["decision"] == "no_valid_artifact"
    assert record["modelCall"]["called"] is False


def test_b2_specific_subject_wins():
    manifest = minimal_manifest([
        {"id":"global","subject":"design.primary-colour","family":"design","kind":"colour-guidance","nature":"knowledge","state":"defined","value":"global","scope":{},"sourceRefs":[]},
        {"id":"at","subject":"design.primary-colour","family":"design","kind":"colour-guidance","nature":"knowledge","state":"defined","value":"austria","scope":{"markets":["at"]},"sourceRefs":[]},
    ])
    plan = minimal_plan(manifest, {"markets":["at"],"outputTypes":["brand-query"]})
    result=build_target(manifest,plan,plan["targets"][0])
    assert result.status == "ready"
    assert result.artefact["availableElementIds"] == ["at"]
    assert "austria" in result.artefact["slots"]["styleTexture"]
    assert "global" not in result.artefact["slots"]["styleTexture"]


def test_b2_incomparable_subjects_fail_and_report_conflict():
    manifest = minimal_manifest([
        {"id":"market","subject":"design.primary-colour","family":"design","kind":"guidance","nature":"knowledge","state":"defined","value":"market","scope":{"markets":["at"]},"sourceRefs":[]},
        {"id":"social","subject":"design.primary-colour","family":"design","kind":"guidance","nature":"knowledge","state":"defined","value":"social","scope":{"channels":["social"]},"sourceRefs":[]},
    ])
    plan=minimal_plan(manifest,{"markets":["at"],"channels":["social"],"outputTypes":["brand-query"]})
    report=build_all(manifest,plan)
    target=report["targets"][0]
    assert target["status"] == "failed"
    assert target["conflicts"][0]["subject"] == "design.primary-colour"
    assert set(target["conflicts"][0]["elementIds"]) == {"market","social"}


def test_b3_integer_and_integral_float_canonicalise_identically():
    assert canonical_json_bytes({"n":1}) == canonical_json_bytes({"n":1.0})
    assert canonical_json_bytes({"n":-0.0}) == b'{"n":0}'


def test_b3_python_and_javascript_canonical_vectors_match():
    vector_path = Path(__file__).with_name("canonical-vectors.json")
    raws = json.loads(vector_path.read_text())
    py = [canonical_json_bytes(json.loads(raw)).decode() for raw in raws]
    proc = subprocess.run(
        ["node", str(Path(__file__).with_name("canonical_js.mjs")), str(vector_path)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    js = proc.stdout.strip().splitlines()
    assert py == js


def test_b3_duplicate_json_keys_are_rejected(tmp_path):
    p=tmp_path/"dup.json"; p.write_text('{"a":1,"a":2}',encoding="utf-8")
    with pytest.raises(ValidationFailure, match="duplicate object key"):
        load_data(p)


def test_b3_yaml_no_is_string_and_duplicate_yaml_keys_are_rejected(tmp_path):
    p=tmp_path/"no.yaml"; p.write_text('scope:\n  markets: [NO]\n',encoding="utf-8")
    assert load_data(p)["scope"]["markets"] == ["NO"]
    d=tmp_path/"dup.yaml"; d.write_text('a: 1\na: 2\n',encoding="utf-8")
    with pytest.raises(ValidationFailure, match="duplicate mapping key"):
        load_data(d)


def test_b4_require_approval_failure_withholds_output():
    manifest,plan=load_simple()
    rule=next(e for e in manifest["elements"] if e["family"]=="rules" and e["state"]=="defined")
    rule["value"]["enforcement"]="require_approval"
    rule["value"]["checks"][0]["params"]["terms"]=["market leader"]
    approve(manifest); bind(plan,manifest)
    result=build_target(manifest,plan,plan["targets"][0])
    assert result.status == "ready"
    record=run_with_model(result.artefact,task_input="Write",model=lambda p:"We are the market leader.")
    assert record["decision"] == "approval_required"
    assert record["output"] is None


def test_h1_phase_applies_to_mismatch_is_invalid():
    check={"primitive":"term_prohibited","params":{"terms":["cheap"],"appliesTo":"task_input"}}
    errors=validate_check(check)
    assert any("incompatible" in error for error in errors)


def test_h1_defined_rule_cannot_bypass_contract_by_using_knowledge_nature():
    manifest=minimal_manifest([
        {"id":"r","family":"rules","kind":"rule","nature":"knowledge","state":"defined","value":{"statement":"No cheap","obligation":"prohibit","enforcement":"block","validationMode":"semantic","checks":[],"condition":{},"requirement":{},"references":[]},"scope":{},"sourceRefs":[]}
    ])
    errors=validate_manifest(manifest,verify_hash=False)
    assert any("valueContractRef" in error for error in errors)


def test_h2_unsupported_declared_profile_fails_closed():
    manifest,_=load_simple(); manifest["profiles"].append("obds-governed-records")
    approve(manifest)
    errors=validate_manifest(manifest)
    assert any("unsupported declared Brand Profile" in error for error in errors)


def test_h3_patch_rejects_same_shape_value_change():
    old,_=load_simple(); new=copy.deepcopy(old)
    new["version"]="1.0.1"
    elem=next(e for e in new["elements"] if e.get("state")=="defined" and e.get("nature")=="knowledge")
    elem["value"] = str(elem["value"]) + " changed"
    report=manifest_change_report(old,new)
    assert report["compatibility"]["patchEligible"] is False
    assert validate_manifest_version_transition(old,new)


def test_h3_measurement_min_greater_than_max_fails():
    sys.path.insert(0,str(ROOT/"design-space"))
    import design_space_ref as ds
    with pytest.raises(ValueError,match="min exceeds max"):
        ds.resolve_measurement({"mode":"absolute","amount":15,"unit":"px","min":{"amount":20,"unit":"px"},"max":{"amount":10,"unit":"px"}})


def test_h3_never_omit_role_must_exist_in_geometry():
    sys.path.insert(0,str(ROOT/"design-space"))
    import design_space_ref as ds
    record={"objects":[{"objectId":"headline","roles":["headline"],"box":{"x":0,"y":0,"width":10,"height":10}}]}
    with pytest.raises(ValueError,match="brand-logo"):
        ds.validate_never_omit_presence(record,{"neverOmit":["brand-logo"],"omitOrder":[]})


def test_permit_is_the_only_foundation_permission_obligation():
    schema=json.loads((VALUE_SCHEMAS/"rule.schema.json").read_text())
    value={"statement":"May use","obligation":"permit","enforcement":"inform","validationMode":"human","checks":[],"condition":{},"requirement":{},"references":[]}
    jsonschema.validate(value,schema)
    value["obligation"]="allow"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(value,schema)


def test_scope_scalars_are_strings_only():
    manifest=minimal_manifest([
        {"id":"x","family":"identity","kind":"guidance","nature":"knowledge","state":"defined","value":"x","scope":{"markets":[False]},"sourceRefs":[]}
    ])
    errors=validate_manifest(manifest,verify_hash=False)
    assert any("scope.markets values must be non-empty strings" in e for e in errors)


def test_rc5_context_delivery_uses_foundation_canonical_bytes():
    import importlib.util
    delivery_path=ROOT/"context-delivery"/"canonical.py"
    spec=importlib.util.spec_from_file_location("delivery_canonical_rc5",delivery_path)
    delivery=importlib.util.module_from_spec(spec); spec.loader.exec_module(delivery)
    payload={"n":0.1,"k":"e\u0301","\ue000":1,"😀":2}
    assert delivery.canonical_json_bytes(payload)==canonical_json_bytes(payload)


def test_rc5_all_public_canonical_copies_are_byte_identical():
    paths=[
        ROOT/"foundation"/"src"/"obds_ref"/"canonical.py",
        ROOT/"context-assembly"/"canonical.py",
        ROOT/"context-delivery"/"canonical.py",
    ]
    contents=[p.read_bytes() for p in paths]
    assert contents[0]==contents[1]==contents[2]


def test_rc5_canonical_boundary_numbers_and_astral_key_order_match_js():
    vector_path=Path(__file__).with_name("canonical-vectors.json")
    raws=json.loads(vector_path.read_text())
    py=[canonical_json_bytes(json.loads(raw)).decode() for raw in raws]
    proc=subprocess.run(
        ["node",str(Path(__file__).with_name("canonical_js.mjs")),str(vector_path)],
        text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,
    )
    assert py==proc.stdout.strip().splitlines()
    assert canonical_json_bytes({"n":1e20})==b'{"n":100000000000000000000}'
    assert canonical_json_bytes({"n":1e21})==b'{"n":1e+21}'


def test_rc5_unrepresentable_python_integer_is_rejected():
    with pytest.raises(ValueError,match="not exactly representable"):
        canonical_json_bytes({"n":9007199254740993})


def test_rc5_unsupported_tokenizer_fails_closed():
    manifest,plan=load_simple()
    plan["tokenizer"]={"id":"openai:o200k","version":"1"}
    errors=__import__("obds_ref.compiler",fromlist=["validate_plan"]).validate_plan(plan)
    assert any("unsupported tokenizer" in e for e in errors)


def test_rc5_legacy_colour_hex_schema_is_reference_internal():
    schema=json.loads((ROOT/"foundation"/"value-schemas"/"colour-hex.schema.json").read_text())
    assert "/reference/1.0.0/" in schema["$id"]
    index=json.loads((PACKAGE_ROOT/"OBDS-1.1.0-SCHEMA-INDEX.json").read_text())
    assert all(item["file"]!="colour-hex.schema.json" for item in index.get("valueSchemas",[]))


def test_rc5_cross_language_canonical_fuzz_256_binary64_values(tmp_path):
    import math, random, struct
    rng=random.Random(20260827)
    raws=[]
    while len(raws)<256:
        bits=rng.getrandbits(64)
        value=struct.unpack('>d',bits.to_bytes(8,'big'))[0]
        if not math.isfinite(value):
            continue
        raws.append(json.dumps({"n":value},separators=(",",":"),allow_nan=False))
    vector_path=tmp_path/'fuzz.json'
    vector_path.write_text(json.dumps(raws),encoding='utf-8')
    py=[canonical_json_bytes(json.loads(raw)).decode() for raw in raws]
    proc=subprocess.run(
        ["node",str(Path(__file__).with_name("canonical_js.mjs")),str(vector_path)],
        text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,
    )
    assert py==proc.stdout.strip().splitlines()
