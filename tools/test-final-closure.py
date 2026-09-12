#!/usr/bin/env python3
"""Focused final-closure boundary regressions; synthetic fixtures are not reports."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("closure_gate", ROOT / "reference/release-gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def main():
    cases = []

    def trial(name, action, reject=False):
        try:
            action()
        except (AssertionError, OSError, ValueError):
            assert reject, name
        else:
            assert not reject, name
        cases.append({"name": name, "passed": True, "expectedRejection": reject})

    with tempfile.TemporaryDirectory(prefix="obds-final-closure-") as directory:
        root = Path(directory)
        for value in ("4.1.3\n", "4.1.2\n", "4.1.4\n", "", "4.1.3 extra\n"):
            (root / "VERSION").write_text(value)
            trial("repository VERSION " + repr(value), lambda: gate.verify_repository_version(root, "repository"), value != "4.1.3\n")
        (root / "VERSION").unlink()
        trial("missing repository VERSION", lambda: gate.verify_repository_version(root, "repository"), True)
        trial("historical flat layout without VERSION", lambda: gate.verify_repository_version(root, "extracted-archive"))
        (root / "VERSION").write_text("4.1.2\n")
        trial("historical flat layout retains old VERSION", lambda: gate.verify_repository_version(root, "extracted-archive"))
        for base in gate.NEUTRAL_WORKSPACES:
            trial("neutral workspace " + base, lambda: gate.verify_public_bytes((base + "/reference/input.json").encode(), "synthetic fixture"))
            assert gate.neutral_path(base + "/reference/input.json")
            assert gate.neutral_path(base + "-runtime/bin/python")
            assert not gate.neutral_path(base + "-personal/input.json")
        private = b"/" + b"Users/closure-test/private/input.json"
        trial("private path text", lambda: gate.verify_public_bytes(private, "synthetic text"), True)
        trial("private path binary", lambda: gate.verify_public_bytes(b"\x00" + private, "synthetic binary"), True)
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            archive.writestr("fixture.txt", private)
        trial("private path nested ZIP", lambda: gate.verify_public_bytes(stream.getvalue(), "synthetic nested ZIP"), True)
        for name in ("OBDS-4.1.3-FOUNDATION-CONFORMANCE.json", "OBDS-4.1.3-TASK-FACTS-CONFORMANCE.json"):
            (root / name).write_text(json.dumps({"syntheticProvenance": "/workspace/obds-release/reference/input.json"}))
        trial("neutral synthetic evidence provenance", lambda: gate.verify_fresh_provenance(root))
        (root / "OBDS-4.1.3-TASK-FACTS-CONFORMANCE.json").write_text(json.dumps({"syntheticProvenance": "/opt/personal-build/input.json"}))
        trial("non-neutral synthetic evidence provenance", lambda: gate.verify_fresh_provenance(root), True)
        tf = ROOT / "reference/task-facts/1.0"
        public = gate.load(tf / "PUBLIC-EVIDENCE-MANIFEST.json")
        if (tf / "EVIDENCE-MANIFEST.json").is_file():
            history = gate.load(tf / "EVIDENCE-MANIFEST.json")
            for entry in history["files"]:
                raw = (tf / entry["path"]).read_bytes()
                assert len(raw) == entry["bytes"]
                assert gate.sha256_file(tf / entry["path"]) == "sha256:" + entry["sha256"]
            cases.append({"name": "all 485 historical files remain byte-identical", "passed": True, "expectedRejection": False})
        public_root = root / "public-fixture"
        target_tf = public_root / "reference/task-facts/1.0"
        target_tf.mkdir(parents=True)
        shutil.copyfile(tf / "PUBLIC-EVIDENCE-MANIFEST.json", target_tf / "PUBLIC-EVIDENCE-MANIFEST.json")
        for entry in public["files"]:
            target = target_tf / entry["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(tf / entry["path"], target)
        for name in public["freshReports"]:
            (public_root / name).write_text(json.dumps({"syntheticProvenance": "/workspace/obds-release/reference/input.json"}))
        trial("public inventory positive control with synthetic provenance", lambda: gate.verify_public_evidence(public_root, "extracted-archive"))
        extra = target_tf / "evidence/historical-record.txt"
        extra.write_bytes(private)
        trial("public archive historical record injection", lambda: gate.verify_public_evidence(public_root, "extracted-archive"), True)
        extra.unlink()
        source = target_tf / public["files"][0]["path"]
        original = source.read_bytes()
        source.write_bytes(original + b"\n")
        trial("public evaluator byte mutation", lambda: gate.verify_public_evidence(public_root, "extracted-archive"), True)
        source.unlink()
        trial("public evaluator deletion", lambda: gate.verify_public_evidence(public_root, "extracted-archive"), True)
        source.write_bytes(original)
        (target_tf / "PUBLIC-EVIDENCE-MANIFEST.json").write_text("{}\n")
        trial("public evidence inventory mutation", lambda: gate.verify_public_evidence(public_root, "extracted-archive"), True)
        for entry in public["files"]:
            assert gate.public_package_member("reference/task-facts/1.0/" + entry["path"])
        assert not gate.public_package_member("reference/task-facts/1.0/EVIDENCE-MANIFEST.json")
        assert not gate.public_package_member("reference/task-facts/1.0/evidence/interop/reports/FINAL-RESULT.md")
        cases.append({"name": "public source allowlist excludes historical reports and inventory", "passed": True, "expectedRejection": False})

        # ---- Historical Audit Evidence Registry ------------------------------
        # Real bytes, copied so the pinned registry digest still authenticates,
        # then mutated one way at a time. The repository tree is never touched.
        prefix = "reference/task-facts/1.0/"
        audit_root = root / "audit-fixture"
        audit_tf = audit_root / prefix
        audit_tf.mkdir(parents=True)
        for name in (gate.HISTORICAL_AUDIT_REGISTRY_FILE, "EVIDENCE-MANIFEST.json"):
            shutil.copyfile(tf / name, audit_tf / name)
        shutil.copytree(tf / "evidence", audit_tf / "evidence")
        registry_path = audit_tf / gate.HISTORICAL_AUDIT_REGISTRY_FILE
        registry_bytes = registry_path.read_bytes()
        registry = gate.load(registry_path)
        assert len(registry["publicSurfaceExclusions"]) == 8
        assert len(registry["nonPublicExecutableSources"]) == 25
        assert registry["inventory"]["files"] == 485
        trial("historical audit store positive control", lambda: gate.verify_historical_audit(audit_root, "repository"))
        trial("historical audit registry present in a public archive", lambda: gate.verify_historical_audit(audit_root, "extracted-archive"), True)

        victim = audit_tf / registry["publicSurfaceExclusions"][0]["path"]
        original = victim.read_bytes()
        victim.write_bytes(original + b"\n")
        trial("historical member size and hash mismatch", lambda: gate.verify_historical_audit(audit_root, "repository"), True)
        victim.write_bytes(b"#" + original[1:])
        assert len(victim.read_bytes()) == len(original)
        trial("historical member substituted at identical size", lambda: gate.verify_historical_audit(audit_root, "repository"), True)
        victim.unlink()
        trial("historical member missing", lambda: gate.verify_historical_audit(audit_root, "repository"), True)
        victim.write_bytes(original)

        extra = audit_tf / "evidence/unexpected-record.json"
        extra.write_text("{}\n")
        trial("unexpected historical member", lambda: gate.verify_historical_audit(audit_root, "repository"), True)
        extra.unlink()

        inventory_path = audit_tf / "EVIDENCE-MANIFEST.json"
        inventory_bytes = inventory_path.read_bytes()
        inventory_path.write_bytes(inventory_bytes + b"\n")
        trial("historical audit inventory mutation", lambda: gate.verify_historical_audit(audit_root, "repository"), True)
        inventory_path.write_bytes(inventory_bytes)

        registry_path.write_bytes(registry_bytes + b"\n")
        trial("historical audit registry byte mutation", lambda: gate.verify_historical_audit(audit_root, "repository"), True)
        registry_path.write_bytes(registry_bytes)

        # The pin above fires first, so the record checks behind it are reached
        # only with the fixture's own digest. The pin is restored either way.
        pinned = gate.HISTORICAL_AUDIT_REGISTRY_SHA256
        try:
            for name, mutate in (
                ("historical registry disagreeing with its inventory",
                 lambda r: r["publicSurfaceExclusions"][0].__setitem__("sha256", "0" * 64)),
                ("historical registry claiming the public surface",
                 lambda r: r.__setitem__("publicSurface", True)),
                ("historical registry with a wrong inventory count",
                 lambda r: r["inventory"].__setitem__("files", 484)),
            ):
                record = gate.load(registry_path)
                mutate(record)
                registry_path.write_text(json.dumps(record, indent=2) + "\n")
                gate.HISTORICAL_AUDIT_REGISTRY_SHA256 = gate.sha256_file(registry_path)
                trial(name, lambda: gate.verify_historical_audit(audit_root, "repository"), True)
        finally:
            gate.HISTORICAL_AUDIT_REGISTRY_SHA256 = pinned
            registry_path.write_bytes(registry_bytes)
        trial("historical audit store restored", lambda: gate.verify_historical_audit(audit_root, "repository"))

        # ---- The two registries stay two registries --------------------------
        for entry in registry["publicSurfaceExclusions"]:
            assert not gate.public_package_member(prefix + entry["path"])
        for entry in registry["nonPublicExecutableSources"]:
            assert not gate.public_package_member(prefix + entry["path"])
        for entry in public["files"]:
            assert gate.public_package_member(prefix + entry["path"])
        assert not gate.public_package_member(prefix + gate.HISTORICAL_AUDIT_REGISTRY_FILE)
        assert not set(e["path"] for e in registry["publicSurfaceExclusions"]) & gate.PUBLIC_EVIDENCE_SOURCES
        cases.append({"name": "eight exclusions non-public, four public sources still ship", "passed": True, "expectedRejection": False})

        # Truthful history is preserved, not scrubbed: the record still carries
        # the original local path, which is exactly why it is not public.
        historical_local = "evidence/interop/cycles/cycle-1/evaluation-evidence/execution.json"
        assert (audit_tf / historical_local).read_bytes() == (tf / historical_local).read_bytes()
        trial("preserved historical record still carries its truthful local path",
              lambda: gate.verify_public_bytes((audit_tf / historical_local).read_bytes(), historical_local), True)
        assert not gate.public_package_member(prefix + historical_local)
        cases.append({"name": "historical local paths preserved and non-public", "passed": True, "expectedRejection": False})

        # ---- Prior-release artefacts ----------------------------------------
        # A published release is immutable, so the working tree keeps 4.1.2's own
        # documents exactly as published. The scan follows distribution, not the
        # working tree, and the exemption is scoped by version and to root
        # documents only.
        for name in ("OBDS-4.1.2-FOUNDATION-CONFORMANCE.json", "OBDS-4.1.2-CHANGELOG.md",
                     "OBDS-4.1.2.md", "OBDS-PUBLIC-README-4.1.2.md", "OBDS-3.0.0-TEST-RESULT.json"):
            assert gate.prior_release_artifact(name), name
        for name in ("OBDS-4.1.3-TEST-RESULT.json", "OBDS-4.1.3.md", "OBDS-PUBLIC-README-4.1.3.md",
                     "PACKAGE-MANIFEST.json", "README.md", "reference/release-gate.py",
                     "spec/4.1.2/OBDS-4.1.2.md", "reference/task-facts/1.0/OBDS-4.1.2-note.md"):
            assert not gate.prior_release_artifact(name), name
        cases.append({"name": "prior-release exemption is version-scoped and root-only", "passed": True, "expectedRejection": False})

        # The rule itself is unchanged for everything this release distributes.
        trial("current-release member private path", lambda: gate.verify_public_bytes(private, "OBDS-4.1.3-TEST-RESULT.json"), True)
        historical_root = ROOT / "OBDS-4.1.2-CHANGELOG.md"
        if historical_root.is_file():
            gate.verify_public_bytes(historical_root.read_bytes(), historical_root.name)
            assert gate.prior_release_artifact(historical_root.name)
            cases.append({"name": "published 4.1.2 artefact exempt and unchanged", "passed": True, "expectedRejection": False})
        # ---- deploy smoke RC inventory path ---------------------------------
        # 4.1.1 shipped tools/deploy-smoke-test.py with "release-work/4.1.0/"
        # written into it, so a correct 4.1.1 deployment failed its own smoke test
        # against the previous release's frozen bytes. The path now comes from the
        # gate, which owns the current release. These cases prove it stays that way.
        # The synthetic gate below states its inventory as a Python literal and
        # records the path it was asked for, so the fixture parses no document and
        # the proof is the requested path itself rather than an inference from it.
        import re as _re
        smoke_spec = importlib.util.spec_from_file_location(
            "deploy_smoke_closure", ROOT / "tools/deploy-smoke-test.py")
        smoke = importlib.util.module_from_spec(smoke_spec)
        smoke_spec.loader.exec_module(smoke)

        smoke_source = (ROOT / "tools/deploy-smoke-test.py").read_text(encoding="utf-8")
        lookup = [line for line in smoke_source.splitlines() if "RC-INVENTORY.json" in line]
        assert len(lookup) == 1, lookup
        assert "gate.EXPECTED_RELEASE" in lookup[0], lookup[0]
        assert not _re.search(r"\d+\.\d+\.\d+", lookup[0]), lookup[0]
        cases.append({"name": "deploy smoke resolves the RC inventory from the gate, with no release of its own",
                      "passed": True, "expectedRejection": False})

        assert len(smoke.MUST_BE_ABSENT) == 34, len(smoke.MUST_BE_ABSENT)
        assert len(smoke.MUST_BE_PRESENT) == 24, len(smoke.MUST_BE_PRESENT)
        assert len({path for path, _ in smoke.MUST_BE_ABSENT}) == 34
        assert len(set(smoke.MUST_BE_PRESENT)) == 24
        cases.append({"name": "deploy smoke keeps 34 absence and 24 presence assertions",
                      "passed": True, "expectedRejection": False})

        marker = b"synthetic publication surface"
        digest = hashlib.sha256(marker).hexdigest()
        for synthetic in ("4.1.3", "9.9.9"):
            fixture = root / ("smoke-" + synthetic)
            (fixture / "reference").mkdir(parents=True)
            asked = fixture / "asked-for.txt"
            url = "/marker-" + synthetic
            (fixture / "reference/release-gate.py").write_text(
                f"EXPECTED_RELEASE = {synthetic!r}\n"
                f"INVENTORY = {{'publication': [{{'path': 'marker.txt', 'url': {url!r},"
                f" 'status': 200, 'sha256': {digest!r}}}]}}\n"
                f"def load(path):\n"
                f"    open({str(asked)!r}, 'a', encoding='utf-8').write(str(path) + '\\n')\n"
                f"    return INVENTORY\n"
                f"def verify_publication(root, inventory=None):\n    return True\n",
                encoding="utf-8")
            (fixture / "404.html").write_bytes(b"synthetic 404")

            def fetch(target, _url=url):
                return (200, marker) if target.endswith(_url) else (404, b"synthetic 404")

            checked = smoke.verify_exact_publication("https://example.invalid", root=fixture, fetch=fetch)
            assert checked == [url], (synthetic, checked)
            requested = asked.read_text(encoding="utf-8").split()
            expected_path = str(fixture / ("release-work/" + synthetic) / "RC-INVENTORY.json")
            assert requested == [expected_path], (synthetic, requested)
            cases.append({"name": "deploy smoke asks for release-work/" + synthetic + "/RC-INVENTORY.json",
                          "passed": True, "expectedRejection": False})

        # the current release must actually be the one the gate declares
        assert gate.EXPECTED_RELEASE == (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        real = [line for line in
                (ROOT / f"release-work/{gate.EXPECTED_RELEASE}/RC-INVENTORY.json").read_text(encoding="utf-8").splitlines()
                if '"url"' in line]
        assert real, "current-release RC inventory is empty"
        cases.append({"name": "current-release RC inventory exists at the derived path",
                      "passed": True, "expectedRejection": False})

        # ---- current-state surfaces (4.1.3) -----------------------------------
        # 4.1.1 and 4.1.2 shipped a README that named 4.1.0 as current and linked
        # 4.1.0 root documents that had left the root, a public README that
        # credited 4.0.0's closures to 4.1.0, Task Facts pages that still called
        # a published capability prospective, and Open Graph cards that printed
        # 4.0.4. Step 15 of the gate claimed to check the README and never did.
        # Each case below feeds the gate the exact defect, or the shipped bytes.
        release = gate.EXPECTED_RELEASE
        release_date = gate.current_release_date(ROOT, release)

        def expect(name, problems, reject, needle=None):
            assert bool(problems) == reject, (name, problems)
            if needle is not None:
                assert any(needle in problem for problem in problems), (name, needle, problems)
            cases.append({"name": name, "passed": True, "expectedRejection": reject})

        def exists(rel):
            return gate.package_path_exists(ROOT, rel)

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        current_line = f"OBDS {release}, stable, {gate.long_date(release_date)}. Published at"
        assert readme.count(current_line) == 1
        expect("README current state", gate.readme_problems(readme, release, release_date, exists), False)
        expect("README announcing the previous release",
               gate.readme_problems(readme.replace(current_line, current_line.replace(release, gate.PRIOR_RELEASE, 1)),
                                    release, release_date, exists), True, "as the current release")
        expect("README with a stale release date",
               gate.readme_problems(readme.replace(current_line, current_line.replace(gate.long_date(release_date), "9 September 2026")),
                                    release, release_date, exists), True, "dates the current release")
        expect("README with two current release lines",
               gate.readme_problems(readme + "\n" + current_line + " somewhere.\n", release, release_date, exists), True,
               "current release lines")
        migration = f"(OBDS-{release}-MIGRATION.md)"
        expect("README missing a critical link",
               gate.readme_problems(readme.replace(migration, "(CONTRIBUTING.md)"), release, release_date, exists), True,
               f"does not link OBDS-{release}-MIGRATION.md")
        expect("README linking a missing file",
               gate.readme_problems(readme + "\nSee [the notes](NOTES-THAT-DO-NOT-EXIST.md).\n", release, release_date, exists),
               True, "does not exist: NOTES-THAT-DO-NOT-EXIST.md")
        expect("README linking a snapshot of an earlier release under spec/",
               gate.readme_problems(readme + "\nHistory: [4.1.2](spec/4.1.2/OBDS-4.1.2.md).\n", release, release_date, exists), False)
        expect("README linking outside the repository",
               gate.readme_problems(readme + "\nSee [sibling](../obds/README.md).\n", release, release_date, exists), True,
               "does not exist: ../obds/README.md")
        expect("README link with a title is still resolved",
               gate.readme_problems(readme + '\nSee [notes](NOTES-THAT-DO-NOT-EXIST.md "title").\n', release, release_date, exists), True,
               "does not exist: NOTES-THAT-DO-NOT-EXIST.md")
        expect("README calling another release current in prose",
               gate.readme_problems(readme + "\nThe current release is 4.1.2.\n", release, release_date, exists), True,
               "OBDS 4.1.2 in the present tense")
        assert gate.package_path_exists(ROOT, "schemas/1.0.0/", "repository")
        assert not gate.package_path_exists(ROOT, "schemas/9.9.9/", "repository")
        assert gate.package_path_exists(ROOT, "schemas/9.9.9/", "extracted-archive")
        assert not gate.package_path_exists(ROOT, "NOTES-THAT-DO-NOT-EXIST.md", "extracted-archive")
        assert not gate.package_path_exists(ROOT, "../obds/README.md", "repository")
        cases.append({"name": "link resolution: flattened contract paths only in an archive, never outside the package",
                      "passed": True, "expectedRejection": False})
        expect("README naming a root document of another release",
               gate.readme_problems(readme + "\nAlso `OBDS-4.1.0-CHANGELOG.md`.\n", release, release_date, exists), True,
               "root release document of OBDS 4.1.0")
        shipped_readme = ROOT / "spec/4.1.2/README.md"
        if shipped_readme.is_file():
            problems = gate.readme_problems(shipped_readme.read_text(encoding="utf-8"), release, release_date, exists)
            for needle in ("announces OBDS 4.1.0 as the current release", "root release document of OBDS 4.1.0",
                           f"does not link OBDS-{release}.md", "does not exist: OBDS-4.1.0.md", "as prospective"):
                assert any(needle in problem for problem in problems), (needle, problems)
            cases.append({"name": "the README shipped in 4.1.2 is refused for every defect it carried",
                          "passed": True, "expectedRejection": True})

        expect("current surfaces of this repository", gate.current_surface_problems(ROOT, "repository", release), False)
        spec_text = (ROOT / f"OBDS-{release}.md").read_text(encoding="utf-8")
        dated = f"**Date:** {release_date}  "
        assert spec_text.count(dated) == 1
        expect("specification dated with this release", gate.spec_date_problems(spec_text, release, release_date), False)
        expect("specification still dated with the previous release",
               gate.spec_date_problems(spec_text.replace(dated, "**Date:** 2026-09-10  ", 1), release, release_date),
               True, f"OBDS-{release}.md is dated")

        public = (ROOT / f"OBDS-PUBLIC-README-{release}.md").read_text(encoding="utf-8")
        expect("public README current state", gate.current_claim_problems("public README", public, release), False)
        expect("public README crediting 4.0.0's closures to a later release",
               gate.current_claim_problems("public README", public + "\nOBDS 4.1.0 closes five production boundaries.\n", release),
               True, "OBDS 4.1.0 in the present tense")
        shipped_public = ROOT / "spec/4.1.2/OBDS-PUBLIC-README-4.1.2.md"
        if shipped_public.is_file():
            expect("the public README shipped in 4.1.2 is refused",
                   gate.current_claim_problems("public README", shipped_public.read_text(encoding="utf-8"), release),
                   True, "OBDS 4.1.0 in the present tense")

        tf = ROOT / "reference/task-facts/1.0"
        suite_readme = (tf / "README.md").read_text(encoding="utf-8")
        adoption = (tf / "ADOPTION.md").read_text(encoding="utf-8")

        def tf_exists(rel):
            return gate.package_relative_exists(ROOT, "reference/task-facts/1.0", rel)

        expect("Task Facts status current", gate.task_facts_status_problems(suite_readme, adoption, release, tf_exists), False)
        first = suite_readme.split("\n\n")[1]
        stale = ("Prospective OBDS 4.1.0 internal candidate; see [ADOPTION.md](ADOPTION.md) for exact authority, identities "
                 "and limitations. Existing OBDS consumers require no adoption or migration. This suite does not add "
                 "production integration to the reference compiler.")
        expect("Task Facts suite README shipped in 4.1.2 status line",
               gate.task_facts_status_problems(suite_readme.replace(first, stale, 1), adoption, release, tf_exists),
               True, "as prospective")
        expect("Task Facts suite README without the productionIntegration limitation",
               gate.task_facts_status_problems(suite_readme.replace("`productionIntegration: false`", "no integration"),
                                               adoption, release, tf_exists), True, "productionIntegration")
        expect("Task Facts suite README linking the previous specification",
               gate.task_facts_status_problems(suite_readme.replace(f"OBDS-{release}.md", "OBDS-4.1.2.md"),
                                               adoption, release, tf_exists), True, "root release document of OBDS 4.1.2")
        record = adoption.split("\n\n", 1)[1]
        assert record.startswith("# Prospective OBDS 4.1.0 adoption of optional Task Facts 1.0\n")
        expect("ADOPTION.md without its status block",
               gate.task_facts_status_problems(suite_readme, record, release, tf_exists), True, "published status block")
        expect("ADOPTION.md status block without the productionIntegration limitation",
               gate.task_facts_status_problems(suite_readme, adoption.replace("`productionIntegration: false`", "no integration", 1),
                                               release, tf_exists), True, "productionIntegration")

        # ---- Open Graph card stamps ------------------------------------------
        if (ROOT / "og").is_dir():
            expect("Open Graph cards stamped for this release", gate.og_card_problems(ROOT, release), False)
            og_spec = importlib.util.spec_from_file_location("og_closure", ROOT / "tools/build-og-images.py")
            og = importlib.util.module_from_spec(og_spec)
            og_spec.loader.exec_module(og)
            site = root / "og-site"
            pages = [p for p in gate.PUBLICATION_EXPECTATIONS if p.endswith("index.html")]
            assert len(pages) == 9, pages
            for page in pages:
                (site / page).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / page, site / page)
            shutil.copytree(ROOT / "og", site / "og")
            expect("synthetic site with current cards", gate.og_card_problems(site, release), False)
            card = site / "og/home.png"
            current = card.read_bytes()

            def unstamped(raw):
                import struct as _struct
                start = len(gate.PNG_SIGNATURE) + 12 + _struct.unpack(">I", raw[8:12])[0]
                length = _struct.unpack(">I", raw[start:start + 4])[0]
                assert raw[start + 4:start + 8] == b"tEXt"
                return raw[:start] + raw[start + 12 + length:]

            bare = unstamped(current)
            assert gate.png_text_chunks(bare).get(gate.OG_STAMP_KEYWORD) is None
            for name, raw, needle in (
                    ("card with no release stamp, as rendered before 4.1.3", bare, "no recorded release"),
                    ("card stamped for the previous release", og.stamp(bare, gate.PRIOR_RELEASE), f"rendered for {gate.PRIOR_RELEASE}"),
                    ("card that is not a PNG", b"<svg/>", "not a readable PNG"),
                    ("card with a corrupt chunk", current[:40] + bytes([current[40] ^ 1]) + current[41:], "not a readable PNG"),
                    ("card truncated after its stamp", og.stamp(bare, release)[:80], "not a readable PNG")):
                card.write_bytes(raw)
                expect(name, gate.og_card_problems(site, release), True, needle)
            card.unlink()
            expect("missing card", gate.og_card_problems(site, release), True, "is missing")
            card.write_bytes(og.stamp(bare, release))
            expect("restamped card", gate.og_card_problems(site, release), False)

            # tools/build-release.py refuses to build while a card is stale.
            build_spec = importlib.util.spec_from_file_location("build_closure", ROOT / "tools/build-release.py")
            build = importlib.util.module_from_spec(build_spec)
            build_spec.loader.exec_module(build)
            build.require_current_og_cards(site, release)
            cases.append({"name": "release build accepts current cards", "passed": True, "expectedRejection": False})
            card.write_bytes(og.stamp(bare, gate.PRIOR_RELEASE))
            try:
                build.require_current_og_cards(site, release)
            except SystemExit as exc:
                assert "og/home.png" in str(exc), exc
            else:
                raise AssertionError("release build accepted a stale Open Graph card")
            cases.append({"name": "release build refuses a stale card", "passed": True, "expectedRejection": True})
            card.write_bytes(og.stamp(bare, release))

            # tools/deploy-smoke-test.py reads the cards a deployment serves.
            def served(target):
                path = target[len("https://candidate.invalid"):]
                page = next((p for p, url in gate.PUBLICATION_URLS.items() if url == path and p.endswith("index.html")), None)
                if page is not None:
                    return 200, (site / page).read_bytes()
                if path.startswith("/og/") and (site / path.lstrip("/")).is_file():
                    return 200, (site / path.lstrip("/")).read_bytes()
                return 404, b"synthetic 404"

            checked = smoke.verify_og_cards("https://candidate.invalid", root=ROOT, fetch=served)
            assert len(checked) == 9, checked
            cases.append({"name": "deploy smoke accepts eight served current cards", "passed": True, "expectedRejection": False})
            for name, mutate in (("deploy smoke refuses a served stale card", lambda: card.write_bytes(og.stamp(bare, gate.PRIOR_RELEASE))),
                                 ("deploy smoke refuses a card the deployment does not serve", lambda: card.unlink())):
                mutate()
                trial(name, lambda: smoke.verify_og_cards("https://candidate.invalid", root=ROOT, fetch=served), True)
            card.write_bytes(og.stamp(bare, release))

    print(json.dumps({"kind": "final-closure-focused-regressions", "passed": True, "count": len(cases), "cases": cases}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
