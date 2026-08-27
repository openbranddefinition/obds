# OBDS 0.9.9 to 1.0.0 Migration

1. Set `schemaVersion` to `1.0.0`.
2. Use the single `OBDS-1.0.1.md` specification.
3. Remove dependencies on a separate `OBDS-CORE` document.
4. Keep `obds-foundation` in every manifest.
5. Treat optional profiles and runtime capabilities as parts of the same specification.
6. Rename references to `CORE Check Registry v1` to `Foundation Check Registry v1`.
7. Re-run the 1.0 schemas and every claimed capability suite.

## Brand State migration

OBDS 1.0 Brand States are:

- `defined`
- `unknown`
- `not_defined`
- `not_applicable`

A pre-1.0 `state: prohibited` element must become an explicit RULE with `obligation: prohibit`, exact scope, enforcement and validation mode. Do not silently map it to another knowledge state.

## Value Contract migration

Every defined FACT value declares `valueContractRef`. The referenced contract carries:

- `shapeHash`;
- `schemaRef`;
- `schemaHash`; and
- optional `validatorRef`.

Several contracts may exist for the same family and kind when approved shapes or contract versions differ. Recompute approval hashes after migration.

A pre-1.0 PATCH-style release that changed value shape or value contract must be reviewed as a compatibility event rather than carried forward automatically.

## Context Assembly migration

Compile targets before assembly. The Compiled Brand Context carries the target-scoped element records and Context Assembly policy. Normal assembly no longer scans the Brand Manifest. Manifest access is reserved for explicit `manifest_checked` no-hit resolution.

## Semantic Boundary migration

Qualitative prose may remain prose. Where a precise IS / IS NOT decision boundary materially improves review, use `family: stance`, `kind: semantic-boundary`, `nature: knowledge` and the standard semantic-boundary contract.

## Pre-publication hardening carried into 1.0.0

Before publishing 1.0:

1. add `asOf` to every Build Plan;
2. assign a shared element `subject` wherever multiple scoped elements are alternatives for the same decision; elements without an override relationship may omit it and default to their ID;
3. ensure scope values are strings;
4. validate governed JSON and YAML with duplicate-key rejection and YAML 1.2 boolean semantics;
5. replace rule obligation `allow` with `permit`;
6. ensure every defined RULES element resolves to a rule value contract;
7. confirm every declared Brand Profile is supported by the consuming implementation;
8. reclassify any PATCH containing value, subject, state, scope, validity, classification, addition or removal changes as MINOR or MAJOR as appropriate; and
9. regenerate approval, plan, compiled-context and derived-view hashes after migration.
