# OBDS 1.0.0 Changelog

## Release

**Version:** OBDS 1.0.0  
**Status:** Stable  
**Date:** 2026-08-27

## The 1.0 decision

OBDS has one normative specification, one required Foundation and optional capabilities. The separate CORE specification is retired.

> **One specification. One Foundation. Optional capabilities.**

## Changed from 0.9.9

- `OBDS-CORE` is no longer a separate normative document.
- `CORE Check Registry v1` is renamed `Foundation Check Registry v1`.
- every 1.0 manifest declares `obds-foundation`.
- existing Context Delivery, Design Space and Visual Operations concepts remain part of the single specification.

## Pre-release history

The sections below record the pre-release hardening cycles that led to 1.0.0. They are history. The released contract is OBDS 1.0.0 stable.

### RC3 integrity and decision hardening

- Brand States now describe knowledge only: `defined`, `unknown`, `not_defined`, `not_applicable`.
- prohibition has one Brand Truth path: an explicit RULE with `obligation: prohibit`.
- Context Assembly now starts from the validated Compiled Brand Context and cannot reconstruct normal target truth from the manifest.
- Compiled Brand Context carries target-scoped `elementRecords`, `availableElementIds` and its Context Assembly policy.
- Model Input Packages require a non-null `compiledContextHash`.
- Runtime Decision Record schema and reference runtime now agree on `assembly_failed`, `assemblyHash` and `modelInputHash`.
- Value Contracts now bind `valueContractRef`, `shapeHash`, `schemaRef`, `schemaHash` and optional `validatorRef`.
- `stance / semantic-boundary` standardises qualitative IS / IS NOT guidance without turning guidance into compliance.
- the release suite includes enum synchronisation tests and a Golden end-to-end pipeline test.

## Release safety

- canonical hashes prove approved bytes;
- shape hashes prove machine structure;
- schema hashes pin the semantic contract;
- validators prove additional deterministic invariants; and
- PATCH releases are limited to source-reference or annotation corrections and cannot change Brand Truth or runtime applicability.

Breaking contract changes after publication require OBDS 2.0.

### RC4 deterministic execution hardening

- added explicit Build Plan `asOf`; compiler selection no longer depends on wall-clock time;
- Compiled Brand Context now carries `build.asOf` and a runtime-enforced validity window;
- added an effective element `subject` key for machine-decidable precedence and conflict resolution; omitted `subject` defaults to the element ID;
- implemented scope-specific winner selection and hard conflicts for incomparable maximal elements of one subject;
- pinned OBDS Canonical Number v1 and added Python-to-JavaScript interoperability vectors;
- strict JSON and YAML loaders reject duplicate keys; YAML uses 1.2 boolean semantics; scope scalars are strings only;
- failed `require_approval` checks now withhold output and route to `approval_required`;
- invalid `phase` / `appliesTo` combinations fail validation;
- every defined RULES element requires a rule value contract regardless of nature;
- unsupported declared Brand Profiles fail closed;
- PATCH eligibility now rejects value, scope, state, validity, subject, classification, contract, addition and removal changes;
- measurement `min > max` fails;
- Composition conformance requires every `neverOmit` role in geometry evidence;
- aligned rule obligation vocabulary on `permit`;
- added root dependency declaration and removed platform metadata from release packaging;
- added 16 adversarial regression tests covering the RC3 review findings.

### RC5 final hardening

- unified Canonical JSON code across Foundation, Context Delivery and Context Assembly and added byte-drift tests;
- aligned canonical number serialisation with ECMAScript / RFC 8785 thresholds;
- pinned object-key ordering to UTF-16 code units and added non-BMP vectors;
- rejected wider integers that cannot round-trip through IEEE-754 binary64;
- made unsupported tokenizer declarations fail closed;
- internalised the legacy `colour-hex` fixture schema;
- compacted Reasoning Chapter rendering and model-facing HARD_BOUNDARIES;
- removed duplicated exact chapter blocks from the model input projection;
- retained explicit empty Rule fields in canonical Brand Truth because exact value-shape contracts make omission structurally significant; empty plumbing is removed only from the runtime model projection;
- added canonicalisation, tokenizer and payload regression tests.

## 1.0.0 stable promotion

The final pre-release contract was promoted to stable 1.0.0 after the complete release gate passed. No normative changes were made during promotion.
