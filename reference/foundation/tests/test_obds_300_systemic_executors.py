"""Systemic mechanisms 4 and 5 — two surfaces that were enumerated by one example.

Mechanism 4 — every Compiled Brand Context executor executes the contract.

The runtime validated the published Compiled Brand Context contract. The CLI did
not, so the same correctly re-sealed schema-invalid artefact was `no_valid_artifact`
on one path and `valid: true` on another, and the official conformance runner's
`validate` case type agreed with the weaker one. The cause was not the CLI. It was
that the enumeration named `run_with_model` and called that the surface.

Mechanism 5 — every consumer of the contract inventory derives it.

`contract_directories()` replaced two hand-kept lists of contract directories.
There was a third, in `manifest_path()`, which resolved every `schemas/3.0.0/`
entry under the frozen 1.0.0 directory — so a regenerated manifest would have
failed verification for the whole new contract surface, and the packaging tests
could not see it because they never sent a produced archive path back.

Both are closed the same way: discovery finds the candidates, the registry in
`systemic_surface` classifies them, and an unclassified new path fails the
enumeration rather than escaping coverage.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import copy
import importlib.util
import io
import json
import shutil
import sys
from pathlib import Path

import pytest

from obds_ref.canonical import artefact_hash
from obds_ref.governed_io import ValidationFailure, load_data
from systemic_surface import (
    COMPILED_CONTEXT_CONSUMERS,
    COMPILED_CONTEXT_MARKERS,
    CONTRACT_VERSION_CONSUMERS,
    CONTRACT_VERSION_MARKERS,
    CONTRACT_VERSION_MODULES,
    EXECUTOR,
    PACKAGE_ROOT,
    REFERENCE,
)

CONTEXT_ASSEMBLY = REFERENCE / "context-assembly"
FOUNDATION_FIXTURES = REFERENCE / "foundation" / "fixtures"
BASE_ARTEFACT = CONTEXT_ASSEMBLY / "examples" / "compiled-social-copy-global-en.json"


# --------------------------------------------------------------------------
# Discovery
# --------------------------------------------------------------------------

def _functions_referencing(path: Path, markers) -> list[str]:
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:  # pragma: no cover - the release does not ship one
        return []
    lines = source.splitlines()
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = "\n".join(lines[node.lineno - 1 : node.end_lineno])
        if any(marker in body for marker in markers):
            found.append(node.name)
    return found


def _discover_compiled_context_consumers() -> set[str]:
    """Production and official-conformance modules that touch a compiled context.

    Test modules are excluded by construction: a test is not a governed executor,
    and the executors a test drives are the ones registered here.
    """
    discovered = set()
    for root in ("reference", "tools"):
        for path in sorted((PACKAGE_ROOT / root).rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            relative = path.relative_to(PACKAGE_ROOT).as_posix()
            if "/tests/" in relative or path.name.startswith("test_"):
                continue
            for name in _functions_referencing(path, COMPILED_CONTEXT_MARKERS):
                discovered.add(f"{relative}::{name}")
    return discovered


def _discover_contract_version_consumers() -> set[str]:
    discovered = set()
    for relative in CONTRACT_VERSION_MODULES:
        path = PACKAGE_ROOT / relative
        if not path.is_file():
            continue
        for name in _functions_referencing(path, CONTRACT_VERSION_MARKERS):
            discovered.add(f"{relative}::{name}")
    return discovered


def test_mechanism_4_every_compiled_context_consumer_is_classified():
    """A new consumer is covered the day it is written, or this fails."""
    discovered = _discover_compiled_context_consumers()
    registered = set(COMPILED_CONTEXT_CONSUMERS)
    unclassified = sorted(discovered - registered)
    assert not unclassified, (
        "these consume a Compiled Brand Context and are in no surface registry, so "
        "nothing drives them: " + ", ".join(unclassified)
    )
    stale = sorted(registered - discovered)
    assert not stale, f"registry entries that no longer exist in the release: {stale}"


def test_mechanism_5_every_contract_version_consumer_is_classified():
    discovered = _discover_contract_version_consumers()
    registered = set(CONTRACT_VERSION_CONSUMERS)
    unclassified = sorted(discovered - registered)
    assert not unclassified, (
        "these read the contract/version inventory and are in no surface registry: "
        + ", ".join(unclassified)
    )
    stale = sorted(registered - discovered)
    assert not stale, f"registry entries that no longer exist in the release: {stale}"


# --------------------------------------------------------------------------
# Mechanism 4 — the adversarial artefacts, driven against every executor.
# --------------------------------------------------------------------------

def _malformed_nested_check(document):
    """A compiled check missing `terms`, which its own contract requires."""
    document["compiledChecks"] = [
        {
            "ruleElementId": "rule.probe",
            "primitive": "term_prohibited",
            "phase": "preflight",
            "enforcement": "block",
            "params": {"appliesTo": "task_input", "match": "word_boundary_ci"},
        }
    ]


ADVERSARIAL_ARTEFACTS = [
    ("unknown property", lambda d: d.__setitem__("totallyUnknownProperty", "x")),
    ("missing required property", lambda d: d.pop("governedResultHash")),
    ("missing compiledChecks", lambda d: d.pop("compiledChecks")),
    ("malformed nested compiled check", _malformed_nested_check),
    ("root is not an object", None),
]


def _artefact(mutate):
    """Every mutation is re-sealed, so the schema gate is what has to kill it."""
    if mutate is None:
        return ["not", "an", "object"]
    document = load_data(BASE_ARTEFACT)
    mutate(document)
    document["artifactHash"] = artefact_hash(document)
    return document


def _valid_artefact():
    document = load_data(BASE_ARTEFACT)
    document["artifactHash"] = artefact_hash(document)
    return document


def _valid_artefact_for(executor):
    """The review validator binds one specific artefact, so it gets that one.

    Every other executor takes any valid Compiled Brand Context.
    """
    if executor.endswith("validate_review"):
        return load_data(CONTEXT_ASSEMBLY / "examples" / "compiled-marketing-review-global-en.json")
    return _valid_artefact()


def _load_flat(directory: Path, name: str):
    key = f"_obds_exec_{directory.name.replace('-', '_')}_{name}"
    if key in sys.modules:
        return sys.modules[key]
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
    spec = importlib.util.spec_from_file_location(key, directory / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


def _write(tmp_path, document):
    path = tmp_path / "artefact.json"
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return path


def _drive_run_with_model(document, tmp_path):
    from obds_ref.runtime import run_with_model

    calls = []
    record = run_with_model(
        document,
        task_input="A clean request.",
        model=lambda prompt: calls.append(prompt) or "A careful answer.",
        target_id=document.get("targetId") if isinstance(document, dict) else None,
    )
    return record["decision"] != "no_valid_artifact", len(calls)


def _drive_run_assembled_with_model(document, tmp_path):
    from obds_ref.runtime import run_assembled_with_model

    calls = []
    record = run_assembled_with_model(
        document,
        {"sources": {"compiledContextHash": None}},
        "rendered",
        task_input="A clean request.",
        model=lambda prompt: calls.append(prompt) or "A careful answer.",
        target_id=document.get("targetId") if isinstance(document, dict) else None,
    )
    # `assembly_failed` is this executor's answer for a package it cannot bind;
    # only `no_valid_artifact` proves the *contract* gate fired, so the valid
    # case is asserted separately below.
    return record["decision"] != "no_valid_artifact", len(calls)


def _drive_command_validate(document, tmp_path):
    from obds_ref.cli import command_validate

    path = _write(tmp_path, document)
    # A file-based executor's first gate is the governed reader: a root the
    # governed contract refuses never reaches the schema. Refused is refused.
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            code = command_validate(argparse.Namespace(file=str(path)))
    except ValidationFailure:
        return False, 0
    return code == 0, 0


def _drive_command_check(document, tmp_path):
    from obds_ref.cli import command_check

    path = _write(tmp_path, document)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            code = command_check(
                argparse.Namespace(artifact=str(path), phase="preflight", text="clean", text_file=None)
            )
    except ValidationFailure:
        return False, 0
    return code == 0, 0


def _drive_validate_document(document, tmp_path):
    from obds_ref.cli import _validate_document

    return not _validate_document(document), 0


def _drive_assembly(document, tmp_path):
    module = _load_flat(CONTEXT_ASSEMBLY, "assemble_context")
    policy = document.get("contextAssembly") if isinstance(document, dict) else {}
    request = {
        "targetId": document.get("targetId") if isinstance(document, dict) else None,
        "deliveryMode": (policy or {}).get("deliveryMode"),
        "applicationMode": (policy or {}).get("applicationMode"),
    }
    try:
        module._validate_compiled_context(document, request)
        return True, 0
    except ValueError:
        return False, 0


def _drive_validate_review(document, tmp_path):
    """The package is made to name the artefact under test, so only the contract answers.

    Left pointing at the original artefact, the `compiledContextHash` comparison
    would refuse every mutation before the contract was ever asked — one gate
    answering for another, which is how the missing contract gate stayed hidden
    here in the first place. The hash boundary has its own driver, in the
    mechanism 2 suite.
    """
    module = _load_flat(CONTEXT_ASSEMBLY, "validate_review")
    assembler = _load_flat(CONTEXT_ASSEMBLY, "assemble_context")
    package = load_data(CONTEXT_ASSEMBLY / "examples" / "model-input-review.json")
    review = load_data(CONTEXT_ASSEMBLY / "examples" / "review-result-valid.json")
    if isinstance(document, dict):
        package["sources"] = {
            **package["sources"],
            "compiledContextHash": assembler.artifact_hash(document),
        }
    try:
        return module.validate_review(document, package, review) is True, 0
    except (ValueError, KeyError):
        return False, 0


EXECUTOR_DRIVERS = {
    "reference/foundation/src/obds_ref/runtime.py::run_with_model": _drive_run_with_model,
    "reference/foundation/src/obds_ref/runtime.py::run_assembled_with_model": _drive_run_assembled_with_model,
    "reference/foundation/src/obds_ref/cli.py::command_validate": _drive_command_validate,
    "reference/foundation/src/obds_ref/cli.py::command_check": _drive_command_check,
    "reference/foundation/src/obds_ref/cli.py::_validate_document": _drive_validate_document,
    "reference/context-assembly/assemble_context.py::_validate_compiled_context": _drive_assembly,
    "reference/context-assembly/validate_review.py::validate_review": _drive_validate_review,
}


def test_mechanism_4_every_registered_executor_has_a_driver():
    """A registry entry nothing drives is a claim, not coverage."""
    registered = {key for key, role in COMPILED_CONTEXT_CONSUMERS.items() if role == EXECUTOR}
    assert registered == set(EXECUTOR_DRIVERS), (
        "executors without a driver: "
        f"{sorted(registered - set(EXECUTOR_DRIVERS))}; "
        f"drivers without an executor: {sorted(set(EXECUTOR_DRIVERS) - registered)}"
    )


@pytest.mark.parametrize("executor", sorted(EXECUTOR_DRIVERS))
def test_mechanism_4_every_executor_accepts_the_valid_artefact(executor, tmp_path):
    """Not a wall: the unmutated artefact still passes every executor's contract gate.

    The assembled executor is driven with a package it cannot bind, so its answer
    for a valid artefact is `assembly_failed`. That is the point: the artefact
    got past the contract gate, which is the only thing asserted here.
    """
    accepted, _ = EXECUTOR_DRIVERS[executor](_valid_artefact_for(executor), tmp_path)
    assert accepted, f"{executor} rejects a valid Compiled Brand Context"


@pytest.mark.parametrize("executor", sorted(EXECUTOR_DRIVERS))
@pytest.mark.parametrize("name,mutate", ADVERSARIAL_ARTEFACTS, ids=[c[0] for c in ADVERSARIAL_ARTEFACTS])
def test_mechanism_4_no_executor_accepts_a_resealed_schema_invalid_artefact(
    executor, name, mutate, tmp_path
):
    """The seal is correct in every case here, so only the contract can refuse it."""
    accepted, model_calls = EXECUTOR_DRIVERS[executor](_artefact(mutate), tmp_path)
    assert not accepted, f"{executor} accepted an artefact with {name}"
    assert model_calls == 0, f"{executor} called the model on an artefact with {name}"


# --------------------------------------------------------------------------
# C1 — the admissibility gate does not depend on the check list.
# --------------------------------------------------------------------------

INADMISSIBLE = "hello ࢗ there"  # U+0897, unassigned in Unicode 15.1


def _artefact_with_no_checks():
    document = load_data(CONTEXT_ASSEMBLY / "examples" / "compiled-brand-query-global-en.json")
    assert document["compiledChecks"] == [], "this fixture is meant to carry no checks"
    return document


def _artefact_with_a_check():
    document = load_data(FOUNDATION_FIXTURES / "preflight-block.context.json")
    assert document["compiledChecks"], "this fixture is meant to carry a check"
    return document


@pytest.mark.parametrize(
    "shape,build",
    [("compiledChecks present", _artefact_with_a_check), ("compiledChecks empty", _artefact_with_no_checks)],
)
def test_c1_inadmissible_task_input_fails_closed_whatever_the_check_list(shape, build):
    """Admissibility is a property of the text, not of which rules are listed.

    `execute_checks` asked it `if checks`, so an artefact enforcing nothing —
    the ordinary case — sent inadmissible task input to the model.
    """
    from obds_ref.runtime import run_with_model

    document = build()
    calls = []
    record = run_with_model(
        document,
        task_input=INADMISSIBLE,
        model=lambda prompt: calls.append(prompt) or "A careful answer.",
        target_id=document.get("targetId"),
    )
    assert record["decision"] == "preflight_blocked", f"{shape}: decided {record['decision']!r}"
    assert calls == [], f"{shape}: the model was called with inadmissible task input"


@pytest.mark.parametrize(
    "shape,build",
    [("compiledChecks present", _artefact_with_a_check), ("compiledChecks empty", _artefact_with_no_checks)],
)
def test_c1_inadmissible_model_output_fails_closed_whatever_the_check_list(shape, build):
    from obds_ref.runtime import run_with_model

    document = build()
    record = run_with_model(
        document,
        task_input="A clean request.",
        model=lambda prompt: f"answer {INADMISSIBLE}",
        target_id=document.get("targetId"),
    )
    assert record["decision"] == "postflight_blocked", f"{shape}: decided {record['decision']!r}"
    assert record["output"] is None, f"{shape}: inadmissible output was returned"


def test_c1_the_check_executor_gates_admissibility_with_no_checks_at_all():
    """The gate is in the executor too, not only in the runtime that calls it."""
    from obds_ref.checks import UnicodeAdmissibilityError, execute_checks

    with pytest.raises(UnicodeAdmissibilityError):
        execute_checks([], phase="preflight", text=INADMISSIBLE)


# --------------------------------------------------------------------------
# Mechanism 5 — a version directory nobody has created yet.
# --------------------------------------------------------------------------

def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def synthetic_contract_version():
    """A contract directory that exists only for the length of one test.

    The registries and the derived discovery are both code; the only honest way
    to ask whether a future version falls out is to create one and look.
    """
    version = "9.9.9"
    created = []
    for family, schema_name in (("schemas", "compiled-context.schema.json"), ("value-schemas", "rule.schema.json")):
        directory = PACKAGE_ROOT / family / version
        directory.mkdir(parents=True, exist_ok=False)
        created.append(directory)
        (directory / schema_name).write_text(
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "$id": f"https://openbranddefinition.org/{family}/{version}/{schema_name}",
                    "type": "object",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    try:
        yield version
    finally:
        for directory in created:
            shutil.rmtree(directory, ignore_errors=True)


def test_mechanism_5_a_future_contract_version_cannot_fall_out(synthetic_contract_version):
    version = synthetic_contract_version
    gate = _load_module("executors_gate", REFERENCE / "release-gate.py")
    builder = _load_module("executors_builder", PACKAGE_ROOT / "tools" / "build-release.py")

    discovered = {url for _, url, _ in gate.contract_directories()}
    assert f"schemas/{version}" in discovered, "discovery does not see a new contract directory"
    assert f"value-schemas/{version}" in discovered, "discovery does not see a new value-contract directory"

    archive_paths = {archive for archive, _ in builder.package_files("3.0.0")}
    expected = {
        f"schemas/{version}/compiled-context.schema.json",
        f"value-schemas/{version}/rule.schema.json",
    }
    missing = sorted(expected - archive_paths)
    assert not missing, f"the release package does not carry a new contract directory: {missing}"

    inventoried = {
        path
        for directory, _, _ in gate.contract_directories()
        for path in directory.glob("*.json")
    }
    for family, schema_name in (("schemas", "compiled-context.schema.json"), ("value-schemas", "rule.schema.json")):
        source = PACKAGE_ROOT / family / version / schema_name
        assert source in inventoried, f"the release gate does not inventory {source}"

    for archive in sorted(expected):
        resolved = gate.manifest_path(archive)
        assert resolved.is_file(), f"manifest_path resolves {archive} to {resolved}, which does not exist"
        assert resolved == PACKAGE_ROOT / archive, (
            f"manifest_path resolves {archive} to {resolved}, not to the file the package carries"
        )


def test_mechanism_5_manifest_path_round_trips_every_packaged_contract():
    """Every contract path the packager produces resolves back to the file it packed.

    `manifest_path()` kept its own version logic and sent every `schemas/3.0.0/`
    entry under the frozen 1.0.0 directory. The packaging tests could not see it
    because they never asked the gate to resolve a produced archive path.
    """
    gate = _load_module("executors_gate_roundtrip", REFERENCE / "release-gate.py")
    builder = _load_module("executors_builder_roundtrip", PACKAGE_ROOT / "tools" / "build-release.py")

    checked = 0
    for archive, source in builder.package_files("3.0.0"):
        if not archive.startswith(("schemas/", "value-schemas/")):
            continue
        checked += 1
        resolved = gate.manifest_path(archive)
        assert resolved.resolve() == source.resolve(), (
            f"manifest_path({archive!r}) resolves to {resolved}, not to {source}"
        )
    assert checked, "no contract path was checked at all"


# --------------------------------------------------------------------------
# Every governed document a runtime receives has a published contract.
# --------------------------------------------------------------------------

MODEL_INPUT_PACKAGE_MUTATIONS = [
    ("another kind", lambda p: p.__setitem__("kind", "not-a-model-input-package")),
    ("another schema version", lambda p: p.__setitem__("schemaVersion", "999.0.0")),
    ("a property the contract forbids", lambda p: p.__setitem__("smuggled", "field")),
    ("a required property removed", lambda p: p.pop("retrieval")),
]


@pytest.mark.parametrize("name,mutate", MODEL_INPUT_PACKAGE_MUTATIONS, ids=[c[0] for c in MODEL_INPUT_PACKAGE_MUTATIONS])
def test_the_assembled_runtime_executes_the_model_input_package_contract(name, mutate):
    """Three documents reach this runtime; all three have a published contract.

    Only the artefact's was executed, so a package declaring another kind at
    another schema version was resealed and released with a model call.
    """
    from obds_ref.canonical import sha256_id
    from obds_ref.runtime import run_assembled_with_model

    compiled = load_data(CONTEXT_ASSEMBLY / "examples" / "compiled-social-copy-global-en.json")
    package = copy.deepcopy(load_data(CONTEXT_ASSEMBLY / "examples" / "model-input-create.json"))
    rendered = (CONTEXT_ASSEMBLY / "examples" / "rendered-input-create.txt").read_text(encoding="utf-8")
    mutate(package)
    package["assemblyHash"] = sha256_id(
        {key: value for key, value in package.items() if key != "assemblyHash"}
    )
    calls = []
    record = run_assembled_with_model(
        compiled, package, rendered,
        task_input=package.get("slots", {}).get("taskInput", ""),
        model=lambda prompt: calls.append(prompt) or "A careful answer.",
    )
    assert record["decision"] == "assembly_failed", f"{name}: decided {record['decision']!r}"
    assert calls == [], f"{name}: the model was called on an invalid package"


def test_the_assembled_runtime_still_accepts_the_published_package():
    from obds_ref.runtime import run_assembled_with_model

    compiled = load_data(CONTEXT_ASSEMBLY / "examples" / "compiled-social-copy-global-en.json")
    package = load_data(CONTEXT_ASSEMBLY / "examples" / "model-input-create.json")
    rendered = (CONTEXT_ASSEMBLY / "examples" / "rendered-input-create.txt").read_text(encoding="utf-8")
    record = run_assembled_with_model(
        compiled, package, rendered,
        task_input=package["slots"]["taskInput"],
        model=lambda prompt: "A careful answer.",
    )
    assert record["decision"] == "released"


NESTED_CONTRACT_MUTATIONS = [
    ("an element record without an id", lambda d: d["elementRecords"][0].pop("id")),
    ("an element record without a family", lambda d: d["elementRecords"][0].pop("family")),
    ("a validity window that is not a date", lambda d: d.__setitem__("validFrom", "not-a-date")),
    ("a validTo that is not a date", lambda d: d.__setitem__("validTo", "whenever")),
    ("a build.asOf that is not a date", lambda d: d["build"].__setitem__("asOf", "yesterday")),
]


@pytest.mark.parametrize("name,mutate", NESTED_CONTRACT_MUTATIONS, ids=[c[0] for c in NESTED_CONTRACT_MUTATIONS])
def test_a_nested_shape_the_contract_left_open_cannot_crash_an_executor(name, mutate):
    """Contract-before-field-access holds only as far as the contract is precise.

    `elementRecords.items` constrained nothing and the validity window was typed
    as a string, so artefacts that satisfied the contract and were correctly
    resealed raised `KeyError` out of Context Assembly and `ValueError` out of
    the runtime, where section 15.9 requires a governed decision.
    """
    from obds_ref.runtime import run_with_model

    document = load_data(BASE_ARTEFACT)
    mutate(document)
    document["artifactHash"] = artefact_hash(document)

    calls = []
    record = run_with_model(
        document,
        task_input="A clean request.",
        model=lambda prompt: calls.append(prompt) or "A careful answer.",
        target_id=document.get("targetId"),
    )
    assert record["decision"] == "no_valid_artifact", f"{name}: decided {record['decision']!r}"
    assert calls == [], f"{name}: the model was called anyway"

    module = _load_flat(CONTEXT_ASSEMBLY, "assemble_context")
    policy = document.get("contextAssembly") or {}
    request = {
        "targetId": document.get("targetId"),
        "deliveryMode": policy.get("deliveryMode"),
        "applicationMode": policy.get("applicationMode"),
    }
    with pytest.raises(ValueError):
        module._validate_compiled_context(document, request)
