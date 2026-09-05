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

# Section 28.1: a test that produces or blesses published evidence is a governed
# reader like any other. Reading the corpus with PyYAML defaults made this suite
# one of the divergent contracts in the release.
governed = module("governed_io_test", "governed_io.py")


def load_yaml(name):
    return governed.load_data(ROOT / "examples" / name)


def load_governed(name):
    return governed.load_data(ROOT / "examples" / name)


def setup(target_id="social-copy-global-en"):
    manifest = load_yaml("manifest.yaml")
    chapter_map = load_yaml("chapter-map.yaml")
    index, chapters = builder.build_views(manifest, chapter_map)
    compiled = load_governed(f"compiled-{target_id}.json")
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
    # F3: retrieval classifications remain metadata, not invented brand states.
    assert "runtime.coverage" not in package["slots"]["stateMap"]


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
    review = load_governed("review-result-blocking.json")
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
        payload = load_governed(name)
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
        payload = load_governed(name)
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
        payload = load_governed(f"compiled-{target_id}.json")
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


def test_canonically_equivalent_identities_are_accepted_1_1_6():
    """Section 8.0a: a compiled context is indexed on canonical identity.

    The compiler emits canonical ids in availableElementIds while
    elementRecords keeps the approved spelling, so indexing the records by their
    raw id rejected a valid artefact whose ids were not already NFC. That made a
    1.1.6 artefact unusable by the same release's Context Assembly.
    """
    import copy

    manifest, compiled, index, chapters = setup()
    compiled = copy.deepcopy(compiled)
    record = copy.deepcopy(compiled["elementRecords"][0])
    raw_id = "context.cafe\u0301"
    record["id"] = raw_id
    record["subject"] = raw_id
    compiled["elementRecords"].append(record)
    compiled["availableElementIds"] = sorted(
        compiled["availableElementIds"] + ["context.caf\u00e9"]
    )
    compiled.pop("artifactHash", None)
    compiled["artifactHash"] = canonical.artefact_hash(compiled)

    policy, by_id = assembler._validate_compiled_context(
        compiled,
        {"targetId": compiled["targetId"],
         "deliveryMode": compiled["contextAssembly"]["deliveryMode"],
         "applicationMode": compiled["contextAssembly"]["applicationMode"]},
    )

    assert "context.caf\u00e9" in by_id
    assert by_id["context.caf\u00e9"]["id"] == raw_id, "the approved spelling is preserved"


def test_build_views_accepts_a_canonically_equivalent_identity_1_1_6():
    """Section 8.0a: a valid NFD identity must not crash the view builders.

    The chapter index was keyed on the canonical identity and then queried with
    the stored spelling, so a manifest that validate_manifest() accepts raised
    KeyError in both build_views copies.
    """
    import copy

    manifest = load_yaml("manifest.yaml")
    template = copy.deepcopy(manifest["elements"][0])
    element = copy.deepcopy(template)
    element["id"] = "structure.cafe\u0301"
    element["subject"] = "structure.cafe\u0301"
    manifest["elements"].append(element)
    # Section 7: a derived view publishes `approval.contentHash` as its claim of
    # binding to an approved manifest, so the builder refuses a manifest that
    # does not reproduce it. This test is about NFD identities, not about
    # approval drift, so it presents a properly sealed manifest.
    manifest["approval"]["contentHash"] = canonical.manifest_content_hash(manifest)

    index, chapters = builder.build_views(manifest)

    cards = [card for card in index["cards"] if card["elementId"] == "structure.caf\u00e9"]
    assert len(cards) == 1, [card["elementId"] for card in index["cards"]]
    assert cards[0]["chapterRefs"], "the card must be reachable from its chapter"


def test_review_references_resolve_across_normalisation_forms_1_1_6():
    """A review naming an element in the other form is not an unknown element."""
    import copy

    manifest, compiled, index, chapters = setup()
    compiled = copy.deepcopy(compiled)
    record = copy.deepcopy(next(e for e in compiled["elementRecords"] if e["id"] == "identity.value.simplicity"))
    record["id"] = "context.cafe\u0301"
    record["subject"] = "context.cafe\u0301"
    compiled["elementRecords"].append(record)
    compiled["availableElementIds"] = sorted(
        compiled["availableElementIds"] + ["context.caf\u00e9"]
    )
    # A Review Result is a review-mode document by contract, so the context it
    # is derived from has to permit that mode.
    compiled["contextAssembly"] = {**compiled["contextAssembly"], "applicationMode": "review", "eligibleGuidanceIds": compiled["contextAssembly"]["eligibleGuidanceIds"] + ["context.café"]}
    compiled.pop("artifactHash", None)
    compiled["artifactHash"] = canonical.artefact_hash(compiled)

    # 3.0.0 executes all three published contracts and binds their identities, so
    # the package and the review have to be a package and a review — not the two
    # hand-built fragments this test used to pass in. They are derived from the
    # shipped examples and rebound to this compiled context; the subject of the
    # test, identity normalisation in review references, is unchanged.
    renderer = module("model_input_review_test", "model_input.py")
    package = governed.load_data(ROOT / "examples" / "model-input-review.json")
    package["manifest"] = copy.deepcopy(compiled["manifest"])
    package["targetId"] = compiled["targetId"]
    package["deliveryMode"] = compiled["contextAssembly"]["deliveryMode"]
    package["applicationMode"] = compiled["contextAssembly"]["applicationMode"]
    package["sources"] = {**package["sources"], "compiledContextHash": compiled["artifactHash"]}
    package["selection"] = {
        **package["selection"],
        "activeGuidanceElementIds": ["context.caf\u0065\u0301"],
    }
    from projection import derive_projection
    slots, selection = derive_projection(compiled, package["selection"], package["projection"],
        delivery_mode=package["deliveryMode"], application_mode=package["applicationMode"])
    slots["taskInput"] = package["slots"]["taskInput"]
    package["slots"], package["selection"] = slots, selection
    package["modelInputHash"] = canonical.text_hash(renderer.render_model_input(package["slots"]))
    package["assemblyHash"] = canonical.sha256_id(
        {key: value for key, value in package.items() if key != "assemblyHash"}
    )

    review = governed.load_data(ROOT / "examples" / "review-result-valid.json")
    review["targetId"] = compiled["targetId"]
    review["applicationMode"] = package["applicationMode"]
    review["modelInputHash"] = package["modelInputHash"]
    review["decision"] = "pass"
    review["findings"] = [
        {
            "id": "finding-1",
            "category": "opportunity",
            "elementIds": ["context.cafe\u0301"],
            "message": "The other normalisation form names the same element.",
        }
    ]
    review["reviewHash"] = canonical.sha256_id(
        {key: value for key, value in review.items() if key != "reviewHash"}
    )

    assert reviewer.validate_review(compiled, package, review) is True

    review["reviewHash"] = canonical.sha256_id(
        {key: value for key, value in review.items() if key != "reviewHash"}
    )

    assert reviewer.validate_review(compiled, package, review) is True


def test_assembly_order_follows_the_canonical_identity_1_1_6():
    """Section 8.0a: two spellings of one identity assemble identically.

    The fact, gap and guidance slots were sorted on the stored spelling, so two
    compiled contexts carrying the same governed truth assembled into a
    different order and produced a different modelInputHash.

    The pair is chosen so the order actually flips. Against `design.caff`, the
    composed form `design.caf\u00e9` sorts after it, because U+00E9 is above
    `f`; the decomposed form `design.cafe\u0301` sorts before it, because `e`
    is below `f`. Canonical ordering has to pick one, and both spellings have to
    agree on it.
    """
    import copy

    NFC_ID = "design.caf\u00e9"
    NFD_ID = "design.cafe\u0301"
    NEIGHBOUR = "design.caff"

    def package_for(stored_id):
        manifest, compiled, index, chapters = setup()
        compiled = copy.deepcopy(compiled)
        renamed = next(
            record for record in compiled["elementRecords"]
            if record["id"] == "structure.brand"
        )
        renamed["id"] = stored_id
        renamed["subject"] = stored_id
        neighbour = copy.deepcopy(renamed)
        neighbour["id"] = NEIGHBOUR
        neighbour["subject"] = NEIGHBOUR
        neighbour["value"] = {"name": "Neighbour"}
        compiled["elementRecords"].append(neighbour)
        compiled["availableElementIds"] = sorted(
            [item for item in compiled["availableElementIds"] if item != "structure.brand"]
            + [NFC_ID, NEIGHBOUR]
        )
        compiled["includedElementIds"] = sorted([
            NFC_ID if item == "structure.brand" else item for item in compiled["includedElementIds"]
        ] + [NEIGHBOUR])
        compiled.pop("artifactHash", None)
        compiled["artifactHash"] = canonical.artefact_hash(compiled)

        request = load_yaml("assembly-request-create.yaml")
        request["selection"]["factElementIds"] = [
            NFC_ID if item == "structure.brand" else item
            for item in request["selection"]["factElementIds"]
        ] + [NEIGHBOUR]
        package, _ = assembler.assemble(compiled, index, chapters, request)
        return package

    nfd_package = package_for(NFD_ID)
    nfc_package = package_for(NFC_ID)

    assert nfd_package["selection"]["factElementIds"] == nfc_package["selection"]["factElementIds"]
    assert nfd_package["slots"] == nfc_package["slots"]
    assert nfd_package["modelInputHash"] == nfc_package["modelInputHash"]


def test_gap_and_guidance_text_is_ordered_before_it_is_rendered_1_1_6():
    """Section 8.0a: the slot text and the emitted arrays must agree.

    The canonical sorts ran after the stateMap and guidanceContext text had been
    built, so the emitted id arrays looked correctly ordered while the rendered
    text still carried the request's selection order, and modelInputHash moved
    with it.
    """
    import copy

    def package_for(order):
        manifest, compiled, index, chapters = setup("marketing-review-global-en")
        request = load_yaml("assembly-request-review.yaml")
        request["selection"]["activeGuidanceElementIds"] = list(order)
        package, _ = assembler.assemble(compiled, index, chapters, request)
        return package

    forward = package_for(["identity.value.simplicity", "identity.value.reliability"])
    reverse = package_for(["identity.value.reliability", "identity.value.simplicity"])

    assert forward["selection"]["activeGuidanceElementIds"] == reverse["selection"]["activeGuidanceElementIds"]
    assert forward["slots"] == reverse["slots"]
    assert forward["modelInputHash"] == reverse["modelInputHash"]


def test_target_id_and_resolution_manifest_compare_on_the_canonical_identity_1_1_6():
    """Section 8.0a: an identity is an identity wherever it is compared."""
    import copy

    manifest, compiled, index, chapters = setup()
    compiled = copy.deepcopy(compiled)
    compiled["targetId"] = "social-copy-global-en-caf\u0065\u0301"
    compiled.pop("artifactHash", None)
    compiled["artifactHash"] = canonical.artefact_hash(compiled)

    policy, by_id = assembler._validate_compiled_context(
        compiled,
        {"targetId": "social-copy-global-en-caf\u00e9",
         "deliveryMode": compiled["contextAssembly"]["deliveryMode"],
         "applicationMode": compiled["contextAssembly"]["applicationMode"]},
    )
    assert by_id, "the compiled context must be accepted across normalisation forms"


def test_resolution_manifest_id_compares_on_the_canonical_identity_1_1_6():
    """Section 8.0a: the manifest_checked resolution path is an identity check.

    The earlier test named this path but exercised only targetId, so reverting
    the resolution-manifest comparison to raw equality still passed.
    """
    import copy

    manifest, compiled, index, chapters = setup()

    # The snapshot is a real manifest, sealed, in the decomposed spelling. A stub
    # carrying only id/version/approval no longer passes this path: section 7
    # requires the snapshot to reproduce the hash it claims, because comparing
    # the declared value alone only proves the snapshot *says* the right thing.
    resolution_manifest = copy.deepcopy(manifest)
    resolution_manifest["id"] = "urn:obds:brand:cafe\u0301"
    resolution_manifest["approval"] = dict(resolution_manifest.get("approval") or {})
    resolution_manifest["approval"]["contentHash"] = canonical.manifest_content_hash(
        resolution_manifest
    )

    compiled = copy.deepcopy(compiled)
    compiled["manifest"] = dict(compiled["manifest"])
    compiled["manifest"]["id"] = "urn:obds:brand:caf\u00e9"
    compiled["manifest"]["contentHash"] = resolution_manifest["approval"]["contentHash"]
    compiled.pop("artifactHash", None)
    compiled["artifactHash"] = canonical.artefact_hash(compiled)

    assembler._validate_resolution_manifest(
        compiled,
        {"resolution": "manifest_checked"},
        resolution_manifest,
    )


def test_model_facing_references_render_the_canonical_identity_1_1_6():
    """Two canonically equivalent rules must render identically, not just hash so.

    text_hash normalises, so a raw rendered reference produced different model
    input text under an identical modelInputHash: the hash asserted an identity
    the bytes did not have.
    """
    import copy

    def rendered(reference):
        element = {
            "id": "rule.example",
            "state": "defined",
            "family": "rules",
            "value": {
                "statement": "Example.",
                "obligation": "require",
                "enforcement": "inform",
                "references": [reference],
                "checks": [{
                    "primitive": "literal_required",
                    "params": {"elementValueRef": {"elementId": reference, "path": "text"}},
                }],
            },
        }
        return assembler.render_rule_for_model(element)

    assert rendered("context.cafe\u0301") == rendered("context.caf\u00e9")


def test_an_applicable_prohibition_reaches_the_model_input_1_1_6():
    """Sections 14.1 and 15.4: a prohibition is a hard boundary whatever its
    enforcement.

    Context Assembly rebuilt the hard boundaries from the element records using
    the enforcement filter alone, so an applicable `obligation: prohibit` RULE
    with advisory enforcement was dropped from the model input even though the
    compiler had put it in the slot.
    """
    import copy

    manifest, compiled, index, chapters = setup()
    compiled = copy.deepcopy(compiled)
    rule = copy.deepcopy(next(
        record for record in compiled["elementRecords"]
        if record.get("family") == "rules" and record.get("state") == "defined"
    ))
    rule["id"] = "rules.advisory-prohibition"
    rule["subject"] = "rules.advisory-prohibition"
    rule["value"] = dict(rule["value"])
    rule["value"]["obligation"] = "prohibit"
    rule["value"]["enforcement"] = "inform"
    rule["value"]["checks"] = []
    compiled["elementRecords"].append(rule)
    compiled["availableElementIds"] = sorted(
        compiled["availableElementIds"] + ["rules.advisory-prohibition"]
    )
    compiled.pop("artifactHash", None)
    compiled["artifactHash"] = canonical.artefact_hash(compiled)

    request = load_yaml("assembly-request-create.yaml")
    package, text = assembler.assemble(compiled, index, chapters, request)

    assert "rules.advisory-prohibition" in package["selection"]["hardBoundaryElementIds"]
    assert "rules.advisory-prohibition" in package["slots"]["hardBoundaries"]
    assert "rules.advisory-prohibition" in text
