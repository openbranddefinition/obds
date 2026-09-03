# OBDS 3.0.0 Test and Runtime Requirements

This file declares every dependency needed to reproduce the official 1067/1067 conformance run.
It separates what a consumer of OBDS needs from what the reference conformance suite needs.

## 1. OBDS consumer requirements

**None imposed by the specification.**

OBDS 3.0.0 is a data and contract specification. A conforming implementation may be written in
any language. The normative artefacts are plain text:

- `OBDS-3.0.0.md` (normative specification);
- `schemas/*.json` (21 public JSON Schemas, draft 2020-12) plus the versioned
  contracts beside them under `schemas/1.1.0/` and `schemas/3.0.0/`;
- `value-schemas/*.json` (6 public value-contract JSON Schemas, draft 2020-12) plus
  `value-schemas/3.0.0/rule.schema.json`;
- `OBDS-3.0.0-SCHEMA-INDEX.json` and `OBDS-3.0.0-CAPABILITY-REGISTRY.json`.

To consume OBDS you need a JSON Schema validator for your platform, a JSON reader and, if you
accept governed YAML, a YAML 1.2 reader that rejects duplicate keys. Nothing in this package is
required at runtime.

**Python is not an OBDS requirement. Node.js is not an OBDS requirement.**
Both are implementation choices of the reference suite in this package only.

## 2. Reference conformance-suite requirements

These are needed only to execute the suite in `reference/` and reproduce the published result.

| Dependency | Minimum | Verified on | Needed for |
|---|---|---|---|
| Python | 3.13 | 3.14 | all seven suites |
| PyYAML | 6.0 | 6.x | governed YAML loading |
| jsonschema | 4.20 | 4.x | schema validation |
| regex | pinned exactly | 2026.9.3 | Unicode-aware check primitives |
| pytest | 8.0 | 9.x | test execution |
| referencing | 0.35 | 0.37 | release-gate schema resolution (ships with jsonschema) |
| **Node.js** | **21** | **22.23.1** | **3 cross-language canonicalisation tests** |

Python dependencies are declared in `requirements.txt` and in
`reference/foundation/pyproject.toml` (`requires-python = ">=3.13"`).

`regex` is pinned to an exact version, not a floor. Section 11.5 delegates
`word_boundary_ci` to that package's own bundled Unicode tables, so an unbounded
dependency would be an unpinned normative contract: two conforming installs could
disagree about what the match mode means. The portable statement of the contract is
`reference/foundation/fixtures/word-boundary-ci.json`; the pin is how the reference
implementation reproduces it.

### Node.js is a hard requirement of the suite

Three tests in `reference/adversarial/test_adversarial.py` execute
`reference/adversarial/canonical_js.mjs` in a Node subprocess and compare its output byte for byte
against the Python canonicaliser:

- `test_b3_python_and_javascript_canonical_vectors_match`
- `test_rc5_canonical_boundary_numbers_and_astral_key_order_match_js`
- `test_rc5_cross_language_canonical_fuzz_256_binary64_values`

They are deliberately **not** skipped when Node is absent. Without `node` on `PATH` the suite
fails; it never reports a silent pass. That is intentional: the cross-language guarantee of
OBDS Canonical JSON v1 is only proven when both implementations actually run.

`canonical_js.mjs` uses ES modules and the `node:fs` prefix, and reads the pinned Unicode
assignment set shipped with the release. It refuses to run on a Node whose ICU carries a
Unicode database below 15.1.0, which is why the minimum is Node 21 rather than 18.

## 3. Reproducing the official result

The suite runs from the package root. In this project the repository root **is** the package
root, so a clone needs no unpacking step:

```bash
git clone https://github.com/<org>/obds.git && cd obds
python -m venv .venv && .venv/bin/pip install -r requirements.txt
node --version                     # must succeed
.venv/bin/python reference/run_all.py
.venv/bin/python reference/release-gate.py
```

From an unpacked release archive the same two commands work unchanged:

```bash
unzip OBDS-3.0.0-FINAL.zip && cd OBDS-3.0.0-FINAL
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python reference/run_all.py
.venv/bin/python reference/release-gate.py
```

Expected outcome:

```text
1067 passed, 0 failed, 0 skipped
```

The suite contains no `skipif`, no `pytest.skip` and no `xfail`. Every case runs on every
execution.

### Two supported layouts

The suite and the release gate resolve the public schemas in either layout and behave
identically in both:

| Layout | Public schemas | Value schemas |
|---|---|---|
| repository, matching the published URLs | `schemas/1.0.0/` | `value-schemas/1.0.0/` |
| unpacked release archive | `schemas/` | `value-schemas/` |

The repository keeps one copy of each schema, at the path its `$id` resolves to. The release
archive flattens them, exactly as 1.0.0, 1.0.1 and 1.0.2 shipped them.

### No cleanup step

Running the suite creates `__pycache__` and `.pytest_cache` directories, and a local `.venv` is
normal. Since 1.0.3 the release gate treats all of them as generated local caches rather than
package junk, so the natural order above succeeds with no manual deletion. What still fails the
gate is junk that would actually be shipped: `.DS_Store`, `Thumbs.db`, editor backups,
`__MACOSX`, and any cache file that has found its way into `PACKAGE-MANIFEST.json`.

## 4. Release-gate check

`reference/release-gate.py` validates the release metadata files against
`release-schemas/release-test-result.schema.json` and
`release-schemas/release-audit.schema.json`, asserts that the declared suite counts sum to the
declared passed count, proves the public schema surface and the normative contract fingerprints
have not moved, verifies every file listed in `PACKAGE-MANIFEST.json` against its recorded
sha256, and proves the package ships no junk. It is a package check, not an OBDS capability and
not part of the conformance suite.

```bash
python reference/release-gate.py
```

## 5. Suite composition

| Suite | Cases |
|---|---:|
| foundation | 961 |
| context-delivery | 3 |
| context-assembly | 24 |
| design-space | 20 |
| integration | 15 |
| golden | 6 |
| adversarial | 38 |
| **Total** | **1067** |

The foundation suite grew from 27 to 43 in OBDS 1.1, to 49 in 1.1.1 with the `requiresDefined`
precedence cases, the `asOf` verbatim case and the section 14 example check, to 75 in 1.1.2
with the section 14.3b escape table and the section 14.0 validity-window cases, to 81 in 1.1.3
with the conflict-relevance and governed-selection cases, to 89 in 1.1.4 with the eight
Unicode NFC scope-comparison regression cases, to 104 in 1.1.5 with the fifteen
`requiresDefinedRefs` regression cases, to 173 in 1.1.6 with the canonical identity,
pinned Unicode, `elementValueRef` applicability and executable validity-boundary cases, and to
323 in 2.0.0 with the governed YAML scalar cases and the section 14.3a conflict and hash cases.
It grew again in 3.0.0 with the Semantic Closure classes and the five systemic mechanisms
described below. The adversarial suite grew from 23 to 33 in 1.1.1 with the line-ending vectors.
It carried 27 cases from 1.0.2, when two cases were added to verify the published examples in
`examples/`. Releases up to and including 1.0.1 ran 105 cases with 25 in foundation; those
historical results stand as published in `spec/1.0.0/` and `spec/1.0.1/`.

## 6. What the 3.0.0 suite adds

Five of the foundation modules are enumerated rather than written case by case. Each reads a
machine-readable surface from `reference/foundation/tests/systemic_surface.py` and fails when a
new code path joins that surface without an entry, so the *shape* of a defect is closed instead
of one instance of it.

| Mechanism | Surface | What it drives |
|---|---|---|
| 1 | published 3.0 contracts | every leaf a contract constrains is constrained by the code, in both directions |
| 2 | governed hash call sites | every verification site is classified, and every verifier has a driver proved to reach it |
| 3 | semantic primitives implemented more than once | one normative vector set against every executable copy |
| 4 | Compiled Brand Context consumers | every executor runs parse, contract, integrity and fields |
| 5 | contract and version consumers | one derived discovery model drives packaging, the gate and path resolution |

Mechanism 2 is the strongest and the most easily overstated, so what it proves is written
down. For each governed hash verification call site the registry names the exact source line of
that site's gate. The test asserts the line occurs exactly once inside that function, copies the
release to a temporary directory, neutralises that one gate inside that one function's line
range, runs that one driver against the copy in a subprocess, and requires the driver to stop
refusing. A driver registered against a site it never reaches does not notice, and fails there.

What that does not prove is how strong each boundary's re-seal expectation is. That expectation
is a declared label beside each driver, and it is a development aid, not a normative claim.

## 7. Node.js

Unchanged from 2.0.0: three cross-language canonicalisation tests execute
`reference/adversarial/canonical_js.mjs` in a Node subprocess. They are not skipped when Node is
absent; without `node` on `PATH` the suite fails rather than reporting a silent pass. The
governed input contract of section 28.1 is compared across the two readers as well, so the
JavaScript reader has to refuse what the Python reader refuses.
