from __future__ import annotations
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Callable
import uuid
from .canonical import (artefact_hash, compiled_context_identity_positions,
                        identity_admissibility_errors, identity_key,
                        model_input_package_identity_positions, sha256_id, text_hash)
from .checks import (
    CompiledCheckContractError,
    UnicodeAdmissibilityError,
    assert_check_input_admissible,
    execute_checks,
)
from .model_input import ModelInputContractError, render_model_input

DECISIONS={"released","build_failed","assembly_failed","no_valid_artifact","preflight_blocked","postflight_blocked","approval_required"}


def _parse_time(raw):
    value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _artifact_valid_at(artefact, runtime_at):
    """A validity window the runtime cannot read is not a window it may ignore.

    The contract constrains these to RFC 3339, so an unreadable value should not
    reach here — but `_parse_time` raising out of the runtime is an uncontrolled
    exception where section 15.9 requires a governed decision, and that is true
    whatever the contract says. Unreadable means invalid.
    """
    start = artefact.get("validFrom")
    end = artefact.get("validTo")
    try:
        if start and runtime_at < _parse_time(start):
            return False
        if end and runtime_at >= _parse_time(end):
            return False
    except (TypeError, ValueError):
        return False
    return True


def _failure_decision(findings, *, phase):
    if any(not x.passed and x.enforcement == "block" for x in findings):
        return "preflight_blocked" if phase == "preflight" else "postflight_blocked"
    if any(not x.passed and x.enforcement == "require_approval" for x in findings):
        return "approval_required"
    return None

def _task_input_hash(task_input):
    """Section 15.9: every runtime attempt creates a Runtime Decision Record.

    `text_hash` refuses a string carrying a code point unassigned in the pinned
    Unicode version, which is correct — but until 3.0.0 it refused by raising
    out of the runtime, so the one attempt that most needs a record produced
    none. A null `taskInputHash` now means exactly one thing, stated in section
    15.9: the task input was inadmissible under section 14.3c, nothing was
    mechanically evaluated, and the decision is fail-closed.
    """
    try:
        assert_check_input_admissible(task_input, where="task input")
        return text_hash(task_input)
    except (TypeError, ValueError):
        return None


def _admissibility_finding(exc, *, phase):
    return {
        "rule_element_id": "obds:runtime:unicode-admissibility",
        "primitive": "unicode_admissibility",
        "enforcement": "block",
        "phase": phase,
        "passed": False,
        "message": str(exc),
        "result": "fail",
    }


COMPILED_CONTEXT_KIND = "obds-compiled-brand-context"
COMPILED_CONTEXT_SCHEMA_VERSION = "3.0.0"


def _assert_artefact_identity(artefact):
    """The artefact has to be the kind and version of thing this runtime executes.

    `artifactHash` proves the payload is intact; it says nothing about whether
    the payload is a Compiled Brand Context of a version this runtime knows. A
    document of another kind, correctly self-hashed, executed.
    """
    if artefact.get("kind") != COMPILED_CONTEXT_KIND:
        raise CompiledCheckContractError(
            f"not a Compiled Brand Context: kind is {artefact.get('kind')!r}"
        )
    if artefact.get("schemaVersion") != COMPILED_CONTEXT_SCHEMA_VERSION:
        raise CompiledCheckContractError(
            "this runtime executes Compiled Brand Context "
            f"{COMPILED_CONTEXT_SCHEMA_VERSION}, not {artefact.get('schemaVersion')!r}"
        )


def _compiled_checks(artefact):
    """Section 11.4: `compiledChecks` is required, so its absence is not empty.

    `_compiled_checks(artefact)` turned a missing required property into
    "this artefact enforces nothing", so deleting the property and rehashing
    disabled every deterministic check and released output the artefact's own
    HARD_BOUNDARIES still prohibited.
    """
    _assert_artefact_identity(artefact)
    checks = artefact.get("compiledChecks")
    if not isinstance(checks, list):
        raise CompiledCheckContractError(
            "compiled context does not state compiledChecks, so it does not state what "
            "it enforces"
        )
    return checks


def _execute_governed_checks(artefact, *, phase, text):
    """Section 14.3c: the admissibility gate belongs to the text, not to the list.

    Admissibility is asked here, independently of Foundation check execution, so
    it cannot be skipped by an artefact that happens to enforce nothing. The
    contract question is asked first, in that order, because an artefact that
    does not state what it enforces is invalid whatever its input looks like.
    """
    checks = _compiled_checks(artefact)
    assert_check_input_admissible(text, where=f"{phase} check input")
    return execute_checks(checks, phase=phase, text=text)


def _reject_artefact(record, exc, *, record_path):
    """Section 13.2: an artefact that leaves a governed parameter open is invalid.

    Not `preflight_blocked` — nothing was evaluated and no task was withheld.
    The artefact itself does not state the decision it claims to carry, which is
    exactly what `no_valid_artifact` already means.
    """
    record["checkResults"].append({
        "rule_element_id": "obds:runtime:compiled-check-contract",
        "primitive": "compiled_check_contract",
        "enforcement": "block",
        "phase": "artefact",
        "passed": False,
        "message": str(exc),
        "result": "fail",
    })
    record["decision"] = "no_valid_artifact"
    if record_path:
        append_runtime_record(record_path, record)
    return record


def _fail_closed_on_admissibility(record, exc, *, phase, record_path):
    """Section 14.3c violation: withhold, record, and say why.

    The decision uses the existing blocked vocabulary rather than a new value:
    the output was withheld at that phase, which is what those values mean, and
    the `checkResults` entry distinguishes "evaluated and failed" from "could
    not be evaluated" — the distinction section 15.9 could not previously make.
    """
    record["checkResults"].append(_admissibility_finding(exc, phase=phase))
    record["decision"] = "preflight_blocked" if phase == "preflight" else "postflight_blocked"
    if record_path:
        append_runtime_record(record_path, record)
    return record


def _new_record(target_id, artefact, task_input, provider, model_id, runtime_at=None):
    runtime_at = runtime_at or datetime.now(timezone.utc)
    return {
        "kind": "obds-runtime-decision-record",
        # 3.0.0 publishes a corrected Runtime Decision Record contract beside
        # the frozen 1.0.0 surface, exactly as 1.1 did for compiled contexts.
        # `taskInputHash` becomes nullable because there is no admissible hash
        # for an inadmissible task input, and section 15.9 requires a record
        # for that attempt all the same.
        "schemaVersion": "3.0.0",
        "recordId": f"urn:uuid:{uuid.uuid4()}",
        "recordedAt": runtime_at.isoformat(),
        # `isinstance`, not truthiness: a non-object artefact reached `.get`
        # here and raised out of the runtime before anything could decide.
        "targetId": target_id or (artefact.get("targetId") if isinstance(artefact, dict) else None),
        "artifactHash": artefact.get("artifactHash") if isinstance(artefact, dict) else None,
        "assemblyHash": None,
        "modelInputHash": None,
        "taskInputHash": _task_input_hash(task_input),
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


_SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"
_CONTEXT_SCHEMA_PATH = _SCHEMA_DIR / "compiled-context.schema.json"
_PACKAGE_SCHEMA_PATH = _SCHEMA_DIR / "model-input-package.schema.json"
_VALIDATORS: dict[str, Any] = {}


def _validator_for(path):
    """One validator per published contract, built once.

    The runtime executed the Compiled Brand Context contract and read the Model
    Input Package by hand: a package declaring `kind: not-a-model-input-package`
    at `schemaVersion: 999.0.0`, resealed, was released with a model call. Three
    documents reach this runtime and all three have a published contract.
    """
    key = str(path)
    if key not in _VALIDATORS:
        import jsonschema

        from .governed_io import load_data

        _VALIDATORS[key] = jsonschema.Draft202012Validator(load_data(path))
    return _VALIDATORS[key]


def _contract_violations(document, path):
    if not isinstance(document, dict):
        return [f"<root>: a governed document is an object, not {type(document).__name__}"]
    return [
        ("/".join(str(part) for part in error.path) or "<root>") + ": " + error.message
        for error in sorted(_validator_for(path).iter_errors(document), key=str)
    ]


def _context_validator():
    """Execute the published Compiled Brand Context contract, not a summary of it.

    The runtime verified `artifactHash`, `kind`, `schemaVersion` and the shape of
    `compiledChecks`, and then read `slots` as if the rest of the contract had
    been checked. It had not: a correctly re-sealed artefact carrying a property
    the contract forbids was released, and one missing a required slot raised
    `KeyError` out of prompt assembly instead of deciding. A hash proves the
    payload is intact. It does not prove the payload is governable.
    """
    return _validator_for(_CONTEXT_SCHEMA_PATH)


def _contract_errors(artefact):
    """Every way the published contract refuses this artefact, worst first."""
    return _contract_violations(artefact, _CONTEXT_SCHEMA_PATH)


def _comparable_identity(value):
    """The canonical comparison key, or the value itself when it is not one.

    `identity_key` is the one identity primitive in the release and it refuses
    an inadmissible string. Both artefacts have already passed section 8.0a at
    this point, so a refusal here means a position the enumeration does not
    cover; returning the raw value keeps the comparison strict rather than
    turning a gap into an accidental match.
    """
    if not isinstance(value, str):
        return value
    try:
        return identity_key(value)
    except (TypeError, ValueError):
        return value


def _governed_artefact_errors(artefact):
    """Everything that disqualifies a received artefact before a field is used.

    Two ratified rules, one gate. The published contract decides whether this is
    a Compiled Brand Context; section 8.0a decides whether the identities it
    carries are ones the canonical form can tell apart. The second was enforced
    where the compiler *produces* a document and nowhere where a runtime
    *receives* one, so `manifest.id` values differing only in CR versus LF —
    which fold to the same bytes — sealed to one `artifactHash` under one
    `approval.contentHash`, and both were released.
    """
    violations = _contract_errors(artefact)
    if violations:
        return [
            "compiled context does not satisfy the published Compiled Brand Context "
            f"{COMPILED_CONTEXT_SCHEMA_VERSION} contract: {violation}"
            for violation in violations
        ]
    return [
        f"compiled context carries an inadmissible governed identity: {error}"
        for error in identity_admissibility_errors(compiled_context_identity_positions(artefact))
    ]


def _governed_package_errors(package):
    """The published Model Input Package contract, then section 8.0a.

    Same two rules and the same order as the Compiled Brand Context gate. The
    package was checked by hash and by a handful of fields, so one declaring
    another kind at another schema version reached the model.
    """
    violations = _contract_violations(package, _PACKAGE_SCHEMA_PATH)
    if violations:
        return [
            "model input package does not satisfy the published Model Input Package "
            f"contract: {violation}"
            for violation in violations
        ]
    return [
        f"model input package carries an inadmissible governed identity: {error}"
        for error in identity_admissibility_errors(model_input_package_identity_positions(package))
    ]


_RECORD_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "runtime-decision-record.schema.json"
_RECORD_VALIDATOR = None


def _record_validator():
    """Execute the published contract, rather than restating two of its rules.

    `kind` and `decision` were checked by hand and everything else in the record
    was unverified, so a record the published contract refuses was still written
    as governed evidence.
    """
    global _RECORD_VALIDATOR
    if _RECORD_VALIDATOR is None:
        import jsonschema

        from .governed_io import load_data

        _RECORD_VALIDATOR = jsonschema.Draft202012Validator(load_data(_RECORD_SCHEMA_PATH))
    return _RECORD_VALIDATOR


def append_runtime_record(path, record):
    value = {key: item for key, item in record.items() if key != "output"}
    errors = sorted(_record_validator().iter_errors(value), key=str)
    if errors:
        location = "/".join(str(part) for part in errors[0].path) or "<root>"
        raise ValueError(f"invalid Runtime Decision Record: {location}: {errors[0].message}")
    if record.get("decision") not in DECISIONS:
        raise ValueError("invalid Runtime Decision Record")
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
    # Section 14. The contract decides whether this document is a Compiled Brand
    # Context before any field of it is read — including the two fields the
    # Runtime Decision Record copies as evidence. Asked after the record was
    # built, `_new_record` reached `artefact.get(...)` first, so a non-object
    # artefact raised `AttributeError` out of the runtime and the record section
    # 15.9 requires for that attempt was never written. Both entry points ask in
    # this order, so the answer cannot depend on which one the caller reached for.
    violations = [] if artefact is None else _governed_artefact_errors(artefact)
    record = _new_record(
        target_id, None if violations else artefact, task_input, provider, model_id, runtime_at
    )
    if artefact is None:
        record["decision"] = "build_failed"
        if record_path:
            append_runtime_record(record_path, record)
        return record
    if violations:
        return _reject_artefact(record, CompiledCheckContractError(violations[0]), record_path=record_path)
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

    try:
        preflight = _execute_governed_checks(artefact, phase="preflight", text=task_input)
    except CompiledCheckContractError as exc:
        return _reject_artefact(record, exc, record_path=record_path)
    except UnicodeAdmissibilityError as exc:
        return _fail_closed_on_admissibility(record, exc, phase="preflight", record_path=record_path)
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

    try:
        postflight = _execute_governed_checks(
            artefact,
            phase="postflight",
            text=output,
        )
    except CompiledCheckContractError as exc:
        return _reject_artefact(record, exc, record_path=record_path)
    except UnicodeAdmissibilityError as exc:
        return _fail_closed_on_admissibility(record, exc, phase="postflight", record_path=record_path)
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
    # Section 14. The contract decides whether this document is a Compiled Brand
    # Context before any field of it is read — including the two fields the
    # Runtime Decision Record copies as evidence. Asked after the record was
    # built, `_new_record` reached `artefact.get(...)` first, so a non-object
    # artefact raised `AttributeError` out of the runtime and the record section
    # 15.9 requires for that attempt was never written. Both entry points ask in
    # this order, so the answer cannot depend on which one the caller reached for.
    violations = [] if artefact is None else _governed_artefact_errors(artefact)
    record = _new_record(
        target_id, None if violations else artefact, task_input, provider, model_id, runtime_at
    )
    if artefact is None:
        record["decision"] = "build_failed"
        if record_path:
            append_runtime_record(record_path, record)
        return record
    if violations:
        return _reject_artefact(record, CompiledCheckContractError(violations[0]), record_path=record_path)
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

    # Section 8.0a over the other received artefact. The package carries element
    # identities and a manifest identity of its own, and none of them was ever
    # asked whether the canonical form can tell it apart from another.
    if _governed_package_errors(package):
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
    try:
        # Section 15.9: `text_hash` refuses an inadmissible string, and refusing
        # here — before the guarded block below — raised straight out of the
        # runtime, so the one attempt that most needs a record produced none.
        rendered_hash = text_hash(model_input_text)
    except (TypeError, ValueError):
        rendered_hash = None
    if rendered_hash is None or package.get("modelInputHash") != rendered_hash:
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

    # Section 15.10 / 26.2, closed in 3.0.0. Every hash the 2.0.0 runtime
    # verified was valid; the one string the checks were applied to was not
    # verified against any of them. Preflight ran on the `task_input` argument
    # while the model was called with `model_input_text`, so a benign decoy
    # released a request whose real assembled input was blocked.
    #
    # The first correction compared `task_input` against `package.slots.taskInput`
    # and `modelInputHash` against `model_input_text`. That is two pairs, not a
    # chain: nothing tied the rendered text to the slots it claimed to render, so
    # editing the rendered `[TASK_INPUT]` block and recomputing both hashes still
    # reached the model with unchecked text.
    #
    # The chain, enforced here, before any check and before any model call:
    #
    #   preflight task input = package.slots.taskInput
    #                        = rendered [TASK_INPUT] bytes
    #
    # The runtime reproduces the rendering from the slots it verified and
    # compares byte for byte, so `model_input_text` stops being an assertion the
    # caller makes and becomes something the runtime derives.
    slots = package.get("slots")
    if not isinstance(slots, dict) or slots.get("taskInput") != task_input:
        return assembly_failed_record(
            target_id=target_id or artefact.get("targetId"),
            artefact=artefact,
            task_input=task_input,
            provider=provider,
            model_id=model_id,
            record_path=record_path,
        )
    try:
        assert_check_input_admissible(slots["taskInput"], where="package task input")
        expected_model_input = render_model_input(slots)
    except (ModelInputContractError, UnicodeAdmissibilityError):
        return assembly_failed_record(
            target_id=target_id or artefact.get("targetId"),
            artefact=artefact,
            task_input=task_input,
            provider=provider,
            model_id=model_id,
            record_path=record_path,
        )
    if expected_model_input != model_input_text or rendered_hash != package.get("modelInputHash"):
        return assembly_failed_record(
            target_id=target_id or artefact.get("targetId"),
            artefact=artefact,
            task_input=task_input,
            provider=provider,
            model_id=model_id,
            record_path=record_path,
        )

    # A package declares which target, which delivery and application mode, and
    # which manifest it was assembled for. Verifying only its hashes left those
    # declarations unchecked, so a resealed package could claim a mode the
    # artefact does not permit and the Runtime Decision Record would carry the
    # claim as governed evidence.
    policy = artefact.get("contextAssembly") or {}
    # Section 8.0a: `targetId` is a governed identity, so it is compared on its
    # canonical form. It was compared as raw document bytes here while the
    # assembler compared it through `identity_key`, so the two disagreed in both
    # directions at once: an NFC/NFD-equivalent target the assembler correctly
    # accepted was refused here, and the comparison rule differed between the
    # two ends of the same seam.
    declared = [
        ("targetId", package.get("targetId"), artefact.get("targetId"), True),
        ("deliveryMode", package.get("deliveryMode"), policy.get("deliveryMode"), False),
        ("applicationMode", package.get("applicationMode"), policy.get("applicationMode"), False),
    ]
    for name, claimed, allowed, canonical in declared:
        if canonical:
            claimed, allowed = _comparable_identity(claimed), _comparable_identity(allowed)
        if allowed is not None and claimed != allowed:
            return assembly_failed_record(
                target_id=target_id or artefact.get("targetId"),
                artefact=artefact,
                task_input=task_input,
                provider=provider,
                model_id=model_id,
                record_path=record_path,
            )
    # The package declares which manifest it was assembled from. Binding only
    # `contentHash` bound the bytes and not the identity: a package naming a
    # different brand at a different version, with the hash left untouched, was
    # released. Governed identity is the triple, compared the way section 8.0a
    # compares identities.
    package_manifest = package.get("manifest") or {}
    artefact_manifest = artefact.get("manifest") or {}
    manifest_identity = [
        ("id", True),
        ("version", False),
        ("contentHash", False),
    ]
    manifest_mismatch = False
    for field_name, canonical in manifest_identity:
        claimed = package_manifest.get(field_name)
        allowed = artefact_manifest.get(field_name)
        if canonical:
            claimed, allowed = _comparable_identity(claimed), _comparable_identity(allowed)
        if claimed != allowed:
            manifest_mismatch = True
            break
    if manifest_mismatch:
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

    try:
        pre = _execute_governed_checks(artefact, phase="preflight", text=task_input)
    except CompiledCheckContractError as exc:
        return _reject_artefact(record, exc, record_path=record_path)
    except UnicodeAdmissibilityError as exc:
        return _fail_closed_on_admissibility(record, exc, phase="preflight", record_path=record_path)
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

    try:
        post = _execute_governed_checks(artefact, phase="postflight", text=output)
    except CompiledCheckContractError as exc:
        return _reject_artefact(record, exc, record_path=record_path)
    except UnicodeAdmissibilityError as exc:
        return _fail_closed_on_admissibility(record, exc, phase="postflight", record_path=record_path)
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
