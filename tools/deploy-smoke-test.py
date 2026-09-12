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
MUST_BE_ABSENT = [("/release-work/", "internal candidate evidence"),
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
    ("/tools/deploy-smoke-test.py",
     "this file. `tools/` ships in the release package so the archive can verify\n     itself, but serving it publishes the inventory of private paths it exists to\n     keep private. .vercelignore excludes tools/ from the deployment only."),
    ("/md/", "withdrawn drafts"),
    ("/licensing/", "withdrawn licensing drafts"),
    ("/archive/", "local archive"),
    ("/.venv/bin/python", "local virtualenv"),
    ("/.venv-obds/bin/python", "local virtualenv, as actually named here"),
    ("/.env.local", "local deployment token"),
    ("/.vercel/project.json", "local deployment link"),
    ("/node_modules/", "local dependencies"),

    # The non-public Task Facts audit store. `reference/` is served, so nothing
    # but .vercelignore keeps these off the website, and the release archive
    # already excludes them: `public_package_member()` ships only the four
    # evaluator sources named by
    # reference/task-facts/1.0/PUBLIC-EVIDENCE-MANIFEST.json, which are asserted
    # present below. A 404 on the directory proves nothing, so every branch of
    # the store is probed by a real file, including two direct siblings of the
    # public four: those two are what proves the re-inclusion is exactly four
    # files and not their directories.
    ("/reference/task-facts/1.0/EVIDENCE-MANIFEST.json",
     "the audit-store inventory of all 485 historical records"),
    ("/reference/task-facts/1.0/HISTORICAL-AUDIT-REGISTRY.json",
     "the Historical Audit Evidence Registry"),
    ("/reference/task-facts/1.0/evidence/", "the audit store itself"),
    ("/reference/task-facts/1.0/evidence/ratification/reports/evidence-inventory.json",
     "ratification audit inventory"),
    ("/reference/task-facts/1.0/evidence/ratification/reviews/conformance-review.md",
     "ratification review record"),
    ("/reference/task-facts/1.0/evidence/interop/reports/FINAL-RESULT.md",
     "historical interoperability report"),
    ("/reference/task-facts/1.0/evidence/interop/source/task-facts-experiment-v0.2/"
     "OBDS-TASK-FACTS-EXPERIMENT-v0.2.md", "the frozen research source document"),
    ("/reference/task-facts/1.0/evidence/interop/cycles/cycle-1/orchestration-evidence.json",
     "cycle orchestration record"),
    ("/reference/task-facts/1.0/evidence/interop/cycles/cycle-1/implementer-input.zip",
     "cycle input archive"),
    ("/reference/task-facts/1.0/evidence/interop/cycles/cycle-1/implementation-node/results.json",
     "a direct sibling of a published evaluator source"),
    ("/reference/task-facts/1.0/evidence/interop/cycles/cycle-1/implementation-python/provenance.json",
     "the same on the Python side"),
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
    # The public Research Package. Published with 3.0.3; asserted here so a
    # deployment that drops it fails loudly instead of leaving outreach links dead.
    "/research/README.md",
    "/research/limits/README.md",
    "/LICENSE.md",
    "/GOVERNANCE.md",
    "/CONTRIBUTING.md",
    "/TRADEMARKS.md",
    "/schemas/1.0.0/brand-manifest.schema.json",
    "/schemas/1.1.0/compiled-context.schema.json",
    "/value-schemas/1.0.0/colour.schema.json",

    # The Task Facts public surface. The four evaluator sources are the only
    # files under evidence/ this release publishes; .vercelignore re-includes
    # exactly them out of 485. Asserted here so an over-broad exclusion fails
    # loudly instead of quietly dropping a published dependency. The schema is
    # the address the Task Facts schema index declares as its retrieval URL,
    # which reference/release-gate.py pins.
    "/reference/task-facts/1.0/PUBLIC-EVIDENCE-MANIFEST.json",
    "/reference/task-facts/1.0/schemas/task-facts.schema.json",
    "/reference/task-facts/1.0/evidence/interop/cycles/cycle-1/implementation-python/evaluate.py",
    "/reference/task-facts/1.0/evidence/interop/cycles/cycle-1/implementation-python/task-facts.schema.json",
    "/reference/task-facts/1.0/evidence/interop/cycles/cycle-1/implementation-node/evaluate.mjs",
    "/reference/task-facts/1.0/evidence/interop/cycles/cycle-1/implementation-node/schemas/task-facts.schema.json",
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


def verify_exact_publication(base, root=None, fetch=None):
    import hashlib
    import importlib.util
    import json
    import tempfile
    from pathlib import Path
    root = root or Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("release_gate_deploy", root / "reference/release-gate.py")
    gate = importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)
    # One authoritative current-release value, the gate's. 4.1.1 shipped this
    # path with 4.1.0 written into it a second time, so the smoke test compared
    # the live surface against the previous release's frozen bytes and failed on
    # a correct deployment. A version number that appears twice is a version
    # number that can disagree with itself.
    inventory = gate.load(root / f"release-work/{gate.EXPECTED_RELEASE}/RC-INVENTORY.json")
    gate.verify_publication(root, inventory)
    if fetch is None:
        def fetch(url):
            try:
                with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
                    return response.status, response.read()
            except urllib.error.HTTPError as error:
                return error.code, error.read()
    checked = []
    with tempfile.TemporaryDirectory() as d:
        copy = Path(d)
        for entry in inventory["publication"]:
            code, raw = fetch(base + entry["url"])
            assert code == entry["status"], "Unexpected status: " + entry["url"]
            assert hashlib.sha256(raw).hexdigest() == entry["sha256"], "Delivered byte drift: " + entry["url"]
            dst = copy / entry["path"]; dst.parent.mkdir(parents=True, exist_ok=True); dst.write_bytes(raw)
            checked.append(entry["url"])
        gate.verify_publication(copy)
        code, raw = fetch(base + "/__obds_release_missing__")
        assert code == 404 and raw == (root / "404.html").read_bytes(), "Missing route must return exact 404 bytes and status"
    for entry in inventory.get("publicArtifacts", []):
        code, raw = fetch(base + entry["url"])
        assert code == entry["status"] and hashlib.sha256(raw).hexdigest() == entry["sha256"], "Public artifact mismatch: " + entry["url"]
        checked.append(entry["url"])
    return checked


def verify_og_cards(base, root=None, fetch=None):
    """Every served page's Open Graph card must be stamped for the current release.

    The live site served cards printing 4.0.4 through the 4.1.2 release, because
    nothing that ran after a deployment looked at them. The page and the card are both
    read from the deployment, and the stamp is read back with the gate's reader.
    """
    import importlib.util
    from pathlib import Path
    root = root or Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("release_gate_og", root / "reference/release-gate.py")
    gate = importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)
    if fetch is None:
        def fetch(url):
            try:
                with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
                    return response.status, response.read()
            except urllib.error.HTTPError as error:
                return error.code, error.read()
    checked = []
    for page in (p for p in gate.PUBLICATION_URLS if p.endswith("index.html")):
        code, raw = fetch(base + gate.PUBLICATION_URLS[page])
        assert code == 200, "Page not served: " + page
        cards = gate.OG_IMAGE_META.findall(raw.decode("utf-8"))
        assert len(cards) == 1, "Expected one og:image on " + page
        code, image = fetch(base + "/" + cards[0])
        assert code == 200, "Open Graph card not served: " + cards[0]
        release = gate.png_text_chunks(image).get(gate.OG_STAMP_KEYWORD)
        assert release == gate.EXPECTED_RELEASE, (
            f"Open Graph card {cards[0]} is stamped {release or 'with no release'}, not {gate.EXPECTED_RELEASE}")
        checked.append("/" + cards[0])
    return checked


def main() -> int:
    base = (sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BASE).rstrip("/")
    print(f"deploy smoke test against {base}")
    print()

    failures: list[str] = []

    try:
        verify_exact_publication(base)
    except (AssertionError, OSError, ValueError, KeyError) as exc:
        failures.append(str(exc))
    try:
        cards = verify_og_cards(base)
        print(f"open graph cards\n  ok    {len(cards)} served cards stamped for the current release\n")
    except (AssertionError, OSError, ValueError, KeyError) as exc:
        failures.append(str(exc))
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
