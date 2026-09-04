# Open Brand Definition Specification

**An open, implementation-ready specification for governed brand truth and AI creation.**

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

Python 3.13 or later, because section 14.3c pins Unicode 15.1.0 and CPython 3.13
is the first release carrying that database. The examples need nothing else; the full conformance
suite additionally needs Node.js 21 or later on `PATH`, the first release whose
ICU carries Unicode 15.1.0.

Both examples below exercise **Compiled Runtime**, not Foundation on its own.
Build plans, `requiresDefined`, the failed target and the absent Compiled Brand
Context are section 26.2 behaviour. Foundation, section 26.1, is the layer
underneath: Brand Elements, the four Brand States, scope, value contracts,
reference resolution and validation. The directory is called
`foundation-minimal` because it holds the smallest manifest, not because
`build` is a Foundation operation. See
[The minimum implementation is Foundation](#the-minimum-implementation-is-foundation)
for where the boundary runs.

### Smallest manifest: required truth is defined, context is produced

```bash
.venv/bin/python -m obds_ref.cli validate examples/foundation-minimal/manifest.yaml
.venv/bin/python -m obds_ref.cli build examples/foundation-minimal/manifest.yaml examples/foundation-minimal/build-plan.yaml --out /tmp/obds-out
```

Selected fields from the build report the CLI prints, plus what landed on disk:

```text
targetId       brand-query-global-en
status         ready
artifactRef    brand-query-global-en.context.json
artifactHash   sha256:101537ac9349901ce10b8a3ccd5ac2f2a112504187666d2ec8892db37679b6e1
governedResultHash sha256:c7594c47e076f4565ab82abd8fcf6fad51a2ad399843784283db4e7768e4ca42
requirements   structure.brand  defined  pass
exit           0

/tmp/obds-out  brand-query-global-en.context.json
               brand-query-global-en.context.md
               build-report.yaml
```

One manifest, one element, one target. That is the smallest runnable OBDS example.

Two hashes, two jobs. `artifactHash` identifies this exact artefact, prose and
compiler provenance included, and a different implementation will produce a
different one. `governedResultHash`, new in 1.1, identifies the governance
decision: which manifest, which target, which truth applied, in which states.
Two independent implementations given the same manifest and the same build plan
must agree on it. Section 14.3a defines the payload.

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

### Where the boundary runs

The distinction matters when you read the examples above, so it is worth being
exact about it.

**Foundation, section 26.1, governs Brand Truth.** Brand Elements and their
IDs, the four Brand States, semantic subjects, scope, validity, value contracts
with their shape and schema hashes, internal reference resolution, approved
immutable snapshots, canonical hashes and honest curation declarations. A
Foundation implementation reads and validates a Brand Manifest. It answers
*what is true, and what the brand has explicitly declared it does not know*.

**Compiled Runtime, section 26.2, adds the build.** Build Plans,
`requiresDefined`, explicit context selection, the rule that a failed target
produces no artefact, canonical JSON artefacts, reproducible hashes, exact
target loading and Runtime Decision Records. It answers *what applies to this
task, and may anything be generated at all*.

So the sequence `requiresDefined → build failure → no Compiled Brand Context →
no model call` is Compiled Runtime behaviour. It is not something a
Foundation-only implementation performs, and this repository's examples
demonstrate it by running the build.

That is a statement about which layer owns the mechanism, not a weakening of
it. The guarantee is unchanged and it is mechanically tested: a failed target
writes no artefact, and with no artefact there is nothing to assemble a model
input from, so the instrumented model records zero calls. What changes is only
the honesty of the label. An implementation that stops at Foundation gets
governed, validated Brand Truth with explicit unknowns; it does not thereby get
the fail-closed build gate, and this page should never have implied otherwise.

**Start with Foundation. Add Compiled Runtime when you need the build to
refuse.**

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

## Authoring and curation

OBDS does not write brand truth, does not check it against the world, and does
not decide that a statement is correct. **A named human role with the authority
to approve brand statements curates it.** Not a tool, not a model, not "the
system". OBDS does not mandate a job title, but it does mandate that the role
exists and is recorded: every approved manifest carries `approvedBy`,
`approvedAt` and a `contentHash` over the complete manifest. Section 7.2
separates the two acts explicitly — an approved source does not approve its OBDS
mapping; only an authorised brand role may approve the resulting Brand Manifest
as brand truth.

Extraction may propose. It may not approve. Section 24: "Extraction may locate
evidence. It may not manufacture brand truth." An AI system may draft a
candidate Brand Element from a brandbook, PIM, DAM entry, legal opinion or test
report; a human approves it; the approval, not the draft, is what makes it
truth. `sourceRefs[]` records where a value came from. It is provenance, not
proof.

**OBDS begins at the approved manifest and ends at a Compiled Brand Context and
the decision record of what happened with it.** Everything upstream — finding
sources, drafting elements, reconciling coverage, deciding what a statement
should say — is curation, a human act OBDS records but does not perform. A
manifest with `status: draft` can be validated, reviewed and argued over. It
cannot be built from.

Two things OBDS cannot guarantee, stated without softening:

**If a curator approves a wrong value, OBDS ships it faithfully and every hash
is valid.** Canonical hashing, schema validation and manifest approval check
that the value a named person approved is the value that reaches the build, byte
for byte. They do not check whether it is correct. OBDS governs whether a value
applies. It does not, and cannot, govern whether it is true.

**If a build target under-declares what it requires, the build succeeds and
nothing blocks the claim.** Section 13.1 forbids a target whose name or
description implies a capability its declared requirements cannot support. That
is a rule for whoever writes and reviews the Build Plan. The compiler has no
independent way to know what a target's name implies, so it provides no
mechanism to detect one. A target called `claim-copy-regulated-de` that never
lists the regulatory claim element in `requiresDefined` will build and pass
every deterministic check OBDS defines.

Full detail, including a worked path from a source document to one element's
`sourceRefs` and the `curation` coverage declaration, is on the
[Authoring and curation](https://openbranddefinition.org/authoring/) page.

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
| [`examples/foundation-minimal/`](examples/foundation-minimal/) | the smallest runnable example: one manifest, one element, one target, built through Compiled Runtime |
| [`examples/fail-closed/`](examples/fail-closed/) | the same shape, one required element `unknown`, build fails |
| [`OBDS-3.0.3-IMPLEMENTER-QUICKSTART.md`](OBDS-3.0.3-IMPLEMENTER-QUICKSTART.md) | five concepts, then the smallest conforming implementation |
| [`OBDS-3.0.3.md`](OBDS-3.0.3.md) | the normative specification |
| [`schemas/1.0.0/`](schemas/1.0.0/) | 21 public JSON Schemas, draft 2020-12 |
| [`value-schemas/1.0.0/`](value-schemas/1.0.0/) | 6 public value-contract schemas |
| [`reference/`](reference/) | reference implementation and the seven conformance suites |
| [`OBDS-3.0.3-TEST-RESULT.json`](OBDS-3.0.3-TEST-RESULT.json) | the verified conformance result |

Also: [`CONTRIBUTING.md`](CONTRIBUTING.md) for how to propose a change,
[`OBDS-3.0.3-CHANGELOG.md`](OBDS-3.0.3-CHANGELOG.md) for what moved and what did
not, [`OBDS-3.0.3-MIGRATION.md`](OBDS-3.0.3-MIGRATION.md) if you are on an
earlier release.

### Release version and schema contract version are separate

The release version and the schema contract version move independently, and
that is deliberate. The 27 public OBDS 1.0.0 contracts are byte-identical
across 1.0.0, 1.0.1, 1.0.2, 1.0.3, 1.0.4, 1.1.0, 1.1.1, 1.1.2, 1.1.3, 1.1.4, 1.1.5, 1.1.6, 2.0.0, 3.0.0, 3.0.1, 3.0.2 and 3.0.3, and the release gate fails
if that ever stops being true. Every one of their `$id` values still resolves
under `/schemas/1.0.0/` and `/value-schemas/1.0.0/`.

OBDS 1.1 added exactly one versioned contract beside them and changed none of
them:
[`schemas/1.1.0/compiled-context.schema.json`](schemas/1.1.0/compiled-context.schema.json),
which adds `governedResultHash` and pins `schemaVersion` to `1.1.0`.

OBDS 3.0 publishes four more, again beside the frozen surface and again changing
none of it: [`schemas/3.0.0/`](schemas/3.0.0/) carries the Build Plan, Compiled
Brand Context and Runtime Decision Record contracts, and
[`value-schemas/3.0.0/rule.schema.json`](value-schemas/3.0.0/rule.schema.json)
carries the RULE value contract. A 3.0 implementation reads 1.0.0 manifests and
produces 3.0.0 Build Plans and compiled contexts. A strict 1.0.0 consumer will
reject a 3.0.0 compiled context, which is what the new contract version is for.

## Conformance

```text
1079 passed
   0 failed
   0 skipped
```

Seven suites: foundation 973, context-delivery 3, context-assembly 24,
design-space 20, integration 15, golden 6, adversarial 38. No `skipif`, no
`pytest.skip`, no `xfail`; every case runs on every execution. Three adversarial
cases run a Node canonicaliser and compare it byte for byte against the Python
one, so the suite fails rather than skips when Node is missing.

Separately, the official declared Foundation conformance suite,
`reference/foundation/conformance-suite.yaml`, which is the only artefact in
the package that names a section 26 profile:

```text
profile   foundation
23 passed
 0 failed
```

Its result is published as `OBDS-3.0.3-FOUNDATION-CONFORMANCE.json`, and
`reference/release-gate.py` re-executes it on every run, so a release cannot
omit it.

**These two numbers are not added together.** All but one of the declared cases
exercise the same examples and fixtures as the pytest suites, through the
declarative `obds conformance` harness instead of pytest. Adding them to the
aggregate would double-count the same coverage. The one case that is not
duplicated, `canonical-hashes`, pins the canonical hashing of the published
`reference/foundation/examples/simple` manifest and its compiled artefact.

This is a conformance suite, not a certification programme. The results apply
to the reference implementation. Under section 26 this release claims exactly
two profiles: **OBDS Foundation (26.1)**, on the declared suite above, and
**OBDS Compiled Runtime (26.2)**, on a named executed case for every
requirement that section lists. No profile is claimed for Context Delivery,
Context Assembly, Visual Operations or Composition: those suites exercise
modules other than the reference compiler. `OBDS-3.0.3-TEST-RESULT.json`
carries the full scope statement.

Independent implementations may run the applicable official suite to support
their own OBDS conformance claim under section 26.

## Acknowledgements

OBDS was developed through human-led design and AI-assisted architecture, implementation and review.

- **Max Jürschik** — Creator and specification lead
- **ChatGPT (GPT-5.6 Sol, OpenAI)** — Co-Architect
- **Claude Code (Anthropic)** — Implementation and engineering

## Licensing

- Specification and documentation: **CC BY 4.0**
- Schemas, release metadata, reference implementation, conformance suite and examples: **Apache License 2.0**

Commercial implementation is permitted and requires no separate permission.
[`LICENSE.md`](LICENSE.md) has the file-by-file mapping, the unmodified licence
texts are in [`LICENSES/`](LICENSES/), and neither licence grants trademark
rights: see [`TRADEMARKS.md`](TRADEMARKS.md).

---

OBDS 3.0.3, stable, 4 September 2026. Published at
[openbranddefinition.org](https://openbranddefinition.org).
