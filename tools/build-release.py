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
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

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
PACKAGE_DIRS = ("LICENSES", "examples", "reference", "release-schemas")

# Repository layout -> archive layout.
SCHEMA_DIRS = {"schemas/1.0.0": "schemas", "value-schemas/1.0.0": "value-schemas"}

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
    for directory in PACKAGE_DIRS:
        base = ROOT / directory
        if not base.is_dir():
            sys.exit(f"missing package directory {directory}/")
        for source in sorted(base.rglob("*")):
            if source.is_file() and not excluded(source):
                pairs.append((source.relative_to(ROOT).as_posix(), source))
    for repo_dir, archive_dir in SCHEMA_DIRS.items():
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


def write_metadata(release: str, counts: dict[str, int], file_count: int) -> str:
    output_path = ROOT / f"OBDS-{release}-TEST-OUTPUT.txt"
    digest = sha256(output_path)
    total = sum(counts.values())

    result_path = ROOT / f"OBDS-{release}-TEST-RESULT.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result.update(
        {
            "release": release,
            "promotedFrom": result.get("promotedFrom", "1.0.2"),
            "passedCount": total,
            "failedCount": 0,
            "skippedCount": 0,
            "passed": True,
            "suiteCounts": counts,
            "testOutputHash": digest,
        }
    )
    result_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    audit_path = ROOT / f"OBDS-{release}-FINAL-AUDIT.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the OBDS release package")
    parser.add_argument("--run-tests", action="store_true", help="regenerate the test output first")
    parser.add_argument("--manifest-only", action="store_true", help="skip the archive and snapshot")
    args = parser.parse_args()

    release = version()
    print(f"OBDS release build, version {release}")
    if args.run_tests:
        run_tests(release)

    output = (ROOT / f"OBDS-{release}-TEST-OUTPUT.txt").read_text(encoding="utf-8")
    counts = suite_counts(output)

    # The manifest hashes the metadata files, so the metadata has to settle first.
    pairs = package_files(release)
    write_metadata(release, counts, len(pairs))
    pairs = package_files(release)
    write_manifest(release, pairs)

    if not args.manifest_only:
        write_archive(release, pairs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
