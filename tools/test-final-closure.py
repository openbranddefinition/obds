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
        for value in ("4.1.2\n", "4.1.1\n", "4.1.3\n", "", "4.1.2 extra\n"):
            (root / "VERSION").write_text(value)
            trial("repository VERSION " + repr(value), lambda: gate.verify_repository_version(root, "repository"), value != "4.1.2\n")
        (root / "VERSION").unlink()
        trial("missing repository VERSION", lambda: gate.verify_repository_version(root, "repository"), True)
        trial("historical flat layout without VERSION", lambda: gate.verify_repository_version(root, "extracted-archive"))
        (root / "VERSION").write_text("4.1.1\n")
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
        for name in ("OBDS-4.1.2-FOUNDATION-CONFORMANCE.json", "OBDS-4.1.2-TASK-FACTS-CONFORMANCE.json"):
            (root / name).write_text(json.dumps({"syntheticProvenance": "/workspace/obds-release/reference/input.json"}))
        trial("neutral synthetic evidence provenance", lambda: gate.verify_fresh_provenance(root))
        (root / "OBDS-4.1.2-TASK-FACTS-CONFORMANCE.json").write_text(json.dumps({"syntheticProvenance": "/opt/personal-build/input.json"}))
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
        # A published release is immutable, so the working tree keeps 4.1.1's own
        # documents exactly as published. The scan follows distribution, not the
        # working tree, and the exemption is scoped by version and to root
        # documents only.
        for name in ("OBDS-4.1.1-FOUNDATION-CONFORMANCE.json", "OBDS-4.1.1-CHANGELOG.md",
                     "OBDS-4.1.1.md", "OBDS-PUBLIC-README-4.1.1.md", "OBDS-3.0.0-TEST-RESULT.json"):
            assert gate.prior_release_artifact(name), name
        for name in ("OBDS-4.1.2-TEST-RESULT.json", "OBDS-4.1.2.md", "OBDS-PUBLIC-README-4.1.2.md",
                     "PACKAGE-MANIFEST.json", "README.md", "reference/release-gate.py",
                     "spec/4.1.1/OBDS-4.1.1.md", "reference/task-facts/1.0/OBDS-4.1.1-note.md"):
            assert not gate.prior_release_artifact(name), name
        cases.append({"name": "prior-release exemption is version-scoped and root-only", "passed": True, "expectedRejection": False})

        # The rule itself is unchanged for everything this release distributes.
        trial("current-release member private path", lambda: gate.verify_public_bytes(private, "OBDS-4.1.2-TEST-RESULT.json"), True)
        historical_root = ROOT / "OBDS-4.1.1-CHANGELOG.md"
        if historical_root.is_file():
            gate.verify_public_bytes(historical_root.read_bytes(), historical_root.name)
            assert gate.prior_release_artifact(historical_root.name)
            cases.append({"name": "published 4.1.1 artefact exempt and unchanged", "passed": True, "expectedRejection": False})
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
        for synthetic in ("4.1.2", "9.9.9"):
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

    print(json.dumps({"kind": "final-closure-focused-regressions", "passed": True, "count": len(cases), "cases": cases}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
