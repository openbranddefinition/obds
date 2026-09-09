RATIFIED WITH NON-BLOCKING FINDINGS

Final ratification record — 2026-09-08. Completed one proposal/review cycle of a maximum of two.

## Decision and identities

- Final proposal: `proposal/candidate-v1/`, candidate-v1. Proposed capability designation: Task Facts 1.0; snapshot payload 0.1 and TFJ-0.1 remain unchanged.
- Evidence package: `evidence/`, containing the copied frozen interoperability run, frozen brief, verification and reproduction records.
- Evidence inventory: `reports/evidence-inventory.json`; SHA-256 `256adf3d4a46d9c4af172c3d3d162b779af68c65d51377530d9c670952c493d9`. This hashes the inventory's raw bytes; the inventory maps every evidence file to its raw-byte SHA-256.
- Final candidate inventory: `reports/candidate-v1-inventory.json`; SHA-256 `a9468438d4aba8531829cd5c03355d0ead2a263aec17b692c350d4e161b0edf1`. This inventory covers all 54 candidate files, including its package manifest.
- Candidate package manifest: `proposal/candidate-v1/PACKAGE-MANIFEST.json`; SHA-256 `95877c7effb1fc3f42ef1b904ab955160c42ad7afeb4cece18dff79fc539ef94`; all 53 self-excluding entries verified.
- Semantics reviewer: APPROVE WITH NON-BLOCKING FINDINGS — `reviews/semantics-review.md`.
- Conformance reviewer: APPROVE WITH NON-BLOCKING FINDINGS — `reviews/conformance-review.md`.
- Ratifier: RATIFY WITH NON-BLOCKING FINDINGS — `ratification/ratifier-verdict.md`; SHA-256 `b5a62adcc95e2194ca9bd695c7d68ff7261e3be2168db9855803dfebdabdea76`.
- Reviews inventory SHA-256: `8c89a4e617a4471649bab7912ca7cbccf30dc4dfac5006fd778b046cb69a3499`.

The independent ratifier accepts the proposal for an official optional evaluator contract within its bounded scope. This record does not register a capability or change the published specification. Author, reviewers and ratifier were separate fresh subagents with no inherited conversation context and restricted input assignments. Isolation was procedural on a shared filesystem, not OS-enforced. No Gemini was used. See `reports/orchestration.json` and each role's provenance statement.

## Exact proposed normative surface

The adopted proposal surface is the frozen candidate's `TASK-FACTS-CONTRACT.md`, `schemas/task-facts.schema.json`, `NORMATIVE-DELTA.md` and proposed conformance obligations in `CONFORMANCE-IMPACT.md`. Other supporting documents are informative. The complete frozen files, not this summary, define the requirements.

The addition is one optional evaluator capability, proposed ID `task-facts`. Full claimants implement the complete typed scalar/set model, simultaneous facts, presence/absence, equality, membership, flat conjunction, distinct missing/empty/unknown/contradictory states, provenance and accepted-evidence binding, bounded partial-function associations, complete snapshot hashing, date/instant distinction and unresolved temporal basis. Strict transport parsing precedes complete-document TFJ validation, routing/uniqueness, ordered bound validation, then applicability. Bound/unbound errors, duplicate-ID family suppression, reason codes, six-field results and snapshot identities preserve the proven semantics.

Consumers retain exact snapshots, conditions, verification contexts and decisions. Trusted hosts supply verification context independently of callers; fact presence and accepted hashes do not prove truth. UNKNOWN, CONTRADICTORY and INVALID do not grant permission. False conditions cannot remove existing static requirements. TFJ identity cannot replace existing governed hashes. No fields or semantics are added to current manifests, Build Plans, Model Input Packages, Runtime Decision Records or build reports. Production adapters and wire bindings remain outside this normative claim.

## Explicit non-goals

Generic policy or arbitrary Boolean languages; regex policy logic; arbitrary code; workflow engines; NLP claim detection; legal/rights truth engines; new brand ontology; Core redesign; general relations/joins; interval predicates; timezone databases; authentication protocols; automatic inventory extraction or completeness proof; production integration conformance. Research and ratification do not establish source truth, exhaustive correctness, production readiness or cross-model benchmarking.

## Compatibility, conformance and versioning

The reviewed public baseline is OBDS 4.0.4 at repository commit `e3464b5f863897260118b6c338a1061e9382c845`, captured in the candidate's baseline sources and independently checked by the conformance reviewer. The older GitHub latest-release entry does not supersede that published specification baseline.

All existing valid packages remain valid because acceptance rules, existing schemas, governed hashes, Brand States, Scope, precedence, Value Contracts and exact-element dependencies remain unchanged. Foundation and existing capability claims gain no mandatory obligation; the evaluator is explicitly invoked and separately claimed. This is a demonstrated normative surface comparison, not exhaustive execution of all possible packages.

New voluntary evaluator claims require complete prose/schema behavior, exact contract and suite identification, and full six-field results preserving 66 fixture decisions and 36 regression records. Schema-only or partial support cannot claim full evaluator conformance, and the vectors cannot substitute for Foundation, Compiled Runtime or production integration conformance. Official suite registration remains later governed work.

Versioning recommendation: **MINOR, prospective 4.1.0 from 4.0.4, explicitly accepted by the final ratifier.** The addition exceeds PATCH clarification and breaks no existing normative contract to require MAJOR. This proposal is not a released OBDS 4.1.0. A changed baseline, mandatory adoption, new wire binding or expanded release delta requires renewed impact analysis.

## Non-blocking findings and later-work boundaries

1. **S-N1 — adoption status:** provide an adoption wrapper or documentation statement alongside the retained experimental/non-normative schema title. Preserve frozen schema provenance and snapshot/TFJ identities.
2. **C1 — runnable conformance and evidence distribution:** before official suite distribution, package a minimal language-neutral runner/comparison command preserving raw invalid bytes, ordered six-field comparisons, envelope/exit behavior, suite identity and machine-readable results. Preserve or package externally referenced evidence so distributed claims remain auditable. Do not change the frozen vectors.
3. **Production integration limitation:** before any production integration claim, separately verify the trusted verifier boundary, artifact/package rebinding, condition/context retention, selected/static dependency handling and compiler/runtime controls. New wire bindings or expanded semantics require fresh review. This run authorizes none of that implementation.

The ratifier explicitly determined that these findings do not undermine evaluator interoperability or backward compatibility.

## Evidence verification and unchanged-state record

The original research status is INTEROPERABLE. Source, contract and implementation inventories, package manifests, implementer ZIP and frozen evaluation result digests reverified. Copied unchanged Python and Node executables reproduced all 66 fixture, 36 regression and 76 counter-probe records per implementation exactly. All 57 source tests passed. The ratifier additionally verified every evidence/candidate/review inventory entry and all 33 packaged schema/vector files against frozen experimental counterparts.

`reports/verify_integrity.py` verifies the entire original research tree, copied evidence tree and frozen candidate; `reports/final-integrity-check.txt` records the final audit. Original research files remain byte-identical to the initial inventory. Review digests also reverified before this final record.

- Whether OBDS was modified: **NO**.
- Whether `_autonomous_interop_run/` was modified: **NO**.
- Whether anything was merged or tagged: **NO**.
- Whether anything was published/released: **NO**.
- Implementation performed in this run: **NO**.

## Only next authorised step

> Prepare a separate implementation/release plan for the ratified proposal.

Do not implement or release the proposal in this run. Workflow complete.
