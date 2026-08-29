# OBDS Changelog

## Release

**Version:** OBDS 1.0.4  
**Status:** Stable  
**Date:** 2026-08-29

## 1.0.4

**Hygiene release. No normative contract change.**

An external research pass on 1.0.3 found two things that a sceptical evaluator
reaches within minutes, and both were about the material around the
specification rather than the specification itself. 1.0.4 closes exactly those
two and nothing else.

**The published conformance result now satisfies section 26 in its own right.**
Section 26 lets an implementation claim conformance only when the result
identifies implementation name and version, suite hash, profile and the passed
and failed counts, and states that no required case was skipped or changed.
`OBDS-1.0.3-TEST-RESULT.json` published the counts and none of the rest, and
the missing identifiers appeared in no other release artefact either. So the
project's own release did not meet the rule it places on every other
implementer. `OBDS-1.0.4-TEST-RESULT.json` now carries:

- `implementation`, with name, version, language and repository;
- `obdsVersion`, the exact version the claim is made for;
- `suiteHash`, a stable identity for the conformance suite that produced the
  result. It covers the suite runner, the seven suite directories and their
  fixtures, and deliberately excludes `reference/foundation/src/`, which is the
  implementation under test and is identified separately;
- `suiteFileCount`;
- `conformanceProfiles`, naming only the profiles this release can defend:
  `obds-foundation` on the declared suite that names it, and `compiled-runtime`
  with a named executed case for every requirement section 26.2 lists. No
  profile is claimed for Context Delivery, Context Assembly, Visual Operations
  or Composition, because those suites exercise modules other than the named
  reference compiler;
- `executedSuites`, reporting every suite the release ran as coverage only,
  with no conformance claim attached;
- `requiredCasesSkippedOrChanged: false`, section 26 clause 4;
- `claimScope`, stating plainly that this is a suite result and not an
  independent certification.

`release-schemas/release-test-result.schema.json` makes every one of these
required, and `reference/release-gate.py` checks them, recomputes the suite
hash from the suite on disk and verifies that the declared profiles account for
every suite with the right case counts. The result cannot quietly fall short of
section 26 again.

**The public material no longer implies that fail-closed is Foundation
behaviour.** The README stated that Foundation is the minimum and nothing
beyond it is mandatory, placed Compiled Runtime in the optional tier, and then
demonstrated `requiresDefined`, the failed target and the absent Compiled Brand
Context under the heading "Foundation minimal". Every mechanism in that
sequence is section 26.2, not 26.1. Section 4.2 of the specification was always
correct; the surrounding material was not.

Corrected in `README.md`, `examples/README.md`, the website and the release
documents:

- Foundation, section 26.1, governs Brand Truth: Brand Elements, the four Brand
  States, semantic subjects, scope, validity, value contracts, reference
  resolution, approved snapshots and canonical hashes;
- Compiled Runtime, section 26.2, adds Build Plans, `requiresDefined`, explicit
  context selection, the rule that a failed target produces no artefact,
  reproducible artefact hashes and Runtime Decision Records;
- both shipped examples carry a Foundation manifest and exercise Compiled
  Runtime. The directory keeps the name `foundation-minimal` because it holds
  the smallest manifest, not because `build` is a Foundation operation.

The fail-closed guarantee itself is unchanged and still mechanically tested: a
failed target writes no artefact, and the instrumented model records zero
calls. Only the capability label was wrong.

**The official Foundation conformance suite was failing, and nothing ran it.**
Found while grounding the profile claim above. `reference/foundation/conformance-suite.yaml`
declares `profile: foundation` and is the only artefact in the package that
names a section 26 profile. It had one failing case, `canonical-hashes`, and the
same failure reproduces from the published 1.0.3 archive. Nothing in the release
path executed it: `run_all.py` runs seven pytest directories and never invokes
`obds conformance`, and the fixture it uses is referenced from nowhere else.

The cause was stale fixture data, not the canonicaliser. Both documents in
`fixtures/canonical-hash-vectors.json` predated the 1.0.0 contract shape: the
manifest was missing `profiles` and `valueContracts`, the artefact was missing
`artifactHash`, `availableElementIds`, `elementRecords` and `contextAssembly`.
Neither would validate against the published schemas, so their stored expected
hashes could not match.

The fixture is now derived from the published `examples/simple` documents in
their current shape. Its expected manifest hash is independently pinned in two
other places the 107-case run already verifies, `approval.contentHash` in the
manifest and `manifestRef.contentHash` in the build plan, so the vector is
cross-checked rather than self-confirming. Its expected artefact hash is the
`artifactHash` the compiler stamps, which `artefact_hash()` excludes from its
own input, so the vector asserts the stamp is self-consistent.

The suite now passes 15 of 15. Three things stop it being omitted again:
`tools/build-release.py` executes it and publishes
`OBDS-1.0.4-FOUNDATION-CONFORMANCE.json`; `reference/release-gate.py`
re-executes it directly and compares the fresh result against the published one
case by case; and the gate's own suite hash covers the fixtures, which the
declarative suite hash does not.

**The two results are not added together.** Fourteen of the fifteen declared
cases exercise the same examples and fixtures as the pytest suites, through the
`obds conformance` harness instead of pytest, so aggregating them would
double-count the same coverage. The 107 stays 107 and the Foundation result is
published separately with its own profile, counts and suite hash. The one
non-duplicated case is `canonical-hashes`.

Unchanged in 1.0.4:

- the normative specification text, apart from its version and filename;
- all 27 public contracts, byte-identical to 1.0.0, 1.0.1, 1.0.2 and 1.0.3;
- `schemaVersion`, which stays `1.0.0`;
- the four Brand States, the capability set and every runtime semantic;
- the 107-case suite and its per-suite counts;
- `spec/1.0.0/`, `spec/1.0.1/`, `spec/1.0.2/` and `spec/1.0.3/`.

## 1.0.3

**Documentation, packaging and developer-experience release. No normative contract change.**

1.0.2 shipped a correct implementation with incorrect prose. The conformance
suite ran 107 cases with 27 in foundation, and several documents kept describing
the 105-case result of 1.0.1. Two documented commands could not be executed at
all. 1.0.3 fixes the documentation and the packaging around an unchanged
contract, and makes the repository itself runnable.

Changed in 1.0.3:

- the reference implementation and the conformance suite are now part of the
  public repository. A clone can install the dependencies, run both examples,
  run all seven suites and run the release gate with no download step;
- the repository root is the package root. The suite and the release gate
  resolve the public schemas in either layout, `schemas/1.0.0/` as published on
  the web or flat `schemas/` as shipped in the release archive, and behave
  identically in both;
- the release gate no longer treats generated local caches as package junk.
  `__pycache__`, `.pytest_cache`, `*.pyc` and a local virtualenv are what
  running the suite produces, so `run_all.py` followed by `release-gate.py`
  now succeeds with no manual cleanup. Shipped junk still fails the gate:
  `.DS_Store`, `Thumbs.db`, editor backups, `__MACOSX`, and any cache file
  listed in `PACKAGE-MANIFEST.json`;
- the release gate judges the package rather than the whole working tree, and
  now verifies every file in `PACKAGE-MANIFEST.json` against its recorded
  sha256 and byte count;
- `examples/README.md` documented `obds build --manifest X --plan Y`, which the
  CLI has never accepted. The correct form is positional,
  `obds build <manifest> <plan> --out <dir>`, and both examples are now
  documented with the exit codes they actually produce;
- `tools/docs-smoke-test.py` executes every command in `README.md`,
  `CONTRIBUTING.md` and `examples/README.md` against the released package and
  fails if a documented command drifts from the CLI or a documented count
  drifts from the release metadata;
- `tools/build-release.py` builds `PACKAGE-MANIFEST.json` and the release
  archive from one file list, so the manifest cannot fall behind the package.

Corrections to statements published in 1.0.2. The 1.0.2 section below is
reproduced as published and is not rewritten; these are the statements it got
wrong, corrected here:

- `OBDS-1.0.2-TEST-REQUIREMENTS.md` was titled `OBDS 1.0.0 Test and Runtime
  Requirements` and declared the run as 105/105 in its introduction, its
  expected output, its release-gate section and its suite-composition table,
  where foundation was listed as 25. The 1.0.2 run was 107 with 27 in
  foundation, as `OBDS-1.0.2-TEST-OUTPUT.txt` and
  `OBDS-1.0.2-TEST-RESULT.json` both record;
- the 1.0.2 changelog lists "the 105-case conformance result" among the things
  1.0.2 did not change. 1.0.2 did change it, from 105 to 107, and its own test
  result says so;
- `README.md` and `CONTRIBUTING.md` printed `# 105 passed` and documented
  running the suite before the release gate, with the virtualenv inside the
  package root. In that order the gate failed on the caches the suite had just
  written and on the virtualenv itself;
- `OBDS-1.0.2-IMPLEMENTER-QUICKSTART.md` was titled `OBDS 1.0.0 Implementer
  Quickstart`.

Not changed in 1.0.3:

- every normative contract;
- all 21 public schemas and all 6 public value schemas, byte for byte, identical
  to 1.0.0, 1.0.1 and 1.0.2;
- every schema `$id`, which continues to resolve under `/schemas/1.0.0/` and
  `/value-schemas/1.0.0/`;
- `schemaVersion`, which remains `1.0.0` because the schema contract did not move;
- the capability registry, the Brand States, precedence, scope resolution,
  conflict handling, `asOf`, the assembled model input slots and the fail-closed
  behaviour;
- the licensing position established in 1.0.2;
- the conformance result: 107 passed, 0 failed, 0 skipped, with the same seven
  suite counts.

`spec/1.0.0/`, `spec/1.0.1/` and `spec/1.0.2/` remain published exactly as
released. None of them is rewritten.

## 1.0.2

**Licensing, packaging and documentation release. No normative contract change.**

1.0.1 replaced the CC BY 4.0 and Apache License 2.0 recommendation with a custom
model: free use for a listed set of purposes, and a separate written commercial
licence for everything else. Those licence documents were drafted but never
published, so the practical effect was that nobody could tell what they were
allowed to build. A specification that cannot be implemented commercially without
asking is not a standard.

1.0.2 replaces that model with two standard licences and publishes them.

Changed in 1.0.2:

- section 32.1 is rewritten. The specification and the documentation are licensed
  under **CC BY 4.0**. The schemas, the release metadata, the reference
  implementation, the conformance suite and the machine-readable examples are
  licensed under the **Apache License 2.0**;
- commercial implementation is permitted and requires no separate permission.
  There is no commercial licence to obtain, no evaluation period and no
  distinction between commercial and non-commercial users;
- the custom Free Use grant and the separate commercial licence requirement are
  removed. So is the draft certification programme as a gate on anything;
- section 32.1 states the modification rule explicitly: a modified specification
  or conformance suite must say it was modified, must not be presented as a
  published OBDS release, and must not reuse a published version identifier;
- the trademark position is separated from the copyright position. Truthful
  compatibility statements need no permission; project naming, logo use and any
  future certification claim are governed by the published trademark policy;
- the package now carries `LICENSE.md`, `LICENSES/CC-BY-4.0.txt`,
  `LICENSES/Apache-2.0.txt`, `NOTICE`, `TRADEMARKS.md`, `GOVERNANCE.md` and
  `CONTRIBUTING.md`. Neither standard licence text is modified;
- the package now carries `examples/`, with a minimal Foundation example and a
  fail-closed example in which required truth is unresolved, no Compiled Brand
  Context is produced and no model is called;
- the release gate additionally proves normative contract identity against 1.0.1,
  not only against 1.0.0.

Not changed in 1.0.2:

- every normative contract;
- all 21 public schemas and all 6 public value schemas, byte for byte, identical
  to both 1.0.0 and 1.0.1;
- every schema `$id`, which continues to resolve under `/schemas/1.0.0/` and
  `/value-schemas/1.0.0/`;
- `schemaVersion`, which remains `1.0.0` because the schema contract did not move;
- the capability registry, the Brand States, precedence, scope resolution,
  conflict handling, `asOf`, the assembled model input slots and the fail-closed
  behaviour;
- the reference implementation and the conformance suite, apart from renamed file
  references and the extended release gate;
- the 105-case conformance result.

`spec/1.0.0/` and `spec/1.0.1/` remain published exactly as released. Section 32
of the 1.0.0 document still carries its original recommendation and section 32.1
of the 1.0.1 document still carries the custom model. Neither is rewritten.

## 1.0.1

**Licensing clarification. No normative contract change.**

Section 32 previously recommended CC BY 4.0 for the specification and documentation and
Apache License 2.0 for schemas, fixtures and reference software. That recommendation did not
match the licensing model under which OBDS is actually published, and it could be read as a
grant of unrestricted commercial use.

Changed in 1.0.1:

- section 32 is renamed from "How the open project is governed" to "How the project is governed";
- OBDS is described as a publicly available, vendor-neutral specification rather than an open standard;
- "reference tooling is open where practical" becomes "reference tooling is published together with the specification";
- the CC BY 4.0 and Apache License 2.0 recommendation is removed;
- a new section 32.1 states the actual use and licensing model: free use for personal,
  educational, academic, non-profit, testing, evaluation and non-production proof-of-concept work,
  including internal evaluation by a commercial organisation; a separate commercial licence for
  paid client work, agency services, consulting, production use, managed services, commercial
  products, commercial redistribution and the sale of OBDS-based deliverables;
- section 32.1 records that the licensing covers the published materials only, not the underlying
  ideas, principles or methods, and that trademarks are reserved separately;
- section 33 and the release artefacts are renamed from 1.0.0 to 1.0.1.

Not changed in 1.0.1:

- every normative contract;
- all 21 public schemas and all 6 public value schemas, byte for byte;
- every schema `$id`, which continues to resolve under `/schemas/1.0.0/` and
  `/value-schemas/1.0.0/`;
- `schemaVersion`, which remains `1.0.0` because the schema contract did not move;
- the reference implementation and the conformance suite, apart from the renamed file
  references they read.

The release gate enforces this: it recomputes a fingerprint over all 27 public contracts and
fails if it differs from the frozen 1.0.0 surface.

OBDS 1.0.0 remains published exactly as released.

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
