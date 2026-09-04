#!/usr/bin/env python3
"""
Governed result reproducibility — one command, three checks.

1. Cross-implementation canonicalisation.
   The published cross-language vectors carry their own expected output, so
   they are an oracle rather than a second opinion. This runs the Node
   implementation in `reference/adversarial/canonical_js.mjs` and compares its
   bytes against `canonicalHex` in the vector document, then re-derives the
   published sha256 from those bytes.

2. Governed result hash stability.
   The same manifest and the same Build Plan are compiled twice into two
   different output directories. The `artifactHash` in the build report must
   be identical.

3. Governed refusal stability.
   A case that must fail closed is compiled twice. It must fail both times,
   with the same error code, and produce no context artefact either time.

Run from the repository root:

    PYTHONPATH=reference/foundation/src python research/governed-result-hash/verify.py

Exit code 0 means every check passed.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VECTORS = REPO / "reference" / "adversarial" / "canonical-vectors.json"
NODE_IMPL = REPO / "reference" / "adversarial" / "canonical_js.mjs"
BENCH = REPO / "research" / "governed-communications-benchmark" / "cases"
ALLOW_CASE = BENCH / "12-allow-faithful-taxonomy-claim"
BLOCK_CASE = BENCH / "06-validity-period-asof-mismatch"

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(label)


def cross_language() -> None:
    doc = json.loads(VECTORS.read_text())
    vectors = doc["vectors"]
    if shutil.which("node") is None:
        print("[SKIP] cross-language canonicalisation — Node.js not installed. "
              "This is a skip, not a pass.")
        failures.append("cross-language canonicalisation (Node.js missing)")
        return
    proc = subprocess.run(["node", str(NODE_IMPL), str(VECTORS)],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        check("cross-language canonicalisation", False, proc.stderr.strip()[:300])
        return
    produced = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    expected = [v["canonicalHex"] for v in vectors]
    check(f"cross-language canonicalisation, {len(expected)} vectors",
          produced == expected,
          f"{len(produced)} of {len(expected)} byte-identical")
    digests = ["sha256:" + hashlib.sha256(bytes.fromhex(h)).hexdigest()
               for h in produced]
    check(f"published sha256 re-derived from those bytes, {len(vectors)} vectors",
          digests == [v["sha256"] for v in vectors])


def build(case_dir: Path, out_dir: Path):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO / "reference" / "foundation" / "src")
    proc = subprocess.run(
        [sys.executable, "-m", "obds_ref.cli", "build",
         str(case_dir / "manifest.json"), str(case_dir / "build-plan.json"),
         "--out", str(out_dir)],
        capture_output=True, text=True, env=env, cwd=str(REPO))
    report = out_dir / "build-report.yaml"
    text = report.read_text() if report.exists() else ""
    contexts = sorted(p.name for p in out_dir.glob("*.context.json")) if out_dir.exists() else []
    return proc, text, contexts


def field(report_text: str, key: str) -> str | None:
    for line in report_text.splitlines():
        stripped = line.strip().lstrip("- ")
        if stripped.startswith(key + ":"):
            return stripped.split(":", 1)[1].strip()
    return None


def error_codes(report_text: str) -> list[str]:
    codes = []
    for line in report_text.splitlines():
        stripped = line.strip().lstrip("- ")
        if stripped.startswith("code:"):
            codes.append(stripped.split(":", 1)[1].strip())
    return codes


def determinism() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        runs = []
        for i in (1, 2):
            _, text, contexts = build(ALLOW_CASE, Path(tmp) / f"allow{i}")
            runs.append((field(text, "artifactHash"), contexts))
        (h1, c1), (h2, c2) = runs
        check("governed result hash is stable across two independent builds",
              h1 is not None and h1 == h2 and c1 == c2 and len(c1) == 1,
              f"{h1}")

        codes = []
        for i in (1, 2):
            _, text, contexts = build(BLOCK_CASE, Path(tmp) / f"block{i}")
            codes.append((error_codes(text), contexts))
        (e1, b1), (e2, b2) = codes
        check("governed refusal is stable across two independent builds",
              bool(e1) and e1 == e2 and b1 == b2 == [],
              f"{', '.join(e1)}; no context artefact produced")


if __name__ == "__main__":
    print("OBDS governed result reproducibility\n")
    cross_language()
    determinism()
    print()
    if failures:
        print(f"{len(failures)} check(s) failed: " + "; ".join(failures))
        sys.exit(1)
    print("All checks passed.")
