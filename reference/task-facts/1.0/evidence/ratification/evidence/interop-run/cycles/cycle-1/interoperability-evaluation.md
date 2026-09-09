# Independent interoperability evaluation — cycle 1

`INTEROPERABLE`

Independence is reasonably established. The two implementers were separate fresh Codex subagents with no inherited context, worked in separate temporary directories, and received the identical implementer ZIP SHA-256 `35fd3c427d6aa1cf6d8c3cc253fa2d1b227891294ea1c1891f158b1b358b7b16`. Both provenance statements attest no sibling implementation or excluded expected/reference access. Orchestration evidence records both implementations frozen before copying. The supplied input and output inventories match before and after evaluation. This is procedural independence supported by attestations; the shared filesystem did not enforce OS isolation. No private clarification was required.

The evaluator read only its role, the frozen contract/schema and fixture inputs, implementation documentation/provenance, and the permitted orchestration/integrity records before executing probes. It did not use either implementation source to design probes. A standalone standard-library generator authored 73 counter-probe files and synthetic verification contexts. Implementations ran unchanged from an external `/private/tmp` directory with `PYTHONDONTWRITEBYTECODE=1`.

| Suite | Files | Decisions per implementation | Full six-field agreement |
| --- | ---: | ---: | --- |
| Frozen fixtures | 6 | 66 | 66 / 66 |
| Frozen regressions | 24 | 36 | 36 / 36 |
| Independent counter-probes | 73 | 76 | 76 / 76 |

Agreement compares ordered records including family, caseId, conditionId, snapshotHash, outcome and reason. Both CLIs emitted the required JSON envelope and exit code 2 on each combined suite because each includes intentional INVALID inputs. No crashes or stderr output occurred.

All 16 relational identity checks passed across both implementations: object-key reordering preserves identity; set-member reordering preserves applicability but changes identity; missing/empty/unknown snapshots differ; changing task ID, action, artifact hash or input-package hash changes snapshot identity. Stale verification contexts become EVIDENCE_UNVERIFIED; independently renewed synthetic contexts restore APPLIES. Every bound counter-probe hash also matches the independently computed TFJ bytes (120 individual implementation checks). Canonicalisable malformed snapshots retain real hashes and routing; parse/TFJ/routing failures remain unbound.

All required counter-probe categories are covered below. Null is exercised both as a canonicalisable malformed snapshot and as a prohibited known string value; booleans, safe integer limits, numeric-looking strings, non-ASCII scalar text, controls, and Unicode scalar key ordering are included. Date/instant comparisons preserve TIME_BASIS_UNRESOLVED in both directions. Duplicate case/condition identities suppress the whole family, while a malformed condition leaves its valid sibling intact.

## Counter-probe detail

Each row records both implementations’ identical outcome/reason sequence. Full hashes and routing fields are in `evaluation-evidence/probe-results-by-name.json`.

| Probe | Agreed outcomes / reasons |
| --- | --- |
| absent-operand | INVALID / SCHEMA_INVALID |
| association-conflict | CONTRADICTORY / ASSOCIATION_CONFLICT |
| bad-op | INVALID / SCHEMA_INVALID |
| base | APPLIES / ALL_TRUE |
| campaign-claim | APPLIES / ALL_TRUE; APPLIES / ALL_TRUE |
| changed-action-stale | UNKNOWN / EVIDENCE_UNVERIFIED |
| changed-action-verified | APPLIES / ALL_TRUE |
| changed-artifactHash-stale | UNKNOWN / EVIDENCE_UNVERIFIED |
| changed-artifactHash-verified | APPLIES / ALL_TRUE |
| changed-id-stale | UNKNOWN / EVIDENCE_UNVERIFIED |
| changed-id-verified | APPLIES / ALL_TRUE |
| changed-inputPackageHash-stale | UNKNOWN / EVIDENCE_UNVERIFIED |
| changed-inputPackageHash-verified | APPLIES / ALL_TRUE |
| contradictory | CONTRADICTORY / FACT_CONTRADICTORY |
| duplicate-association | INVALID / TYPE_MISMATCH |
| duplicate-atoms | INVALID / SCHEMA_INVALID |
| duplicate-case-id | INVALID / DUPLICATE_ID |
| duplicate-condition-id | INVALID / DUPLICATE_ID |
| duplicate-set | INVALID / TYPE_MISMATCH |
| empty | DOES_NOT_APPLY / PREDICATE_FALSE |
| extra-case | INVALID / SCHEMA_INVALID |
| malformed-condition-valid-sibling | APPLIES / ALL_TRUE; INVALID / SCHEMA_INVALID |
| malformed-snapshot-array | INVALID / SCHEMA_INVALID |
| malformed-snapshot-boolean | INVALID / SCHEMA_INVALID |
| malformed-snapshot-integer | INVALID / SCHEMA_INVALID |
| malformed-snapshot-null | INVALID / SCHEMA_INVALID |
| malformed-snapshot-object | INVALID / SCHEMA_INVALID |
| malformed-snapshot-string | INVALID / SCHEMA_INVALID |
| missing-context | INVALID / SCHEMA_INVALID |
| missing-requires | INVALID / SCHEMA_INVALID |
| missing | UNKNOWN / FACT_MISSING |
| multiple-assets | APPLIES / ALL_TRUE |
| multiple-claims | APPLIES / ALL_TRUE |
| object-reordered | APPLIES / ALL_TRUE |
| partner-portrait | APPLIES / ALL_TRUE; APPLIES / ALL_TRUE |
| raw-bom | INVALID / JSON_PARSE_ERROR |
| raw-duplicate-key | INVALID / JSON_PARSE_ERROR |
| raw-escaped-duplicate-key | INVALID / JSON_PARSE_ERROR |
| raw-exponent | INVALID / NON_CANONICAL_INPUT |
| raw-float | INVALID / NON_CANONICAL_INPUT |
| raw-infinity | INVALID / JSON_PARSE_ERROR |
| raw-malformed-json | INVALID / JSON_PARSE_ERROR |
| raw-minus-zero | INVALID / SCHEMA_INVALID |
| raw-nan-after-float | INVALID / JSON_PARSE_ERROR |
| raw-nan | INVALID / JSON_PARSE_ERROR |
| raw-surrogate | INVALID / NON_CANONICAL_INPUT |
| raw-top-array | INVALID / SCHEMA_INVALID |
| raw-trailing | INVALID / JSON_PARSE_ERROR |
| raw-unsafe-integer | INVALID / NON_CANONICAL_INPUT |
| set-reordered | APPLIES / ALL_TRUE |
| special-fact-constructor | APPLIES / ALL_TRUE |
| special-fact-hasOwnProperty | APPLIES / ALL_TRUE |
| special-fact-toString | APPLIES / ALL_TRUE |
| time-date-instant | UNKNOWN / TIME_BASIS_UNRESOLVED |
| time-instant-date | UNKNOWN / TIME_BASIS_UNRESOLVED |
| time-leap-invalid | INVALID / TYPE_MISMATCH |
| time-leap-valid | APPLIES / ALL_TRUE |
| time-offset-equal | APPLIES / ALL_TRUE |
| time-unknown-offset | INVALID / TYPE_MISMATCH |
| time-year-one | APPLIES / ALL_TRUE |
| unknown | UNKNOWN / FACT_UNKNOWN |
| value-bool-as-int | INVALID / TYPE_MISMATCH |
| value-false | APPLIES / ALL_TRUE |
| value-int-as-bool | INVALID / TYPE_MISMATCH |
| value-integer-as-string | INVALID / TYPE_MISMATCH |
| value-maxint | APPLIES / ALL_TRUE |
| value-minint | APPLIES / ALL_TRUE |
| value-null | INVALID / TYPE_MISMATCH |
| value-numeric-string | APPLIES / ALL_TRUE |
| value-true | APPLIES / ALL_TRUE |
| value-unicode | APPLIES / ALL_TRUE |
| value-zero | APPLIES / ALL_TRUE |
| wrong-scalar-set | INVALID / TYPE_MISMATCH |

## Freeze and informational expectation check

The six aggregate result files were written and SHA-256 inventoried in `evaluation-evidence/RESULTS-FROZEN.json` before any expected-results file was opened. The freeze was verified again during finalization. Only afterwards were expected results inspected: Python and Node each match all 66 literal fixture expectations and all 36 regression expectations (ignoring fixture `basis`, which is explanatory metadata). This comparison is informational and did not determine cross-implementation agreement. No reference evaluator was used.

## Blocking divergences

None. No divergence classification applies. Neither implementation nor the frozen contract was repaired or modified. This verdict concerns the supplied contract, frozen inputs and listed probes; it does not establish production readiness, source truth or OBDS conformance.

## Reproduction

Run `PYTHONDONTWRITEBYTECODE=1 python3 _autonomous_interop_run/cycles/cycle-1/evaluation-evidence/run_evaluation.py` from the repository root. This regenerates independent probes in a new external temporary directory and writes both outputs and comparisons. `execution.json` records original commands, file order, working directory, exit codes and counts. `probe-inputs/` preserves exact raw probe documents. Run `finalize_report.py` only after the execution freeze to reproduce the informational expected comparison and this report.

`INTEROPERABLE`
