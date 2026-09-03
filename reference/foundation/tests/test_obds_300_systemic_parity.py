"""Systemic mechanism 3 — a primitive implemented twice must not mean two things.

Five of the nineteen defects eleven review rounds produced had one shape: a
ratified semantic primitive was implemented more than once and the copies drifted.
The JavaScript reader deduplicated keys on NFC while Python used the canonical
comparison. It asked whether an integer was *safe* while Python asked whether it
was exactly representable. It lost a `__proto__` key to a prototype setter. It
repaired malformed UTF-8 that Python refuses. And `word_boundary_ci` declared one
Unicode version while its engine implemented another.

Each was found by someone thinking of that specific case. This closes the shape:
one normative vector set, executed against every implementation the registry
names, with the same governed result required from all of them. A vector nobody
thought of is covered as soon as it is added once, in one place.

The vectors are generated rather than listed where generation is honest — a
grammar over section 28.1's own decision points produces cases no one enumerated,
and the two readers still have to agree about every one.
"""

from __future__ import annotations

import copy
import itertools
import json
import random
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from obds_ref.canonical import canonical_json_bytes
from obds_ref.checks import (
    DEFAULT_IGNORABLE_CODE_POINTS,
    WHITESPACE_CODE_POINTS,
    WORD_SEGMENTATION_UNICODE_VERSION,
    _contains,
    execute_checks,
    validate_check,
)
from obds_ref.compiler import ValidationFailure, load_data
from systemic_surface import (
    BYTE_IDENTICAL_COPIES,
    COMPILED_CONTEXT_CONSUMERS,
    CONTRACT_VERSION_CONSUMERS,
    CONTRACT_VERSION_MODULES,
    HASH_CALL_SITES,
    PACKAGE_ROOT,
    PUBLISHED_3_0_CONTRACTS,
    REFERENCE,
    SEMANTIC_PRIMITIVE_IMPLEMENTATIONS,
)

JS_HARNESS = REFERENCE / "adversarial" / "canonical_js.mjs"


def _release() -> str:
    """The release this package is, read from the specification it ships."""
    import re as _release_re

    names = sorted(
        path.name for path in PACKAGE_ROOT.glob("OBDS-*.md")
        if _release_re.fullmatch(r"OBDS-\d+\.\d+\.\d+\.md", path.name)
    )
    assert len(names) == 1, f"expected one normative specification, found {names}"
    return names[0][len("OBDS-"):-len(".md")]


def _node():
    node = shutil.which("node")
    if node is None:  # pragma: no cover - the JS suite is skipped without node
        pytest.skip("node is not available")
    return node


# --------------------------------------------------------------------------
# Enumeration guards
# --------------------------------------------------------------------------

def test_every_duplicated_primitive_is_registered():
    """A primitive implemented twice without an entry escapes this mechanism."""
    for name, entry in SEMANTIC_PRIMITIVE_IMPLEMENTATIONS.items():
        assert entry["implementations"], name
        assert entry["authoritative"], name
        assert entry["note"], f"{name}: an entry without a reason is not a decision"
        for relative in entry["implementations"]:
            assert (PACKAGE_ROOT / relative).is_file(), f"{name}: {relative}"
        assert (PACKAGE_ROOT / entry["authoritative"]).is_file(), name


def test_the_byte_identical_copies_are_byte_identical():
    """One spelling of a shared contract, or it is two contracts."""
    import hashlib

    for name, paths in BYTE_IDENTICAL_COPIES.items():
        digests = {
            hashlib.sha256((PACKAGE_ROOT / relative).read_bytes()).hexdigest(): relative
            for relative in paths
        }
        assert len(digests) == 1, f"{name} has diverged: {sorted(digests.values())}"


def test_the_registry_and_the_release_gate_pin_the_same_copies():
    """Two lists of the same thing are two chances to be wrong about it."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("parity_gate", REFERENCE / "release-gate.py")
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    assert {
        name: sorted(paths) for name, paths in gate.GOVERNED_CONTRACT_COPIES.items()
    } == {
        name: sorted(paths) for name, paths in BYTE_IDENTICAL_COPIES.items()
    }


def _load(name, path):
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _published_contract_files():
    """Every published contract file, found by looking rather than by asking.

    Deliberately independent of the discovery the release tooling uses: a test
    that derives the surface the same way the code does cannot notice the code
    deriving it wrongly.
    """
    found = []
    for family in ("schemas", "value-schemas"):
        base = PACKAGE_ROOT / family
        if not base.is_dir():
            continue
        for directory in sorted(base.iterdir()):
            if not directory.is_dir():
                continue
            parts = directory.name.split(".")
            if len(parts) != 3 or not all(part.isdigit() for part in parts):
                continue
            for path in sorted(directory.glob("*.json")):
                found.append((f"{family}/{directory.name}", path))
    return found


def test_every_published_contract_directory_reaches_the_release_package():
    """A contract in the repository and not in the archive is a published 404.

    The package builder and the release gate each kept their own list of contract
    directories. Both stopped at 1.1.0. `schemas/3.0.0/` and
    `value-schemas/3.0.0/` existed and would have been left out of the archive,
    and the gate, reading the other copy of the same stale list, could not have
    said so. This asserts the outcome rather than the mechanism, so a future
    `4.0.0/` cannot fall out either.
    """
    builder = _load("parity_builder", PACKAGE_ROOT / "tools" / "build-release.py")
    published = _published_contract_files()
    assert published, "no published contract directory was found at all"

    packaged = {path for _, path in builder.package_files(_release())}
    missing = sorted(
        str(path.relative_to(PACKAGE_ROOT)) for _, path in published if path not in packaged
    )
    assert not missing, "published contracts left out of the release package: " + ", ".join(missing)


def test_the_release_gate_inventories_every_published_contract():
    """The gate cannot check a surface it does not know it serves."""
    gate = _load("parity_gate_contracts", REFERENCE / "release-gate.py")
    inventoried = {
        path
        for directory, _, _ in gate.contract_directories()
        for path in directory.glob("*.json")
    }
    missing = sorted(
        str(path.relative_to(PACKAGE_ROOT))
        for _, path in _published_contract_files()
        if path not in inventoried
    )
    assert not missing, "published contracts outside the release-gate inventory: " + ", ".join(missing)


RELEASE_TOOLING_READERS = (
    ("tools/build-release.py", "parity_builder_reader"),
    ("tools/docs-smoke-test.py", "parity_smoke_reader"),
)


@pytest.mark.parametrize("relative,module_name", RELEASE_TOOLING_READERS, ids=[r[0] for r in RELEASE_TOOLING_READERS])
def test_release_tooling_reads_governed_release_evidence_under_the_governed_contract(
    tmp_path, relative, module_name
):
    """The tools that produce and check the release are governed readers too.

    `publication-record.json` says what the release contains. The release gate
    read it under section 28.1 and refused a duplicated key; the build script
    read it with `json.loads`, took the last one silently, and then wrote the
    file back. Two readers, one file, and the permissive one held the pen.
    """
    module = _load(module_name, PACKAGE_ROOT / relative)
    assert hasattr(module, "load"), f"{relative} has no governed reader"

    duplicated = tmp_path / "publication-record.json"
    duplicated.write_text(
        '{"currentRelease": "3.0.0", "releases": {"3.0.0": {"note": "a"}}, '
        '"releases": {"3.0.0": {"note": "b"}}}',
        encoding="utf-8",
    )
    with pytest.raises(ValidationFailure):
        module.load(duplicated)

    # Not vacuous: the same reader reads a real governed release document. It
    # reads the package manifest rather than `publication-record.json`, which is
    # website material and is not in the archive: from 3.0.1 the tooling is
    # packaged, so a test that reads a repository-only file passes in the
    # repository and fails in the package it is shipped inside.
    manifest = module.load(PACKAGE_ROOT / "PACKAGE-MANIFEST.json")
    assert isinstance(manifest, dict) and "files" in manifest


def test_every_path_the_surface_registries_name_reaches_the_release_package():
    """A file the suite reads has to be in the package the suite is run against.

    The 3.0.0 archive omitted `tools/`. The surface registries name
    `tools/build-release.py` and `tools/docs-smoke-test.py`, which in the
    repository is correct: the packager computes governed hashes and resolves
    contract paths, so it is part of the surface. In the unpacked archive the
    files were absent, eight enumeration guards refused a release the repository
    had passed, and the two commands the release documents for the archive layout
    did not run.

    Nothing caught it. The release gate and the suite both run in the repository,
    where the files exist, and only the post-deployment docs smoke test unpacks
    the archive. So the invariant is asserted here, where it is cheap: every path
    a registry names is a path the packager ships.
    """
    builder = _load("parity_builder_surface", PACKAGE_ROOT / "tools" / "build-release.py")
    packaged = {path for _, path in builder.package_files(_release())}

    named: set[str] = set()
    for key in HASH_CALL_SITES:
        named.add(key.split("::", 1)[0])
    for key in COMPILED_CONTEXT_CONSUMERS:
        named.add(key.split("::", 1)[0])
    for key in CONTRACT_VERSION_CONSUMERS:
        named.add(key.split("::", 1)[0])
    named.update(CONTRACT_VERSION_MODULES)
    named.update(PUBLISHED_3_0_CONTRACTS)
    for primitive in SEMANTIC_PRIMITIVE_IMPLEMENTATIONS.values():
        named.add(primitive["authoritative"])
        named.update(primitive["implementations"])
    for copies in BYTE_IDENTICAL_COPIES.values():
        named.update(copies)

    missing = sorted(
        relative for relative in named
        if (PACKAGE_ROOT / relative).is_file() and (PACKAGE_ROOT / relative) not in packaged
    )
    assert not missing, (
        "these files are named by a surface registry and would not be in the release "
        "archive, so the archive cannot run the suite it was verified with:\n  "
        + "\n  ".join(missing)
    )


def test_the_package_builder_and_the_release_gate_share_one_contract_list():
    """One definition. Two copies of a list are two chances to be wrong about it."""
    builder = _load("parity_builder_shared", PACKAGE_ROOT / "tools" / "build-release.py")
    gate = _load("parity_gate_shared", REFERENCE / "release-gate.py")
    assert builder.schema_dirs() == {
        directory.relative_to(PACKAGE_ROOT).as_posix(): archive
        for directory, _, archive in gate.contract_directories()
    }


# --------------------------------------------------------------------------
# The normative vector set for governed JSON reading.
#
# Half enumerated, half generated. The enumerated half carries the cases the
# reviews found, so they can never regress. The generated half exists because
# every one of those cases was found by someone thinking of it, and thinking of
# cases does not scale.
# --------------------------------------------------------------------------

ENUMERATED_READER_VECTORS = {
    "plain": '{"kind":"probe","value":1}',
    "duplicate-key": '{"kind":"probe","value":1,"value":2}',
    "duplicate-key-nfc": '{"kind":"probe","caf\\u00e9":1,"cafe\\u0301":2}',
    "duplicate-key-after-fold": r'{"kind":"probe","a\rb":1,"a\nb":2}',
    "proto-key": '{"kind":"probe","__proto__":{"polluted":true}}',
    "constructor-key": '{"kind":"probe","constructor":"x"}',
    "exactly-representable-2-53": '{"kind":"probe","value":9007199254740992}',
    "not-exactly-representable": '{"kind":"probe","value":9007199254740993}',
    "overflow-to-infinity": '{"kind":"probe","value":1e400}',
    "underflow": '{"kind":"probe","value":1e-400}',
    "negative-zero": '{"kind":"probe","value":-0}',
    "nan-literal": '{"kind":"probe","value":NaN}',
    "infinity-literal": '{"kind":"probe","value":Infinity}',
    "leading-zero": '{"kind":"probe","value":017}',
    "plus-sign": '{"kind":"probe","value":+1}',
    "hex": '{"kind":"probe","value":0x1F}',
    "trailing-comma": '{"kind":"probe","value":1,}',
    "single-quotes": "{'kind':'probe'}",
    "sequence-root": '[{"kind":"probe"}]',
    "scalar-root": '"probe"',
    "trailing-content": '{"kind":"probe"} {"kind":"probe"}',
    "escaped-surrogate-pair": r'{"kind":"probe","value":"😀"}',
    "lone-escaped-surrogate": r'{"kind":"probe","value":"\ud83d"}',
    "escaped-solidus": r'{"kind":"probe","value":"a\/b"}',
    "deep": '{"kind":"probe","value":' + "[" * 140 + "null" + "]" * 140 + "}",
    "empty-object": "{}",
    "empty-key": '{"":1,"kind":"probe"}',
}


def _generated_reader_vectors(count=120, seed=20260902):
    """A grammar over section 28.1's decision points, not over JSON at large.

    Every fragment below is a place the two readers could disagree: a number
    spelling, an escape, a key that means something to one language, a nesting or
    duplication. Random combination reaches pairs nobody would write down.
    """
    keys = ['"kind"', '"value"', '"a"', '"__proto__"', '"constructor"', '"toString"',
            '"caf\\u00e9"', '"cafe\\u0301"', r'"a\rb"', r'"a\nb"', '""', '"0"']
    scalars = ["1", "-1", "0", "-0", "1.5", "1e3", "1E3", "1e-3",
               "9007199254740992", "9007199254740993", "1e308", "1e400", "1e-400",
               '"text"', '"\\u00e9"', '"e\\u0301"', r'"a\/b"', r'"😀"',
               "true", "false", "null", "[]", "{}", "[1,2]", '{"n":1}']
    generator = random.Random(seed)
    vectors = {}
    for index in range(count):
        pairs = []
        for _ in range(generator.randint(1, 4)):
            pairs.append(f"{generator.choice(keys)}:{generator.choice(scalars)}")
        body = "{" + ",".join(pairs) + "}"
        if generator.random() < 0.25:
            body = "{" + f'"outer":{body}' + "}"
        vectors[f"generated-{index:03d}"] = body
    return vectors


READER_VECTORS = {**ENUMERATED_READER_VECTORS, **_generated_reader_vectors()}


def _python_reads(text, tmp_path, name):
    path = tmp_path / f"{name}.json"
    path.write_text(text, encoding="utf-8")
    try:
        return canonical_json_bytes(load_data(path)).decode("utf-8")
    except (ValidationFailure, ValueError, TypeError):
        return None


def _javascript_reads(text, tmp_path, name, mode="--read"):
    path = tmp_path / f"{name}.json"
    path.write_text(text, encoding="utf-8")
    completed = subprocess.run(
        [_node(), str(JS_HARNESS), mode, str(path)], capture_output=True, text=True
    )
    if completed.returncode != 0:
        return None
    return bytes.fromhex(completed.stdout.strip()).decode("utf-8")


def _python_parses(text, tmp_path, name):
    """The reader stage alone, matched against the harness's reader stage.

    `read_governed_document` plus the root-object rule, which is exactly what
    `loadGovernedData` is on the JavaScript side. Using `load_data` here would
    compare Python's parser *plus* canonical admissibility against JavaScript's
    parser alone, and report an asymmetry the test itself created.
    """
    from obds_ref.governed_io import read_governed_document

    path = tmp_path / f"{name}.json"
    path.write_text(text, encoding="utf-8")
    try:
        document = read_governed_document(path)
    except (ValidationFailure, ValueError, TypeError):
        return None
    if not isinstance(document, dict):
        return None
    return _stable(document)


def _stable(value):
    """A comparable serialisation of a *parsed* value, across two languages.

    Numbers go through the project's own canonical token, because JSON has one
    number type and the two host languages do not: Python distinguishes `1000`
    from `1000.0` and JavaScript does not. Comparing host spellings would report
    a divergence that the contract does not have.
    """
    from obds_ref.canonical import _number_token

    if isinstance(value, bool) or value is None:
        return json.dumps(value)
    if isinstance(value, (int, float)):
        return _number_token(value)
    if isinstance(value, str):
        # ASCII-escaped on both sides, so the comparison is about the value the
        # readers produced and not about how each host language prints it. A lone
        # surrogate prints two different ways and is one parsed value.
        return json.dumps(value)
    if isinstance(value, list):
        return "[" + ",".join(_stable(item) for item in value) + "]"
    keys = sorted(value)
    return "{" + ",".join(json.dumps(k) + ":" + _stable(value[k]) for k in keys) + "}"


@pytest.mark.parametrize("name", sorted(READER_VECTORS))
def test_mechanism_3_every_reader_agrees_on_every_vector(tmp_path, name):
    """One vector set, every implementation, the same governed result.

    Same canonical form, or the same refusal. Nothing in between: "accepted with
    a different value" and "accepted where the other refuses" are the two ways
    two implementations of one contract stop being one contract.
    """
    text = READER_VECTORS[name]

    # Stage one: the reader. Measured on its own, because canonicalisation has
    # its own duplicate-key check and a later stage agreeing can mask an earlier
    # stage diverging — which is exactly how one reader-level difference survived
    # a comparison that only looked at canonical forms.
    python_parse = _python_parses(text, tmp_path, name)
    javascript_parse = _javascript_reads(text, tmp_path, name, mode="--read-parse")
    assert (python_parse is None) == (javascript_parse is None), (
        f"{name}: the readers disagree about whether this is governable — python "
        f"{'refused' if python_parse is None else 'accepted'}, javascript "
        f"{'refused' if javascript_parse is None else 'accepted'} — {text[:80]}"
    )
    if python_parse is not None:
        assert python_parse == javascript_parse, (
            f"{name}: the readers produced different values for {text[:80]}"
        )

    # Stage two: canonicalisation of what the readers produced.
    python = _python_reads(text, tmp_path, name)
    javascript = _javascript_reads(text, tmp_path, name)
    assert (python is None) == (javascript is None), (
        f"{name}: python {'refused' if python is None else 'accepted'}, "
        f"javascript {'refused' if javascript is None else 'accepted'} — {text[:80]}"
    )
    if python is not None:
        assert python == javascript, f"{name}: different canonical forms for {text[:80]}"


def test_mechanism_3_the_vector_set_reaches_both_outcomes():
    """A vector set everything refuses proves as little as one nothing refuses."""
    import tempfile

    directory = Path(tempfile.mkdtemp())
    try:
        accepted = refused = 0
        for name, text in READER_VECTORS.items():
            if _python_reads(text, directory, name) is None:
                refused += 1
            else:
                accepted += 1
        assert accepted >= 20, f"only {accepted} vectors are governable"
        assert refused >= 10, f"only {refused} vectors are refused"
    finally:
        shutil.rmtree(directory)


# --------------------------------------------------------------------------
# Unicode integrity: the declared contract, the fixtures and the executed
# behaviour must be the same thing.
# --------------------------------------------------------------------------

def test_mechanism_3_the_declared_unicode_contract_is_the_executed_one():
    """Not a stamped version string.

    `word_boundary_ci` declared 15.1.0 because section 14.3c pins 15.1.0 for
    canonicalisation, while its engine implemented 17.0.0 — and Unicode 17 moved
    U+00B8 CEDILLA to `Word_Break=ALetter`, so the declaration and the behaviour
    disagreed about a real string. The version is now read from the engine, and
    this proves the reading is true.
    """
    import importlib.metadata

    metadata = importlib.metadata.distribution("regex").read_text("METADATA") or ""
    assert f"supports Unicode {WORD_SEGMENTATION_UNICODE_VERSION}" in metadata

    requirements = (PACKAGE_ROOT / "requirements.txt").read_text(encoding="utf-8")
    regex_line = next(line for line in requirements.splitlines() if line.startswith("regex"))
    assert "==" in regex_line, regex_line


def test_mechanism_3_the_word_boundary_fixtures_are_the_executed_behaviour():
    """Every normative fixture, executed. The fixtures are the contract."""
    fixtures = load_data(REFERENCE / "foundation" / "fixtures" / "word-boundary-ci.json")
    assert fixtures["unicodeVersion"] == WORD_SEGMENTATION_UNICODE_VERSION
    assert len(fixtures["cases"]) >= 20, "the fixture set is too small to pin a segmentation engine"
    for case in fixtures["cases"]:
        assert _contains(case["text"], case["term"], "word_boundary_ci") is case["matches"], case


def test_mechanism_3_a_host_unicode_difference_cannot_reach_a_governed_outcome():
    """The pin is what makes the host database irrelevant, so prove it does.

    Every code point that differs between the canonicalisation pin and any later
    database is unassigned in the pin, so it is refused before normalisation. A
    text a governed check evaluates therefore contains only code points every
    conforming host agrees about.
    """
    from obds_ref.canonical import UNICODE_PIN_VERSION, _assigned_in_pinned_unicode
    from obds_ref.checks import UnicodeAdmissibilityError, assert_check_input_admissible

    assert UNICODE_PIN_VERSION == "15.1.0"
    # Code points the host database knows and the pin does not — one of them,
    # U+0897, is among the twelve that gained a non-zero combining class after
    # 15.1.0, which is the case that made NFC host-dependent.
    for code_point in (0x0897, 0x1B4E, 0x1C89):
        assert not _assigned_in_pinned_unicode(code_point), hex(code_point)
        with pytest.raises(UnicodeAdmissibilityError):
            assert_check_input_admissible("probe" + chr(code_point), where="parity probe")

    # And the whole pinned separator and ignorable vocabulary is admissible, so
    # the refusal above is about the pin and not about a coincidence.
    for character in sorted(WHITESPACE_CODE_POINTS | DEFAULT_IGNORABLE_CODE_POINTS):
        if character == "\r":
            continue  # section 14.3 folds it; refused for its own stated reason
        assert_check_input_admissible(f"a{character}b", where="parity probe")


# --------------------------------------------------------------------------
# Match modes: one vector set, executed through both the authoring validator and
# the compiled executor, so the two cannot mean different things either.
# --------------------------------------------------------------------------

MATCH_VECTORS = [
    ("exact", "the best", "We are the best.", True),
    ("exact", "the best", "We are The Best.", False),
    ("case_insensitive", "the best", "We are The Best.", True),
    ("case_insensitive", "the best", "We are The  Best.", False),
    ("normalized_whitespace_ci", "the best", "We are The  Best.", True),
    ("normalized_whitespace_ci", "the best", "We are The Best.", True),
    ("normalized_whitespace_ci", "secret", "the sec​ret", True),
    ("normalized_whitespace_ci", "secret", "the sec­ret", True),
    ("case_insensitive", "secret", "the sec​ret", False),
    ("word_boundary_ci", "cheap", "Buy cheap now.", True),
    ("word_boundary_ci", "cheap", "cheaper than ever", False),
]


@pytest.mark.parametrize("match,term,text,expected", MATCH_VECTORS)
def test_mechanism_3_a_match_mode_means_one_thing_everywhere(match, term, text, expected):
    """The primitive, the authoring validator and the compiled executor agree.

    `_contains` is the primitive; `validate_check` decides whether a check may be
    written; `execute_checks` decides what a compiled check does. A mode that
    means one thing in the first and another in the third is the same drift as
    two languages disagreeing.
    """
    assert _contains(text, term, match) is expected

    check = {
        "ruleElementId": "rules.parity",
        "primitive": "term_prohibited",
        "phase": "postflight",
        "enforcement": "block",
        "params": {"terms": [term], "match": match, "appliesTo": "output"},
    }
    assert validate_check(check) == []
    finding = execute_checks([check], phase="postflight", text=text)[0]
    assert finding.passed is (not expected), (match, term, text)
