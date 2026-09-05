"""The drivers for mechanism 2, one per registered hash verification call site.

They live in their own module for one reason: the proof that a driver actually
exercises the call site it is registered against runs each of them in a
subprocess, against a copy of the release with that site's gate neutralised. A
driver that cannot be addressed by name from outside the test process cannot be
proved to hit anything.

Each driver takes a mode and returns whether the code accepted:

    valid    the untouched fixture
    tamper   a mutated payload under its original hash
    reseal   a mutated payload whose own hash the caller recomputed
"""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

from obds_ref.canonical import (
    artefact_hash,
    manifest_content_hash,
    sha256_id,
    text_hash,
    value_shape_hash,
)
from obds_ref.compiler import build_target, load_data, validate_manifest
from obds_ref.model_input import render_model_input
from obds_ref.runtime import run_assembled_with_model, run_with_model

TESTS = Path(__file__).resolve().parent
FOUNDATION = TESTS.parent
REFERENCE = FOUNDATION.parent
PACKAGE_ROOT = REFERENCE.parent

CA_ROOT = REFERENCE / "context-assembly"
CD_ROOT = REFERENCE / "context-delivery"


def _flat(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if str(path.parent) not in sys.path:
        sys.path.insert(0, str(path.parent))
    spec.loader.exec_module(module)
    return module


def _example(name):
    base = PACKAGE_ROOT / "examples" / name
    return load_data(base / "manifest.yaml"), load_data(base / "build-plan.yaml")


# --------------------------------------------------------------------------
# One driver per hash site. Each returns True when the code accepts.
#
# `tamper` mutates the payload without touching any hash; `reseal` mutates and
# then recomputes the hash the payload carries, which is what a caller who
# controls the document would do.
# --------------------------------------------------------------------------

def _drive_manifest_approval_compiler(mode):
    manifest, _ = _example("foundation-minimal")
    manifest = copy.deepcopy(manifest)
    if mode != "valid":
        manifest["elements"][0]["annotations"] = ["tampered"]
    if mode == "reseal":
        # Reseal is the whole point: a caller who edits the manifest can also
        # recompute its `approval.contentHash`. So this case *must* be accepted
        # here — the compiler's job is to prove the hash matches the payload, and
        # it does. What must not be accepted is the resealed manifest reaching a
        # plan that names the old hash, which the next driver covers.
        manifest["approval"]["contentHash"] = manifest_content_hash(manifest)
    return validate_manifest(manifest) == []


def _drive_manifest_approval_plan_binding(mode):
    """The plan's `manifestRef` names the manifest actually being built.

    The manifest's approval hash is resealed in every mutating mode, so the
    "manifest reproduces its own hash" check cannot answer for this site. What is
    left is the plan still naming the original.
    """
    manifest, plan = _example("foundation-minimal")
    manifest, plan = copy.deepcopy(manifest), copy.deepcopy(plan)
    if mode != "valid":
        manifest["elements"][0]["annotations"] = ["tampered"]
        manifest["approval"]["contentHash"] = manifest_content_hash(manifest)
    if mode == "reseal":
        plan["manifestRef"] = {
            **plan["manifestRef"],
            "contentHash": manifest["approval"]["contentHash"],
        }
    result = build_target(manifest, plan, plan["targets"][0])
    return result.status == "ready"


def _drive_manifest_approval_view_builders(mode):
    builder = _flat("hash_build_views", CA_ROOT / "build_views.py")
    manifest = copy.deepcopy(load_data(CA_ROOT / "examples" / "manifest.yaml"))
    chapter_map = load_data(CA_ROOT / "examples" / "chapter-map.yaml")
    if mode != "valid":
        manifest["elements"][0]["annotations"] = ["tampered"]
    if mode == "reseal":
        manifest["approval"]["contentHash"] = manifest_content_hash(manifest)
    try:
        builder.build_views(manifest, chapter_map)
        return True
    except (ValueError, KeyError):
        return False


def _drive_manifest_approval_resolution_snapshot(mode):
    assembler = _flat("hash_assembler_snapshot", CA_ROOT / "assemble_context.py")
    compiled = load_data(CA_ROOT / "examples" / "compiled-brand-query-global-en.json")
    snapshot = copy.deepcopy(load_data(CA_ROOT / "examples" / "manifest.yaml"))
    if mode != "valid":
        # Annotations, not the id: an identity change is refused by the identity
        # clause of the same condition, which would answer for this site.
        snapshot["elements"][0]["annotations"] = ["tampered"]
        # Resealed in both mutating modes, so the snapshot reproduces its own
        # hash and only "this is not the manifest the artefact names" is left.
        snapshot["approval"]["contentHash"] = manifest_content_hash(snapshot)
    try:
        assembler._validate_resolution_manifest(
            compiled, {"resolution": "manifest_checked"}, snapshot
        )
        return True
    except ValueError:
        return False


def _drive_value_contract_schema_hash(mode):
    manifest, _ = _example("foundation-minimal")
    manifest = copy.deepcopy(manifest)
    contract = manifest["valueContracts"][0]
    if mode != "valid":
        contract["schemaHash"] = "sha256:" + "0" * 64
    if mode == "reseal":
        # There is nothing to reseal: the hash is a claim about a file this
        # document does not carry, so a caller cannot make a wrong value right.
        # That is the property under test.
        contract["schemaHash"] = "sha256:" + "1" * 64
    return validate_manifest(manifest, verify_hash=False) == []


def _drive_value_contract_shape_hash(mode):
    """The element value has the shape its contract declares.

    The declared `shapeHash` is what moves here, not the element value: adding a
    field to the value is also refused by the value schema, which would answer
    for this site.
    """
    manifest, _ = _example("foundation-minimal")
    manifest = copy.deepcopy(manifest)
    element = manifest["elements"][0]
    if mode != "valid":
        for contract in manifest["valueContracts"]:
            if contract["id"] == element.get("valueContractRef"):
                contract["shapeHash"] = "sha256:" + "0" * 64
    if mode == "reseal":
        for contract in manifest["valueContracts"]:
            if contract["id"] == element.get("valueContractRef"):
                contract["shapeHash"] = value_shape_hash(element["value"])
    manifest["approval"]["contentHash"] = manifest_content_hash(manifest)
    return validate_manifest(manifest) == []


def _probe_artefact():
    manifest, plan = _example("foundation-minimal")
    result = build_target(manifest, plan, plan["targets"][0])
    assert result.status == "ready", [error.message for error in result.errors]
    return result.artefact


def _drive_artefact_hash_runtime(mode):
    artefact = copy.deepcopy(_probe_artefact())
    if mode != "valid":
        artefact["slots"] = {**artefact["slots"], "hardBoundaries": "tampered"}
    if mode == "reseal":
        artefact["artifactHash"] = artefact_hash(artefact)
    record = run_with_model(
        artefact,
        task_input="A clean request.",
        model=lambda prompt: "A careful answer.",
        target_id=artefact.get("targetId"),
    )
    return record["decision"] != "no_valid_artifact"


def _drive_artefact_hash_assembly(mode):
    assembler = _flat("hash_assembler_artefact", CA_ROOT / "assemble_context.py")
    compiled = copy.deepcopy(load_data(CA_ROOT / "examples" / "compiled-social-copy-global-en.json"))
    index = load_data(CA_ROOT / "examples" / "search-index.json")
    chapters = load_data(CA_ROOT / "examples" / "reasoning-chapters.json")
    request = load_data(CA_ROOT / "examples" / "assembly-request-create.yaml")
    if mode != "valid":
        compiled["slots"] = {**compiled["slots"], "hardBoundaries": "tampered"}
    if mode == "reseal":
        compiled["artifactHash"] = artefact_hash(compiled)
    try:
        assembler.assemble(compiled, index, chapters, request)
        return True
    except (ValueError, KeyError):
        return False


def _drive_artefact_hash_review(mode):
    """The artefact's own seal, inside the review validator.

    The package is rebound to the mutated artefact, so the `compiledContextHash`
    site cannot answer for this one: only "the artefact does not reproduce its
    own seal" is left to fire.
    """
    reviewer, compiled, package, review = _review_fixture()
    compiled = copy.deepcopy(compiled)
    if mode != "valid":
        compiled["slots"] = {**compiled["slots"], "hardBoundaries": "tampered"}
        package["sources"] = {
            **package["sources"],
            "compiledContextHash": artefact_hash(compiled),
        }
        _reseal_package(package)
    if mode == "reseal":
        compiled["artifactHash"] = artefact_hash(compiled)
    return _run_review(reviewer, compiled, package, review)


def _drive_artefact_hash_assembled_runtime(mode):
    """The artefact's seal on the *assembled* entry point.

    This site shared `_drive_artefact_hash_runtime` with `run_with_model`, and
    that driver calls only `run_with_model`. Two call sites, one proof, and the
    second one was never exercised at all.
    """
    compiled, package, rendered = _assembled_fixture()
    compiled = copy.deepcopy(compiled)
    if mode != "valid":
        compiled["slots"] = {**compiled["slots"], "hardBoundaries": "tampered"}
    if mode == "reseal":
        compiled["artifactHash"] = artefact_hash(compiled)
        package["sources"] = {**package["sources"], "compiledContextHash": compiled["artifactHash"]}
        _reseal_package(package)
    record = run_assembled_with_model(
        compiled, package, rendered,
        task_input=package["slots"]["taskInput"],
        model=lambda prompt: "A careful answer.",
    )
    return record["decision"] != "no_valid_artifact"


def _assembled_fixture():
    compiled = load_data(CA_ROOT / "examples" / "compiled-social-copy-global-en.json")
    package = copy.deepcopy(load_data(CA_ROOT / "examples" / "model-input-create.json"))
    rendered = (CA_ROOT / "examples" / "rendered-input-create.txt").read_text(encoding="utf-8")
    return compiled, package, rendered


def _reseal_package(package):
    package["assemblyHash"] = sha256_id(
        {key: value for key, value in package.items() if key != "assemblyHash"}
    )
    return package


def _drive_package_compiled_context_hash(mode):
    compiled, package, rendered = _assembled_fixture()
    if mode != "valid":
        package["sources"] = {**package["sources"], "compiledContextHash": "sha256:" + "0" * 64}
        # Resealed in both mutating modes: the package's own seal must not answer
        # for the site that binds it to the artefact.
        _reseal_package(package)
    record = run_assembled_with_model(
        compiled, package, rendered,
        task_input=package["slots"]["taskInput"],
        model=lambda prompt: "A careful answer.",
    )
    return record["decision"] != "assembly_failed"


def _drive_package_model_input_hash(mode):
    """The declared model input is the one the package's verified slots render.

    The package is resealed in both mutating modes so its own seal cannot answer
    for this site.
    """
    compiled, package, rendered = _assembled_fixture()
    if mode != "valid":
        package["slots"] = {**package["slots"], "taskInput": "a different governed request"}
        rendered = render_model_input(package["slots"])
        _reseal_package(package)
    if mode == "reseal":
        package["modelInputHash"] = text_hash(rendered)
        _reseal_package(package)
    record = run_assembled_with_model(
        compiled, package, rendered,
        task_input=package["slots"]["taskInput"],
        model=lambda prompt: "A careful answer.",
    )
    return record["decision"] != "assembly_failed"


def _drive_package_assembly_hash(mode):
    """The package's own seal.

    `assembledAt` is mutated rather than a declared mode: every other field the
    runtime compares would be refused by the check that compares it, which would
    answer for this site.
    """
    compiled, package, rendered = _assembled_fixture()
    if mode != "valid":
        package["assembledAt"] = "2099-01-01T00:00:00Z"
    if mode == "reseal":
        _reseal_package(package)
    record = run_assembled_with_model(
        compiled, package, rendered,
        task_input=package["slots"]["taskInput"],
        model=lambda prompt: "A careful answer.",
    )
    return record["decision"] != "assembly_failed"


def _drive_view_hash(collection_key, item_hash_key, view_hash_key, which):
    def driver(mode):
        assembler = _flat(f"hash_assembler_{which}", CA_ROOT / "assemble_context.py")
        compiled = load_data(CA_ROOT / "examples" / "compiled-social-copy-global-en.json")
        index = copy.deepcopy(load_data(CA_ROOT / "examples" / "search-index.json"))
        chapters = copy.deepcopy(load_data(CA_ROOT / "examples" / "reasoning-chapters.json"))
        request = load_data(CA_ROOT / "examples" / "assembly-request-create.yaml")
        view = index if which == "index" else chapters
        if mode != "valid":
            if item_hash_key:
                view[collection_key][0]["label" if which == "index" else "title"] = "tampered"
            else:
                view[view_hash_key] = "sha256:" + "0" * 64
        if mode == "reseal" and item_hash_key:
            item = view[collection_key][0]
            item.pop(item_hash_key, None)
            item[item_hash_key] = sha256_id(item)
            view.pop(view_hash_key, None)
            view[view_hash_key] = sha256_id(view)
        try:
            assembler.assemble(compiled, index, chapters, request)
            return True
        except (ValueError, KeyError):
            return False

    return driver


def _drive_view_builder_manifest(package_dir):
    """The same boundary in each package that ships a view builder."""

    def driver(mode):
        builder = _flat(f"hash_build_views_{package_dir.name.replace('-', '_')}", package_dir / "build_views.py")
        manifest = copy.deepcopy(load_data(package_dir / "examples" / "manifest.yaml"))
        chapter_map = load_data(package_dir / "examples" / "chapter-map.yaml")
        if mode != "valid":
            manifest["elements"][0]["annotations"] = ["tampered"]
        if mode == "reseal":
            manifest["approval"]["contentHash"] = manifest_content_hash(manifest)
        try:
            builder.build_views(manifest, chapter_map)
            return True
        except (ValueError, KeyError):
            return False

    return driver


def _review_fixture():
    reviewer = _flat("hash_reviewer_sites", CA_ROOT / "validate_review.py")
    compiled = load_data(CA_ROOT / "examples" / "compiled-marketing-review-global-en.json")
    package = copy.deepcopy(load_data(CA_ROOT / "examples" / "model-input-review.json"))
    review = copy.deepcopy(load_data(CA_ROOT / "examples" / "review-result-valid.json"))
    return reviewer, compiled, package, review


def _run_review(reviewer, compiled, package, review):
    try:
        return reviewer.validate_review(compiled, package, review) is True
    except (ValueError, KeyError):
        return False


def _drive_review_compiled_context_hash(mode):
    """The package names the artefact the review was derived from.

    The package is resealed in both mutating modes so its own `assemblyHash`
    site cannot answer for this one.
    """
    reviewer, compiled, package, review = _review_fixture()
    if mode != "valid":
        package["sources"] = {**package["sources"], "compiledContextHash": "sha256:" + "0" * 64}
        _reseal_package(package)
    return _run_review(reviewer, compiled, package, review)


def _drive_review_assembly_hash(mode):
    """The package's own seal: selection cannot move under it."""
    reviewer, compiled, package, review = _review_fixture()
    if mode != "valid":
        # F3 now independently rejects a smuggled selection. Change metadata
        # here to isolate the assemblyHash gate rather than test two gates.
        package["assembledAt"] = "2099-01-01T00:00:00Z"
    if mode == "reseal":
        _reseal_package(package)
    return _run_review(reviewer, compiled, package, review)


def _drive_review_model_input_hash(mode):
    """The declared model input is the one the package's slots render.

    Resealing here means recomputing the package's `assemblyHash` and the
    review's `reviewHash` around the *stale* `modelInputHash`, which is exactly
    what a caller holding both documents would do. It must still fail, because
    the hash is reproduced from `slots`, not compared between two claims.
    """
    reviewer, compiled, package, review = _review_fixture()
    if mode != "valid":
        package["slots"] = {**package["slots"], "taskInput": "a different governed request"}
        # Resealed in both mutating modes: the package's own seal site must not
        # answer for the model input site.
        _reseal_package(package)
    if mode == "reseal":
        review["reviewHash"] = sha256_id({k: v for k, v in review.items() if k != "reviewHash"})
    return _run_review(reviewer, compiled, package, review)


def _drive_review_review_hash(mode):
    """The review's own seal over its decision and findings."""
    reviewer, compiled, package, review = _review_fixture()
    if mode != "valid":
        review["decision"] = "pass" if review["decision"] != "pass" else "pass_with_suggestions"
    if mode == "reseal":
        review["reviewHash"] = sha256_id({k: v for k, v in review.items() if k != "reviewHash"})
    return _run_review(reviewer, compiled, package, review)


def _drive_cli_artefact_hash(mode):
    """The CLI gate both CLI executors call."""
    from obds_ref.cli import _compiled_context_errors

    artefact = copy.deepcopy(_probe_artefact())
    if mode != "valid":
        artefact["slots"] = {**artefact["slots"], "hardBoundaries": "tampered"}
    if mode == "reseal":
        artefact["artifactHash"] = artefact_hash(artefact)
    return not _compiled_context_errors(artefact)


def _drive_conformance_artefact_hash(mode):
    """The declared hash conformance case, run through the conformance runner.

    Driven by reimplementing the comparison, this proved nothing about
    `command_conformance`. It builds a one-case suite over a copy of the fixture
    and runs the real command, so the case that fails is the declared one.
    """
    import argparse
    import io
    import json
    import tempfile
    from contextlib import redirect_stdout

    from obds_ref.cli import command_conformance

    fixtures = PACKAGE_ROOT / "reference" / "foundation" / "fixtures"
    fixture = copy.deepcopy(load_data(fixtures / "canonical-hash-vectors.json"))
    if mode != "valid":
        artefact = fixture["artefact"]["input"]
        artefact["slots"] = {**artefact["slots"], "hardBoundaries": "tampered"}
    if mode == "reseal":
        # The caller recomputed the artefact's own seal. The case compares the
        # *declared expected* hash, which names the original payload, so this
        # must still fail.
        fixture["artefact"]["input"]["artifactHash"] = artefact_hash(fixture["artefact"]["input"])

    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        (base / "fixtures").mkdir()
        (base / "fixtures" / "canonical-hash-vectors.json").write_text(
            json.dumps(fixture, ensure_ascii=False), encoding="utf-8"
        )
        suite = base / "suite.yaml"
        suite.write_text(
            "profile: foundation\ncases:\n"
            "- id: canonical-hashes\n  type: canonical\n"
            "  document: fixtures/canonical-hash-vectors.json\n",
            encoding="utf-8",
        )
        out = base / "result.json"
        with redirect_stdout(io.StringIO()):
            command_conformance(argparse.Namespace(suite=str(suite), out=str(out)))
        return bool(load_data(out)["passed"])


def _gate():
    return _flat("hash_release_gate", REFERENCE / "release-gate.py")


def _drive_gate_contract_copies(mode):
    """The byte-identical governed copies, recomputed per file."""
    gate = _gate()

    def run():
        del gate.failures[:]
        gate.check_governed_contract_copies()
        return not gate.failures

    if mode == "valid":
        return run()
    original = dict(gate.GOVERNED_CONTRACT_COPIES)
    try:
        name = next(iter(original))
        # A copy that is not byte-identical: recomputing per file is the only way
        # to notice, which is exactly the responsibility this site declares.
        gate.GOVERNED_CONTRACT_COPIES = {
            **original,
            name: list(original[name]) + ["reference/foundation/src/obds_ref/compiler.py"],
        }
        return run()
    finally:
        gate.GOVERNED_CONTRACT_COPIES = original
        del gate.failures[:]


def _drive_view_hash(collection_key, item_hash_key, view_hash_key, which):
    def driver(mode):
        assembler = _flat(f"hash_assembler_{which}", CA_ROOT / "assemble_context.py")
        compiled = load_data(CA_ROOT / "examples" / "compiled-social-copy-global-en.json")
        index = copy.deepcopy(load_data(CA_ROOT / "examples" / "search-index.json"))
        chapters = copy.deepcopy(load_data(CA_ROOT / "examples" / "reasoning-chapters.json"))
        request = load_data(CA_ROOT / "examples" / "assembly-request-create.yaml")
        view = index if which == "index" else chapters
        if mode != "valid":
            if item_hash_key:
                view[collection_key][0]["label" if which == "index" else "title"] = "tampered"
            else:
                view[view_hash_key] = "sha256:" + "0" * 64
        if mode == "reseal" and item_hash_key:
            item = view[collection_key][0]
            item.pop(item_hash_key, None)
            item[item_hash_key] = sha256_id(item)
            view.pop(view_hash_key, None)
            view[view_hash_key] = sha256_id(view)
        try:
            assembler.assemble(compiled, index, chapters, request)
            return True
        except (ValueError, KeyError):
            return False

    return driver


def _drive_view_builder_manifest(package_dir):
    """The same boundary in each package that ships a view builder."""

    def driver(mode):
        builder = _flat(f"hash_build_views_{package_dir.name.replace('-', '_')}", package_dir / "build_views.py")
        manifest = copy.deepcopy(load_data(package_dir / "examples" / "manifest.yaml"))
        chapter_map = load_data(package_dir / "examples" / "chapter-map.yaml")
        if mode != "valid":
            manifest["elements"][0]["annotations"] = ["tampered"]
        if mode == "reseal":
            manifest["approval"]["contentHash"] = manifest_content_hash(manifest)
        try:
            builder.build_views(manifest, chapter_map)
            return True
        except (ValueError, KeyError):
            return False

    return driver


def _review_fixture():
    reviewer = _flat("hash_reviewer_sites", CA_ROOT / "validate_review.py")
    compiled = load_data(CA_ROOT / "examples" / "compiled-marketing-review-global-en.json")
    package = copy.deepcopy(load_data(CA_ROOT / "examples" / "model-input-review.json"))
    review = copy.deepcopy(load_data(CA_ROOT / "examples" / "review-result-valid.json"))
    return reviewer, compiled, package, review


def _run_review(reviewer, compiled, package, review):
    try:
        return reviewer.validate_review(compiled, package, review) is True
    except (ValueError, KeyError):
        return False


def _drive_review_compiled_context_hash(mode):
    """The package names the artefact the review was derived from.

    The package is resealed in both mutating modes so its own `assemblyHash`
    site cannot answer for this one.
    """
    reviewer, compiled, package, review = _review_fixture()
    if mode != "valid":
        package["sources"] = {**package["sources"], "compiledContextHash": "sha256:" + "0" * 64}
        _reseal_package(package)
    return _run_review(reviewer, compiled, package, review)


def _drive_review_assembly_hash(mode):
    """The package's own seal: selection cannot move under it."""
    reviewer, compiled, package, review = _review_fixture()
    if mode != "valid":
        # F3 now independently rejects a smuggled selection. Change metadata
        # here to isolate the assemblyHash gate rather than test two gates.
        package["assembledAt"] = "2099-01-01T00:00:00Z"
    if mode == "reseal":
        _reseal_package(package)
    return _run_review(reviewer, compiled, package, review)


def _drive_review_model_input_hash(mode):
    """The declared model input is the one the package's slots render.

    Resealing here means recomputing the package's `assemblyHash` and the
    review's `reviewHash` around the *stale* `modelInputHash`, which is exactly
    what a caller holding both documents would do. It must still fail, because
    the hash is reproduced from `slots`, not compared between two claims.
    """
    reviewer, compiled, package, review = _review_fixture()
    if mode != "valid":
        package["slots"] = {**package["slots"], "taskInput": "a different governed request"}
        # Resealed in both mutating modes: the package's own seal site must not
        # answer for the model input site.
        _reseal_package(package)
    if mode == "reseal":
        review["reviewHash"] = sha256_id({k: v for k, v in review.items() if k != "reviewHash"})
    return _run_review(reviewer, compiled, package, review)


def _drive_review_review_hash(mode):
    """The review's own seal over its decision and findings."""
    reviewer, compiled, package, review = _review_fixture()
    if mode != "valid":
        review["decision"] = "pass" if review["decision"] != "pass" else "pass_with_suggestions"
    if mode == "reseal":
        review["reviewHash"] = sha256_id({k: v for k, v in review.items() if k != "reviewHash"})
    return _run_review(reviewer, compiled, package, review)


def _drive_cli_artefact_hash(mode):
    """The CLI gate both CLI executors call."""
    from obds_ref.cli import _compiled_context_errors

    artefact = copy.deepcopy(_probe_artefact())
    if mode != "valid":
        artefact["slots"] = {**artefact["slots"], "hardBoundaries": "tampered"}
    if mode == "reseal":
        artefact["artifactHash"] = artefact_hash(artefact)
    return not _compiled_context_errors(artefact)


def _drive_conformance_artefact_hash(mode):
    """The declared hash conformance case, run through the conformance runner.

    Driven by reimplementing the comparison, this proved nothing about
    `command_conformance`. It builds a one-case suite over a copy of the fixture
    and runs the real command, so the case that fails is the declared one.
    """
    import argparse
    import io
    import json
    import tempfile
    from contextlib import redirect_stdout

    from obds_ref.cli import command_conformance

    fixtures = PACKAGE_ROOT / "reference" / "foundation" / "fixtures"
    fixture = copy.deepcopy(load_data(fixtures / "canonical-hash-vectors.json"))
    if mode != "valid":
        artefact = fixture["artefact"]["input"]
        artefact["slots"] = {**artefact["slots"], "hardBoundaries": "tampered"}
    if mode == "reseal":
        # The caller recomputed the artefact's own seal. The case compares the
        # *declared expected* hash, which names the original payload, so this
        # must still fail.
        fixture["artefact"]["input"]["artifactHash"] = artefact_hash(fixture["artefact"]["input"])

    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        (base / "fixtures").mkdir()
        (base / "fixtures" / "canonical-hash-vectors.json").write_text(
            json.dumps(fixture, ensure_ascii=False), encoding="utf-8"
        )
        suite = base / "suite.yaml"
        suite.write_text(
            "profile: foundation\ncases:\n"
            "- id: canonical-hashes\n  type: canonical\n"
            "  document: fixtures/canonical-hash-vectors.json\n",
            encoding="utf-8",
        )
        out = base / "result.json"
        with redirect_stdout(io.StringIO()):
            command_conformance(argparse.Namespace(suite=str(suite), out=str(out)))
        return bool(load_data(out)["passed"])


def _gate():
    return _flat("hash_release_gate", REFERENCE / "release-gate.py")


def _drive_gate_contract_copies(mode):
    """The byte-identical governed copies, recomputed per file."""
    gate = _gate()

    def run():
        del gate.failures[:]
        gate.check_governed_contract_copies()
        return not gate.failures

    if mode == "valid":
        return run()
    original = dict(gate.GOVERNED_CONTRACT_COPIES)
    try:
        name = next(iter(original))
        # A copy that is not byte-identical: recomputing per file is the only way
        # to notice, which is exactly the responsibility this site declares.
        gate.GOVERNED_CONTRACT_COPIES = {
            **original,
            name: list(original[name]) + ["reference/foundation/src/obds_ref/compiler.py"],
        }
        return run()
    finally:
        gate.GOVERNED_CONTRACT_COPIES = original
        del gate.failures[:]


def _drive_gate_manifest(mode):
    """Every packaged file's digest, recomputed from the file on disk.

    Driven through `check_manifest` itself, over a manifest this driver hands it.
    Reimplementing the comparison here proved nothing about the gate.
    """
    gate = _gate()
    manifest = copy.deepcopy(load_data(PACKAGE_ROOT / "PACKAGE-MANIFEST.json"))
    if mode != "valid":
        entry = next(
            item for item in manifest["files"] if gate.manifest_path(item["path"]).is_file()
        )
        entry["sha256"] = "sha256:" + "0" * 64
    del gate.failures[:]
    gate.check_manifest(manifest)
    hit = [message for message in gate.failures if "sha256 mismatch" in message or "differs" in message]
    del gate.failures[:]
    return not hit


# Keyed by call site, not by hash name. `reference/foundation/src/obds_ref/runtime.py::run_with_model::artifactHash`
# and `reference/context-assembly/validate_review.py::validate_review::artifactHash` are two
# responsibilities and two proofs.
DRIVERS = {
    "reference/foundation/src/obds_ref/compiler.py::validate_manifest::contentHash": (_drive_manifest_approval_compiler, "reseal-accepted"),
    "reference/foundation/src/obds_ref/compiler.py::build_target::contentHash": (_drive_manifest_approval_plan_binding, "reseal-accepted"),
    "reference/context-assembly/build_views.py::build_views::contentHash":
        (_drive_view_builder_manifest(CA_ROOT), "reseal-accepted"),
    "reference/context-delivery/build_views.py::build_views::contentHash":
        (_drive_view_builder_manifest(CD_ROOT), "reseal-accepted"),
    "reference/context-assembly/assemble_context.py::_validate_resolution_manifest::contentHash":
        (_drive_manifest_approval_resolution_snapshot, "reseal-rejected"),
    "reference/foundation/src/obds_ref/compiler.py::validate_manifest::schemaHash": (_drive_value_contract_schema_hash, "reseal-rejected"),
    "reference/foundation/src/obds_ref/compiler.py::validate_manifest::shapeHash": (_drive_value_contract_shape_hash, "reseal-accepted"),
    "reference/foundation/src/obds_ref/runtime.py::run_with_model::artifactHash": (_drive_artefact_hash_runtime, "reseal-accepted"),
    "reference/foundation/src/obds_ref/runtime.py::run_assembled_with_model::artifactHash": (_drive_artefact_hash_assembled_runtime, "reseal-accepted"),
    "reference/context-assembly/assemble_context.py::_validate_compiled_context::artifactHash": (_drive_artefact_hash_assembly, "reseal-accepted"),
    "reference/context-assembly/validate_review.py::validate_review::artifactHash": (_drive_artefact_hash_review, "reseal-accepted"),
    "reference/context-assembly/validate_review.py::validate_review::compiledContextHash": (_drive_review_compiled_context_hash, "reseal-rejected"),
    "reference/context-assembly/validate_review.py::validate_review::assemblyHash": (_drive_review_assembly_hash, "reseal-accepted"),
    "reference/context-assembly/validate_review.py::validate_review::modelInputHash": (_drive_review_model_input_hash, "reseal-rejected"),
    "reference/context-assembly/validate_review.py::validate_review::reviewHash": (_drive_review_review_hash, "reseal-accepted"),
    "reference/foundation/src/obds_ref/cli.py::_compiled_context_errors::artifactHash": (_drive_cli_artefact_hash, "reseal-accepted"),
    "reference/foundation/src/obds_ref/cli.py::command_conformance::artifactHash": (_drive_conformance_artefact_hash, "reseal-rejected"),
    "reference/foundation/src/obds_ref/runtime.py::run_assembled_with_model::compiledContextHash": (_drive_package_compiled_context_hash, "reseal-rejected"),
    "reference/foundation/src/obds_ref/runtime.py::run_assembled_with_model::modelInputHash": (_drive_package_model_input_hash, "reseal-accepted"),
    "reference/foundation/src/obds_ref/runtime.py::run_assembled_with_model::assemblyHash": (_drive_package_assembly_hash, "reseal-accepted"),
    "reference/context-assembly/assemble_context.py::assemble::cardHash": (_drive_view_hash("cards", "cardHash", "indexHash", "index"), "reseal-accepted"),
    "reference/context-assembly/assemble_context.py::assemble::indexHash": (_drive_view_hash("cards", None, "indexHash", "index"), "reseal-rejected"),
    "reference/context-assembly/assemble_context.py::assemble::chapterHash": (_drive_view_hash("chapters", "chapterHash", "chapterSetHash", "chapters"), "reseal-accepted"),
    "reference/context-assembly/assemble_context.py::assemble::chapterSetHash": (_drive_view_hash("chapters", None, "chapterSetHash", "chapters"), "reseal-rejected"),
    "reference/release-gate.py::check_governed_contract_copies::*": (_drive_gate_contract_copies, "reseal-rejected"),
}


def drive(site_id, mode):
    """Run one registered driver. The subprocess entry point uses this."""
    driver, _ = DRIVERS[site_id]
    return driver(mode)




def _drive_generation_boundary(boundary):
    def driver(mode):
        import tempfile
        from obds_ref.compiler import build_all
        from obds_ref.generation import _read_report, _report_hash, generation_relative, load_generation_artifact
        from obds_ref.governed_io import save_json, save_yaml, ValidationFailure
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest, plan = _example('foundation-minimal')
            report = build_all(manifest, plan, output_dir=root)
            generation_id = report['generationId']
            report_path = root/generation_relative(generation_id)/'build-report.yaml'
            artifact_path = root/report['targets'][0]['artifactRef']
            if mode != 'valid':
                if boundary == 'report':
                    report['builtAt'] = '2099-01-01T00:00:00Z'
                    if mode == 'reseal': report['reportHash'] = _report_hash(report)
                elif boundary == 'generation':
                    report['planHash'] = 'sha256:'+'0'*64
                    report['reportHash'] = _report_hash(report)
                else:
                    artifact = load_data(artifact_path)
                    artifact['slots']['factGrounding'] = 'tampered'
                    artifact['artifactHash'] = artefact_hash(artifact)
                    save_json(artifact_path, artifact)
                    if mode == 'reseal':
                        report['targets'][0]['artifactHash'] = artifact['artifactHash']
                        report['reportHash'] = _report_hash(report)
                save_yaml(report_path, report)
            try:
                if boundary == 'artifact':
                    load_generation_artifact(root, generation_id, plan['targets'][0]['id'])
                else:
                    _read_report(root, generation_id)
                return True
            except ValidationFailure:
                return False
    return driver


DRIVERS.update({
    'reference/foundation/src/obds_ref/generation.py::_read_report::reportHash': (_drive_generation_boundary('report'), 'reseal-accepted'),
    'reference/foundation/src/obds_ref/generation.py::_read_report::generationId': (_drive_generation_boundary('generation'), 'reseal-rejected'),
    'reference/foundation/src/obds_ref/generation.py::load_generation_artifact::artifactHash': (_drive_generation_boundary('artifact'), 'reseal-accepted'),
})


if __name__ == "__main__":  # pragma: no cover - exercised through subprocesses
    print("ACCEPTED" if drive(sys.argv[1], sys.argv[2]) else "REFUSED")
