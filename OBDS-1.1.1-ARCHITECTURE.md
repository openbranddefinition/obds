# OBDS 1.1 Architecture

```text
SOURCES
Brandbooks / PIM / DAM / Legal / approved decisions
        |
        v
OBDS FOUNDATION
Brand Manifest / Elements / States / Rules / Value Contracts / Provenance
        |
        +-----------------------------+
        |                             |
        v                             v
OPTIONAL CAPABILITIES            BUILD CONFIGURATION
Context / Claims /               targets / required truth /
Composition / Visual /           token budgets / policies
Localisation / Operations             |
        |                             |
        +-------------+---------------+
                      v
                 COMPILER
                      |
                      v
          COMPILED BRAND CONTEXT
                      |
             +--------+---------+
             |                  |
             v                  v
       CONTEXT ASSEMBLY     RENDER LAYER
             |                  |
             v                  v
      MODEL INPUT PACKAGE   GEOMETRY EVIDENCE
             |                  |
             v                  v
          AI / AGENTS       VISUAL VALIDATION
             |                  |
             +--------+---------+
                      v
              RUNTIME DECISION
```


OBDS 1.1 adds one value to the runtime artefact: `governedResultHash`, defined in
section 14.3a. `artifactHash` identifies the exact artefact, including its rendered
slots, token counts and compiler provenance, so two implementations that render
governed truth differently produce different artefacts and different hashes.
`governedResultHash` identifies the governance decision underneath: which manifest,
which target, which approved truth applied, in which states. It is the value two
independent implementations must agree on for the same manifest and Build Plan, and
the only architectural addition in the 1.1 line.
## Semantic control

FACTS say what is true. RULES say what is required or prohibited. STANCE semantic boundaries say how the brand is and how it is not. Brand States say whether the relevant knowledge is defined.

## Boundary

OBDS defines approved truth, constraints, relationships and evidence contracts.

Implementations decide models, prompts, routing, coordinates, HTML, CSS, rendering strategy and execution infrastructure.

> **One specification. One Foundation. Optional capabilities.**

## 1.0.0 execution identity

A deterministic build is identified by the approved Manifest, the Build Plan including `asOf`, the compiler version and the declared schemas and validators. Scoped alternatives share one semantic `subject`; the compiler resolves specificity or fails on conflict before emitting the Compiled Brand Context.
