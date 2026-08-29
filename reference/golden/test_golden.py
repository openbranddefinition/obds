from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import re
import sys

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[2]
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
SCHEMAS = _schema_dir(ROOT, "schemas")
VALUE_SCHEMAS = _schema_dir(ROOT, "value-schemas")
SPEC = (ROOT / "OBDS-1.0.3.md").read_text(encoding="utf-8")

FOUNDATION_SRC = ROOT / "reference" / "foundation" / "src"
CA_ROOT = ROOT / "reference" / "context-assembly"
sys.path.insert(0, str(FOUNDATION_SRC))
sys.path.insert(0, str(CA_ROOT))

from obds_ref.compiler import (
    build_target,
    validate_manifest,
    validate_plan,
    validate_plan_against_manifest,
    VALID_STATES,
)
from obds_ref.runtime import DECISIONS, run_assembled_with_model


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_module("golden_build_views", CA_ROOT / "build_views.py")
assembler = load_module("golden_assemble", CA_ROOT / "assemble_context.py")
reviewer = load_module("golden_review", CA_ROOT / "validate_review.py")
canonical = load_module("golden_canonical", CA_ROOT / "canonical.py")


def schema(name: str):
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def test_golden_manifest_to_runtime_decision():
    examples = CA_ROOT / "examples"
    manifest = yaml.safe_load((examples / "manifest.yaml").read_text(encoding="utf-8"))
    plan = yaml.safe_load((examples / "build-plan.yaml").read_text(encoding="utf-8"))
    request = yaml.safe_load((examples / "assembly-request-review.yaml").read_text(encoding="utf-8"))
    chapter_map = yaml.safe_load((examples / "chapter-map.yaml").read_text(encoding="utf-8"))

    assert validate_manifest(manifest) == []
    assert validate_plan(plan) == []
    assert validate_plan_against_manifest(plan, manifest) == []

    target = next(item for item in plan["targets"] if item["id"] == request["targetId"])
    result = build_target(manifest, plan, target)
    assert result.status == "ready"
    compiled = result.artefact
    jsonschema.validate(compiled, schema("compiled-context.schema.json"))

    search_index, chapter_set = builder.build_views(manifest, chapter_map)
    package, model_input = assembler.assemble(compiled, search_index, chapter_set, request)
    jsonschema.validate(package, schema("model-input-package.schema.json"))
    assert package["sources"]["compiledContextHash"] == compiled["artifactHash"]

    review = {
        "kind": "obds-review-result",
        "schemaVersion": "1.0.0",
        "targetId": package["targetId"],
        "applicationMode": "review",
        "modelInputHash": package["modelInputHash"],
        "decision": "pass_with_suggestions",
        "findings": [
            {
                "id": "golden-opportunity",
                "category": "opportunity",
                "elementIds": ["identity.value.simplicity"],
                "message": "The line could express the active simplicity guidance more directly.",
            }
        ],
    }
    review["reviewHash"] = canonical.sha256_id(review)
    jsonschema.validate(review, schema("review-result.schema.json"))
    assert reviewer.validate_review(compiled, package, review) is True

    record = run_assembled_with_model(
        compiled,
        package,
        model_input,
        task_input=request["taskInput"],
        model=lambda prompt: ("Useful and simple.", "golden-request-1"),
        provider="golden",
        model_id="deterministic-stub",
    )
    assert record["decision"] == "released"
    assert record["assemblyHash"] == package["assemblyHash"]
    assert record["modelInputHash"] == package["modelInputHash"]
    persisted = {key: value for key, value in record.items() if key != "output"}
    jsonschema.validate(persisted, schema("runtime-decision-record.schema.json"))


def test_tampered_assembly_fails_before_model_call():
    examples = CA_ROOT / "examples"
    compiled = json.loads((examples / "compiled-marketing-review-global-en.json").read_text(encoding="utf-8"))
    package = json.loads((examples / "model-input-review.json").read_text(encoding="utf-8"))
    model_input = "tampered"
    calls = []
    record = run_assembled_with_model(
        compiled,
        package,
        model_input,
        task_input="Review this.",
        model=lambda prompt: calls.append(prompt) or "never",
    )
    assert record["decision"] == "assembly_failed"
    assert record["modelCall"]["called"] is False
    assert calls == []


def test_normative_state_and_runtime_decision_enums_are_synchronised():
    manifest_schema = schema("brand-manifest.schema.json")
    schema_states = set(manifest_schema["$defs"]["element"]["properties"]["state"]["enum"])
    assert schema_states == VALID_STATES == {"defined", "unknown", "not_defined", "not_applicable"}

    state_section = SPEC.split("### 8.1 What each state means", 1)[1].split("### 8.2", 1)[0]
    spec_states = set(re.findall(r"^\| `([a-z_]+)` \|", state_section, flags=re.MULTILINE))
    assert spec_states == schema_states

    runtime_schema = schema("runtime-decision-record.schema.json")
    schema_decisions = set(runtime_schema["properties"]["decision"]["enum"])
    assert schema_decisions == DECISIONS

    line = re.search(r"Allowed decisions are (.+?)\.", SPEC)
    assert line
    spec_decisions = set(re.findall(r"`([a-z_]+)`", line.group(1)))
    assert spec_decisions == schema_decisions


def test_context_assembly_and_review_enums_are_synchronised():
    request_schema = schema("assembly-request.schema.json")
    package_schema = schema("model-input-package.schema.json")
    review_schema = schema("review-result.schema.json")

    request_delivery = set(request_schema["properties"]["deliveryMode"]["enum"])
    package_delivery = set(package_schema["properties"]["deliveryMode"]["enum"])
    assert request_delivery == package_delivery == assembler.DELIVERY_MODES

    request_app = set(request_schema["properties"]["applicationMode"]["enum"])
    package_app = set(package_schema["properties"]["applicationMode"]["enum"])
    assert request_app == package_app == assembler.APPLICATION_MODES

    request_truth = set(request_schema["properties"]["retrieval"]["properties"]["truthOutcome"]["enum"])
    package_truth = set(package_schema["properties"]["retrieval"]["properties"]["truthOutcome"]["enum"])
    assert request_truth == package_truth == assembler.TRUTH_OUTCOMES

    categories = set(review_schema["properties"]["findings"]["items"]["properties"]["category"]["enum"])
    decisions = set(review_schema["properties"]["decision"]["enum"])
    assert categories == reviewer.FINDING_CATEGORIES
    assert decisions == reviewer.REVIEW_DECISIONS


def test_prohibition_has_one_brand_truth_path():
    manifest_schema = schema("brand-manifest.schema.json")
    states = manifest_schema["$defs"]["element"]["properties"]["state"]["enum"]
    assert "prohibited" not in states
    assert "state: prohibited" in SPEC
    assert "is not part of OBDS 1.0 Brand States" in SPEC
    rule_schema = json.loads((VALUE_SCHEMAS / "rule.schema.json").read_text(encoding="utf-8"))
    assert "prohibit" in rule_schema["properties"]["obligation"]["enum"]


def test_semantic_boundary_is_structured_but_not_a_rule():
    boundary_schema = json.loads((VALUE_SCHEMAS / "semantic-boundary.schema.json").read_text(encoding="utf-8"))
    payload = {
        "subject": "photography",
        "quality": "authentic",
        "is": ["observed", "believable", "lived_in"],
        "isNot": ["staged", "glossy", "sterile"],
        "tieBreaker": {"prefer": "believable", "over": "polished"},
    }
    jsonschema.validate(payload, boundary_schema)
    assert "only a separate applicable RULE" in SPEC
