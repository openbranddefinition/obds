# OBDS 3.0.2 Implementer Quickstart

## Start with five concepts

1. **Brand Manifest**: governed Brand Truth.
2. **Brand Element**: one scoped fact, rule, context item, stance or known state.
3. **Value Contract**: the machine-readable contract for a structured value. It binds shape, semantic schema and optional deterministic validation.
4. **Build Plan**: declares `asOf`, the target, required truth and optional Context Assembly policy.
5. **Runtime evidence**: records what was compiled, assembled, checked, rendered or decided.

## Smallest implementation

Support `obds-foundation`, section 26.1:

- parse the manifest;
- validate IDs, effective subjects, states, string-only scope and references;
- resolve every required `valueContractRef`;
- verify `shapeHash`, `schemaRef`, `schemaHash` and any declared value-contract validator;
- reject an element whose own contract does not resolve; and
- preserve canonical hashes.

Brand States describe knowledge only: `defined`, `unknown`, `not_defined`, `not_applicable`. A prohibition is always an explicit RULE with `obligation: prohibit`.

That much answers *what is true, and what the brand has explicitly declared it
does not know*. It does not yet refuse to produce anything.

Add `compiled-runtime`, section 26.2, when the build must refuse:

- read a Build Plan with an explicit `asOf`;
- resolve `requiresDefined` against the applicable elements;
- fail the target when required truth is missing, `unknown`, `not_defined`, out
  of scope, expired or conflicting;
- write **no** Compiled Brand Context for a failed target, so nothing downstream
  has anything to assemble a model input from; and
- record the outcome in a Runtime Decision Record.

This is where the fail-closed guarantee lives. A Foundation-only implementation
holds governed truth with explicit unknowns; it does not run this gate.

Add Context Delivery, Context Assembly, Composition, Visual Operations, Claims or Localisation only when the product needs them.

## Context Assembly

Normal assembly starts from one validated Compiled Brand Context. It does not rescan the manifest to reconstruct target scope or hard boundaries. Exact manifest access is reserved for the declared `manifest_checked` no-hit resolution path.

## Semantic boundaries

Use `stance / semantic-boundary` for structured qualitative IS / IS NOT guidance. It can support `material_conflict` or `opportunity`. Only a separate RULE creates a violation.

## Release safety

A PATCH release is limited to source-reference or annotation corrections. Value, subject, state, scope, validity, classification, shape and contract changes require at least MINOR. The Manifest Change Report keeps those change classes separate.

> Start with Foundation. Add only the capabilities your implementation can prove.

## Deterministic time and precedence

- Every Build Plan has a timezone-aware `asOf`.
- Element validity is evaluated against `asOf`, never the compiler clock.
- Element `subject` is the precedence key. If omitted it defaults to the element ID.
- More specific scope wins within one subject. Incomparable maximal candidates fail the build.
- Runtime rejects a Compiled Brand Context outside its declared validity window.

## Strict interchange

- Governed JSON and YAML reject duplicate keys.
- A governed document has an object root. A sequence, a scalar or an empty
  document is not governable.
- YAML uses YAML 1.2 boolean semantics, and the ambiguous plain-scalar forms of
  section 28.1 are rejected rather than resolved either way.
- Scope values are strings.
- OBDS Canonical Number v1 makes integral values such as `1` and `1.0` hash identically and pins non-integral binary64 serialisation.
- **One reader, every entry point.** A path-taking reader and a bytes-taking
  reader are one contract with two doors. If your release gate, your conformance
  runner or your test suite reads governed documents with a different parser than
  your compiler, you have two contracts and one of them will bless a document the
  other refuses.

## Governed decisions from received documents

Before reading any field of a Compiled Brand Context, a Model Input Package or a
Review Result:

1. parse it under the governed input contract;
2. validate it against its published contract;
3. reproduce every required hash from the payload it describes; and
4. bind every required identity to the artefact upstream.

Reproducing a hash proves the document is intact. It does not prove the document
is the one this decision is about: bind `manifest.id`, `manifest.version`,
`manifest.contentHash` and `targetId` as well. Comparing two supplied values is
neither, and must not be described as verification.

Fail closed: an invalid governed document produces a governed rejection with a
Runtime Decision Record, never an uncontrolled exception and never a model call.

## Do not invent a missing parameter

A compiled check carries every parameter that changes its outcome. If one is
absent, refuse the check. Supplying `case_insensitive` for a missing `match` is
not a default, it is a governed decision the artefact never stated.

## Canonical and token safety

- Use the release Canonical JSON implementation or reproduce its cross-language vectors exactly.
- Reject duplicate keys and integers that cannot round-trip through binary64.
- Do not claim a tokenizer you do not execute. The reference `obds:whitespace-v1` tokenizer is deterministic but intentionally model-agnostic.
- Keep canonical Brand Truth rich; keep the model projection compact and hashed.
