#!/usr/bin/env python3
"""Build the OBDS release package from the repository.

One file list drives everything: `PACKAGE-MANIFEST.json`, the release archive
and the published snapshot under `spec/<version>/`. The manifest therefore
cannot fall behind the package, which is what `reference/release-gate.py`
verifies on every run.

The repository keeps each public schema at the path its `$id` resolves to,
`schemas/1.0.0/` and `value-schemas/1.0.0/`. The release archive flattens them
to `schemas/` and `value-schemas/`, exactly as 1.0.0, 1.0.1 and 1.0.2 shipped
them. This script performs that mapping; the suite and the gate read either
layout.

Usage, from the repository root:

    python3 tools/build-release.py                 # manifest, metadata, archive, snapshot
    python3 tools/build-release.py --run-tests     # also regenerate the test output first
    python3 tools/build-release.py --manifest-only # only PACKAGE-MANIFEST.json and metadata

Generated caches and shipped junk are never included.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import re
import shutil
import subprocess
import sys
import zipfile
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]

PACKAGE_ROOT_FILES = (
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "LICENSE.md",
    "NOTICE",
    "README.md",
    "TRADEMARKS.md",
    "requirements.txt",
)
# One definition, in the gate, for the same reason `contract_directories()` and
# the suite hash live there: the gate ships inside the archive and this script
# does not, so a reader of the package can see what the package is. Two copies of
# a directory list are two chances to be wrong about it, which is exactly how
# `tools/` came to be named by the surface registries and left out of the
# 3.0.0 archive.
def package_dirs() -> tuple[str, ...]:
    return tuple(_gate().PACKAGE_DIRS)

# Repository layout -> archive layout. Derived, not listed: see
# `contract_directories()` in reference/release-gate.py, which owns the
# definition for the same reason it owns the suite hash. This script kept its
# own copy of that list, both copies went stale at 1.1.0, and a 3.0.0 archive
# would have shipped without the contracts 3.0.0 publishes.
def schema_dirs() -> dict[str, str]:
    return {
        directory.relative_to(ROOT).as_posix(): archive
        for directory, _, archive in _gate().contract_directories()
    }

CACHE_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox", ".eggs", "node_modules"}
CACHE_SUFFIXES = (".pyc", ".pyo")
JUNK_DIRS = {"__MACOSX", ".ipynb_checkpoints"}
JUNK_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
JUNK_SUFFIXES = (".swp", ".swo", ".orig", ".rej", ".bak", ".tmp", "~")

SUITE_ORDER = (
    "foundation",
    "context-delivery",
    "context-assembly",
    "design-space",
    "integration",
    "golden",
    "adversarial",
)

# Section 26 requires a conformance result to identify the implementation, the
# suite, the profile and the counts. These constants supply the first three;
# the counts come from the run.
IMPLEMENTATION = {
    "name": "org.openbranddefinition.reference-compiler",
    "version": "1.0.0",
    "language": "Python",
    "repository": "https://github.com/openbranddefinition/obds",
}

# Section 26 claims this release actually makes. Two, and no more.
#
# Phase A listed six. Four of them (context-delivery, context-assembly,
# visual-operations, composition) were evidenced by modules that are not the
# named implementation: reference/design-space/design_space_ref.py,
# reference/context-assembly/assemble_context.py and
# reference/context-delivery/build_views.py never import obds_ref. They were
# removed in 1.0.4. Do not re-add a profile without a declared suite for it.
FOUNDATION_PROFILE = {
    "id": "obds-foundation",
    "conformanceSection": "26.1",
    "basis": (
        "reference/foundation/conformance-suite.yaml declares `profile: foundation`. "
        "It is the only artefact in this package that names a conformance profile. "
        "Every declared case is executed by the release build and re-executed by "
        "reference/release-gate.py; the result is published as "
        "OBDS-<release>-FOUNDATION-CONFORMANCE.json."
    ),
    "declaredSuite": "reference/foundation/conformance-suite.yaml",
}

# Section 26.2 has no declared per-profile suite in this release, so the claim
# rests on named executed cases, one per requirement in the section's own list.
COMPILED_RUNTIME_PROFILE = {
    "id": "compiled-runtime",
    "conformanceSection": "26.2",
    "basis": (
        "No declared per-profile conformance suite exists for section 26.2 in "
        "this release, so this is not a claim of the form 'passed the official "
        "26.2 suite'. It is a claim that every requirement section 26.2 lists is "
        "implemented by the named reference compiler and exercised by a named "
        "executed case, enumerated in requirementsExercised. Defining a declared "
        "26.2 suite is Phase B work."
    ),
    # Section 26.2 evidence. Each requirement names one or more executed case
    # IDs, and reference/release-gate.py resolves every one of them against the
    # suite it actually ran: the case must exist, must have executed, must have
    # passed, and must not be reused to satisfy a second requirement. Before
    # 2.0.0 this array held prose and the gate only counted its length, so
    # fourteen invented strings passed the gate unchanged.
    "requirementsExercised": [
        {"requirement": "exact Build Plans",
         "cases": ["foundation/tests.test_obds_200::test_exact_build_plans_bind_one_manifest"]},
        {"requirement": "requiresDefined",
         "cases": ["foundation/tests.test_reference::test_required_unknown_fails_and_emits_no_artefact"]},
        {"requirement": "every required element present in the produced context",
         "cases": ["foundation/tests.test_obds_11::test_required_knowledge_element_reaches_the_artefact"]},
        {"requirement": "explicit context selection",
         "cases": ["foundation/tests.test_obds_200::test_explicit_context_selection_decides_slot_contents"]},
        {"requirement": "no artefact for a failed target",
         "cases": ["foundation/tests.test_examples::test_fail_closed_example_emits_no_context_and_calls_no_model"]},
        {"requirement": "canonical JSON artefacts",
         "cases": ["foundation/tests.test_obds_200::test_canonical_json_artefacts_are_written_canonically",
                   "foundation/tests.test_reference::test_canonical_json_normalises_nfc_and_line_endings"]},
        {"requirement": "reproducible hashes",
         "cases": ["foundation/tests.test_reference::test_simple_target_builds_and_hash_is_reproducible"]},
        {"requirement": "a governedResultHash that matches section 14.3a for the same manifest and Build Plan",
         "cases": ["foundation/tests.test_obds_11::test_governed_result_hash_matches_the_fixture",
                   "foundation/tests.test_obds_11::test_compiled_context_carries_the_governed_result_hash"]},
        {"requirement": "Foundation Check Registry v1",
         "cases": ["foundation/tests.test_obds_200::test_foundation_check_registry_v1_compiles_and_refuses"]},
        {"requirement": "exact target loading",
         "cases": ["foundation/tests.test_obds_200::test_exact_target_loading_builds_only_the_named_target",
                   "foundation/tests.test_reference::test_invalid_hash_no_call"]},
        {"requirement": "Runtime Decision Records",
         "cases": ["foundation/tests.test_reference::test_runtime_record_ndjson",
                   "foundation/tests.test_reference::test_assembly_failed_runtime_record_is_schema_valid"]},
        {"requirement": "zero instrumented model calls after failed build or blocking preflight",
         "cases": ["foundation/tests.test_reference::test_failed_build_means_no_model_call",
                   "foundation/tests.test_reference::test_blocking_preflight_means_no_model_call"]},
        {"requirement": "withheld output after blocking postflight",
         "cases": ["foundation/tests.test_reference::test_blocking_postflight_withholds_output"]},
        {"requirement": "per-slot token reporting",
         "cases": ["foundation/tests.test_obds_200::test_per_slot_token_reporting_is_the_sum_of_its_slots"]},
        # The six Semantic Closure requirements section 26.2 gained in 3.0.0.
        # Same rule as above: each names an executed case the gate resolves
        # against the run it performs itself.
        {"requirement": "the governed input contract at every governed reader",
         "cases": ["foundation/tests.test_obds_300_class_a::test_a1_every_governed_reader_is_the_one_governed_reader",
                   "foundation/tests.test_obds_300_class_a::test_a2_readers_agree_on_every_shipped_governed_document"]},
        {"requirement": "identity binding of the manifest triple wherever an artefact names a manifest",
         "cases": ["foundation/tests.test_obds_300_class_b::test_b2_one_content_hash_cannot_resolve_to_two_governed_identities",
                   "foundation/tests.test_obds_300_class_b::test_b1_a_shared_field_is_an_identity_position_in_every_artefact_that_carries_it"]},
        {"requirement": "two-stage validation of Foundation RULE checks",
         "cases": ["foundation/tests.test_obds_300_class_c::test_c10_a_deferred_literal_passes_the_stage_that_authors_it",
                   "foundation/tests.test_obds_300_class_c::test_c10_a_deferred_literal_is_still_refused_once_it_should_have_been_resolved"]},
        {"requirement": "exact task-input binding",
         "cases": ["foundation/tests.test_obds_300_class_c::test_c9_a_forged_rendered_task_input_never_reaches_the_model",
                   "foundation/tests.test_obds_300_class_c::test_c9_a_decoy_task_input_never_reaches_the_model"]},
        {"requirement": "contract validation of every governed runtime document before governed field use",
         "cases": ["foundation/tests.test_obds_300_systemic_executors::test_the_assembled_runtime_executes_the_model_input_package_contract[another kind]",
                   "foundation/tests.test_obds_300_systemic_executors::test_mechanism_4_no_executor_accepts_a_resealed_schema_invalid_artefact[missing required property-reference/foundation/src/obds_ref/cli.py::command_validate]"]},
        {"requirement": "governed hashes reproduced rather than declared",
         "cases": ["foundation/tests.test_obds_300_class_b::test_b2_a_resolution_snapshot_must_reproduce_its_approval_hash"]},
    ],
}

# Every suite the release executed, with no conformance claim attached. This is
# where context-delivery, context-assembly and design-space are reported now.
EXECUTED_SUITES_NOTE = (
    "Suites executed by reference/run_all.py, reported as coverage only. No "
    "conformance profile is claimed for context-delivery, context-assembly or "
    "design-space: those suites exercise reference/context-delivery/build_views.py, "
    "reference/context-assembly/assemble_context.py and "
    "reference/design-space/design_space_ref.py, none of which is the "
    "implementation named in `implementation`."
)

# The suite hash covers the published conformance suite: the runner, the seven
# suite directories and their fixtures. It excludes reference/foundation/src/,
# the implementation under test, which IMPLEMENTATION identifies instead. The
# definition lives in reference/release-gate.py because the gate ships inside
# the release archive and this script does not.

FOUNDATION_CLAIM_SCOPE = (
    "Result of the official OBDS Foundation Conformance Suite declared in "
    "reference/foundation/conformance-suite.yaml, profile `foundation`, "
    "executed against the reference implementation. Every declared case ran and "
    "passed; none was skipped or changed. This run is deliberately not added to "
    "the aggregate suiteCounts: 14 of its 15 cases exercise the same fixtures "
    "and examples as the pytest suites, so aggregating both would double-count "
    "the same coverage."
)

CLAIM_SCOPE = (
    "Result of the OBDS conformance runs for the exact release and suite hash "
    "named in this file, executed against the reference implementation named in "
    "`implementation`. Every required case ran; none was skipped, changed or "
    "expected to fail. `conformanceProfiles` lists only profiles this release "
    "can defend: `obds-foundation` because a declared conformance suite names "
    "that profile and every one of its cases passed, and `compiled-runtime` "
    "because every requirement section 26.2 lists names one or more executed "
    "cases in the `requirementsExercised` array of the `compiled-runtime` entry "
    "in `conformanceProfiles`, and the release gate resolves each of them "
    "against the suite it runs itself: the case must exist, must have passed "
    "and must not be reused for a second requirement. What the gate proves is "
    "that the named evidence really ran and really passed. That a case "
    "materially exercises the requirement it is attached to is an authoring "
    "judgement no name-resolving check can make, and it is claimed here rather "
    "than proven. No profile is claimed "
    "for context-delivery, context-assembly, visual-operations or composition; "
    "those suites are reported under `executedSuites` as coverage only, because "
    "they exercise modules other than the named implementation. This file is a "
    "suite result under section 26, not an independent certification and not a "
    "statement about any other implementation."
)


PRIOR_RELEASE = "3.0.3"


def _release_kind(release: str) -> str:
    """MAJOR, MINOR or PATCH, read off the version rather than asserted.

    1.1.0 shipped notes copied from 1.0.4 calling a MINOR release a maintenance
    release; 2.0.0 nearly shipped the same sentence over a MAJOR one. The word
    is derived here so it cannot be left behind by the next bump.
    """
    major, minor, patch = (int(part) for part in release.split("."))
    if minor == 0 and patch == 0:
        return "MAJOR"
    return "MINOR" if patch == 0 else "PATCH"


def _english_list(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def release_notes(release: str, counts: dict[str, int]) -> list[str]:
    """The TEST-RESULT notes, generated for this release rather than carried.

    OBDS 1.1.0 shipped notes copied from 1.0.4: they described a hygiene release
    with no normative contract change, claimed byte-identity only through 1.0.3,
    reported a case count the same file contradicted, and named a file that did
    not exist. Nothing checked them because nothing generated them.
    """
    total = sum(counts.values())
    record = load(ROOT / "publication-record.json")
    entry = record.get("releases", {}).get(release, {})
    note = entry.get("note")
    if not note:
        raise SystemExit(
            f"publication-record.json has no releases.{release}.note; the "
            "release kind is stated there and derived here, not written twice"
        )
    published = sorted(
        (v for v in record.get("releases", {}) if v != release),
        key=lambda v: tuple(int(part) for part in v.split(".")),
    )
    surface = _english_list(published) if published else "no earlier release"
    return [
        f"OBDS {release} is a {_release_kind(release)} release: {note}.",
        f"The public schema surface is byte-identical to OBDS {surface}.",
        "The specification and the documentation are licensed under CC BY 4.0. "
        "The schemas, release metadata, reference implementation, conformance "
        "suite and examples are licensed under the Apache License 2.0.",
        "This file carries the section 26 identifiers: implementation, "
        "obdsVersion, suiteHash, conformanceProfiles, the counts and "
        "requiredCasesSkippedOrChanged.",
        "suiteHash covers the suite runner and the seven suite directories with "
        "their fixtures. It excludes reference/foundation/src/, which is the "
        "implementation under test and is identified by the implementation field.",
        "A profile is listed under conformanceProfiles because the executed "
        "suite contains cases for that conformance section. It is evidence for "
        "the section, not an independent certification.",
        f"This release runs {total} cases, "
        + ", ".join(f"{name} {count}" for name, count in sorted(counts.items()))
        + ".",
        "The result is reproducible in two layouts: the repository, where the "
        "public schemas sit at schemas/1.0.0/, and an unpacked release archive, "
        "where they are flat.",
        "Node.js is required to execute the cross-language canonicalisation "
        f"tests. See OBDS-{release}-TEST-REQUIREMENTS.md.",
    ]


def version() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def excluded(path: Path) -> bool:
    parts = path.relative_to(ROOT).parts
    if any(p in CACHE_DIRS or p in JUNK_DIRS or p.startswith(".venv") for p in parts):
        return True
    if any(p.endswith(".egg-info") for p in parts):
        return True
    return path.name in JUNK_NAMES or path.name.endswith(CACHE_SUFFIXES + JUNK_SUFFIXES)


def package_files(release: str) -> list[tuple[str, Path]]:
    """(archive path, source path) for every file the package ships, sorted."""
    pairs: list[tuple[str, Path]] = []
    for name in PACKAGE_ROOT_FILES:
        source = ROOT / name
        if not source.is_file():
            sys.exit(f"missing package file {name}")
        pairs.append((name, source))
    for source in sorted(ROOT.glob(f"OBDS-*{release}*")):
        if source.is_file() and not excluded(source):
            pairs.append((source.name, source))
    for directory in package_dirs():
        base = ROOT / directory
        if not base.is_dir():
            sys.exit(f"missing package directory {directory}/")
        for source in sorted(base.rglob("*")):
            if source.is_file() and not excluded(source):
                pairs.append((source.relative_to(ROOT).as_posix(), source))
    discovered = schema_dirs()
    if not discovered:
        sys.exit("no published contract directory found under schemas/ or value-schemas/")
    for repo_dir, archive_dir in sorted(discovered.items()):
        base = ROOT / repo_dir
        if not base.is_dir():
            sys.exit(f"missing schema directory {repo_dir}/")
        for source in sorted(base.glob("*.json")):
            pairs.append((f"{archive_dir}/{source.name}", source))
    seen = {archive for archive, _ in pairs}
    if len(seen) != len(pairs):
        sys.exit("duplicate archive path in the package file list")
    return sorted(pairs)


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def run_tests(release: str) -> None:
    print("running the conformance suite")
    proc = subprocess.run(
        [sys.executable, "reference/run_all.py"], cwd=ROOT, text=True, capture_output=True
    )
    sys.stdout.write(proc.stdout)
    if proc.returncode:
        sys.stderr.write(proc.stderr)
        sys.exit("conformance suite failed; not building a release")
    (ROOT / f"OBDS-{release}-TEST-OUTPUT.txt").write_text(proc.stdout, encoding="utf-8")
    print(f"wrote OBDS-{release}-TEST-OUTPUT.txt")


def run_official_foundation_conformance(release: str) -> dict:
    """Execute the official declared Foundation conformance suite and publish it.

    Section 26 clause 1 requires passing every required case in the official
    Conformance Suite for the named profile. This run is deliberately NOT added
    to `suiteCounts`: 14 of its 15 cases exercise the same fixtures and examples
    as the pytest suites, so adding them would double-count the same coverage.
    It is published as its own result with its own profile, counts and suite
    hash.
    """
    print("running the official Foundation conformance suite")
    src = ROOT / "reference" / "foundation" / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from obds_ref.cli import command_conformance

    path = ROOT / f"OBDS-{release}-FOUNDATION-CONFORMANCE.json"
    args = SimpleNamespace(suite=str(ROOT / "reference/foundation/conformance-suite.yaml"),
                           out=str(path))
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        command_conformance(args)
    result = load(path)
    if result.get("failedCount") or not result.get("passed"):
        failing = ", ".join(c["id"] for c in result.get("cases", []) if not c.get("passed"))
        sys.exit(f"official Foundation conformance failed ({failing}); not building a release")
    result["obdsRelease"] = release
    result["claimScope"] = FOUNDATION_CLAIM_SCOPE
    path.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote OBDS-{release}-FOUNDATION-CONFORMANCE.json "
          f"({result['passedCount']} passed / {result['failedCount']} failed)")
    return result


_GATE = None


def _gate():
    """The release gate, which owns the suite-hash definition.

    The gate ships inside the release archive and the build tooling does not, so
    the definition lives there and is imported here. One definition, and anyone
    with the package can recompute the suite identity without this script.
    """
    global _GATE
    if _GATE is None:
        spec = importlib.util.spec_from_file_location(
            "obds_release_gate", ROOT / "reference" / "release-gate.py"
        )
        if spec is None or spec.loader is None:
            sys.exit("cannot load reference/release-gate.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _GATE = module
    return _GATE


def load(path: Path):
    """Section 28.1: release evidence is governed data, so it is read as such.

    The gate reads every one of these files under the governed contract and this
    script read them with a raw parser, in the one direction where it matters: a
    duplicated `releases` key in `publication-record.json` was silently last-wins
    here and refused there, and this is the script that rewrites that file.
    """
    return _gate().load(path)


def suite_identity() -> tuple[str, int]:
    gate = _gate()
    pairs = gate.suite_files()
    if not pairs:
        sys.exit("no conformance suite files found")
    return gate.suite_hash(pairs), len(pairs)


def conformance_profiles(foundation_result: dict) -> list[dict[str, object]]:
    """Exactly the profiles this release can defend. See the constants above."""
    foundation = dict(FOUNDATION_PROFILE)
    foundation["passedCount"] = foundation_result["passedCount"]
    foundation["failedCount"] = foundation_result["failedCount"]
    foundation["declaredCaseCount"] = foundation_result["passedCount"] + foundation_result["failedCount"]
    foundation["suiteHash"] = foundation_result["suiteHash"]
    return [foundation, dict(COMPILED_RUNTIME_PROFILE)]


def suite_counts(output: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    current = None
    for line in output.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
        elif current and " passed in " in line:
            counts[current] = int(line.split()[0])
            current = None
    missing = [s for s in SUITE_ORDER if s not in counts]
    if missing:
        sys.exit(f"test output has no result for {missing}")
    return counts


def write_metadata(release: str, counts: dict[str, int], file_count: int,
                   foundation_result: dict) -> str:
    output_path = ROOT / f"OBDS-{release}-TEST-OUTPUT.txt"
    digest = sha256(output_path)
    total = sum(counts.values())

    result_path = ROOT / f"OBDS-{release}-TEST-RESULT.json"
    declared_suite_hash, suite_file_count = suite_identity()
    result = load(result_path)
    result.update(
        {
            "release": release,
            "promotedFrom": PRIOR_RELEASE,
            "notes": release_notes(release, counts),
            "passedCount": total,
            "failedCount": 0,
            "skippedCount": 0,
            "passed": True,
            "suiteCounts": counts,
            "testOutputHash": digest,
            # Section 26 identifiers.
            "implementation": dict(IMPLEMENTATION),
            "obdsVersion": release,
            "suiteHash": declared_suite_hash,
            "suiteFileCount": suite_file_count,
            "conformanceProfiles": conformance_profiles(foundation_result),
            "executedSuites": {"note": EXECUTED_SUITES_NOTE, "counts": counts},
            "requiredCasesSkippedOrChanged": False,
            "claimScope": CLAIM_SCOPE,
        }
    )
    result_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    audit_path = ROOT / f"OBDS-{release}-FINAL-AUDIT.json"
    audit = load(audit_path)
    audit.update(
        {
            "release": release,
            "testsPassed": total,
            "testsFailed": 0,
            "testsSkipped": 0,
            "suiteCounts": counts,
            "testOutputHash": digest,
            "packageFileCount": file_count,
            "packageJunkFiles": 0,
        }
    )
    audit_path.write_text(
        json.dumps(audit, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote OBDS-{release}-TEST-RESULT.json and OBDS-{release}-FINAL-AUDIT.json")
    return digest


def write_manifest(release: str, pairs: list[tuple[str, Path]]) -> None:
    manifest = {
        "fileCount": len(pairs),
        "files": [
            {"bytes": source.stat().st_size, "path": archive, "sha256": sha256(source)}
            for archive, source in pairs
        ],
        "kind": "obds-package-manifest",
        "normativeSpecification": f"OBDS-{release}.md",
        "note": (
            "PACKAGE-MANIFEST.json is excluded from its own file list. Every other file in the "
            "package is listed exactly once. Paths are archive paths: the release archive ships "
            "the public schemas flat, while the repository keeps them at the URL paths their $id "
            "resolves to, schemas/1.0.0/ and value-schemas/1.0.0/."
        ),
        "release": "stable",
        "schemaVersion": "1.0.0",
        "version": release,
    }
    (ROOT / "PACKAGE-MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote PACKAGE-MANIFEST.json with {len(pairs)} files")


def write_archive(release: str, pairs: list[tuple[str, Path]]) -> Path:
    snapshot = ROOT / "spec" / release
    snapshot.mkdir(parents=True, exist_ok=True)
    archive_path = snapshot / f"OBDS-{release}-FINAL.zip"
    top = f"OBDS-{release}-FINAL"
    everything = pairs + [("PACKAGE-MANIFEST.json", ROOT / "PACKAGE-MANIFEST.json")]
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, source in sorted(everything):
            archive.write(source, f"{top}/{name}")
    print(f"wrote {archive_path.relative_to(ROOT)} ({archive_path.stat().st_size} bytes)")

    # The published snapshot mirrors the flat release documents next to the archive,
    # as spec/1.0.0/, spec/1.0.1/ and spec/1.0.2/ already do.
    for name, source in everything:
        if "/" in name:
            continue
        if name.startswith(("OBDS-", "PACKAGE-MANIFEST")) or name in ("README.md", "requirements.txt"):
            shutil.copy2(source, snapshot / name)
    print(f"synced spec/{release}/ release documents")
    return archive_path


def sync_publication_surface(release: str, counts: dict[str, int], archive: Path | None) -> None:
    """Write the built values into the publication record and the website.

    These three numbers, `testOutputHash`, `packageZipSha256` and
    `websiteIndexSha256`, were hand-copied through 1.1.0 and drifted every time.
    Generating them here means the release gate's cross-check in step 12 can
    never be satisfied by a stale copy, because there is no copy step left.
    """
    result = load(ROOT / f"OBDS-{release}-TEST-RESULT.json")
    record_path = ROOT / "publication-record.json"
    if not record_path.is_file():
        return
    record = load(record_path)

    record["currentRelease"] = release
    record["conformanceTestsPassed"] = result["passedCount"]
    record["conformanceTestsFailed"] = result["failedCount"]
    record["conformanceTestsSkipped"] = result["skippedCount"]
    record["testOutputHash"] = result["testOutputHash"]
    entry = record.setdefault("releases", {}).setdefault(release, {})
    entry["testOutputHash"] = result["testOutputHash"]
    if archive is not None and archive.is_file():
        digest = sha256(archive)
        record["packageZipSha256"] = digest
        entry["packageZipSha256"] = digest

    index_html = ROOT / "index.html"
    if index_html.is_file():
        site = index_html.read_text(encoding="utf-8")
        site = re.sub(
            r"sha256:[0-9a-f]{64}",
            lambda m: result["testOutputHash"]
            if m.group(0) != record.get("schemaSurfaceFingerprint")
            else m.group(0),
            site,
        )
        index_html.write_text(site, encoding="utf-8")
        record["websiteIndexSha256"] = sha256(index_html)

    record_path.write_text(
        json.dumps(record, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print("synced publication-record.json and index.html to the built artefacts")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the OBDS release package")
    parser.add_argument("--run-tests", action="store_true", help="regenerate the test output first")
    parser.add_argument("--manifest-only", action="store_true", help="skip the archive and snapshot")
    args = parser.parse_args()

    release = version()
    print(f"OBDS release build, version {release}")
    if args.run_tests:
        run_tests(release)
    foundation_result = run_official_foundation_conformance(release)

    output = (ROOT / f"OBDS-{release}-TEST-OUTPUT.txt").read_text(encoding="utf-8")
    counts = suite_counts(output)

    # The manifest hashes the metadata files, so the metadata has to settle first.
    pairs = package_files(release)
    write_metadata(release, counts, len(pairs), foundation_result)
    pairs = package_files(release)
    write_manifest(release, pairs)

    archive = None
    if not args.manifest_only:
        archive = write_archive(release, pairs)
    sync_publication_surface(release, counts, archive)
    return 0


if __name__ == "__main__":
    sys.exit(main())
