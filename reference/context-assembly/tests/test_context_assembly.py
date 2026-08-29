from pathlib import Path
import importlib.util
import json
import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


builder = module("builder_test", "build_views.py")
assembler = module("assembler_test", "assemble_context.py")
reviewer = module("reviewer_test", "validate_review.py")
canonical = module("canonical_test", "canonical.py")


def load_yaml(name):
    return yaml.safe_load((ROOT / "examples" / name).read_text(encoding="utf-8"))


def setup(target_id="social-copy-global-en"):
    manifest = load_yaml("manifest.yaml")
    chapter_map = load_yaml("chapter-map.yaml")
    index, chapters = builder.build_views(manifest, chapter_map)
    compiled = json.loads(
        (ROOT / "examples" / f"compiled-{target_id}.json").read_text(encoding="utf-8")
    )
    return manifest, compiled, index, chapters


def test_ready_assembly_is_deterministic_except_volatile_fields():
    manifest, compiled, index, chapters = setup()
    request = load_yaml("assembly-request-create.yaml")
    first, first_text = assembler.assemble(compiled, index, chapters, request)
    second, second_text = assembler.assemble(compiled, index, chapters, request)

    assert first_text == second_text
    assert first["modelInputHash"] == second["modelInputHash"]
    assert first["slots"] == second["slots"]
    assert first["selection"] == second["selection"]


def test_all_hard_boundaries_are_included():
    manifest, compiled, index, chapters = setup()
    request = load_yaml("assembly-request-create.yaml")
    package, _ = assembler.assemble(compiled, index, chapters, request)
    assert package["selection"]["hardBoundaryElementIds"] == [
        "rule.claims.require-approval",
        "rule.logo.clear-zone",
    ]
    assert "rule.logo.clear-zone" in package["slots"]["hardBoundaries"]
    assert "rule.claims.require-approval" in package["slots"]["hardBoundaries"]


def test_search_cards_are_audit_only_not_a_model_slot():
    manifest, compiled, index, chapters = setup()
    request = load_yaml("assembly-request-create.yaml")
    package, model_input = assembler.assemble(compiled, index, chapters, request)

    assert package["selection"]["searchCardIds"]
    assert "[SEARCH_CARD" not in model_input
    for card_id in package["selection"]["searchCardIds"]:
        assert card_id not in model_input


def test_selective_expression_only_activates_selected_guidance():
    manifest, compiled, index, chapters = setup()
    request = load_yaml("assembly-request-create.yaml")
    package, _ = assembler.assemble(compiled, index, chapters, request)

    assert package["selection"]["activeGuidanceElementIds"] == [
        "identity.value.simplicity"
    ]
    active_section = package["slots"]["guidanceContext"].split(
        "[REASONING_CHAPTERS]"
    )[0]
    assert "identity.value.simplicity" in active_section
    assert "identity.value.innovation" not in active_section
    assert "identity.value.reliability" not in active_section
    assert "Only elements listed under ACTIVE_GUIDANCE" in package["slots"]["guidanceContext"]


def test_unresolved_no_hit_fails():
    manifest, compiled, index, chapters = setup("brand-query-global-en")
    request = load_yaml("assembly-request-unresolved.yaml")
    try:
        assembler.assemble(compiled, index, chapters, request)
    except ValueError as error:
        assert "retrieval silence unresolved" in str(error)
    else:
        raise AssertionError("expected no-hit failure")


def test_manifest_checked_not_covered_is_explicit():
    manifest, compiled, index, chapters = setup("brand-query-global-en")
    request = load_yaml("assembly-request-not-covered.yaml")
    package, _ = assembler.assemble(
        compiled, index, chapters, request, resolution_manifest=manifest
    )
    assert package["retrieval"]["truthOutcome"] == "not_covered"
    assert "does not imply permission or prohibition" in package["slots"]["stateMap"]


def test_opportunity_must_reference_active_guidance():
    manifest, compiled, index, chapters = setup("marketing-review-global-en")
    request = load_yaml("assembly-request-review.yaml")
    package, _ = assembler.assemble(compiled, index, chapters, request)

    review = {
        "kind": "obds-review-result",
        "schemaVersion": "1.0.0",
        "targetId": package["targetId"],
        "applicationMode": "review",
        "modelInputHash": package["modelInputHash"],
        "decision": "pass_with_suggestions",
        "findings": [{
            "id": "bad",
            "category": "opportunity",
            "elementIds": ["identity.value.innovation"],
            "message": "Innovation is missing.",
        }],
    }
    review["reviewHash"] = canonical.sha256_id(review)

    try:
        reviewer.validate_review(compiled, package, review)
    except ValueError as error:
        assert "active guidance only" in str(error)
    else:
        raise AssertionError("expected inactive-guidance failure")


def test_fail_requires_explicit_blocking_rule():
    manifest, compiled, index, chapters = setup("marketing-review-global-en")
    request = load_yaml("assembly-request-review.yaml")
    package, _ = assembler.assemble(compiled, index, chapters, request)

    invalid = {
        "kind": "obds-review-result",
        "schemaVersion": "1.0.0",
        "targetId": package["targetId"],
        "applicationMode": "review",
        "modelInputHash": package["modelInputHash"],
        "decision": "fail",
        "findings": [{
            "id": "bad-fail",
            "category": "material_conflict",
            "elementIds": ["identity.value.simplicity"],
            "message": "The text is complex.",
        }],
    }
    invalid["reviewHash"] = canonical.sha256_id(invalid)

    try:
        reviewer.validate_review(compiled, package, invalid)
    except ValueError as error:
        assert "blocking RULE violation" in str(error)
    else:
        raise AssertionError("expected rule-required failure")


def test_valid_rule_violation_can_fail():
    manifest, compiled, index, chapters = setup("marketing-review-global-en")
    request = load_yaml("assembly-request-review.yaml")
    package, _ = assembler.assemble(compiled, index, chapters, request)
    review = json.loads(
        (ROOT / "examples" / "review-result-blocking.json").read_text(encoding="utf-8")
    )
    assert reviewer.validate_review(compiled, package, review) is True


def test_schemas_validate_reference_outputs():
    model_schema = json.loads(
        (ROOT / "schemas" / "model-input-package.schema.json").read_text(encoding="utf-8")
    )
    request_schema = json.loads(
        (ROOT / "schemas" / "assembly-request.schema.json").read_text(encoding="utf-8")
    )
    review_schema = json.loads(
        (ROOT / "schemas" / "review-result.schema.json").read_text(encoding="utf-8")
    )

    for name in [
        "model-input-create.json",
        "model-input-review.json",
        "model-input-not-covered.json",
    ]:
        payload = json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))
        jsonschema.validate(payload, model_schema)

    for name in [
        "assembly-request-create.yaml",
        "assembly-request-review.yaml",
        "assembly-request-not-covered.yaml",
    ]:
        jsonschema.validate(load_yaml(name), request_schema)

    for name in [
        "review-result-valid.json",
        "review-result-blocking.json",
    ]:
        payload = json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))
        jsonschema.validate(payload, review_schema)


def test_model_input_binds_exact_compiled_context():
    manifest, compiled, index, chapters = setup()
    request = load_yaml("assembly-request-create.yaml")
    package, _ = assembler.assemble(compiled, index, chapters, request)
    assert package["sources"]["compiledContextHash"] == compiled["artifactHash"]
    assert package["sources"]["compiledContextHash"] is not None


def test_normal_assembly_rejects_manifest_access():
    manifest, compiled, index, chapters = setup()
    request = load_yaml("assembly-request-create.yaml")
    try:
        assembler.assemble(
            compiled, index, chapters, request, resolution_manifest=manifest
        )
    except ValueError as error:
        assert "manifest access is allowed only" in str(error)
    else:
        raise AssertionError("expected normal-path manifest access rejection")


def test_compiled_context_schema_validates_fixtures():
    schema = json.loads(
        (ROOT.parent / "foundation" / "schemas" / "compiled-context.schema.json").read_text(encoding="utf-8")
    )
    for target_id in [
        "social-copy-global-en",
        "marketing-review-global-en",
        "brand-query-global-en",
    ]:
        payload = json.loads(
            (ROOT / "examples" / f"compiled-{target_id}.json").read_text(encoding="utf-8")
        )
        jsonschema.validate(payload, schema)


def test_rc5_assembly_rejects_unsupported_compiled_tokenizer():
    manifest, compiled, index, chapters = setup()
    compiled = json.loads(json.dumps(compiled))
    compiled["tokenBudget"]["tokenizerId"] = "openai:o200k"
    # Hash must be internally consistent so failure is tokenizer support, not hash mismatch.
    compiled["artifactHash"] = assembler.artifact_hash(compiled)
    request = load_yaml("assembly-request-create.yaml")
    try:
        assembler.assemble(compiled,index,chapters,request)
    except ValueError as error:
        assert "unsupported tokenizer" in str(error)
    else:
        raise AssertionError("expected unsupported-tokenizer failure")


def test_rc5_model_projection_omits_validator_plumbing_and_duplicate_exact_chapter_blocks():
    manifest, compiled, index, chapters = setup()
    request = load_yaml("assembly-request-create.yaml")
    package, model_input = assembler.assemble(compiled,index,chapters,request)
    hard = package["slots"]["hardBoundaries"]
    assert "validatorRef" not in hard
    assert '"condition":{}' not in hard
    assert "rule.logo.clear-zone [require/block]" in hard
    # Exact clear-zone fact and rule are already in exact slots and must not be duplicated in reasoning chapter text.
    guidance = package["slots"]["guidanceContext"]
    assert guidance.count("design.logo.clear-zone") == 0
    assert guidance.count("rule.logo.clear-zone") == 0
