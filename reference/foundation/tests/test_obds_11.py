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
from obds_ref.canonical import canonical_json_bytes, sha256_id

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


# --- 1.1.1 B5: requiresDefined is an element-ID requirement ------------------

def _manifest_from_case(base_manifest, case):
    """Build a manifest whose elements match a requires-defined-precedence case."""
    from obds_ref.canonical import manifest_content_hash

    manifest = copy.deepcopy(base_manifest)
    template = copy.deepcopy(manifest["elements"][0])
    elements = []
    for spec in case["elements"]:
        element = copy.deepcopy(template)
        element["id"] = spec["id"]
        element["subject"] = spec["subject"]
        element["scope"] = copy.deepcopy(spec["scope"])
        element["state"] = spec["state"]
        element["value"] = {"name": f"Example Minimal Brand {spec['id']}"}
        elements.append(element)
    manifest["elements"] = elements
    manifest["approval"].pop("contentHash", None)
    manifest["approval"]["contentHash"] = manifest_content_hash(manifest)
    return manifest


@pytest.mark.parametrize("case", fixture("requires-defined-precedence.json")["cases"],
                         ids=lambda c: c["id"])
def test_requires_defined_is_an_element_id_requirement(case):
    """Section 13.1: the listed element must itself win its semantic subject.

    An override that displaces the listed element does not satisfy a
    requirement naming the displaced one, even when the override is `defined`.
    Reinterpreting an id requirement as a subject requirement is exactly the
    reading 1.1.1 forbids.
    """
    base_manifest, base_plan = example("foundation-minimal")
    manifest = _manifest_from_case(base_manifest, case)
    plan = copy.deepcopy(base_plan)
    plan["manifestRef"]["contentHash"] = manifest["approval"]["contentHash"]
    plan["targets"][0]["scope"] = copy.deepcopy(case["targetScope"])
    plan["targets"][0]["requiresDefined"] = list(case["requiresDefined"])

    result = build_target(manifest, plan, plan["targets"][0])

    assert result.status == case["expectedStatus"], (
        f"{case['id']}: {case['description']}"
    )
    codes = [e.code for e in result.errors]
    if case["expectedCode"] is None:
        assert codes == []
    else:
        assert case["expectedCode"] in codes, codes


# --- 1.1.1 B4: asOf is carried verbatim into the governed payload ------------

def test_governed_payload_carries_as_of_verbatim():
    """Section 14.3a: `asOf` is the Build Plan string, not a re-serialisation.

    Two plans naming the same instant with different offsets are different
    documents and must produce different governed result hashes. A compiler that
    normalised `Z` to `+00:00` would silently make them agree, which is a
    different contract from the one 1.1.1 states.
    """
    manifest, plan = example("foundation-minimal")
    target = plan["targets"][0]
    elements = list(manifest["elements"])

    for literal in ("2026-08-28T00:00:00Z", "2026-08-28T00:00:00+00:00",
                    "2026-08-28T02:00:00+02:00"):
        payload = governed_result_payload(manifest, target, literal, elements)
        assert payload["asOf"] == literal, "asOf was reformatted"

    same_instant = [
        sha256_id(governed_result_payload(manifest, target, literal, elements))
        for literal in ("2026-08-28T00:00:00Z", "2026-08-28T00:00:00+00:00")
    ]
    assert same_instant[0] != same_instant[1], (
        "two spellings of one instant collapsed to one hash; section 14.3a says "
        "they are different documents"
    )

    # And the artefact produced by a full build carries the plan's own spelling.
    variant = copy.deepcopy(plan)
    variant["asOf"] = "2026-08-28T02:00:00+02:00"
    artefact = build_target(manifest, variant, variant["targets"][0]).artefact
    assert artefact["build"]["asOf"] == "2026-08-28T02:00:00+02:00"


# --- 1.1.1 B2: the normative section 14 example is a valid 1.1 artefact ------

def test_section_14_example_validates_against_the_published_contract():
    """The spec's own Compiled Brand Context example must pass the 1.1 schema.

    In 1.1.0 it carried `schemaVersion: 1.0.0` and no `governedResultHash`, so
    an implementer who followed the normative example emitted an artefact the
    release's own contract rejected.
    """
    import re

    import jsonschema

    # The release archive does not ship VERSION, so the specification is found
    # by its own filename, which is OBDS-<x.y.z>.md in both layouts.
    candidates = [path for path in PACKAGE_ROOT.glob("OBDS-*.md")
                  if re.fullmatch(r"OBDS-\d+\.\d+\.\d+\.md", path.name)]
    assert len(candidates) == 1, f"expected one specification, found {candidates}"
    text = candidates[0].read_text(encoding="utf-8")
    section = text.split("## 14. Compiled Brand Context", 1)[1].split("### 14.0", 1)[0]
    block = re.search(r"```json\n(.*?)\n```", section, re.S).group(1)
    example_artefact = json.loads(block)

    assert example_artefact["schemaVersion"] == "1.1.0"
    assert "governedResultHash" in example_artefact
    assert example_artefact["id"] == (
        f"{example_artefact['manifest']['id']}:context:{example_artefact['targetId']}"
    )

    # Both layouts keep the versioned contract in its own directory.
    schema_path = PACKAGE_ROOT / "schemas" / "1.1.0" / "compiled-context.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    # The example uses "sha256:..." placeholders for hashes; substitute a
    # well-formed digest so the structural contract is what is under test.
    placeholder = "sha256:" + "0" * 64
    def fill(node):
        if isinstance(node, dict):
            return {k: fill(v) for k, v in node.items()}
        if isinstance(node, list):
            return [fill(v) for v in node]
        if node == "sha256:...":
            return placeholder
        return node

    jsonschema.Draft202012Validator(schema).validate(fill(example_artefact))


# --- 1.1.2 B1: section 14.3b, the escape set -------------------------------

def _escape_expectation(code_point: int) -> str:
    """What section 14.3b says a single character serialises to."""
    short = {0x22: '\\"', 0x5C: "\\\\", 0x08: "\\b", 0x09: "\\t",
             0x0A: "\\n", 0x0C: "\\f", 0x0D: "\\r"}
    if code_point in short:
        return short[code_point]
    if code_point <= 0x1F:
        return "\\u%04x" % code_point
    return chr(code_point)


@pytest.mark.parametrize("case", fixture("canonical-escapes.json")["cases"],
                         ids=lambda c: c["codePoint"])
def test_canonical_escapes_follow_section_14_3b(case):
    """The escape set is the contract, so it is asserted character by character.

    Before 1.1.2 section 14.3 named no escape set at all: step 7 covered only
    non-ASCII. A tab could be serialised as a short escape or as a six-character
    escape, both valid JSON, and the two hash differently.
    """
    code_point = int(case["codePoint"][2:], 16)
    expected_char = _escape_expectation(code_point)
    if code_point == 0x0D:
        # Step 2 turns carriage return into line feed before step 7 runs, so
        # canonical output can never contain \r.
        expected_char = "\\n"

    value_bytes = canonical_json_bytes(case["stringValue"])
    assert value_bytes.decode("utf-8") == '{"v":"a%sb"}' % expected_char

    key_bytes = canonical_json_bytes(case["objectKey"])
    assert key_bytes.decode("utf-8") == '{"a%sb":1}' % expected_char


def test_canonical_escapes_do_not_escape_solidus_or_delete():
    """Two consequences section 14.3b states explicitly, pinned separately."""
    assert canonical_json_bytes({"v": "a/b"}) == b'{"v":"a/b"}'
    assert canonical_json_bytes({"v": "a" + chr(0x7F) + "b"}).decode("utf-8") == (
        '{"v":"a' + chr(0x7F) + 'b"}'
    )


def test_canonical_escapes_use_lowercase_hex():
    assert canonical_json_bytes({"v": chr(0x1F)}) == b'{"v":"\\u001f"}'
    assert canonical_json_bytes({"v": chr(0x00)}) == b'{"v":"\\u0000"}'


# --- 1.1.2 B2: section 14.0, the artefact validity window -------------------

def _validity_manifest(base_manifest, case):
    from obds_ref.canonical import manifest_content_hash

    manifest = copy.deepcopy(base_manifest)
    template = copy.deepcopy(manifest["elements"][0])
    elements = []
    for spec in case["elements"]:
        element = copy.deepcopy(template)
        element["id"] = spec["id"]
        element["subject"] = spec["subject"]
        element["scope"] = copy.deepcopy(spec["scope"])
        element["state"] = "defined"
        element["validity"] = {"from": spec["from"], "to": spec["to"]}
        element["value"] = {"name": spec["id"]}
        elements.append(element)
    manifest["elements"] = elements
    manifest["approval"].pop("contentHash", None)
    manifest["approval"]["contentHash"] = manifest_content_hash(manifest)
    return manifest


@pytest.mark.parametrize("case", fixture("validity-window.json")["cases"],
                         ids=lambda c: c["id"])
def test_validity_window_uses_every_scope_matching_element(case):
    """Section 14.0: the window comes from all target-scope-matching elements.

    Taken before the asOf filter and before precedence, so an element that is
    not yet valid, or that loses its subject, still bounds the window. In 1.1.1
    the same paragraph said both "the compiled selection" and "all
    target-scope-matching elements", and the two sets differ.
    """
    data = fixture("validity-window.json")
    base_manifest, base_plan = example("foundation-minimal")
    manifest = _validity_manifest(base_manifest, case)
    plan = copy.deepcopy(base_plan)
    plan["manifestRef"]["contentHash"] = manifest["approval"]["contentHash"]
    plan["asOf"] = data["asOf"]
    plan["targets"][0]["scope"] = copy.deepcopy(data["targetScope"])
    plan["targets"][0]["requiresDefined"] = list(case["requiresDefined"])

    result = build_target(manifest, plan, plan["targets"][0])
    assert result.status == case["expectedStatus"], case["description"]
    artefact = result.artefact
    assert artefact["validFrom"] == case["expectedValidFrom"], case["description"]
    assert artefact["validTo"] == case["expectedValidTo"], case["description"]


def test_validity_window_interval_is_half_open():
    """validTo is exclusive: valid one second before, invalid at validTo itself."""
    from datetime import datetime, timezone

    boundary = fixture("validity-window.json")["runtimeBoundary"]
    valid_to = datetime.fromisoformat(boundary["validTo"].replace("Z", "+00:00"))
    accepted = datetime.fromisoformat(boundary["acceptedAt"].replace("Z", "+00:00"))
    rejected = datetime.fromisoformat(boundary["rejectedAt"].replace("Z", "+00:00"))

    assert accepted < valid_to, "the accepted instant must fall inside the window"
    assert not (rejected < valid_to), "validTo itself must be outside the window"
    assert rejected == valid_to


# --- 1.1.3 B1: section 10.2a, decision-relevant subject conflicts -----------

TRAITS = {
    "fact": {"nature": "fact", "family": "structure", "kind": "brand-identity"},
    "knowledge": {"nature": "knowledge", "family": "context", "kind": "guidance"},
    "blocking-rule": {"nature": "knowledge", "family": "rules", "kind": "rule",
                      "value": {"enforcement": "block", "statement": "placeholder"}},
    "unknown-state": {"nature": "knowledge", "family": "context", "kind": "guidance",
                      "state": "unknown"},
}


def _element_from_spec(template, spec):
    from obds_ref.canonical import manifest_content_hash  # noqa: F401

    element = copy.deepcopy(template)
    element["id"] = spec["id"]
    element["subject"] = spec["subject"]
    element["scope"] = copy.deepcopy(spec["scope"])
    element.update(copy.deepcopy(TRAITS[spec["traits"]]))
    element.setdefault("state", "defined")
    if element["state"] == "defined" and "value" not in element:
        element["value"] = {"name": spec["id"]}
    if element["state"] != "defined":
        element.pop("value", None)
        element.pop("valueContractRef", None)
    return element


def _manifest_with(base_manifest, specs):
    from obds_ref.canonical import manifest_content_hash

    manifest = copy.deepcopy(base_manifest)
    template = copy.deepcopy(manifest["elements"][0])
    manifest["elements"] = [_element_from_spec(template, spec) for spec in specs]
    manifest["approval"].pop("contentHash", None)
    manifest["approval"]["contentHash"] = manifest_content_hash(manifest)
    return manifest


@pytest.mark.parametrize("case", fixture("subject-conflict-relevance.json")["cases"],
                         ids=lambda c: c["id"])
def test_subject_conflict_fails_only_when_decision_relevant(case):
    """Section 10.2a: a conflict fails a target only when the target can read it.

    Before 1.1.3 every conflict anywhere in the scope-matching set failed every
    target, so a manifest defect on a subject a target never touches blocked that
    target. That is fail-arbitrary, not fail-closed: the same manifest would
    block or build depending on which unrelated subject a curator left open.
    """
    data = fixture("subject-conflict-relevance.json")
    base_manifest, base_plan = example("foundation-minimal")
    manifest = _manifest_with(base_manifest, case["elements"])
    plan = copy.deepcopy(base_plan)
    plan["manifestRef"]["contentHash"] = manifest["approval"]["contentHash"]
    target = plan["targets"][0]
    target["scope"] = copy.deepcopy(data["targetScope"])
    target["requiresDefined"] = list(case["requiresDefined"])
    target["styleTexture"] = copy.deepcopy(case["styleTexture"])
    target["stateMap"] = copy.deepcopy(case["stateMap"])

    result = build_target(manifest, plan, target)

    assert result.status == case["expectedStatus"], case["description"]
    codes = [error.code for error in result.errors]
    for expected in case["expectedCodes"]:
        assert expected in codes, f"{case['id']}: expected {expected}, got {codes}"
    if not case["expectedCodes"]:
        assert "OBDS-BUILD-SUBJECT-CONFLICT" not in codes, case["description"]

    # An irrelevant conflict must still be visible. Silently discarding it would
    # hide a real manifest defect.
    assert result.conflicts, "the conflict must be reported whatever the outcome"
    relevant = [c.get("decisionRelevant") for c in result.conflicts]
    assert case["expectedDecisionRelevant"] in relevant, (
        f"{case['id']}: decisionRelevant flags were {relevant}"
    )


# --- 1.1.3 B3: section 14.3a, projection must not change the selection ------

def test_projection_policies_do_not_change_the_governed_selection():
    """styleTexture and stateMap decide what is rendered, not what was resolved.

    Four targets differing only in their projection policies must resolve the
    identical `selection`. Their governedResultHash values still differ, because
    both policies sit inside `target` and the payload carries `target` verbatim:
    two plans asking for different projections are different governed requests.
    What must not happen is the projection changing which truth was resolved.
    An implementation building `selection` from includedElementIds would produce
    a different selection for each variant, and that is the failure this pins.
    """
    from obds_ref.compiler import _resolve_subject_precedence, _valid_at, scope_matches
    from obds_ref.compiler import _parse_timestamp

    data = fixture("governed-selection-projection.json")
    base_manifest, base_plan = example("foundation-minimal")
    manifest = _manifest_with(base_manifest, data["elements"])

    selections = {}
    governed = {}
    artefacts = {}
    for variant in data["variants"]:
        plan = copy.deepcopy(base_plan)
        plan["manifestRef"]["contentHash"] = manifest["approval"]["contentHash"]
        target = plan["targets"][0]
        target["scope"] = copy.deepcopy(data["targetScope"])
        target["requiresDefined"] = list(data["requiresDefined"])
        target["styleTexture"] = copy.deepcopy(variant["styleTexture"])
        target["stateMap"] = copy.deepcopy(variant["stateMap"])

        result = build_target(manifest, plan, target)
        assert result.status == "ready", f"{variant['id']}: {[e.code for e in result.errors]}"
        governed[variant["id"]] = result.artefact["governedResultHash"]
        artefacts[variant["id"]] = result.artefact["artifactHash"]

        # Rebuild the selection the way section 14.3a defines it: applicability
        # then precedence, and nothing after it.
        as_of = _parse_timestamp(plan["asOf"], field_name="asOf")
        scope_matching = [
            element for element in manifest["elements"]
            if scope_matches(element.get("scope", {}), target["scope"])
        ]
        time_applicable = [e for e in scope_matching if _valid_at(e, as_of)]
        applicable, _ = _resolve_subject_precedence(time_applicable)
        payload = governed_result_payload(manifest, target, plan["asOf"], applicable)
        selections[variant["id"]] = [entry["elementId"] for entry in payload["selection"]]

    expectation = data["expectation"]
    for variant_id, ids in selections.items():
        assert ids == expectation["selectionElementIds"], (
            f"{variant_id}: projection changed the resolved selection: {ids}"
        )
    assert len({tuple(ids) for ids in selections.values()}) == 1

    # The artefact must differ, and so must the governed hash, because both
    # policies are inside `target`. Neither is a defect; both are the contract.
    assert len(set(artefacts.values())) == len(artefacts), (
        "projection policy did not change the artefact: " + repr(artefacts)
    )
    assert len(set(governed.values())) == len(governed), (
        "target carries the policies verbatim, so the governed hash must move too"
    )
