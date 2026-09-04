"""The published examples must behave exactly as examples/README.md documents.

These cases keep examples/ load-bearing. An example that drifts from the
reference implementation is worse than no example at all.

The quickstart case at the bottom extends that to the package README itself.
It exists because the README published an `artifactHash` that stopped
reproducing at 3.0.0 and shipped wrong in two releases: the only assertion on
that value was that the artefact agreed with itself, which is true of every
artefact and therefore proves nothing about the number a reader compares.
"""

from __future__ import annotations

import re
from pathlib import Path

from obds_ref.canonical import artefact_hash
from obds_ref.compiler import build_all, load_data, validate_manifest, validate_plan
from obds_ref.runtime import run_with_model

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
EXAMPLES = PACKAGE_ROOT / "examples"
README = PACKAGE_ROOT / "README.md"


def _load(name: str):
    return (
        load_data(EXAMPLES / name / "manifest.yaml"),
        load_data(EXAMPLES / name / "build-plan.yaml"),
    )


def test_foundation_minimal_example_is_the_smallest_thing_that_compiles(tmp_path):
    manifest, plan = _load("foundation-minimal")

    assert validate_manifest(manifest) == []
    assert validate_plan(plan) == []
    assert manifest["profiles"] == ["obds-foundation"]
    assert len(manifest["elements"]) == 1

    report = build_all(manifest, plan, output_dir=tmp_path)
    target = report["targets"][0]

    assert target["status"] == "ready"
    assert target["artifactRef"] == "brand-query-global-en.context.json"
    assert [(r["elementId"], r["actualState"], r["result"]) for r in target["requirements"]] == [
        ("structure.brand", "defined", "pass")
    ]

    artefact = load_data(tmp_path / target["artifactRef"])
    assert artefact["artifactHash"] == artefact_hash(artefact)


def test_fail_closed_example_emits_no_context_and_calls_no_model(tmp_path):
    manifest, plan = _load("fail-closed")

    assert validate_manifest(manifest) == []
    assert validate_plan(plan) == []

    unknown = next(e for e in manifest["elements"] if e["id"] == "context.efficacy-claim")
    assert unknown["state"] == "unknown"
    assert "value" not in unknown, "a non-defined state must not carry a value"

    report = build_all(manifest, plan, output_dir=tmp_path)
    target = report["targets"][0]

    assert target["status"] == "failed"
    assert target["artifactRef"] is None
    assert list(tmp_path.glob("*.context.json")) == []

    failed = {r["elementId"]: r for r in target["requirements"] if r["result"] == "fail"}
    assert failed["context.efficacy-claim"]["actualState"] == "unknown"

    calls: list[str] = []

    def model(prompt: str) -> str:
        calls.append(prompt)
        return "must not happen"

    record = run_with_model(None, task_input="Write a claim headline", model=model)
    assert calls == []
    assert record["decision"] == "build_failed"


# --- 3.0.2: the README quickstart is executable evidence, not prose ---------

def _quickstart_block() -> dict[str, str]:
    """The values README.md publishes as the output of the quickstart build.

    Parsed out of the document rather than restated here, so correcting the
    README and correcting this test are the same edit. A copy of the expected
    values in the test file would drift from the page exactly as the page
    drifted from the compiler.
    """
    text = README.read_text(encoding="utf-8")
    match = re.search(
        r"```text\n(targetId\s+brand-query-global-en\n.*?)```",
        text,
        re.DOTALL,
    )
    assert match, "README.md no longer carries the quickstart output block"
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2 and not line.startswith(" ") and not line.startswith("/"):
            fields[parts[0]] = parts[1].strip()
    return fields


def test_the_readme_quickstart_reproduces_exactly_what_it_publishes(tmp_path):
    """A published hash a reader diffs must be the hash the command produces.

    The README block is the first thing an external implementer executes, and
    every value in it is checked here against a real build: the target, the
    status, the artefact reference, both hashes, the requirement row, and the
    three files that land in the output directory.
    """
    published = _quickstart_block()
    manifest, plan = _load("foundation-minimal")
    report = build_all(manifest, plan, output_dir=tmp_path)
    target = report["targets"][0]
    artefact = load_data(tmp_path / target["artifactRef"])

    assert published["targetId"] == target["targetId"]
    assert published["status"] == target["status"]
    assert published["artifactRef"] == target["artifactRef"]
    assert published["artifactHash"] == artefact["artifactHash"]
    assert published["governedResultHash"] == artefact["governedResultHash"]

    element_id, state, outcome = published["requirements"].split()
    assert [(r["elementId"], r["actualState"], r["result"]) for r in target["requirements"]] == [
        (element_id, state, outcome)
    ]

    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "brand-query-global-en.context.json",
        "brand-query-global-en.context.md",
        "build-report.yaml",
    ]


def test_the_quickstart_hashes_are_not_self_referential():
    """The guard that would have caught the 3.0.0 drift.

    `artefact["artifactHash"] == artefact_hash(artefact)` holds for every
    artefact ever sealed, including one whose contents changed. The published
    value has to be a literal in the document, checked against a build.
    """
    published = _quickstart_block()
    text = README.read_text(encoding="utf-8")

    for field in ("artifactHash", "governedResultHash"):
        value = published[field]
        assert value.startswith("sha256:") and len(value) == len("sha256:") + 64, field
        assert text.count(value) >= 1, field
