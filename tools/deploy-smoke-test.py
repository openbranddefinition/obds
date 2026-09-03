#!/usr/bin/env python3
"""Check a deployed OBDS site for exposed local material.

Vercel does not apply .gitignore. Without a .vercelignore the CLI uploads every
path in the working directory, which is how `answers/` — internal reports and
third-party source PDFs — became publicly reachable on openbranddefinition.org.
`.vercelignore` fixes that; this script is what proves it stayed fixed.

Run it after every deployment:

    python3 tools/deploy-smoke-test.py
    python3 tools/deploy-smoke-test.py https://obds-sigma.vercel.app

`tools/` is part of the release package from 3.0.1 on, so editing this file
moves a release hash. That is the price of an archive that can verify itself:
the surface registries name the packager, and a file the suite reads has to be
in the package the suite is run against.
"""
from __future__ import annotations

import sys
import urllib.error
import urllib.request

DEFAULT_BASE = "https://openbranddefinition.org"
TIMEOUT = 25

# Must NOT be served. Each entry is a path plus why it matters.
MUST_BE_ABSENT = [
    ("/answers/", "the working-notes directory itself"),
    ("/openbranddefinition-site-0.9.5-public-draft.zip",
     "withdrawn draft site archive; the directory pattern in .vercelignore "
     "carried a trailing slash and never matched the companion zip"),
    ("/.claude/settings.local.json",
     "local Claude Code permissions, gitignored but not excluded from the upload "
     "until .vercelignore listed .claude/"),
    # Deep paths inside answers/, because Vercel serves files individually and a
    # 404 on the directory alone does not prove the files are gone. In 1.1.6
    # exactly three entries were removed, the ones that named a client's source
    # documents: this file is itself served from the deployed site, so listing
    # them published the inventory it exists to keep private. The ten that
    # remain name only internal reports and benchmarks, so deep-path coverage of
    # answers/ is unchanged apart from those three.
    ("/answers/Sprint/research/sustainability-claims/README.md", "internal benchmark"),
    ("/answers/Sprint/research/sustainability-claims/evidence-base.md", "internal benchmark evidence"),
    ("/answers/Sprint/research/sustainability-claims/raw-results.json", "internal benchmark output"),
    ("/answers/Sprint/EXECUTIVE-REPORT.md", "internal report"),
    ("/answers/1.1-outreach-rerun/EXECUTIVE-REPORT.md", "internal report"),
    ("/answers/1.1-outreach-rerun/sustainability/RESULTS.md", "internal report"),
    ("/answers/1.1-outreach-rerun/evaluator/B-due-diligence.md", "internal report"),
    ("/answers/1.1.1/OUTREACH-GATE.md", "internal gate report"),
    ("/answers/1.1.2/RC-REPORT.md", "an internal pre-publication report"),
    ("/answers/1.0.4-1.1/KNOWN-ISSUE-1.0.4-testOutputHash.md", "internal note"),
    ("/md/", "withdrawn drafts"),
    ("/licensing/", "withdrawn licensing drafts"),
    ("/archive/", "local archive"),
    ("/.venv/bin/python", "local virtualenv"),
    ("/.venv-obds/bin/python", "local virtualenv, as actually named here"),
    ("/.env.local", "local deployment token"),
    ("/.vercel/project.json", "local deployment link"),
    ("/node_modules/", "local dependencies"),
]

# Must be served. A blocklist that also breaks the site is not a fix.
MUST_BE_PRESENT = [
    "/",
    # The release download. Listed here because .vercelignore excludes root-level
    # archives: if that pattern ever stops being root-anchored, this fails loudly
    # instead of the download quietly disappearing.
    "/spec/1.1.6/OBDS-1.1.6-FINAL.zip",
    "/spec/1.1.5/OBDS-1.1.5-FINAL.zip",
    "/llms.txt",
    "/publication-record.json",
    "/sitemap.xml",
    "/robots.txt",
    "/authoring/",
    "/examples/README.md",
    "/LICENSE.md",
    "/GOVERNANCE.md",
    "/CONTRIBUTING.md",
    "/TRADEMARKS.md",
    "/schemas/1.0.0/brand-manifest.schema.json",
    "/schemas/1.1.0/compiled-context.schema.json",
    "/value-schemas/1.0.0/colour.schema.json",
]


def status(url: str) -> int:
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code
    except (urllib.error.URLError, TimeoutError) as error:
        print(f"  unreachable: {url} ({error})")
        return 0


def main() -> int:
    base = (sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BASE).rstrip("/")
    print(f"deploy smoke test against {base}")
    print()

    failures: list[str] = []

    print("must be absent")
    for path, why in MUST_BE_ABSENT:
        code = status(base + path)
        # 404 and 410 are both correct. Anything that serves is not.
        ok = code in (404, 410)
        print(f"  {'ok  ' if ok else 'FAIL'}  {code:<4} {path}")
        if not ok:
            failures.append(f"{path} is reachable ({code}): {why}")

    print()
    print("must be present")
    for path in MUST_BE_PRESENT:
        code = status(base + path)
        ok = code == 200
        print(f"  {'ok  ' if ok else 'FAIL'}  {code:<4} {path}")
        if not ok:
            failures.append(f"{path} is not served ({code})")

    print()
    if failures:
        print("DEPLOY SMOKE TEST: FAIL")
        for item in failures:
            print("  -", item)
        return 1
    print("DEPLOY SMOKE TEST: PASS")
    print(f"  {len(MUST_BE_ABSENT)} local paths absent, "
          f"{len(MUST_BE_PRESENT)} public paths served")
    return 0


if __name__ == "__main__":
    sys.exit(main())
