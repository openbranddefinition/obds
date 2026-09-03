"""OBDS 3.0.0 Class A — one governed interchange contract.

The 2.0.0 release shipped four different governed input contracts across eight
readers, of which one conformed. Nothing detected it, because all 29 shipped
governed documents happened to read identically under all four: the release was
internally consistent by accident of its data rather than by construction.

These tests close the class rather than the call sites. They enumerate the
governed readers, drive them over a corpus built from the forms the four
contracts disagreed about, and require that every reader either produces the
same value or refuses. A new reader that carries its own approximation of
section 28.1 fails A1 and A2 the moment it is added.

Each test is negative: disabling the mechanism it names turns the suite red.
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from obds_ref import governed_io
from obds_ref.canonical import canonical_json_bytes, sha256_id
from obds_ref.compiler import ValidationFailure, load_data, validate_manifest
from obds_ref.governed_io import MAX_NESTING_DEPTH, read_governed_document, read_governed_text

TESTS = Path(__file__).resolve().parent
FOUNDATION = TESTS.parent
REFERENCE = FOUNDATION.parent
PACKAGE_ROOT = REFERENCE.parent

# Every directory in the release that carries its own flat copy of the governed
# contract. `canonical.py` and `governed_io.py` are copied rather than shared
# because these packages are executed flat, not imported as packages; the
# release gate pins the copies byte-identical.
FLAT_PACKAGES = ("context-assembly", "context-delivery", "design-space")


# --------------------------------------------------------------------------
# The corpus. Every entry is a scalar the four 2.0.0 contracts disagreed about.
# --------------------------------------------------------------------------

AMBIGUOUS_SCALARS = [
    "017", "0o17", "0x1F", "0b101", "1_000",
    "12:30", "00:00", "1:2:3",
    "yes", "no", "on", "off", "y", "n",
    "true", "false", "True", "FALSE",
    "null", "Null", "NULL", "~",
    "1e3", "1.0e+3", ".5", "5.", "-0",
    ".inf", "-.inf", ".nan", ".Inf", ".NaN",
    "2026-09-02", "2026-09-02T00:00:00Z",
    "=", "!ruby/object", "<<",
]


def _yaml_doc(scalar: str) -> str:
    return f"kind: probe\nvalue: {scalar}\n"


# The governed reader surface, enumerated exactly. Not a lower bound: A1 compares
# this set for equality, so a reader that disappears fails the test and a reader
# added without an entry here fails it too. "At least five readers conform" is
# the shape of assertion that let four contracts ship as one.
EXPECTED_GOVERNED_READERS = {
    "governed_io.load_data",
    "governed_io.read_governed_document",
    "compiler.load_data",
    "cli._load_conformance_fixture",
    "context-assembly/build_views.load",
    "context-delivery/build_views.load",
    "release-gate.load",
}

# The release ships a second implementation of the contract, in another runtime.
# Class A applies to it, but it is out-of-process and JSON-only, so it is driven
# as its own A2 comparison rather than folded into the in-process registry.
JAVASCRIPT_READER = "reference/adversarial/canonical_js.mjs --read"


def _governed_readers():
    """Every entry point in the release that turns bytes into a governed value.

    Listed by import rather than by grep so the list cannot silently rot: if a
    module stops exporting its reader, this collection fails.
    """
    from obds_ref import cli as obds_cli

    readers = {
        "governed_io.load_data": governed_io.load_data,
        "governed_io.read_governed_document": governed_io.read_governed_document,
        "compiler.load_data": load_data,
        "cli._load_conformance_fixture": obds_cli._load_conformance_fixture,
    }
    for package in FLAT_PACKAGES:
        directory = REFERENCE / package
        if not (directory / "build_views.py").is_file():
            continue
        readers[f"{package}/build_views.load"] = _import_flat(directory, "build_views").load
    gate = _import_gate()
    readers["release-gate.load"] = gate.load
    return readers


def _javascript_reader(path):
    """The shipped second implementation, driven as a reader.

    It reads JSON only, so a YAML probe is refused here and A2's YAML corpus
    excludes it — a JSON reader refusing YAML is not a disagreement about a
    governed value. What it must agree about is every JSON document: the same
    canonical bytes, or the same refusal.
    """
    import shutil
    import subprocess

    node = shutil.which("node")
    if node is None:  # pragma: no cover - the JS suite is skipped without node
        pytest.skip("node is not available")
    harness = REFERENCE / "adversarial" / "canonical_js.mjs"
    completed = subprocess.run(
        [node, str(harness), "--read", str(path)], capture_output=True, text=True
    )
    if completed.returncode != 0:
        raise ValidationFailure([f"{path}: {completed.stderr.strip().splitlines()[-1]}"])
    return bytes.fromhex(completed.stdout.strip()).decode("utf-8")


def _import_flat(directory: Path, name: str):
    import importlib.util

    key = f"_obds_flat_{directory.name.replace('-', '_')}_{name}"
    if key in sys.modules:
        return sys.modules[key]
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
    spec = importlib.util.spec_from_file_location(key, directory / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


def _import_gate():
    import importlib.util

    key = "_obds_release_gate"
    if key in sys.modules:
        return sys.modules[key]
    spec = importlib.util.spec_from_file_location(key, REFERENCE / "release-gate.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


def _read(reader, path):
    """Normalise every reader's refusal to one exception type for comparison."""
    try:
        return ("ok", reader(path))
    except Exception as exc:  # noqa: BLE001 - a refusal is a refusal
        return ("refused", type(exc).__name__)


# --------------------------------------------------------------------------
# A1 — the reader registry
# --------------------------------------------------------------------------

def test_a1_every_governed_reader_is_the_one_governed_reader(tmp_path):
    """Section 28.1: one contract, so one implementation of it.

    Behavioural agreement is asserted by A2. This test asserts the stronger
    property that makes A2 impossible to regress: no reader carries its own
    parsing code at all. Before 3.0.0 five of them did.
    """
    readers = _governed_readers()
    assert set(readers) == EXPECTED_GOVERNED_READERS, (
        "the governed reader surface changed: "
        f"missing {sorted(EXPECTED_GOVERNED_READERS - set(readers))}, "
        f"unexpected {sorted(set(readers) - EXPECTED_GOVERNED_READERS)}"
    )
    for name, reader in readers.items():
        source = getattr(reader, "__module__", "")
        wrapped = reader
        assert wrapped is governed_io.load_data or "governed_io" in source or _delegates(reader), (
            f"{name} does not use the one governed reader"
        )


def _delegates(reader) -> bool:
    """A wrapper is acceptable; a second parser is not."""
    import inspect

    try:
        body = inspect.getsource(reader)
    except (OSError, TypeError):
        return False
    forbidden = ("yaml.load(", "yaml.safe_load(", "json.loads(", "json.load(")
    return not any(token in body for token in forbidden)


# A raw parser call is permitted only where it does not read a governed document,
# and only with a reason stated here, per call site.
#
# The discriminator is intent, not directory. An earlier version of this scan
# looked for the words "examples", "fixtures" or "corpus" on the same line, and
# an independent review found two governed readers it therefore never saw — both
# parsing the normative Compiled Brand Context out of the specification's own
# markdown, where no such word appears. A keyword heuristic decides what to
# *look* at; this list decides what is *allowed*, which is the assertion Class A
# actually needs.
RAW_PARSER_CALLS = (
    "json.loads(", "json.load(", "yaml.safe_load(", "yaml.load(",
    # An independent review found three of these in the JavaScript
    # canonicalisation harness, invisible to a Python-only scan: `JSON.parse` is
    # last-wins on a duplicate key, so the release's own cross-implementation
    # comparison read a different document than the governed reader did.
    "JSON.parse(",
)

# Every source language the release ships. The scan was `rglob("*.py")` and
# therefore could not see the file whose whole purpose is to be a second
# implementation.
SOURCE_SUFFIXES = (".py", ".mjs", ".js")

# Modules that *are* the governed reader.
READER_IMPLEMENTATION_FILES = {"governed_io.py", "canonical.py"}

# Every directory the scan walks. It walked `reference/` alone, so the tooling
# that *produces* the release was outside its field of view: `build-release.py`
# read `publication-record.json` with a raw parser, last-wins on a duplicate key
# in the one file that says what the release contains, and then rewrote it.
SCANNED_ROOTS = ("reference", "tools")


def _scanned_sources():
    """Every source file in the release that could carry a reader."""
    for root in SCANNED_ROOTS:
        base = PACKAGE_ROOT / root
        if not base.is_dir():
            continue
        for item in sorted(base.rglob("*")):
            if item.is_file() and item.suffix in SOURCE_SUFFIXES and "__pycache__" not in item.parts:
                yield item

# Every permitted raw parse in the release, keyed by file and by the source line
# itself, with the reason it is not a governed read. A line that moves keeps its
# entry; a line that changes loses it and has to be re-justified.
RAW_PARSER_ALLOWLIST = {
    ('reference/adversarial/canonical_js.mjs', 'if (text[at] === \'"\') { at += 1; return JSON.parse(text.slice(start, at)); }'):
        'inside the governed reader itself: unescaping one already-delimited JSON string token',
    ('reference/adversarial/canonical_js.mjs', 'const parsed=JSON.parse(raw);'):
        'the vector input is the string under test, parsed identically on both sides so the comparison compares canonicalisation and nothing else',
    ('reference/foundation/tests/test_reference.py', 'schema = json.loads((ROOT / "value-schemas" / schema_name).read_text(encoding="utf-8"))'):
        'JSON Schema contract, validated against rather than hashed as a governed value',
    ('reference/context-assembly/tests/test_context_assembly.py', 'model_schema = json.loads('):
        'JSON Schema contract, validated against rather than hashed as a governed value',
    ('reference/context-assembly/tests/test_context_assembly.py', 'request_schema = json.loads('):
        'JSON Schema contract, validated against rather than hashed as a governed value',
    ('reference/context-assembly/tests/test_context_assembly.py', 'review_schema = json.loads('):
        'JSON Schema contract, validated against rather than hashed as a governed value',
    ('reference/context-assembly/tests/test_context_assembly.py', 'schema = json.loads('):
        'JSON Schema contract, validated against rather than hashed as a governed value',
    ('reference/design-space/tests/test_design_space.py', 'return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))'):
        'JSON Schema contract, validated against rather than hashed as a governed value',
    ('reference/golden/test_golden.py', 'return json.loads(candidate.read_text(encoding="utf-8"))'):
        'JSON Schema contract, resolved by the document\'s declared version',
    ('reference/integration/test_integration.py', 'obj=json.loads(path.read_text())'):
        'JSON Schema contract: the $id sweep over the published schema directory',
    ('reference/foundation/tests/test_obds_200.py', 'result = json.loads('):
        'release packaging metadata, not a governed document',
    ('reference/foundation/src/obds_ref/cli.py', '"probe": repr(yaml.safe_load("a: true")) + repr(yaml.safe_load("a: 1e3")),'):
        'the parser-isolation conformance probe: it measures PyYAML, it reads no document',
    ('reference/foundation/tests/test_obds_300_class_b.py', 'return json.loads(canonical_json_bytes(document).decode("utf-8"))'):
        'parses bytes this test just produced from an in-memory value',
    ('reference/foundation/tests/test_obds_300_class_e_d.py', 'before = repr(yaml.safe_load("a: true"))'):
        'seam S1 probe: it measures PyYAML, it reads no document',
    ('reference/foundation/tests/test_obds_300_class_e_d.py', 'assert repr(yaml.safe_load("a: true")) == before'):
        'seam S1 probe: it measures PyYAML, it reads no document',
    ('reference/adversarial/test_adversarial.py', 'py = [canonical_json_bytes(json.loads(raw)).decode() for raw in raws]'):
        'the vector input is the string under test, parsed identically on both sides so the comparison compares canonicalisation and nothing else',
    ('reference/adversarial/test_adversarial.py', 'schema=json.loads((VALUE_SCHEMAS/"rule.schema.json").read_text())'):
        'JSON Schema contract, validated against rather than hashed as a governed value',
    ('reference/adversarial/test_adversarial.py', 'py=[canonical_json_bytes(json.loads(raw)).decode() for raw in raws]'):
        'the vector input is the string under test, parsed identically on both sides so the comparison compares canonicalisation and nothing else',
    ('reference/adversarial/test_adversarial.py', 'schema=json.loads((ROOT/"foundation"/"value-schemas"/"colour-hex.schema.json").read_text())'):
        'JSON Schema contract, validated against rather than hashed as a governed value',
    ('reference/adversarial/test_adversarial.py', 'index=json.loads((PACKAGE_ROOT/f"OBDS-{_release()}-SCHEMA-INDEX.json").read_text())'):
        'release packaging metadata, not a governed document',
    ('reference/adversarial/test_adversarial.py', 'py=[canonical_json_bytes(json.loads(raw)).decode() for raw in raws]'):
        'the vector input is the string under test, parsed identically on both sides so the comparison compares canonicalisation and nothing else',
    ('reference/adversarial/test_adversarial.py', 'py = [canonical_json_bytes(json.loads(raw)).decode() for raw in raws]'):
        'the vector input is the string under test, parsed identically on both sides so the comparison compares canonicalisation and nothing else',
    ('reference/adversarial/test_adversarial.py', 'produced = canonical_json_bytes(json.loads(case["input"]))'):
        'parses a string this test just produced, not a document',
    ('reference/adversarial/test_adversarial.py', 'canonical_json_bytes(json.loads(case["input"]))'):
        'parses a string this test just produced, not a document',
    ('reference/context-assembly/tests/test_context_assembly.py', 'compiled = json.loads(json.dumps(compiled))'):
        'parses a string this test just produced, not a document',
    ('reference/context-delivery/tests/test_views.py', 'card_schema = json.loads((ROOT / "schemas" / "search-card.schema.json").read_text(encoding="utf-8"))'):
        'JSON Schema contract, validated against rather than hashed as a governed value',
    ('reference/context-delivery/tests/test_views.py', 'chapter_schema = json.loads((ROOT / "schemas" / "reasoning-chapter.schema.json").read_text(encoding="utf-8"))'):
        'JSON Schema contract, validated against rather than hashed as a governed value',
    ('reference/foundation/tests/test_obds_11.py', 'schema = json.loads(schema_path.read_text(encoding="utf-8"))'):
        'JSON Schema contract, validated against rather than hashed as a governed value',
    ('reference/golden/test_golden.py', 'rule_schema = json.loads((VALUE_SCHEMAS / "rule.schema.json").read_text(encoding="utf-8"))'):
        'JSON Schema contract, validated against rather than hashed as a governed value',
    ('reference/golden/test_golden.py', 'boundary_schema = json.loads((VALUE_SCHEMAS / "semantic-boundary.schema.json").read_text(encoding="utf-8"))'):
        'JSON Schema contract, validated against rather than hashed as a governed value',
    ('reference/golden/test_golden.py', 'return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))'):
        'JSON Schema contract, validated against rather than hashed as a governed value',
    ('reference/integration/test_integration.py', "index=json.loads((ROOT/f'OBDS-{RELEASE}-SCHEMA-INDEX.json').read_text())"):
        'release packaging metadata, not a governed document',
    ('reference/integration/test_integration.py', "obj=json.loads((SCHEMAS/item['file']).read_text())"):
        'JSON Schema contract, validated against rather than hashed as a governed value',
    ('reference/integration/test_integration.py', "obj=json.loads((VALUE_SCHEMAS/item['file']).read_text())"):
        'JSON Schema contract, validated against rather than hashed as a governed value',
    ('reference/integration/test_integration.py', "registry=json.loads((ROOT/f'OBDS-{RELEASE}-CAPABILITY-REGISTRY.json').read_text())"):
        'release packaging metadata, not a governed document',
    ('reference/integration/test_integration.py', "index=json.loads((ROOT/f'OBDS-{RELEASE}-SCHEMA-INDEX.json').read_text())"):
        'release packaging metadata, not a governed document',
    ('reference/integration/test_integration.py', "helper=json.loads((ROOT/'reference'/'foundation'/'value-schemas'/'colour-hex.schema.json').read_text())"):
        'JSON Schema contract, validated against rather than hashed as a governed value',
    ('reference/integration/test_integration.py', "schema=json.loads((SCHEMAS/'brand-manifest.schema.json').read_text())"):
        'JSON Schema contract, validated against rather than hashed as a governed value',
    ('reference/integration/test_integration.py', "schema=json.loads((SCHEMAS/'brand-manifest.schema.json').read_text())"):
        'JSON Schema contract, validated against rather than hashed as a governed value',
    ('reference/integration/test_integration.py', "schema=json.loads((SCHEMAS/'brand-manifest.schema.json').read_text()); assert 'valueContracts' in schema['required']"):
        'JSON Schema contract, validated against rather than hashed as a governed value',
    ('reference/integration/test_integration.py', "registry=json.loads((ROOT/f'OBDS-{RELEASE}-CAPABILITY-REGISTRY.json').read_text())"):
        'release packaging metadata, not a governed document',
    ('reference/integration/test_integration.py', "index=json.loads((ROOT/f'OBDS-{RELEASE}-SCHEMA-INDEX.json').read_text())"):
        'release packaging metadata, not a governed document',
}


def test_a1_no_module_reads_a_governed_document_with_a_raw_parser():
    """A1, stated by discovery rather than by a hand-kept list of readers.

    The enumerated registry above is a hand-kept list compared against a function
    that builds the same list, so on its own it cannot notice a reader nobody
    enumerated. Two independent reviews found exactly that, twice: first a
    compiled context read with `json.loads` in a test, then the normative
    compiled-context example read the same way in a test *and* in the release
    gate. None of them was inside any assertion.

    So this scans every raw parse in the release and requires a stated reason for
    each survivor. There is no reason a governed document could be given.
    """
    offenders = []
    for path in _scanned_sources():
        if path.name in READER_IMPLEMENTATION_FILES:
            continue
        if path.name == Path(__file__).name:
            continue
        relative = str(path.relative_to(PACKAGE_ROOT))
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not any(call in line for call in RAW_PARSER_CALLS):
                continue
            if (relative, line.strip()) in RAW_PARSER_ALLOWLIST:
                continue
            offenders.append(f"{relative}:{number}: {line.strip()}")
    assert not offenders, (
        "a raw parser call has no stated reason, so it is a governed reader outside "
        "the one governed contract:\n" + "\n".join(offenders)
    )


def test_a1_the_allowlist_has_no_dead_entries():
    """An allowlist that outlives its call sites stops describing the release."""
    live = set()
    for path in _scanned_sources():
        relative = str(path.relative_to(PACKAGE_ROOT))
        for line in path.read_text(encoding="utf-8").splitlines():
            live.add((relative, line.strip()))
    dead = sorted(key for key in RAW_PARSER_ALLOWLIST if key not in live)
    assert not dead, f"allowlist entries no longer present in the release: {dead}"


def test_a1_the_javascript_reader_refuses_what_the_python_reader_refuses(tmp_path):
    """Class A applies in every runtime the release ships, not only in Python.

    `canonical_js.mjs` exists to prove that two independent implementations agree
    on section 14.3 canonicalisation. It read the Unicode pin and the vector
    document with `JSON.parse`, which is last-wins on a duplicate object key, so
    the comparison could be run against a different document than the Python side
    saw — in the one file whose purpose is that they agree.
    """
    import shutil
    import subprocess

    node = shutil.which("node")
    if node is None:  # pragma: no cover - the JS suite is skipped without node
        pytest.skip("node is not available")

    harness = REFERENCE / "adversarial" / "canonical_js.mjs"
    document = tmp_path / "duplicate-vectors.json"
    document.write_text(
        '{"vectors":[{"input":"{\\"a\\":1}"}],"vectors":[{"input":"{\\"b\\":2}"}]}',
        encoding="utf-8",
    )

    completed = subprocess.run([node, str(harness), str(document)], capture_output=True, text=True)
    assert completed.returncode != 0, (
        "the JavaScript reader accepted a duplicate object key: it printed "
        + completed.stdout.strip()
    )
    assert "duplicate object key" in completed.stderr

    with pytest.raises(ValidationFailure):
        load_data(document)

    # And the honest corpus still runs, so the refusal is a contract and not a
    # broken reader.
    vectors = REFERENCE / "adversarial" / "canonical-vectors.json"
    honest = subprocess.run([node, str(harness), str(vectors)], capture_output=True, text=True)
    assert honest.returncode == 0, honest.stderr
    assert honest.stdout.strip()


# --------------------------------------------------------------------------
# A2 — cross-reader agreement. This is the test that names the invariant.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("scalar", AMBIGUOUS_SCALARS)
def test_a2_readers_agree_on_every_ambiguous_scalar(tmp_path, scalar):
    """For every governed document: same value, or every reader refuses.

    `017` bound 15 under one contract and 17 under another; `12:30` bound 750
    and the string. Both were carried into a `manifest.contentHash` that claims
    to bind exactly the bytes a Search Card was built from.
    """
    path = tmp_path / "probe.yaml"
    path.write_text(_yaml_doc(scalar), encoding="utf-8")
    results = {name: _read(reader, path) for name, reader in _governed_readers().items()}
    statuses = {status for status, _ in results.values()}
    assert len(statuses) == 1, f"readers disagree about whether {scalar!r} is governable: {results}"
    if statuses == {"ok"}:
        shapes = {name: canonical_json_bytes(value) for name, (_, value) in results.items()}
        assert len(set(shapes.values())) == 1, f"readers disagree about the value of {scalar!r}: {shapes}"


def _javascript_canonical_form(path):
    """The shipped second implementation, driven as a governed reader.

    Returns the canonical form it produced, or raises `ValidationFailure` if it
    refused the document — the same two outcomes the Python reader has, so the
    comparison is value-for-value and refusal-for-refusal.
    """
    import shutil
    import subprocess

    node = shutil.which("node")
    if node is None:  # pragma: no cover - the JS suite is skipped without node
        pytest.skip("node is not available")
    harness = REFERENCE / "adversarial" / "canonical_js.mjs"
    completed = subprocess.run(
        [node, str(harness), "--read", str(path)], capture_output=True, text=True
    )
    if completed.returncode != 0:
        message = (completed.stderr.strip().splitlines() or ["refused"])[-1]
        raise ValidationFailure([f"{path}: {message}"])
    return bytes.fromhex(completed.stdout.strip()).decode("utf-8")


JSON_PROBES = {
    # Every one of these is a document the two runtimes could disagree about.
    # `2^53` is the case an independent review found: exactly representable as
    # binary64 and *not* a JavaScript safe integer, so a `Number.isSafeInteger`
    # test refused a document the contract admits.
    "exactly-representable-2-53": '{"kind":"probe","value":9007199254740992}',
    "not-exactly-representable": '{"kind":"probe","value":9007199254740993}',
    "large-negative": '{"kind":"probe","value":-9007199254740992}',
    "float": '{"kind":"probe","value":1.5e3}',
    "minus-zero": '{"kind":"probe","value":-0}',
    "duplicate-key": '{"kind":"probe","value":1,"value":2}',
    "duplicate-key-nfc": '{"kind":"probe","caf\u00e9":1,"cafe\u0301":2}',
    "leading-zero": '{"kind":"probe","value":017}',
    "plus-sign": '{"kind":"probe","value":+1}',
    "hex": '{"kind":"probe","value":0x1F}',
    "nan": '{"kind":"probe","value":NaN}',
    "infinity": '{"kind":"probe","value":Infinity}',
    "trailing-comma": '{"kind":"probe","value":1,}',
    "single-quotes": "{'kind':'probe'}",
    "sequence-root": '[{"kind":"probe"}]',
    "trailing-content": '{"kind":"probe"} {"kind":"probe"}',
    "astral-escaped-surrogate-pair": r'{"kind":"probe","value":"\ud83d\ude00"}',
    "escaped-solidus": r'{"kind":"probe","value":"a\/b"}',
    "deep": '{"kind":"probe","value":' + "[" * 140 + "null" + "]" * 140 + "}",
    # Keys that are two under NFC and one after section 14.3's line-ending fold.
    # Written as escapes so the document stays syntactically valid JSON and the
    # readers reach the *key comparison* rather than a syntax error.
    "canonically-colliding-keys": r'{"kind":"probe","a\rb":1,"a\nb":2}',
    # A finite *spelling* whose value is not finite. `parse_constant` catches the
    # literals `Infinity` and `NaN`; this is an ordinary number that overflows.
    "overflow-to-infinity": '{"kind":"probe","value":1e400}',
    "overflow-to-negative-infinity": '{"kind":"probe","value":-1e400}',
    "underflow-to-zero": '{"kind":"probe","value":1e-400}',
    # JavaScript object semantics, not JSON semantics. Assigning `__proto__` on
    # an ordinary object invokes the inherited prototype setter, so the key was
    # silently absent from the JavaScript reader's value while the Python reader
    # carried it. A governed reader may not lose a key because of its name.
    "proto-key": '{"kind":"probe","__proto__":{"polluted":true}}',
    "proto-key-shallow": '{"kind":"probe","__proto__":"x"}',
    "constructor-key": '{"kind":"probe","constructor":"x"}',
    "prototype-key": '{"kind":"probe","prototype":"x"}',
    "to-string-key": '{"kind":"probe","toString":"x"}',
}

# Probes that are bytes rather than text, because the divergence is in the
# decoding. Node's `readFileSync(file, "utf8")` substitutes U+FFFD for a
# malformed sequence, so it read a different document than the Python reader
# refused outright.
BYTE_PROBES = {
    "invalid-utf8-continuation": b'{"kind":"probe","value":"\xff\xfe"}',
    "truncated-utf8-sequence": b'{"kind":"probe","value":"\xe2\x82"}',
    "lone-surrogate-bytes": b'{"kind":"probe","value":"\xed\xa0\x80"}',
    "overlong-encoding": b'{"kind":"probe","value":"\xc0\xaf"}',
}


@pytest.mark.parametrize("probe", sorted(BYTE_PROBES))
def test_a2_the_javascript_reader_agrees_on_bytes_that_are_not_utf8(tmp_path, probe):
    """Section 28.1: governed input is UTF-8, and what is not UTF-8 is not input.

    Substituting U+FFFD is a decision about what the document says, taken by a
    decoder rather than by the contract.
    """
    path = tmp_path / "probe.json"
    path.write_bytes(BYTE_PROBES[probe])

    try:
        load_data(path)
        python_accepted = True
    except (ValidationFailure, ValueError, UnicodeDecodeError):
        python_accepted = False

    try:
        _javascript_canonical_form(path)
        javascript_accepted = True
    except ValidationFailure:
        javascript_accepted = False

    assert python_accepted is False, "the Python reader accepted bytes that are not UTF-8"
    assert javascript_accepted == python_accepted, (
        f"{probe}: javascript {'accepted' if javascript_accepted else 'refused'}, "
        f"python {'accepted' if python_accepted else 'refused'}"
    )


@pytest.mark.parametrize("probe", sorted(JSON_PROBES))
def test_a2_the_javascript_reader_agrees_with_the_governed_contract(tmp_path, probe):
    """A2 across runtimes, not only across modules.

    `canonical_js.mjs` exists to prove two independent implementations agree on
    section 14.3. That proof is worth nothing if the two do not first agree on
    what the document *is*, and an independent review found them disagreeing on
    exactly that: the JavaScript reader refused `9007199254740992` — a value the
    shipped canonical vectors admit — because it asked whether the integer was
    *safe* rather than whether it was exactly representable.
    """
    path = tmp_path / "probe.json"
    path.write_text(JSON_PROBES[probe], encoding="utf-8")

    try:
        expected = canonical_json_bytes(load_data(path)).decode("utf-8")
    except (ValidationFailure, ValueError, TypeError):
        expected = None

    try:
        actual = _javascript_canonical_form(path)
    except ValidationFailure:
        actual = None

    assert (expected is None) == (actual is None), (
        f"{probe}: python {'refused' if expected is None else 'accepted'}, "
        f"javascript {'refused' if actual is None else 'accepted'}"
    )
    if expected is not None:
        assert expected == actual, probe


def test_a2_the_javascript_vector_path_refuses_canonically_colliding_keys(tmp_path):
    """The JavaScript reader's *normal* path, not only its `--read` mode.

    `--read` canonicalises afterwards and would catch a key collision as a side
    effect. The vector path does not canonicalise the document, so a reader that
    deduplicates on NFC alone published a conformance result for a document the
    Python reader refuses.
    """
    import shutil
    import subprocess

    node = shutil.which("node")
    if node is None:  # pragma: no cover - the JS suite is skipped without node
        pytest.skip("node is not available")

    document = tmp_path / "colliding-vectors.json"
    document.write_text(
        r'{"vectors":[{"input":"{\"a\":1}"}],"a\rb":1,"a\nb":2}', encoding="utf-8"
    )

    with pytest.raises(ValidationFailure):
        load_data(document)

    harness = REFERENCE / "adversarial" / "canonical_js.mjs"
    completed = subprocess.run([node, str(harness), str(document)], capture_output=True, text=True)
    assert completed.returncode != 0, (
        "the JavaScript vector path published a result for a document the governed "
        "reader refuses: " + completed.stdout.strip()
    )
    assert "duplicate object key" in completed.stderr


def test_a2_the_javascript_reader_agrees_on_every_shipped_governed_json_document():
    documents = sorted(
        path for path in PACKAGE_ROOT.glob("reference/**/*.json")
        if "__pycache__" not in path.parts and ".pytest_cache" not in path.parts
        and "governed-input" not in path.parts
    )
    assert len(documents) >= 10, len(documents)
    for path in documents:
        try:
            expected = canonical_json_bytes(load_data(path)).decode("utf-8")
        except (ValidationFailure, ValueError, TypeError):
            expected = None
        try:
            actual = _javascript_canonical_form(path)
        except ValidationFailure:
            actual = None
        assert (expected is None) == (actual is None), path
        if expected is not None:
            assert expected == actual, path


def test_a2_readers_agree_on_every_shipped_governed_document():
    """The corpus that shipped, read by every reader, compared byte for byte."""
    documents = sorted(
        path
        for pattern in ("examples/**/*.yaml", "examples/**/*.json")
        for path in PACKAGE_ROOT.glob(pattern)
    )
    assert documents, "no shipped governed documents found"
    readers = _governed_readers()
    for path in documents:
        results = {name: _read(reader, path) for name, reader in readers.items()}
        statuses = {status for status, _ in results.values()}
        assert len(statuses) == 1, f"readers disagree about {path.name}: {results}"
        if statuses == {"ok"}:
            shapes = {canonical_json_bytes(value) for _, value in results.values()}
            assert len(shapes) == 1, f"readers disagree about the value of {path.name}"


# --------------------------------------------------------------------------
# A3 — the bounds are the contract's, not the runtime's
# --------------------------------------------------------------------------

@pytest.mark.parametrize("spelling", ["1e400", "-1e400", "1E400"])
def test_a3_a_number_whose_value_is_not_finite_is_refused_by_every_reader(tmp_path, spelling):
    """Section 28.1 refuses a non-finite number, however it is spelled.

    `parse_constant` catches `Infinity`, `-Infinity` and `NaN`. It does not catch
    a syntactically ordinary number that overflows to infinity, which Python's
    default `parse_float` produces happily. `load_data` refused it downstream
    through `canonical_json_bytes`; `read_governed_document` did not, and that is
    the path `canonical`'s own pin reader uses.
    """
    path = tmp_path / "overflow.json"
    path.write_text('{"kind":"probe","value":' + spelling + "}", encoding="utf-8")
    for name, reader in _governed_readers().items():
        status, _ = _read(reader, path)
        assert status == "refused", f"{name} accepted {spelling} as a governed number"


def test_a3_every_reader_enforces_the_nesting_bound(tmp_path):
    """An unstated limit is whatever the host stack happens to be.

    The 2.0.0 conformance runner read fixtures raw, so a deep document raised
    RecursionError out of the runner instead of failing the case.
    """
    depth = MAX_NESTING_DEPTH + 40
    payload = "null"
    for _ in range(depth):
        payload = "[" + payload + "]"
    path = tmp_path / "deep.json"
    path.write_text('{"kind": "probe", "value": ' + payload + "}", encoding="utf-8")
    for name, reader in _governed_readers().items():
        status, detail = _read(reader, path)
        assert status == "refused", f"{name} accepted a document nested {depth} deep"
        assert detail != "RecursionError", f"{name} crashed rather than refused"


def test_a3_every_reader_bounds_alias_expansion(tmp_path):
    """The 425-byte alias bomb did not terminate in six seconds under one reader."""
    lines = ["kind: probe", "a: &a [x, x, x, x, x, x, x, x, x]"]
    for index, previous in enumerate("abcdefghij"[:9]):
        nxt = "abcdefghij"[index + 1]
        lines.append(f"{nxt}: &{nxt} [*{previous}, *{previous}, *{previous}, *{previous}, *{previous}, *{previous}, *{previous}, *{previous}, *{previous}]")
    lines.append("value: *j")
    path = tmp_path / "bomb.yaml"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for name, reader in _governed_readers().items():
        status, _ = _read(reader, path)
        assert status == "refused", f"{name} expanded an unbounded alias"


# The two governed entry points, over the forms section 28.1 actually bounds.
# `read_governed_text` exists because the release gate scrapes governed bytes
# out of published HTML and never has a path to hand. It shipped as a second
# reader: the nesting bound was stated in `read_governed_document` alone, so an
# in-memory document 101 levels deep was governable and the same bytes on disk
# were not. Each entry is (name, suffix, text).
ENTRY_POINT_PARITY_CASES = [
    ("json at the nesting bound", "accepted", ".json", '{"kind":"probe","value":' + "[" * (MAX_NESTING_DEPTH - 2) + "null" + "]" * (MAX_NESTING_DEPTH - 2) + "}"),
    ("json over the nesting bound", "refused", ".json", '{"kind":"probe","value":' + "[" * (MAX_NESTING_DEPTH + 1) + "null" + "]" * (MAX_NESTING_DEPTH + 1) + "}"),
    ("yaml over the nesting bound", "refused", ".yaml", "kind: probe\nvalue: " + "[" * (MAX_NESTING_DEPTH + 1) + "]" * (MAX_NESTING_DEPTH + 1) + "\n"),
    ("duplicate json property", "refused", ".json", '{"kind":"probe","a":1,"a":2}'),
    ("duplicate yaml key", "refused", ".yaml", "kind: probe\na: 1\na: 2\n"),
    ("keys colliding only after canonicalisation", "refused", ".json", '{"kind":"probe","\u00e9":1,"e\u0301":2}'),
    ("truncated json", "refused", ".json", '{"kind":"probe","value":'),
    ("json root that is a bare scalar", "refused", ".json", "42"),
    ("json root that is a sequence", "refused", ".json", "[1,2,3]"),
    ("yaml root that is a sequence", "refused", ".yaml", "- kind: probe\n"),
    ("yaml root that is a bare scalar", "refused", ".yaml", "42\n"),
    ("empty document", "refused", ".json", ""),
    ("non-finite json constant", "refused", ".json", '{"kind":"probe","value":NaN}'),
    ("json number that overflows to infinity", "refused", ".json", '{"kind":"probe","value":1e400}'),
    ("yaml version-sensitive line break", "refused", ".yaml", "kind: probe\nvalue: a\u2028b\n"),
    ("yaml alias expansion bomb", "refused", ".yaml", "kind: probe\n" + "a: &a [x, x, x, x, x, x, x, x, x]\n" + "".join(
        f"{'abcdefghij'[i + 1]}: &{'abcdefghij'[i + 1]} [" + ", ".join([f"*{'abcdefghij'[i]}"] * 9) + "]\n"
        for i in range(9)
    ) + "value: *j\n"),
    ("yaml sexagesimal, a YAML 1.1 resolver reads 22", "refused", ".yaml", "kind: probe\nvalue: 2:2\n"),
    ("yaml norway", "accepted", ".yaml", "kind: probe\nvalue: NO\n"),
    ("ordinary governed json", "accepted", ".json", '{"kind":"probe","value":[1,2,3]}'),
    ("ordinary governed yaml", "accepted", ".yaml", "kind: probe\nvalue:\n  - 1\n  - 2\n"),
]


@pytest.mark.parametrize("name,expected,suffix,text", ENTRY_POINT_PARITY_CASES, ids=[c[0] for c in ENTRY_POINT_PARITY_CASES])
def test_a3_both_governed_entry_points_decide_the_same_bytes_the_same_way(tmp_path, name, expected, suffix, text):
    """Same governed bytes, same verdict, whichever entry point carried them.

    A bound stated at one entry point is not part of the contract, it is part of
    that function. This drives both over the forms section 28.1 constrains and
    requires one verdict, and where both accept, one value.
    """
    path = tmp_path / f"probe{suffix}"
    path.write_text(text, encoding="utf-8")
    is_json = suffix == ".json"

    try:
        from_text = read_governed_text(text, is_json=is_json)
        text_status = "accepted"
    except ValidationFailure as exc:
        from_text, text_status = None, "refused"
        assert exc.errors, f"{name}: the in-memory reader refused without saying why"
    except Exception as exc:  # noqa: BLE001 - an uncontrolled escape is the defect
        pytest.fail(f"{name}: the in-memory reader raised {type(exc).__name__} instead of refusing")

    try:
        from_file = read_governed_document(path)
        file_status = "accepted"
    except ValidationFailure:
        from_file, file_status = None, "refused"
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"{name}: the file reader raised {type(exc).__name__} instead of refusing")

    # `load_data` is a governed reader too, and it was the only one that refused
    # a sequence root while the two below it returned the list. It is in the
    # comparison now, so a rule that lives in one layer cannot pass as the
    # contract again.
    try:
        load_data(path)
        document_status = "accepted"
    except ValidationFailure:
        document_status = "refused"
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"{name}: load_data raised {type(exc).__name__} instead of refusing")

    assert text_status == document_status, (
        f"{name}: read_governed_text {text_status} what load_data {document_status}"
    )
    assert text_status == file_status, (
        f"{name}: read_governed_text {text_status} what read_governed_document {file_status}"
    )
    # Parity alone is satisfied by two readers that are wrong together, which is
    # what a shared implementation makes easy. The verdict is stated per case so
    # dropping the bound from the shared reader fails here rather than passing
    # quietly on both sides.
    assert text_status == expected, f"{name}: section 28.1 says {expected}, both readers said {text_status}"
    if text_status == "accepted":
        assert canonical_json_bytes(from_text) == canonical_json_bytes(from_file), (
            f"{name}: the two entry points accepted the same bytes as different values"
        )


# --------------------------------------------------------------------------
# A4 — import hygiene. The only test that catches the derivation defect.
# --------------------------------------------------------------------------

def test_a4_importing_the_release_does_not_mutate_pyyaml():
    """No module changes another module's parser.

    `build_views` derived its loader as a bare subclass and then item-assigned
    into `yaml_implicit_resolvers`, which is inherited, so importing it mutated
    PyYAML process-wide. The dumper shares the resolver, so the governed writer
    changed too and `load_data` began refusing its own writer's output. It also
    silently changed what every test harness in the process read, which is how
    one defect was found from two directions by two auditors.

    Run in a subprocess: the assertion is about what an import does to a fresh
    interpreter, and this one has already imported everything.
    """
    modules = [str(REFERENCE / package) for package in FLAT_PACKAGES]
    script = textwrap.dedent(
        f"""
        import sys, json, importlib.util
        sys.path.insert(0, {str(FOUNDATION / "src")!r})
        import yaml

        def snapshot():
            return json.dumps({{
                "resolver": sorted(
                    (ch or "", [t for t, _ in items])
                    for ch, items in yaml.resolver.Resolver.yaml_implicit_resolvers.items()
                ),
                "safe": sorted(
                    (ch or "", [t for t, _ in items])
                    for ch, items in yaml.SafeLoader.yaml_implicit_resolvers.items()
                ),
                "probe_true": repr(yaml.safe_load("a: true")),
                "probe_num": repr(yaml.safe_load("a: 1e3")),
                "dump": yaml.safe_dump({{"b": "true", "c": "1e3"}}, sort_keys=True),
            }}, sort_keys=True)

        before = snapshot()

        import obds_ref.governed_io, obds_ref.canonical, obds_ref.compiler
        import obds_ref.checks, obds_ref.runtime, obds_ref.cli
        for directory in {modules!r}:
            sys.path.insert(0, directory)
        for directory in {modules!r}:
            for name in ("canonical", "governed_io", "build_views", "assemble_context", "design_space_ref"):
                path = __import__("pathlib").Path(directory) / (name + ".py")
                if not path.is_file():
                    continue
                key = directory.rsplit("/", 1)[-1].replace("-", "_") + "_" + name
                spec = importlib.util.spec_from_file_location(key, path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[key] = module
                spec.loader.exec_module(module)

        after = snapshot()
        print("SAME" if before == after else "CHANGED")
        if before != after:
            print(before)
            print(after)
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, cwd=str(PACKAGE_ROOT)
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.startswith("SAME"), (
        "importing the release mutated PyYAML process-wide:\n" + completed.stdout
    )


# --------------------------------------------------------------------------
# A5 — the writer and the reader are one contract
# --------------------------------------------------------------------------

def test_a5_round_trip_is_order_independent(tmp_path):
    """`save_yaml` output must be readable by `load_data` in any import order.

    The 2.0.0 failure mode was import-order dependent, so a round-trip test in
    a process that had imported only the compiler passed while the shipped
    build wrote documents the compiler refused.
    """
    from obds_ref.compiler import save_yaml

    document = {
        "kind": "probe",
        "strings": ["true", "1e3", "017", "12:30", "yes", "~", "null", ".inf", "no"],
        "numbers": [17, 1000.0, -0.5],
        "flags": [True, False],
        "nothing": None,
    }
    path = tmp_path / "round-trip.yaml"
    save_yaml(path, document)
    for name, reader in _governed_readers().items():
        status, value = _read(reader, path)
        assert status == "ok", f"{name} refused the governed writer's own output: {value}"
        assert value == document, f"{name} round-tripped the governed writer's output to a different value"


# --------------------------------------------------------------------------
# A6 / A7 — duplicate property names
# --------------------------------------------------------------------------

def test_a6_duplicate_json_property_names_are_refused_by_every_reader(tmp_path):
    """Last-wins is a silent choice between two documents.

    The permissive JSON readers took the last copy. One of them was the Unicode
    pin table, which decides which code points every hash in the system admits.
    """
    path = tmp_path / "duplicate.json"
    path.write_text('{"kind": "probe", "value": 1, "value": 2}', encoding="utf-8")
    for name, reader in _governed_readers().items():
        status, _ = _read(reader, path)
        assert status == "refused", f"{name} accepted a duplicated JSON property name"


@pytest.mark.parametrize("suffix,body", [
    (".json", '{"kind":"probe","a\rb":1,"a\nb":2}'),
    (".yaml", 'kind: probe\n"a\\rb": 1\n"a\\nb": 2\n'),
])
def test_a6_keys_that_collide_only_after_canonicalisation_are_refused(tmp_path, suffix, body):
    """Deduplicating on NFC alone is not the canonical comparison.

    Section 14.3 step 2 folds CRLF and CR to LF, so `a\\rb` and `a\\nb` are one key
    in canonical form and two keys under NFC. `load_data` caught it downstream
    through `canonical_json_bytes`; `read_governed_document` did not, and
    `canonical._load_unicode_pin` reads the table behind every hash in the system
    through exactly that lower path.
    """
    path = tmp_path / f"collide{suffix}"
    path.write_text(body, encoding="utf-8")
    for name, reader in _governed_readers().items():
        status, _ = _read(reader, path)
        assert status == "refused", f"{name} accepted keys that collide after canonicalisation"


def test_a6_duplicate_yaml_mapping_keys_are_refused_by_every_reader(tmp_path):
    path = tmp_path / "duplicate.yaml"
    path.write_text("kind: probe\nvalue: 1\nvalue: 2\n", encoding="utf-8")
    for name, reader in _governed_readers().items():
        status, _ = _read(reader, path)
        assert status == "refused", f"{name} accepted a duplicated YAML mapping key"


def test_a7_schema_hash_refuses_a_schema_with_a_duplicated_property_name(tmp_path):
    """`schemaHash` is a governed hash, so its bytes are read under section 28.1.

    A permissive reader hashed whichever copy of the duplicated key came last,
    so two schemas that disagree could produce one `schemaHash` and a value
    contract could be gated by a schema nobody chose.
    """
    schema = tmp_path / "colour.schema.json"
    schema.write_text(
        '{"$schema": "https://json-schema.org/draft/2020-12/schema",'
        ' "type": "object", "type": "string"}',
        encoding="utf-8",
    )
    with pytest.raises(ValidationFailure):
        load_data(schema)


def test_a7_the_unicode_pin_is_read_under_the_governed_contract(tmp_path):
    """The pin decides which code points `canonical_json_bytes` admits.

    Before 3.0.0 it was read with a permissive `json.load`, so the table behind
    every hash in the system was the one governed input with no governed reader
    behind it.
    """
    pin = tmp_path / "unicode-pin.json"
    pin.write_text('{"unicodeVersion": "15.1.0", "assignedRanges": [[0, 1]], "assignedRanges": [[0, 9]]}',
                   encoding="utf-8")
    with pytest.raises(ValidationFailure):
        read_governed_document(pin)
