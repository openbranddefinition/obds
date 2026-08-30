# OBDS 1.1.1 Test and Runtime Requirements

This file declares every dependency needed to reproduce the official 139/139 conformance run.
It separates what a consumer of OBDS needs from what the reference conformance suite needs.

## 1. OBDS consumer requirements

**None imposed by the specification.**

OBDS 1.1.1 is a data and contract specification. A conforming implementation may be written in
any language. The normative artefacts are plain text:

- `OBDS-1.1.1.md` (normative specification);
- `schemas/*.json` (21 public JSON Schemas, draft 2020-12);
- `value-schemas/*.json` (6 public value-contract JSON Schemas, draft 2020-12);
- `OBDS-1.1.1-SCHEMA-INDEX.json` and `OBDS-1.1.1-CAPABILITY-REGISTRY.json`.

To consume OBDS you need a JSON Schema validator for your platform, a JSON reader and, if you
accept governed YAML, a YAML 1.2 reader that rejects duplicate keys. Nothing in this package is
required at runtime.

**Python is not an OBDS requirement. Node.js is not an OBDS requirement.**
Both are implementation choices of the reference suite in this package only.

## 2. Reference conformance-suite requirements

These are needed only to execute the suite in `reference/` and reproduce the published result.

| Dependency | Minimum | Verified on | Needed for |
|---|---|---|---|
| Python | 3.11 | 3.14 | all seven suites |
| PyYAML | 6.0 | 6.x | governed YAML loading |
| jsonschema | 4.20 | 4.x | schema validation |
| regex | 2025.0 | 2025.x | Unicode-aware check primitives |
| pytest | 8.0 | 9.x | test execution |
| referencing | 0.35 | 0.37 | release-gate schema resolution (ships with jsonschema) |
| **Node.js** | **18 LTS** | **22.23.1** | **3 cross-language canonicalisation tests** |

Python dependencies are declared in `requirements.txt` and in
`reference/foundation/pyproject.toml` (`requires-python = ">=3.11"`).

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

`canonical_js.mjs` uses ES modules and the `node:fs` prefix. Any current Node LTS satisfies this.

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
unzip OBDS-1.1.1-FINAL.zip && cd OBDS-1.1.1-FINAL
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python reference/run_all.py
.venv/bin/python reference/release-gate.py
```

Expected outcome:

```text
139 passed, 0 failed, 0 skipped
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
not part of the 139-case conformance suite.

```bash
python reference/release-gate.py
```

## 5. Suite composition

| Suite | Cases |
|---|---:|
| foundation | 49 |
| context-delivery | 3 |
| context-assembly | 15 |
| design-space | 18 |
| integration | 15 |
| golden | 6 |
| adversarial | 33 |
| **Total** | **139** |

The foundation suite grew from 27 to 43 in OBDS 1.1, which added the normative 1.1 cases, and to 49
in 1.1.1, which added the `requiresDefined` precedence cases, the `asOf` verbatim case and the
section 14 example check. The adversarial suite grew from 23 to 33 with the line-ending vectors. It carried
27 cases from 1.0.2, when two cases were added to verify the published examples in `examples/`.
Releases up to and including 1.0.1 ran 105 cases with 25 in foundation; those historical results
stand as published in `spec/1.0.0/` and `spec/1.0.1/`.
