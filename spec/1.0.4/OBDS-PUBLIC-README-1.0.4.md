# Open Brand Definition

**OBDS 1.0.4** is the stable Open Brand Definition Specification.

It defines a vendor-neutral control layer for approved brand truth used by AI systems and renderers.

## Model

**One specification. One Foundation. Optional capabilities.**

The Foundation defines Brand Elements, knowledge states, rules, value contracts, scope, provenance and integrity. Optional capabilities add Context Assembly, Claims, Localisation, Composition and Visual Operations.

FACTS say what is true. RULES say what is required or prohibited. Semantic Boundaries say how the brand is and how it is not. Unknown stays unknown.

OBDS does not define agents, model routing, HTML, CSS, layout coordinates or renderer code.

For dynamic rendering:

> **OBDS defines the permissible design space. The renderer creates one solution inside it. The validator proves that it stayed inside.**


## Status

**OBDS 1.0.4. Stable. 2026-08-29.**

1.0.4 is a hygiene release. No normative contract changed, and the public schema surface is byte-identical to 1.0.0, 1.0.1, 1.0.2 and 1.0.3.

It corrects two things the specification itself already had right and the surrounding material did not.

The published conformance result now satisfies section 26 in its own right: it identifies the implementation by name and version, the conformance suite by hash, the profiles the executed cases provide evidence for, and the passed, failed and skipped counts, and it states that no required case was skipped or changed. The release gate verifies every one of those and recomputes the suite hash, so the result cannot silently fall short of the rule the specification places on every implementer.

The public material no longer implies that the fail-closed build gate is Foundation behaviour. Foundation, section 26.1, governs Brand Truth. Compiled Runtime, section 26.2, adds Build Plans, `requiresDefined`, the rule that a failed target produces no artefact, and Runtime Decision Records. The guarantee is unchanged and still mechanically tested; only its capability label is now correct.

## Use and licensing

Two standard licences, neither of them modified.

- **Specification and documentation: CC BY 4.0.**
- **Schemas, release metadata, reference implementation, conformance suite and examples: Apache License 2.0.**

Commercial implementation is permitted and requires no separate permission. There is no commercial licence to obtain and no evaluation period. Section 32.1 has the detail, `LICENSE.md` has the file-by-file mapping, and the full licence texts are in `LICENSES/`.

Neither licence grants trademark rights. Truthful compatibility statements such as "implements OBDS 1.0" need no permission. Project naming, logo use and any future certification claim are governed by `TRADEMARKS.md`. No certification programme is live.
