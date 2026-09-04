# Open Brand Definition

**OBDS 3.0.4** is the stable Open Brand Definition Specification.

It defines a vendor-neutral control layer for approved brand truth used by AI systems and renderers.

## Model

**One specification. One Foundation. Optional capabilities.**

The Foundation defines Brand Elements, knowledge states, rules, value contracts, scope, provenance and integrity. Optional capabilities add Context Assembly, Claims, Localisation, Composition and Visual Operations.

FACTS say what is true. RULES say what is required or prohibited. Semantic Boundaries say how the brand is and how it is not. Unknown stays unknown.

OBDS does not define agents, model routing, HTML, CSS, layout coordinates or renderer code.

For dynamic rendering:

> **OBDS defines the permissible design space. The renderer creates one solution inside it. The validator proves that it stayed inside.**


## Status

**OBDS 3.0.4. Stable. 2026-09-04.**

OBDS 3.0 is the Semantic Closure release.

It adds no Brand State, no profile, no capability and no architecture. It closes five places where one governed semantic was stated once and implemented twice, so that two conforming readers, two entry points or two executors could reach different governed answers from the same approved bytes.

- **Governed input.** One interchange contract at every governed reader and every entry point of each, including the rule that a governed document has an object root.
- **Governed identity.** One coordinate system across the four governed artefact kinds. Where an artefact names another artefact's manifest it binds `id`, `version` and `contentHash` together. Carriage return and line feed are refused at an identity position because canonicalisation cannot tell them apart; NEL, LINE SEPARATOR and PARAGRAPH SEPARATOR are preserved.
- **RULE enforcement.** A deterministic Foundation RULE declares at least one registered Foundation check, rule-level `validatorRef` is removed, and a check is validated where it is written as well as where it is executed.
- **Runtime contract enforcement.** Every governed document is validated against its published 3.0 contract before any field of it is read, and every required hash is reproduced from its payload rather than compared between two supplied claims.
- **Conflict relevance.** One relevance model, decided once by the compiler and consumed downstream rather than re-derived.

3.0.1 is a packaging correction on top of it: the release archive now carries the tooling needed to reproduce the documented standalone checks. 3.0.2 is an outreach-gate correction on top of that: the compiler and the runtime were brought back to two contracts 3.0 already publishes, section 10.2a conflict relevance and section 26.2 exact target loading, and the README quickstart publishes a hash the documented command reproduces. 3.0.3 is a documentation and public-surface neutrality patch on top of that: one sector-specific example value in the section 9 Scope example became a neutral placeholder. 3.0.4 is a documentation and public-positioning patch on top of that: the current public wording calls OBDS an open specification rather than an open standard. No normative contract changed in any of the four.

Each of the five closures is a breaking correction to an existing normative contract, which is why 3.0.0 is MAJOR. For most projects the migration is the Build Plan and nothing else: `schemaVersion: 3.0.0`, and `stateMap` and `styleTexture` stated on every target.

`schemas/3.0.0/` publishes the Build Plan, Compiled Brand Context and Runtime Decision Record contracts, and `value-schemas/3.0.0/` publishes the RULE value contract. The OBDS 1.0.0 contract surface remains frozen and byte-identical across every release so far, and the 1.1.0 contract published beside it is unchanged.

1079 conformance cases pass, 0 fail, 0 skip. The official declared Foundation conformance suite is 23 of 23 and is reported separately.

## Use and licensing

Two standard licences, neither of them modified.

- **Specification and documentation: CC BY 4.0.**
- **Schemas, release metadata, reference implementation, conformance suite and examples: Apache License 2.0.**

Commercial implementation is permitted and requires no separate permission. There is no commercial licence to obtain and no evaluation period. Section 32.1 has the detail, `LICENSE.md` has the file-by-file mapping, and the full licence texts are in `LICENSES/`.

Neither licence grants trademark rights. Truthful compatibility statements such as "implements OBDS 3.0" need no permission. Project naming, logo use and any future certification claim are governed by `TRADEMARKS.md`. No certification programme is live.
