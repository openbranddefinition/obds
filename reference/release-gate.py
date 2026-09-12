#!/usr/bin/env python3
"""OBDS 4.1.3 release gate.

Validates the release metadata of this package, proves the normative contract
has not moved, and proves the package ships no junk.

This is a package check. It is not an OBDS capability, not a profile and not
part of the conformance suite.

Run from the package root, which in this repository is the repository root:

    python reference/release-gate.py

It runs in two layouts and behaves identically in both:

- the working repository, where the public schemas live at their published
  URL paths, ``schemas/1.0.0/`` and ``value-schemas/1.0.0/``; and
- an unpacked release archive, where they are flat, ``schemas/`` and
  ``value-schemas/``.

Generated local test caches (``__pycache__``, ``.pytest_cache``, ``*.pyc``, a
virtualenv) are not package junk. They are what running the conformance suite
produces, so the natural order

    python reference/run_all.py
    python reference/release-gate.py

succeeds with no manual cleanup. What still fails the gate is junk that would
actually be shipped: ``.DS_Store``, ``Thumbs.db``, editor backups, ``__MACOSX``,
and any generated cache that has found its way into ``PACKAGE-MANIFEST.json``.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import subprocess
import textwrap
import sys
from html.parser import HTMLParser
from contextlib import redirect_stdout
from types import SimpleNamespace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Section 28.1. The gate validates published examples and the declared
# conformance suite, so it is a governed reader like any other and used to be
# one of the divergent ones: it read both with PyYAML's YAML 1.1 defaults, so
# it could bless an example the compiler refuses and refuse one the compiler
# accepts.
_FOUNDATION_SRC = ROOT / "reference" / "foundation" / "src"
if str(_FOUNDATION_SRC) not in sys.path:
    sys.path.insert(0, str(_FOUNDATION_SRC))
from obds_ref.governed_io import (  # noqa: E402
    ValidationFailure as _GovernedParseError,
    load_data as _load_governed,
    read_governed_text as _read_governed_text,
)

# Concrete expected values for THIS release. The generic schemas stay value-free;
# the fixture lives here.
EXPECTED_SUITE_COUNTS = {
    "foundation": 1052,
    "context-delivery": 3,
    "context-assembly": 24,
    "design-space": 20,
    "integration": 15,
    "golden": 6,
    "adversarial": 38,
}
EXPECTED_TOTAL = 1158
EXPECTED_RELEASE = "4.1.3"
EXPECTED_STATUS = "stable"
EXPECTED_PUBLIC_SCHEMAS = 21
EXPECTED_PUBLIC_VALUE_SCHEMAS = 6
# OBDS 1.1 adds exactly one versioned contract beside the frozen 1.0.0 surface.
EXPECTED_V11_SCHEMAS = {"compiled-context.schema.json"}

# The OBDS 1.0.0 contract surface stays frozen and byte-identical across 1.0.0,
# 1.0.1, 1.0.2, 1.0.3 and 1.0.4, and OBDS 1.1 does not touch it. 1.1 publishes one
# additional versioned contract beside it, schemas/1.1.0/compiled-context.schema.json,
# and changes none of the 27. This fingerprint is sha256 over the sorted
# "dir/file:sha256" lines of all 27 public 1.0.0 contracts.
FROZEN_SCHEMA_SURFACE = "517683bb3496867daa2346ceb2f7844e46015f926ff757a9c23da90cf1e5f469"

# Normative contract identity against the immediately preceding release. Every
# entry is sha256 of the contract as published in spec/1.0.4/, and unchanged from
# 1.0.3, 1.0.2, 1.0.1 and 1.0.0 before it, and from 1.1.0 after it. The
# fingerprint excludes `release` and `releaseModel.normativeSpecification`, which
# are packaging, so a version bump alone never moves it. It is computed over the
# frozen OBDS 1.0.0 surface only: a contract published beside that surface at its
# own version, such as schemas/1.1.0/compiled-context.schema.json, is listed in
# the index and the map but excluded here, because including it would make the
# frozen-surface proof impossible to state. A maintenance release must not move
# any of them.
PRIOR_RELEASE = "4.1.2"
PRIOR_CONTRACT_FINGERPRINTS = {
    "capability-registry": "68fb26cc27f0db658b80de805fc0e27ed271c3881b67de18763a620f2e6107b1",
    "schema-index": "6899ccd33e780c54529e17f5e13320d782863e830c0f6648bf10dab337a55b83",
    "publication-map-contracts": "429247482e5f9d70a867e05e7a223f13c39b9a77c457ca5300a49e74a77f150d",
}

# Files that must exist for the licensing position to be self-describing, with the
# sha256 of the two standard licence texts as published by their stewards. A
# release must never ship a modified licence text.
REQUIRED_LICENCE_FILES = {
    "LICENSES/Apache-2.0.txt": "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
    "LICENSES/CC-BY-4.0.txt": "9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411",
}
REQUIRED_LICENCE_DOCS = ("LICENSE.md", "NOTICE", "TRADEMARKS.md", "GOVERNANCE.md", "CONTRIBUTING.md")

# Wording retired by the 1.0.2 licensing model is forbidden in current claims.
# Authenticated history and reviewed non-claim executable payloads are distinct.
RETIRED_LICENSING_WORDING = (
    "separate commercial licence",
    "commercial licence is required",
    "Free Use",
    "under legal review",
    "grants no right",
    "nothing on this page grants",
    "tooling carve-out",
    "carve-out",
)

# What the package is. Everything outside this is repository or website
# material: the published release snapshots under spec/, the site itself,
# local notes and any local virtualenv. The gate judges the package only.
#
# `tools/` joined the package in 3.0.1. The 3.0.0 archive omitted it, and the
# systemic surface registries name `tools/build-release.py` and
# `tools/docs-smoke-test.py`: in the repository that is correct, because the
# packager is part of the governed hash surface, but in an unpacked archive the
# files were absent and eight enumeration guards refused a release the
# repository had passed. The two commands README and TEST-REQUIREMENTS document
# for the archive layout did not run. A directory the suite reads is part of the
# package, or the package is not the thing the suite was run against.
PACKAGE_ROOT_FILES = (
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "LICENSE.md",
    "NOTICE",
    "PACKAGE-MANIFEST.json",
    "README.md",
    "TRADEMARKS.md",
    "requirements.txt",
)
PACKAGE_DIRS = ("LICENSES", "examples", "reference", "release-schemas", "tools")

# Generated by running the suite or by a local virtualenv. Never shipped, never
# junk. Ruling: a developer must not have to delete these to run the gate.
GENERATED_CACHE_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".eggs",
    "node_modules",
}
GENERATED_CACHE_SUFFIXES = (".pyc", ".pyo", ".egg-info")

# Junk that would actually be shipped, and still fails the gate.
JUNK_DIRS = {"__MACOSX", ".ipynb_checkpoints"}
JUNK_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
JUNK_SUFFIXES = (".swp", ".swo", ".orig", ".rej", ".bak", ".tmp", "~")

# The conformance suite, for the section 26 suite hash. The runner plus the seven
# suite directories; the implementation under test is excluded and identified
# separately in the result.
SUITE_RUNNER = "reference/run_all.py"
SUITE_EXCLUDED_PREFIX = "reference/foundation/src/"

failures: list[str] = []



def section_26_2_requirements(spec_text: str) -> list[str]:
    """The requirements section 26.2 actually lists, read from the specification.

    Pinning them in this file would only move the problem: an author editing the
    release metadata would edit the pin beside it. They are derived from the
    normative sentence instead, so the claim is measured against the standard.
    """
    marker = "### 26.2 OBDS Compiled Runtime"
    if marker not in spec_text:
        return []
    body = spec_text.split(marker, 1)[1].lstrip()
    sentence = body.split("\n\n", 1)[0].strip()
    prefix = "Additionally requires "
    if not sentence.startswith(prefix) or not sentence.endswith("."):
        return []
    listed = sentence[len(prefix):-1]
    parts = [item.strip() for item in listed.split(", ")]
    if parts and " and " in parts[-1]:
        head, _, tail = parts[-1].rpartition(" and ")
        parts[-1:] = [head.strip(), tail.strip()]
    return [item.replace("`", "") for item in parts if item]

CONFORMANCE_SUITES = (
    "foundation",
    "context-delivery",
    "context-assembly",
    "design-space",
    "integration",
    "golden",
    "adversarial",
)


def executed_conformance_cases() -> tuple[dict[str, str], dict[str, int], list[str]]:
    """Every case the official suite executed, by id, with its outcome.

    The gate runs the suites itself rather than trusting a recorded list, so an
    evidence id can only resolve if the case really ran in this checkout.
    """
    import tempfile
    import xml.etree.ElementTree as ElementTree

    outcomes: dict[str, str] = {}
    counts: dict[str, int] = {}
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        for suite in CONFORMANCE_SUITES:
            directory = ROOT / "reference" / suite
            if not directory.is_dir():
                failures.append(f"{suite}: suite directory is missing")
                continue
            report = Path(tmp) / f"{suite}.xml"
            completed = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", f"--junitxml={report}"],
                cwd=directory,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            if completed.returncode != 0:
                tail = (completed.stdout or "").strip().splitlines()
                failures.append(f"{suite}: pytest exited {completed.returncode}: "
                                + (tail[-1] if tail else "no output"))
            if not report.is_file():
                failures.append(f"{suite}: pytest produced no report")
                continue
            executed = 0
            for case in ElementTree.parse(report).getroot().iter("testcase"):
                identifier = f"{suite}/{case.get('classname')}::{case.get('name')}"
                outcome = "passed"
                for child in case:
                    if child.tag in ("failure", "error"):
                        outcome = "failed"
                    elif child.tag == "skipped":
                        outcome = "skipped"
                outcomes[identifier] = outcome
                executed += 1
            counts[suite] = executed
    return outcomes, counts, failures


def _check_section_26_2_evidence(entry: dict) -> None:
    """Guard 20. Resolve the evidence, do not count it.

    Until 2.0.0 this guard asserted `len(requirementsExercised) >= 12`. A
    release author could replace all fourteen case names with invented strings
    and the gate still passed, which is the same failure the 1.1.5 validity
    guard had: a guard that advertises a protection it cannot give.
    """
    entries = entry.get("requirementsExercised") or []
    declared = [item.get("requirement") for item in entries]

    spec_path = ROOT / f"OBDS-{EXPECTED_RELEASE}.md"
    required = section_26_2_requirements(
        spec_path.read_text(encoding="utf-8") if spec_path.is_file() else ""
    )
    check(len(required) >= 10,
          "TEST-RESULT: section 26.2 could not be read from the specification, so "
          "the evidence claim cannot be measured against it")
    check(
        list(declared) == list(required),
        "TEST-RESULT: requirementsExercised must name exactly the requirements "
        "section 26.2 lists, in the order it lists them; the difference is "
        f"{sorted(set(required) ^ set(x for x in declared if x))}",
    )

    executed, counts, failures = executed_conformance_cases()
    check(not failures, "TEST-RESULT: the gate could not execute the suite: " + "; ".join(failures))
    check(bool(executed), "TEST-RESULT: no conformance case could be resolved at all")
    # The gate just ran the suite. It must believe that run, not the recorded
    # output beside it: adding a test made run_all report one more case while
    # the gate reported the frozen number and passed.
    check(
        counts == EXPECTED_SUITE_COUNTS,
        f"TEST-RESULT: the suite the gate executed is {counts}, "
        f"not the {EXPECTED_SUITE_COUNTS} this release claims",
    )
    check(
        sum(counts.values()) == EXPECTED_TOTAL,
        f"TEST-RESULT: the gate executed {sum(counts.values())} cases, "
        f"not the {EXPECTED_TOTAL} this release claims",
    )

    seen: dict[str, str] = {}
    for item in entries:
        requirement = item.get("requirement")
        cases = item.get("cases")
        if not isinstance(cases, list) or not cases:
            check(False, f"TEST-RESULT: {requirement!r} names no evidence case")
            continue
        for identifier in cases:
            if identifier not in executed:
                check(False,
                      f"TEST-RESULT: evidence case does not exist in the executed "
                      f"suite: {identifier} (for {requirement!r})")
                continue
            check(executed[identifier] == "passed",
                  f"TEST-RESULT: evidence case did not pass, it {executed[identifier]}: "
                  f"{identifier} (for {requirement!r})")
            check(identifier not in seen,
                  f"TEST-RESULT: evidence case {identifier} is claimed for both "
                  f"{seen.get(identifier)!r} and {requirement!r}")
            seen[identifier] = requirement


def check(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    """Section 28.1: release evidence is governed data, so it is read as such.

    This was the eighth reader in the release and the most permissive of them:
    a duplicated key in the publication map or the audit was silently
    last-wins, in the one file whose job is to say what the release contains.
    """
    return _load_governed(path)


# Section 28.1 is one contract, so the module that states it is one file. It is
# copied next to each package's `canonical.py` because those packages are
# imported flat rather than as a package, and the copies are pinned here: a
# release cannot ship two spellings of the governed reader, which is the defect
# 3.0.0 exists to close.
GOVERNED_CONTRACT_COPIES = {
    "projection.py": ["reference/foundation/src/obds_ref/projection.py", "reference/context-assembly/projection.py"],
    "governed_io.py": [
        "reference/foundation/src/obds_ref/governed_io.py",
        "reference/context-assembly/governed_io.py",
        "reference/context-delivery/governed_io.py",
        "reference/design-space/governed_io.py",
    ],
    "build_views.py": [
        "reference/context-assembly/build_views.py",
        "reference/context-delivery/build_views.py",
    ],
    "model_input.py": [
        "reference/foundation/src/obds_ref/model_input.py",
        "reference/context-assembly/model_input.py",
        "reference/context-delivery/model_input.py",
        "reference/design-space/model_input.py",
    ],
    "canonical.py": [
        "reference/foundation/src/obds_ref/canonical.py",
        "reference/context-assembly/canonical.py",
        "reference/context-delivery/canonical.py",
        "reference/design-space/canonical.py",
    ],
}


def check_governed_contract_copies() -> None:
    for name, paths in GOVERNED_CONTRACT_COPIES.items():
        digests = {}
        for rel in paths:
            path = ROOT / rel
            if not path.is_file():
                check(False, f"{rel} is missing: the governed contract must ship in every package")
                continue
            digests.setdefault(sha256_file(path), []).append(rel)
        check(
            len(digests) <= 1,
            f"{name} has diverged across packages: "
            + "; ".join(f"{digest[:19]} -> {', '.join(files)}" for digest, files in sorted(digests.items())),
        )


def schema_dir(name: str) -> Path:
    """Resolve schemas/ and value-schemas/ in either supported layout."""
    flat = ROOT / name
    if any(flat.glob("*.json")):
        return flat
    versioned = flat / "1.0.0"
    if any(versioned.glob("*.json")):
        return versioned
    return flat


SCHEMAS_DIR = schema_dir("schemas")
VALUE_SCHEMAS_DIR = schema_dir("value-schemas")

# The archive flattens exactly one contract surface, the frozen 1.0.0 one,
# because 1.0.0 through 1.0.4 shipped it that way and consumers resolve it at
# that path. Every other version keeps its version in the path.
FLATTENED_CONTRACT_VERSION = "1.0.0"
_CONTRACT_VERSION_DIR = re.compile(r"^\d+\.\d+\.\d+$")


def contract_directories() -> list[tuple[Path, str, str]]:
    """Every published contract surface, discovered rather than listed.

    This was a hand-kept list here and a second hand-kept copy in
    `tools/build-release.py`. Both named 1.0.0 and 1.1.0. The repository had
    since grown `schemas/3.0.0/` and `value-schemas/3.0.0/`, so cutting 3.0.0
    would have produced an archive without the contracts the release publishes
    — and this gate, reading the other copy of the same stale list, had no way
    to notice the surface it was supposed to be inventorying.

    Returns `(directory, published URL path, archive path)`. Both supported
    layouts are covered: the working repository, where contracts sit at the path
    their `$id` resolves to, and an unpacked archive, where the frozen surface is
    flat.
    """
    found: list[tuple[Path, str, str]] = []
    for family in ("schemas", "value-schemas"):
        base = ROOT / family
        if not base.is_dir():
            continue
        if any(base.glob("*.json")):
            found.append((base, f"{family}/{FLATTENED_CONTRACT_VERSION}", family))
        for directory in sorted(base.iterdir()):
            if not directory.is_dir() or not _CONTRACT_VERSION_DIR.match(directory.name):
                continue
            if not any(directory.glob("*.json")):
                continue
            url = f"{family}/{directory.name}"
            archive = family if directory.name == FLATTENED_CONTRACT_VERSION else url
            found.append((directory, url, archive))
    return found


def is_generated_cache(path: Path, root: Path = ROOT) -> bool:
    parts = path.relative_to(root).parts
    if any(part in GENERATED_CACHE_DIRS for part in parts):
        return True
    if any(part.startswith(".venv") or part.endswith(".egg-info") for part in parts):
        return True
    return path.name.endswith(GENERATED_CACHE_SUFFIXES)


def package_paths() -> list[Path]:
    """Every path that belongs to the package, files and directories."""
    found: list[Path] = []
    for name in PACKAGE_ROOT_FILES:
        candidate = ROOT / name
        if candidate.is_file():
            found.append(candidate)
    found.extend(sorted(p for p in ROOT.glob("OBDS-*") if p.is_file()))
    contract_dirs = [directory for directory, _, _ in contract_directories()]
    for directory in (*(ROOT / d for d in PACKAGE_DIRS), *contract_dirs):
        if directory.is_dir():
            found.extend(sorted(directory.rglob("*")))
    return [p for p in found if public_package_member(p.relative_to(ROOT).as_posix())]


def package_text_files() -> list[Path]:
    return [p for p in package_paths() if p.is_file() and not is_generated_cache(p)]


def find_junk() -> list[str]:
    found = []
    for path in package_paths():
        if is_generated_cache(path):
            continue
        rel = path.relative_to(ROOT).as_posix()
        if any(part in JUNK_DIRS for part in path.parts):
            found.append(rel)
        elif path.name in JUNK_NAMES or path.name.endswith(JUNK_SUFFIXES):
            found.append(rel)
    return sorted(set(found))


def run_official_foundation_conformance() -> dict | None:
    """Execute the official declared Foundation conformance suite.

    Section 26 clause 1 permits a conformance claim only when the implementation
    passes every required case in the official Conformance Suite for the named
    profile. The only artefact in this package that names a profile is
    ``reference/foundation/conformance-suite.yaml``.

    Until 1.0.4 nothing in the release path executed it. It had been failing on
    a stale fixture since before 1.0.3 shipped, and neither the 107-case run nor
    this gate could see it. The gate now runs it directly, so omitting it is not
    possible and a stale fixture cannot pass silently.
    """
    suite_path = ROOT / "reference" / "foundation" / "conformance-suite.yaml"
    if not suite_path.is_file():
        failures.append("missing reference/foundation/conformance-suite.yaml")
        return None
    src = ROOT / "reference" / "foundation" / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    try:
        from obds_ref.cli import command_conformance
    except ImportError as exc:  # pragma: no cover
        failures.append(f"cannot execute official Foundation conformance: {exc}")
        return None

    out = ROOT / ".gate-foundation-conformance.json"
    args = SimpleNamespace(suite=str(suite_path), out=str(out))
    stdout = io.StringIO()
    try:
        with redirect_stdout(stdout):
            command_conformance(args)
        # Section 28.1: the conformance result is published evidence.
        result = load(out)
    except Exception as exc:  # pragma: no cover
        failures.append(f"official Foundation conformance did not execute: {exc}")
        return None
    finally:
        out.unlink(missing_ok=True)
    return result


def check_official_foundation_conformance(declared_cases: int) -> dict | None:
    result = run_official_foundation_conformance()
    if result is None:
        return None
    check(
        result.get("profile") == "foundation",
        f"official conformance result profile is {result.get('profile')!r}, expected 'foundation'",
    )
    check(
        result.get("failedCount") == 0,
        f"official Foundation conformance has {result.get('failedCount')} failing case(s): "
        + ", ".join(c["id"] for c in result.get("cases", []) if not c.get("passed")),
    )
    check(result.get("passed") is True, "official Foundation conformance did not pass")
    check(
        result.get("passedCount") == declared_cases,
        f"official Foundation conformance ran {result.get('passedCount')} of "
        f"{declared_cases} declared cases; no required case may be skipped or changed",
    )
    return result


def suite_files() -> list[tuple[str, Path]]:
    """(package-relative path, source) for every file in the published suite.

    Section 26 requires a conformance result to name the suite it ran. The suite
    is the runner plus the seven suite directories and their fixtures. It
    excludes ``reference/foundation/src/``, which is the implementation under
    test and is identified separately by the result's ``implementation`` field.

    This definition lives in the gate because the gate ships inside the release
    archive: anyone with the package can recompute the suite identity.
    """
    pairs: list[tuple[str, Path]] = []
    runner = ROOT / SUITE_RUNNER
    if runner.is_file():
        pairs.append((SUITE_RUNNER, runner))
    for suite in EXPECTED_SUITE_COUNTS:
        base = ROOT / "reference" / suite
        if not base.is_dir():
            continue
        for source in sorted(base.rglob("*")):
            if not source.is_file() or is_generated_cache(source):
                continue
            rel = source.relative_to(ROOT).as_posix()
            if rel.startswith(SUITE_EXCLUDED_PREFIX):
                continue
            pairs.append((rel, source))
    return sorted(pairs)


def suite_hash(pairs: list[tuple[str, Path]]) -> str:
    """Stable identity for the suite: sorted paths with their content hashes."""
    payload = json.dumps(
        [[rel, sha256_file(source)] for rel, source in pairs],
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def validate_schemas(test_result, audit) -> None:
    try:
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
    except ImportError as exc:  # pragma: no cover
        failures.append(f"cannot validate release metadata: {exc}")
        return

    schema_root = ROOT / "release-schemas"
    resources = []
    for name in ("release-test-result.schema.json", "release-audit.schema.json"):
        schema = load(schema_root / name)
        resources.append((schema["$id"], Resource.from_contents(schema)))
    registry = Registry().with_resources(resources)

    pairs = [
        (f"OBDS-{EXPECTED_RELEASE}-TEST-RESULT.json", "release-test-result.schema.json", test_result),
        (f"OBDS-{EXPECTED_RELEASE}-FINAL-AUDIT.json", "release-audit.schema.json", audit),
    ]
    for label, schema_name, instance in pairs:
        schema = load(schema_root / schema_name)
        validator = Draft202012Validator(schema, registry=registry)
        for error in sorted(validator.iter_errors(instance), key=str):
            location = "/".join(str(part) for part in error.path) or "<root>"
            failures.append(f"{label}: {location}: {error.message}")


def published_yaml_elements(html: str) -> list[dict]:
    """Every Brand Element example embedded in a published HTML page.

    A published page teaches by example, so its examples must satisfy the same
    contracts as real data. 1.1.0 shipped an authoring page whose only worked
    example failed two of them. Blocks are found by their `id:` and `state:`
    keys rather than by a class name, so restyling the page cannot silently
    remove the check.
    """
    import html as html_mod

    import yaml as yaml_mod

    elements: list[dict] = []
    for block in re.findall(r"<pre[^>]*>(.*?)</pre>|<code[^>]*>(.*?)</code>", html, re.S):
        text = next((b for b in block if b), "")
        text = re.sub(r"<[^>]+>", "", text)
        text = html_mod.unescape(text)
        if not re.search(r"^\s*id:\s*\S", text, re.M) or "state:" not in text:
            continue
        try:
            payload = _read_governed_text(textwrap.dedent(text), is_json=False)
        except (yaml_mod.YAMLError, _GovernedParseError, ValueError):
            continue
        if isinstance(payload, dict) and "id" in payload and "state" in payload:
            elements.append(payload)
    return elements


def manifest_path(rel: str) -> Path:
    """Map a manifest path onto the current layout, from the discovered surface.

    The frozen 1.0.0 contracts are flat in the archive and under 1.0.0/ in the
    repository; every other version keeps its version in the path in both.

    This carried its own version logic — a third interpretation of the contract
    surface beside the packager's and the gate's inventory. It named 1.1.0 and
    stopped, so once packaging discovered `schemas/3.0.0/`, every 3.0.0 entry in
    a regenerated manifest resolved to `schemas/1.0.0/3.0.0/…`, which does not
    exist, and manifest verification failed for the whole new contract surface.
    It now derives from `contract_directories()`, so a version directory that
    discovery finds is a version directory this resolves. Longest archive prefix
    first: `schemas/1.1.0/…` must not be read as the flat `schemas/` surface.
    """
    for directory, _, archive in sorted(
        contract_directories(), key=lambda entry: len(entry[2]), reverse=True
    ):
        prefix = f"{archive}/"
        if rel.startswith(prefix):
            return directory / rel[len(prefix):]
    return ROOT / rel


def check_manifest(audit) -> int:
    """Every file the package ships must exist and hash as declared."""
    path = ROOT / "PACKAGE-MANIFEST.json"
    if not path.is_file():
        failures.append("missing PACKAGE-MANIFEST.json")
        return 0
    manifest = load(path)
    entries = manifest["files"]
    check(
        manifest["fileCount"] == len(entries),
        f"PACKAGE-MANIFEST fileCount={manifest['fileCount']} but lists {len(entries)} files",
    )
    check(
        manifest.get("version") == EXPECTED_RELEASE,
        f"PACKAGE-MANIFEST version={manifest.get('version')} != {EXPECTED_RELEASE}",
    )
    missing, mismatched, cached = [], [], []
    for entry in entries:
        rel = entry["path"]
        if any(part in GENERATED_CACHE_DIRS for part in Path(rel).parts) or rel.endswith(
            GENERATED_CACHE_SUFFIXES
        ):
            cached.append(rel)
            continue
        target = manifest_path(rel)
        if not target.is_file():
            missing.append(rel)
            continue
        if sha256_file(target) != entry["sha256"]:
            mismatched.append(rel)
        elif target.stat().st_size != entry["bytes"]:
            mismatched.append(rel)
    check(not cached, f"PACKAGE-MANIFEST ships generated cache files: {cached[:10]}")
    check(not missing, f"PACKAGE-MANIFEST lists {len(missing)} missing files: {missing[:10]}")
    check(
        not mismatched,
        f"PACKAGE-MANIFEST hash mismatch on {len(mismatched)} files: {mismatched[:10]}",
    )
    check(
        audit["packageFileCount"] == len(entries),
        f"audit packageFileCount={audit['packageFileCount']} but manifest lists {len(entries)}",
    )
    return len(entries)


def verify_task_facts_schema(root=ROOT):
    """Independent local retrieval for the preserved experimental URN."""
    companion = load(root / "OBDS-4.1.3-TASK-FACTS-SCHEMA-INDEX.json")
    assert companion["capability"] == "task-facts"
    assert companion["payloadVersion"] == "0.1"
    assert companion["canonicalization"] == "TFJ-0.1"
    assert len(companion["schemas"]) == 1
    entry = companion["schemas"][0]
    raw = (root / entry["localPath"]).read_bytes()
    assert raw == (root / entry["contractLocalPath"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == entry["sha256"]
    schema = json.loads(raw)
    assert schema["$id"] == entry["id"] and entry["id"].startswith("urn:")
    assert entry["retrievalUrl"] == "https://openbranddefinition.org/" + entry["localPath"]
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    Draft202012Validator.check_schema(schema)
    registry = Registry().with_resource(entry["id"], Resource.from_contents(schema))
    assert registry.resolver().lookup(entry["id"]).contents == schema
    return companion


def prior_registry(registry):
    import copy
    result = copy.deepcopy(registry)
    entries = result["runtimeCapabilities"]
    added = [entry for entry in entries if entry.get("id") == "task-facts"]
    assert added == [{"id": "task-facts", "conformanceSection": "26.10"}], "Task Facts must be exactly one optional runtime registration"
    result["runtimeCapabilities"] = [entry for entry in entries if entry.get("id") != "task-facts"]
    return result


PUBLICATION_EXPECTATIONS = {'index.html': ['<meta name="description" content="Open, implementation-ready specification for determining which brand truth applies to an AI task, resolving conflicts and failing closed when required truth is missing. Machine-readable brand guidelines with governed applicability. OBDS 4.1.3, CC BY 4.0 and Apache 2.0.">', '<meta property="og:image:alt" content="OBDS — Governed Brand Truth for AI — Open Brand Definition Specification 4.1.3">', '<meta property="og:description" content="Which brand truth applies to this AI task, and may it run? An open specification for governed applicability, conflict resolution and fail-closed execution. OBDS 4.1.3.">', '<meta name="obds-version" content="4.1.3">', '"version": "4.1.3",', '"url": "https://openbranddefinition.org/spec/4.1.3/OBDS-4.1.3-FINAL.zip",', '"version": "4.1.3",', '<div class="status">OBDS / 4.1.3 stable</div>', '<span>Open Brand Definition Specification 4.1.3</span>', '<div><span class="label">Status</span><span class="value" data-copy="en">4.1.3 stable. 12 September 2026.</span><span class="value" data-copy="de">4.1.3 stabil. 12. September 2026.</span></div>', '<h2 data-copy="en">4.1.3 is the current release.</h2>', '<h2 data-copy="de">4.1.3 ist der aktuelle Release.</h2>', '<div class="publication-row"><div class="publication-key" data-copy="en">Specification</div><div class="publication-key" data-copy="de">Spezifikation</div><div class="publication-value">OBDS 4.1.3</div></div>', '<div class="state-row"><div><span class="state-name"><a href="/spec/4.1.3/OBDS-4.1.3.md">OBDS-4.1.3.md</a></span></div><div data-copy="en">The normative specification. One document.</div><div data-copy="de">Die normative Spezifikation. Ein Dokument.</div></div>', '<div class="state-row"><div><span class="state-name"><a href="/spec/4.1.3/OBDS-4.1.3-FINAL.zip">OBDS-4.1.3-FINAL.zip</a></span></div><div data-copy="en">The complete package: specification, 35 existing public contracts plus optional Task Facts, reference implementation and the full conformance suite.</div><div data-copy="de">Das vollständige Paket: Spezifikation, 35 bestehende öffentliche Contracts plus optionale Task Facts, Referenzimplementierung und die komplette Conformance Suite.</div></div>', '<div class="state-row"><div><span class="state-name"><a href="/spec/4.1.3/OBDS-4.1.3-IMPLEMENTER-QUICKSTART.md">QUICKSTART.md</a></span></div><div data-copy="en">Five concepts and the smallest conforming implementation.</div><div data-copy="de">Fünf Konzepte und die kleinste konforme Implementierung.</div></div>', '<div class="state-row"><div><span class="state-name"><a href="/spec/4.1.3/OBDS-4.1.3-SCHEMA-INDEX.json">SCHEMA-INDEX.json</a></span></div><div data-copy="en">All 21 schemas, 6 value schemas and the versioned 1.1.0, 3.0.0 and 4.0.0 contracts beside them, with their identifiers.</div><div data-copy="de">Alle 21 Schemas, 6 Value Schemas und die versionierten 1.1.0-, 3.0.0- und 4.0.0-Contracts daneben, mit Identifiern.</div></div>', '<div class="state-row"><div><span class="state-name"><a href="/spec/4.1.3/OBDS-4.1.3-PUBLICATION-MAP.json">PUBLICATION-MAP.json</a></span></div><div data-copy="en">Every schema identifier mapped to the exact address that serves it.</div><div data-copy="de">Jeder Schema-Identifier auf die Adresse gemappt, die ihn ausliefert.</div></div>', '<div class="state-row"><div><span class="state-name"><a href="/spec/4.1.3/OBDS-4.1.3-TEST-REQUIREMENTS.md">TEST-REQUIREMENTS.md</a></span></div><div data-copy="en">Everything needed to reproduce 1158 of 1158 yourself.</div><div data-copy="de">Alles, was nötig ist, um 1158 von 1158 selbst zu reproduzieren.</div></div>', '<div class="state-row"><div><span class="state-name"><a href="/spec/4.1.3/OBDS-4.1.3-CHANGELOG.md">CHANGELOG.md</a></span></div><div data-copy="en">What 4.1.3 adds, and the complete list of what remains unchanged.</div><div data-copy="de">Was 4.1.3 ergänzt, und die vollständige Liste dessen, was unverändert bleibt.</div></div>', '<div class="state-row"><div><span class="state-name"><a href="/spec/4.1.3/OBDS-4.1.3-MIGRATION.md">MIGRATION.md</a></span></div><div data-copy="en">Existing valid packages require no migration; Task Facts adoption is voluntary.</div><div data-copy="de">Bestehende gültige Pakete benötigen keine Migration; Task Facts bleibt optional.</div></div>', '<a href="/spec/4.1.3/OBDS-4.1.3.md">', '<a href="/spec/4.1.3/OBDS-4.1.3-FINAL.zip">', '<p data-copy="de">© 2026 Kill The Dragon GmbH. Open Brand Definition und OBDS werden seit 22. Juli 2026 auf dieser Website öffentlich dokumentiert. OBDS 4.1.3 ist der aktuelle stabile Release vom 12. September 2026. Spezifikation, Referenzimplementierung und Conformance Suite sind unter <a href="https://github.com/openbranddefinition/obds" target="_blank" rel="noopener">github.com/openbranddefinition/obds</a> veröffentlicht. Die Spezifikation und die Dokumentation stehen unter der Creative Commons Attribution 4.0 International Lizenz. Die Schemas, die Release-Metadaten, die Referenzimplementierung, die Conformance Suite und die Beispiele stehen unter der Apache License 2.0. Beide Lizenztexte sind unverändert unter <a href="/LICENSES/CC-BY-4.0.txt">/LICENSES/CC-BY-4.0.txt</a> und <a href="/LICENSES/Apache-2.0.txt">/LICENSES/Apache-2.0.txt</a> veröffentlicht, die Zuordnung steht in <a href="/LICENSE.md">LICENSE.md</a>. Kommerzielle Implementierung ist erlaubt und braucht keine gesonderte Erlaubnis. Auf allgemeine Ideen, Prinzipien, Methoden oder unabhängig entwickelte kompatible Systeme wird kein Anspruch erhoben. Namen, Logos und Marken werden von keiner der beiden Lizenzen eingeräumt und sind in <a href="/TRADEMARKS.md">TRADEMARKS.md</a> gesondert geregelt. Es wird keine Markenregistrierung beansprucht, und kein Zertifizierungsprogramm ist aktiv. Kontakt lets@killthedragon.com.</p>', '<p data-copy="en">© 2026 Kill The Dragon GmbH. Open Brand Definition and OBDS have been publicly documented on this website since 22 July 2026. OBDS 4.1.3 is the current stable release, dated 12 September 2026. The specification, the reference implementation and the conformance suite are published at <a href="https://github.com/openbranddefinition/obds" target="_blank" rel="noopener">github.com/openbranddefinition/obds</a>. The specification and the documentation are licensed under the Creative Commons Attribution 4.0 International Licence. The schemas, the release metadata, the reference implementation, the conformance suite and the examples are licensed under the Apache License 2.0. Both licence texts are published unmodified at <a href="/LICENSES/CC-BY-4.0.txt">/LICENSES/CC-BY-4.0.txt</a> and <a href="/LICENSES/Apache-2.0.txt">/LICENSES/Apache-2.0.txt</a>, and the mapping is in <a href="/LICENSE.md">LICENSE.md</a>. Commercial implementation is permitted and requires no separate permission. No claim is made to general ideas, principles, methods or independently developed compatible systems. Names, logos and marks are granted by neither licence and are governed separately in <a href="/TRADEMARKS.md">TRADEMARKS.md</a>. No trademark registration is claimed and no certification programme is live. Contact lets@killthedragon.com.</p>'], 'authoring/index.html': ['<meta property="og:image:alt" content="Authoring and curation — Open Brand Definition Specification 4.1.3">', '<div class="status">OBDS / 4.1.3 stable</div>', '<span>Companion to OBDS 4.1.3</span>', '<a href="/spec/4.1.3/OBDS-4.1.3.md#7-brand-manifest">', '<a href="/spec/4.1.3/OBDS-4.1.3.md#24-selective-extraction-and-curation">', '<a href="/spec/4.1.3/OBDS-4.1.3.md#26-conformance-claims">'], 'examples/index.html': ['<meta property="og:image:alt" content="See OBDS decide — Open Brand Definition Specification 4.1.3">', '<div class="status">OBDS / 4.1.3 stable</div>', '<span>Companion to OBDS 4.1.3</span>', '<p class="code-caption">Or download <a href="/spec/4.1.3/OBDS-4.1.3-FINAL.zip">OBDS-4.1.3-FINAL.zip</a>, extract it, and run the same commands from the extracted directory.</p>', '<a href="/spec/4.1.3/OBDS-4.1.3.md">', '<a href="/spec/4.1.3/OBDS-4.1.3-IMPLEMENTER-QUICKSTART.md">'], 'what-is-obds/index.html': ['<meta property="og:image:alt" content="What is OBDS? — Open Brand Definition Specification 4.1.3">', '"version": "4.1.3",', '<div class="status">OBDS / 4.1.3 stable</div>', '<span>Companion to OBDS 4.1.3</span>', '<a href="/spec/4.1.3/OBDS-4.1.3.md">'], 'research/index.html': ['<meta property="og:image:alt" content="OBDS Research — Open Brand Definition Specification 4.1.3">', '<div class="status">OBDS / 4.1.3 stable</div>', '<span>Companion to OBDS 4.1.3</span>'], 'research/supabrand/index.html': ['<meta property="og:image:alt" content="SUPABRAND research — Open Brand Definition Specification 4.1.3">', '<div class="status">OBDS / 4.1.3 stable</div>', '<span>Companion to OBDS 4.1.3</span>'], 'machine-readable-brand-guidelines/index.html': ['<meta property="og:image:alt" content="Machine-readable brand guidelines — Open Brand Definition Specification 4.1.3">', '<div class="status">OBDS / 4.1.3 stable</div>', '<span>Companion to OBDS 4.1.3</span>'], 'brand-governance-for-ai/index.html': ['<meta property="og:image:alt" content="Brand governance for AI — Open Brand Definition Specification 4.1.3">', '<div class="status">OBDS / 4.1.3 stable</div>', '<span>Companion to OBDS 4.1.3</span>'], 'compare/machine-readable-brand-specifications/index.html': ['<meta property="og:image:alt" content="Machine-readable brand specifications compared — Open Brand Definition Specification 4.1.3">', '<div class="status">OBDS / 4.1.3 stable</div>', '<span>Companion to OBDS 4.1.3</span>', '<td><a href="/spec/4.1.3/OBDS-4.1.3.md">OBDS</a></td>', '<td>4.1.3</td>', '<th>Defined in the specification text</th><th>BRAND.md 0.3.0</th><th>Brando 1.3</th><th>BCP 0.8</th><th>MRBS 1.0.0</th><th>OBDS 4.1.3</th>', '<a href="/spec/4.1.3/OBDS-4.1.3.md">', '<a href="/spec/4.1.3/OBDS-4.1.3.md">OBDS-4.1.3.md</a>'], '404.html': ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,follow"><title>404 | Open Brand Definition</title><style>html,body{height:100%;margin:0}body{display:grid;place-items:center;background:#fff;color:#000;font-family:Helvetica Neue,Helvetica,Arial,sans-serif}main{width:min(90vw,900px);border:1px solid;padding:24px}h1{font-size:clamp(64px,20vw,220px);line-height:.75;letter-spacing:-.08em;margin:0 0 60px}a{color:inherit}</style></head><body><main><h1>404</h1><p>Nothing is defined here. OBDS 4.1.3 stable.</p><p><a href="/">Return to Open Brand Definition</a> &middot; <a href="/what-is-obds/">What is OBDS</a> &middot; <a href="/examples/">Examples</a> &middot; <a href="/spec/4.1.3/OBDS-4.1.3.md">Specification</a></p></main></body></html>'], 'llms.txt': ['Current release: 4.1.3 (stable, 12 September 2026)', 'https://openbranddefinition.org/spec/4.1.3/OBDS-4.1.3.md', 'Schema index: https://openbranddefinition.org/spec/4.1.3/OBDS-4.1.3-SCHEMA-INDEX.json', 'Publication map: https://openbranddefinition.org/spec/4.1.3/OBDS-4.1.3-PUBLICATION-MAP.json', 'Complete package: https://openbranddefinition.org/spec/4.1.3/OBDS-4.1.3-FINAL.zip', 'Quickstart: https://openbranddefinition.org/spec/4.1.3/OBDS-4.1.3-IMPLEMENTER-QUICKSTART.md', 'Changelog: https://openbranddefinition.org/spec/4.1.3/OBDS-4.1.3-CHANGELOG.md', 'Migration: https://openbranddefinition.org/spec/4.1.3/OBDS-4.1.3-MIGRATION.md', 'the licensing wording that was current at the time. Section 32.1 of 4.1.3 is']}
PUBLICATION_URLS = {p: ("/" if p == "index.html" else "/" + p.removesuffix("index.html")) for p in PUBLICATION_EXPECTATIONS}
PUBLICATION_URLS.update({"publication-record.json": "/publication-record.json", "sitemap.xml": "/sitemap.xml"})


# Frozen occurrence multiplicities from the approved publication surface. Counts
# are constants, never derived from candidate bytes. Overlapping expectations
# retain their own contracts (for example a complete row and each link in it).
PUBLICATION_OCCURRENCE_COUNTS = {'index.html': [1, 1, 1, 1, 2, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1, 1], 'authoring/index.html': [1, 1, 1, 1, 1, 1], 'examples/index.html': [1, 1, 1, 1, 1, 1], 'what-is-obds/index.html': [1, 1, 1, 1, 1], 'research/index.html': [1, 1, 1], 'research/supabrand/index.html': [1, 1, 1], 'machine-readable-brand-guidelines/index.html': [1, 1, 1], 'brand-governance-for-ai/index.html': [1, 1, 1], 'compare/machine-readable-brand-specifications/index.html': [1, 1, 1, 1, 1, 1, 3, 1], '404.html': [1], 'llms.txt': [1, 1, 1, 1, 1, 1, 1, 1, 1]}
# These exact legacy entries are superseded by object/key checks below. Keep the
# complete legacy expectations available to the independent mutation matrix.
PUBLICATION_STRUCTURED_FIELDS = {"index.html": {4, 5, 6}, "what-is-obds/index.html": {1}}


# Each textual HTML occurrence is bound to the approved element path. A copy
# elsewhere (including comments or other elements) cannot satisfy that location.
PUBLICATION_ELEMENT_PATHS = {'index.html': {0: [(('html', 1), ('head', 1), ('meta', 6))], 1: [(('html', 1), ('head', 1), ('meta', 15))], 2: [(('html', 1), ('head', 1), ('meta', 16))], 3: [(('html', 1), ('head', 1), ('meta', 25))], 7: [(('html', 1), ('body', 1), ('div', 1), ('header', 1), ('div', 1))], 8: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 1), ('div', 1), ('div', 1), ('span', 1))], 9: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 1), ('div', 2), ('div', 3))], 10: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 13), ('div', 2), ('h2', 1))], 11: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 13), ('div', 2), ('h2', 2))], 12: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 13), ('div', 2), ('div', 1), ('div', 1))], 13: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 13), ('div', 2), ('div', 2), ('div', 1))], 14: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 13), ('div', 2), ('div', 2), ('div', 2))], 15: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 13), ('div', 2), ('div', 2), ('div', 3))], 16: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 13), ('div', 2), ('div', 2), ('div', 4))], 17: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 13), ('div', 2), ('div', 2), ('div', 5))], 18: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 13), ('div', 2), ('div', 2), ('div', 6))], 19: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 13), ('div', 2), ('div', 2), ('div', 8))], 20: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 13), ('div', 2), ('div', 2), ('div', 9))], 21: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 13), ('div', 2), ('div', 2), ('div', 1), ('div', 1), ('span', 1), ('a', 1)), (('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 13), ('div', 2), ('div', 4), ('a', 1))], 22: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 13), ('div', 2), ('div', 2), ('div', 2), ('div', 1), ('span', 1), ('a', 1)), (('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 13), ('div', 2), ('div', 4), ('a', 4))], 23: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 14), ('div', 2), ('div', 6), ('p', 1))], 24: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 14), ('div', 2), ('div', 6), ('p', 2))]}, 'authoring/index.html': {0: [(('html', 1), ('head', 1), ('meta', 15))], 1: [(('html', 1), ('body', 1), ('div', 1), ('header', 1), ('div', 1))], 2: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 1), ('div', 1), ('div', 1), ('span', 2))], 3: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 7), ('div', 2), ('div', 2), ('a', 1))], 4: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 7), ('div', 2), ('div', 2), ('a', 2))], 5: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 7), ('div', 2), ('div', 2), ('a', 3))]}, 'examples/index.html': {0: [(('html', 1), ('head', 1), ('meta', 15))], 1: [(('html', 1), ('body', 1), ('div', 1), ('header', 1), ('div', 1))], 2: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 1), ('div', 1), ('div', 1), ('span', 2))], 3: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 2), ('div', 2), ('p', 2))], 4: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 5), ('div', 2), ('div', 1), ('a', 2))], 5: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 5), ('div', 2), ('div', 1), ('a', 3))]}, 'what-is-obds/index.html': {0: [(('html', 1), ('head', 1), ('meta', 15))], 2: [(('html', 1), ('body', 1), ('div', 1), ('header', 1), ('div', 1))], 3: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 1), ('div', 1), ('div', 1), ('span', 2))], 4: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 2), ('div', 2), ('div', 7), ('a', 2))]}, 'research/index.html': {0: [(('html', 1), ('head', 1), ('meta', 15))], 1: [(('html', 1), ('body', 1), ('div', 1), ('header', 1), ('div', 1))], 2: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 1), ('div', 1), ('div', 1), ('span', 2))]}, 'research/supabrand/index.html': {0: [(('html', 1), ('head', 1), ('meta', 15))], 1: [(('html', 1), ('body', 1), ('div', 1), ('header', 1), ('div', 1))], 2: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 1), ('div', 1), ('div', 1), ('span', 2))]}, 'machine-readable-brand-guidelines/index.html': {0: [(('html', 1), ('head', 1), ('meta', 15))], 1: [(('html', 1), ('body', 1), ('div', 1), ('header', 1), ('div', 1))], 2: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 1), ('div', 1), ('div', 1), ('span', 2))]}, 'brand-governance-for-ai/index.html': {0: [(('html', 1), ('head', 1), ('meta', 15))], 1: [(('html', 1), ('body', 1), ('div', 1), ('header', 1), ('div', 1))], 2: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 1), ('div', 1), ('div', 1), ('span', 2))]}, 'compare/machine-readable-brand-specifications/index.html': {0: [(('html', 1), ('head', 1), ('meta', 15))], 1: [(('html', 1), ('body', 1), ('div', 1), ('header', 1), ('div', 1))], 2: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 1), ('div', 1), ('div', 1), ('span', 2))], 3: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 2), ('div', 2), ('div', 3), ('div', 1), ('table', 1), ('tr', 6), ('td', 1))], 4: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 2), ('div', 2), ('div', 3), ('div', 1), ('table', 1), ('tr', 6), ('td', 4))], 5: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 2), ('div', 2), ('div', 4), ('div', 1), ('table', 1), ('tr', 1), ('th', 1))], 6: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 2), ('div', 2), ('div', 3), ('div', 1), ('table', 1), ('tr', 6), ('td', 1), ('a', 1)), (('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 3), ('div', 2), ('div', 4), ('a', 3)), (('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 3), ('div', 2), ('div', 5), ('div', 1), ('div', 2), ('a', 7))], 7: [(('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 3), ('div', 2), ('div', 5), ('div', 1), ('div', 2), ('a', 7))]}, '404.html': {0: [()]}}


class _PublicationLocations(HTMLParser):
    """Element paths count same-tag siblings; whitespace and JSON key order do not move them."""
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.text = text
        self.lines = text.splitlines(keepends=True)
        self.stack = [((), {})]
        self.locations = {}
        self.feed(text)
        self.close()

    def handle_starttag(self, tag, attrs):
        parent, counts = self.stack[-1]
        counts[tag] = counts.get(tag, 0) + 1
        path = parent + ((tag, counts[tag]),)
        line, column = self.getpos()
        self.locations[path] = sum(map(len, self.lines[:line - 1])) + column
        if tag not in self.VOID:
            self.stack.append((path, {}))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index][0][-1][0] == tag:
                del self.stack[index:]
                break


class _PublicationScripts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.active = None
        self.documents = []

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            assert self.active is None, "Nested publication script"
            types = [value for key, value in attrs if key == "type"]
            assert len(types) <= 1, "Ambiguous publication script type"
            self.active = [] if types == ["application/ld+json"] else None

    def handle_data(self, data):
        if self.active is not None:
            self.active.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.active is not None:
            self.documents.append("".join(self.active))
            self.active = None


def _publication_object(pairs):
    result = {}
    for key, value in pairs:
        assert key not in result, "Duplicate publication JSON-LD key: " + key
        result[key] = value
    return result


def _publication_invalid_constant(value):
    raise ValueError("Invalid publication JSON-LD number: " + value)


def verify_publication_structured(text, rel):
    """Bind each required version/download to its semantic object, not text order."""
    parser = _PublicationScripts()
    parser.feed(text)
    parser.close()
    assert parser.active is None, rel + ": unterminated JSON-LD script"
    documents = [json.loads(raw, object_pairs_hook=_publication_object, parse_constant=_publication_invalid_constant) for raw in parser.documents]
    assert all(isinstance(doc, dict) for doc in documents), rel + ": malformed JSON-LD document"
    def objects(value):
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from objects(child)
        elif isinstance(value, list):
            for child in value:
                yield from objects(child)
    all_objects = list(objects(documents))
    if rel == "index.html":
        graphs = [doc["@graph"] for doc in documents if "@graph" in doc]
        assert len(graphs) == 1 and isinstance(graphs[0], list), "Missing/ambiguous homepage JSON-LD graph"
        graph = graphs[0]
        assert all(isinstance(node, dict) for node in graph), "Malformed homepage JSON-LD graph"
        for identity, kind in [("implementation", "SoftwareSourceCode"), ("obds", "TechArticle")]:
            nodes = [node for node in graph if node.get("@id") == "https://openbranddefinition.org/#" + identity]
            definitions = [node for node in all_objects if node.get("@id") == "https://openbranddefinition.org/#" + identity and set(node) != {"@id"}]
            assert len(definitions) == 1, "Ambiguous JSON-LD definition: " + identity
            assert len(nodes) == 1, "Missing/ambiguous JSON-LD identity: " + identity
            node = nodes[0]
            assert node.get("@type") == kind and node.get("version") == EXPECTED_RELEASE, "Stale/missing JSON-LD version: " + identity
            if identity == "implementation":
                assert node.get("url") == "https://openbranddefinition.org/spec/4.1.3/OBDS-4.1.3-FINAL.zip", "Stale/missing implementation download"
    elif rel == "what-is-obds/index.html":
        articles = [doc for doc in documents if doc.get("url") == "https://openbranddefinition.org/what-is-obds/"]
        assert len(articles) == 1 and articles[0].get("@type") == "TechArticle", "Missing/ambiguous what-is-obds article"
        about = articles[0].get("about")
        assert isinstance(about, dict) and about.get("@type") == "SoftwareSourceCode", "Missing what-is-obds about object"
        assert about.get("version") == EXPECTED_RELEASE, "Stale/missing what-is-obds about version"


# Plain-text declarations retain their approved section and nonblank-line
# occurrence. Blank-line formatting is irrelevant; moving a copy to another
# section cannot repair a stale current declaration or historical qualifier.
PUBLICATION_TEXT_LOCATIONS = {0: [('', 3, 'Current release: 4.1.3 (stable, 12 September 2026)')], 1: [('## Authoritative specification', 0, 'https://openbranddefinition.org/spec/4.1.3/OBDS-4.1.3.md')], 2: [('## Schemas', 0, 'Schema index: https://openbranddefinition.org/spec/4.1.3/OBDS-4.1.3-SCHEMA-INDEX.json')], 3: [('## Schemas', 1, 'Publication map: https://openbranddefinition.org/spec/4.1.3/OBDS-4.1.3-PUBLICATION-MAP.json')], 4: [('## Downloads', 0, 'Complete package: https://openbranddefinition.org/spec/4.1.3/OBDS-4.1.3-FINAL.zip')], 5: [('## Downloads', 1, 'Quickstart: https://openbranddefinition.org/spec/4.1.3/OBDS-4.1.3-IMPLEMENTER-QUICKSTART.md')], 6: [('## Downloads', 2, 'Changelog: https://openbranddefinition.org/spec/4.1.3/OBDS-4.1.3-CHANGELOG.md')], 7: [('## Downloads', 3, 'Migration: https://openbranddefinition.org/spec/4.1.3/OBDS-4.1.3-MIGRATION.md')], 8: [('## Previous releases', 28, 'the licensing wording that was current at the time. Section 32.1 of 4.1.3 is')]}


def verify_publication_text(text):
    sections = {"": []}
    heading = ""
    for line in text.splitlines():
        if line.startswith("## "):
            heading = line
            assert heading not in sections, "Duplicate llms publication section"
            sections[heading] = []
        elif line.strip():
            sections[heading].append(line)
    for index, locations in PUBLICATION_TEXT_LOCATIONS.items():
        field = PUBLICATION_EXPECTATIONS["llms.txt"][index]
        for heading, occurrence, expected_line in locations:
            lines = sections.get(heading, [])
            assert occurrence < len(lines) and lines[occurrence] == expected_line, "Missing/stale llms publication occurrence: " + field



# The only historical root changelog retained by this release. An exemption is
# conditional on its pinned historical bytes, never its wording or directory.
HISTORICAL_CHANGELOG = "OBDS-4.1.2-CHANGELOG.md"
HISTORICAL_CHANGELOG_SHA256 = "sha256:2179678add99a28714a2f7231b07145f7e72224d344e9ee9dd52a0cdfbfe2bca"


# Explicit semantic-role review: this mandatory executable invokes
# verify_changelog_history and verify_licensing_test_source from main. Its
# literals locate authenticated history and construct rejected current claims;
# they publish no operative terms. The digest binds that review to ALL bytes,
# including comments, docstrings and the entry point. Any edit requires a fresh
# role review and digest update: a test filename or marker never establishes it.
# Publication roles take precedence even over an authenticated registration.
NON_CLAIM_EXECUTABLE_SOURCES = {
    "tools/test-task-facts-release.py": {
        "role": "non-claim executable release regression",
        "sha256": 'sha256:0930ee43dbde624c6f65b1e0e8697bdabb8e6dbdb18ed8f8d346a6af53bbb921',
    },
}


def non_claim_executable_source(root, rel):
    """Authenticate an explicit reviewed role; conflicts and drift fail closed."""
    if rel not in NON_CLAIM_EXECUTABLE_SOURCES:
        return False
    record = NON_CLAIM_EXECUTABLE_SOURCES[rel]
    if (rel in PUBLICATION_URLS or not rel.endswith(".py")
            or not isinstance(record, dict)
            or set(record) != {"role", "sha256"}
            or record.get("role") != "non-claim executable release regression"
            or not isinstance(record.get("sha256"), str)
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", record["sha256"])):
        raise ValueError("conflicting or malformed executable regression role")
    if sha256_file(root / rel) != record["sha256"]:
        raise ValueError("executable regression differs from reviewed non-claim bytes")
    return True


def current_licensing_paths(root, package_files, context):
    """Repository publication claims supplement archived package surfaces."""
    paths = list(package_files)
    if context == "repository":
        paths.extend(root / rel for rel in PUBLICATION_URLS)
    return paths


def current_changelog_claims(raw):
    """Bind retained version records to immutable history, returning current text.

    The complete 4.1.2 document is retained as a suffix, including its legacy
    titles and non-version headings. Its digest authenticates that structure;
    merely adding an old version heading never grants historical treatment.
    This works in standalone archives without Git or a second historical file.
    """
    boundary = list(re.finditer(rb"(?m)^# OBDS 4\.1\.2(?: [^\r\n]*)?\n(?=\n## 4\.1\.2\n)", raw))
    if len(boundary) != 1:
        raise ValueError("missing or ambiguous historical changelog boundary")
    prefix, history = raw[:boundary[0].start()], raw[boundary[0].start():]
    if "sha256:" + hashlib.sha256(history).hexdigest() != HISTORICAL_CHANGELOG_SHA256:
        raise ValueError("historical changelog suffix differs from verified 4.1.2 bytes")
    text = prefix.decode("utf-8")
    # Current sections use canonical ATX headings. Reject ambiguous Markdown
    # containers that could turn the historical boundary into current prose.
    if not text.startswith("# OBDS changelog\n\n") or not text.endswith("\n\n"):
        raise ValueError("malformed current changelog document structure")
    if re.search(r"(?m)^\s*(?:`{3,}|~{3,}|={3,}|-{3,})|<!--|<[^>]*>", text):
        raise ValueError("ambiguous current changelog markup")
    current = 0
    for line in text.splitlines():
        if not line.lstrip().startswith("#"):
            continue
        if line == "# OBDS changelog":
            if current or line != text.splitlines()[0]:
                raise ValueError("duplicate current changelog title")
            continue
        if line == "## " + EXPECTED_RELEASE:
            current += 1
        elif (not re.fullmatch(r"#{3,6} [^#\s].*", line)
              or re.search(r"\d+\.\d+(?:\.\d+)?", line)):
            raise ValueError("unclassified or malformed current changelog heading")
    if current != 1 or text.count("# OBDS changelog\n") != 1:
        raise ValueError("missing or duplicate current release section")
    versions = [tuple(map(int, match.groups())) for match in
                re.finditer(rb"(?m)^## (\d+)\.(\d+)\.(\d+)\n", history)]
    if (not versions or versions[0] != (4, 1, 2)
            or any(a <= b for a, b in zip(versions, versions[1:]))):
        raise ValueError("ambiguous historical version section order")
    return text


def retired_licensing_failures(root, paths):
    diagnostics = []
    for path in sorted(set(paths)):
        rel = path.relative_to(root).as_posix()
        try:
            if non_claim_executable_source(root, rel):
                continue
        except (ValueError, OSError) as exc:
            diagnostics.append(f"Invalid licensing surface classification in {rel}: {exc}")
            continue
        if rel == HISTORICAL_CHANGELOG:
            if sha256_file(path) != HISTORICAL_CHANGELOG_SHA256:
                diagnostics.append("Historical changelog bytes changed: " + rel)
            continue
        if rel == "reference/release-gate.py" or rel.startswith("LICENSES/"):
            continue
        if path.suffix.lower() == ".zip":
            continue
        if rel == f"OBDS-{EXPECTED_RELEASE}-CHANGELOG.md":
            try:
                text = current_changelog_claims(path.read_bytes())
            except (ValueError, OSError) as exc:
                diagnostics.append(f"Invalid changelog history/current structure in {rel}: {exc}")
                continue
        else:
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
        for phrase in RETIRED_LICENSING_WORDING:
            if phrase.lower() in text.lower():
                diagnostics.append(f"retired licensing wording {phrase!r} in {rel}")
    return diagnostics


class _ContractClaims(_PublicationLocations):
    """Visible English claims, bound to their existing publication element paths."""
    INLINE = {"strong", "em", "b", "i", "span"}

    def __init__(self, text):
        self.claims = {}
        self.active_claims = []
        super().__init__(text)

    def handle_starttag(self, tag, attrs):
        super().handle_starttag(tag, attrs)
        path = self.stack[-1][0]
        if ("data-copy", "en") in attrs:
            hidden = any(key in {"hidden", "style"} or (key == "aria-hidden" and value == "true") for key, value in attrs)
            self.active_claims.append((path, [" [markup] "] if hidden else [], self.locations[path], tag))
        elif self.active_claims and ((tag in self.INLINE and not attrs) or tag in {"code", "a"}):
            pass
        elif self.active_claims:
            for _, parts, _, _ in self.active_claims:
                parts.append(" [markup] ")

    def handle_data(self, data):
        for _, parts, _, _ in self.active_claims:
            parts.append(data)

    def handle_entityref(self, name):
        from html import unescape
        self.handle_data(unescape("&" + name + ";"))

    def handle_charref(self, name):
        from html import unescape
        self.handle_data(unescape("&#" + name + ";"))

    def handle_endtag(self, tag):
        path = self.stack[-1][0]
        for claim in list(self.active_claims):
            if claim[0] == path and claim[3] == tag:
                line, column = self.getpos()
                end = sum(map(len, self.lines[:line - 1])) + column + len("</" + tag + ">")
                self.claims[path] = (" ".join("".join(claim[1]).split()), claim[2], end)
                self.active_claims.remove(claim)
        super().handle_endtag(tag)


# Filled from the approved four English count-bearing elements, independently
# of the candidate. Existing PUBLICATION_ELEMENT_PATHS remain unchanged.
HOMEPAGE_CONTRACT_PATHS = ((('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 12), ('div', 2), ('div', 1), ('div', 2), ('div', 3), ('p', 1)), (('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 13), ('div', 2), ('div', 2), ('div', 2), ('div', 2)), (('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 13), ('div', 2), ('div', 3), ('div', 2), ('p', 1)), (('html', 1), ('body', 1), ('div', 1), ('main', 1), ('section', 13), ('div', 2), ('div', 4), ('a', 4), ('span', 3)))


def verify_homepage_contracts(text, count=35):
    assert count == 35, "Existing public contract baseline must remain 35"
    parsed = _ContractClaims(text)
    replacements = []
    claim_pattern = re.compile(r"\b35 existing public contracts plus optional Task Facts\b")
    for path in HOMEPAGE_CONTRACT_PATHS:
        assert path in parsed.claims, "Missing homepage public contract claim"
        claim, start, end = parsed.claims[path]
        assert "[markup]" not in claim, "Non-visible or unsupported contract claim markup"
        matches = list(claim_pattern.finditer(claim))
        assert len(matches) == 1, "Homepage must state 35 existing public contracts plus optional Task Facts at " + repr(path)
        remainder = claim[:matches[0].start()] + claim[matches[0].end():]
        assert not re.search(r"\b(?:contracts|Task Facts|including|includes|included|total|nonoptional|required|mandatory|not optional)\b", remainder, re.I), "Conflicting homepage contract claim"
        # Only these count-bearing elements normalize harmless inline formatting;
        # all original required row text, paths, links and multiplicities survive.
        opening_end = text.index(">", start) + 1
        closing_start = text.rfind("</", start, end)
        replacements.append((opening_end, closing_start, claim))
    for path, (claim, _, _) in parsed.claims.items():
        if path not in HOMEPAGE_CONTRACT_PATHS:
            assert not re.search(r"\b(?:\d+|total)\s+(?:existing\s+)?public contracts\b", claim, re.I), "Unclassified homepage public contract count"
    for start, end, claim in sorted(replacements, reverse=True):
        text = text[:start] + claim + text[end:]
    return text


def verify_publication(root=ROOT, inventory=None):
    """Exact required current fields, with separately retained historical fields."""
    ignored = {".git", "reference", "spec", "release-work", "schemas", "value-schemas", "node_modules"}
    pages = {p.relative_to(root).as_posix() for p in root.rglob("*.html") if not (set(p.relative_to(root).parts) & ignored)}
    assert pages == {p for p in PUBLICATION_EXPECTATIONS if p.endswith(".html")}, "Publication HTML inventory missing/extra page"
    for rel, required in PUBLICATION_EXPECTATIONS.items():
        text = (root / rel).read_text(encoding="utf-8")
        if rel == "index.html":
            text = verify_homepage_contracts(text)
        if rel.endswith(".html"):
            verify_publication_structured(text, rel)
        elif rel == "llms.txt":
            verify_publication_text(text)
        locations = _PublicationLocations(text).locations if rel.endswith(".html") else {}
        counts = PUBLICATION_OCCURRENCE_COUNTS[rel]
        assert len(counts) == len(required), "Incomplete publication occurrence contract"
        for index, field in enumerate(required):
            if index in PUBLICATION_STRUCTURED_FIELDS.get(rel, set()):
                continue
            for path in PUBLICATION_ELEMENT_PATHS.get(rel, {}).get(index, []):
                offset = 0 if path == () else locations.get(path)
                assert offset is not None and text.startswith(field, offset), f"{rel}: missing/stale required element {path}: {field[:100]}"
            assert text.count(field) == counts[index], f"{rel}: missing/stale/extra required current occurrence: {field[:100]}"
    record = load(root / "publication-record.json")
    assert record["currentRelease"] == EXPECTED_RELEASE
    assert EXPECTED_RELEASE in record["releases"] and "4.1.2" in record["releases"]
    sitemap = (root / "sitemap.xml").read_text()
    assert "/spec/4.1.3/" in sitemap and "/spec/4.1.2/" in sitemap
    if inventory is not None:
        entries = inventory["publication"]
        assert {e["path"] for e in entries} == set(PUBLICATION_URLS)
        for entry in entries:
            assert entry["url"] == PUBLICATION_URLS[entry["path"]]
            assert hashlib.sha256((root / entry["path"]).read_bytes()).hexdigest() == entry["sha256"], "Frozen publication byte mismatch: " + entry["path"]
    return True


# The human final-closure decision preserves history outside the distributable.
PUBLIC_EVIDENCE_SOURCES = frozenset(['evidence/interop/cycles/cycle-1/implementation-python/evaluate.py', 'evidence/interop/cycles/cycle-1/implementation-python/task-facts.schema.json', 'evidence/interop/cycles/cycle-1/implementation-node/evaluate.mjs', 'evidence/interop/cycles/cycle-1/implementation-node/schemas/task-facts.schema.json'])
PUBLIC_EVIDENCE_MANIFEST_SHA256 = "sha256:62ade7d044608b6a353b89b88ee1548587ed60aa39217bae3f4312010545fea7"
NEUTRAL_WORKSPACES = ("/workspace/obds-release", "/private/tmp/obds-release", "/tmp/obds-release")

# The Historical Audit Evidence Registry, the other half of the 4.1 boundary.
# Membership means the entry must exist in the preserved non-public audit store
# and verify by identity, SHA-256 and byte size. It never means the entry ships,
# and it never stands in for a fresh public conformance result. The registry is
# pinned by its own raw bytes, so a quiet edit to the record of what history
# contains is itself a gate failure.
HISTORICAL_AUDIT_REGISTRY_FILE = "HISTORICAL-AUDIT-REGISTRY.json"
HISTORICAL_AUDIT_REGISTRY_SHA256 = "sha256:73d54c24723695a7aa38304d06b0a0d06c17e32b5ca8a8d67474801a8af84f56"


def public_package_member(rel):
    prefix = "reference/task-facts/1.0/"
    if rel in (prefix + "EVIDENCE-MANIFEST.json", prefix + HISTORICAL_AUDIT_REGISTRY_FILE):
        return False
    if rel.startswith(prefix + "evidence/"):
        return rel[len(prefix):] in PUBLIC_EVIDENCE_SOURCES
    return True


# Root documents of an earlier release. A published release is immutable, so the
# repository keeps 4.1.2's own artefacts exactly as they were published, and one
# of them truthfully records the absolute fixture paths of the machine that built
# it. The private/local-path rule is a rule about what this release distributes,
# not about what the working tree remembers, so it follows distribution: these
# files are exempt from the scan and must stay byte-identical. The exemption is
# not taken on trust — `main` refuses it for anything the package actually ships.
PRIOR_RELEASE_ROOT_DOCUMENT = re.compile(r"^OBDS-(?:PUBLIC-README-)?(\d+\.\d+\.\d+)[^/]*$")


def prior_release_artifact(rel):
    match = PRIOR_RELEASE_ROOT_DOCUMENT.fullmatch(rel)
    return match is not None and match.group(1) != EXPECTED_RELEASE


def neutral_path(value):
    return any(value == base or value.startswith(base + "/") or
               value.startswith(base + "-runtime/") for base in NEUTRAL_WORKSPACES)


def require_neutral_execution(root):
    assert neutral_path(str(root.resolve())), "Fresh release execution requires a neutral workspace"
    assert neutral_path(sys.executable), "Fresh release Python must use a neutral runtime path"
    import shutil
    node = shutil.which("node")
    assert node and neutral_path(node), "Fresh release Node must use a neutral runtime path"


def verify_repository_version(root, context):
    if context == "repository":
        assert (root / "VERSION").read_text(encoding="utf-8").strip() == EXPECTED_RELEASE, "Repository VERSION must equal 4.1.3"


def verify_public_bytes(raw, label):
    # Scan bytes, including binary members and nested archives, without rewriting.
    assert not re.search(rb"/(?:Users|home)/[^/\s]+|(?:[A-Za-z]:)?[\\/](?:Users|Documents and Settings)[\\/]|/(?:private/)?var/folders/", raw), "Private/local path in public member: " + label
    import zipfile
    if zipfile.is_zipfile(io.BytesIO(raw)):
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            for name in archive.namelist():
                verify_public_bytes(archive.read(name), label + "!" + name)


def verify_fresh_provenance(root):
    def visit(value):
        if isinstance(value, dict):
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, str) and value.startswith("/"):
            assert neutral_path(value), "Non-neutral fresh evidence provenance"
    for name in ("OBDS-4.1.3-FOUNDATION-CONFORMANCE.json", "OBDS-4.1.3-TASK-FACTS-CONFORMANCE.json"):
        raw = (root / name).read_bytes()
        verify_public_bytes(raw, name)
        visit(load(root / name))


def verify_public_evidence(root, context):
    tf = root / "reference/task-facts/1.0"
    assert sha256_file(tf / "PUBLIC-EVIDENCE-MANIFEST.json") == PUBLIC_EVIDENCE_MANIFEST_SHA256, "Public evidence inventory differs"
    manifest = load(tf / "PUBLIC-EVIDENCE-MANIFEST.json")
    assert {e["path"] for e in manifest["files"]} == PUBLIC_EVIDENCE_SOURCES
    for entry in manifest["files"]:
        source = tf / entry["path"]
        assert source.stat().st_size == entry["bytes"] and sha256_file(source) == "sha256:" + entry["sha256"], "Public source evidence differs"
    if context == "extracted-archive":
        assert not (tf / "EVIDENCE-MANIFEST.json").exists(), "Historical audit inventory must remain non-public"
        observed = {p.relative_to(tf).as_posix() for p in (tf / "evidence").rglob("*") if p.is_file() and not is_generated_cache(p, root)}
        assert observed == PUBLIC_EVIDENCE_SOURCES, "Public evidence contains historical or extra records"
    verify_fresh_provenance(root)


def verify_historical_audit(root, context):
    """Audit-store integrity, deliberately not a conformance result.

    `verify_public_evidence` answers what the public archive may contain. This
    answers the other half of the 4.1 boundary: whether the history the
    release says it preserved is still that history, byte for byte, in a store
    the public archive never needs. The two are separate on purpose. Private
    evidence that verifies here proves nothing about a public claim, and a
    public claim that passes there is not allowed to lean on this store.

    Substitution is the failure worth naming: a member still present, still the
    declared size, no longer the declared bytes. Size and digest are therefore
    both checked against two independent records, the registry and the
    inventory, and the two have to agree with each other as well as with disk.
    """
    tf = root / "reference/task-facts/1.0"
    registry_path = tf / HISTORICAL_AUDIT_REGISTRY_FILE
    inventory_name = "EVIDENCE-MANIFEST.json"
    if context != "repository":
        assert not registry_path.exists(), "Historical audit registry must remain non-public"
        assert not (tf / inventory_name).exists(), "Historical audit inventory must remain non-public"
        return True

    assert sha256_file(registry_path) == HISTORICAL_AUDIT_REGISTRY_SHA256, "Historical audit registry differs"
    registry = load(registry_path)
    assert registry["kind"] == "task-facts-historical-audit-evidence-registry"
    assert registry["role"] == "historical-non-public-audit-evidence", "Historical audit role differs"
    assert registry["status"] == "preserved-immutable", "Historical audit status differs"
    assert registry["publicSurface"] is False, "Historical audit evidence is not a public surface"

    declared = registry["inventory"]
    assert declared["path"] == inventory_name
    inventory_path = tf / declared["path"]
    raw = inventory_path.read_bytes()
    assert len(raw) == declared["bytes"], "Historical audit inventory size differs"
    assert hashlib.sha256(raw).hexdigest() == declared["sha256"], "Historical audit inventory differs"
    inventory = load(inventory_path)
    assert len(inventory["files"]) == declared["files"], "Historical audit inventory count differs"
    members = {entry["path"]: entry for entry in inventory["files"]}
    assert len(members) == len(inventory["files"]), "Duplicate historical audit inventory path"

    observed = {p.relative_to(tf).as_posix() for p in (tf / "evidence").rglob("*")
                if p.is_file() and not is_generated_cache(p, root)}
    assert observed == set(members), "Historical audit store membership differs"

    for entry in inventory["files"]:
        source = tf / entry["path"]
        assert source.is_file(), "Missing historical audit member: " + entry["path"]
        raw = source.read_bytes()
        assert len(raw) == entry["bytes"], "Historical audit size mismatch: " + entry["path"]
        assert hashlib.sha256(raw).hexdigest() == entry["sha256"], "Historical audit hash mismatch: " + entry["path"]

    for group in ("publicSurfaceExclusions", "nonPublicExecutableSources"):
        for entry in registry[group]:
            recorded = members.get(entry["path"])
            assert recorded is not None, "Historical audit member outside the inventory: " + entry["path"]
            assert recorded["bytes"] == entry["bytes"] and recorded["sha256"] == entry["sha256"], \
                "Historical audit registry and inventory disagree: " + entry["path"]
            assert not public_package_member("reference/task-facts/1.0/" + entry["path"]), \
                "Historical audit member is also a public package member: " + entry["path"]
    return True


def verify_task_facts(root=ROOT, execute=True):
    import importlib.util
    import tempfile
    verify_task_facts_schema(root)
    tf = root / "reference/task-facts/1.0"
    context = package_context(root)
    verify_public_evidence(root, context)
    if context == "repository":
        manifest = load(tf / "EVIDENCE-MANIFEST.json")
        observed = {p.relative_to(tf).as_posix() for p in (tf / "evidence").rglob("*") if p.is_file()}
        assert observed == {e["path"] for e in manifest["files"]}, "Evidence membership differs"
        for entry in manifest["files"]:
            raw = (tf / entry["path"]).read_bytes()
            assert len(raw) == entry["bytes"] and hashlib.sha256(raw).hexdigest() == entry["sha256"], "Evidence digest mismatch: " + entry["path"]
    spec = importlib.util.spec_from_file_location("task_facts_protocol", tf / "compare.py")
    protocol = importlib.util.module_from_spec(spec); spec.loader.exec_module(protocol)
    suite, suite_root, suite_hash = protocol.load_suite(tf / "SUITE.json")
    result = load(root / "OBDS-4.1.3-TASK-FACTS-CONFORMANCE.json")
    assert result["passed"] is True and result["productionIntegration"] is False
    assert result["suiteHash"] == suite_hash and len(result["subjects"]) == 2
    from jsonschema import Draft202012Validator
    validator = Draft202012Validator(json.loads((tf / "RESULT.schema.json").read_text()))
    for subject, (name, command) in zip(result["subjects"], [("research-python", [sys.executable, str(tf / "evidence/interop/cycles/cycle-1/implementation-python/evaluate.py")]), ("research-node", ["node", str(tf / "evidence/interop/cycles/cycle-1/implementation-node/evaluate.mjs")])]):
        validator.validate(subject)
        assert subject["implementation"]["name"] == name and subject["suiteHash"] == suite_hash
        assert subject["passed"] and subject["failed"] == subject["skipped"] == 0
        assert len(subject["groups"]) == 2
        for measured, group in zip(subject["groups"], suite["groups"]):
            assert measured["name"] == group["name"] and measured["passed"]
            actual, mismatches = protocol.compare(__import__("base64").b64decode(measured["stdout"]["base64"]), measured["processExit"], protocol.expected(suite_root, group))
            assert not mismatches and actual == measured["actual"]
        if execute:
            with tempfile.TemporaryDirectory() as d:
                output = Path(d) / "result.json"
                subprocess.run([sys.executable, str(tf / "run-suite.py"), "--suite", str(tf / "SUITE.json"), "--result", str(output), "--implementation-name", name, "--implementation-version", "frozen-cycle-1", "--", *command], cwd=root, check=True)
                fresh = load(output)
                assert fresh["passed"] and fresh["suiteHash"] == suite_hash
                assert [g["actual"] for g in fresh["groups"]] == [g["actual"] for g in subject["groups"]]
                assert fresh["implementation"]["executables"][-1]["sha256"] == subject["implementation"]["executables"][-1]["sha256"]
    return True


def package_context(root=ROOT):
    """An archive is identified by positive flattened contract layout and manifest."""
    if (root / "schemas/1.0.0/brand-manifest.schema.json").is_file():
        return "repository"
    manifest = load(root / "PACKAGE-MANIFEST.json")
    assert manifest["version"] == EXPECTED_RELEASE
    assert (root / "schemas/brand-manifest.schema.json").is_file()
    assert manifest["normativeSpecification"] == "OBDS-4.1.3.md"
    return "extracted-archive"


# ---------------------------------------------------------------------------
# Current-state surfaces that step 15 claimed and never read. Added in 4.1.3.
#
# Step 15's comment has said since 1.1.3 that "the README" is a checked
# current-release surface. The code never checked the README's current release;
# step 8 reads it only for count claims. 4.1.1 and 4.1.2 shipped a README that
# named 4.1.0 as the current release and linked five 4.1.0 root documents: four
# left the root with 4.1.1 and the changelog with 4.1.2, so on GitHub the links
# to the specification, the quickstart and the test result were dead. The public
# README credited 4.0.0's five production-boundary closures to 4.1.0, a
# sentence carried forward by version replacement, and the Task Facts pages
# still introduced a published capability as a prospective internal candidate.
# Each function returns the problems it finds rather than asserting, so
# tools/test-final-closure.py can drive it with the exact defective text.
# ---------------------------------------------------------------------------

README_CURRENT_LINE = re.compile(r"^OBDS (\d+\.\d+\.\d+), stable, (\d{1,2} [A-Z][a-z]+ \d{4})\. Published at", re.M)
README_CRITICAL_DOCUMENTS = ("OBDS-{r}.md", "OBDS-{r}-IMPLEMENTER-QUICKSTART.md",
                             "OBDS-{r}-TEST-RESULT.json", "OBDS-{r}-CHANGELOG.md",
                             "OBDS-{r}-MIGRATION.md")
ROOT_RELEASE_DOCUMENT = re.compile(r"(?<![\w-])(?:spec/(\d+\.\d+\.\d+)/)?OBDS-(?:PUBLIC-README-)?(\d+\.\d+\.\d+)(?=[-.])")
PRESENT_TENSE_RELEASE = re.compile(
    r"\bOBDS (\d+\.\d+\.\d+) (?:is|adds|closes|changes|corrects|repairs|fixes|introduces)\b"
    r"|\bcurrent (?:stable )?release (?:is|:) ?(?:OBDS )?(\d+\.\d+\.\d+)", re.I)
PROSPECTIVE_WORDING = re.compile(r"(?i)\bprospective\b|\binternal candidate\b")
MARKDOWN_LINK = re.compile(r"\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
TASK_FACTS_STATUS = "> **Status: published.**"
MONTHS = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")


def long_date(iso):
    year, month, day = (int(part) for part in iso.split("-"))
    return f"{day} {MONTHS[month - 1]} {year}"


def current_release_date(root=ROOT, release=EXPECTED_RELEASE):
    """ISO date of this release, read from its own changelog section.

    The changelog ships in both layouts; publication-record.json does not, so it
    is cross-checked against the changelog in the repository rather than used as
    the source.
    """
    text = (root / f"OBDS-{release}-CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(r"(?m)^## " + re.escape(release) + r"\n\n(\d{1,2}) ([A-Z][a-z]+) (\d{4})\.\n", text)
    if match is None:
        raise ValueError(f"OBDS-{release}-CHANGELOG.md carries no dated {release} section")
    day, month, year = match.groups()
    return f"{int(year):04d}-{MONTHS.index(month) + 1:02d}-{int(day):02d}"


def root_document_versions(text):
    """Releases named by root release documents. A path under spec/<v>/ naming
    that same release is a deliberate link into history, not a current document."""
    found = set()
    for snapshot, named in ROOT_RELEASE_DOCUMENT.findall(text):
        if snapshot != named:
            found.add(named)
    return found


def markdown_targets(text):
    """Relative link targets, without anchors. External and in-page links are skipped."""
    targets = []
    for target in MARKDOWN_LINK.findall(text):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        targets.append(target.split("#", 1)[0])
    return [t for t in targets if t]


def package_path_exists(root, rel, context="repository"):
    """Whether a package-relative link target exists in the layout being gated.

    The README is written for the repository, where every contract sits at its
    published URL path, and there every link must resolve. An extracted archive
    flattens the frozen contract surface, so its links into schemas/ and
    value-schemas/ are not resolved there; every other link still is.
    """
    import posixpath
    rel = posixpath.normpath(rel.rstrip("/") or ".")
    if rel == ".." or rel.startswith(("../", "/")):
        return False
    if context != "repository" and rel.startswith(("schemas/", "value-schemas/")):
        return True
    return (root / rel).exists()


def package_relative_exists(root, base, target, context="repository"):
    """A link target relative to `base`, which must stay inside the package."""
    import posixpath
    rel = posixpath.normpath(posixpath.join(base, target))
    return not (rel == ".." or rel.startswith("../")) and package_path_exists(root, rel, context)


def current_claim_problems(label, text, release=EXPECTED_RELEASE):
    problems = []
    for named in sorted({a or b for a, b in PRESENT_TENSE_RELEASE.findall(text)}):
        if named != release:
            problems.append(f"{label} describes OBDS {named} in the present tense as if it were current")
    if PROSPECTIVE_WORDING.search(text):
        problems.append(f"{label} still describes a published release or capability as prospective")
    return problems


def readme_problems(text, release, release_date, exists):
    """Current-state checks for README.md. `exists(rel)` resolves a link target."""
    problems = []
    lines = README_CURRENT_LINE.findall(text)
    if len(lines) != 1:
        problems.append(f"README.md carries {len(lines)} current release lines, expected exactly one")
    for named, date in lines:
        if named != release:
            problems.append(f"README.md announces OBDS {named} as the current release, not {release}")
        if date != long_date(release_date):
            problems.append(f"README.md dates the current release {date}, not {long_date(release_date)}")
    for named in sorted(root_document_versions(text)):
        if named != release:
            problems.append(f"README.md names a root release document of OBDS {named}, not {release}")
    targets = markdown_targets(text)
    for pattern in README_CRITICAL_DOCUMENTS:
        name = pattern.format(r=release)
        if name not in targets:
            problems.append(f"README.md does not link {name}")
    for target in sorted(set(targets)):
        if not exists(target):
            problems.append(f"README.md links a file that does not exist: {target}")
    problems.extend(current_claim_problems("README.md", text, release))
    return problems


def task_facts_status_problems(suite_readme, adoption, release, exists):
    """The suite README states the current status; ADOPTION.md keeps its record under a status block.

    `exists(rel)` resolves a target relative to reference/task-facts/1.0/.
    """
    label = "reference/task-facts/1.0/README.md"
    problems = current_claim_problems(label, suite_readme, release)
    if "published, optional" not in suite_readme:
        problems.append(f"{label} does not state that Task Facts 1.0 is published and optional")
    if "`productionIntegration: false`" not in suite_readme:
        problems.append(f"{label} does not state the productionIntegration: false limitation")
    for named in sorted(root_document_versions(suite_readme)):
        if named != release:
            problems.append(f"{label} names a root release document of OBDS {named}, not {release}")
    for target in sorted(set(markdown_targets(suite_readme))):
        if not exists(target):
            problems.append(f"{label} links a file that does not exist: {target}")
    # The record below the block keeps its pre-publication wording on purpose,
    # so only the block is read, and the block quotes that wording to explain it.
    status = adoption.split("\n\n", 1)[0]
    if not status.startswith(TASK_FACTS_STATUS):
        problems.append("reference/task-facts/1.0/ADOPTION.md does not open with its published status block")
    elif "`productionIntegration: false`" not in status:
        problems.append("reference/task-facts/1.0/ADOPTION.md status block drops the productionIntegration: false limitation")
    return problems


# Open Graph cards. The eight cards under og/ were rendered for 4.0.4, and the
# cards published with 4.1.0, 4.1.1 and 4.1.2 still printed 4.0.4 while each
# page's og:image:alt named the current release. A PNG cannot be read for its
# text, so tools/build-og-images.py stamps each card with the release it was
# rendered for, in a tEXt chunk, and this reads the stamp back. og/ is website
# material, not package material, so the check runs in the repository only.
OG_STAMP_KEYWORD = "OBDS-Release"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
OG_IMAGE_META = re.compile(r'<meta property="og:image" content="https://openbranddefinition\.org/(og/[a-z0-9-]+\.png)">')


def png_text_chunks(raw):
    """Every tEXt chunk of a PNG as keyword -> text. Raises ValueError on anything that is not a PNG."""
    import struct
    import zlib
    if not raw.startswith(PNG_SIGNATURE):
        raise ValueError("not a PNG")
    chunks, offset = {}, len(PNG_SIGNATURE)
    while offset < len(raw):
        if offset + 8 > len(raw):
            raise ValueError("truncated PNG chunk header")
        length, kind = struct.unpack(">I4s", raw[offset:offset + 8])
        body = raw[offset + 8:offset + 8 + length]
        crc = raw[offset + 8 + length:offset + 12 + length]
        if len(body) != length or len(crc) != 4 or struct.unpack(">I", crc)[0] != zlib.crc32(kind + body):
            raise ValueError("corrupt PNG chunk")
        if kind == b"tEXt" and b"\0" in body:
            keyword, text = body.split(b"\0", 1)
            chunks[keyword.decode("latin-1")] = text.decode("latin-1")
        offset += 12 + length
        if kind == b"IEND":
            return chunks
    raise ValueError("PNG ends before IEND")


def og_card_problems(root=ROOT, release=EXPECTED_RELEASE):
    problems = []
    pages = [p for p in PUBLICATION_EXPECTATIONS if p.endswith("index.html")]
    for page in pages:
        found = OG_IMAGE_META.findall((root / page).read_text(encoding="utf-8"))
        if len(found) != 1:
            problems.append(f"{page} declares {len(found)} og:image cards, expected one")
            continue
        card = root / found[0]
        if not card.is_file():
            problems.append(f"{page}: Open Graph card {found[0]} is missing")
            continue
        try:
            stamp = png_text_chunks(card.read_bytes()).get(OG_STAMP_KEYWORD)
        except ValueError as exc:
            problems.append(f"{found[0]} is not a readable PNG: {exc}")
            continue
        if stamp != release:
            problems.append(f"{found[0]} was rendered for {stamp or 'no recorded release'}, not {release}")
    return problems


def spec_date_problems(spec_text, release, release_date):
    """Step 14 reads the specification's own Version line. Its Date line moves
    with every release too, and nothing read it."""
    stamped = re.findall(r"(?m)^\*\*Date:\*\*\s*(\S+)", spec_text.split("\n---", 1)[0])
    if stamped != [release_date]:
        return [f"OBDS-{release}.md is dated {stamped or 'nowhere'}, not {release_date}"]
    return []


def current_surface_problems(root=ROOT, context="repository", release=EXPECTED_RELEASE):
    """Everything above, for the layout being gated."""
    problems = []
    release_date = current_release_date(root, release)
    problems += readme_problems((root / "README.md").read_text(encoding="utf-8"), release, release_date,
                                lambda rel: package_path_exists(root, rel, context))
    problems += spec_date_problems((root / f"OBDS-{release}.md").read_text(encoding="utf-8"), release, release_date)
    public = (root / f"OBDS-PUBLIC-README-{release}.md").read_text(encoding="utf-8")
    problems += current_claim_problems(f"OBDS-PUBLIC-README-{release}.md", public, release)
    if f"**OBDS {release}. Stable. {release_date}.**" not in public:
        problems.append(f"OBDS-PUBLIC-README-{release}.md does not state **OBDS {release}. Stable. {release_date}.**")
    for name in ("IMPLEMENTER-QUICKSTART.md", "ARCHITECTURE.md", "TEST-REQUIREMENTS.md", "MIGRATION.md"):
        rel = f"OBDS-{release}-{name}"
        problems += current_claim_problems(rel, (root / rel).read_text(encoding="utf-8"), release)
    tf = root / "reference/task-facts/1.0"
    problems += task_facts_status_problems(
        (tf / "README.md").read_text(encoding="utf-8"), (tf / "ADOPTION.md").read_text(encoding="utf-8"),
        release, lambda rel: package_relative_exists(root, "reference/task-facts/1.0", rel, context))
    if context == "repository":
        record = load(root / "publication-record.json")
        if record.get("stableReleaseDate") != release_date or record.get("releases", {}).get(release, {}).get("date") != release_date:
            problems.append(f"publication-record.json does not date {release} {release_date}, as its changelog does")
        problems += og_card_problems(root, release)
    return problems


def main() -> int:
    try:
        context = package_context()
        verify_repository_version(ROOT, context)
        verify_historical_audit(ROOT, context)
        verify_task_facts()
        exempt = []
        for path in package_text_files():
            rel = path.relative_to(ROOT).as_posix()
            if prior_release_artifact(rel):
                exempt.append(rel)
                continue
            verify_public_bytes(path.read_bytes(), rel)
        # The exemption is a claim about distribution, so distribution answers it,
        # and only this release's own manifest is allowed to answer.
        manifest = load(ROOT / "PACKAGE-MANIFEST.json")
        assert manifest["version"] == EXPECTED_RELEASE, "Package manifest is not this release"
        shipped = {entry["path"] for entry in manifest["files"]}
        leaked = sorted(set(exempt) & shipped)
        assert not leaked, "Prior-release artefacts in the current release package: " + ", ".join(leaked)
        if context == "repository":
            inventory_path = ROOT / f"release-work/{EXPECTED_RELEASE}/RC-INVENTORY.json"
            inventory = load(inventory_path) if inventory_path.is_file() else None
            verify_publication(inventory=inventory)
        print("Release verification context:", context)
    except (AssertionError, OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print("RELEASE GATE: FAIL Task Facts/publication:", exc)
        return 1
    test_result = load(ROOT / f"OBDS-{EXPECTED_RELEASE}-TEST-RESULT.json")
    audit = load(ROOT / f"OBDS-{EXPECTED_RELEASE}-FINAL-AUDIT.json")

    validate_schemas(test_result, audit)

    # 1. counts must sum. This is the check that would have caught adversarial=105.
    for label, doc, total_key in (
        ("TEST-RESULT", test_result, "passedCount"),
        ("FINAL-AUDIT", audit, "testsPassed"),
    ):
        counts = doc["suiteCounts"]
        total = doc[total_key]
        check(
            sum(counts.values()) == total,
            f"{label}: sum(suiteCounts)={sum(counts.values())} != {total_key}={total}",
        )
        check(counts == EXPECTED_SUITE_COUNTS, f"{label}: suiteCounts != verified run")
        check(total == EXPECTED_TOTAL, f"{label}: {total_key} != {EXPECTED_TOTAL}")

    # 2. the two metadata files must agree with each other.
    check(test_result["suiteCounts"] == audit["suiteCounts"], "suiteCounts differ between TEST-RESULT and FINAL-AUDIT")
    check(test_result["testOutputHash"] == audit["testOutputHash"], "testOutputHash differs between TEST-RESULT and FINAL-AUDIT")
    check(test_result["release"] == audit["release"] == EXPECTED_RELEASE, "release identity mismatch")
    check(test_result["status"] == audit["status"] == EXPECTED_STATUS, "status is not stable in both files")
    check(test_result["failedCount"] == 0 and audit["testsFailed"] == 0, "declared failures are not zero")

    # 3. the declared hash must be the hash of the actual test output.
    output_path = ROOT / f"OBDS-{EXPECTED_RELEASE}-TEST-OUTPUT.txt"
    actual = sha256_file(output_path)
    check(
        test_result["testOutputHash"] == actual,
        f"testOutputHash != sha256(OBDS-{EXPECTED_RELEASE}-TEST-OUTPUT.txt) {actual}",
    )

    # 4. the test output itself must agree with the declared counts.
    output = output_path.read_text(encoding="utf-8")
    check(f"TOTAL: {EXPECTED_TOTAL} passed" in output, "test output does not report the declared total")
    check("failed" not in output, "test output reports failures")
    check("error" not in output.lower(), "test output reports errors")
    check("skipped" not in output, "test output reports skipped cases")
    for suite, count in EXPECTED_SUITE_COUNTS.items():
        check(
            re.search(rf"^## {re.escape(suite)}$", output, re.M) is not None,
            f"test output missing suite header {suite}",
        )
        check(f"{count} passed in " in output, f"test output missing '{count} passed' for {suite}")

    # 4b. section 26 conformance-result identifiers.
    #
    # Section 26 lets an implementation claim conformance only when the result
    # identifies implementation name and version, suite hash, profile and the
    # counts, and no required case was skipped or changed. Before 1.0.4 the
    # published result carried the counts and nothing else, so the project's own
    # release did not satisfy the rule it imposes on every other implementer.
    # These checks exist so that cannot happen again.
    implementation = test_result.get("implementation") or {}
    check(bool(implementation.get("name")), "TEST-RESULT: section 26 requires implementation.name")
    check(bool(implementation.get("version")), "TEST-RESULT: section 26 requires implementation.version")
    check(
        test_result.get("obdsVersion") == EXPECTED_RELEASE,
        f"TEST-RESULT: obdsVersion != {EXPECTED_RELEASE}",
    )
    check(
        test_result.get("requiredCasesSkippedOrChanged") is False,
        "TEST-RESULT: section 26 clause 4 requires requiredCasesSkippedOrChanged false",
    )
    check(test_result.get("skippedCount") == 0, "TEST-RESULT: skippedCount is not zero")
    check(bool(test_result.get("claimScope")), "TEST-RESULT: section 26 requires the scope of the claim")

    profiles = test_result.get("conformanceProfiles") or []
    check(bool(profiles), "TEST-RESULT: section 26 requires at least one named profile")
    ids = {p.get("id") for p in profiles}
    check(
        ids <= {"obds-foundation", "compiled-runtime"},
        f"TEST-RESULT: undefensible conformance profile(s) {sorted(ids - {'obds-foundation', 'compiled-runtime'})}; "
        "a profile needs a declared suite or a per-requirement evidence list",
    )
    check("obds-foundation" in ids, "TEST-RESULT: obds-foundation must be claimed")
    for entry in profiles:
        check(len(entry.get("basis") or "") >= 40,
              f"TEST-RESULT: profile {entry.get('id')} has no basis statement")
        if entry.get("id") == "compiled-runtime":
            _check_section_26_2_evidence(entry)

    executed = test_result.get("executedSuites") or {}
    check(
        (executed.get("counts") or {}) == EXPECTED_SUITE_COUNTS,
        "TEST-RESULT: executedSuites.counts != the verified run",
    )
    check(len(executed.get("note") or "") >= 40,
          "TEST-RESULT: executedSuites needs a note stating it carries no conformance claim")

    # The declared suite hash must be the hash of the suite actually on disk.
    # suite_files() and suite_hash() live in this file, which ships inside the
    # release archive, so anyone who downloads the package can recompute the
    # suite identity without the build tooling.
    suite_pairs = suite_files()
    actual_suite_hash = suite_hash(suite_pairs)
    check(
        test_result.get("suiteHash") == actual_suite_hash,
        f"TEST-RESULT: suiteHash != sha256 of the suite on disk {actual_suite_hash}",
    )
    check(
        test_result.get("suiteFileCount") == len(suite_pairs),
        f"TEST-RESULT: suiteFileCount {test_result.get('suiteFileCount')} "
        f"!= {len(suite_pairs)} suite files on disk",
    )

    # 4c. the official declared Foundation conformance suite must be green.
    #
    # This is separate from the aggregate run and must not be added to it: all
    # but one of its declared cases exercise the same fixtures and examples as the
    # pytest suites, so counting both would double-count the same coverage.
    suite_doc = None
    suite_yaml = ROOT / "reference" / "foundation" / "conformance-suite.yaml"
    declared_cases = 0
    if suite_yaml.is_file():
        try:
            suite_doc = _load_governed(suite_yaml)
            declared_cases = len(suite_doc.get("cases", []))
        except Exception as exc:  # pragma: no cover
            failures.append(f"cannot read the declared conformance suite: {exc}")
    check(declared_cases > 0, "the declared conformance suite has no cases")
    foundation_conformance = check_official_foundation_conformance(declared_cases)

    # The published Foundation conformance result must match what just ran.
    fc_path = ROOT / f"OBDS-{EXPECTED_RELEASE}-FOUNDATION-CONFORMANCE.json"
    if not fc_path.is_file():
        failures.append(
            f"missing OBDS-{EXPECTED_RELEASE}-FOUNDATION-CONFORMANCE.json; the official "
            "Foundation conformance run was not published with this release"
        )
    elif foundation_conformance is not None:
        published = load(fc_path)
        for key in ("profile", "passedCount", "failedCount", "passed", "suiteHash"):
            check(
                published.get(key) == foundation_conformance.get(key),
                f"published Foundation conformance {key} "
                f"{published.get(key)!r} != freshly executed {foundation_conformance.get(key)!r}",
            )
        check(
            published.get("obdsRelease") == EXPECTED_RELEASE,
            f"published Foundation conformance obdsRelease != {EXPECTED_RELEASE}",
        )
        published_ids = sorted(c["id"] for c in published.get("cases", []))
        declared_ids = sorted(c["id"] for c in (suite_doc or {}).get("cases", []))
        check(
            published_ids == declared_ids,
            "published Foundation conformance does not cover exactly the declared cases",
        )

    # 5. public schema surface.
    schemas = sorted(p.name for p in SCHEMAS_DIR.glob("*.json"))
    value_schemas = sorted(p.name for p in VALUE_SCHEMAS_DIR.glob("*.json"))
    check(len(schemas) == EXPECTED_PUBLIC_SCHEMAS, f"public schema count {len(schemas)} != {EXPECTED_PUBLIC_SCHEMAS}")
    check(
        len(value_schemas) == EXPECTED_PUBLIC_VALUE_SCHEMAS,
        f"public value schema count {len(value_schemas)} != {EXPECTED_PUBLIC_VALUE_SCHEMAS}",
    )
    check(audit["publicSchemaCount"] == len(schemas), "audit publicSchemaCount != disk")
    check(audit["publicValueSchemaCount"] == len(value_schemas), "audit publicValueSchemaCount != disk")

    # The 1.1 contract surface: exactly one file, and the 1.0.0 surface untouched.
    v11 = ROOT / "schemas" / "1.1.0"
    if not v11.is_dir():
        v11 = ROOT / "schemas" / "1.1.0"
    found_v11 = {p.name for p in v11.glob("*.json")} if v11.is_dir() else set()
    check(
        found_v11 == EXPECTED_V11_SCHEMAS,
        f"schemas/1.1.0/ contains {sorted(found_v11)}, expected {sorted(EXPECTED_V11_SCHEMAS)}",
    )
    if found_v11 == EXPECTED_V11_SCHEMAS:
        v11_doc = load(v11 / "compiled-context.schema.json")
        check(
            v11_doc.get("$id") == "https://openbranddefinition.org/schemas/1.1.0/compiled-context.schema.json",
            "schemas/1.1.0/compiled-context.schema.json has the wrong $id",
        )
        check(
            v11_doc["properties"]["schemaVersion"].get("const") == "1.1.0",
            "the 1.1.0 contract does not pin schemaVersion to 1.1.0",
        )
        check(
            "governedResultHash" in v11_doc.get("required", []),
            "the 1.1.0 contract does not require governedResultHash",
        )

    index = load(ROOT / f"OBDS-{EXPECTED_RELEASE}-SCHEMA-INDEX.json")
    check(sorted(i["file"] for i in index["schemas"]) == schemas, "schema index does not match schemas/")
    check(sorted(i["file"] for i in index["valueSchemas"]) == value_schemas, "schema index does not match value-schemas/")
    versioned_index = index.get("versionedSchemas", [])
    ids = ([i["id"] for i in index["schemas"]]
           + [i["id"] for i in index["valueSchemas"]]
           + [i["id"] for i in versioned_index])
    check(len(ids) == len(set(ids)), "duplicate $id in schema index")
    check(
        index.get("release") == EXPECTED_RELEASE,
        f"schema index release is {index.get('release')!r}, expected {EXPECTED_RELEASE!r}",
    )

    # 5b. no normative contract change: the public schema surface must equal 1.0.0.
    lines = []
    for label, directory in (("schemas", SCHEMAS_DIR), ("value-schemas", VALUE_SCHEMAS_DIR)):
        for path in sorted(directory.glob("*.json")):
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            lines.append(f"{label}/{path.name}:{digest}")
    surface = hashlib.sha256("\n".join(lines).encode()).hexdigest()
    check(
        surface == FROZEN_SCHEMA_SURFACE,
        f"public schema surface changed since 1.0.0: {surface} != {FROZEN_SCHEMA_SURFACE}",
    )
    check(
        all(i["id"].startswith("https://openbranddefinition.org/schemas/1.0.0/") for i in index["schemas"]),
        "schema $id no longer points at the 1.0.0 contract",
    )
    check(
        all(i["id"].startswith("https://openbranddefinition.org/value-schemas/1.0.0/") for i in index["valueSchemas"]),
        "value schema $id no longer points at the 1.0.0 contract",
    )

    # 5c. normative contract identity against the previous release.
    def _canon_fingerprint(payload) -> str:
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()

    registry = load(ROOT / f"OBDS-{EXPECTED_RELEASE}-CAPABILITY-REGISTRY.json")
    registry = {k: v for k, v in registry.items() if k != "release"}
    _release_model = dict(registry.get("releaseModel", {}))
    _release_model.pop("normativeSpecification", None)  # release filename is packaging
    registry["releaseModel"] = _release_model
    pubmap = load(ROOT / f"OBDS-{EXPECTED_RELEASE}-PUBLICATION-MAP.json")
    # The identity fingerprint covers the frozen OBDS 1.0.0 surface only.
    # Contracts published beside it at their own version are checked separately,
    # in 5e, so that adding one can never be mistaken for moving the 27.
    def _frozen_only(entries):
        return [
            e for e in entries
            if e["id"].startswith("https://openbranddefinition.org/schemas/1.0.0/")
            or e["id"].startswith("https://openbranddefinition.org/value-schemas/1.0.0/")
        ]

    actual_contract = {
        "capability-registry": _canon_fingerprint(prior_registry(registry)),
        "schema-index": _canon_fingerprint(
            {"schemas": index["schemas"], "valueSchemas": index["valueSchemas"]}
        ),
        "publication-map-contracts": _canon_fingerprint(_frozen_only(pubmap["contracts"])),
    }
    for key, expected in PRIOR_CONTRACT_FINGERPRINTS.items():
        check(
            actual_contract[key] == expected,
            f"normative contract moved since {PRIOR_RELEASE}: {key} "
            f"{actual_contract[key]} != {expected}",
        )
    check(
        pubmap["schemaSurfaceFingerprint"] == f"sha256:{FROZEN_SCHEMA_SURFACE}",
        "publication map schemaSurfaceFingerprint does not match the frozen surface",
    )
    check(pubmap["schemaContractVersion"] == "1.0.0", "schema contract version moved")

    # 5d. the licensing position must be complete and unmodified.
    for rel, digest in REQUIRED_LICENCE_FILES.items():
        path = ROOT / rel
        if not path.is_file():
            failures.append(f"missing licence text {rel}")
            continue
        actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        check(
            actual_digest == digest,
            f"{rel} is not the unmodified standard licence text: {actual_digest} != {digest}",
        )
    for name in REQUIRED_LICENCE_DOCS:
        check((ROOT / name).is_file(), f"missing {name}")

    # 5e. Package claims and the complete active publication inventory are current
    # surfaces. Historical bytes have one exact, digest-checked exception.
    licensing_paths = current_licensing_paths(ROOT, package_text_files(), context)
    failures.extend(retired_licensing_failures(ROOT, licensing_paths))

    # 6. package junk. Generated caches are not junk; shipped junk is.
    junk = find_junk()
    check(not junk, f"package contains {len(junk)} junk files: {junk[:10]}")
    check(audit["packageJunkFiles"] == len(junk), f"audit packageJunkFiles={audit['packageJunkFiles']} but found {len(junk)}")

    # 6b. the shipped file list must be complete, correct and cache-free.
    check_governed_contract_copies()
    file_count = check_manifest(audit)

    # 7. no file may present this release as a pre-release. The scanner cannot be
    #    its own subject, so its own source is excluded.
    pattern = "release" + "[ -]" + "candidate"
    self_path = Path(__file__).resolve()
    for path in package_text_files():
        if path.suffix.lower() in {".zip"} or path.resolve() == self_path:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if re.search(pattern, text, re.I):
            failures.append(f"pre-release status wording in {path.relative_to(ROOT).as_posix()}")

    # ------------------------------------------------------------------
    # 8 to 13 were added in 1.1.1. Every one of them exists because a human
    # reader found the defect and no mechanical check did. The class is always
    # the same: a value that had to be copied by hand from one document into
    # another, and drifted.
    # ------------------------------------------------------------------

    # 8. every document that states the conformance numbers must state the same
    #    ones. 1.1.0 published 123, 122 and 107 across its own documents.
    # A number is only checked when the sentence is about THIS release. Lines
    # that describe an earlier release are history, not drift, so they are
    # skipped by name rather than by loosening the check.
    historical_line = re.compile(
        r"since\s+\d|before\s+\d|up to and including|Releases? up to|grew from|"
        r"historical|previously|earlier release|1\.0\.[0-4]|1\.1\.0",
        re.I,
    )
    aggregate_re = re.compile(
        r"\b(\d{2,4})\s+(?:conformance\s+)?(?:cases?|passed)\b|\b(\d{2,4})/(?:\d{2,4})\b",
        re.I,
    )
    # The foundation count is only claimed in a suite-composition context.
    foundation_re = re.compile(
        r"foundation\s*\|\s*(\d{1,4})\s*\||foundation\s+(\d{1,4})\b", re.I
    )
    for rel in (
        "README.md",
        f"OBDS-{EXPECTED_RELEASE}-CHANGELOG.md",
        f"OBDS-PUBLIC-README-{EXPECTED_RELEASE}.md",
        f"OBDS-{EXPECTED_RELEASE}-TEST-REQUIREMENTS.md",
    ):
        path = ROOT / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if "CHANGELOG" in rel:
            # A changelog is history by construction. Only the section for this
            # release makes a claim about this release.
            heading = f"\n## {EXPECTED_RELEASE}\n"
            if heading not in text:
                failures.append(f"{rel} has no section for {EXPECTED_RELEASE}")
                continue
            body = text.split(heading, 1)[1]
            text = body.split("\n## ", 1)[0]
        for line in text.splitlines():
            if historical_line.search(line):
                continue
            totals = {
                int(g) for match in aggregate_re.findall(line) for g in match
                if g and 50 <= int(g) <= 9999
            }
            wrong_total = sorted(t for t in totals if t != EXPECTED_TOTAL)
            check(
                not wrong_total,
                f"{rel} states conformance total {wrong_total} on a line about this "
                f"release, but this release is {EXPECTED_TOTAL}: {line.strip()[:70]}",
            )
            founds = {
                int(g) for match in foundation_re.findall(line) for g in match if g
            }
            wrong_found = sorted(
                f for f in founds if f != EXPECTED_SUITE_COUNTS["foundation"]
            )
            check(
                not wrong_found,
                f"{rel} states foundation count {wrong_found}, but this release is "
                f"{EXPECTED_SUITE_COUNTS['foundation']}: {line.strip()[:70]}",
            )

    # 9. no release document may name another release. A whole stale document
    #    survived into 1.1.0 because nothing checked the version in its own text.
    other_release = re.compile(r"OBDS-(\d+\.\d+\.\d+)(?:-[A-Za-z-]+)?\.(?:md|json|zip|txt)")
    historical_ok = re.compile(r"spec/\d+\.\d+\.\d+/|/spec/|CHANGELOG|MIGRATION|Previous|previous|historical")
    for rel in (
        f"OBDS-{EXPECTED_RELEASE}-TEST-REQUIREMENTS.md",
        f"OBDS-{EXPECTED_RELEASE}-IMPLEMENTER-QUICKSTART.md",
    ):
        path = ROOT / rel
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if historical_ok.search(line):
                continue
            for found in other_release.findall(line):
                check(
                    found == EXPECTED_RELEASE,
                    f"{rel} references release {found}: {line.strip()[:90]}",
                )
        first_line = path.read_text(encoding="utf-8").splitlines()[0]
        check(
            EXPECTED_RELEASE in first_line or not re.search(r"\d+\.\d+(\.\d+)?", first_line),
            f"{rel} title names another release: {first_line.strip()[:90]}",
        )

    # 10. the conformance result must not contradict itself. 1.1.0 shipped a
    #     TEST-RESULT.json whose notes described a different release, whose
    #     promotedFrom disagreed with the publication record, and whose
    #     claimScope promised an enumeration the file did not contain.
    check(
        test_result.get("release") == EXPECTED_RELEASE,
        f"TEST-RESULT release is {test_result.get('release')!r}",
    )
    check(
        test_result.get("obdsVersion") == EXPECTED_RELEASE,
        f"TEST-RESULT obdsVersion is {test_result.get('obdsVersion')!r}",
    )
    check(
        test_result.get("promotedFrom") == PRIOR_RELEASE,
        f"TEST-RESULT promotedFrom is {test_result.get('promotedFrom')!r}, "
        f"expected {PRIOR_RELEASE!r}",
    )
    notes_text = " ".join(test_result.get("notes", []))
    # Only a note that describes *this* release is checked; a note that
    # enumerates the releases a contract has been identical across is history.
    for stale in re.findall(r"OBDS (\d+\.\d+\.\d+) is\b", notes_text):
        check(
            stale == EXPECTED_RELEASE,
            f"TEST-RESULT notes describe OBDS {stale}, not {EXPECTED_RELEASE}",
        )
    for stale_total in {int(m) for m in re.findall(r"\b(\d{3})\s+cases\b", notes_text)}:
        check(
            stale_total == EXPECTED_TOTAL,
            f"TEST-RESULT notes state {stale_total} cases, not {EXPECTED_TOTAL}",
        )
    claim = test_result.get("claimScope", "")

    def _contains_key(node, key: str) -> bool:
        if isinstance(node, dict):
            return key in node or any(_contains_key(v, key) for v in node.values())
        if isinstance(node, list):
            return any(_contains_key(v, key) for v in node)
        return False

    for promised in re.findall(r"`([A-Za-z][A-Za-z0-9]*)`", claim):
        check(
            _contains_key(test_result, promised),
            f"TEST-RESULT claimScope names `{promised}`, which the file does not contain",
        )

    # 11. every contract this release serves must be indexed and mapped, and
    #     every indexed or mapped contract must be served. 1.1.0 served
    #     schemas/1.1.0/compiled-context.schema.json and listed it in neither.
    served: dict[str, Path] = {}
    for directory, url_path, _ in contract_directories():
        for path in sorted(directory.glob("*.json")):
            served[f"https://openbranddefinition.org/{url_path}/{path.name}"] = path

    indexed = {i["id"] for i in index["schemas"]} | {i["id"] for i in index["valueSchemas"]}
    indexed |= {i["id"] for i in versioned_index}
    mapped = {c["id"] for c in pubmap["contracts"]}

    for missing in sorted(set(served) - indexed):
        failures.append(f"served contract missing from the schema index: {missing}")
    for missing in sorted(set(served) - mapped):
        failures.append(f"served contract missing from the publication map: {missing}")
    for extra in sorted(indexed - set(served)):
        failures.append(f"schema index lists a contract this release does not serve: {extra}")
    for extra in sorted(mapped - set(served)):
        failures.append(f"publication map lists a contract this release does not serve: {extra}")
    check(
        pubmap.get("totalPublicContracts") == len(served),
        f"publication map totalPublicContracts={pubmap.get('totalPublicContracts')} "
        f"but this release serves {len(served)}",
    )
    for contract in pubmap["contracts"]:
        path = served.get(contract["id"])
        if path is None:
            continue
        digest = sha256_file(path)
        check(
            contract.get("sha256") == digest,
            f"publication map sha256 for {contract['id']} does not match the served bytes",
        )

    # 12. the publication record and the website must agree with what was built.
    #     Both are hand-maintained and both drifted in 1.1.0.
    record_path = ROOT / "publication-record.json"
    if record_path.is_file():
        record = load(record_path)
        check(
            record.get("currentRelease") == EXPECTED_RELEASE,
            f"publication-record currentRelease is {record.get('currentRelease')!r}",
        )
        check(
            record.get("testOutputHash") == test_result.get("testOutputHash"),
            "publication-record testOutputHash differs from the built TEST-RESULT",
        )
        check(
            record.get("conformanceTestsPassed") == EXPECTED_TOTAL,
            f"publication-record conformanceTestsPassed="
            f"{record.get('conformanceTestsPassed')}, expected {EXPECTED_TOTAL}",
        )
        release_entry = (record.get("releases") or {}).get(EXPECTED_RELEASE, {})
        check(
            release_entry.get("testOutputHash") == test_result.get("testOutputHash"),
            f"publication-record releases[{EXPECTED_RELEASE}].testOutputHash "
            "differs from the built TEST-RESULT",
        )
        zip_path = ROOT / "spec" / EXPECTED_RELEASE / f"OBDS-{EXPECTED_RELEASE}-FINAL.zip"
        if zip_path.is_file():
            zip_digest = sha256_file(zip_path)
            check(
                record.get("packageZipSha256") == zip_digest,
                "publication-record packageZipSha256 differs from the built archive",
            )
            check(
                release_entry.get("packageZipSha256") == zip_digest,
                f"publication-record releases[{EXPECTED_RELEASE}].packageZipSha256 "
                "differs from the built archive",
            )
        index_html = ROOT / "index.html"
        if index_html.is_file():
            site = index_html.read_text(encoding="utf-8")
            check(
                record.get("websiteIndexSha256") == sha256_file(index_html),
                "publication-record websiteIndexSha256 differs from index.html",
            )
            check(
                test_result.get("testOutputHash") in site,
                "the website does not carry this release's testOutputHash",
            )
            check(
                f"{EXPECTED_TOTAL} passed" in site,
                f"the website does not state {EXPECTED_TOTAL} passed",
            )
            check(
                f"OBDS / {EXPECTED_RELEASE} " in site or f">OBDS {EXPECTED_RELEASE}<" in site,
                f"the website does not present {EXPECTED_RELEASE} as the current release",
            )
            for suite_name, suite_count in EXPECTED_SUITE_COUNTS.items():
                marker = (f'<span class="state-name">{suite_name}</span></div>'
                          f'<div class="publication-value">')
                if marker in site:
                    stated = site.split(marker, 1)[1].split("<", 1)[0].strip()
                    check(
                        stated == str(suite_count),
                        f"the website states {suite_name} {stated}, expected {suite_count}",
                    )
            try:
                verify_homepage_contracts(site, len(served))
            except AssertionError as exc:
                failures.append(str(exc))

    # 13. normative and published examples must satisfy the published contracts.
    #     The 1.1.0 section 14 artefact example and the authoring page's only
    #     worked example both failed the schemas shipped beside them.
    try:
        import jsonschema as _jsonschema
    except ImportError:
        _jsonschema = None
    if _jsonschema is not None:
        spec_candidates = sorted(ROOT.glob(f"OBDS-{EXPECTED_RELEASE}.md"))
        current_context_contract = ROOT / "schemas" / "3.0.0" / "compiled-context.schema.json"
        if spec_candidates and current_context_contract.is_file():
            text = spec_candidates[0].read_text(encoding="utf-8")
            if "## 14. Compiled Brand Context" in text:
                section = text.split("## 14. Compiled Brand Context", 1)[1].split("### 14.0", 1)[0]
                block = re.search(r"```json\n(.*?)\n```", section, re.S)
                if block:
                    # Section 28.1: the normative Compiled Brand Context example
                    # is governed data, read under the governed contract.
                    example = _read_governed_text(block.group(1), is_json=True)
                    placeholder = "sha256:" + "0" * 64

                    def _fill(node):
                        if isinstance(node, dict):
                            return {k: _fill(v) for k, v in node.items()}
                        if isinstance(node, list):
                            return [_fill(v) for v in node]
                        return placeholder if node == "sha256:..." else node

                    errors = sorted(
                        _jsonschema.Draft202012Validator(
                            load(current_context_contract)
                        ).iter_errors(_fill(example)),
                        key=lambda e: list(e.path),
                    )
                    for err in errors[:5]:
                        failures.append(
                            "the section 14 normative example fails "
                            f"schemas/3.0.0/compiled-context.schema.json: "
                            f"{list(err.path)} {err.message[:110]}"
                        )
                    expected_id = f"{example['manifest']['id']}:context:{example['targetId']}"
                    check(
                        example.get("id") == expected_id,
                        "the section 14 example id does not follow "
                        "{manifest.id}:context:{targetId}",
                    )

        # Published structured examples outside the specification. The
        # authoring page's worked example is the one a curator copies first, so
        # it must satisfy the same contracts as a real manifest element.
        manifest_schema = ROOT / "schemas" / "brand-manifest.schema.json"
        if not manifest_schema.is_file():
            manifest_schema = ROOT / "schemas" / "1.0.0" / "brand-manifest.schema.json"
        colour_schema = ROOT / "value-schemas" / "colour.schema.json"
        if not colour_schema.is_file():
            colour_schema = ROOT / "value-schemas" / "1.0.0" / "colour.schema.json"

        for rel in ("authoring/index.html",):
            path = ROOT / rel
            if not path.is_file() or not manifest_schema.is_file():
                continue
            for element in published_yaml_elements(path.read_text(encoding="utf-8")):
                manifest_doc = load(manifest_schema)
                # The element subschema uses internal $refs, so it must be
                # validated with the document's own $defs as the resolution root.
                element_schema = {
                    "$ref": "#/$defs/element",
                    "$defs": manifest_doc["$defs"],
                }
                for err in sorted(
                    _jsonschema.Draft202012Validator(element_schema).iter_errors(element),
                    key=lambda e: list(e.path),
                )[:5]:
                    failures.append(
                        f"{rel}: published element example fails "
                        f"{manifest_schema.name}#/$defs/element: "
                        f"{list(err.path)} {err.message[:110]}"
                    )
                if element.get("kind") == "colour" and colour_schema.is_file():
                    for err in sorted(
                        _jsonschema.Draft202012Validator(
                            load(colour_schema)
                        ).iter_errors(element.get("value", {})),
                        key=lambda e: list(e.path),
                    )[:5]:
                        failures.append(
                            f"{rel}: published colour value fails "
                            f"{colour_schema.name}: {list(err.path)} {err.message[:110]}"
                        )

    # ------------------------------------------------------------------
    # 14 to 17 were added in 1.1.2. Each one is a regression the outreach gate
    # found in published 1.1.1 that checks 8 to 13 walked straight past.
    # ------------------------------------------------------------------

    # 14. the specification must stamp itself with this release. 1.1.1 shipped a
    #     normative document whose own Version line read 1.1.0.
    spec_path = ROOT / f"OBDS-{EXPECTED_RELEASE}.md"
    if spec_path.is_file():
        spec_head = spec_path.read_text(encoding="utf-8").split("\n---", 1)[0]
        stamped = re.search(r"^\*\*Version:\*\*\s*(\S+)", spec_head, re.M)
        check(
            stamped is not None,
            f"OBDS-{EXPECTED_RELEASE}.md carries no **Version:** line",
        )
        if stamped:
            check(
                stamped.group(1) == EXPECTED_RELEASE,
                f"OBDS-{EXPECTED_RELEASE}.md stamps itself "
                f"**Version:** {stamped.group(1)}, not {EXPECTED_RELEASE}",
            )
    public_readme = ROOT / f"OBDS-PUBLIC-README-{EXPECTED_RELEASE}.md"
    if public_readme.is_file():
        head = "\n".join(public_readme.read_text(encoding="utf-8").splitlines()[:40])
        claims = re.findall(r"\*\*OBDS (\d+\.\d+\.\d+)[\.\*]", head)
        for named in set(claims):
            check(
                named == EXPECTED_RELEASE,
                f"OBDS-PUBLIC-README-{EXPECTED_RELEASE}.md announces OBDS {named}",
            )

    # 15. NO current-release surface may announce another release. Widened in
    #     1.1.3: 1.1.2 checked index.html only, and /authoring/ shipped
    #     announcing OBDS 1.1.0 in its title, badge and subtitle for a whole
    #     release. Every HTML page, llms.txt, the README and the publication
    #     metadata are current-release surfaces. This step checks the pages and
    #     llms.txt; until 4.1.3 nothing checked the README's current release
    #     (step 8 reads it for count claims only), which is what 15a adds.
    for page in sorted(ROOT.glob("*.html")) + sorted(ROOT.glob("*/index.html")):
        if not page.is_file():
            continue
        rel_page = page.relative_to(ROOT).as_posix()
        page_text = page.read_text(encoding="utf-8")
        page_head = page_text.split("</head>", 1)[0]
        release_re = re.compile(r"\b(\d+\.\d+\.\d+)\b")
        # The title and the visible status badge are what a reader sees first.
        title = re.search(r"<title>(.*?)</title>", page_head, re.S)
        badge = re.search(r'class="status"[^>]*>([^<]*)<', page_text)
        subtitle = re.search(r"Companion to OBDS ([\d.]+)", page_text)
        for label, fragment in (("<title>", title.group(1) if title else None),
                                ("status badge", badge.group(1) if badge else None),
                                ("subtitle", subtitle.group(0) if subtitle else None)):
            if not fragment:
                continue
            for named in set(release_re.findall(fragment)):
                check(
                    named == EXPECTED_RELEASE,
                    f"{rel_page} {label} names release {named}, "
                    f"not {EXPECTED_RELEASE}",
                )

    # llms.txt announces the current release in prose, which no earlier check
    # read. 1.1.2 shipped it saying 1.1.1.
    llms = ROOT / "llms.txt"
    if llms.is_file():
        first_lines = "\n".join(llms.read_text(encoding="utf-8").splitlines()[:12])
        current = re.search(r"Current release:\s*(\S+)", first_lines)
        check(
            current is not None,
            "llms.txt carries no 'Current release:' line",
        )
        if current:
            check(
                current.group(1) == EXPECTED_RELEASE,
                f"llms.txt announces current release {current.group(1)}, "
                f"not {EXPECTED_RELEASE}",
            )

    index_html_path = ROOT / "index.html"
    if index_html_path.is_file():
        site_text = index_html_path.read_text(encoding="utf-8")
        head_text = site_text.split("</head>", 1)[0]
        version_pattern = re.compile(r"\b(\d+\.\d+\.\d+)\b")
        for label, fragment in (
            ("<title>", re.search(r"<title>(.*?)</title>", head_text, re.S)),
            ("meta description", re.search(r'name="description" content="(.*?)"', head_text, re.S)),
            ("og:description", re.search(r'property="og:description" content="(.*?)"', head_text, re.S)),
            ("obds-version meta", re.search(r'name="obds-version" content="(.*?)"', head_text, re.S)),
        ):
            if fragment is None:
                continue
            for named in set(version_pattern.findall(fragment.group(1))):
                check(
                    named == EXPECTED_RELEASE,
                    f"the website {label} names release {named}, "
                    f"not {EXPECTED_RELEASE}",
                )

    # 15a. README.md, the public README, the current release documents, the Task
    #      Facts status pages and, in the repository, the Open Graph cards. See
    #      current_surface_problems() for what step 15 had been claiming since 1.1.3.
    try:
        for problem in current_surface_problems(ROOT, context):
            check(False, problem)
    except (OSError, ValueError, KeyError) as exc:
        check(False, f"current-state surfaces could not be read: {exc}")

    # 16. a historical changelog section must keep its own numbers. Correcting
    #     the current release's count by string replacement rewrote 1.1.0's
    #     history in 1.1.1, which is worse than the defect it fixed.
    changelog = ROOT / f"OBDS-{EXPECTED_RELEASE}-CHANGELOG.md"
    if changelog.is_file():
        text = changelog.read_text(encoding="utf-8")
        sections = re.split(r"\n## (?=\d+\.\d+\.\d+\n)", text)
        for section in sections[1:]:
            name = section.split("\n", 1)[0].strip()
            if name == EXPECTED_RELEASE:
                continue
            body = section.split("\n", 1)[1] if "\n" in section else ""
            for line in body.splitlines():
                if "**Conformance.**" not in line:
                    continue
                stated = {int(m) for m in re.findall(r"\b(\d{2,4})\b", line)
                          if 50 <= int(m) <= 9999}
                check(
                    EXPECTED_TOTAL not in stated,
                    f"the changelog's historical {name} section states this "
                    f"release's count {EXPECTED_TOTAL}: {line.strip()[:80]}",
                )

    # 17. the two 1.1.2 normative fixtures must agree with the rules they pin.
    #     Both describe behaviour no governed-result vector can reach.
    escapes = ROOT / "reference" / "foundation" / "fixtures" / "obds-1.1" / "canonical-escapes.json"
    vectors_path = ROOT / "reference" / "adversarial" / "canonical-vectors.json"
    if escapes.is_file() and vectors_path.is_file():
        vector_doc = load(vectors_path)
        # 1.1.3 gave the vector file expected output, so it is an object with a
        # `vectors` array. A bare array is still accepted for older layouts.
        published = set(
            vector_doc if isinstance(vector_doc, list)
            else [case["input"] for case in vector_doc["vectors"]]
        )
        missing = []
        for case in load(escapes)["cases"]:
            for payload in (case["stringValue"], case["objectKey"]):
                raw = json.dumps(payload, ensure_ascii=False)
                if raw not in published:
                    missing.append(case["codePoint"])
        check(
            not missing,
            "canonical escape rows absent from the cross-language vectors: "
            f"{sorted(set(missing))}",
        )

    # 18. the cross-language vectors must be usable without a second
    #     implementation. Before 1.1.3 they carried inputs only, so a third party
    #     could prove their two implementations agreed and nothing more.
    if vectors_path.is_file():
        vector_doc = load(vectors_path)
        check(
            isinstance(vector_doc, dict) and "vectors" in vector_doc,
            "canonical-vectors.json carries no expected output",
        )
        if isinstance(vector_doc, dict) and "vectors" in vector_doc:
            incomplete = [
                case.get("input", "?")[:40] for case in vector_doc["vectors"]
                if not {"input", "canonical", "canonicalHex", "sha256"} <= set(case)
            ]
            check(
                not incomplete,
                f"canonical vectors without full expected output: {incomplete[:5]}",
            )
            mismatched = []
            for case in vector_doc["vectors"]:
                if not {"canonicalHex", "sha256"} <= set(case):
                    continue
                raw = bytes.fromhex(case["canonicalHex"])
                if "sha256:" + hashlib.sha256(raw).hexdigest() != case["sha256"]:
                    mismatched.append(case["input"][:40])
            check(
                not mismatched,
                f"canonical vector sha256 does not match its own bytes: {mismatched[:5]}",
            )
            ordering = [c for c in vector_doc["vectors"]
                        if c["input"].startswith('{"10"') or c["input"].startswith('{"2"')]
            check(
                ordering,
                "no integer-like key-ordering vector is published; section 14.3 "
                "step 3 names that case explicitly",
            )

    validity = ROOT / "reference" / "foundation" / "fixtures" / "obds-1.1" / "validity-window.json"
    if validity.is_file() and spec_path.is_file():
        data = load(validity)
        spec_text = spec_path.read_text(encoding="utf-8")
        section = spec_text.split("### 14.0 Artefact validity", 1)
        check(len(section) == 2, "section 14.0 is missing from the specification")
        if len(section) == 2:
            body = section[1].split("### 14.1", 1)[0]
            check(
                "every element whose scope matches the target" in body,
                "section 14.0 no longer states which element set bounds the window",
            )
            check(
                "the compiled selection remains valid" not in body,
                "section 14.0 still carries the retired 'compiled selection' wording",
            )
        boundary = data.get("runtimeBoundary", {})
        check(
            boundary.get("rejectedAt") == boundary.get("validTo"),
            "the validity fixture no longer pins the half-open boundary at validTo",
        )

    # Guard 19. The check above compares two fixture constants to each other, so
    # it is true whatever the implementation does: on 2.0.0 both boundary
    # comparisons in the compiler and both in the runtime could be inverted and
    # this guard, the test beside it and the whole suite stayed green. A guard
    # may not advertise protection it cannot give, so the claim now depends on
    # tests that call the implementation at the exact boundary instants, and the
    # gate executes them.
    boundary_tests = ROOT / "reference" / "foundation" / "tests" / "test_obds_116.py"
    check(boundary_tests.is_file(), "the executable validity boundary tests are missing")
    if boundary_tests.is_file():
        source = boundary_tests.read_text(encoding="utf-8")
        for symbol in (
            "_valid_at(element, as_of)",
            "_artifact_valid_at(artefact, runtime_at)",
            "run_with_model(",
        ):
            check(
                symbol in source,
                f"the boundary tests no longer execute {symbol}",
            )
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "tests/test_obds_116.py",
             "-k", "half_open or applies_the_half_open or window"],
            cwd=ROOT / "reference" / "foundation",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        tail = (completed.stdout or "").strip().splitlines()
        check(
            completed.returncode == 0,
            "the executable validity boundary tests do not pass: "
            + (tail[-1] if tail else "no output"),
        )
        executed = re.search(r"(\d+) passed", completed.stdout or "")
        boundary_count = int(executed.group(1)) if executed else 0
        check(
            boundary_count >= 16,
            f"only {boundary_count} executable boundary cases ran; both bounds of "
            "the compiler and of the runtime must be exercised at the instant",
        )

    if failures:
        print("RELEASE GATE: FAIL")
        for item in failures:
            print("  -", item)
        return 1

    layout = "flat" if SCHEMAS_DIR == ROOT / "schemas" else "published URL paths"
    print("RELEASE GATE: PASS")
    print(f"  release            {EXPECTED_RELEASE} {EXPECTED_STATUS}")
    print(f"  tests              {EXPECTED_TOTAL} passed / 0 failed / 0 skipped")
    print(f"  suiteCounts sum    {sum(EXPECTED_SUITE_COUNTS.values())}")
    print(f"  public schemas     {len(schemas)} + {len(value_schemas)} value schemas ({layout})")
    print(f"  schema surface     unchanged since 1.0.0 ({FROZEN_SCHEMA_SURFACE[:16]})")
    print(f"  package files      {file_count} listed, all present and hash-verified")
    print(f"  package junk files {len(junk)}")
    print(f"  contract identity  unchanged vs {PRIOR_RELEASE} (registry, schema index, publication map)")
    print(f"  licence texts      unmodified CC BY 4.0 and Apache 2.0")
    print(f"  testOutputHash     {actual}")
    print(
        f"  section 26 result  {implementation.get('name')} {implementation.get('version')}, "
        f"{len(profiles)} profiles, 0 skipped or changed"
    )
    print(f"  suiteHash          {test_result.get('suiteHash')} ({test_result.get('suiteFileCount')} files)")
    if foundation_conformance:
        print(
            f"  foundation suite   profile {foundation_conformance.get('profile')}, "
            f"{foundation_conformance.get('passedCount')} passed / "
            f"{foundation_conformance.get('failedCount')} failed, executed by this gate"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
