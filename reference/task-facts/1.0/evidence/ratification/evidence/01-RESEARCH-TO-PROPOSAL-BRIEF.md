# Research-to-Proposal Brief — Optional Task Facts Contract

**Status:** Frozen proposal input  
**Purpose:** Convert proven experimental evidence into a bounded normative proposal for independent ratification.

## Evidence entering this stage

The Task Facts interoperability experiment reached:

`INTEROPERABLE`

using the approved experimental contract v0.2.

Recorded results:

- 66/66 original frozen decisions matched Python vs Node
- 36/36 frozen regression records matched
- 76/76 independent counter-probe decisions matched
- all compared cross-language hashes agreed
- 16/16 relational identity checks passed
- 120 independently computed bound probe hash checks passed
- both implementations matched 102/102 expected records after outputs were frozen
- source tests: 57 passed
- OBDS modified: NO
- no release created
- nothing published

Isolation was procedural on a shared filesystem, not OS-enforced. A fresh Astra reviewer, two fresh Codex implementers and a separate fresh evaluator performed the roles. Claude Code was unavailable for delegation. Therefore this proves cross-implementation interoperability for the tested evidence set, not a cross-model benchmark.

## Research conclusion

The evidence supports an **optional interoperable contract** for Task Facts / Conditional Applicability.

It does **not** support a Core redesign.

The repeated problem was the portable handoff between:

```text
verified facts about the concrete task/artifact
→ conditional applicability
→ selected governed requirements/dependencies
```

The experiment demonstrated a small interoperable solution for the frozen cases.

## Boundary to preserve

### Brand Scope

Relatively stable applicability context, such as:

- market
- locale
- jurisdiction
- channel
- audience
- product family
- output type

### Task Facts

Facts about the exact requested action or artefact, such as:

- claims actually used
- assets actually used
- partner presence
- campaign identity
- product association
- relevant temporal facts

Task Facts do not themselves prove that a claim is semantically present, that rights exist, or that a caller assertion is true.

## Minimum proven capability

The proposal may include only capabilities already justified by the experiment:

- typed scalar facts
- typed set facts
- multiple independent facts simultaneously
- presence / absence
- equality
- membership
- flat conjunction of independent facts
- distinct missing / empty / unknown / contradictory states
- provenance / verification status
- limited associations needed by the proven cases
- deterministic task snapshot binding and hashing
- date vs date-time distinction
- unresolved timezone preservation
- deterministic routing/error binding
- deterministic structural error classification

## Proven structural clarifications from v0.2

The normative proposal must preserve the v0.2 decisions for:

1. validation-stage order:
   - strict JSON transport parse
   - canonicalisation / TFJ validation
   - routing validation
   - typed snapshot / verification / condition validation
   - applicability evaluation

2. routing/error binding:
   - bound per-decision INVALID when routing identity and canonical snapshot identity remain available
   - unbound INVALID only when routing or canonical identity cannot be determined

3. duplicate IDs:
   - duplicate case ID => unbound `INVALID / DUPLICATE_ID`
   - duplicate condition ID => unbound `INVALID / DUPLICATE_ID`

4. raw input classification:
   - syntactically invalid JSON such as NaN => `INVALID / JSON_PARSE_ERROR`
   - syntactically valid but non-canonical/TFJ-invalid input => `INVALID / NON_CANONICAL_INPUT`

## Must remain out of scope

- generic policy language
- arbitrary code
- regex policy language
- workflow engine
- NLP semantic-claim detection
- automatic legal truth determination
- automatic rights truth determination
- new brand ontology
- OBDS Core redesign
- any claim that task facts are true merely because supplied by a caller

## Ratification question

The council must decide:

> Should the proven experimental Task Facts contract become an official optional OBDS contract without changing existing OBDS Core semantics?

The answer must be evidence-based.

A ratification does not itself publish a release.
