"""OBDS 3.0.0 Class B — governed identity and approval integrity.

The invariant: the same `approval.contentHash` cannot resolve to a different
governed identity.

It failed in 2.0.0 for one reason, and the reason has a closed form.
Canonicalisation is `fold_LF . NFC`; identity is `NFC`. So canonicalisation is a
strict coarsening of identity and the coarsening is exactly the section 14.3
step-2 line-ending fold — verified over 2,299,296 strings, with `fold` and `NFC`
commuting in every case. Every collision in the class is therefore a
CR/CRLF-vs-LF collision, and every such pair in an identity position is a
collision. 16 collisions were found across 14 identity positions; all 16 are one
defect and one fix.

These tests are written against the class, not against the 16 examples. B1
builds one document that populates every audited identity position, checks the
compiler's own enumeration covers all of them, and then drives every position
against every forbidden separator. B2 states the universal property the class
violated.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from obds_ref.canonical import (
    IDENTITY_FORBIDDEN_CHARACTERS,
    artefact_hash,
    compiled_context_identity_positions,
    model_input_package_identity_positions,
    _normalise_string,
    canonical_json_bytes,
    identity_key,
    manifest_content_hash,
    sha256_id,
)
from obds_ref.compiler import (
    IDENTITY_POSITION_ENUMERATORS,
    _manifest_identity_positions,
    _plan_identity_positions,
    build_all,
    load_data,
    validate_manifest,
    validate_plan,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[3]

# The identity positions the closure audit enumerated. B1 asserts the compiler's
# enumeration covers every one of them, so the driven test below cannot pass by
# enumerating a shorter list than the class.
AUDITED_POSITIONS = {
    "id",
    # Added in the fifth review round. The audit's original list stopped at
    # `id`, and so did the enumerator and this oracle — registry and test agreed
    # with each other while both were incomplete, which is the one way a
    # hand-kept oracle can fail silently.
    "version",
    "valueContracts[].id",
    "elements[].id",
    "elements[].subject",
    "elements[].kind",
    "elements[].valueContractRef",
    "elements[].scope",
    "elements[].value.references[]",
    "elements[].value.requiresDefinedRefs[]",
    "elements[].value.checks[].params.elementValueRef.elementId",
    "manifestRef.id",
    "manifestRef.version",
    "targets[].id",
    "targets[].requiresDefined[]",
    "targets[].scope",
    "targets[].contextAssembly.eligibleGuidanceIds[]",
    "targets[].styleTexture.elementIds[]",
    "targets[].stateMap.kinds[]",
}


def example(name):
    base = PACKAGE_ROOT / "examples" / name
    return load_data(base / "manifest.yaml"), load_data(base / "build-plan.yaml")


def _all_examples():
    root = PACKAGE_ROOT / "examples"
    return sorted(path.name for path in root.iterdir() if (path / "manifest.yaml").is_file())


def _shape(where: str) -> str:
    """Collapse `elements[3].scope.markets[0]` to `elements[].scope`."""
    import re

    where = re.sub(r"\[\d+\]", "[]", where)
    if ".scope." in where:
        return where.split(".scope.")[0] + ".scope"
    return where


# --------------------------------------------------------------------------
# One document that populates every audited identity position.
#
# Every identity in it is unique, so a position can be addressed by its value
# rather than by a path expression: replace that one string anywhere in the
# document and exactly one position changes. That keeps the test driven by the
# compiler's enumeration rather than by a hand-maintained path parser.
# --------------------------------------------------------------------------

def _full_coverage_documents():
    manifest, plan = example("foundation-minimal")
    manifest = copy.deepcopy(manifest)
    plan = copy.deepcopy(plan)

    manifest["version"] = "7.8.9"
    plan["manifestRef"]["version"] = "7.8.9"

    base = copy.deepcopy(manifest["elements"][0])
    base.pop("valueContractRef", None)

    guidance = copy.deepcopy(base)
    guidance.update(
        {
            "id": "identity.pos-guidance",
            "family": "identity",
            "kind": "pos-kind-guidance",
            "subject": "pos-subject-guidance",
            "nature": "knowledge",
            "state": "defined",
            "scope": {"locales": ["pos-scope-locale"]},
            "value": {"statement": "Guidance."},
        }
    )

    fact = copy.deepcopy(base)
    fact.update(
        {
            "id": "context.pos-fact",
            "valueContractRef": "vc.pos-fact",
            "family": "context",
            "kind": "pos-kind-fact",
            "subject": "pos-subject-fact",
            "nature": "fact",
            "state": "defined",
            "scope": {},
            "value": {"statement": "A fact."},
        }
    )

    rule = copy.deepcopy(base)
    rule.update(
        {
            "id": "rules.pos-rule",
            "family": "rules",
            "kind": "pos-kind-rule",
            "subject": "pos-subject-rule",
            "nature": "knowledge",
            "state": "defined",
            "scope": {},
            "value": {
                "obligation": "prohibit",
                "enforcement": "block",
                "validationMode": "deterministic",
                "canonicalWording": "Never say it.",
                "references": ["context.pos-fact"],
                "requiresDefinedRefs": ["context.pos-fact"],
                "checks": [
                    {
                        "primitive": "term_prohibited",
                        "phase": "postflight",
                        "params": {
                            "terms": ["forbidden"],
                            "match": "case_insensitive",
                            "elementValueRef": {"elementId": "context.pos-fact", "path": "statement"},
                        },
                    }
                ],
            },
        }
    )

    manifest["elements"] = manifest["elements"] + [guidance, fact, rule]

    target = copy.deepcopy(plan["targets"][0])
    target["id"] = "pos-target"
    target["requiresDefined"] = ["structure.brand"]
    target["scope"] = {"locales": ["pos-scope-locale"]}
    target["contextAssembly"] = {"deliveryMode":"lookup", "applicationMode":"create", "noHitPolicy":"resolve_before_answer", "eligibleGuidanceIds": ["identity.pos-guidance"]}
    target["styleTexture"] = {"mode": "selected", "elementIds": ["identity.pos-guidance"]}
    target["stateMap"] = {"mode": "kinds", "kinds": ["pos-kind-fact"]}
    plan["targets"] = [target]

    return manifest, plan


def _replace_everywhere(document, needle: str, replacement: str):
    """Swap one unique identity for another, anywhere it appears."""
    if isinstance(document, dict):
        return {
            (replacement if key == needle else key): _replace_everywhere(value, needle, replacement)
            for key, value in document.items()
        }
    if isinstance(document, list):
        return [_replace_everywhere(item, needle, replacement) for item in document]
    if document == needle:
        return replacement
    return document


# --------------------------------------------------------------------------
# B1 — every identity position, every line separator
# --------------------------------------------------------------------------

def test_b1_the_enumeration_covers_every_audited_identity_position():
    """The class is 14 positions, so the enumeration must reach all of them.

    Without this, the driven test below would silently shrink with the
    enumerator it derives from, which is exactly how a class-wide defect
    survives a fix aimed at one fixture.
    """
    manifest, plan = _full_coverage_documents()
    shapes = {_shape(where) for where, _ in _manifest_identity_positions(manifest)}
    shapes |= {_shape(where) for where, _ in _plan_identity_positions(plan)}
    missing = AUDITED_POSITIONS - shapes
    assert not missing, f"identity positions not enumerated by the compiler: {sorted(missing)}"


@pytest.mark.parametrize("separator", sorted(IDENTITY_FORBIDDEN_CHARACTERS))
def test_b1_every_manifest_identity_position_refuses_every_line_separator(separator):
    manifest, _ = _full_coverage_documents()
    positions = [(where, value) for where, value in _manifest_identity_positions(manifest) if isinstance(value, str)]
    assert len(positions) >= 15, f"the manifest identity enumeration is too small: {len(positions)}"
    for where, value in positions:
        mutated = _replace_everywhere(manifest, value, f"a{separator}b")
        errors = validate_manifest(mutated, verify_hash=False)
        assert any("line separator" in error for error in errors), (
            f"{where} accepted a governed identity containing {separator!r}: {errors}"
        )


@pytest.mark.parametrize("separator", sorted(IDENTITY_FORBIDDEN_CHARACTERS))
def test_b1_every_plan_identity_position_refuses_every_line_separator(separator):
    _, plan = _full_coverage_documents()
    positions = [(where, value) for where, value in _plan_identity_positions(plan) if isinstance(value, str)]
    assert len(positions) >= 8, f"the plan identity enumeration is too small: {len(positions)}"
    for where, value in positions:
        mutated = _replace_everywhere(plan, value, f"a{separator}b")
        errors = validate_plan(mutated)
        assert any("line separator" in error for error in errors), (
            f"{where} accepted a governed identity containing {separator!r}: {errors}"
        )


# The characters that must survive: step 2 does not touch them, so two
# identities differing only there are still two identities.
IDENTITY_PRESERVED_CHARACTERS = {
    "\u0085": "U+0085 NEXT LINE",
    "\u2028": "U+2028 LINE SEPARATOR",
    "\u2029": "U+2029 PARAGRAPH SEPARATOR",
}

CA_EXAMPLES = PACKAGE_ROOT / "reference" / "context-assembly" / "examples"


def _received_artefacts():
    from obds_ref.governed_io import load_data as _load

    return (
        _load(CA_EXAMPLES / "compiled-social-copy-global-en.json"),
        _load(CA_EXAMPLES / "model-input-review.json"),
    )


def test_b1_every_governed_artefact_kind_has_an_identity_enumeration():
    """The set of governed artefacts is enumerable, or a new one has no positions.

    Class B enumerated the two artefacts the compiler *produces* and stopped. The
    two a runtime *receives* had no enumeration at all, so `manifest.id` in a
    Compiled Brand Context could carry a CR — and `a\rb` and `a\nb`, which the
    canonical form cannot tell apart, sealed to one `artifactHash` under one
    `approval.contentHash` and both ran.
    """
    expected = {
        "brand-manifest",
        "obds-build-plan",
        "obds-compiled-brand-context",
        "obds-model-input-package",
    }
    assert set(IDENTITY_POSITION_ENUMERATORS) == expected, (
        "a governed artefact kind without an identity-position enumeration has no "
        "identity positions at all: "
        f"{sorted(expected ^ set(IDENTITY_POSITION_ENUMERATORS))}"
    )
    artefact, package = _received_artefacts()
    for kind, document in (
        ("obds-compiled-brand-context", artefact),
        ("obds-model-input-package", package),
    ):
        positions = list(IDENTITY_POSITION_ENUMERATORS[kind](document))
        assert positions, f"{kind}: the enumeration finds no identity position at all"


def _leaf_paths(document, prefix=""):
    """Every scalar position in a document, as a dotted path with [] for lists."""
    if isinstance(document, dict):
        for key, value in document.items():
            yield from _leaf_paths(value, f"{prefix}.{key}" if prefix else str(key))
    elif isinstance(document, list):
        for item in document:
            yield from _leaf_paths(item, f"{prefix}[]")
    elif isinstance(document, str):
        yield prefix


def _enumerated_paths(kind, document):
    return {_shape(where) for where, value in IDENTITY_POSITION_ENUMERATORS[kind](document) if isinstance(value, str)}


def test_b1_a_shared_field_is_an_identity_position_in_every_artefact_that_carries_it():
    """One field, one answer, whichever governed artefact carries it.

    `manifest.version` was an identity position in the received-artefact
    enumeration and not in the manifest's own or the plan's. So a CR in it
    validated, compiled `ready`, produced the same `contentHash`, `planHash` and
    `artifactHash` as its LF twin, and was then refused by the runtime: two
    governed identities under one seal, with the compiler and the runtime giving
    different answers about whether they exist.

    The hand-kept oracle above could not catch that, because it was written from
    the same list as the enumerator. This is derived from the documents instead:
    it asks which positions the artefacts actually share and requires the
    enumerations to agree about them.
    """
    manifest, plan = _full_coverage_documents()
    artefact, package = _received_artefacts()
    documents = {
        "brand-manifest": manifest,
        "obds-build-plan": plan,
        "obds-compiled-brand-context": artefact,
        "obds-model-input-package": package,
    }
    # The paths that name a governed identity somewhere. Derived: a position one
    # enumerator lists is an identity position, so any other artefact carrying
    # the same path must list it too.
    claimed = set()
    for kind, document in documents.items():
        claimed |= _enumerated_paths(kind, document)

    divergent = []
    for kind, document in documents.items():
        present = {path for path in _leaf_paths(document)}
        enumerated = _enumerated_paths(kind, document)
        for path in sorted(claimed & present):
            if path not in enumerated:
                divergent.append(f"{kind}: {path}")
    assert not divergent, (
        "these positions are governed identities in one artefact and not in another, "
        "so two implementations can disagree about how many identities a document has:\n  "
        + "\n  ".join(divergent)
    )


@pytest.mark.parametrize("separator", sorted(IDENTITY_FORBIDDEN_CHARACTERS))
def test_b1_a_received_compiled_context_refuses_every_line_separator(separator):
    """Every enumerated position, driven through the runtime that receives it."""
    from obds_ref.runtime import run_with_model

    artefact, _ = _received_artefacts()
    positions = [
        (where, value)
        for where, value in compiled_context_identity_positions(artefact)
        if isinstance(value, str)
    ]
    assert len(positions) >= 10, f"the compiled context enumeration is too small: {len(positions)}"
    for where, value in positions:
        mutated = _replace_everywhere(artefact, value, f"a{separator}b")
        mutated["artifactHash"] = artefact_hash(mutated)
        calls = []
        record = run_with_model(
            mutated,
            task_input="A clean request.",
            model=lambda prompt: calls.append(prompt) or "A careful answer.",
            target_id=mutated.get("targetId"),
        )
        assert record["decision"] == "no_valid_artifact", (
            f"{where} accepted a governed identity containing {separator!r}"
        )
        assert calls == [], f"{where}: the model was called anyway"


@pytest.mark.parametrize("separator", sorted(IDENTITY_FORBIDDEN_CHARACTERS))
def test_b1_a_received_model_input_package_refuses_every_line_separator(separator):
    from obds_ref.runtime import _governed_package_errors

    _, package = _received_artefacts()
    positions = [
        (where, value)
        for where, value in model_input_package_identity_positions(package)
        if isinstance(value, str)
    ]
    assert len(positions) >= 5, f"the package identity enumeration is too small: {len(positions)}"
    for where, value in positions:
        mutated = _replace_everywhere(package, value, f"a{separator}b")
        assert _governed_package_errors(mutated), (
            f"{where} accepted a governed identity containing {separator!r}"
        )


@pytest.mark.parametrize("character", sorted(IDENTITY_PRESERVED_CHARACTERS))
def test_b1_a_received_compiled_context_preserves_the_characters_step_two_does_not_touch(character):
    """The ratified character scope is CR and LF, and no wider.

    NEL, LINE SEPARATOR and PARAGRAPH SEPARATOR survive canonicalisation, so two
    identities differing only there are two identities. Refusing them would
    narrow the accepted input space for a reason this closure does not have.
    """
    from obds_ref.runtime import run_with_model

    artefact, _ = _received_artefacts()
    mutated = dict(artefact)
    mutated["manifest"] = {**artefact["manifest"], "id": f"urn:obds:brand:a{character}b"}
    mutated["artifactHash"] = artefact_hash(mutated)
    record = run_with_model(
        mutated,
        task_input="A clean request.",
        model=lambda prompt: "A careful answer.",
        target_id=mutated.get("targetId"),
    )
    assert record["decision"] == "released", (
        f"{IDENTITY_PRESERVED_CHARACTERS[character]} was refused in a governed identity"
    )


def test_b1_the_collision_the_class_exists_for_cannot_reach_a_governed_decision():
    """`a\rb` and `a\nb` are two identities that seal to one hash. Both must fail."""
    from obds_ref.runtime import run_with_model

    artefact, _ = _received_artefacts()
    seals = {}
    for separator in ("\r", "\n"):
        mutated = dict(artefact)
        mutated["manifest"] = {**artefact["manifest"], "id": f"urn:obds:brand:a{separator}b"}
        mutated["artifactHash"] = artefact_hash(mutated)
        seals[separator] = mutated["artifactHash"]
        record = run_with_model(
            mutated,
            task_input="A clean request.",
            model=lambda prompt: "A careful answer.",
            target_id=mutated.get("targetId"),
        )
        assert record["decision"] == "no_valid_artifact", f"{separator!r} reached a governed decision"
    assert seals["\r"] == seals["\n"], (
        "the premise of this class no longer holds: the two spellings no longer collide"
    )


def _assembled_probe():
    from obds_ref.governed_io import load_data as _load

    compiled = _load(CA_EXAMPLES / "compiled-social-copy-global-en.json")
    package = copy.deepcopy(_load(CA_EXAMPLES / "model-input-create.json"))
    rendered = (CA_EXAMPLES / "rendered-input-create.txt").read_text(encoding="utf-8")
    return compiled, package, rendered


def _reseal_package(package):
    package["assemblyHash"] = sha256_id(
        {key: value for key, value in package.items() if key != "assemblyHash"}
    )
    return package


def _run_assembled(compiled, package, rendered):
    from obds_ref.runtime import run_assembled_with_model

    calls = []
    record = run_assembled_with_model(
        compiled,
        package,
        rendered,
        task_input=package["slots"]["taskInput"],
        model=lambda prompt: calls.append(prompt) or "A careful answer.",
    )
    return record["decision"], len(calls)


@pytest.mark.parametrize("field,value", [("id", "urn:obds:brand:a-different-brand"), ("version", "999.999.999")])
def test_b2_the_assembled_runtime_binds_the_whole_manifest_identity(field, value):
    """`contentHash` binds the bytes. Identity is the triple.

    A package naming a different brand at a different version, with the hash left
    untouched and its own seal recomputed, was released.
    """
    compiled, package, rendered = _assembled_probe()
    assert package["manifest"][field] != value
    package["manifest"] = {**package["manifest"], field: value}
    _reseal_package(package)
    decision, calls = _run_assembled(compiled, package, rendered)
    assert decision == "assembly_failed", f"a package declaring manifest.{field}={value!r} was {decision}"
    assert calls == 0, "the model was called on an unbound manifest identity"


def test_b2_the_assembled_runtime_still_accepts_the_matching_identity():
    """Not a wall: the untouched package still binds."""
    compiled, package, rendered = _assembled_probe()
    decision, calls = _run_assembled(compiled, package, rendered)
    assert decision == "released"
    assert calls == 1


def test_b2_target_identity_is_compared_the_way_the_assembler_compares_it():
    """Section 8.0a: `targetId` is an identity, so NFC and NFD are one identity.

    The runtime compared it as raw document bytes while Context Assembly compared
    it through `identity_key`, so the two ends of the same seam disagreed: a
    target the assembler accepted, the runtime refused.
    """
    compiled, package, rendered = _assembled_probe()
    nfc, nfd = "caf\u00e9-target", "cafe\u0301-target"
    assert identity_key(nfc) == identity_key(nfd)

    compiled = copy.deepcopy(compiled)
    compiled["targetId"] = nfc
    compiled["artifactHash"] = artefact_hash(compiled)
    package["targetId"] = nfd
    package["sources"] = {**package["sources"], "compiledContextHash": compiled["artifactHash"]}
    _reseal_package(package)

    decision, calls = _run_assembled(compiled, package, rendered)
    assert decision == "released", (
        f"a canonically equivalent targetId was refused as {decision}"
    )
    assert calls == 1


def _review_probe():
    import importlib.util
    import sys as _sys

    directory = PACKAGE_ROOT / "reference" / "context-assembly"
    if str(directory) not in _sys.path:
        _sys.path.insert(0, str(directory))
    key = "_obds_class_b_validate_review"
    if key not in _sys.modules:
        spec = importlib.util.spec_from_file_location(key, directory / "validate_review.py")
        module = importlib.util.module_from_spec(spec)
        _sys.modules[key] = module
        spec.loader.exec_module(module)
    from obds_ref.governed_io import load_data as _load

    return (
        _sys.modules[key],
        _load(directory / "examples" / "compiled-marketing-review-global-en.json"),
        copy.deepcopy(_load(directory / "examples" / "model-input-review.json")),
        copy.deepcopy(_load(directory / "examples" / "review-result-valid.json")),
    )


REVIEW_IDENTITY_SUBSTITUTIONS = [
    ("package manifest id", lambda p, r: p.__setitem__("manifest", {**p["manifest"], "id": "urn:obds:brand:another"})),
    ("package manifest version", lambda p, r: p.__setitem__("manifest", {**p["manifest"], "version": "999.999.999"})),
    ("package manifest contentHash", lambda p, r: p.__setitem__("manifest", {**p["manifest"], "contentHash": "sha256:" + "0" * 64})),
    ("package targetId", lambda p, r: p.__setitem__("targetId", "another-target")),
    ("review targetId", lambda p, r: r.__setitem__("targetId", "another-target")),
]


@pytest.mark.parametrize("name,mutate", REVIEW_IDENTITY_SUBSTITUTIONS, ids=[c[0] for c in REVIEW_IDENTITY_SUBSTITUTIONS])
def test_b2_a_review_is_bound_to_the_identities_it_claims(name, mutate):
    """Reproducing four hashes proves the documents are intact, not that they belong together.

    Nothing tied the package's and the review's governed identities to the
    artefact, so a package naming another brand, another version or another
    target validated a review about it — with every hash correctly resealed.
    """
    reviewer, compiled, package, review = _review_probe()
    mutate(package, review)
    package["assemblyHash"] = sha256_id(
        {key: value for key, value in package.items() if key != "assemblyHash"}
    )
    review["reviewHash"] = sha256_id(
        {key: value for key, value in review.items() if key != "reviewHash"}
    )
    with pytest.raises(ValueError):
        reviewer.validate_review(compiled, package, review)


def test_b2_the_matching_review_still_validates():
    """Not a wall: the untouched trio still binds."""
    reviewer, compiled, package, review = _review_probe()
    assert reviewer.validate_review(compiled, package, review) is True


def test_b1_identity_key_refuses_what_validation_refuses():
    """The backstop: no other path can build a key validation would reject."""
    for separator in IDENTITY_FORBIDDEN_CHARACTERS:
        with pytest.raises(ValueError):
            identity_key(f"context.a{separator}b")
    # NFC equality is untouched for every admissible string.
    assert identity_key("context.café") == identity_key("context.café")


def test_b1_the_rule_is_exactly_cr_and_lf_and_no_wider():
    """The class is the CR/CRLF-vs-LF collision class. Nothing else.

    CR is the character section 14.3 step 2 rewrites; LF is what it rewrites CR
    into, so LF is the collision counterpart and section 14.3's rule for keys
    refuses both sides rather than picking one.

    NEL, LINE SEPARATOR and PARAGRAPH SEPARATOR survive canonicalisation
    unchanged and no collision was ever demonstrated for them. Refusing them
    would narrow the accepted input space for a reason this closure cycle does
    not have, so this test pins them as admissible.
    """
    assert set(IDENTITY_FORBIDDEN_CHARACTERS) == {"\r", "\n"}
    for preserved in ("\u0085", "\u2028", "\u2029"):
        probe = f"context.a{preserved}b"
        assert _normalise_string(probe) == probe, (
            f"U+{ord(preserved):04X} does not survive canonicalisation after all"
        )
        assert identity_key(probe) == probe

    manifest, _ = _full_coverage_documents()
    for preserved in ("\u0085", "\u2028", "\u2029"):
        mutated = _replace_everywhere(manifest, "rules.pos-rule", f"rules.a{preserved}b")
        assert not [
            error for error in validate_manifest(mutated, verify_hash=False)
            if "line separator" in error
        ], f"U+{ord(preserved):04X} was refused in an identity position"


def test_b1_the_manifest_reference_is_an_identity_position():
    """`manifestRef.id` names the approved manifest, so it is compared as one.

    An independent review found it missing from both the enumeration and the
    audited list, so `obds validate` called such a plan valid and the build then
    raised out of `identity_key` instead of reporting an invalid document. The
    oracle and the implementation were incomplete in the same way, which is why
    the sweep could not catch it.
    """
    _, plan = example("foundation-minimal")
    assert "manifestRef.id" in {where for where, _ in _plan_identity_positions(plan)}
    for separator in ("\r", "\n"):
        mutated = copy.deepcopy(plan)
        mutated["manifestRef"]["id"] = mutated["manifestRef"]["id"] + separator + "x"
        errors = validate_plan(mutated)
        assert any("manifestRef.id" in error and "line separator" in error for error in errors), errors


@pytest.mark.parametrize("package", ["context-assembly", "context-delivery"])
@pytest.mark.parametrize("separator", ["\r", "\n"])
def test_b1_the_view_builders_apply_the_identity_rule(package, separator):
    """Class B reaches every path that emits a governed identity, not only validation.

    Both view builders emitted `manifest["id"]` raw, so two manifests differing
    only CR-vs-LF shared one `approval.contentHash`, one `indexHash` and one
    `chapterSetHash` while the views declared two different governed identities.
    The Class B tests drove `validate_manifest`, `validate_plan` and
    `identity_key`; they never drove `build_views`.
    """
    import copy
    import importlib.util
    import sys

    root = PACKAGE_ROOT / "reference" / package
    spec = importlib.util.spec_from_file_location(
        f"b1_build_views_{package.replace('-', '_')}", root / "build_views.py"
    )
    module = importlib.util.module_from_spec(spec)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    spec.loader.exec_module(module)

    manifest = copy.deepcopy(load_data(root / "examples" / "manifest.yaml"))
    chapter_map = load_data(root / "examples" / "chapter-map.yaml")

    # The honest corpus still builds.
    module.build_views(copy.deepcopy(manifest), chapter_map)

    manifest["id"] = f"urn:obds:brand:a{separator}b"
    manifest["approval"]["contentHash"] = manifest_content_hash(manifest)
    with pytest.raises(ValueError):
        module.build_views(manifest, chapter_map)


@pytest.mark.parametrize("package", ["context-assembly", "context-delivery"])
def test_b2_a_derived_view_refuses_a_stale_approval_hash(package):
    """A view publishes `approval.contentHash` as a claim, so it must reproduce it.

    The builders copied it. So a manifest could be edited after approval and its
    Search Cards still published under the old hash: two different governed
    identity sets, one claimed approved manifest — the Class B invariant, reached
    through the view builders rather than through validation.
    """
    import copy
    import importlib.util
    import sys

    root = PACKAGE_ROOT / "reference" / package
    spec = importlib.util.spec_from_file_location(
        f"b2_build_views_{package.replace('-', '_')}", root / "build_views.py"
    )
    module = importlib.util.module_from_spec(spec)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    spec.loader.exec_module(module)

    manifest = copy.deepcopy(load_data(root / "examples" / "manifest.yaml"))
    chapter_map = load_data(root / "examples" / "chapter-map.yaml")
    declared = manifest["approval"]["contentHash"]

    # Sealed: builds.
    module.build_views(copy.deepcopy(manifest), chapter_map)

    # Edited after approval, hash left alone: refused.
    manifest["elements"][0]["id"] = "structure.changed-after-approval"
    assert manifest["approval"]["contentHash"] == declared
    with pytest.raises(ValueError) as caught:
        module.build_views(manifest, chapter_map)
    assert "approval contentHash" in str(caught.value)


def test_b2_a_resolution_snapshot_must_reproduce_its_approval_hash():
    """The one runtime path that reads the manifest reconstructs an approved object.

    `manifest_checked` compared the snapshot's *declared* `approval.contentHash`
    against the compiled context. A snapshot carrying a different governed
    identity set can declare that value too, simply by copying it — so the
    comparison proved only that the snapshot said the right thing.
    """
    import copy
    import importlib.util
    import sys

    root = PACKAGE_ROOT / "reference" / "context-assembly"
    spec = importlib.util.spec_from_file_location("b2_assembler", root / "assemble_context.py")
    assembler = importlib.util.module_from_spec(spec)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    spec.loader.exec_module(assembler)

    compiled = load_data(root / "examples" / "compiled-brand-query-global-en.json")
    snapshot = copy.deepcopy(load_data(root / "examples" / "manifest.yaml"))

    # The honest snapshot passes.
    assembler._validate_resolution_manifest(
        compiled, {"resolution": "manifest_checked"}, snapshot
    )

    # A different identity set, wearing the expected hash, does not.
    forged = copy.deepcopy(snapshot)
    forged["elements"][0]["id"] = "different.governed.identity"
    forged["approval"]["contentHash"] = compiled["manifest"]["contentHash"]
    assert manifest_content_hash(forged) != forged["approval"]["contentHash"]
    with pytest.raises(ValueError) as caught:
        assembler._validate_resolution_manifest(
            compiled, {"resolution": "manifest_checked"}, forged
        )
    assert "reproduce its approval contentHash" in str(caught.value)


def test_b1_the_shipped_corpus_is_unaffected():
    """Measured impact of the identity character rule: zero."""
    for name in _all_examples():
        manifest, plan = example(name)
        assert not [
            error for error in validate_manifest(manifest, verify_hash=False) if "line separator" in error
        ]
        assert not [error for error in validate_plan(plan) if "line separator" in error]


# --------------------------------------------------------------------------
# B2 — the universal property
# --------------------------------------------------------------------------

def _canonical_round_trip(document):
    """The document as re-read from its own section 14.3 canonical bytes."""
    return json.loads(canonical_json_bytes(document).decode("utf-8"))


def _governed(report):
    """A build report minus the one field that is packaging, not governance."""
    report = dict(report)
    report.pop("builtAt", None)
    report.pop("reportHash", None)
    return report


@pytest.mark.parametrize("name", _all_examples())
def test_b2_a_document_and_its_own_canonical_form_agree(name):
    """A document and its canonical form must agree on validity and on hashes.

    The decisive 2.0.0 artefact was a manifest that validated clean, whose own
    canonical form validation rejects as a duplicate, with `contentHash`
    unchanged either way. Stated as a property, three of seven probes broke it.
    """
    manifest, plan = example(name)
    for document in (manifest, plan):
        assert sha256_id(document) == sha256_id(_canonical_round_trip(document))

    assert validate_manifest(manifest, verify_hash=False) == validate_manifest(
        _canonical_round_trip(manifest), verify_hash=False
    )
    assert validate_plan(plan) == validate_plan(_canonical_round_trip(plan))
    assert manifest_content_hash(manifest) == manifest_content_hash(_canonical_round_trip(manifest))


@pytest.mark.parametrize("name", _all_examples())
def test_b2_the_governed_build_agrees_with_its_own_canonical_form(name):
    """Same approval, same governed result, through every hash in the build."""
    manifest, plan = example(name)
    direct = _governed(build_all(manifest, plan))
    mirrored = _governed(build_all(_canonical_round_trip(manifest), _canonical_round_trip(plan)))
    assert sha256_id(direct) == sha256_id(mirrored), (
        "a document and its own canonical form produced different governed results"
    )


def test_b2_one_content_hash_cannot_resolve_to_two_governed_identities():
    """The class invariant, driven by the decisive artefact.

    Two elements differing only CR-vs-LF shared one `contentHash`, validated
    clean, and produced two different included-element sets. The canonical form
    of that manifest declares one element where the source declared two.
    """
    manifest, _ = example("foundation-minimal")
    template = copy.deepcopy(manifest["elements"][0])
    broad = copy.deepcopy(template)
    broad["id"] = "context.a\rb"
    narrow = copy.deepcopy(template)
    narrow["id"] = "context.a\nb"
    manifest["elements"] = [manifest["elements"][0], broad, narrow]

    errors = validate_manifest(manifest, verify_hash=False)
    assert errors, "the decisive artefact still validates clean"
    assert all("line separator" in error for error in errors), errors

    mirror = _canonical_round_trip(manifest)
    assert len(mirror["elements"]) == 3
    assert len({element["id"] for element in mirror["elements"]}) == 2, (
        "the canonical form did not collapse the two identities, so this "
        "fixture no longer reproduces the class"
    )
