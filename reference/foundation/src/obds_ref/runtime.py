from __future__ import annotations
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Callable
import uuid
from .canonical import artefact_hash, text_hash, sha256_id
from .checks import execute_checks

DECISIONS={"released","build_failed","assembly_failed","no_valid_artifact","preflight_blocked","postflight_blocked","approval_required"}


def _parse_time(raw):
    value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _artifact_valid_at(artefact, runtime_at):
    start = artefact.get("validFrom")
    end = artefact.get("validTo")
    if start and runtime_at < _parse_time(start):
        return False
    if end and runtime_at >= _parse_time(end):
        return False
    return True


def _failure_decision(findings, *, phase):
    if any(not x.passed and x.enforcement == "block" for x in findings):
        return "preflight_blocked" if phase == "preflight" else "postflight_blocked"
    if any(not x.passed and x.enforcement == "require_approval" for x in findings):
        return "approval_required"
    return None

def _new_record(target_id, artefact, task_input, provider, model_id, runtime_at=None):
    runtime_at = runtime_at or datetime.now(timezone.utc)
    return {
        "kind": "obds-runtime-decision-record",
        "schemaVersion": "1.0.0",
        "recordId": f"urn:uuid:{uuid.uuid4()}",
        "recordedAt": runtime_at.isoformat(),
        "targetId": target_id or (artefact.get("targetId") if artefact else None),
        "artifactHash": artefact.get("artifactHash") if artefact else None,
        "assemblyHash": None,
        "modelInputHash": None,
        "taskInputHash": text_hash(task_input),
        "decision": None,
        "modelCall": {
            "called": False,
            "provider": provider,
            "model": model_id,
            "requestId": None,
        },
        "checkResults": [],
        "output": None,
    }


def append_runtime_record(path, record):
    if (
        record.get("kind") != "obds-runtime-decision-record"
        or record.get("decision") not in DECISIONS
    ):
        raise ValueError("invalid Runtime Decision Record")
    value = {key: item for key, item in record.items() if key != "output"}
    with Path(path).open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        )


def run_with_model(
    artefact,
    *,
    task_input,
    model: Callable[[str], str | tuple[str, str | None]],
    target_id=None,
    provider=None,
    model_id=None,
    record_path=None,
    runtime_at=None,
):
    runtime_at = runtime_at or datetime.now(timezone.utc)
    record = _new_record(
        target_id, artefact, task_input, provider, model_id, runtime_at
    )
    if artefact is None:
        record["decision"] = "build_failed"
        if record_path:
            append_runtime_record(record_path, record)
        return record
    if artefact.get("artifactHash") != artefact_hash(artefact):
        record["decision"] = "no_valid_artifact"
        if record_path:
            append_runtime_record(record_path, record)
        return record
    if not _artifact_valid_at(artefact, runtime_at):
        record["decision"] = "no_valid_artifact"
        if record_path:
            append_runtime_record(record_path, record)
        return record

    preflight = execute_checks(
        artefact.get("compiledChecks", []),
        phase="preflight",
        text=task_input,
    )
    record["checkResults"].extend(
        [
            {**asdict(item), "result": "pass" if item.passed else "fail"}
            for item in preflight
        ]
    )
    preflight_decision = _failure_decision(preflight, phase="preflight")
    if preflight_decision:
        record["decision"] = preflight_decision
        if record_path:
            append_runtime_record(record_path, record)
        return record

    slots = artefact["slots"]
    prompt = (
        f"[HARD_BOUNDARIES]\n{slots['hardBoundaries']}\n\n"
        f"[FACT_GROUNDING]\n{slots['factGrounding']}\n\n"
        f"[STATE_MAP]\n{slots['stateMap']}\n\n"
        f"[STYLE_TEXTURE]\n{slots['styleTexture']}\n\n"
        f"[TASK_INPUT]\n{task_input}\n"
    )
    record["modelCall"]["called"] = True
    response = model(prompt)
    if isinstance(response, tuple):
        output, request_id = response
        record["modelCall"]["requestId"] = request_id
    else:
        output = response

    postflight = execute_checks(
        artefact.get("compiledChecks", []),
        phase="postflight",
        text=output,
    )
    record["checkResults"].extend(
        [
            {**asdict(item), "result": "pass" if item.passed else "fail"}
            for item in postflight
        ]
    )
    postflight_decision = _failure_decision(postflight, phase="postflight")
    if postflight_decision:
        record["decision"] = postflight_decision
        if record_path:
            append_runtime_record(record_path, record)
        return record

    record["decision"] = "released"
    record["output"] = output
    if record_path:
        append_runtime_record(record_path, record)
    return record


def assembly_failed_record(*, target_id, artefact, task_input, provider=None, model_id=None, record_path=None):
    record = _new_record(target_id, artefact, task_input, provider, model_id)
    record["decision"] = "assembly_failed"
    if record_path:
        append_runtime_record(record_path, record)
    return record


def run_assembled_with_model(
    artefact,
    package,
    model_input_text,
    *,
    task_input,
    model: Callable[[str], str | tuple[str, str | None]],
    target_id=None,
    provider=None,
    model_id=None,
    record_path=None,
    runtime_at=None,
):
    runtime_at = runtime_at or datetime.now(timezone.utc)
    record = _new_record(target_id, artefact, task_input, provider, model_id, runtime_at)
    if artefact is None:
        record["decision"] = "build_failed"
        if record_path:
            append_runtime_record(record_path, record)
        return record
    if artefact.get("artifactHash") != artefact_hash(artefact):
        record["decision"] = "no_valid_artifact"
        if record_path:
            append_runtime_record(record_path, record)
        return record
    if not _artifact_valid_at(artefact, runtime_at):
        record["decision"] = "no_valid_artifact"
        if record_path:
            append_runtime_record(record_path, record)
        return record

    if not isinstance(package, dict):
        return assembly_failed_record(
            target_id=target_id or artefact.get("targetId"),
            artefact=artefact,
            task_input=task_input,
            provider=provider,
            model_id=model_id,
            record_path=record_path,
        )

    compiled_hash = (package.get("sources") or {}).get("compiledContextHash")
    if compiled_hash != artefact.get("artifactHash"):
        return assembly_failed_record(
            target_id=target_id or artefact.get("targetId"),
            artefact=artefact,
            task_input=task_input,
            provider=provider,
            model_id=model_id,
            record_path=record_path,
        )
    if package.get("modelInputHash") != text_hash(model_input_text):
        return assembly_failed_record(
            target_id=target_id or artefact.get("targetId"),
            artefact=artefact,
            task_input=task_input,
            provider=provider,
            model_id=model_id,
            record_path=record_path,
        )
    payload = {key: value for key, value in package.items() if key != "assemblyHash"}
    if package.get("assemblyHash") != sha256_id(payload):
        return assembly_failed_record(
            target_id=target_id or artefact.get("targetId"),
            artefact=artefact,
            task_input=task_input,
            provider=provider,
            model_id=model_id,
            record_path=record_path,
        )

    record["assemblyHash"] = package["assemblyHash"]
    record["modelInputHash"] = package["modelInputHash"]

    pre = execute_checks(artefact.get("compiledChecks", []), phase="preflight", text=task_input)
    record["checkResults"].extend(
        [{**asdict(x), "result": "pass" if x.passed else "fail"} for x in pre]
    )
    pre_decision = _failure_decision(pre, phase="preflight")
    if pre_decision:
        record["decision"] = pre_decision
        if record_path:
            append_runtime_record(record_path, record)
        return record

    record["modelCall"]["called"] = True
    response = model(model_input_text)
    if isinstance(response, tuple):
        output, request_id = response
        record["modelCall"]["requestId"] = request_id
    else:
        output = response

    post = execute_checks(artefact.get("compiledChecks", []), phase="postflight", text=output)
    record["checkResults"].extend(
        [{**asdict(x), "result": "pass" if x.passed else "fail"} for x in post]
    )
    post_decision = _failure_decision(post, phase="postflight")
    if post_decision:
        record["decision"] = post_decision
        if record_path:
            append_runtime_record(record_path, record)
        return record

    record["decision"] = "released"
    record["output"] = output
    if record_path:
        append_runtime_record(record_path, record)
    return record
