#!/usr/bin/env python3
"""OBDS documentation smoke test.

Proves that every command a first-time implementer copies out of this repository
still works, in both supported layouts.

For each documented command it does two things:

1. asserts the exact command line still appears in the documentation file it is
   supposed to appear in, so an edit to the docs cannot silently leave this test
   asserting a command nobody ships any more; and
2. executes it and checks the exit code and the headline result.

It runs the commands twice: once against the repository, where the public
schemas sit at their published URL paths under `schemas/1.0.0/`, and once
against a fresh unpack of `spec/<version>/OBDS-<version>-FINAL.zip`, where they
are flat. Both must produce the same result.

It also checks that no document claims a pass count other than `passedCount` in
`OBDS-<version>-TEST-RESULT.json`.

Run from the repository root:

    python3 tools/docs-smoke-test.py
    python3 tools/docs-smoke-test.py --python /path/to/venv/bin/python

Requires Python 3.13+, Node.js 21+ on PATH and the release's Python
dependencies. Without `--python` it builds a temporary virtualenv, which needs
network access.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import venv
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DOC_README = "README.md"
DOC_CONTRIBUTING = "CONTRIBUTING.md"
DOC_EXAMPLES = "examples/README.md"

# Documents that must never claim a pass count other than the released one.
COUNT_DOCS = (
    DOC_README,
    DOC_CONTRIBUTING,
    DOC_EXAMPLES,
    "reference/README.md",
    "publication-record.json",
    "index.html",
)

# How the interpreter is spelled in the documentation.
DOC_PYTHON = ".venv/bin/python"

# (doc file, command with {py}, expected exit code, substring expected on stdout)
CASES = [
    (DOC_README, "{py} reference/run_all.py", 0, "TOTAL: {total} passed"),
    (DOC_README, "{py} reference/release-gate.py", 0, "RELEASE GATE: PASS"),
    (
        DOC_README,
        "{py} -m obds_ref.cli validate examples/foundation-minimal/manifest.yaml",
        0,
        '"valid": true',
    ),
    (
        DOC_README,
        "{py} -m obds_ref.cli build examples/foundation-minimal/manifest.yaml"
        " examples/foundation-minimal/build-plan.yaml --out /tmp/obds-out",
        0,
        '"status": "ready"',
    ),
    (
        DOC_README,
        "{py} -m obds_ref.cli build examples/fail-closed/manifest.yaml"
        " examples/fail-closed/build-plan.yaml --out /tmp/obds-fail",
        2,
        "OBDS-BUILD-REQUIRED-NOT-DEFINED",
    ),
    (DOC_CONTRIBUTING, "{py} reference/run_all.py", 0, "TOTAL: {total} passed"),
    (DOC_CONTRIBUTING, "{py} reference/release-gate.py", 0, "RELEASE GATE: PASS"),
    (
        DOC_EXAMPLES,
        "{py} -m obds_ref.cli validate examples/foundation-minimal/manifest.yaml",
        0,
        '"valid": true',
    ),
    (
        DOC_EXAMPLES,
        "{py} -m obds_ref.cli build examples/foundation-minimal/manifest.yaml"
        " examples/foundation-minimal/build-plan.yaml --out /tmp/obds-out",
        0,
        '"status": "ready"',
    ),
    (
        DOC_EXAMPLES,
        "{py} -m obds_ref.cli build examples/fail-closed/manifest.yaml"
        " examples/fail-closed/build-plan.yaml --out /tmp/obds-fail",
        2,
        "OBDS-BUILD-REQUIRED-NOT-DEFINED",
    ),
]

# Since 1.0.3 the gate tolerates the caches the suite writes, so the documented
# order is suite first, gate second. Running it in that order here is the check
# that it stays true.
EXECUTION_ORDER = ("reference/run_all.py", "reference/release-gate.py")

failures: list[str] = []


def fail(message: str) -> None:
    failures.append(message)
    print(f"  FAIL  {message}")


def ok(message: str) -> None:
    print(f"  ok    {message}")


_GOVERNED_READER = None


def load(path: Path):
    """Section 28.1: release evidence is governed data, so it is read as such.

    The release gate reads these same files under the governed contract. This
    script read them with a raw parser, which accepts documents the contract
    refuses — a smoke test that is more permissive than the gate reports green on
    input the release would reject.
    """
    global _GOVERNED_READER
    if _GOVERNED_READER is None:
        source = ROOT / "reference" / "foundation" / "src"
        if str(source) not in sys.path:
            sys.path.insert(0, str(source))
        from obds_ref.governed_io import load_data

        _GOVERNED_READER = load_data
    return _GOVERNED_READER(path)


def release_version() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def check_counts(version: str) -> None:
    print("\n[1/4] declared pass counts")
    result = load(ROOT / f"OBDS-{version}-TEST-RESULT.json")
    expected = result["passedCount"]
    counts = result["suiteCounts"]
    if sum(counts.values()) != expected:
        fail(f"release metadata is inconsistent: sum(suiteCounts) != passedCount ({expected})")

    # Since 1.0.4 there are two published conformance numbers: the aggregate
    # pytest run and the official declared Foundation conformance suite, which
    # is deliberately not aggregated into it. Both are allowed in prose, and both
    # are pinned to the published results, so neither can drift silently.
    foundation_path = ROOT / f"OBDS-{version}-FOUNDATION-CONFORMANCE.json"
    if not foundation_path.is_file():
        fail(f"OBDS-{version}-FOUNDATION-CONFORMANCE.json is missing; the official "
             "Foundation conformance run was not published with this release")
        foundation_expected = None
    else:
        foundation = load(foundation_path)
        if foundation.get("failedCount") or not foundation.get("passed"):
            fail("official Foundation conformance is not green in the published result")
        foundation_expected = str(foundation["passedCount"])
        ok(f"official Foundation conformance published: profile "
           f"{foundation.get('profile')}, {foundation_expected} passed / "
           f"{foundation.get('failedCount')} failed")

    allowed = {str(expected)} | ({foundation_expected} if foundation_expected else set())
    pattern = re.compile(r"(\d{1,4})\s*(?:passed|bestanden|tests passed|of\s+\d{2,4})")
    for name in COUNT_DOCS:
        path = ROOT / name
        if not path.is_file():
            fail(f"{name} is missing")
            continue
        text = path.read_text(encoding="utf-8")
        bad = sorted({m for m in pattern.findall(text) if m not in allowed})
        if bad:
            fail(f"{name} claims pass count(s) {bad}, released result is {expected}")
        else:
            ok(f"{name} agrees with the published counts {sorted(allowed)}")

    output = (ROOT / f"OBDS-{version}-TEST-OUTPUT.txt").read_text(encoding="utf-8")
    for suite, count in sorted(counts.items()):
        if f"## {suite}\n" not in output:
            fail(f"test output has no section for suite {suite}")
        elif f"{count} passed in " not in output:
            fail(f"test output does not report {count} passed for {suite}")
    ok("suite composition: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))


def check_documented() -> None:
    print("\n[2/4] documented command lines still present")
    for doc in sorted({case[0] for case in CASES}):
        if "pip install -r requirements.txt" not in (ROOT / doc).read_text(encoding="utf-8"):
            fail(f"{doc} does not tell the reader how to install the dependencies")
        else:
            ok(f"{doc} documents the dependency install")

    seen: set[tuple[str, str]] = set()
    for doc, command, _code, _needle in CASES:
        literal = " ".join(command.format(py=DOC_PYTHON).split())
        if (doc, literal) in seen:
            continue
        seen.add((doc, literal))
        text = " ".join((ROOT / doc).read_text(encoding="utf-8").split())
        if literal in text:
            ok(f"{doc}: {literal}")
        else:
            fail(f"{doc} no longer contains: {literal}")


def rank(case: tuple) -> int:
    script = case[1].format(py="").split()[0]
    return EXECUTION_ORDER.index(script) if script in EXECUTION_ORDER else len(EXECUTION_ORDER)


def run_cases(package: Path, python: str, label: str, step: str, version: str) -> None:
    print(f"\n{step} documented commands execute: {label}")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(package / "reference" / "foundation" / "src")

    # The declared total lives in the release metadata, not in this script, so a
    # suite that grows does not need this file edited.
    total = load(package / f"OBDS-{version}-TEST-RESULT.json")["passedCount"]

    already_run: set[str] = set()
    for _doc, command, code, needle in sorted(CASES, key=rank):
        needle = needle.format(total=total)
        argv = command.format(py="").split()
        key = " ".join(argv)
        if key in already_run:
            continue
        already_run.add(key)
        proc = subprocess.run(
            [python, *argv], cwd=package, env=env, capture_output=True, text=True, timeout=900
        )
        pretty = " ".join(command.format(py="python").split())
        if proc.returncode != code:
            tail = (proc.stdout + proc.stderr)[-800:]
            fail(f"{pretty} exited {proc.returncode}, expected {code}\n{tail}")
        elif needle not in proc.stdout:
            fail(f"{pretty} did not print {needle!r}\n{proc.stdout[-800:]}")
        else:
            ok(f"{pretty} -> exit {code}, {needle!r}")


def build_python(workdir: Path, given: str | None) -> str:
    if given:
        return given
    env_dir = workdir / "venv"
    venv.EnvBuilder(with_pip=True).create(env_dir)
    python = str(env_dir / "bin" / "python")
    subprocess.run(
        [python, "-m", "pip", "install", "-q", "-r", str(ROOT / "requirements.txt")], check=True
    )
    return python


def main() -> int:
    parser = argparse.ArgumentParser(description="OBDS documentation smoke test")
    parser.add_argument(
        "--python",
        help="interpreter that already carries the release dependencies; "
        "by default a temporary virtualenv is built",
    )
    args = parser.parse_args()

    version = release_version()
    zip_path = ROOT / "spec" / version / f"OBDS-{version}-FINAL.zip"
    if not zip_path.is_file():
        print(f"missing release archive {zip_path.relative_to(ROOT)}; run tools/build-release.py")
        return 1
    if shutil.which("node") is None:
        print("node is not on PATH; three adversarial tests need it and are never skipped")
        return 1

    print(f"OBDS documentation smoke test, release {version}")
    check_counts(version)
    check_documented()

    with tempfile.TemporaryDirectory(prefix="obds-smoke-") as tmp:
        workdir = Path(tmp)
        python = build_python(workdir, args.python)

        run_cases(ROOT, python, "repository layout (schemas/1.0.0/)", "[3/4]", version)

        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(workdir / "unpacked")
        package = workdir / "unpacked" / f"OBDS-{version}-FINAL"
        if not package.is_dir():
            fail(f"unexpected archive layout in {zip_path.name}")
        else:
            run_cases(package, python, "release archive layout (schemas/)", "[4/4]", version)

    print()
    if failures:
        print(f"DOCS SMOKE TEST: FAIL ({len(failures)} problems)")
        return 1
    print("DOCS SMOKE TEST: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
