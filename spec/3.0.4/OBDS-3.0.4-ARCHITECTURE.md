# OBDS 3.0 Architecture

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


The runtime artefact carries two hashes with two jobs. `artifactHash` identifies
the exact artefact, including its rendered slots, token counts and compiler
provenance, so two implementations that render governed truth differently produce
different artefacts and different hashes. `governedResultHash`, defined in section
14.3a, identifies the governance decision underneath: which manifest, which target,
which approved truth applied, in which states. It is the value two independent
implementations must agree on for the same manifest and Build Plan.

3.0 adds no box to the diagram above. What it changes is the contract on each
arrow. Reading is one governed input contract at every reader and every entry
point of each. Identity is one coordinate system across the four governed
artefact kinds, and an artefact that names another artefact's manifest binds
`id`, `version` and `contentHash` together. Conflict relevance is decided once,
by the compiler, and consumed downstream rather than re-derived. Every consumer
that derives a governed decision validates the published contract, reproduces the
required hashes and binds the required identities before reading a field.

A declared hash is not verified integrity. Reproduction proves a payload is
intact; identity binding proves it is the payload this decision is about. A
governed decision needs both, and they are two questions.
## Semantic control

FACTS say what is true. RULES say what is required or prohibited. STANCE semantic boundaries say how the brand is and how it is not. Brand States say whether the relevant knowledge is defined.

## Boundary

OBDS defines approved truth, constraints, relationships and evidence contracts.

Implementations decide models, prompts, routing, coordinates, HTML, CSS, rendering strategy and execution infrastructure.

> **One specification. One Foundation. Optional capabilities.**

## 1.0.0 execution identity

A deterministic build is identified by the approved Manifest, the Build Plan including `asOf`, the compiler version and the declared schemas and validators. Scoped alternatives share one semantic `subject`; the compiler resolves specificity or fails on conflict before emitting the Compiled Brand Context.
