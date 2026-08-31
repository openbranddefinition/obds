# Open Brand Definition

**OBDS 1.1.4** is the stable Open Brand Definition Specification.

It defines a vendor-neutral control layer for approved brand truth used by AI systems and renderers.

## Model

**One specification. One Foundation. Optional capabilities.**

The Foundation defines Brand Elements, knowledge states, rules, value contracts, scope, provenance and integrity. Optional capabilities add Context Assembly, Claims, Localisation, Composition and Visual Operations.

FACTS say what is true. RULES say what is required or prohibited. Semantic Boundaries say how the brand is and how it is not. Unknown stays unknown.

OBDS does not define agents, model routing, HTML, CSS, layout coordinates or renderer code.

For dynamic rendering:

> **OBDS defines the permissible design space. The renderer creates one solution inside it. The validator proves that it stayed inside.**


## Status

**OBDS 1.1.4. Stable. 2026-08-31.**

OBDS 1.1 is the independent-implementability release.

An independent implementation, written blind from the public documents, reproduced eight published OBDS hashes on its first attempt and then could not reproduce `artifactHash`. The cause was not a defect in the canonicaliser. OBDS defined no payload that two implementations were required to produce identically, so there was nothing to be interoperable about.

1.1 adds that: `governedResultHash`, section 14.3a. It carries the governance decision — which manifest, which target, which truth applied, in which states — and two independent implementations given the same manifest and the same Build Plan must produce the same value, whatever their prose, compiler, tokenizer or token counts. `artifactHash` keeps its 1.0 meaning unchanged and still identifies the exact artefact.

Section 10.2 precedence is now stated once and decidably. The scope vocabulary is closed at nine dimensions. The tokenizer, the validator registry and the four build failure codes are defined rather than inferred. Required truth now always reaches the artefact.

The OBDS 1.0.0 contract surface remains frozen and byte-identical across 1.0.0, 1.0.1, 1.0.2, 1.0.3 and 1.0.4. OBDS 1.1 adds one versioned contract beside it, `schemas/1.1.0/compiled-context.schema.json`, and changes none of them.

184 conformance cases pass, 0 fail, 0 skip. The official declared Foundation conformance suite is 15 of 15 and is reported separately.

## Use and licensing

Two standard licences, neither of them modified.

- **Specification and documentation: CC BY 4.0.**
- **Schemas, release metadata, reference implementation, conformance suite and examples: Apache License 2.0.**

Commercial implementation is permitted and requires no separate permission. There is no commercial licence to obtain and no evaluation period. Section 32.1 has the detail, `LICENSE.md` has the file-by-file mapping, and the full licence texts are in `LICENSES/`.

Neither licence grants trademark rights. Truthful compatibility statements such as "implements OBDS 1.0" need no permission. Project naming, logo use and any future certification claim are governed by `TRADEMARKS.md`. No certification programme is live.
