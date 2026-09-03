"""Systemic mechanism 2 — a received hash is not proof.

Five of the nineteen defects eleven review rounds produced had one shape: a
governed hash was copied where it should have been reproduced. The view builders
published `approval.contentHash` without recomputing it. The resolution snapshot
compared its own declared value against the compiled context. The derived views
were never checked against `cardHash` or `chapterHash` at all. Each was found by
someone happening to look at that one boundary.

This closes the shape instead. Every hash boundary in Classes A–E is enumerated
in `systemic_surface.HASH_VERIFICATION_SITES`, and each is driven through the
same three cases:

    valid payload, correct hash                     → accept
    mutated payload, old hash                       → reject
    mutated payload, hash recomputed by the caller  → reject, because the
                                                      binding one level up broke

The third case is the one that matters. A caller who can edit a payload can also
recompute the hash printed beside it, so a boundary that only compares a
self-declared hash proves nothing. What has to hold is the *chain*: the hash a
payload carries must be reproducible from the payload, and the payload must be
the one something upstream named.
"""

from __future__ import annotations

import ast
import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from obds_ref.canonical import (
    artefact_hash,
    manifest_content_hash,
    sha256_id,
    text_hash,
    value_shape_hash,
)
from obds_ref.compiler import build_target, load_data, validate_manifest, validate_plan
from obds_ref.model_input import render_model_input
from obds_ref.runtime import run_assembled_with_model, run_with_model
from hash_drivers import DRIVERS
from systemic_surface import (
    COMPARISON_ONLY,
    GOVERNED_HASH_FIELDS,
    HASH_CALL_SITES,
    HASH_PRODUCING_CALLS,
    PACKAGE_ROOT,
    REFERENCE,
    VERIFIER,
)



def _discover_hash_call_sites():
    """Every function in the governed implementation that touches a hash.

    Keyed `path::function::field`, or `::*` for a function that produces or
    reproduces a hash without naming a governed field. Comment lines are
    stripped: a hash named only in prose is not a call site.

    Test modules are excluded by construction, the same way mechanism 4 excludes
    them: a test is not a governed hash consumer, and the consumers a test drives
    are the ones registered here.
    """
    discovered = set()
    for root in ("reference", "tools"):
        for path in sorted((PACKAGE_ROOT / root).rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            relative = path.relative_to(PACKAGE_ROOT).as_posix()
            if "/tests/" in relative or path.name.startswith("test_"):
                continue
            source = path.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source)
            except SyntaxError:  # pragma: no cover - the release ships none
                continue
            lines = source.splitlines()
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                body = "\n".join(lines[node.lineno - 1 : node.end_lineno])
                code = "\n".join(l for l in body.splitlines() if not l.strip().startswith("#"))
                fields = sorted({field for field in GOVERNED_HASH_FIELDS if field in code})
                if fields:
                    for field in fields:
                        discovered.add(f"{relative}::{node.name}::{field}")
                elif any(call in code for call in HASH_PRODUCING_CALLS):
                    discovered.add(f"{relative}::{node.name}::*")
    return discovered


def test_mechanism_2_every_hash_call_site_is_classified():
    """A hash use nobody classified is a hash use nobody proved.

    This is the enumeration guard. It replaced a scan for hash *field names* in
    the corpus, which registered `modelInputHash` once and let one runtime driver
    stand in for every other function comparing that field — including the one in
    `validate_review` that reproduced nothing.
    """
    discovered = _discover_hash_call_sites()
    registered = set(HASH_CALL_SITES)
    unclassified = sorted(discovered - registered)
    assert not unclassified, (
        "these functions consume or produce a governed hash and are in no surface "
        "registry, so nothing proves what they verify:\n  " + "\n  ".join(unclassified)
    )
    stale = sorted(registered - discovered)
    assert not stale, f"registry entries that no longer exist in the release: {stale}"


def test_mechanism_2_every_verifier_site_has_a_driver():
    """One verification responsibility, one directly exercised proof."""
    verifiers = {key for key, site in HASH_CALL_SITES.items() if site["role"] == VERIFIER}
    assert verifiers == set(DRIVERS), (
        f"verifier sites without a driver: {sorted(verifiers - set(DRIVERS))}; "
        f"drivers without a verifier site: {sorted(set(DRIVERS) - verifiers)}"
    )
    for key in verifiers:
        assert HASH_CALL_SITES[key].get("reproduces"), f"{key}: no reproduction declared"


def test_mechanism_2_every_comparison_only_site_names_a_verified_boundary():
    """A comparison is safe because something else already reproduced the value.

    Naming that boundary is the claim, and the claim has to resolve: the named
    site must exist and must itself be a verifier with a driver. A comment
    asserting "this was checked upstream" is not a proof of anything.
    """
    for key, site in HASH_CALL_SITES.items():
        if site["role"] != COMPARISON_ONLY:
            continue
        after = site.get("after")
        assert after, f"{key}: comparison-only with no prior verified boundary named"
        assert after in HASH_CALL_SITES, f"{key}: names {after}, which is not a registered site"
        assert HASH_CALL_SITES[after]["role"] == VERIFIER, (
            f"{key}: names {after}, which is not a verifier"
        )
        assert after in DRIVERS, f"{key}: names {after}, which no driver exercises"


def test_mechanism_2_every_registered_site_states_a_role_and_a_reason():
    roles = {"producer", "verifier", "comparison-only", "internal", "non-governed",
             "release-bookkeeping"}
    for key, site in HASH_CALL_SITES.items():
        assert site.get("role") in roles, f"{key}: unknown role {site.get('role')!r}"
        assert site.get("note"), f"{key}: no reason stated"


@pytest.mark.parametrize("site_id", sorted(DRIVERS))
def test_mechanism_2_a_hash_is_reproduced_not_trusted(site_id):
    """Three cases per boundary: valid, tampered, and tampered-then-resealed.

    `reseal-rejected` is the strong form: the caller recomputed the hash the
    payload carries and the boundary still refuses, because something upstream
    named the original payload. `reseal-accepted` is the honest weaker form: the
    hash is a self-claim with no upstream binding at that boundary, so resealing
    it legitimately produces a different, valid document — and the binding is
    proven at the site that *does* have an upstream, which the registry names.
    """
    driver, reseal_expectation = DRIVERS[site_id]

    assert driver("valid") is True, f"{site_id}: the untouched fixture is refused"
    assert driver("tamper") is False, (
        f"{site_id}: a mutated payload was accepted under its old hash — the hash was "
        "trusted rather than reproduced"
    )
    resealed = driver("reseal")
    if reseal_expectation == "reseal-rejected":
        assert resealed is False, (
            f"{site_id}: recomputing the hash made a mutated payload acceptable, so this "
            "boundary verifies only a self-claim"
        )
    else:
        assert resealed is True, (
            f"{site_id}: the registry says this boundary has no upstream binding, so a "
            "resealed payload is a different valid document and must be accepted"
        )


def test_mechanism_2_at_least_one_boundary_binds_upstream_for_every_payload():
    """Every governed payload must cross at least one boundary it cannot reseal past.

    `reseal-accepted` is honest at a self-claim boundary, but it cannot be true of
    every boundary a payload crosses — then editing and resealing is unconstrained.
    """
    payloads = {
        "manifest": [
            "reference/foundation/src/obds_ref/compiler.py::validate_manifest::contentHash",
            "reference/foundation/src/obds_ref/compiler.py::build_target::contentHash",
            "reference/context-assembly/build_views.py::build_views::contentHash",
            "reference/context-assembly/assemble_context.py::_validate_resolution_manifest::contentHash",
        ],
        "compiled artefact": [
            "reference/foundation/src/obds_ref/runtime.py::run_with_model::artifactHash",
            "reference/context-assembly/assemble_context.py::_validate_compiled_context::artifactHash",
            "reference/foundation/src/obds_ref/runtime.py::run_assembled_with_model::compiledContextHash",
            "reference/context-assembly/validate_review.py::validate_review::artifactHash",
        ],
        "model input package": [
            "reference/foundation/src/obds_ref/runtime.py::run_assembled_with_model::compiledContextHash",
            "reference/foundation/src/obds_ref/runtime.py::run_assembled_with_model::modelInputHash",
            "reference/foundation/src/obds_ref/runtime.py::run_assembled_with_model::assemblyHash",
            "reference/context-assembly/validate_review.py::validate_review::modelInputHash",
            "reference/context-assembly/validate_review.py::validate_review::assemblyHash",
        ],
        "derived views": [
            "reference/context-assembly/assemble_context.py::assemble::cardHash",
            "reference/context-assembly/assemble_context.py::assemble::indexHash",
            "reference/context-assembly/assemble_context.py::assemble::chapterHash",
            "reference/context-assembly/assemble_context.py::assemble::chapterSetHash",
        ],
        "review result": [
            "reference/context-assembly/validate_review.py::validate_review::reviewHash",
            "reference/context-assembly/validate_review.py::validate_review::modelInputHash",
        ],
    }
    for payload, sites in payloads.items():
        binding = [site for site in sites if DRIVERS[site][1] == "reseal-rejected"]
        assert binding, (
            f"{payload}: every boundary it crosses accepts a resealed payload, so nothing "
            "constrains editing it"
        )


# --------------------------------------------------------------------------
# The proof that a driver proves anything.
#
# `test_mechanism_2_every_verifier_site_has_a_driver` asserts a site *has* a
# driver. It cannot see whether the driver reaches that site: two runtime
# `artifactHash` entries shared one driver that called only `run_with_model`, so
# a registered site was never exercised at all and the registry still reported
# full coverage. Others were answered by a different gate firing first.
#
# So the claim is tested rather than declared. For each verifier site the
# registry names the exact source of its gate. The check below neutralises that
# one gate in a copy of the release, runs that one driver against the copy in a
# subprocess, and requires the driver to stop refusing. A driver that does not
# reach its site does not notice, and fails here.
# --------------------------------------------------------------------------

import os
import shutil
import subprocess
import tempfile


COPIED_FOR_PROOF = ("reference", "schemas", "value-schemas", "examples", "tools")


@pytest.fixture(scope="module")
def neutralisation_workspace():
    """A writable copy of the release, so one gate at a time can be removed."""
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / "obds"
        root.mkdir()
        for name in COPIED_FOR_PROOF:
            source = PACKAGE_ROOT / name
            if source.is_dir():
                shutil.copytree(
                    source, root / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
                )
        for name in ("PACKAGE-MANIFEST.json", "VERSION"):
            if (PACKAGE_ROOT / name).is_file():
                shutil.copy2(PACKAGE_ROOT / name, root / name)
        yield root


def _function_range(source: str, name: str):
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node.lineno, node.end_lineno
    return None


def _run_driver(root: Path, site_id: str, mode: str) -> str:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        [
            str(root / "reference" / "foundation" / "src"),
            str(root / "reference" / "foundation" / "tests"),
        ]
    )
    environment.pop("PYTHONDONTWRITEBYTECODE", None)
    completed = subprocess.run(
        [sys.executable, str(root / "reference" / "foundation" / "tests" / "hash_drivers.py"), site_id, mode],
        capture_output=True,
        text=True,
        env=environment,
        cwd=str(root),
    )
    assert completed.returncode == 0, (
        f"{site_id}: the driver could not run against the copied release:\n{completed.stderr[-2000:]}"
    )
    return completed.stdout.strip().splitlines()[-1]


VERIFIER_SITES = sorted(key for key, site in HASH_CALL_SITES.items() if site["role"] == VERIFIER)


@pytest.mark.parametrize("site_id", VERIFIER_SITES)
def test_mechanism_2_the_declared_gate_is_the_one_the_site_actually_uses(site_id):
    """The registered gate must be that function's, and only that function's."""
    site = HASH_CALL_SITES[site_id]
    relative, function_name, _ = site_id.split("::")
    source = (PACKAGE_ROOT / relative).read_text(encoding="utf-8")
    span = _function_range(source, function_name)
    assert span, f"{site_id}: {function_name} does not exist in {relative}"
    body = "\n".join(source.splitlines()[span[0] - 1 : span[1]])
    assert body.count(site["gate"]) == 1, (
        f"{site_id}: the declared gate does not appear exactly once inside {function_name}"
    )


@pytest.mark.parametrize("site_id", VERIFIER_SITES)
def test_mechanism_2_neutralising_the_gate_turns_its_own_driver_red(site_id, neutralisation_workspace):
    """Remove this site's gate, and this site's driver must stop refusing.

    Without this, a driver registered against a site it never calls reports the
    same green as one that does.
    """
    site = HASH_CALL_SITES[site_id]
    relative, function_name, _ = site_id.split("::")
    target = neutralisation_workspace / relative
    original = target.read_text(encoding="utf-8")

    # Patched inside this function's line range only. Two runtime entry points
    # carry a byte-identical seal check, and replacing it file-wide would remove
    # both gates — which is how one driver could stand in for the other in the
    # first place.
    span = _function_range(original, function_name)
    assert span, f"{site_id}: {function_name} not found in the copied release"
    lines = original.splitlines(keepends=True)
    before, body, after = lines[: span[0] - 1], lines[span[0] - 1 : span[1]], lines[span[1] :]
    joined = "".join(body)
    assert joined.count(site["gate"]) == 1, f"{site_id}: gate not found in the copied release"
    patched = "".join(before) + joined.replace(site["gate"], site["neutralised"]) + "".join(after)

    assert _run_driver(neutralisation_workspace, site_id, "tamper") == "REFUSED", (
        f"{site_id}: the driver does not refuse a tampered payload even before the gate is removed"
    )
    try:
        target.write_text(patched, encoding="utf-8")
        result = _run_driver(neutralisation_workspace, site_id, "tamper")
    finally:
        target.write_text(original, encoding="utf-8")
    assert result == "ACCEPTED", (
        f"{site_id}: its gate was removed and its driver still refused, so the driver is not "
        "exercising this site — something else is answering for it"
    )
