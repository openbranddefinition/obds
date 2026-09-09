Independent Python Task Facts evaluator

Requires Python 3.11+; uses only the standard library. The supplied frozen schema is copied unchanged alongside the evaluator and interpreted locally. No install or network access is required.

From this temporary workspace:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s implementation-python -v
PYTHONDONTWRITEBYTECODE=1 python3 implementation-python/evaluate.py input/fixtures/*.json input/regressions/inputs/*.json
```

The CLI processes paths in argument order and prints `{"results": [...]}`. Its exit code is 2 when any decision is INVALID, otherwise 0. A missing file produces one unbound INPUT_IO_ERROR record while other files continue. `results.json` contains the supplied six fixture families followed by all regression input files, each group in filename order. No expected-result material was available or consulted; these are implementation outputs, not a claim of independent agreement.

Public functions in evaluate.py: `canonical_bytes(value)`, `snapshot_hash(value)`, `strict_load(raw)`, `evaluate(snapshot, condition, verification_context)`, `evaluate_family(family)`, and `evaluate_path(path)`. `evaluate_family` raises `Invalid` on TFJ/routing failures; `evaluate_path` returns unbound records for file-boundary failures.

Provenance and the explicit independence statement are in provenance.json. Test output is in test-output.txt. FROZEN-MANIFEST.json hashes every output file except itself. Output is frozen after this manifest is written; no revisions follow completion.
