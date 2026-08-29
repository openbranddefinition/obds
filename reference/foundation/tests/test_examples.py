"""The published examples must behave exactly as examples/README.md documents.

These two cases keep examples/ load-bearing. An example that drifts from the
reference implementation is worse than no example at all.
"""

from __future__ import annotations

from pathlib import Path

from obds_ref.canonical import artefact_hash
from obds_ref.compiler import build_all, load_data, validate_manifest, validate_plan
from obds_ref.runtime import run_with_model

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
EXAMPLES = PACKAGE_ROOT / "examples"


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
