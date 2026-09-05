"""Systemic mechanism 1 — a published contract and the code cannot diverge.

Nine of the nineteen defects eleven review rounds produced had one shape: a
published 3.0 contract constrains a field and the code does not, so a document
the contract rejects still reaches a governed decision. Each was found by
someone guessing the right field — `enforcement`, then `mode`, then `appliesTo`,
then `compiledChecks`, then a number that overflows.

Guessing does not close a shape. This does: it takes each published contract,
finds every leaf the contract constrains *by asking the contract*, and requires
the code to constrain it too. A field nobody has thought of is covered the day it
is added to a schema, and a contract published without an executor fails
outright.

Both directions are tested:

    contract rejects  → the code must reject
    contract accepts  → the code must not reject because of that value

The second direction matters as much as the first. A code path stricter than the
published contract is the same interoperability defect wearing the other face:
an independent implementation follows the contract and is refused.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest

from obds_ref.canonical import (
    artefact_hash,
    manifest_content_hash,
    sha256_id,
    value_shape_hash,
)
from obds_ref.checks import CompiledCheckContractError, assert_materialised
from obds_ref.compiler import (
    ValidationFailure,
    build_target,
    load_data,
    validate_manifest,
    validate_plan,
)
from obds_ref.runtime import DECISIONS, append_runtime_record, run_with_model
from systemic_surface import PACKAGE_ROOT, PUBLISHED_3_0_CONTRACTS, REFERENCE

# A value no vocabulary in the release contains. Substituted into a leaf, it asks
# the contract "is this field constrained?" without the test needing to know.
SENTINEL = "obds-systemic-probe-value"


def contract(relative: str):
    return load_data(PACKAGE_ROOT / relative)


def validator_for(relative: str):
    return jsonschema.Draft202012Validator(contract(relative))


# --------------------------------------------------------------------------
# Base documents: one valid instance per contract, plus the executor that
# decides whether the *code* accepts it.
# --------------------------------------------------------------------------

def _example(name):
    base = PACKAGE_ROOT / "examples" / name
    return load_data(base / "manifest.yaml"), load_data(base / "build-plan.yaml")


def _rule_value():
    return {
        "statement": "Never say it.",
        "obligation": "prohibit",
        "enforcement": "block",
        "validationMode": "deterministic",
        "canonicalWording": "Never say it.",
        "condition": {},
        "requirement": {},
        "references": [],
        "checks": [
            {
                "primitive": "term_prohibited",
                "phase": "postflight",
                "params": {"terms": ["the best"], "match": "case_insensitive", "appliesTo": "output"},
            }
        ],
    }


def _manifest_with_rule(rule_value):
    """A valid manifest whose only rule is the one under test."""
    manifest, plan = _example("foundation-minimal")
    manifest = copy.deepcopy(manifest)
    template = copy.deepcopy(manifest["elements"][0])
    template.update(
        {
            "id": "rules.probe",
            "family": "rules",
            "kind": "probe-rule",
            "subject": "subject:probe",
            "nature": "knowledge",
            "state": "defined",
            "scope": {},
            "value": rule_value,
            "valueContractRef": "urn:obds:probe#value-contract:rules:probe",
        }
    )
    schema_ref = "https://openbranddefinition.org/value-schemas/3.0.0/rule.schema.json"
    manifest["elements"] = manifest["elements"] + [template]
    manifest["valueContracts"] = list(manifest["valueContracts"]) + [
        {
            "id": template["valueContractRef"],
            "family": "rules",
            "kind": "rule",
            "shapeHash": value_shape_hash(rule_value),
            "schemaRef": schema_ref,
            "schemaHash": sha256_id(
                load_data(REFERENCE / "foundation" / "value-schemas" / "3.0.0" / "rule.schema.json")
            ),
            "validatorRef": None,
        }
    ]
    manifest["approval"]["contentHash"] = manifest_content_hash(manifest)
    plan = copy.deepcopy(plan)
    plan["manifestRef"]["contentHash"] = manifest["approval"]["contentHash"]
    return manifest, plan


def _artefact_with_a_compiled_check():
    manifest, plan = _manifest_with_rule(_rule_value())
    result = build_target(manifest, plan, plan["targets"][0])
    assert result.status == "ready", [error.message for error in result.errors]
    assert result.artefact["compiledChecks"], "the probe artefact carries no compiled check"
    return result.artefact


def _runtime_record():
    artefact = _artefact_with_a_compiled_check()
    record = run_with_model(
        artefact,
        task_input="A clean request.",
        model=lambda prompt: "A careful answer.",
        target_id=artefact["targetId"],
    )
    return {key: value for key, value in record.items() if key != "output"}


# Each executor answers one question: does the *code* accept this document?
# `True` means accepted; `False` means refused, however the refusal is spelled.

def _code_accepts_build_plan(document):
    return validate_plan(document) == []


def _code_accepts_rule_value(document):
    manifest, _ = _manifest_with_rule(document)
    return validate_manifest(manifest, verify_hash=False) == []


def _code_accepts_compiled_context(document, *, reseal=False):
    """A compiled artefact reaches the code through the runtime that executes it.

    Both directions reseal. Presenting a mutated artefact with its original hash
    let the runtime's hash check answer every probe, so this executor reported
    "the code rejects it" for every leaf in the contract while the runtime read
    `slots` without ever validating the contract at all. The hash is not the
    subject of either direction: it proves the payload is intact, and mechanism 1
    is about whether an intact payload is governable.
    """
    document = copy.deepcopy(document)
    if reseal:
        document["artifactHash"] = artefact_hash(document)
    try:
        for check in document.get("compiledChecks", []):
            assert_materialised(check)
    except CompiledCheckContractError:
        return False
    record = run_with_model(
        document,
        task_input="A clean request.",
        model=lambda prompt: "A careful answer.",
        target_id=document.get("targetId"),
    )
    return record["decision"] not in {"no_valid_artifact", "build_failed"}


def _code_accepts_runtime_record(document, tmp_path=None):
    import tempfile

    directory = Path(tempfile.mkdtemp())
    try:
        append_runtime_record(directory / "records.ndjson", copy.deepcopy(document))
        return True
    except (ValueError, TypeError):
        return False
    finally:
        for item in directory.iterdir():
            item.unlink()
        directory.rmdir()


def _accepts(code_accepts, document, *, reseal):
    """Call an executor, passing `reseal` only to the one that understands it."""
    import inspect

    if "reseal" in inspect.signature(code_accepts).parameters:
        return code_accepts(document, reseal=reseal)
    return code_accepts(document)


EXECUTORS = {
    "build-plan": (lambda: _example("foundation-minimal")[1], _code_accepts_build_plan),
    "rule-value": (_rule_value, _code_accepts_rule_value),
    "compiled-context": (_artefact_with_a_compiled_check, _code_accepts_compiled_context),
    "runtime-decision-record": (_runtime_record, _code_accepts_runtime_record),
}


def test_every_published_3_0_contract_has_an_executor():
    """A contract nothing executes is a claim, not a check.

    This is the enumeration guard: publishing a 3.0 contract without naming what
    executes it fails here rather than escaping the systemic tests below.
    """
    published = set(PUBLISHED_3_0_CONTRACTS.values())
    assert published == set(EXECUTORS), (
        f"contracts without an executor: {sorted(published - set(EXECUTORS))}; "
        f"executors without a contract: {sorted(set(EXECUTORS) - published)}"
    )
    for relative in PUBLISHED_3_0_CONTRACTS:
        assert (PACKAGE_ROOT / relative).is_file(), relative


def test_the_published_contracts_are_the_ones_on_disk():
    """The registry names every 3.0 contract, and no more."""
    on_disk = {
        str(path.relative_to(PACKAGE_ROOT))
        for directory in ("schemas/3.0.0", "value-schemas/3.0.0")
        for path in (PACKAGE_ROOT / directory).glob("*.json")
    }
    # The 3.0 record is frozen; its current executor now uses the 4.0 contract.
    on_disk.remove("schemas/3.0.0/runtime-decision-record.schema.json")
    on_disk.add("schemas/4.0.0/runtime-decision-record.schema.json")
    assert on_disk == set(PUBLISHED_3_0_CONTRACTS), (
        f"unregistered: {sorted(on_disk - set(PUBLISHED_3_0_CONTRACTS))}; "
        f"missing: {sorted(set(PUBLISHED_3_0_CONTRACTS) - on_disk)}"
    )


# --------------------------------------------------------------------------
# Leaf enumeration. The document is walked, not the schema, so a constraint
# expressed through `oneOf`, `if`/`then` or `$defs` is found the same way as one
# written directly on a property.
# --------------------------------------------------------------------------

def _leaves(document, path=()):
    if isinstance(document, dict):
        for key, value in document.items():
            yield from _leaves(value, path + (key,))
    elif isinstance(document, list):
        for index, value in enumerate(document):
            yield from _leaves(value, path + (index,))
    else:
        yield path, document


def _replace(document, path, value):
    clone = copy.deepcopy(document)
    node = clone
    for step in path[:-1]:
        node = node[step]
    node[path[-1]] = value
    return clone


def _schema_accepts(validator, document):
    return not list(validator.iter_errors(document))


CONSTRAINED_LEAF_CASES = []
for _relative, _name in sorted(PUBLISHED_3_0_CONTRACTS.items(), key=lambda item: item[1]):
    CONSTRAINED_LEAF_CASES.append(pytest.param(_relative, _name, id=_name))


@pytest.mark.parametrize("relative,name", CONSTRAINED_LEAF_CASES)
def test_mechanism_1_contract_rejects_implies_code_rejects(relative, name):
    """Every leaf the contract constrains, the code constrains too.

    Substituting a sentinel asks the contract whether a leaf is decision-bearing.
    Where the contract says yes, the code has to say yes as well — otherwise a
    document the published contract refuses still produces a governed decision,
    which is exactly how `enforcement`, `mode`, `appliesTo`, `compiledChecks` and
    an overflowing number each escaped in turn.
    """
    validator = validator_for(relative)
    build_base, code_accepts = EXECUTORS[name]
    base = build_base()

    assert _schema_accepts(validator, base), f"{name}: the base document does not satisfy its own contract"
    assert code_accepts(base), f"{name}: the code rejects its own valid base document"

    constrained = []
    divergent = []
    for path, value in _leaves(base):
        if isinstance(value, bool) or value is None:
            continue
        if name == "compiled-context" and path == ("artifactHash",):
            # The seal is not one of the fields the seal covers: resealing
            # restores it by construction, so driving it here would only measure
            # the reseal. It is driven without resealing after the loop.
            continue
        probe = _replace(base, path, SENTINEL)
        if _schema_accepts(validator, probe):
            continue
        constrained.append(path)
        try:
            accepted = _accepts(code_accepts, probe, reseal=True)
        except (ValidationFailure, ValueError, TypeError, KeyError):
            accepted = False
        if accepted:
            divergent.append(".".join(str(step) for step in path))

    if name == "compiled-context":
        tampered = _replace(base, ("artifactHash",), SENTINEL)
        assert not _accepts(code_accepts, tampered, reseal=False), (
            "a compiled context whose seal does not match its payload was accepted"
        )

    assert constrained, f"{name}: the contract constrains no leaf of its own base document"
    assert not divergent, (
        f"{name}: the published contract refuses these leaves and the code does not: "
        + ", ".join(sorted(divergent))
    )


@pytest.mark.parametrize("relative,name", CONSTRAINED_LEAF_CASES)
def test_mechanism_1_contract_accepts_implies_code_accepts(relative, name):
    """The other direction: the code may not be stricter than what it publishes.

    A code path narrower than the contract is the same interoperability defect
    wearing the other face — an independent implementation follows the published
    vocabulary and is refused.

    Only enumerated vocabularies are driven here, because they are the values the
    contract explicitly declares admissible. A substitution that is legal by the
    contract but meaningless in context is skipped, and skipping is recorded:
    the test asserts it drove something.
    """
    validator = validator_for(relative)
    build_base, code_accepts = EXECUTORS[name]
    base = build_base()

    driven = 0
    divergent = []
    for path, value in _leaves(base):
        if not isinstance(value, str):
            continue
        # Discover this leaf's vocabulary by asking the contract about every
        # value any enum in the release declares for a field of this name.
        for candidate in _vocabulary_for(relative, path[-1]):
            if candidate == value:
                continue
            probe = _replace(base, path, candidate)
            if not _schema_accepts(validator, probe):
                continue
            driven += 1
            try:
                accepted = _accepts(code_accepts, probe, reseal=True)
            except (ValidationFailure, ValueError, TypeError, KeyError):
                accepted = False
            if not accepted:
                divergent.append(f"{'.'.join(str(step) for step in path)}={candidate}")

    assert driven, f"{name}: no enumerated vocabulary was driven"
    assert not divergent, (
        f"{name}: the published contract admits these values and the code refuses them: "
        + ", ".join(sorted(divergent))
    )


def _vocabulary_for(relative, field):
    """Every value the contract declares for a property of this name."""
    values = set()

    def walk(node, key=None):
        if isinstance(node, dict):
            if key == field:
                if isinstance(node.get("enum"), list):
                    values.update(item for item in node["enum"] if isinstance(item, str))
                if isinstance(node.get("const"), str):
                    values.add(node["const"])
            for name, child in node.items():
                if name == "properties" and isinstance(child, dict):
                    for property_name, property_schema in child.items():
                        walk(property_schema, property_name)
                else:
                    walk(child, key)
        elif isinstance(node, list):
            for child in node:
                walk(child, key)

    walk(contract(relative))
    return sorted(values)


RESEALED_CONTRACT_CASES = [
    ("a property the contract forbids", lambda d: d.__setitem__("totallyUnknownProperty", "x")),
    ("a required slot removed", lambda d: d["slots"].pop("styleTexture")),
    ("a required top-level property removed", lambda d: d.pop("governedResultHash")),
    ("a required build property removed", lambda d: d["build"].pop("asOf")),
]


@pytest.mark.parametrize("name,mutate", RESEALED_CONTRACT_CASES, ids=[c[0] for c in RESEALED_CONTRACT_CASES])
def test_mechanism_1_a_resealed_schema_invalid_context_is_no_valid_artifact(name, mutate):
    """A correct seal over a document the contract refuses is still refused.

    The hash and the contract answer two different questions. The runtime asked
    only the first and then read `slots`, so a resealed artefact carrying a
    forbidden property was `released`, and one missing a required slot raised
    `KeyError` out of prompt assembly — a crash where the contract requires a
    governed decision. Every case here reseals, so the schema gate is what has
    to kill the artefact.
    """
    document = _artefact_with_a_compiled_check()
    mutate(document)
    document["artifactHash"] = artefact_hash(document)

    calls = []

    def model(prompt):
        calls.append(prompt)
        return "should not happen"

    record = run_with_model(
        document,
        task_input="A clean request.",
        model=model,
        target_id=document.get("targetId"),
    )
    assert record["decision"] == "no_valid_artifact", (
        f"{name}: a schema-invalid compiled context decided {record['decision']!r}"
    )
    assert record["modelCall"]["called"] is False, f"{name}: the model was called anyway"
    assert calls == [], f"{name}: the model was called anyway"


def test_mechanism_1_a_valid_context_still_reaches_the_model():
    """The gate is not a wall: the unmutated artefact takes the governed path."""
    document = _artefact_with_a_compiled_check()
    document["artifactHash"] = artefact_hash(document)
    calls = []
    record = run_with_model(
        document,
        task_input="A clean request.",
        model=lambda prompt: (calls.append(prompt), "A careful answer.")[1],
        target_id=document.get("targetId"),
    )
    assert record["decision"] == "released"
    assert record["modelCall"]["called"] is True
    assert len(calls) == 1


def test_mechanism_1_the_runtime_validates_the_contract_it_publishes():
    """The runtime's validator is the file the release serves, not a copy of it."""
    from obds_ref import runtime as runtime_module

    published = PACKAGE_ROOT / "schemas" / "3.0.0" / "compiled-context.schema.json"
    assert load_data(runtime_module._CONTEXT_SCHEMA_PATH) == load_data(published), (
        "the runtime validates a Compiled Brand Context contract the release does not serve"
    )


def test_mechanism_1_the_decision_vocabulary_is_one_vocabulary():
    """The runtime's decision values and the record contract's are one list."""
    record_contract = contract("schemas/4.0.0/runtime-decision-record.schema.json")
    assert set(record_contract["properties"]["decision"]["enum"]) == DECISIONS


def test_mechanism_1_the_enforcement_vocabulary_is_one_vocabulary():
    """The RULE contract, the compiled contract and the runtime agree on it.

    They did not: the compiled contract listed `advise`, which OBDS does not
    have, and omitted `warn` and `inform`, which it does.
    """
    from obds_ref.checks import COMPILED_ENFORCEMENT_VALUES

    rule_values = set(_vocabulary_for("value-schemas/3.0.0/rule.schema.json", "enforcement"))
    compiled_values = set(
        _vocabulary_for("schemas/3.0.0/compiled-context.schema.json", "enforcement")
    )
    assert compiled_values == set(COMPILED_ENFORCEMENT_VALUES)
    assert compiled_values <= rule_values, (
        "the compiled contract admits an enforcement value the RULE contract does not: "
        f"{sorted(compiled_values - rule_values)}"
    )


def test_mechanism_1_the_match_vocabulary_is_one_vocabulary():
    from obds_ref.checks import LITERAL_MATCH_MODES, TERM_MATCH_MODES

    declared = set(_vocabulary_for("schemas/3.0.0/compiled-context.schema.json", "match"))
    assert declared == TERM_MATCH_MODES | LITERAL_MATCH_MODES, (
        f"contract {sorted(declared)} vs code {sorted(TERM_MATCH_MODES | LITERAL_MATCH_MODES)}"
    )
