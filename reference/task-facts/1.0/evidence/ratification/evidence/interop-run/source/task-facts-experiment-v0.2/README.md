# Task Facts experiment v0.2

Non-normative, standalone targeted contract clarification. No OBDS Core semantics changed and no predicate capability was added. This package is ready for design review, not integration or release.

Read [the contract](OBDS-TASK-FACTS-EXPERIMENT-v0.2.md) and [the delta](V0.1-TO-V0.2-DELTA.md). The independent v0.1 evaluation returned **NOT INTEROPERABLE** despite agreement on all 66 frozen decisions. This revision addresses its validation-layer, duplicate-routing-ID and raw-input classification ambiguities. Independent v0.2 interoperability remains unproven.

The original six fixture files and `expected-results.json` are copied byte-for-byte: **6 families, 28 cases, 66 decisions**. The snapshot payload retains `contractVersion: "0.1"`, TFJ-0.1 bytes and every original decision hash. Package/schema revision 0.2 does not change snapshot identity. Examples and verifier attestations remain synthetic; inherited source-corpus claims are not newly verified.

Additional transport documents live separately in `regressions/inputs/`, with literal expected records in `regressions/expected-results.json`: **24 scenarios, 36 emitted records**. These cover all 13 reported divergences plus routing/typing precedence and verification-context boundaries. They do not add a seventh substantive fixture family. Some files deliberately contain invalid JSON tokens.

Old/new counts: **31 → 57 unittest tests** (26 added: 24 vector tests and 2 preservation/batch tests); **0 → 24 boundary regression scenarios**; **66 → 102 frozen expected records** across both sets. The original substantive suite stays at 66. Vector tests check both the reference API's file boundary and actual CLI output, including null filling, sibling isolation and exit codes.

Run with Python 3.10+ and `jsonschema==4.26.0`:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python3 reference/evaluate.py fixtures/*.json
PYTHONDONTWRITEBYTECODE=1 python3 reference/evaluate.py regressions/inputs/*.json
```

Tests exit 0. Both CLI suites intentionally exit 2 because INVALID cases are expected. The CLI always emits `{"results": [...]}`; each failed transport/routing document contributes one record with null family/case/condition/hash fields. Other files retain their results. Typed errors with valid routing retain IDs and the actual canonical snapshot hash; an invalid condition does not suppress its valid sibling.

The [schema](schemas/task-facts.schema.json) separates routing from typed payload validation. Read the mandatory validation layers in contract section 6 before implementing: recursively validating payloads as a routing gate is forbidden. `evaluate(snapshot, condition, verification_context)` is the existing single-condition reference API. Verification context must come from a trusted verifier; embedded fixture attestations only simulate that boundary. No independent Python or Node implementation is delivered.

`PACKAGE-MANIFEST.json` inventories every file except itself by raw SHA-256 and records the supplied input hashes and frozen v0.1 file digests. Self-exclusion avoids circular hashing; this is not a signature or release manifest. The package and tests work after relocation, without the sibling v0.1 directory or evaluator access to expectations.
