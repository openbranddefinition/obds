# OBDS 0.9.9 to 1.0.0 Migration

1. Set `schemaVersion` to `1.0.0`.
2. Use the single current specification document.
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

## 1.1.4 to 1.1.5

No schema changed and no manifest change is required.

The one observable change is that a manifest whose applicable RULE declares a
`requiresDefinedRefs` dependency that does not resolve to `defined` now fails
manifest validation or the target build. Such a manifest was already outside the
specification; the reference compiler simply did not say so.

## 1.1.3 to 1.1.4

No migration work. No schema changed and no manifest change is required.

Scope values are now normalised to Unicode NFC when they are compared, as section
9 already required. A consumer can observe a behavioural change only if a manifest
currently relies on an NFD scope value failing to match its canonically equivalent
NFC value. That manifest was already broken; 1.1.4 makes the required comparison.

## 1.0.4 to 1.1

No migration work for a manifest. Manifests stay at `schemaVersion: 1.0.0` and no
element contract changed.

For an implementation, four things:

1. **Emit `governedResultHash`** per section 14.3a and declare
   `schemaVersion: 1.1.0` on the Compiled Brand Context. Validate it against
   `schemas/1.1.0/compiled-context.schema.json`. The 1.0.0 contract is unchanged
   and 1.0 artefacts remain valid 1.0 artefacts.
2. **Check your precedence reading.** Section 10.2 now states the rule as strict
   subset inclusion on matched targets. If you read the old wording as
   "restricts more dimensions" you resolved some manifests as hard conflicts that
   1.1 resolves to a winner. Run `precedence-vectors` before assuming you agree.
3. **Check that required truth reaches your artefact.** If your context
   selection could drop an element named in `requiresDefined`, it was producing
   an incomplete context. Section 13.2 now says so explicitly.
4. **Adopt the four required-truth error codes** from section 13.1a if you
   report build failures.

`artifactHash` for an unchanged manifest and plan will move, because the artefact
gained a field and a schema version. That is expected across a version change.
Section 16.1 approvals bind the artefacts they were issued against; a rebuild
under 1.1 is a new artefact and needs its own approval.

## 1.0.3 to 1.0.4

No migration work. 1.0.4 changes release metadata and documentation only.

- No schema, no `$id`, no `schemaVersion` and no capability semantic changed.
- The public schema surface is byte-identical to 1.0.0, 1.0.1, 1.0.2 and 1.0.3.
- An implementation that conforms to 1.0.3 conforms to 1.0.4 with no work.

Two things are worth knowing.

First, if you publish your own conformance result, section 26 requires it to
identify the implementation by name and version, the suite by hash, the profile
and the counts, and to state that no required case was skipped or changed.
`OBDS-1.0.4-TEST-RESULT.json` is now a worked example of a result that meets
that rule, and `release-schemas/release-test-result.schema.json` is the shape
to validate against. A 1.0.3-era result that carried only counts should be
reissued.

Second, if your documentation repeated the OBDS pitch, check the same thing
1.0.4 corrected. `requiresDefined`, a failed target producing no Compiled Brand
Context and therefore no model call is Compiled Runtime, section 26.2. It is
not Foundation-only behaviour. Foundation, section 26.1, governs Brand Truth.
Nothing about the guarantee changed; only its label.

## 1.0.2 to 1.0.3

No migration work. 1.0.3 changes documentation, packaging and developer
experience only.

- No schema, no `$id`, no `schemaVersion` and no capability semantic changed.
- The public schema surface is byte-identical to 1.0.0, 1.0.1 and 1.0.2.
- An implementation that conforms to 1.0.2 conforms to 1.0.3 with no work.
- The only thing an implementer has to know is that documented commands have
  changed: `obds build` takes the manifest and the plan positionally, and the
  release gate now runs cleanly after the conformance suite.

## 1.0.1 to 1.0.2

No migration work. 1.0.2 changes licensing, packaging and documentation only.

- No manifest changes. No schema changes. No `$id` changes.
- `schemaVersion` stays `1.0.0`.
- An implementation that conforms to 1.0.1 conforms to 1.0.2 with no work.
- What changed for you is permission, not code: the specification and the
  documentation are now CC BY 4.0, and the schemas, the reference implementation,
  the conformance suite and the examples are now Apache License 2.0. Commercial
  implementation needs no separate permission.
- If you were waiting on a commercial licence before shipping, you are not
  waiting on anything any more.
