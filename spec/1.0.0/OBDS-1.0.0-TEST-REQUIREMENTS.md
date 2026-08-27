# OBDS 1.0.0 Test and Runtime Requirements

This file declares every dependency needed to reproduce the official 105/105 conformance run.
It separates what a consumer of OBDS needs from what the reference conformance suite needs.

## 1. OBDS consumer requirements

**None imposed by the specification.**

OBDS 1.0.0 is a data and contract specification. A conforming implementation may be written in
any language. The normative artefacts are plain text:

- `OBDS-1.0.0.md` (normative specification);
- `schemas/*.json` (21 public JSON Schemas, draft 2020-12);
- `value-schemas/*.json` (6 public value-contract JSON Schemas, draft 2020-12);
- `OBDS-1.0.0-SCHEMA-INDEX.json` and `OBDS-1.0.0-CAPABILITY-REGISTRY.json`.

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

From the package root, in a clean environment with no reused cache:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
node --version                     # must succeed
find . -name __pycache__ -prune -exec rm -rf {} +
find . -name .pytest_cache -prune -exec rm -rf {} +
PYTHONPATH="$PWD/reference/foundation/src" python reference/run_all.py
```

Expected outcome:

```text
105 passed, 0 failed, 0 skipped
```

The suite contains no `skipif`, no `pytest.skip` and no `xfail`. Every case runs on every
execution.

## 4. Release-gate check

`reference/release-gate.py` validates the release metadata files against
`release-schemas/release-test-result.schema.json` and
`release-schemas/release-audit.schema.json`, and asserts that the declared suite counts sum to
the declared passed count. It is a package check, not an OBDS capability and not part of the
105-case conformance suite.

```bash
python reference/release-gate.py
```

## 5. Suite composition

| Suite | Cases |
|---|---:|
| foundation | 25 |
| context-delivery | 3 |
| context-assembly | 15 |
| design-space | 18 |
| integration | 15 |
| golden | 6 |
| adversarial | 23 |
| **Total** | **105** |
