"""OBDS 1.1 normative cases.

Every expected value comes from a fixture under fixtures/obds-1.1/, each of
which was derived twice independently before it was written. These tests assert
the reference implementation against those fixtures; they do not define the
values.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from obds_ref.compiler import (
    build_all,
    build_target,
    governed_result_payload,
    load_data,
)
from obds_ref.canonical import sha256_id

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT.parents[1]
FIXTURES = ROOT / "fixtures" / "obds-1.1"


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def example(name):
    base = PACKAGE_ROOT / "examples" / name
    return load_data(base / "manifest.yaml"), load_data(base / "build-plan.yaml")


# --- governed result --------------------------------------------------------

def test_governed_result_hash_matches_the_fixture():
    for vector in fixture("governed-result-hash.json")["vectors"]:
        manifest, plan = example(vector["example"])
        payload = governed_result_payload(
            manifest, plan["targets"][0], plan["asOf"], list(manifest["elements"])
        )
        assert payload == vector["payload"], vector["example"]
        assert sha256_id(payload) == vector["expectedGovernedResultHash"], vector["example"]


def test_governed_result_hash_ignores_capacity():
    """maxTokens is capacity, not governance. It must not move the hash."""
    data = fixture("governed-result-invariance.json")
    manifest, plan = example("foundation-minimal")
    hashes = {
        sha256_id(governed_result_payload(
            manifest, variant["target"], plan["asOf"], list(manifest["elements"])
        ))
        for variant in data["variants"]
    }
    assert hashes == {data["expectedGovernedResultHash"]}


def test_governed_result_hash_survives_a_governance_neutral_patch():
    """Section 27.2: a source-reference rotation is not a change to Brand Truth."""
    data = fixture("governed-result-neutrality.json")
    manifest, plan = example("foundation-minimal")
    target = plan["targets"][0]
    before = sha256_id(governed_result_payload(
        manifest, target, plan["asOf"], list(manifest["elements"])
    ))

    patched = copy.deepcopy(manifest)
    patched["version"] = "1.0.1"
    for element in patched["elements"]:
        element["sourceRefs"] = ["dossier#sha256:rotated"]
        element["annotations"] = [{"note": "provenance correction"}]
    after = sha256_id(governed_result_payload(
        patched, target, plan["asOf"], list(patched["elements"])
    ))

    assert before == after == data["expectedGovernedResultHash"]


def test_governed_result_hash_moves_when_a_value_moves():
    """The other direction: a real change to Brand Truth MUST move the hash."""
    manifest, plan = example("foundation-minimal")
    target = plan["targets"][0]
    before = sha256_id(governed_result_payload(
        manifest, target, plan["asOf"], list(manifest["elements"])
    ))
    changed = copy.deepcopy(manifest)
    changed["elements"][0]["value"]["name"] = "A Different Brand"
    after = sha256_id(governed_result_payload(
        changed, target, plan["asOf"], list(changed["elements"])
    ))
    assert before != after


def test_compiled_context_carries_the_governed_result_hash():
    manifest, plan = example("foundation-minimal")
    result = build_target(manifest, plan, plan["targets"][0])
    assert result.status == "ready", [e.code for e in result.errors]
    artefact = result.artefact
    assert artefact["schemaVersion"] == "1.1.0"
    assert artefact["governedResultHash"].startswith("sha256:")
    assert artefact["governedResultHash"] != artefact["artifactHash"]


def test_governed_result_excludes_implementation_facts():
    manifest, plan = example("foundation-minimal")
    payload = governed_result_payload(
        manifest, plan["targets"][0], plan["asOf"], list(manifest["elements"])
    )
    serialised = json.dumps(payload)
    for excluded in ("maxTokens", "compilerId", "compilerVersion", "tokenizer",
                     "artifactHash", "slots", "tokenBudget"):
        assert excluded not in serialised, excluded
    assert "version" not in payload["manifest"], "R-14 excludes the manifest version"
    for entry in payload["selection"]:
        assert set(entry) == {"elementId", "subject", "state", "valueHash"}


# --- context id -------------------------------------------------------------

def test_context_id_construction():
    for case in fixture("context-id.json")["cases"]:
        assert f"{case['manifestId']}:context:{case['targetId']}" == case["expectedId"]


def test_compiled_context_id_follows_the_rule():
    manifest, plan = example("foundation-minimal")
    result = build_target(manifest, plan, plan["targets"][0])
    artefact = result.artefact
    assert artefact["id"] == f"{manifest['id']}:context:{plan['targets'][0]['id']}"


# --- required element inclusion, D-5 ----------------------------------------

def test_required_knowledge_element_reaches_the_artefact():
    """A required element must not be dropped by context selection.

    Before 1.1 a knowledge-natured element named in requiresDefined was verified
    as `defined`, the build succeeded, and the element was absent from the
    artefact whenever styleTexture.mode was `none`.
    """
    manifest, plan = example("foundation-minimal")
    manifest = copy.deepcopy(manifest)
    manifest["elements"].append({
        "id": "context.tone",
        "family": "context",
        "kind": "guidance",
        "nature": "knowledge",
        "state": "defined",
        "scope": {},
        "sourceRefs": [],
        "validity": {"from": None, "to": None},
        "annotations": [],
        "value": "Plain and direct.",
    })
    from obds_ref.canonical import manifest_content_hash
    manifest["approval"]["contentHash"] = manifest_content_hash(manifest)

    plan = copy.deepcopy(plan)
    plan["manifestRef"]["contentHash"] = manifest["approval"]["contentHash"]
    target = plan["targets"][0]
    target["requiresDefined"] = ["structure.brand", "context.tone"]
    target["styleTexture"] = {"mode": "none", "elementIds": []}

    result = build_target(manifest, plan, target)
    assert result.status == "ready", [e.code for e in result.errors]
    assert "context.tone" in result.artefact["includedElementIds"]
    assert "context.tone" in result.artefact["slots"]["styleTexture"]


# --- build error codes ------------------------------------------------------

def _plan_requiring(plan, element_id, **target_overrides):
    plan = copy.deepcopy(plan)
    target = plan["targets"][0]
    target["requiresDefined"] = [element_id]
    target.update(target_overrides)
    return plan


def test_missing_required_element_reports_not_found():
    """A requiresDefined id that is not in the manifest gets its own code.

    Before 1.1 this surfaced as OBDS-BUILD-REQUIRED-NOT-DEFINED, the same code
    an out-of-scope or expired element produced, so an operator could not tell
    "never curated" from "mis-scoped target".
    """
    manifest, plan = example("foundation-minimal")
    plan = _plan_requiring(plan, "structure.does-not-exist")
    result = build_target(manifest, plan, plan["targets"][0])
    assert result.status == "failed"
    assert [e.code for e in result.errors] == ["OBDS-BUILD-REQUIRED-NOT-FOUND"]
    assert result.requirements[0]["actualState"] == "missing"


def test_out_of_scope_required_element_reports_its_own_code():
    manifest, plan = example("foundation-minimal")
    manifest = copy.deepcopy(manifest)
    manifest["elements"][0]["scope"] = {"markets": ["DE"]}
    from obds_ref.canonical import manifest_content_hash
    manifest["approval"]["contentHash"] = manifest_content_hash(manifest)
    plan = copy.deepcopy(plan)
    plan["manifestRef"]["contentHash"] = manifest["approval"]["contentHash"]
    plan["targets"][0]["scope"] = {"locales": ["en"], "outputTypes": ["brand-query"],
                                   "markets": ["AT"]}
    result = build_target(manifest, plan, plan["targets"][0])
    assert result.status == "failed"
    assert [e.code for e in result.errors] == ["OBDS-BUILD-REQUIRED-OUT-OF-SCOPE"]


def test_expired_required_element_reports_its_own_code():
    manifest, plan = example("foundation-minimal")
    manifest = copy.deepcopy(manifest)
    manifest["elements"][0]["validity"] = {"from": None, "to": "2026-01-01T00:00:00Z"}
    from obds_ref.canonical import manifest_content_hash
    manifest["approval"]["contentHash"] = manifest_content_hash(manifest)
    plan = copy.deepcopy(plan)
    plan["manifestRef"]["contentHash"] = manifest["approval"]["contentHash"]
    result = build_target(manifest, plan, plan["targets"][0])
    assert result.status == "failed"
    assert [e.code for e in result.errors] == ["OBDS-BUILD-REQUIRED-EXPIRED"]


# --- scope vocabulary and applicability --------------------------------------

def test_content_purposes_is_an_accepted_scope_dimension():
    """Section 9 documented contentPurposes; the reference used to reject it."""
    from obds_ref.compiler import SCOPE_DIMENSIONS
    assert "contentPurposes" in SCOPE_DIMENSIONS
    assert "brands" in SCOPE_DIMENSIONS
    assert len(SCOPE_DIMENSIONS) == 9


def test_element_restricting_a_dimension_the_target_omits_is_not_applicable():
    manifest, plan = example("foundation-minimal")
    manifest = copy.deepcopy(manifest)
    manifest["elements"][0]["scope"] = {"channels": ["linkedin"]}
    from obds_ref.canonical import manifest_content_hash
    manifest["approval"]["contentHash"] = manifest_content_hash(manifest)
    plan = copy.deepcopy(plan)
    plan["manifestRef"]["contentHash"] = manifest["approval"]["contentHash"]
    result = build_target(manifest, plan, plan["targets"][0])
    assert result.status == "failed"
    assert result.requirements[0]["actualState"] == "not_applicable"


# --- tokenizer ---------------------------------------------------------------

def test_whitespace_v1_separator_set():
    from obds_ref.compiler import _whitespace_tokens
    for case in fixture("whitespace-v1.json")["cases"]:
        assert _whitespace_tokens(case["text"]) == case["expectedTokens"], case["label"]


# --- compiler identity, section 14.4 ----------------------------------------

def test_compiler_identity_is_the_compiler_that_ran():
    """An implementation records its own identity, never the plan's.

    Before 1.1 the artefact copied the Build Plan's declared compiler identity,
    so a plan naming any other compiler produced an artefact claiming provenance
    that never happened. A build plan naming a foreign compiler still builds:
    the plan's compiler block is provenance, not a precondition.
    """
    from obds_ref.compiler import COMPILER_ID, COMPILER_VERSION
    manifest, plan = example("foundation-minimal")
    plan = copy.deepcopy(plan)
    plan["compiler"] = {"id": "org.independent.obds-ts-foundation", "version": "0.1.0"}

    result = build_target(manifest, plan, plan["targets"][0])
    assert result.status == "ready", [e.code for e in result.errors]
    assert result.artefact["build"]["compilerId"] == COMPILER_ID
    assert result.artefact["build"]["compilerVersion"] == COMPILER_VERSION
