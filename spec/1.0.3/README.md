# Open Brand Definition Specification

**An open standard for governed brand truth and AI creation.**

Retrieval finds relevant information. OBDS determines what applies.

```text
Sources
  ↓
Governed Brand Truth
  ↓
Applicability Resolution
  ↓
Required Truth Check
  ↓
Compiled Context
  ↓
Model / Renderer
  ↓
Validation + Evidence
```

RAG can retrieve relevant material. OBDS decides which approved Brand Truth
applies to a declared context: this market, this channel, this output type, at
this point in time. It separates a retrieval miss from truth the brand has
explicitly marked as unknown, not defined or not applicable. When required truth
is unresolved or in conflict, the build fails before a model is called, rather
than producing fluent output from an assumption nobody approved.

## Run it

The repository root is the package root. A clone is directly runnable.

```bash
git clone https://github.com/openbranddefinition/obds.git
cd obds
python -m venv .venv && .venv/bin/pip install -r requirements.txt
export PYTHONPATH=reference/foundation/src
```

`PYTHONPATH` points Python at the uninstalled reference compiler included in
this repository.

Python 3.11 or later. The examples need nothing else; the full conformance
suite additionally needs Node.js 18 or later on `PATH`.

### Foundation minimal: required truth is defined, context is produced

```bash
.venv/bin/python -m obds_ref.cli validate examples/foundation-minimal/manifest.yaml
.venv/bin/python -m obds_ref.cli build examples/foundation-minimal/manifest.yaml examples/foundation-minimal/build-plan.yaml --out /tmp/obds-out
```

Selected fields from the build report the CLI prints, plus what landed on disk:

```text
targetId       brand-query-global-en
status         ready
artifactRef    brand-query-global-en.context.json
artifactHash   sha256:564ca93d7b8aa694a39633b451df2a2d11961e13b17d993353c4c56af0a1849d
requirements   structure.brand  defined  pass
exit           0

/tmp/obds-out  brand-query-global-en.context.json
               brand-query-global-en.context.md
               build-report.yaml
```

One manifest, one element, one target. That is the smallest runnable OBDS example.

### Fail closed: required truth is unknown, nothing is generated

```bash
.venv/bin/python -m obds_ref.cli build examples/fail-closed/manifest.yaml examples/fail-closed/build-plan.yaml --out /tmp/obds-fail
```

```text
targetId       claim-copy-global-en
status         failed
artifactRef    null
requirements   structure.brand         defined  pass
               context.efficacy-claim  unknown  fail
error          OBDS-BUILD-REQUIRED-NOT-DEFINED
exit           2

/tmp/obds-fail build-report.yaml        (no Compiled Brand Context written)
```

Downstream of that, in the runtime rather than the CLI:

```text
model calls    0
decision       build_failed
```

The same shape as the first example with one difference: the brand expects a
value for `context.efficacy-claim` and does not have one. The element carries no
`value` key at all, because a non-defined state must not carry one. It is never
guessed, never widened to a neighbouring scope and never quietly dropped to let
the build succeed. No Compiled Brand Context exists, so there is nothing to
assemble a model input from, so no model is called.

### Full conformance suite

```bash
.venv/bin/python reference/run_all.py
.venv/bin/python reference/release-gate.py
```

Both examples are conformance cases. `reference/foundation/tests/test_examples.py`
asserts the statuses, the reproducible artifact hash, the empty output directory
and the zero model calls shown above, with an instrumented model that records
every call. An example that drifts from the reference implementation fails the
suite.

## The minimum implementation is Foundation

**The minimum OBDS implementation is Foundation.** Nothing beyond it is
mandatory.

```text
Foundation  →  Governed Context  →  Automated Production
```

| Stage | Question it answers | Adds | Reach for it when |
|---|---|---|---|
| **Foundation** *(required)* | What is true? | Brand Elements, the four Brand States, Rules, Scope, Semantic Boundaries, provenance, Value Contracts | always |
| Governed Context | What applies to this task? | Compiled Runtime, Context Delivery, Context Assembly, and with them explicit `asOf`, precedence, declared conflicts, a runtime decision record | several markets, products or campaigns; temporary rules; agents generating without a person in the loop |
| Automated Production | How can creation stay inside governed design boundaries? | Composition and Visual Operations, and with them the design space, omission priority, geometry evidence, deterministic visual checks | something is actually rendered: dynamic HTML, banners, generated PDFs, batch assets |

Three points on one path, not three standards. The capabilities beyond
Foundation are optional, declared, versioned and separately testable, and they
already exist in this release. Section 4.2 of the specification defines the
underlying minimal implementation path. The number of schemas in the package is
not the number of concepts a first implementation has to build.

**Start with Foundation. Add control as the problem grows.**

## What OBDS governs

Approved Brand Truth. Explicit knowledge states. Scope and applicability. Time,
through a declared `asOf`. Precedence and conflicts. Rules. Provenance. The
exact compiled context handed to a model. Optionally claims, localisation,
composition and visual validation. Runtime evidence of what was decided.

## What OBDS is not

Not a vector database. Not a RAG framework. Not an agent framework. Not a prompt
library. Not a DAM, PIM or CMS. Not a renderer. Not a generic enterprise policy
engine.

OBDS is specifically about brand.

## Brand States

Four states, and they are about knowledge only:

```text
defined           the brand has approved this value
unknown           the brand expects a value here and does not have one
not_defined       the brand has deliberately decided not to define this
not_applicable    this does not apply in this scope
```

A retrieval miss is not `unknown`, `unknown` is not a deliberate
`not_defined`, and neither is `not_applicable`. Collapsing them is how a system
ends up inventing brand truth.

A prohibition is an explicit RULE with `obligation: prohibit`, carrying its own
scope, enforcement and validation mode. `prohibited` is not a Brand State.

## Design space

**OBDS defines the permissible design space. The renderer creates inside it.**

A brand can govern composition roles, identity hierarchy, measurement bounds
(floor, ceiling, absolute), clear zones, omission priority and spatial
constraints, and a renderer can then produce any solution that stays inside
them. OBDS carries no layout coordinates. It declares what must hold; the
validator proves the result held it.

## Repository

| Path | What it is |
|---|---|
| [`examples/foundation-minimal/`](examples/foundation-minimal/) | the smallest runnable Foundation example: one manifest, one element, one target |
| [`examples/fail-closed/`](examples/fail-closed/) | the same shape, one required element `unknown`, build fails |
| [`OBDS-1.0.3-IMPLEMENTER-QUICKSTART.md`](OBDS-1.0.3-IMPLEMENTER-QUICKSTART.md) | five concepts, then the smallest conforming implementation |
| [`OBDS-1.0.3.md`](OBDS-1.0.3.md) | the normative specification |
| [`schemas/1.0.0/`](schemas/1.0.0/) | 21 public JSON Schemas, draft 2020-12 |
| [`value-schemas/1.0.0/`](value-schemas/1.0.0/) | 6 public value-contract schemas |
| [`reference/`](reference/) | reference implementation and the seven conformance suites |
| [`OBDS-1.0.3-TEST-RESULT.json`](OBDS-1.0.3-TEST-RESULT.json) | the verified conformance result |

Also: [`CONTRIBUTING.md`](CONTRIBUTING.md) for how to propose a change,
[`OBDS-1.0.3-CHANGELOG.md`](OBDS-1.0.3-CHANGELOG.md) for what moved and what did
not, [`OBDS-1.0.3-MIGRATION.md`](OBDS-1.0.3-MIGRATION.md) if you are on an
earlier release.

### `schemaVersion: 1.0.0` in a 1.0.3 release

Not a mistake, and not a typo to work around. The release version and the schema
contract version are deliberately separate. 1.0.3 changes documentation,
packaging and developer experience only. The normative schema contract has not
moved since 1.0.0, so `schemaVersion` stays `1.0.0` and every schema `$id` still
resolves under `/schemas/1.0.0/` and `/value-schemas/1.0.0/`. The 27 public
contracts are byte-identical across 1.0.0, 1.0.1, 1.0.2 and 1.0.3, and the
release gate fails if that ever stops being true.

## Conformance

```text
107 passed
  0 failed
  0 skipped
```

Seven suites: foundation 27, context-delivery 3, context-assembly 15,
design-space 18, integration 15, golden 6, adversarial 23. No `skipif`, no
`pytest.skip`, no `xfail`; every case runs on every execution. Three adversarial
cases run a Node canonicaliser and compare it byte for byte against the Python
one, so the suite fails rather than skips when Node is missing.

This is a conformance suite, not a certification programme. The published
107/107 result applies to the reference implementation. Independent
implementations may run the applicable official suite to support their own OBDS
conformance claim under section 26.

## Licensing

- Specification and documentation: **CC BY 4.0**
- Schemas, release metadata, reference implementation, conformance suite and examples: **Apache License 2.0**

Commercial implementation is permitted and requires no separate permission.
[`LICENSE.md`](LICENSE.md) has the file-by-file mapping, the unmodified licence
texts are in [`LICENSES/`](LICENSES/), and neither licence grants trademark
rights: see [`TRADEMARKS.md`](TRADEMARKS.md).

---

OBDS 1.0.3, stable, 29 August 2026. Published at
[openbranddefinition.org](https://openbranddefinition.org).
