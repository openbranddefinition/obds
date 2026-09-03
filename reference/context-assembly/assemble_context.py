from __future__ import annotations

from datetime import datetime, timezone
import copy
import json
import re
import uuid

from pathlib import Path

from canonical import (compiled_context_identity_positions, identity_admissibility_errors,
                       identity_key, manifest_content_hash,
                       model_input_package_identity_positions, sha256_id, text_hash)
from governed_io import load_data as _load_governed



DELIVERY_MODES = {"lookup", "reasoning", "full"}
APPLICATION_MODES = {"create", "review", "compliance"}
RETRIEVAL_STATUSES = {"hit", "partial", "no_match", "low_confidence", "access_filtered"}
RESOLUTION_MODES = {"direct", "widened", "manifest_checked", "unresolved"}
SUPPORTED_TOKENIZERS = {("obds:whitespace-v1", "1.0.0")}

TRUTH_OUTCOMES = {
    "defined", "unknown", "not_defined", "not_applicable", "prohibited",
    "not_covered", "access_limited", "mixed", "unresolved"
}

# Section 15.10: one renderer, shared with the runtime, so the runtime can
# reproduce exactly these bytes from the package it verified.
from model_input import SLOT_ORDER, render_model_input  # noqa: F401


# Section 14. Context Assembly consumes a Compiled Brand Context, so it executes
# the published contract like every other executor. It verified `artifactHash`
# and then a hand-picked set of properties, which is a summary of the contract
# rather than the contract: a correctly re-sealed artefact carrying a property
# the contract forbids was assembled from.
_HERE = Path(__file__).resolve().parent
_CONTEXT_SCHEMA_PATH = _HERE.parents[1] / "schemas" / "3.0.0" / "compiled-context.schema.json"
_PACKAGE_SCHEMA_PATH = _HERE / "schemas" / "model-input-package.schema.json"
_REVIEW_SCHEMA_PATH = _HERE / "schemas" / "review-result.schema.json"
_VALIDATORS = {}


def _validator_for(path):
    key = str(path)
    if key not in _VALIDATORS:
        import jsonschema

        _VALIDATORS[key] = jsonschema.Draft202012Validator(_load_governed(path))
    return _VALIDATORS[key]


def _contract_violations(document, path, what):
    if not isinstance(document, dict):
        return [f"<root>: a {what} is an object, not {type(document).__name__}"]
    return [
        ("/".join(str(part) for part in error.path) or "<root>") + ": " + error.message
        for error in sorted(_validator_for(path).iter_errors(document), key=str)
    ]


def _identity_violations(positions):
    return [
        f"inadmissible governed identity: {error}"
        for error in identity_admissibility_errors(positions)
    ]


def compiled_context_contract_errors(compiled_context):
    """Every way the published contract refuses this artefact, worst first."""
    violations = _contract_violations(
        compiled_context, _CONTEXT_SCHEMA_PATH, "Compiled Brand Context"
    )
    if violations:
        return violations
    # Section 8.0a, the same rule the runtime applies to a received artefact:
    # an identity the canonical form cannot tell apart from another one is not
    # a governable identity, wherever the artefact is consumed.
    return _identity_violations(compiled_context_identity_positions(compiled_context))


def model_input_package_contract_errors(package):
    """The published Model Input Package contract, then section 8.0a.

    Three governed documents reach Context Assembly and the runtime. Only one of
    them had its contract executed, so a package declaring another kind at
    another schema version was consumed by both.
    """
    violations = _contract_violations(package, _PACKAGE_SCHEMA_PATH, "Model Input Package")
    if violations:
        return violations
    return _identity_violations(model_input_package_identity_positions(package))


def review_result_contract_errors(review):
    """The published Review Result contract."""
    return _contract_violations(review, _REVIEW_SCHEMA_PATH, "Review Result")


def artifact_hash(artefact):
    payload = copy.deepcopy(artefact)
    payload.pop("artifactHash", None)
    return sha256_id(payload)


def _compact_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def render_element(element):
    value = element.get("value")
    if isinstance(value, str):
        rendered = value
    elif value is None:
        rendered = ""
    else:
        rendered = _compact_json(value)
    return f"{identity_key(element['id'])} [{element['state']}]: {rendered}".rstrip()


def render_rule_for_model(element):
    value = element.get("value") or {}
    prefix = f"{identity_key(element['id'])} [{value.get('obligation','?')}/{value.get('enforcement','inform')}]"
    parts = [f"{prefix}: {value.get('statement','').strip()}"]
    refs = value.get("references") or []
    if refs:
        # Section 8.0a: a reference names an identity, so the model sees the
        # canonical form. Rendering the stored spelling made two canonically
        # equivalent rules render differently while text_hash, which normalises,
        # reported the same modelInputHash for both.
        parts.append("refs=" + ",".join(identity_key(item) for item in refs))
    condition = value.get("condition") or {}
    if condition:
        parts.append("condition=" + _compact_json(condition))
    requirement = value.get("requirement") or {}
    if requirement:
        parts.append("requirement=" + _compact_json(requirement))
    checks = value.get("checks") or []
    if checks:
        compact_checks = []
        for check in checks:
            primitive = check.get("primitive", "check")
            params = dict(check.get("params") or {})
            reference = params.get("elementValueRef")
            if isinstance(reference, dict) and isinstance(reference.get("elementId"), str):
                reference = dict(reference)
                reference["elementId"] = identity_key(reference["elementId"])
                params["elementValueRef"] = reference
            compact_checks.append(primitive + "(" + _compact_json(params) + ")")
        parts.append("checks=" + ";".join(compact_checks))
    return " | ".join(parts)


def _filtered_reference_chapter_content(chapter, excluded_ids, declared_universe):
    """Section 14.3a / 10.2a seam, corrected in 3.0.0.

    Until then this filtered against `excluded_ids` only — the elements already
    rendered into another slot — and kept everything else. A block for an
    element *outside* the compiled artefact's declared universe is not in
    `excluded_ids`, so it was kept: an out-of-scope or expired element reached
    the model through a Reasoning Chapter while the compiler's own
    `availableElementIds` never named it. The filter ran the right way round for
    "already said" and the wrong way round for "may be said at all".

    A block is rendered exactly when its element is in the declared universe and
    is not already present in another slot. A chapter whose renderer this code
    does not recognise carries content it cannot attribute to elements, so it
    cannot be admitted at all.
    """
    renderer = chapter.get("renderer") or {}
    if renderer.get("id") != "org.openbranddefinition.reference-chapter-renderer":
        raise ValueError(
            "unrecognised Reasoning Chapter renderer, so its content cannot be "
            f"attributed to the compiled artefact's declared universe: {renderer.get('id')}"
        )
    blocks = re.split(r"(?m)(?=^## )", chapter.get("content", ""))
    kept = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # The generator writes `## <elementId> [family/kind/state]`, so the id is
        # everything before the bracket — not the first whitespace-delimited
        # token. An element id may legitimately contain a space, and reading only
        # the first token truncated `identity.value.innovation smuggled` to
        # `identity.value.innovation`, which *is* in the universe. The block was
        # then attributed to the wrong element and kept.
        match = re.match(r"^##\s+(.+?)\s+\[[^\[\]]*\]\s*$", block.splitlines()[0])
        if not match:
            raise ValueError(
                f"Reasoning Chapter {chapter.get('id')} carries a block whose heading "
                f"does not name exactly one element: {block.splitlines()[0]!r}"
            )
        element_id = identity_key(match.group(1))
        if element_id not in declared_universe:
            continue
        if element_id in excluded_ids:
            continue
        kept.append(block)
    return "\n\n".join(kept)

def _validate_compiled_context(compiled_context, request):
    violations = compiled_context_contract_errors(compiled_context)
    if violations:
        raise ValueError(
            "compiled context does not satisfy the published Compiled Brand Context "
            f"3.0.0 contract: {violations[0]}"
        )
    if compiled_context.get("kind") != "obds-compiled-brand-context":
        raise ValueError("Context Assembly requires a Compiled Brand Context")
    if compiled_context.get("artifactHash") != artifact_hash(compiled_context):
        raise ValueError("compiled context artifactHash mismatch")
    if identity_key(compiled_context.get("targetId") or "") != identity_key(request.get("targetId") or ""):
        raise ValueError("assembly target does not match compiled context")

    token_budget = compiled_context.get("tokenBudget") or {}
    tokenizer_key = (token_budget.get("tokenizerId"), token_budget.get("tokenizerVersion"))
    if tokenizer_key not in SUPPORTED_TOKENIZERS:
        raise ValueError(
            f"unsupported tokenizer in compiled context: {tokenizer_key[0]}@{tokenizer_key[1]}"
        )

    policy = compiled_context.get("contextAssembly")
    if not isinstance(policy, dict):
        raise ValueError("compiled context has no Context Assembly policy")
    if request.get("deliveryMode") not in DELIVERY_MODES:
        raise ValueError("invalid deliveryMode")
    if request.get("applicationMode") not in APPLICATION_MODES:
        raise ValueError("invalid applicationMode")
    if request.get("deliveryMode") != policy.get("deliveryMode"):
        raise ValueError("deliveryMode not allowed by compiled context")
    if request.get("applicationMode") != policy.get("applicationMode"):
        raise ValueError("applicationMode not allowed by compiled context")

    records = compiled_context.get("elementRecords")
    if not isinstance(records, list):
        raise ValueError("compiled context has no elementRecords")
    # Section 8.0a: identities are compared on their canonical form. The
    # compiled context emits canonical ids in availableElementIds while
    # elementRecords keeps the approved spelling, so indexing the records by
    # their raw id rejected a valid artefact whose ids were not already NFC.
    by_id = {identity_key(item["id"]): item for item in records}
    if len(by_id) != len(records):
        raise ValueError("duplicate element IDs in compiled context")
    declared = {identity_key(item) for item in compiled_context.get("availableElementIds", [])}
    if declared != set(by_id):
        raise ValueError("compiled context availableElementIds mismatch")
    return policy, by_id


def _validate_resolution_manifest(compiled_context, retrieval, resolution_manifest):
    if retrieval.get("resolution") == "manifest_checked":
        if resolution_manifest is None:
            raise ValueError("manifest_checked resolution requires exact manifest snapshot")
        expected = compiled_context["manifest"]
        actual_hash = (resolution_manifest.get("approval") or {}).get("contentHash")
        if (
            identity_key(resolution_manifest.get("id") or "") != identity_key(expected.get("id") or "")
            or resolution_manifest.get("version") != expected.get("version")
            or actual_hash != expected.get("contentHash")
        ):
            raise ValueError("resolution manifest does not match compiled context")
        # Section 7: comparing the *declared* hash only proves the snapshot says
        # the right thing. A snapshot carrying a different governed identity set
        # can say it too, simply by copying the expected value. So the snapshot
        # has to reproduce the hash it claims — the same rule the derived views
        # follow, applied to the one path that reads the manifest at runtime.
        if manifest_content_hash(resolution_manifest) != actual_hash:
            raise ValueError(
                "resolution manifest does not reproduce its approval contentHash, so it "
                "is not the approved manifest the compiled context names"
            )
    elif resolution_manifest is not None:
        raise ValueError("manifest access is allowed only for manifest_checked no-hit resolution")


def _assert_view_integrity(view, view_hash_key, collection_key, item_hash_key, label):
    """Reproduce a derived view's own hashes, item by item and then as a whole."""
    for item in view.get(collection_key, []):
        declared = item.get(item_hash_key)
        recomputed = sha256_id({k: v for k, v in item.items() if k != item_hash_key})
        if declared != recomputed:
            raise ValueError(f"{label} {item.get('id')} does not reproduce its {item_hash_key}")
    declared = view.get(view_hash_key)
    recomputed = sha256_id({k: v for k, v in view.items() if k != view_hash_key})
    if declared != recomputed:
        raise ValueError(f"derived view does not reproduce its {view_hash_key}")


def assemble(compiled_context, search_index, chapter_set, request, *, resolution_manifest=None):
    policy, by_id = _validate_compiled_context(compiled_context, request)
    manifest_ref = compiled_context["manifest"]
    manifest_hash = manifest_ref["contentHash"]

    for source in (search_index, chapter_set):
        if source["manifest"]["contentHash"] != manifest_hash:
            raise ValueError("derived view manifest mismatch")
        if identity_key(source["manifest"]["id"]) != identity_key(manifest_ref["id"]) or source["manifest"]["version"] != manifest_ref["version"]:
            raise ValueError("derived view manifest identity mismatch")

    # The compiled artefact is checked against its own `artifactHash`; the
    # derived views were not checked against theirs. So a Search Card or a
    # Reasoning Chapter could be edited after generation and still be assembled,
    # with the stale `cardHash`, `chapterHash`, `indexHash` and `chapterSetHash`
    # carried into the Model Input Package as if they described what was sent.
    # A block whose heading names an available element then delivered arbitrary
    # text to the model. A hash a package publishes has to be a hash the
    # assembler reproduced.
    _assert_view_integrity(search_index, "indexHash", "cards", "cardHash", "Search Card")
    _assert_view_integrity(chapter_set, "chapterSetHash", "chapters", "chapterHash", "Reasoning Chapter")

    cards = {item["id"]: item for item in search_index["cards"]}
    chapters = {item["id"]: item for item in chapter_set["chapters"]}

    retrieval = request["retrieval"]
    if retrieval.get("status") not in RETRIEVAL_STATUSES:
        raise ValueError("invalid retrieval status")
    if retrieval.get("resolution") not in RESOLUTION_MODES:
        raise ValueError("invalid retrieval resolution")
    if retrieval.get("truthOutcome") not in TRUTH_OUTCOMES:
        raise ValueError("invalid retrieval truthOutcome")
    if (
        retrieval["status"] in {"no_match", "low_confidence"}
        and (retrieval["resolution"] == "unresolved" or retrieval["truthOutcome"] == "unresolved")
    ):
        raise ValueError("retrieval silence unresolved")
    _validate_resolution_manifest(compiled_context, retrieval, resolution_manifest)

    selected = request["selection"]
    for card_id in selected["searchCardIds"]:
        if card_id not in cards:
            raise ValueError(f"unknown Search Card: {card_id}")
    for chapter_id in selected["reasoningChapterIds"]:
        if chapter_id not in chapters:
            raise ValueError(f"unknown Reasoning Chapter: {chapter_id}")

    for key in ("factElementIds", "gapElementIds", "activeGuidanceElementIds"):
        for element_id in selected[key]:
            if identity_key(element_id) not in by_id:
                raise ValueError(f"element is not available in compiled target: {element_id}")

    eligible = {identity_key(item) for item in policy.get("eligibleGuidanceIds", [])}
    active = {identity_key(item) for item in selected["activeGuidanceElementIds"]}
    if not active.issubset(eligible):
        raise ValueError("active guidance is not eligible for compiled target")

    hard_boundary_elements = [
        element
        for element in by_id.values()
        if element.get("family") == "rules"
        and element.get("state") == "defined"
        and (
            (element.get("value") or {}).get("enforcement") in {"block", "require_approval"}
            # Section 14.1, and section 15.4 downstream: an applicable
            # prohibition is a hard boundary whatever its enforcement. Selecting
            # on enforcement alone dropped it out of the model input even when
            # the compiler had correctly placed it in the slot.
            or (element.get("value") or {}).get("obligation") == "prohibit"
        )
    ]
    hard_boundary_elements.sort(key=lambda item: identity_key(item["id"]))
    hard_boundary_ids = [identity_key(item["id"]) for item in hard_boundary_elements]

    fact_elements = []
    for element_id in selected["factElementIds"]:
        element = by_id[identity_key(element_id)]
        if element.get("state") != "defined":
            raise ValueError(f"fact element is not defined: {element_id}")
        if element.get("family") == "rules":
            raise ValueError(f"rule cannot be fact grounding: {element_id}")
        fact_elements.append(element)

    gap_elements = []
    for element_id in selected["gapElementIds"]:
        element = by_id[identity_key(element_id)]
        if element.get("state") not in {"unknown", "not_defined", "not_applicable"}:
            raise ValueError(f"gap element has no knowledge-gap state: {element_id}")
        gap_elements.append(element)

    if request["applicationMode"] == "compliance" and selected["activeGuidanceElementIds"]:
        raise ValueError("compliance mode cannot activate expression guidance")

    active_guidance = []
    for element_id in selected["activeGuidanceElementIds"]:
        element = by_id[identity_key(element_id)]
        if element.get("state") != "defined":
            raise ValueError(f"active guidance is not defined: {element_id}")
        if element.get("family") == "rules":
            raise ValueError(f"rule cannot be active guidance: {element_id}")
        active_guidance.append(element)

    # Section 14.3a: the compiled artefact's declared universe, established once
    # and used by everything that renders. `_validate_compiled_context` has
    # already proven this equals the `elementRecords` index.
    declared_universe = {identity_key(item) for item in compiled_context.get("availableElementIds", [])}

    selected_chapters = [chapters[item] for item in selected["reasoningChapterIds"]]
    if request["deliveryMode"] == "reasoning" and not selected_chapters:
        raise ValueError("reasoning mode requires at least one chapter")

    def _refuse_chapters_outside_the_universe(chapters_to_check):
        """A chapter that *declares* elements outside the universe is reported.

        Silently trimming them would move the defect from the model input into a
        filter nobody reads. This runs on the chapters that are actually
        rendered, which under `deliveryMode: full` is not the requested set: full
        mode replaces the selection with every chapter, so checking only the
        request's chapters left the expansion unchecked.
        """
        for chapter in chapters_to_check:
            outside = sorted(
                identity_key(item)
                for item in chapter.get("elementIds", [])
                if identity_key(item) not in declared_universe
            )
            if outside:
                raise ValueError(
                    f"Reasoning Chapter {chapter.get('id')} declares elements outside the "
                    "compiled artefact's declared universe: " + ", ".join(outside)
                )

    _refuse_chapters_outside_the_universe(selected_chapters)

    if request["deliveryMode"] == "full":
        selected_chapters = list(chapters.values())
        # Full mode is an expansion, so the universe check runs again over what
        # the expansion produced.
        _refuse_chapters_outside_the_universe(selected_chapters)
        fact_elements = [
            item for item in by_id.values()
            if item.get("nature") == "fact"
            and item.get("state") == "defined"
            and item.get("family") != "rules"
        ]
        gap_elements = [
            item for item in by_id.values()
            if item.get("state") in {"unknown", "not_defined", "not_applicable"}
        ]

    # Section 8.0a: ordering is an identity ordering, and it has to happen
    # before anything is rendered. Sorting after the slots were built left the
    # selection order in stateMap, guidanceContext and modelInputHash while the
    # emitted id arrays looked correctly sorted.
    fact_elements.sort(key=lambda item: identity_key(item["id"]))
    gap_elements.sort(key=lambda item: identity_key(item["id"]))
    active_guidance.sort(key=lambda item: identity_key(item["id"]))
    selected_chapters.sort(key=lambda item: item["id"])

    state_lines = [render_element(item) for item in gap_elements]
    if retrieval["truthOutcome"] == "not_covered":
        state_lines.append(
            "runtime.coverage [not_covered]: "
            "The current manifest contains no applicable element for the question. "
            "This does not imply permission or prohibition."
        )
    elif retrieval["truthOutcome"] == "access_limited":
        state_lines.append(
            "runtime.coverage [access_limited]: "
            "Applicable brand truth may exist but is unavailable to this target."
        )
    elif retrieval["truthOutcome"] == "prohibited":
        state_lines.append(
            "runtime.decision [prohibited]: "
            "An applicable explicit prohibit RULE blocks the requested action or value."
        )

    guidance_parts = []
    if active_guidance:
        guidance_parts.append(
            "[ACTIVE_GUIDANCE]\n" + "\n".join(render_element(item) for item in active_guidance)
        )
    if selected_chapters:
        exact_ids = set(hard_boundary_ids)
        exact_ids.update(identity_key(item["id"]) for item in fact_elements)
        exact_ids.update(identity_key(item["id"]) for item in gap_elements)
        exact_ids.update(identity_key(item["id"]) for item in active_guidance)
        chapter_parts = []
        for item in selected_chapters:
            content = _filtered_reference_chapter_content(item, exact_ids, declared_universe)
            if content:
                chapter_parts.append(f"{identity_key(item['id'])}: {content}")
        if chapter_parts:
            guidance_parts.append(
                "[REASONING_CHAPTERS]\n"
                "Generated relationship context. Exact elements already present in other slots are omitted here. "
                "Only elements listed under ACTIVE_GUIDANCE are expression requirements for this task.\n\n"
                + "\n\n".join(chapter_parts)
            )

    # Section 14.3a / 10.2a seam. Every element rendered into a slot above is
    # drawn from `by_id`, and `_validate_compiled_context` has already proven
    # `by_id` equals `availableElementIds`, so the slot side of this seam holds
    # by construction and an assertion here could not fail. The side that could
    # fail — and did — is Reasoning Chapter content, which is text rather than an
    # element lookup; it is filtered against `declared_universe` where it is
    # rendered, and a chapter that declares an undeclared element is refused
    # outright above.

    slots = {
        "hardBoundaries": "\n".join(render_rule_for_model(item) for item in hard_boundary_elements),
        "factGrounding": "\n".join(render_element(item) for item in fact_elements),
        "stateMap": "\n".join(state_lines),
        "guidanceContext": "\n\n".join(guidance_parts),
        "taskInput": request["taskInput"],
    }
    final_text = render_model_input(slots)

    actual_tokens = len(final_text.split())
    max_tokens = request["tokenBudget"]["max"]
    if actual_tokens > max_tokens:
        raise ValueError(f"token overflow: actual={actual_tokens}, max={max_tokens}")

    package = {
        "kind": "obds-model-input-package",
        "schemaVersion": "1.0.0",
        "id": f"urn:obds:model-input:{uuid.uuid4()}",
        "assembledAt": datetime.now(timezone.utc).isoformat(),
        "targetId": request["targetId"],
        "deliveryMode": request["deliveryMode"],
        "applicationMode": request["applicationMode"],
        "manifest": copy.deepcopy(manifest_ref),
        "sources": {
            "compiledContextHash": compiled_context["artifactHash"],
            "searchIndexHash": search_index["indexHash"],
            "chapterSetHash": chapter_set["chapterSetHash"],
        },
        "retrieval": retrieval,
        "selection": {
            "searchCardIds": selected["searchCardIds"],
            "reasoningChapterIds": [item["id"] for item in selected_chapters],
            "hardBoundaryElementIds": hard_boundary_ids,
            "factElementIds": sorted(identity_key(item["id"]) for item in fact_elements),
            "gapElementIds": sorted(identity_key(item["id"]) for item in gap_elements),
            "activeGuidanceElementIds": sorted(active),
        },
        "slots": slots,
        "tokenBudget": {
            "tokenizerId": compiled_context["tokenBudget"]["tokenizerId"],
            "tokenizerVersion": compiled_context["tokenBudget"]["tokenizerVersion"],
            "max": max_tokens,
            "actual": actual_tokens,
        },
        "modelInputHash": text_hash(final_text),
    }
    package["assemblyHash"] = sha256_id(package)
    return package, final_text
