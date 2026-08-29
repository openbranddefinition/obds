from __future__ import annotations

from datetime import datetime, timezone
import copy
import json
import re
import uuid

from canonical import sha256_id, text_hash



DELIVERY_MODES = {"lookup", "reasoning", "full"}
APPLICATION_MODES = {"create", "review", "compliance"}
RETRIEVAL_STATUSES = {"hit", "partial", "no_match", "low_confidence", "access_filtered"}
RESOLUTION_MODES = {"direct", "widened", "manifest_checked", "unresolved"}
SUPPORTED_TOKENIZERS = {("obds:whitespace-v1", "1.0.0")}

TRUTH_OUTCOMES = {
    "defined", "unknown", "not_defined", "not_applicable", "prohibited",
    "not_covered", "access_limited", "mixed", "unresolved"
}

SLOT_ORDER = [
    ("HARD_BOUNDARIES", "hardBoundaries"),
    ("FACT_GROUNDING", "factGrounding"),
    ("STATE_MAP", "stateMap"),
    ("GUIDANCE_CONTEXT", "guidanceContext"),
    ("TASK_INPUT", "taskInput"),
]


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
    return f"{element['id']} [{element['state']}]: {rendered}".rstrip()


def render_rule_for_model(element):
    value = element.get("value") or {}
    prefix = f"{element['id']} [{value.get('obligation','?')}/{value.get('enforcement','inform')}]"
    parts = [f"{prefix}: {value.get('statement','').strip()}"]
    refs = value.get("references") or []
    if refs:
        parts.append("refs=" + ",".join(refs))
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
            params = check.get("params") or {}
            compact_checks.append(primitive + "(" + _compact_json(params) + ")")
        parts.append("checks=" + ";".join(compact_checks))
    return " | ".join(parts)


def _filtered_reference_chapter_content(chapter, excluded_ids):
    renderer = chapter.get("renderer") or {}
    if renderer.get("id") != "org.openbranddefinition.reference-chapter-renderer":
        return chapter.get("content", "")
    blocks = re.split(r"(?m)(?=^## )", chapter.get("content", ""))
    kept = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        match = re.match(r"^##\s+([^\s]+)", block)
        if match and match.group(1) in excluded_ids:
            continue
        kept.append(block)
    return "\n\n".join(kept)

def render_model_input(slots):
    parts = []
    for label, key in SLOT_ORDER:
        parts.append(f"[{label}]\n{slots[key]}")
    return "\n\n".join(parts)


def _validate_compiled_context(compiled_context, request):
    if compiled_context.get("kind") != "obds-compiled-brand-context":
        raise ValueError("Context Assembly requires a Compiled Brand Context")
    if compiled_context.get("artifactHash") != artifact_hash(compiled_context):
        raise ValueError("compiled context artifactHash mismatch")
    if compiled_context.get("targetId") != request.get("targetId"):
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
    by_id = {item["id"]: item for item in records}
    if len(by_id) != len(records):
        raise ValueError("duplicate element IDs in compiled context")
    declared = set(compiled_context.get("availableElementIds", []))
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
            resolution_manifest.get("id") != expected.get("id")
            or resolution_manifest.get("version") != expected.get("version")
            or actual_hash != expected.get("contentHash")
        ):
            raise ValueError("resolution manifest does not match compiled context")
    elif resolution_manifest is not None:
        raise ValueError("manifest access is allowed only for manifest_checked no-hit resolution")


def assemble(compiled_context, search_index, chapter_set, request, *, resolution_manifest=None):
    policy, by_id = _validate_compiled_context(compiled_context, request)
    manifest_ref = compiled_context["manifest"]
    manifest_hash = manifest_ref["contentHash"]

    for source in (search_index, chapter_set):
        if source["manifest"]["contentHash"] != manifest_hash:
            raise ValueError("derived view manifest mismatch")
        if source["manifest"]["id"] != manifest_ref["id"] or source["manifest"]["version"] != manifest_ref["version"]:
            raise ValueError("derived view manifest identity mismatch")

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
            if element_id not in by_id:
                raise ValueError(f"element is not available in compiled target: {element_id}")

    eligible = set(policy.get("eligibleGuidanceIds", []))
    active = set(selected["activeGuidanceElementIds"])
    if not active.issubset(eligible):
        raise ValueError("active guidance is not eligible for compiled target")

    hard_boundary_elements = [
        element
        for element in by_id.values()
        if element.get("family") == "rules"
        and element.get("state") == "defined"
        and (element.get("value") or {}).get("enforcement") in {"block", "require_approval"}
    ]
    hard_boundary_elements.sort(key=lambda item: item["id"])
    hard_boundary_ids = [item["id"] for item in hard_boundary_elements]

    fact_elements = []
    for element_id in selected["factElementIds"]:
        element = by_id[element_id]
        if element.get("state") != "defined":
            raise ValueError(f"fact element is not defined: {element_id}")
        if element.get("family") == "rules":
            raise ValueError(f"rule cannot be fact grounding: {element_id}")
        fact_elements.append(element)

    gap_elements = []
    for element_id in selected["gapElementIds"]:
        element = by_id[element_id]
        if element.get("state") not in {"unknown", "not_defined", "not_applicable"}:
            raise ValueError(f"gap element has no knowledge-gap state: {element_id}")
        gap_elements.append(element)

    if request["applicationMode"] == "compliance" and selected["activeGuidanceElementIds"]:
        raise ValueError("compliance mode cannot activate expression guidance")

    active_guidance = []
    for element_id in selected["activeGuidanceElementIds"]:
        element = by_id[element_id]
        if element.get("state") != "defined":
            raise ValueError(f"active guidance is not defined: {element_id}")
        if element.get("family") == "rules":
            raise ValueError(f"rule cannot be active guidance: {element_id}")
        active_guidance.append(element)

    selected_chapters = [chapters[item] for item in selected["reasoningChapterIds"]]
    if request["deliveryMode"] == "reasoning" and not selected_chapters:
        raise ValueError("reasoning mode requires at least one chapter")

    if request["deliveryMode"] == "full":
        selected_chapters = list(chapters.values())
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
        exact_ids.update(item["id"] for item in fact_elements)
        exact_ids.update(item["id"] for item in gap_elements)
        exact_ids.update(item["id"] for item in active_guidance)
        chapter_parts = []
        for item in selected_chapters:
            content = _filtered_reference_chapter_content(item, exact_ids)
            if content:
                chapter_parts.append(f"{item['id']}: {content}")
        if chapter_parts:
            guidance_parts.append(
                "[REASONING_CHAPTERS]\n"
                "Generated relationship context. Exact elements already present in other slots are omitted here. "
                "Only elements listed under ACTIVE_GUIDANCE are expression requirements for this task.\n\n"
                + "\n\n".join(chapter_parts)
            )

    fact_elements.sort(key=lambda item: item["id"])
    gap_elements.sort(key=lambda item: item["id"])
    active_guidance.sort(key=lambda item: item["id"])
    selected_chapters.sort(key=lambda item: item["id"])

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
            "factElementIds": sorted(item["id"] for item in fact_elements),
            "gapElementIds": sorted(item["id"] for item in gap_elements),
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
