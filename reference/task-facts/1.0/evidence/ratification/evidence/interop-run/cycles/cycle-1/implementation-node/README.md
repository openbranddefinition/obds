# Independent Node.js Task Facts implementation

Standalone implementation of the frozen experimental v0.2 contract (snapshot payload version 0.1). No external dependencies or installation needed. Uses the supplied schema, unchanged, through a validator implementing its used vocabulary, plus contract-specific semantic validation.

From this directory:

```sh
node --test test.mjs
node evaluate.mjs ../fixtures/*.json
node run-fixtures.mjs ../fixtures ../regressions/inputs
```

`evaluate.mjs` processes explicit file paths in argument order. `run-fixtures.mjs` additionally expands each supplied directory's JSON files in lexical filename order. Both always emit a JSON object with a `results` array, and exit 2 when any record is INVALID (otherwise 0). The supplied suites intentionally contain invalid inputs. The output directory can be relocated; its schema resolves relative to its module, and input paths resolve from the caller's current directory.

Exports: `parseStrict(bytes)`, `validateTFJ(value)`, `canonical(value)` (canonical Unicode string, encoded as UTF-8 for hashing), `hash(value)`, `evaluate(snapshot, condition, verificationContext)`, `evaluate_family(decodedFamily)`, `evaluate_path(path)`, and `Invalid`. `evaluate_family` raises `Invalid` for TFJ/routing failures; the path boundary converts them into unbound records. Already-decoded JavaScript numbers cannot preserve JSON number-token categories; use `parseStrict` for raw transport validation.

`results.json` contains all six supplied substantive fixture families (66 records). `regression-results.json` contains all supplied regression inputs (36 records). Neither is compared against excluded expected/reference results. Tests use independently constructed cases and direct contract assertions. `test-results.txt` records 16 passing tests, including actual CLI execution.

## Independence and freeze

Only the supplied ROLE.md, implementer-input.zip, and files extracted from that ZIP were accessed as task inputs. No sibling implementation, Python implementation, previous implementation, expected results, reference evaluator, reference tests, evaluator reports, or private SUPABRAND ground truth was accessed. The archive's README and contract mention excluded materials; no referenced excluded materials were sought or accessed. No contract file was edited.

This output is complete and frozen. `PROVENANCE.json` records input digest, runtime, dependencies and test result. `FROZEN-MANIFEST.json` hashes every other output file; its self-exclusion avoids circular hashing. Freeze is a completion declaration, not a cryptographic signature or interoperability finding.
