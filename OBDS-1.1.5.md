# Open Brand Definition Specification (OBDS)

## OBDS 1.1: Stable Specification

**Version:** 1.1.5  
**Status:** Stable  
**Date:** 2026-08-31  
**Project home:** https://openbranddefinition.org  

---

## 1. Purpose

OBDS is an open, vendor-neutral specification for approved brand facts, rules, context and known gaps.

It is a **brand control layer for AI systems**. It sits between brand sources, such as Brandbooks, PIM, DAM and legal systems, and the runtime that uses models or agents.

```text
Brandbooks / PIM / DAM / Legal
              ↓
             OBDS
 Manifest → Build → Contexts + Checks
              ↓
      AI Runtime / Agent Platform
              ↓
             Models
```

OBDS is not an AI operating system. It does not define agents, model routing, memory, scheduling, retries, tool discovery, authentication or distributed execution.

The practical distinction is:

> Brandbooks explain the brand. OBDS controls which approved brand truth may be used for a declared context.

OBDS does not reproduce a Brandbook, portal or source archive. It selects the smallest approved brand truth that changes an answer, check, approval or execution decision.

> More content is not more context. Relevant brand truth is context.

OBDS separates three runtime needs:

- short descriptions for finding;
- full elements for exact facts and rules; and
- coherent chapters for understanding relationships.

> Short descriptions for finding. Full facts for answering. Chapters for understanding.

1.0.0 closes the runtime chain by defining the exact package sent to the model.

> **Complete compliance. Selective expression.**

All applicable rules remain binding. A single marketing artefact is not required to visibly demonstrate every brand value.

1.0.0 extends the same principle to visual production:

> **Declare the design space. Do not prescribe the layout.**

OBDS may define measurements, relations, roles, hierarchy, omission priority and spatial constraints. The render layer chooses one concrete composition inside that space. A validator proves that the result stayed inside the declared boundaries.

At release time, OBDS builds the declared runtime views. At runtime, Context Assembly selects, resolves and hashes the exact model input before the model call. Visual runtimes may additionally emit geometry evidence and run deterministic visual checks.

OBDS guarantees that the same approved inputs can produce the same compiled payload. It does not guarantee that an approved value is factually correct, that every relevant value has been entered or that a model will follow every semantic instruction.

### 1.1 Project name

**Open Brand Definition** is the public project at https://openbranddefinition.org.  
**OBDS** means **Open Brand Definition Specification**.

### 1.2 Writing rule

OBDS uses the simplest wording that keeps the meaning exact.

Project documentation SHOULD:

- explain the purpose before the mechanism;
- use one main idea per sentence;
- define a technical term when it first appears;
- prefer concrete behaviour over status language; and
- avoid strength claims that are not tested.

Machine-readable field names remain stable when changing them would break compatibility or reduce precision.

---

## 2. Normative language

The keywords **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **MAY** and **OPTIONAL** are normative.

Sections explicitly marked *informative* do not determine conformance.

---

## 3. What OBDS is designed to do

OBDS is designed to:

- choose the applicable brand value predictably;
- stop builds when required brand truth is missing or conflicting;
- build compact AI contexts before release;
- run simple mechanical checks without model judgement;
- keep brands, markets and targets separate;
- produce repeatable hashes and clear build reports;
- support export between implementations; and
- add optional depth only when it solves a real problem.

### 3.1 Non-goals

OBDS is not:

- an AI operating system;
- an agent or tool protocol;
- a product information management system;
- a digital asset management system;
- a content management system;
- a prompt library;
- a substitute for legal or human review;
- a requirement that every sentence become a record;
- a requirement that every organisation implement every profile;
- a requirement to compile every theoretical scope combination;
- a promise that authoring is already easy for Brand Managers;
- a promise of zero latency or guaranteed cache savings; or
- a claim that prompt structure alone guarantees model compliance;
- a layout-template schema;
- pixel coordinates or renderer-generated positions as Brand Truth;
- per-format capacity tables as a Foundation requirement;
- HTML, CSS, SVG or renderer code;
- motion timelines; or
- a requirement that one fixed layout be preserved across aspect ratios.

---

## 4. How the parts fit together

OBDS keeps approved brand truth separate from build settings and runtime tools.

```text
OBDS FOUNDATION
  Approved manifest, elements, states, scope and sources

BUILD CONFIGURATION
  Declared targets, required truth, slot selection and token budget

COMPILER
  Chooses the applicable approved content once before release

CONTEXT ASSEMBLY
  Resolves retrieval, selects active guidance and hashes the exact model input

RENDER LAYER
  Creates one concrete visual composition inside the declared design space

VISUAL VALIDATION
  Checks geometry evidence against declared spatial constraints

COMPILED RUNTIME
  Loads exact contexts and evidence, checks validity and runs declared validators

OPTIONAL PROFILES
  Claims, assets, localisation, record-level approval and specialised formats
```

The Brand Manifest contains brand truth. Build Plans, prompts, models, workflows and compiler settings do not.

A small brand may use the Foundation and one general target. A global organisation may define more targets. OBDS adds complexity only for contexts that are actually used.

### 4.1 One specification, one Foundation, optional capabilities

OBDS 1.0 has **one normative specification**. There is no separate CORE specification and no second class of "non-core" OBDS features.

Every conforming implementation supports the **Foundation**. The same specification defines two optional layers:

1. **Brand Profiles** add data contracts a Brand Manifest may use.
10. **Runtime Capabilities** add implementation behaviour an engine may claim.

```text
OBDS
├─ Foundation                         required
├─ Brand Profiles                     optional
│  ├─ Governed Records
│  ├─ Release Approval
│  ├─ Claims and Evidence
│  ├─ Assets and Rights
│  ├─ Localisation
│  ├─ Assurance and Lineage
│  ├─ Composition
│  └─ Visual Operations
└─ Runtime Capabilities               optional
   ├─ Compiled Runtime
   ├─ Context Delivery
   ├─ Context Assembly
   ├─ Text
   ├─ Visual Operations
   ├─ Composition
   ├─ Claims
   ├─ Localisation
   └─ Operations
```

The Brand Manifest field `profiles[]` declares the Brand Profile contracts used by that manifest. Every 1.0 manifest MUST include `obds-foundation`.

Registered 1.0 Brand Profile identifiers are:

| Profile | Identifier |
|---|---|
| Foundation | `obds-foundation` |
| Governed Records | `obds-governed-records` |
| Release Approval | `obds-release-approval` |
| Claims and Evidence | `obds-claims-evidence` |
| Assets and Rights | `obds-assets-rights` |
| Localisation | `obds-localisation` |
| Assurance and Lineage | `obds-assurance-lineage` |
| Composition | `obds-composition` |
| Visual Operations | `obds-visual-operations` |

Example:

```yaml
profiles:
  - obds-foundation
  - obds-composition
  - obds-visual-operations
```

Rules:

- Foundation is a dependency, not a separate document.
- A Brand Profile adds a brand-data contract. It does not create parallel Brand Truth.
- Runtime Capabilities are conformance claims and are not added to `profiles[]` merely because an implementation supports them.
An implementation MUST reject a manifest declaring a Brand Profile it does not implement and enforce. Unsupported declared profiles MUST NOT be silently ignored.
- A Brand Profile and a Runtime Capability MAY share a domain name, such as Composition. The profile declares brand data; the capability declares what an implementation can validate or execute.
- An implementation MUST NOT claim a Runtime Capability it does not validate.
- A manifest MUST NOT use a Brand Profile contract without declaring that profile.
- Implementations MAY support more Brand Profiles and Runtime Capabilities than one manifest uses.
- The absence of an optional profile makes no claim about the brand.

> **One specification. One Foundation. Optional capabilities.**

### 4.2 Minimal implementation path

A new implementation does not need every OBDS capability.

1. **Foundation:** read and validate Brand Manifests.
2. **Compiled Runtime:** build exact target contexts and checks.
3. **Context Delivery:** add Search Cards and Reasoning Chapters when retrieval is needed.
4. **Context Assembly:** produce the exact model input package when an LLM is called.
5. **Visual Operations and Composition:** add only when the implementation renders or validates visual assets.

Supporting schemas are loaded only for the capabilities an implementation claims. The number of schemas in the release package is not the number of concepts a basic implementation must implement.

---

## 5. Ground rules and system rules

### 5.1 Overarching principles

> **The source is evidence, not the model.**

A source provides evidence and material for curation. Its length, navigation, page structure and repetition do not determine the OBDS model.

> **Derive structure. Declare policy.**

OBDS MAY derive mechanical facts such as hashes, diffs, token counts, dead references and representation conflicts. It MUST NOT derive brand policy from observed repetition, missing information or technical convenience.

> **Declare relationships, not layouts.**

A brand MAY govern how values relate, which roles exist, which identity is primary and what may be omitted. OBDS MUST NOT turn those decisions into fixed pixel positions or a hidden template system.

### 5.2 Five OBDS Ground Rules

#### 1. Only store what changes an outcome.

Store only content that changes a selection, answer, generation, check, approval or execution decision.

Long explanations MAY remain in a source archive or Dossier. They enter the Brand Manifest only when their meaning materially affects use.

#### 2. Generic advice is not brand truth.

General communication or design best practice is not automatically brand-specific truth.

Generic advice MAY enter the manifest only when the brand explicitly adopts it and it materially changes output or evaluation.

#### 3. One decision, one authoritative place.

Within one brand release, each brand decision has one canonical representation. Human views, runtime contexts and summaries are generated from it and MUST NOT be maintained as independent truth.

Deliberate copies across independently approved brand manifests are separate decisions.

#### 4. Unknown is better than invented.

Missing, ambiguous or conflicting truth remains `unknown` or unresolved until it is resolved and approved.

`unknown` MUST NOT automatically create a prohibition, permission, fallback value or binding rule.

#### 5. Examples explain. Facts and rules decide.

Examples MAY guide understanding and evaluation. They do not approve facts, claims, products, assets, markets, translations or permissions.

An exact example becomes authoritative only when it is separately approved as the applicable FACT, claim, disclaimer or required text.

### 5.3 Three content types

OBDS distinguishes three content types:

| Nature | Meaning | Canonical treatment |
|---|---|---|
| **FACT** | Mechanically testable or queryable brand truth | structured value contract and deterministic selection |
| **KNOWLEDGE** | Approved meaning or context requiring interpretation | self-contained canonical prose or dataset |
| **CONFIGURATION** | Build and runtime settings | outside the Brand Manifest |

STANCE is not a fourth content type. It groups FACT and KNOWLEDGE used for qualitative review.

### 5.4 Use one governed unit

Do not split content merely because it can be edited separately. A Brand Element SHOULD be the largest coherent value whose parts share approval, scope and selection behaviour.

Create a separate element only when a part needs its own:

- state;
- scope;
- provenance;
- validity;
- rights;
- conflict handling; or
- selection behaviour.

Theoretical editability alone is not a reason to split.

### 5.5 Each element must make sense on its own

A selected element MUST be understandable without opening its source page, reading a hidden heading or consulting a parent brand.

- Brands do not inherit meaning from one another at runtime.
- No silent fallback to parent, sibling, market or locale.
- Shared approved content is copied when the manifest is written.
- A copy MAY keep a source link for audit, but runtime meaning MUST NOT depend on that source.
- Internal references inside one package are allowed when they resolve immutably.

### 5.6 Fail closed, never invent

A production compiler rejects a target when required truth is missing, ambiguous, expired, conflicting or blocked by an applicable explicit prohibit RULE. Runtime rejects a request when no exact valid artefact exists.

“Never invent” means:

- no inferred approval;
- no inferred local availability;
- no inferred claim, translation, asset identity or legal permission;
- no policy inferred from repeated source usage;
- no prohibition inferred from an `unknown` dependency;
- no helpful resolution of unclear pronouns or image-only meaning; and
- no silent choice between incomparable rules.

### 5.7 Build once, use simply

The canonical model may be structured and detailed. Humans receive generated Human Projections. AI runtimes receive immutable Compiled Brand Contexts, not the complete raw manifest.

The compiler chooses applicable values, detects conflicts and checks the token budget before release. Runtime only loads the exact context, checks its hash and validity, assembles the prompt and runs declared validators.

---

## 6. Files and packages

```text
OBDS SOURCE PACKAGE
├─ Brand Manifest
├─ optional profile declarations
├─ optional Localisation Manifests
├─ optional source snapshots and curation report
├─ optional asset and evidence files
├─ package index and hashes
└─ optional Human Projections

OBDS BUILD PACKAGE: separate build output
├─ Build Plan
├─ compiler and tokenizer declarations
├─ build report
├─ Compiled Brand Context artefacts
├─ optional Search Index
└─ optional Reasoning Chapters

RUNTIME: separate
├─ exact compiled-context loading
├─ Context Assembly Policy
├─ Model Input Packages
├─ optional Review Results
├─ executable validators
├─ models and tools
└─ agents and workflows
```

A portable source export MUST preserve the logical identity, values, sources, scopes and versions. A portable build export MUST preserve the Build Plan, build report, compiled artefacts and hashes.

---

## 7. Brand Manifest

```yaml
id: urn:obds:brand:example
kind: brand-manifest
name: Example Brand
schemaVersion: 1.0.0
version: 1.0.0
status: approved            # draft | approved | archived
owner: Example Company
createdAt: 2026-07-20T10:00:00+02:00
updatedAt: 2026-07-20T10:00:00+02:00
profiles:
  - obds-foundation
valueContracts:
  - id: urn:obds:brand:example#value-contract:design:colour:v1
    family: design
    kind: colour
    shapeHash: sha256:...
    schemaRef: https://openbranddefinition.org/value-schemas/1.0.0/colour.schema.json
    schemaHash: sha256:...
    validatorRef: obds:validator:colour-consistency-v1
curation:                  # optional; used when derived from source material
  sourceSnapshotRefs: []
  coverage: partial        # complete | partial | unknown
  reportRef:
approval:
  approvedBy: person-or-role-id
  approvedAt: 2026-07-20T10:00:00+02:00
  contentHash: sha256:...
  reviewedAgainst:          # recommended when replacing an approved version
    version: 1.0.0
    contentHash: sha256:...
elements: []
```

Rules:

- `id` is stable across versions.
- `schemaVersion` identifies the OBDS specification contract and is `1.0.0` for this release.
- `profiles[]` MUST contain `obds-foundation`.
- every profile-specific value contract used by the manifest MUST have its corresponding profile declared.
- `version` follows Semantic Versioning.
- Approved manifest versions are immutable.
- Changing normative content creates a new manifest version.
- `status: approved` requires `approvedBy`, `approvedAt` and `contentHash`.
- `contentHash` covers the complete manifest except the approval object and generated non-authoritative views.
- It uses the canonical JSON rules in §14.3.
- Approval confirms a pre-existing snapshot and MUST NOT rewrite any element.
- A manifest MAY be approved while honestly declaring `unknown`, `not_defined` or `not_applicable` elements.
- When a new approved manifest replaces an earlier approved version, `approval.reviewedAgainst` SHOULD identify the exact previous version and content hash reviewed by the approver.
- `reviewedAgainst` records the comparison basis. It does not prove that every change was read.
- A change report is derived from two manifest snapshots and is not a second source of truth.

### 7.1 Manifest approval as the default

OBDS Foundation assumes that a responsible person approves a complete Brand Manifest release. This matches the ordinary cadence of brand governance: teams usually approve a guideline or brand release, not hundreds of tiny values separately.

Record-level approval remains available through the Governed Records Profile for claims, rights, local exceptions or other independently controlled values.

### 7.2 Source coverage declaration

A manifest derived from existing guidelines or other source material MAY declare:

```yaml
curation:
  sourceSnapshotRefs: []
  coverage: complete | partial | unknown
  modalities:
    text: complete | partial | not_assessed | not_applicable
    figures: complete | partial | not_assessed | not_applicable
    tables: complete | partial | not_assessed | not_applicable
    metadata: complete | partial | not_assessed | not_applicable
  reportRef:
```

This remains deliberately small:

- absence makes no completeness claim;
- `unknown` means coverage has not been assessed;
- `partial` means known material remains unresolved, excluded or outside the manifest;
- `complete` MAY be claimed only when the referenced curation report reconciles every declared source unit and every relevant source modality;
- a multi-modal source MUST NOT claim `complete` when a relevant modality is `partial` or `not_assessed`;
- `not_applicable` is valid only when that modality is absent or irrelevant to the declared source snapshot;
- `reportRef` is required for `complete` and `partial`; and
- the curation declaration is governance metadata and is included in the manifest content hash.

The report does not force all source content into OBDS. It makes every disposition visible.

Source approval and transformation approval are different:

- an approved or official source does not automatically approve its OBDS mapping;
- an importer or test team MAY verify technical validity and coverage;
- only an authorised brand role may approve the resulting Brand Manifest as brand truth; and
- until that approval exists, the transformation remains `draft`.

---

## 8. Brand Element

```yaml
id: colour-brand-orange
subject: design.colour.brand-orange
family: design
kind: colour
nature: fact
state: defined
value: {}
scope: {}
sourceRefs: []
validity:
  from:
  to:
annotations: []
```

### 8.0 Semantic subject

Every Brand Element has one effective semantic `subject`: the decision or truth slot the element governs.

```yaml
id: design.primary-colour.at
subject: design.primary-colour
```

Rules:

- when `subject` is omitted, it defaults exactly to the element `id`;
- elements intended to override or compete with one another MUST declare the same `subject`;
- `subject` is stable semantic identity and is independent from file location, `kind` and display labels;
- precedence and conflict resolution in §10.2 operate only within one effective subject; and
- implementations MUST NOT infer a shared subject from similar values, names or visual roles.

The `subject` inside a `semantic-boundary` value is descriptive qualitative content. The top-level element `subject` is the machine key used for precedence.

Elements MAY carry an optional `classification`: an opaque identifier string.
OBDS assigns it no meaning, defines no vocabulary for it and enforces no policy
from it. It is governed metadata: section 13.6 change reports track it and
section 27.2 forbids changing it in a PATCH release. A runtime MAY consume it for
access policy, which OBDS does not define.

### 8.1 What each state means

| State | Meaning | `value` | Production behaviour |
|---|---|---:|---|
| `defined` | An applicable value exists | required | eligible when approved and in scope |
| `unknown` | A value is expected but not known | absent | block dependent use or escalate |
| `not_defined` | The brand deliberately defines no value | absent | return “not defined”; never infer |
| `not_applicable` | The element does not apply | absent | omit with explanation |

Workflow states such as `draft`, `extracted`, `verified` or `pending_review` are not brand states. They belong to authoring tools or the optional Governed Records Profile.

Brand States describe knowledge status only. A prohibition is not a knowledge state. A brand prohibition MUST be represented by an explicit RULE with `obligation: prohibit`, its declared `enforcement` and its declared validation method. Runtime MAY report the decision outcome `prohibited` when such a rule applies.

### 8.2 Group related values

One structured `value` MAY contain several properties when they all:

- share the same state, scope, sources and validity;
- are approved together;
- are always selected together; and
- do not need independent blocking or conflict handling.

Examples:

- One colour entity MAY contain screen, print and spot expressions.
- A typography system MAY contain headline and body roles when governed as one release.
- A Category Entry Point MAY contain trigger, need and brand role as one coherent KNOWLEDGE aggregate.
- A Brand Story SHOULD normally remain one KNOWLEDGE capsule.

Split a child value into its own element only when its approval, scope or selection behaviour differs. Replacement history does not belong in the Foundation element contract.

### 8.3 Value contracts and shape assertions

Every defined FACT value MUST reference exactly one declared value contract through `valueContractRef`. Structured KNOWLEDGE contracts MAY require the same mechanism. The standard `stance / semantic-boundary` contract does.

```yaml
valueContracts:
  - id: urn:obds:brand:example#value-contract:design:colour:v1
    family: design
    kind: colour
    shapeHash: sha256:...
    schemaRef: https://openbranddefinition.org/value-schemas/1.0.0/colour.schema.json
    schemaHash: sha256:...
    validatorRef: obds:validator:colour-consistency-v1   # optional

elements:
  - id: design.primary-colour
    family: design
    kind: colour
    nature: fact
    state: defined
    valueContractRef: urn:obds:brand:example#value-contract:design:colour:v1
    value: {}
```

Rules:

- `valueContractRef` MUST resolve to exactly one contract in the same manifest snapshot;
- the contract `family` and `kind` MUST match the element;
- several contracts MAY exist for the same `(family, kind)` when they intentionally describe different approved value shapes or contract versions;
- `shapeHash` is computed with OBDS JSON Shape v1;
- `schemaRef` identifies the exact semantic JSON Schema used to validate the value;
- `schemaHash` is the canonical SHA-256 hash of that schema payload and MUST reproduce before the schema is trusted;
- `validatorRef` is optional and adds deterministic invariants that JSON Schema alone cannot prove;
- when `validatorRef` is present, it MUST resolve and pass before the element is accepted;
- the compiler verifies shape, schema and validator independently;
- the same contract ID MUST NOT be reused with different shape, schema or validator semantics;
- a field or folder name alone does not define a valid format;
- KNOWLEDGE MAY remain self-contained prose when prose is the correct canonical form.

**OBDS JSON Shape v1**

The shape function removes scalar values but preserves JSON structure:

- string becomes `{"type":"string"}`;
- number becomes `{"type":"number"}`;
- boolean becomes `{"type":"boolean"}`;
- null becomes `{"type":"null"}`;
- object becomes `{"type":"object","properties":{...}}`, preserving property names and recursively derived child shapes;
- array becomes `{"type":"array","items":[...]}`, containing the sorted unique child shapes and ignoring array length and item order.

`shapeHash` is SHA-256 over the canonical JSON representation of that derived shape.

A value changing from a string to an object changes `shapeHash` even when the represented business meaning is intended to stay the same.

The three checks answer different questions:

```text
manifest contentHash  -> are these the approved manifest bytes?
value shapeHash       -> does this value still expose the approved machine shape?
schema + validator    -> is this value semantically valid for its declared contract?
```

None replaces the others.

### 8.4 Preserve useful meaning without reproducing the source

Curation MUST preserve details that materially affect how the brand is understood or used. It MUST NOT preserve content merely because it occupies a page, section or repeated position in the source.

Examples, rationales, boundary cases and narrative details SHOULD remain inside a KNOWLEDGE capsule when they materially affect generation or evaluation. Content may be shortened, but important omissions MUST be recorded as condensed, routed, excluded or unresolved. Shorter is not automatically better.

A `defined` element MUST be state-pure:

- it MUST NOT hide an operationally relevant unknown inside its value;
- a known part and an independently relevant unknown part are split into separate elements; or
- the unknown part is omitted when no declared task requires it.

Observed consistency MAY support a candidate FACT. It does not create a binding RULE.

When a source contradicts a production-relevant value that was previously read as `defined`, the value MUST NOT remain production-eligible merely because the earlier reading was plausible. Until an authorised resolution exists, the affected element is `unknown` and the contradiction is recorded separately as curation evidence.

OBDS 1.0.0 does **not** add a `known_false` Brand State. Contradiction history belongs to curation or assurance records, not current truth.

A blocking or approval-requiring RULE derived from source material MUST be supported by explicit source evidence or explicit brand approval for the obligation and consequence. Absence, repeated usage and technical portal configuration are not sufficient by themselves.

### 8.5 Sources and notes

`sourceRefs[]` records where content came from. A page label or extraction note does not become approved brand truth merely because it is stored as a source.

`annotations[]` are explanatory notes. They cannot define scope, conditions, prohibitions or binding instructions.

An `unknown` element MAY carry clearly labelled interim operational guidance in an annotation, such as whom to contact while an authoritative asset registry is missing. The annotation does not resolve the unknown value and MUST NOT be treated as brand truth.

### 8.6 IDs, internal references and duplicate representations

Integrity checks run before target compilation.

- Every element ID MUST be unique inside one manifest snapshot.
- Every field defined by OBDS or a declared value contract as an internal element reference MUST resolve to exactly one element in that snapshot.
- A missing or ambiguous internal reference fails validation.
- Foundation internal references include `RULES.value.references[]`, `RULES.value.requiresDefinedRefs[]`, `checks[].params.elementValueRef.elementId` and references declared by registered value contracts.
- Build Plan references such as `requiresDefined[]`, `styleTexture.elementIds[]` and `contextAssembly.eligibleGuidanceIds[]` MUST resolve against the referenced manifest before any target is built.
- `sourceRefs[]`, external asset locations and `validatorRef` are not internal element references unless their contract explicitly says otherwise.
- When one value contract permits several representations of the same value, the contract MUST define their consistency check.
- Contradictory representations fail validation. The system MUST NOT choose one representation silently.

These rules remove phantom records and contradictory copied values before runtime.

---

## 9. Scope

```yaml
scope:
  brands: [example-group]
  markets: [AT]
  locales: [de-AT]
  jurisdictions: [AT]
  channels: [linkedin]
  audiences: [professional-installers]
  productFamilies: [luminaires]
  outputTypes: [social-copy]
  contentPurposes: [awareness]
```

The scope vocabulary is closed. Exactly these nine dimensions exist:
`brands`, `markets`, `locales`, `jurisdictions`, `channels`, `audiences`,
`productFamilies`, `outputTypes`, `contentPurposes`. An unknown dimension is
invalid and MUST fail validation.

Rules:

- Omitted dimensions mean unrestricted by that element.
- Scope values are compared as sets after Unicode NFC normalisation. Order is not
  significant and duplicates after normalisation are invalid.
- An element that restricts a dimension the build target does not declare is
  **not applicable** to that target. Truth is never widened to a dimension the
  task did not state.
- Empty arrays are invalid.
- Scope values are non-empty strings. Boolean and numeric scope scalars are invalid.
- Market, locale and jurisdiction are independent.
- Vague regions require registered definitions.
- A build target uses one atomic target value per dimension.
- Multi-target requests are split into separate runs.
- Missing task dimensions block only where a required decision depends on them.

---

## 10. Choose the applicable value during the build

### 10.1 When an element applies

An element matches a build target when every declared scope restriction matches the target and the element is valid at the Build Plan `asOf` timestamp.

The Build Plan MUST declare `asOf` as a timezone-aware ISO 8601 timestamp. Compilation MUST NOT select elements against the compiler wall clock. Element validity uses a half-open interval: `validity.from` is inclusive and `validity.to` is exclusive.

### 10.2 When more than one element applies

For the same semantic subject, precedence is set inclusion on matched targets.

**An element A is more specific than an element B when the set of build targets A
matches is a strict subset of the set of build targets B matches.**

Section 9 already supplies the semantics: an omitted dimension means unrestricted,
so every scope is already a set of matching targets. Operationally, with `dim(X)`
the dimensions X restricts and `vals(X, d)` its allowed values in dimension `d`:

- A is more specific than B when `vals(A, d)` is a subset of `vals(B, d)` for
  every `d` in `dim(B)`, and A's matched-target set is strictly smaller, which
  holds when A restricts more dimensions or narrows at least one shared
  dimension;
- otherwise A and B are incomparable.

This relation is a strict partial order: irreflexive, antisymmetric and
transitive, all inherited from strict subset inclusion.

Then:

- the more specific element wins only inside its declared scope;
- array order, timestamps and file order are never precedence;
- two incomparable maximal elements are a hard conflict;
- an applicable explicit prohibit RULE blocks according to its exact scope and declared enforcement.

#### 10.2a When a hard conflict fails a target

A hard conflict is a property of a subject, not of a build. Whether it fails a
given target depends on whether that target's outcome could depend on how the
conflict is resolved.

**A hard conflict MUST fail a target when the conflicted subject is
decision-relevant to that target, and MUST NOT fail it otherwise.** A subject is
decision-relevant to a target when at least one of its incomparable maximal
elements would, if it won, reach that target's requirements or its compiled
context. Concretely, when that element is:

1. named in the target's `requiresDefined`;
2. a RULES element whose `enforcement` is `block` or `require_approval`, so it
   belongs in HARD_BOUNDARIES;
3. a `defined` element of `nature: fact` outside `family: rules`, so it belongs
   in FACT_GROUNDING;
4. carried into STATE_MAP by the target's declared `stateMap` policy; or
5. carried into STYLE_TEXTURE by the target's declared `styleTexture` policy.

The first three are unconditional: a target cannot opt out of its own
requirements, its hard boundaries or its fact grounding. The last two follow the
policy the target declared, so a target that selects narrowly is not failed by a
conflict it never reads.

**An irrelevant conflict MUST NOT be silently discarded.** The Build Report MUST
still carry it in `conflicts[]`, marked as not decision-relevant for this target,
so an operator sees a manifest-level defect that this particular target happened
not to touch. It is a manifest problem either way; it is only this target's
problem when the target reads it.

Failing a target on a conflict it cannot observe is not fail-closed, it is
fail-arbitrary: the same manifest would block or build depending on which
unrelated subject a curator happened to leave unresolved.

### 10.3 Missing or conflicting content

The compiler MUST distinguish:

- no relevant element exists;
- an element explicitly says `unknown`;
- an element explicitly says `not_defined`;
- a required task dimension is missing; and
- multiple applicable elements conflict.

These outcomes MUST NOT collapse into a generic null.

---

## 11. Element families

Families give content a stable home. They do not prescribe folder structures.

### 11.1 STRUCTURE

Brand identity and architecture: names, roles, legal ownership, portfolio relations, markets and official identifiers.

### 11.2 IDENTITY

Purpose, promise, values, personality, positioning, voice, naming and approved brand lines.

Language content is placed by function:

- voice, naming and preferred expression belong in IDENTITY;
- required or prohibited terms belong in RULES;
- locale-specific changes belong in the Localisation Profile;
- general linguistic context may belong in CONTEXT.

LANGUAGE is not a separate Foundation family.

### 11.3 DESIGN

Queryable visual values: colour entities, logo identities, typography systems, spacing, grids, motion, imagery and other visual systems.

**Boundary:**

- DESIGN stores a value to look up.
- RULES stores an objectively testable obligation that uses or constrains a value.
- STANCE or KNOWLEDGE stores qualitative judgement.

A design obligation SHOULD reference an authoritative design element instead of copying its value into rule prose.

### 11.4 RULES

A rule declares an obligation, its consequence and how a violation is assessed:

```yaml
statement:
obligation: require | prohibit | permit | recommend
enforcement: block | require_approval | warn | inform
validationMode: deterministic | semantic | human | external
checks: []
validatorRef:
condition: {}
requirement: {}
references: []
requiresDefinedRefs: []
```

`enforcement` defines what happens when the rule is violated. `validationMode` defines how the violation is established.

`references[]` explains or links a rule. It does not automatically make the referenced element a prerequisite.

`requiresDefinedRefs[]` is explicit policy. When an applicable rule lists an element there, that referenced element MUST resolve to one applicable `defined` value before the rule can be used. If it does not, the target fails rather than pretending that the rule's extension is known.

This is intentionally separate from `references[]`: explanation does not create dependency, but an explicitly declared dependency does.

- `deterministic` requires at least one registered `check` or one resolvable, versioned `validatorRef`.
- When both are declared, all checks and the validator MUST pass.
- A structured `condition` alone is not a validator.
- Rules without a registered check or executable validator MUST use `semantic`, `human` or `external`.
- A semantic or human-reviewed rule MAY block output, but tooling MUST NOT report it as mechanically proven.

Qualitative principles without a defined violation belong in STANCE or KNOWLEDGE.

**Single prohibition rule:** Brand prohibition is represented only here, through `obligation: prohibit`. `state: prohibited` is not part of OBDS 1.0 Brand States. This keeps prohibition, enforcement, evidence and scope in one machine-readable place.

### 11.5 Foundation Check Registry v1

The Foundation registry is deliberately small and closed. Rule authors write data, not code.

Every check is a pure function of its declared phase input and parameters. Implementations MUST use Unicode NFC normalization before text comparison. `case_insensitive` uses Unicode default case folding. `word_boundary_ci` uses Unicode word segmentation pinned by registry fixtures.

| Primitive | Default phase | Fails when | Parameters |
|---|---|---|---|
| `term_prohibited` | postflight | a prohibited term occurs | `terms[]`, `match: exact \| case_insensitive \| word_boundary_ci`, `appliesTo: output \| task_input` |
| `term_required` | postflight | required terms are absent | `terms[]`, `mode: any \| all`, `match` |
| `literal_required` | postflight | a required literal is absent | `literal` or `elementValueRef`, `match: exact \| normalized_whitespace` |
| `length_max` | postflight | text exceeds the limit | `max`, `unit: characters`, `appliesTo: output \| task_input` |

Rules:

- `elementValueRef` is resolved against the exact approved manifest snapshot during the build.
- Unsupported primitives, invalid parameters or unsupported registry versions fail the target build.
- Runtime MUST execute every compiled Foundation check natively or reject the artefact.
- Foundation Check Registry v1 excludes regex, general expression languages and token-length checks.
- More complex deterministic logic uses `validatorRef` or an optional namespaced profile.
- `appliesTo: task_input` requires `phase: preflight`; `appliesTo: output` requires `phase: postflight`. A mismatched pair is invalid and MUST fail validation.
- Every defined element in the RULES family MUST validate against a rule value contract regardless of its `nature`.
Canonical Rule values retain explicit empty structural fields such as `checks`, `condition`, `requirement` and `references` in 1.0 so one rule contract has a stable machine shape. Runtime model projections MAY omit empty validator plumbing.

### 11.5a Foundation Validator Registry v1

`validatorRef` names a deterministic invariant that JSON Schema alone cannot
prove. The registry is closed, like the Foundation Check Registry, and contains
one entry in OBDS 1.1.

| Validator | Applies to | Rule |
|---|---|---|
| `obds:validator:colour-consistency-v1` | value contracts of kind `colour` | when an sRGB expression carries both `hex` and `rgb`, both MUST describe the same channel values (section 12.1) |

Resolution rules:

- a `validatorRef` in the `obds:validator:` namespace MUST resolve against this
  registry for the declared OBDS version;
- a reference in any other namespace is implementation-defined, and an
  implementation that does not support it MUST fail closed, as section 8.3
  already requires; and
- the validator's input is the element value, canonically serialised per section
  14.3, and its outcome is pass or fail with a message.

Section 26.1 requires execution of registry validators. It does not require
execution of validators outside this registry, which by definition have no
published resolution.

### 11.6 CONTEXT

Approved knowledge about audiences, competitors, market context, history and durable learnings.

### 11.7 STANCE

Qualitative boundaries, perspectives, trade-off principles and review rubrics used when mechanical checks are insufficient.

#### 11.7.1 Semantic Boundary

`kind: semantic-boundary` is the standard structured contract for qualitative IS / IS NOT guidance.

```yaml
id: stance.voice.confidence
family: stance
kind: semantic-boundary
nature: knowledge
state: defined
valueContractRef: urn:obds:brand:example#value-contract:stance:semantic-boundary:v1
value:
  subject: voice
  quality: confident
  is:
    - clear
    - specific
    - decisive
    - grounded
  isNot:
    - aggressive
    - boastful
    - absolute_without_evidence
  tieBreaker:
    prefer: precise
    over: forceful
```

Rules:

- `is[]` describes positive semantic evidence for the quality;
- `isNot[]` describes explicit qualitative contradiction, not a deterministic prohibited-term list;
- `tieBreaker` is optional and resolves a declared qualitative trade-off;
- absence of an `is[]` trait is not a violation;
- when the boundary is active guidance, strong evidence of an `isNot[]` trait MAY support `material_conflict`;
- only a separate applicable RULE may turn that conflict into a compliance violation; and
- the contract is equally valid for voice, photography, art direction, composition, product depiction and other qualitative brand subjects.

The standard semantic-boundary schema is part of the 1.0 Foundation value-contract registry.

### 11.8 DECISIONS

DECISIONS is a record kind, not an element `family`. `decisions` is not a valid value for the element `family` field; the valid families are the six named in sections 11.1 to 11.7.

An optional append-only log explaining significant brand changes. The manifest is current truth; decisions explain how it changed.

---

## 12. Foundation value formats

The Foundation keeps contracts deliberately small. Capability Profiles MAY add richer contracts.

### 12.1 Colour entity

```yaml
name: Brand Orange
hex: "#FF6600"
rgb: [255, 102, 0]
expressions:
  screen:
    colourSpace: srgb
    hex: "#FF6600"
    rgb: [255, 102, 0]
  print:
    colourSpace: cmyk
    profile: FOGRA51
    values: [0, 70, 100, 0]
  spot:
    system: pantone
    code: "..."
roles:
  - role: accent
```

The top-level `name` and `hex` are the Foundation colour contract and are required by `colour.schema.json`; the sRGB expression repeats them inside `expressions` for readers that consume expressions directly. Both MUST describe the same value.

One colour MAY remain one governed aggregate. An expression becomes independent only when scope, source, validity or governance differs.

For an sRGB expression that contains both `hex` and `rgb`, both representations MUST describe the same channel values. A mismatch fails validation. Other value contracts MAY allow duplicate representations only when they define an equally exact consistency check.

`primary`, `secondary` and `accent` are contextual roles, not intrinsic colour identities.

### 12.2 Logo identity

```yaml
name: Primary Wordmark
assetRef: asset-logo-primary
variant: horizontal
```

Clear-zone, minimum-size and background values MAY be included as structured properties when governed together or separate elements when independently scoped.

### 12.3 Typography system

```yaml
name: Primary Typography
roles:
  headline:
    family: Example Display
    weight: 700
  body:
    family: Example Sans
    weight: 400
```

### 12.4 Measurement Contract v2

1.0.0 extends the existing measurement contract without invalidating the earlier form.

```yaml
quantityKind: cap-height     # standard or namespaced quantity kind
mode: relative               # relative | absolute
amount: 0.6667
basisRef: measurement-product-class-box
symbol: R                    # optional display label

system:
  type: relative             # relative | absolute
  id: R                      # required for relative systems

min:
  amount: 9
  unit: px

max:
  amount: 18
  unit: px
```

Rules:

- `quantityKind` states what is measured. Examples include `font-size`, `cap-height`, `line-height`, `spacing`, `clear-zone`, `width`, `height`, `border-thickness` and namespaced custom quantities.
- `mode: relative` requires `basisRef`.
- `mode: absolute` requires an absolute `unit`.
- `system.type: relative` requires a stable brand-defined system `id`, such as `H` or `R`.
- `system.type: absolute` declares that the measurement does not scale with a relative brand system.
- `min` and `max` are optional absolute production bounds.
- when `min` or `max` is present, the renderer resolves the preferred value first and then applies the bound;
- when both bounds are present, they MUST use the same unit and `min.amount` MUST be less than or equal to `max.amount`;
- a floor or ceiling is Brand Truth only when explicitly approved or sourced. A consumer MUST NOT promote a derived bound into the manifest automatically.
- quantity kinds are not interchangeable. A cap height is not a font size.
- values from different systems MUST NOT be combined unless a declared relation or validator defines the interaction.

Legacy measurements containing only `mode`, `amount`, `basisRef` and optional `symbol` remain valid in 1.0.0 but make no claim about quantity kind, production bounds or system membership.

---

## 13. Build Plan

A Build Plan is configuration, not brand truth. It lists only the contexts the implementation will use.

```yaml
id: urn:obds:build-plan:example
kind: obds-build-plan
schemaVersion: 1.0.0
asOf: 2026-08-27T00:00:00Z
manifestRef:
  id: urn:obds:brand:example
  version: 1.0.0
  contentHash: sha256:...
compiler:
  id: org.openbranddefinition.reference-compiler
  version: 1.0.0
tokenizer:
  id: obds:whitespace-v1
  version: 1.0.0
targets:
  - id: brand-assistant-de-at
    scope:
      markets: [AT]
      locales: [de-AT]
      outputTypes: [brand-query]

    requiresDefined:
      - product.availability
      - claims.approved

    styleTexture:
      mode: all              # all | selected | none
      elementIds: []         # required only when mode = selected

    stateMap:
      mode: all_applicable   # none | kinds | all_applicable
      kinds: []              # required only when mode = kinds

    contextAssembly:
      deliveryMode: reasoning       # lookup | reasoning | full
      applicationMode: create       # create | review | compliance
      eligibleGuidanceIds: []
      noHitPolicy: resolve_before_answer

    releasePolicy: build_only
    maxTokens: 2400
```

### 13.0 Build time is explicit

`asOf` is required configuration. It is part of the Build Plan hash and fixes the temporal viewpoint used for element validity and precedence. The same Manifest and Build Plan therefore select the same elements independently of wall-clock time.

A Compiled Brand Context carries the exact `asOf` and a selection-stability validity window. Runtime MUST reject the artefact outside that window.

### 13.1 Target requirements

`requiresDefined` is a list of exact Brand Element IDs. It is an **element-ID
requirement, not a subject requirement**, and the two MUST NOT be conflated.

For each listed ID, the compiler MUST find that exact element, and that exact
element MUST be the applicable winner for its semantic subject with state
`defined`. If another element wins the subject under section 10 precedence, the
requirement is **not** satisfied, even when the winning element is itself
`defined` and even when it is a more specific override of the listed one. An
implementation MUST NOT silently reinterpret a listed ID as a requirement on
that element's subject.

The target fails when the listed element:

- does not exist;
- does not apply to the target scope;
- is expired;
- is conflicting;
- has any state other than `defined`; or
- lost its semantic subject to a more specific applicable element.

The rule is deliberately strict. A Build Plan that means "whatever governs this
subject" is asking for something OBDS 1.1 does not offer: reusable
subject-level requirements are deferred target-governance research, and until
they exist a plan that wants an override to satisfy a requirement MUST name the
overriding element.

The Build Report MUST name the failed element, expected state and actual result.

A target name or description MUST NOT imply a capability that its declared requirements and selected context cannot support. If a review, claim, market or design capability depends on specific truth, that truth belongs in `requiresDefined`.

This small rule makes production prerequisites visible in the Build Plan instead of hiding them in compiler code or prompts.

### 13.1a Build failure codes

A Build Report reports a failure with an exact code. Codes are normative because
Build Reports are interchange artefacts; message text and process exit codes are
not.

| Code | Condition |
|---|---|
| `OBDS-BUILD-REQUIRED-NOT-FOUND` | a `requiresDefined` ID does not exist in the manifest |
| `OBDS-BUILD-REQUIRED-OUT-OF-SCOPE` | the element exists but does not apply to the target scope |
| `OBDS-BUILD-REQUIRED-EXPIRED` | the element exists and is in scope but is not valid at `asOf` |
| `OBDS-BUILD-REQUIRED-NOT-DEFINED` | the listed element applies but is not the `defined` winner of its semantic subject, whether because its own state is not `defined` or because a more specific applicable element won that subject |
| `OBDS-BUILD-SUBJECT-CONFLICT` | two incomparable maximal elements share one semantic subject that is decision-relevant to this target under section 10.2a |
| `OBDS-BUILD-MANIFEST-HASH` | the manifest content hash does not match the Build Plan reference |
| `OBDS-BUILD-STYLE-SELECTION` | a selected style element is not an applicable defined KNOWLEDGE element |
| `OBDS-BUILD-TOKEN-OVERFLOW` | the compiled context exceeds the declared token budget |

The first four exist as separate codes because they need different human
responses: curate the truth, correct the target scope, renew the fact, or resolve
the state. Before OBDS 1.1 all four surfaced identically and an operator could not
tell them apart.

### 13.2 Context selection

OBDS Foundation does not use an opaque `selectionProfile` string.

HARD_BOUNDARIES and FACT_GROUNDING always include every applicable element required by the target.

Every element named in `requiresDefined` MUST reach the Compiled Brand Context. Context selection governs additional content only: `styleTexture` and `stateMap` MUST NOT remove a required element. A build that verifies required truth as `defined` and then produces a context without it is invalid.

`styleTexture` controls only KNOWLEDGE and STANCE:

- `all` includes every applicable KNOWLEDGE and STANCE element;
- `selected` includes only the listed applicable element IDs; and
- `none` omits STYLE_TEXTURE.

The compiler MUST NOT summarise, rewrite or rank STYLE_TEXTURE content. A shorter context requires an explicit smaller target or pre-approved shorter Brand Elements.

`stateMap.mode` controls STATE_MAP:

- `all_applicable` includes every permitted applicable `unknown`, `not_defined` and `not_applicable` element;
- `kinds` includes only the declared kinds and is explicitly partial; and
- `none` omits STATE_MAP and makes no known-gap coverage claim.

`all_applicable` SHOULD be used only when the target is intended to answer broad questions about applicable gaps. A task-specific target SHOULD include only gaps that change its answer, check or build decision.

### 13.3 Context Assembly Policy

`contextAssembly` is runtime configuration, not brand truth.

- `deliveryMode` declares the expected reasoning grain.
- `applicationMode` declares whether the model creates, reviews or performs compliance checking.
- `eligibleGuidanceIds` limits which values, voice traits and STANCE elements may become active guidance for this target.
- The runtime records the smaller `activeGuidanceElementIds` actually selected for the task.
- `noHitPolicy: resolve_before_answer` requires the runtime to distinguish retrieval failure from missing brand truth before answering.

A target with no `contextAssembly` object uses implementation defaults and makes no OBDS Context Assembly conformance claim.

### 13.4 General build rules

- The Build Plan MUST reference one exact approved manifest snapshot.
- Every internal element ID named by a target MUST exist in that manifest snapshot.
- `requiresDefined[]`, `styleTexture.elementIds[]` and `contextAssembly.eligibleGuidanceIds[]` are validated before target compilation.
- Targets MUST be explicitly declared.
- A compiler MUST NOT generate an undeclared Cartesian product of scopes.
- STATE_MAP observes the same scope, sensitivity and access policy as every other slot.
- `maxTokens` applies to all compiled brand slots under the declared tokenizer.
- The compiler MUST NOT change target meaning to fit the budget.
- HARD_BOUNDARIES and FACT_GROUNDING MUST NOT be removed.
- STATE_MAP coverage MUST NOT be silently downgraded.
- `releasePolicy: build_only` is the Foundation default.
- `artifact_approval_required` is defined by the optional Release Approval Profile.

### 13.5 What the compiler does

For each release, the compiler:

1. verifies unique element IDs;
2. resolves every required `valueContractRef`;
3. recomputes and verifies every declared `shapeHash`;
4. resolves every `schemaRef` and verifies its `schemaHash`;
5. validates each contracted value against that exact schema;
6. resolves and executes every declared value-contract `validatorRef`;
7. resolves every declared internal element reference;
8. verifies manifest approval, canonical content hash and declared profiles;
9. verifies that the Build Plan references the exact manifest;
10. checks every `requiresDefined`, selected STYLE_TEXTURE element and Context Assembly eligibility reference;
11. selects applicable elements using §9 and §10;
12. fails on conflicts or required missing truth;
13. validates registered rule checks and resolves every `elementValueRef`;
14. verifies every declared executable rule `validatorRef`;
15. builds the four brand slots and the structured target-scoped element records;
16. measures every slot with the declared tokenizer;
17. fails rather than truncating content or changing target policy; and
18. emits a canonical JSON artefact only when the target is valid.

### 13.6 Manifest change report

A conforming toolchain MUST compare two manifest snapshots and produce a deterministic change report.

```json
{
  "kind": "obds-manifest-change-report",
  "schemaVersion": "1.0.0",
  "oldManifest": {"id": "urn:obds:brand:example", "version": "1.0.0", "contentHash": "sha256:..."},
  "newManifest": {"id": "urn:obds:brand:example", "version": "1.0.1", "contentHash": "sha256:..."},
  "added": [],
  "changed": [{
    "elementId": "design.primary-colour",
    "oldHash": "sha256:...",
    "newHash": "sha256:...",
    "changeKinds": ["sources", "value", "value_shape", "contract"],
    "oldValueHash": "sha256:...",
    "newValueHash": "sha256:...",
    "oldValueShapeHash": "sha256:...",
    "newValueShapeHash": "sha256:...",
    "oldContractId": "urn:obds:brand:example#value-contract:design:colour:v1",
    "newContractId": "urn:obds:brand:example#value-contract:design:colour:v2"
  }],
  "removed": [],
  "compatibility": {
    "patchEligible": false,
    "shapeChangedElementIds": ["design.primary-colour"],
    "contractChangedElementIds": ["design.primary-colour"]
  }
}
```

The report:

- compares stable element IDs;
- preserves each complete element hash for full audit;
- separately hashes the element `value`;
- separately hashes the derived OBDS JSON Shape v1 structure;
- resolves the old and new value-contract IDs;
- emits machine-readable `changeKinds`;
- distinguishes at least `value`, `value_shape`, `contract`, `subject`, `state`, `scope`, `sources`, `validity`, `annotations`, `classification` and `metadata`;
- sorts entries by element ID;
- contains no approval decision;
- can be reproduced from the two snapshots; and
- prevents source-reference rotation from hiding a structural compatibility change.

A complete element hash answers whether the element bytes changed. `valueHash` answers whether the value payload changed. `valueShapeHash` answers whether its machine-readable structure changed. These are separate integrity questions.

The report MUST set `compatibility.patchEligible` to `false` when any existing element has a `value_shape` or `contract` change.

A human-readable companion report MAY explain why a shape changed. It does not replace the machine-readable classification.

### 13.7 Build Report

The Build Report MUST include `conflicts[]`. Each subject conflict names the effective semantic subject and the incomparable maximal element IDs that caused the target to fail.

```yaml
buildId:
builtAt:
planId:
planHash:
manifestId:
manifestVersion:
manifestContentHash:
compilerVersion:
targets:
  - targetId:
    status: ready | failed
    artifactRef:
    artifactHash:
    tokenCounts:
      hardBoundaries:
      factGrounding:
      stateMap:
      styleTexture:
      total:
      max:
    budgetStatus: within_budget | overflow
    requirements:
      - elementId:
        expectedState: defined
        actualState:
        result: pass | fail
    includedElementIds: []
    excludedElementIds: []
    conflicts: []
    errors: []
```

A failed target MUST NOT produce a production artefact.

`builtAt`, logs, worker IDs and diagnostics belong in the Build Report. They do not affect `artifactHash`.

---

## 14. Compiled Brand Context

A Compiled Brand Context is the machine-readable runtime artefact for one target.

The normative artefact is JSON. A Markdown view MAY be generated for people and prompt inspection.

```json
{
  "kind": "obds-compiled-brand-context",
  "schemaVersion": "1.1.0",
  "id": "urn:obds:brand:example:context:brand-assistant-de-at",
  "targetId": "brand-assistant-de-at",
  "manifest": {
    "id": "urn:obds:brand:example",
    "version": "1.0.0",
    "contentHash": "sha256:..."
  },
  "build": {
    "planId": "urn:obds:build-plan:example",
    "planHash": "sha256:...",
    "compilerId": "org.openbranddefinition.reference-compiler",
    "compilerVersion": "1.0.0",
    "asOf": "2026-08-27T00:00:00Z"
  },
  "scope": {
    "markets": ["AT"],
    "locales": ["de-AT"],
    "outputTypes": ["brand-query"]
  },
  "tokenBudget": {
    "tokenizerId": "obds:whitespace-v1",
    "tokenizerVersion": "1.0.0",
    "max": 2400,
    "actual": 1280
  },
  "checkRegistryVersion": 1,
  "compiledChecks": [],
  "stateMapCoverage": "complete",
  "stateMapEntryCount": 3,
  "validFrom": null,
  "validTo": null,
  "includedElementIds": [],
  "availableElementIds": [],
  "elementRecords": [],
  "contextAssembly": null,
  "slots": {
    "hardBoundaries": "...",
    "factGrounding": "...",
    "stateMap": "...",
    "styleTexture": "..."
  },
  "governedResultHash": "sha256:...",
  "artifactHash": "sha256:..."
}
```

The compiled context `id` is constructed, not chosen: it is the manifest `id`,
the literal segment `:context:` and the target `id`, concatenated in that order
and otherwise unaltered.

```text
{manifest.id}:context:{targetId}
```

Neither part is escaped, trimmed or case-folded, and a target `id` that itself
contains a colon is carried through unchanged. Two implementations given the
same manifest and Build Plan therefore produce the same context `id`.

### 14.0 Artefact validity

`validFrom` and `validTo` bound the interval in which rebuilding this target
would produce the same selection. The interval is half-open: `validFrom` is
inclusive and `validTo` is exclusive. Runtime MUST reject an artefact used
before `validFrom` or at or after `validTo`.

The window is derived from **every element whose scope matches the target
scope**, and from no other element. That set is taken **before** the `asOf`
validity filter and **before** subject precedence, so it includes:

- an element that is not yet valid at `asOf`;
- an element that has already expired at `asOf`; and
- an element that is applicable but loses its semantic subject to a more
  specific element.

An element whose scope does not match the target contributes nothing.

From that set, collect every `validity.from` and `validity.to` timestamp.
`validFrom` is the latest of those boundaries at or before `asOf`, or `null` if
there is none. `validTo` is the earliest strictly after `asOf`, or `null` if
there is none.

The wider set is deliberate and is the whole point of the field. A losing
candidate whose validity begins tomorrow changes the selection tomorrow; an
element not yet valid at `asOf` changes it when it becomes valid. Deriving the
window from the surviving selection alone would leave an artefact nominally
valid past the moment its own selection stops being correct, which is the
failure this field exists to prevent.

### 14.1 Slot content

- **hardBoundaries** contains applicable prohibitions and rules with `enforcement: block` or `require_approval`.
- **factGrounding** contains applicable `defined` FACT values. It contains no inferred values.
- **stateMap** contains the states selected by the target's `stateMap` policy.
- **styleTexture** contains the KNOWLEDGE and STANCE elements selected by `styleTexture`.

Prohibition appears in `hardBoundaries` through applicable explicit RULE elements. It is not a Brand State.

Runtime task data is not part of the Compiled Brand Context.

### 14.2 Compiled checks

`compiledChecks` contains fully resolved Foundation checks and executable validator references.

```json
{
  "ruleElementId": "rule.no-cheap",
  "primitive": "term_prohibited",
  "phase": "postflight",
  "enforcement": "block",
  "params": {
    "terms": ["cheap"],
    "match": "word_boundary_ci",
    "appliesTo": "output"
  }
}
```

Runtime executes compiled Foundation checks without reading the Brand Manifest.

### 14.3 Canonical hash

`artifactHash` is SHA-256 over a canonical JSON payload.

The payload is the complete Compiled Brand Context except `artifactHash`.

Canonicalisation is:

1. recursively normalise every string and object key to Unicode NFC;
2. convert line endings inside every string and object key to LF, CRLF first and then any remaining CR;
3. after normalisation, sort object keys into lexicographic order by UTF-16 code unit, comparing code unit by code unit and treating a shorter key that is a prefix of a longer one as smaller. This is the ordering RFC 8785 specifies. It is **not** ECMAScript property enumeration order, which places integer-like keys first and in numeric order: `{"10":1,"2":2}` canonicalises with `"10"` before `"2"`, not the reverse;
4. preserve array order;
5. serialise JSON as UTF-8 without a byte-order mark;
6. use no insignificant whitespace;
7. escape strings and object keys exactly as section 14.3b specifies, and encode every other character directly as UTF-8 rather than as an optional escape variant;
8. serialise numbers using the ECMAScript-compatible shortest round-trippable IEEE-754 binary64 representation used by RFC 8785, with positive and negative zero both written as `0`; and
9. compute SHA-256 over those bytes.

A conforming implementation MUST reproduce the same hash for the same payload. Cross-language conformance vectors are part of the release suite and include notation thresholds, Unicode normalisation, non-BMP object keys, and CR and CRLF in both string values and object keys.

**OBDS numeric domain:** governed numbers are finite IEEE-754 binary64 values. Parsers with wider integer types MUST reject integer values that cannot be converted to binary64 without changing the integer value. NaN, positive infinity and negative infinity are invalid. Thus JSON numbers `1` and `1.0` canonicalise identically, while a wider integer such as `9007199254740993` is rejected rather than silently rounded.

Governed JSON and YAML inputs MUST reject duplicate mapping keys, including keys that become equal after the normalisation in steps 1 and 2. Two keys that differ only in line endings, such as `a\rb` and `a\nb`, collide after step 2 and MUST be rejected rather than silently collapsed. YAML authoring uses YAML 1.2 boolean semantics: only `true` and `false` are booleans. Scope array values are strings only.

A canonical hash proves byte identity after canonicalisation. It does **not** prove that a value still has the structure a consumer expects. Value-contract and shape validation are independent gates and MUST run before an approved manifest or compiled artefact is accepted.

Volatile build data is not part of the artefact.

### 14.3b String escaping

Step 7 of section 14.3 is stated here in full because it decides bytes, and
therefore hashes. It applies identically to string values and to object keys.

This is the string serialisation of RFC 8785 section 3.2.2.2, which is the same
serialisation ECMAScript `JSON.stringify` produces. It is written out rather
than only cited so that an implementation whose standard library differs has an
unambiguous target.

After the normalisation in steps 1 and 2, a string is serialised between two
`U+0022` quotation marks, and each character is emitted as follows.

| Character | Emitted as |
|---|---|
| `U+0022` quotation mark | `\"` |
| `U+005C` reverse solidus | `\\` |
| `U+0008` backspace | `\b` |
| `U+0009` character tabulation | `\t` |
| `U+000A` line feed | `\n` |
| `U+000C` form feed | `\f` |
| `U+000D` carriage return | `\r` |
| any other character in `U+0000` to `U+001F` | `\u00xx`, four hexadecimal digits, **lowercase** |
| every other character | **directly**, as UTF-8 |

Consequences worth stating, because each one is a place two implementations
could otherwise disagree:

- **`U+002F` solidus is not escaped.** `\/` is valid JSON and is not canonical.
- **`U+007F` delete is not escaped.** It is not in the `U+0000` to `U+001F`
  range, so it is emitted directly.
- **`U+2028` and `U+2029` are not escaped.** They are emitted directly, like any
  other non-ASCII character. An implementation that transports canonical output
  as text MUST NOT treat them as line terminators.
- **Hexadecimal digits in `\u` escapes are lowercase.** `\u001f`, never
  `\u001F`.
- **`\r` cannot occur** in canonical output. Step 2 converts every carriage
  return to a line feed before this step runs. The row is listed so the escape
  set is complete, not because canonical output can contain it.
- **Non-ASCII characters, inside and outside the Basic Multilingual Plane, are
  emitted directly.** There is no `\uXXXX` form for them and no surrogate pair
  in canonical output.

Cross-language vectors covering every row of this table, in string values and in
object keys, are part of the release suite.

### 14.3a Governed result hash

`artifactHash` identifies this exact artefact, including its rendered slots and
its compiler provenance. Two implementations that render governed truth
differently produce different artefacts and therefore different hashes, and that
is correct.

`governedResultHash` identifies the **governance decision** instead, and is the
value two independent implementations MUST agree on.

It is SHA-256 over the section 14.3 canonical JSON of this payload:

```json
{
  "kind": "obds-governed-result",
  "schemaVersion": "1.1.0",
  "manifest": { "id": "urn:obds:brand:example" },
  "target": {},
  "asOf": "2026-08-27T00:00:00Z",
  "selection": [
    { "elementId": "structure.brand",
      "subject": "structure.brand",
      "state": "defined",
      "valueHash": "sha256:..." }
  ]
}
```

Rules:

- `manifest` carries the manifest `id` only. The manifest `version` is excluded:
  a version bump that changes no element value MUST NOT move the hash.
- `target` is the Build Plan target object **verbatim, as the document carries
  it**, with `maxTokens` removed. Absent optional fields stay absent; an
  implementation MUST NOT insert its defaults before hashing, because two
  implementations with different defaults would then disagree.
- `maxTokens` is capacity, which is implementation-facing.
- `asOf` is the timezone-aware ISO 8601 string **exactly as the validated Build
  Plan carries it**. An implementation MUST NOT parse and re-serialise it for
  this payload, MUST NOT convert its offset and MUST NOT normalise `Z` to
  `+00:00` or the reverse. Two Build Plans that express the same instant with
  different offsets are different documents and produce different
  `governedResultHash` values; making them agree is a Build Plan authoring
  decision, not a compiler one.
- `selection` contains one entry per applicable element for the target, sorted
  by `elementId` in UTF-16 code-unit order. "Applicable" means the result of
  **applicability then precedence**, and nothing after it: scope matching,
  validity at `asOf`, and subject precedence under section 10. It is the
  governed result as resolved, **before** any projection or inclusion filtering.
- **`styleTexture` and `stateMap` MUST NOT change `selection`.** They are
  projection policies: they decide what the compiled artefact renders into its
  slots, not what the governance decision resolved to. Two targets differing
  only in those policies resolve the same governed truth and MUST carry the same
  `selection`, element for element and state for state. An implementation that
  builds `selection` from `includedElementIds`, or from any post-projection set,
  is not conforming.

  Both policies do remain inside `target`, and `target` is in this payload
  verbatim, so changing one still moves `governedResultHash`. That is correct
  and is not a contradiction: two Build Plans that ask for different projections
  are different governed requests, and the hash identifies the request together
  with what it resolved to. What the rule forbids is the projection silently
  changing **which truth was resolved**, which is the part two implementations
  must agree on.
- `subject` is the effective semantic subject, defaulting to the element `id`.
- `valueHash` is SHA-256 over the section 14.3 canonical JSON of the element
  `value`, and is `null` for any state other than `defined`. Content integrity
  comes from these hashes, so the payload does not depend on how the manifest
  document was serialised.
- Excluded from the payload: `sourceRefs`, `annotations`, `compiledChecks`,
  `validFrom`, `validTo`, compiler identity, tokenizer identity, slots, token
  counts and `artifactHash`.

A subject in hard conflict contributes no entry, and cannot silently collapse
with a subject that has no element: section 10.2 makes an unresolved conflict a
target failure, and section 13.5 produces no artefact for a failed target, so no
`governedResultHash` exists for such a build at all.

The exclusions are the contract. A section 27.2 governance-neutral PATCH, which
rotates source references or corrects annotations without changing Brand Truth,
MUST NOT move `governedResultHash`. A change to any selected element value MUST
move it.

`governedResultHash` is present in the Compiled Brand Context and is inside the
`artifactHash` payload, like every other artefact field. It does not replace
`artifactHash` and does not change its meaning.

### 14.4 Token budget

Token guarantees apply only to the declared tokenizer and version.

- An implementation MUST fail closed when the Build Plan declares a tokenizer ID or version that it does not actually execute. It MUST NOT count with one tokenizer and stamp another tokenizer identity into the artefact.
- `obds:whitespace-v1@1.0.0` is defined as: normalise to Unicode NFC, then count
  maximal runs of non-separator characters, where the separator set is the
  Unicode `White_Space` property together with U+001C, U+001D, U+001E and
  U+001F. Those four are not `White_Space` and are separators here.
- An implementation MUST record its **own** compiler identity and version in the
  artefact. It MUST NOT stamp an identity it did not execute, and in particular
  MUST NOT copy the identity the Build Plan declares when that is not the
  compiler that ran. The Build Plan's `compiler` block states the compiler the
  plan author used or expected; it is provenance, not a precondition, and an
  implementation does not fail closed merely because it is not that compiler.

  This differs deliberately from the tokenizer rule above. A tokenizer is a
  specified algorithm that any implementation can execute, so declaring one is a
  requirement any implementation can meet or refuse. A compiler identity is a
  product name, not an algorithm. A fail-closed rule on it would mean every
  independent implementation had to refuse the published examples, which would
  make the section 14.3a vectors unreachable to exactly the implementations they
  exist to prove agreement between.
- The reference implementation supports `obds:whitespace-v1@1.0.0` only. It is a deterministic budget estimator, not a claim of equivalence to any deployed model tokenizer. Production budgets SHOULD include headroom or use an implementation that supports the deployed model tokenizer exactly.
- HARD_BOUNDARIES and FACT_GROUNDING are never removed to fit a budget.
- STATE_MAP follows the declared target policy.
- STYLE_TEXTURE follows the explicit `styleTexture` setting.
- The compiler does not create emergency summaries.
- Overflow fails the target with per-slot diagnostics.

### 14.5 Human-readable view

A Markdown view MAY render the four slots in this order:

```text
[HARD_BOUNDARIES]
[FACT_GROUNDING]
[STATE_MAP]
[STYLE_TEXTURE]
```

The Markdown view is generated from the JSON artefact and is not maintained separately.

### 14.6 Search Cards

A Search Card is a generated, non-authoritative retrieval record for one Brand Element.

```json
{
  "kind": "obds-search-card",
  "schemaVersion": "1.0.0",
  "id": "urn:obds:search-card:example:design.logo.clear-zone",
  "manifest": {
    "id": "urn:obds:brand:example",
    "version": "1.0.0",
    "contentHash": "sha256:..."
  },
  "elementId": "design.logo.clear-zone",
  "label": "Logo clear zone",
  "summary": "Minimum clear space required around the primary logo.",
  "aliases": ["logo spacing", "protection zone", "clearspace"],
  "chapterRefs": ["chapter.logo-system"],
  "generator": {
    "id": "org.openbranddefinition.search-card-renderer",
    "version": "1.0.0"
  },
  "cardHash": "sha256:..."
}
```

Rules:

- Search Cards are generated from one exact manifest snapshot.
- They are never edited as independent brand truth.
- They MAY include a short summary and aliases for retrieval.
- They MUST point to exactly one complete Brand Element.
- They MAY select content but MUST NOT be used as final evidence for an answer or decision.
- The selected full element, applicable rules and known gaps remain authoritative.
- A Search Card MUST NOT introduce a rule, permission, prohibition, claim or value absent from its element.
- Rebuilding with the same manifest and renderer version MUST produce the same canonical card payload.
- `cardHash` covers the complete card except `cardHash`.

### 14.7 Reasoning Chapters

A Reasoning Chapter is a generated, non-authoritative view that places related approved elements together for multi-rule reasoning.

```json
{
  "kind": "obds-reasoning-chapter",
  "schemaVersion": "1.0.0",
  "id": "chapter.logo-system",
  "title": "Logo system",
  "manifest": {
    "id": "urn:obds:brand:example",
    "version": "1.0.0",
    "contentHash": "sha256:..."
  },
  "elementIds": [
    "design.logo.primary",
    "design.logo.clear-zone",
    "rule.logo.minimum-size"
  ],
  "content": "...",
  "renderer": {
    "id": "org.openbranddefinition.reasoning-chapter-renderer",
    "version": "1.0.0"
  },
  "chapterHash": "sha256:..."
}
```

Rules:

- Chapters are generated from approved elements and retain their element IDs.
- A chapter MAY weave FACT, KNOWLEDGE, RULES and STANCE into readable prose.
- It MUST preserve material meaning and MUST NOT add brand truth.
- It MUST NOT weaken enforcement, hide an unknown or convert an example into permission.
- Chapters are not maintained independently.
- The full selected elements remain available for exact lookup and audit.
- `chapterHash` covers the complete chapter except `chapterHash`.

### 14.8 One truth, two reasoning grains

OBDS uses two complementary grains:

- **elements** for exact lookup, states, references and checks;
- **chapters** for relationships, exceptions and multi-rule reasoning.

Search Cards are only the finding layer that connects a query to both grains.

A runtime SHOULD provide:

```text
selected Reasoning Chapters
+ selected full Brand Elements
+ all applicable HARD_BOUNDARIES
+ relevant known gaps
```

It SHOULD NOT provide Search Card summaries as the answer context.

---

## 15. Runtime contract

### 15.1 Load the exact context

Runtime MUST:

1. receive one exact target ID;
2. load the matching valid JSON artefact;
3. verify `artifactHash`, manifest reference and validity;
4. fail when no valid artefact exists; and
5. never fall back silently to another target, market, locale or channel.

Runtime does not resolve the Brand Manifest again in the normal production path. Context Assembly may inspect the exact manifest snapshot only when the declared no-hit policy requires truth resolution.

### 15.2 Context Assembly Contract

Context Assembly converts governed truth, derived views and task input into one exact Model Input Package.

```text
Compiled Brand Context
+ Search Cards
+ Reasoning Chapters
+ Task Input
        ↓
Context Assembly
        ↓
Model Input Package
        ↓
Model
```

Context Assembly is runtime configuration. It MUST NOT create or approve brand truth.

The normal production assembler MUST accept the validated Compiled Brand Context as its governed element universe. It MUST NOT rescan the Brand Manifest to rebuild hard boundaries, target scope or eligibility. The Compiled Brand Context therefore carries the target-scoped `elementRecords`, `availableElementIds` and `contextAssembly` policy used by assembly.

Manifest access is permitted only in the explicit `manifest_checked` no-hit resolution path. That access MUST use the exact manifest ID, version and content hash referenced by the Compiled Brand Context.

### 15.3 Model Input Package

```yaml
kind: obds-model-input-package
schemaVersion: 1.0.0
id: urn:obds:model-input:...
assembledAt: 2026-07-31T09:00:00Z
targetId: brand-review-global-en

deliveryMode: reasoning       # lookup | reasoning | full
applicationMode: review       # create | review | compliance

manifest:
  id:
  version:
  contentHash:

sources:
  compiledContextHash: sha256:...
  searchIndexHash:
  chapterSetHash:

retrieval:
  status: hit                 # hit | partial | no_match | low_confidence | access_filtered
  resolution: direct          # direct | widened | manifest_checked | unresolved
  truthOutcome: mixed         # defined | unknown | not_defined | not_applicable |
                              # prohibited | not_covered | access_limited | mixed | unresolved

selection:
  searchCardIds: []           # audit only; never sent as answer context
  reasoningChapterIds: []
  hardBoundaryElementIds: []
  factElementIds: []
  gapElementIds: []
  activeGuidanceElementIds: []

slots:
  hardBoundaries: ""
  factGrounding: ""
  stateMap: ""
  guidanceContext: ""
  taskInput: ""

tokenBudget:
  tokenizerId:
  tokenizerVersion:
  max:
  actual:

modelInputHash: sha256:...
assemblyHash: sha256:...
```

The exact model input is rendered in this fixed order:

```text
[HARD_BOUNDARIES]
[FACT_GROUNDING]
[STATE_MAP]
[GUIDANCE_CONTEXT]
[TASK_INPUT]
```

`modelInputHash` covers the exact UTF-8 bytes sent to the model after Unicode NFC and LF normalisation.

`assemblyHash` covers the complete Model Input Package except `assemblyHash`.

The rendered model input is a deterministic runtime projection, not a second source of Brand Truth. It SHOULD omit validator-only plumbing that does not help the model act correctly, MAY render equivalent structures compactly, and MAY omit repeated chapter blocks when the same full element is already present in HARD_BOUNDARIES, FACT_GROUNDING, STATE_MAP or ACTIVE_GUIDANCE. Any such projection is covered by `modelInputHash`; the complete governed element remains available in the Compiled Brand Context for audit and validation.

### 15.4 Assembly invariants

1. **Assembly starts from one exact Compiled Brand Context.**  
   `sources.compiledContextHash` is required and MUST equal the loaded artefact hash. Normal assembly MUST NOT reconstruct target scope or hard boundaries from the manifest.

2. **Search Cards never enter the model input.**  
   Their IDs and hashes may be recorded for audit.

3. **HARD_BOUNDARIES are complete for the target.**  
   Retrieval MUST NOT remove an applicable blocking or approval-requiring rule.

4. **FACT_GROUNDING uses full governed elements.**  
   Search Card summaries cannot replace facts, claims, rules or values.

5. **Relevant known gaps are included.**  
   A gap is relevant when it changes the answer, prevents an unsafe assumption or blocks execution.

6. **GUIDANCE_CONTEXT is non-authoritative.**  
   It may contain active guidance and Reasoning Chapters. It cannot add a rule, permission, exception, claim or fact.

7. **Full governed elements win.**  
   If a chapter or generated view materially conflicts with a linked element, assembly fails.

8. **Capability matches context.**  
   A lookup package cannot silently claim broad Brand Review capability.

9. **Token overflow cannot weaken truth.**  
   HARD_BOUNDARIES, required FACTS and decision-relevant gaps are not removed to fit the budget.

10. **The final input is hashed before the model call.**  
   Runtime records `modelInputHash` and `assemblyHash`.

### 15.5 Retrieval silence and no-hit resolution

> **Retrieval silence is not brand truth.**

A missing retrieval result may mean:

- the truth exists but was not retrieved;
- it was retrieved but not assembled;
- the manifest contains an explicit known gap;
- the target lacks access;
- the current manifest does not cover the question.

These outcomes MUST NOT collapse into one generic “not found”.

When `retrieval.status` is `no_match` or `low_confidence`, the runtime MUST resolve the result before making a brand claim:

```text
no match
→ widen retrieval
→ inspect linked chapters and aliases
→ check the exact manifest snapshot when needed
→ classify truthOutcome
→ answer, state the gap or stop
```

Rules:

- `resolution: unresolved` with `truthOutcome: unresolved` MUST NOT support a factual brand answer.
- `truthOutcome: not_covered` means the current manifest has no applicable element for the question.
- `not_covered` does not mean permitted or prohibited.
- `access_limited` does not imply that the truth is absent.
- An explicit `unknown`, `not_defined` or `not_applicable` state remains the authoritative knowledge outcome when found.
- `truthOutcome: prohibited` is a runtime decision outcome produced by an applicable explicit prohibit RULE, not by a Brand State.

### 15.6 Proportional brand application

> **Complete compliance. Selective expression.**

All applicable rules must be satisfied. Not every value, voice trait or brand principle must be visibly expressed in every artefact.

> **Values guide. Rules decide.**

Rules:

1. Only an explicit RULE may create a `violation` or non-compliance decision.
2. A value not visibly expressed is not automatically violated.
3. Absence is not contradiction.
4. A single artefact is not required to demonstrate the entire brand.
5. Expression review uses only `activeGuidanceElementIds` selected for the task.
6. Eligible but inactive guidance MUST NOT be reported as missing.
7. Brand values and STANCE may identify a material conflict only when the artefact actively contradicts them.
8. For an active `semantic-boundary`, evidence aligned with `isNot[]` MAY support `material_conflict`; missing evidence from `is[]` is at most an `opportunity`.
9. The runtime MUST NOT convert a value, example or repeated pattern into an undeclared rule.

Examples:

```text
Not acceptable:
Fail: The headline does not express innovation.

Acceptable:
Opportunity: Innovation is relevant to this campaign objective
but is not yet strongly expressed.

Acceptable:
Material conflict: The unsupported claim conflicts with the
active reliability principle.

Acceptable:
Violation: The output uses a prohibited claim.
```

### 15.7 Review Findings Contract

A review finding uses one of three categories:

| Category | Meaning | May fail compliance? |
|---|---|---:|
| `violation` | An explicit applicable RULE was breached | yes |
| `material_conflict` | The artefact actively contradicts active guidance | no, unless a separate rule requires approval |
| `opportunity` | The artefact could express active guidance more effectively | no |

`not_relevant` is not emitted as a finding.

A review result:

```yaml
kind: obds-review-result
schemaVersion: 1.0.0
targetId:
applicationMode: review
modelInputHash:
decision: pass              # pass | pass_with_suggestions | approval_required | fail
findings:
  - id:
    category: opportunity
    elementIds:
      - identity.value.innovation
    message:
reviewHash:
```

Rules:

- `violation` MUST reference at least one applicable RULE element.
- `material_conflict` and `opportunity` MUST reference active guidance.
- `fail` requires at least one blocking `violation`.
- `approval_required` requires an applicable approval-requiring RULE.
- `opportunity` never changes a pass into failure.
- A reviewer SHOULD report rule violations first, then material conflicts, then no more than the most relevant opportunities.

### 15.8 Checks before and after generation

```text
load context
→ assemble exact input
→ run preflight checks
→ call model
→ run postflight checks
→ optionally review
→ release, block or route
```

Rules:

- Mechanical enforcement consists only of compiled registered checks and executable versioned `validatorRef` checks.
- Preflight checks TASK_INPUT and required dependencies.
- Postflight checks generated output.
- A blocking preflight failure MUST stop before the model call.
- A blocking postflight failure MUST withhold the generated output.
- Semantic, human and external rules remain visible in HARD_BOUNDARIES but MUST NOT be reported as mechanically proven.
- Value and STANCE review MUST follow §15.6 and §15.7.

### 15.9 Runtime Decision Record

Every runtime attempt MUST create a Runtime Decision Record:

```json
{
  "kind": "obds-runtime-decision-record",
  "schemaVersion": "1.0.0",
  "recordId": "urn:uuid:...",
  "recordedAt": "2026-07-31T09:00:00Z",
  "targetId": "social-copy-de-at",
  "artifactHash": "sha256:...",
  "assemblyHash": "sha256:...",
  "modelInputHash": "sha256:...",
  "taskInputHash": "sha256:...",
  "decision": "released",
  "modelCall": {
    "called": true,
    "provider": "example",
    "model": "example",
    "requestId": null
  },
  "checkResults": []
}
```

Allowed decisions are `released`, `build_failed`, `assembly_failed`, `no_valid_artifact`, `preflight_blocked`, `postflight_blocked` and `approval_required`.

Rules:

- `artifactHash` is null when no valid artefact existed.
- `assemblyHash` and `modelInputHash` are null when Context Assembly was not used or when assembly failed before a valid package existed.
- `taskInputHash` covers task input after Unicode NFC and LF normalisation.
- `modelCall.called` MUST reflect the instrumented model adapter used for that attempt.
- Check results include phase, rule ID, primitive or validator ID, enforcement, result and message.
- Records MUST be exportable as an append-only ordered sequence.
- A Runtime Decision Record is auditable system evidence, not cryptographic proof that no other uninstrumented call occurred.

### 15.10 What compilation and assembly add

A small supervised brand chat MAY use a readable Brandbook directly.

Compiled Runtime and Context Assembly add value when a system must:

- stop on missing required truth;
- distinguish retrieval failure from absent brand truth;
- preserve explicit known gaps;
- reproduce the exact model input;
- apply the complete rule set without turning every value into a checklist;
- run mechanical checks; or
- prove that an unsafe task did not reach a model.

---

## 16. Governed Records Profile

Use when individual elements require independent approval, expiry or audit.

```yaml
governance:
  status: draft | approved | rejected | superseded
  approval:
    approvedBy:
    approvedAt:
    approvedContentHash:
```

Rules:

- record approval confirms an existing snapshot;
- it MUST NOT write state, value, scope or validity;
- production eligibility requires both an approved manifest and approved record where this profile applies;
- the approved hash covers normative record content; and
- profile use SHOULD be limited to elements that genuinely require independent governance.

Typical uses: claims, rights, market availability, legal text and local exceptions.

## 16.1 Release Approval Profile

Use only when a regulated or high-risk target requires a person to approve the exact canonical compiled payload that runtime uses.

A target declares:

```yaml
releasePolicy: artifact_approval_required
```

The Build Report carries:

```yaml
artifactApproval:
  approvedBy:
  approvedAt:
  approvedArtifactHash:
```

Rules:

- manifest approval remains required and is not replaced;
- `approvedArtifactHash` MUST equal `artifactHash`;
- approval confirms the canonical payload identified by `artifactHash` and MUST NOT modify the artefact;
- runtime MUST reject an artefact whose required approval is missing or mismatched; and
- rebuilds with the same `artifactHash` MAY reuse the existing approval because approval binds to the payload, not the build event.

This profile is optional. Foundation targets use `build_only` and incur no second approval step.

## 17. Claims and Evidence Profile

### 17.1 Claim

```yaml
canonicalWording:
allowedVariants: []
prohibitedVariants: []
claimType: factual | comparative | environmental | performance | award | testimonial | other
conditions: []
evidenceRefs: []
disclaimerRefs: []
riskLevel: low | medium | high | regulated
legalOwner:
```

A claim is usable only when required evidence and disclaimers are valid for the same scope.

### 17.2 Evidence

```yaml
type: test-report | certification | dataset | legal-opinion | study | approval | other
title:
issuer:
methodologySummary:
limitations: []
integrityHash:
```

### 17.3 Disclaimer

```yaml
canonicalText:
placement:
conditions: []
```

Evidence expiry or invalidation MUST make dependent claims unusable.

## 18. Assets and Rights Profile

```yaml
assetId:
kind: logo | font | template | image | video | guideline | other
variants:
  - mediaType:
    storageRef:
    contentHash:
rights:
  owner:
  licence:
  territories: []
  channels: []
  validFrom:
  validTo:
  aiEditingAllowed:
  generativeExpansionAllowed:
  aiTrainingAllowed:
referenceRole: normative | illustrative
```

Consequences:

- an unresolved normative asset blocks dependent production use;
- an unresolved illustrative asset raises a warning but does not change the governed value;
- illustrative files cannot hide rules or scope; and
- file integrity and rights are separate questions.

## 19. Localisation Profile

A Localisation Manifest defines explicit deviations for one exact target tuple. It is not read-time inheritance.

```yaml
id:
kind: localisation-manifest
baseManifestId:
baseManifestVersion:
target:
  market: JP
  locale: ja-JP
  jurisdiction: JP
status: approved
approval: {}
overrides:
  - baseElementId:
    baseElementHash:
    localElement: {}
    reason:
    driftStatus: current | base_changed | expired | unresolved
```

Rules:

- whole governed elements are overridden, never opaque fragments;
- the local element remains complete;
- no localisation-of-localisation;
- base hash drift blocks the override until review; and
- target dimensions never fallback implicitly.

## 20. Assurance and Lineage Profile

Adds:

- source-to-element lineage;
- transformation history;
- drift detection;
- source snapshot comparison;
- element replacement, split and merge history;
- assurance status; and
- optional independent review.

The Foundation element contract does not include `supersedes[]` on every element. When historical replacement matters, this profile may use a separate lineage record:

```yaml
kind: obds-element-lineage
fromElementIds: [identity.old-positioning]
toElementIds: [identity.positioning]
changeType: replace | split | merge
fromManifest:
  version:
  contentHash:
toManifest:
  version:
  contentHash:
```

The current manifest remains current truth. Lineage explains how IDs changed across versions.

## 21. Visual Operations Profile

The Visual Operations Profile adds deterministic geometry checks without turning OBDS into a renderer.

### 21.1 Render Geometry Record

A renderer MAY emit a geometry evidence record for the exact artefact it produced:

```json
{
  "kind": "obds-render-geometry-record",
  "schemaVersion": "1.0.0",
  "targetId": "banner-300x250",
  "renderedArtifactHash": "sha256:...",
  "canvas": {
    "width": 300,
    "height": 250,
    "unit": "px",
    "origin": "top-left"
  },
  "objects": [
    {
      "objectId": "brand-logo-1",
      "roles": ["brand-logo"],
      "elementRefs": ["design.logo.primary"],
      "box": {"x": 240, "y": 16, "width": 44, "height": 18},
      "metrics": {}
    }
  ]
}
```

Rules:

- coordinates increase rightward and downward from the top-left origin;
- `box` is an axis-aligned bounding box in the declared canvas unit;
- transformed or rotated geometry MAY use a conservative bounding box;
- geometry requiring more precision uses `validatorRef`;
- the record is runtime evidence, not Brand Truth.

### 21.2 Visual Check Registry v1

The registry is deliberately small.

| Primitive | Fails when | Typical purpose |
|---|---|---|
| `visual.min_size` | a selected object metric is below the declared minimum | logo, CTA, type legibility |
| `visual.clear_zone` | another selected object enters the protected object's declared keep-out region | logo and identity protection |
| `visual.contains` | a selected object leaves its declared container or inset | safe zones, Frame, Shutter |
| `visual.no_overlap` | selected object sets intersect | legal, product, CTA, logos |

Rules:

- checks operate on one Render Geometry Record;
- selectors use declared composition roles and MAY additionally filter by element reference;
- numeric parameters and `elementValueRef` values are resolved before the check runs;
- units must match or have an explicitly declared conversion;
- visual checks are deterministic only for geometry actually present in the evidence record;
- unsupported geometry fails or routes to `validatorRef`, never to a guessed result.

Anything richer than this closed set belongs behind a versioned `validatorRef`.

### 21.3 Composition Profile v1

Composition is Brand Truth only where the brand has actually decided it.

The profile adds four DESIGN or STRUCTURE value contracts. It does not add a new family.

#### Composition roles

```yaml
id: design.composition.roles
family: design
kind: composition-role-system
nature: fact
state: defined
value:
  roles:
    - id: brand-logo
      category: identity
    - id: partner-logo
      category: identity
    - id: hero-product
      category: product
    - id: headline
      category: copy
    - id: supporting-copy
      category: copy
    - id: cta
      category: interaction
    - id: legal
      category: legal
```

Roles describe what an object **is** in a composition. They do not prescribe coordinates.

#### Identity hierarchy

```yaml
id: structure.identity-hierarchy
family: structure
kind: identity-hierarchy
nature: fact
state: defined
value:
  tiers:
    - [brand-logo]
    - [partner-logo, retailer-logo]
```

Earlier tiers have higher identity priority. Roles in one tier are equal unless another explicit relation says otherwise.

Hierarchy MUST NOT be inferred from the size of rendered logos.

#### Omission priority

```yaml
id: design.composition.omission-priority
family: design
kind: omission-priority
nature: fact
state: defined
value:
  neverOmit:
    - brand-logo
    - required-legal
  omitOrder:
    - supporting-copy
    - optional-cta
```

`neverOmit` and `omitOrder` express what the brand is willing to sacrifice when space is insufficient. They do not define how the renderer removes or rewrites content.
A Render Geometry Record claiming Composition conformance MUST contain every role listed in `neverOmit`. Absence is a conformance failure and is not treated as a vacuous pass of other geometry checks.

A role absent from both lists has no declared omission priority. The renderer MUST NOT invent one when the decision matters.

#### Composition relations

```yaml
id: design.relation.logo-spacing-clear-zone
family: design
kind: composition-relation
nature: fact
state: defined
value:
  between:
    - design.spacing.standard
    - design.logo.clear-zone
  relation: additive
```

Closed relation types:

- `additive`: both effects accumulate;
- `subsuming`: one declared `dominantElementId` contains or replaces the effect of the other;
- `exclusive`: both may not govern the same interaction at once; unresolved co-application is a conflict.

A relation changes no source value. It declares how already valid values interact.

### 21.4 What the profile does not define

The Composition and Visual Operations Profiles do **not** define:

- pixel positions;
- per-format layout templates;
- per-aspect-ratio capacity tables;
- fixed preserve/may-change matrices;
- HTML, CSS or renderer code;
- animation timelines; or
- model prompts.

> OBDS defines the permissible design space. The render layer produces one solution inside it. The validator proves that the solution stayed inside.

---

# Checks, tools and conformance

## 22. What validation checks

### 22.1 Structure

Checks schemas, types, enums, state/value conditions and profile declarations.

### 22.2 Meaning and references

Checks references, scopes, contracts, validity, supersession and conflicts.

### 22.3 Approval

Checks manifest approval and any activated record-level profile.

### 22.4 Files, hashes and derived views

Checks files, hashes, indexes and optional signatures.

When Search Cards or Reasoning Chapters are published, validation also checks:

- exact manifest binding;
- one valid element per Search Card;
- all chapter element IDs resolve;
- cards and chapters are marked non-authoritative;
- derived payloads do not contain unresolved phantom IDs; and
- canonical card and chapter hashes reproduce.

When Context Assembly is used, validation additionally checks:

- all applicable HARD_BOUNDARIES are present;
- Search Card text is absent from the final model input;
- selected FACTS and gaps resolve to full elements;
- active guidance is eligible for the target;
- retrieval no-hit status is resolved before a factual brand answer;
- exact model-input and assembly hashes reproduce; and
- Review Results follow the proportional application contract.

When the Design Space or Visual Operations Profiles are used, validation additionally checks:

- measurement quantity kinds, systems and bounds;
- registered composition relations and their referenced element IDs;
- role references used by hierarchy and omission-priority records;
- every `RULES.value.requiresDefinedRefs[]` dependency;
- Render Geometry Record structure and units;
- every declared Visual Check Registry primitive; and
- source contradiction and measurement-observation records remain non-authoritative until explicitly curated into Brand Truth.

### 22.5 Qualitative review

Checks STANCE, voice and contextual fit. It MAY use human or model judgement but MUST NOT override failed deterministic validation.

## 23. Optional clarity check

Software cannot prove completely that an element makes sense on its own.

Reference tools MAY show an element to a model with minimal context and ask it to:

1. state what the element applies to; and
2. identify missing information needed to apply it.

Results SHOULD be classified as:

- `stated`;
- `inferred_guess`; or
- `cannot_tell`.

This check is advisory and depends on the model and prompt. Tooling MUST record both versions. The result is not a conformance requirement and does not replace human review.

## 24. Selective extraction and curation

> Extraction may locate evidence. It may not manufacture brand truth.

The source is evidence, not the model. An importer MUST NOT mirror source navigation, page count or prose volume by default.

Each relevant source unit is routed to one primary destination:

1. **MANIFEST:** approved operational brand truth that changes an answer, check, approval or execution decision;
2. **DOSSIER:** useful non-authoritative history, rationale, narrative texture or inspiration;
3. **EXTERNAL AUTHORITY:** dynamic product, asset, rights, claim, market or legal data owned by another system;
4. **EXCLUDE:** navigation, duplication, generic advice, obsolete guidance or material without operational effect.

Unresolved material remains `unresolved`; it is not forced into one of the four destinations.

Reference tooling SHOULD enforce:

- paths or kinds come from the specification or a human-approved extension act;
- extraction produces observations or candidates, never approvals;
- unknown mappings are reported, not invented;
- source structure does not determine manifest structure;
- generic advice is excluded unless explicitly adopted as brand-specific truth;
- observed patterns do not become binding rules;
- `unknown` dependencies do not create policy;
- technical portal themes, fonts or metadata are not brand truth unless the source explicitly gives them that authority;
- examples do not approve claims, assets, markets or permissions;
- image-only meaning is flagged for human review;
- every completeness claim identifies the source modalities actually assessed;
- measurements taken from figures are stored as `measured` observations and remain non-authoritative until curated and approved;
- an `unknown` caused by source absence SHOULD retain a curation assessment describing what modalities and source locations were searched;
- source contradictions are recorded separately and do not create a new Brand State;
- source location is provenance, not payload; and
- compression or deduplication produces a source-to-disposition trace appropriate to any declared coverage claim.

Adding a new registered path or kind is a separate, versioned human decision. Extraction MUST NOT do it automatically.

## 25. Track what changed during migration or compression

A migration, merge, deduplication or compression that claims `complete` coverage MUST account for every declared source unit with one outcome:

- `represented`: retained directly in one or more Brand Elements;
- `condensed`: materially represented in a governed aggregate with declared compression;
- `routed`: intentionally assigned to runtime, source archive, Dossier or another named layer;
- `excluded`: intentionally omitted with a reason; or
- `unresolved`: not yet safely modelled.

Each disposition MUST identify the target element or destination where applicable. A clean target set does not prove that no source truth was lost.

## 26. Conformance claims

Conformance is demonstrated by normative tests, not self-description.

An implementation MAY claim conformance only when:

1. it passes every required case in the official Conformance Suite for the exact OBDS version and named profile;
2. it publishes or retains the machine-readable suite result;
3. the result identifies implementation name and version, suite hash, profile, passed count and failed count; and
4. no required case was skipped or changed.

A tool MAY say “uses OBDS concepts” without conformance. It MUST NOT say “OBDS conformant” unless the applicable suite is green.

### 26.1 OBDS Foundation

Requires unique element IDs, exact internal reference resolution, explicit `valueContractRef` resolution, Foundation Validator Registry execution, value-shape hash verification, exact schema hash verification, semantic schema validation, declared value-contract validator execution, deterministic shape-aware manifest change reports, immutable approved snapshots, canonical hashes, governed units and honest curation declarations where used.

When an implementation claims source-to-manifest curation support, it also retains a source-to-disposition report and demonstrates the Ground Rules in §5 through the published Curation Review Fixtures. Semantic curation judgement is not represented as fully parser-proven.

### 26.2 OBDS Compiled Runtime

Additionally requires exact Build Plans, `requiresDefined`, every required element present in the produced context, explicit context selection, no artefact for a failed target, canonical JSON artefacts, reproducible hashes, a `governedResultHash` that matches section 14.3a for the same manifest and Build Plan, Foundation Check Registry v1, exact target loading, Runtime Decision Records, zero instrumented model calls after failed build or blocking preflight, withheld output after blocking postflight and per-slot token reporting.

An implementation claiming OBDS Context Delivery additionally verifies generated Search Cards and Reasoning Chapters, keeps them non-authoritative and demonstrates that final answers use full selected elements rather than Search Card summaries alone.

### 26.3 OBDS Context Assembly Profile

Additionally requires:

- one exact validated Compiled Brand Context as the normal assembly input;
- one exact Model Input Package per model call;
- complete applicable HARD_BOUNDARIES;
- full-element FACT grounding;
- explicit active guidance;
- no-hit resolution;
- exact model-input and assembly hashes;
- proportional review categories; and
- no non-compliance decision derived solely from a value, STANCE or missing expression.

### 26.4 OBDS Text Profile

Additionally requires applicable IDENTITY, RULES, CONTEXT and localisation behaviour.

### 26.5 OBDS Visual Operations Profile

Additionally requires:

- DESIGN, referenced assets and applicable visual rules;
- Measurement Contract v2 validation where v2 fields are used;
- valid Render Geometry Records;
- the Visual Check Registry v1 for claimed deterministic spatial checks;
- exact separation between declared Brand Truth and measured observations; and
- no visual-conformance claim for geometry that was not present in the evidence record.

### 26.6 OBDS Composition Profile

Additionally requires:

- a valid composition-role system for every role referenced by the profile;
- valid identity-hierarchy references;
- valid omission-priority references;
- valid composition-relation references;
- explicit conflict on unresolved `exclusive` co-application; and
- no renderer-generated coordinates stored as Brand Truth.

### 26.7 OBDS Claims Profile

Additionally requires the Claims and Evidence Profile and dependency validation.

### 26.8 OBDS Localisation Profile

Additionally requires exact locale overlays and no silent locale fallback.

### 26.9 OBDS Operations Profile

Additionally requires all declared profiles, package integrity, Runtime Decision Record export, output traceability and documented rollback.

The implementation MUST state the exact OBDS version, profile and scope of the claim.

---

## 27. Versioning

### 27.1 Specification stability

OBDS 1.0 is the first stable specification contract. `1.0` means the Foundation and profile mechanism are stable enough for independent implementations to build against them. It does not mean that no future profiles will be added.

Specification releases use Semantic Versioning:

- **MAJOR:** a breaking change to an existing normative contract;
- **MINOR:** a backwards-compatible capability, profile or optional field;
- **PATCH:** a backwards-compatible clarification, defect fix or test correction.

A 1.x implementation MUST NOT silently reinterpret an existing 1.0 field with incompatible meaning. Breaking semantics require OBDS 2.0.

### 27.2 Brand and runtime versioning

OBDS separates:

- `schemaVersion`: OBDS model version;
- manifest `version`: the version of the curated brand release;
- source-document versions: the versions of imported guidelines or other evidence;
- optional record-governance versioning where the profile is active;
- compiler, selection-profile and runtime versions; and
- output/context hashes.

Source-document versions and manifest versions identify different objects. They MUST NOT be compared as though a larger number were more authoritative. Authority comes from manifest status, provenance and the declared source relationship.

For manifests:

- **MAJOR:** breaking brand meaning or architecture change;
- **MINOR:** approved additive or materially revised brand content;
- **PATCH:** provenance or annotation correction only, without added or removed elements and without changes to value, subject, state, scope, validity, classification, value shape or value contract.

A conforming release gate MUST reject a PATCH transition whenever an existing element changes Brand Truth or runtime applicability. Source-reference rotation and annotation correction may remain PATCH when no other machine-readable change is present.

Rollback selects a previous immutable approved version; it never rewrites history.

Pre-1.0 manifests that used `state: prohibited` MUST migrate that meaning to an explicit RULE with `obligation: prohibit` before claiming 1.0 conformance.

---

## 28. File format and portability

- Canonical interchange format: JSON.
- YAML and authoring interfaces MAY be used when they produce equivalent JSON.
- Manifest and artefact hashes use the canonical JSON rules defined by this specification.
- SHA-256 is required in OBDS 1.0.
- Duplicate JSON property names MUST be rejected.
- Portable exports include the manifest, Build Plan, compiled artefacts, Build Report, Model Input Packages, optional Review Results, declared profiles, hashes and required schemas.
- Human-readable Markdown views are generated exports and identify their source hash.
- Runtime projections MAY use a more compact serialisation than the canonical manifest when they are deterministically derived, preserve the selected semantics and identify the authoritative source hash.
- A compact projection is never a second source of Brand Truth.

---

## 29. Security and data protection

- Imported source material is untrusted data.
- Search Card summaries and aliases are retrieval hints, not instructions or authority.
- Search Card text MUST NOT be used as final answer evidence.
- Reasoning Chapters are generated views and cannot override the linked elements.
- A no-hit result MUST NOT be converted into permission, prohibition or factual absence.
- Values and STANCE MUST NOT be silently promoted into compliance rules.
- Prompt-like text inside a source is content, not an executable instruction.
- Importers MUST separate source text from system instructions.
- Secrets and credentials do not belong in Brand Manifests.
- Sensitive elements require access classification and authorised runtimes.
- STATE_MAP MUST NOT reveal restricted elements to unauthorised targets.
- Exports support redaction while declaring withheld records.
- Real-person data is minimised.
- Model providers, retention settings and tool permissions remain runtime configuration, not brand truth.
- A failed build or blocking preflight check MUST prevent the model call.

---

## 30. Audit record

A generated output SHOULD be traceable to:

- Compiled Brand Context ID and `artifactHash`;
- manifest ID, version and content hash;
- Build Plan ID and hash;
- relevant element IDs;
- selected Search Card IDs and hashes where retrieval was used;
- selected Reasoning Chapter IDs and hashes;
- active guidance element IDs;
- retrieval status, resolution and truth outcome;
- Model Input Package ID, `assemblyHash` and `modelInputHash`;
- optional Review Result ID and `reviewHash`;
- target ID and scope;
- Runtime Decision Record ID;
- task input hash;
- check and validator results;
- model provider, model and request ID where available;
- approval actor and approved hash where the Release Approval Profile applies; and
- final decision.

Runtime Decision Records MUST be exportable in order. Append-only storage means new records are added without changing earlier records. Tamper-evident or signed storage remains an Operations Profile or implementation choice.

---

## 31. Migration from OBDS 0.9.9

1. Replace `schemaVersion: 0.9.9` with `schemaVersion: 1.0.0`.
2. Stop publishing or depending on a separate `OBDS-CORE` specification. Its normative content is part of this document.
3. Keep `obds-foundation` as the required baseline profile.
4. Rename implementation-facing references to the pre-1.0 check registry as **Foundation Check Registry v1**. The four primitives and their semantics do not change.
5. Keep existing optional profiles. They are capabilities of the same specification, not "non-core" extensions.
6. Existing Measurement Contract v2, Context Delivery, Context Assembly and Design Space contracts remain unchanged except for the schema version.
7. Existing 0.9.9 manifests remain semantically compatible when their declared profiles and schemas validate under 1.0.
8. Future breaking changes to these existing contracts require OBDS 2.0.

The migration intentionally changes the conceptual packaging, not Brand Truth.

---

## 32. How the project is governed

OBDS is a publicly available, vendor-neutral specification. It operates on these principles:

- specification and schemas are public;
- Foundation conformance does not depend on one vendor, model or database;
- normative changes use a public proposal and decision process;
- migrations and tests accompany breaking changes;
- reference tooling is published together with the specification;
- vendor extensions are optional and namespaced; and
- trademarks or certification marks have transparent rules.

### 32.1 Use and licensing

OBDS is released under two standard licences. Neither licence text is modified.

- **Specification and documentation: Creative Commons Attribution 4.0 International (CC BY 4.0).** This covers this document and the accompanying prose: architecture, changelog, migration notes, quickstart, test requirements, governance and contribution documents, and the project website.
- **Implementation layer: Apache License 2.0.** This covers the schemas, the value schemas, the release metadata, the reference implementation, the conformance suite and the machine-readable examples.

Commercial implementation is permitted and requires no separate permission. Building an OBDS implementation, shipping it inside a commercial product, running it in production, offering it as a service, or delivering OBDS work to paying clients requires nothing beyond compliance with the two licences above. There is no commercial licence to obtain, no evaluation period and no distinction between commercial and non-commercial users.

Modification and redistribution are permitted on the terms of the applicable licence. A modified specification or a modified conformance suite MUST state that it was modified and MUST NOT be presented as a published OBDS release, and MUST NOT reuse the version identifier of a published release.

Neither licence grants trademark rights. CC BY 4.0 section 2(b)(2) and Apache License 2.0 section 6 exclude them explicitly. Truthful statements of compatibility, such as "implements OBDS 1.0", need no permission. Use of the project name as a product name, use of the logo, claims of official status, and any future certification claim are governed separately by the published trademark policy. No certification programme is live and no certification mark is registered.

No claim is made to the underlying ideas, principles or methods. Building a different system from similar ideas has never required permission and does not require it now.

The licence texts, the licence mapping and the trademark policy are published at `https://openbranddefinition.org`.

---

## 33. Release files for 1.0

A credible OBDS 1.0 release includes:

1. one normative specification: `OBDS-1.1.5.md`;
2. machine-readable schemas for the Foundation and declared profiles;
3. a Foundation reference compiler and conformance suite;
4. Context Delivery reference tests;
5. Context Assembly reference tests;
6. Design Space and Visual Operations reference tests;
7. one aggregate test result;
8. migration notes and changelog; and
9. neutral examples.

There is no separate CORE specification. Foundation semantics live in the main specification.

---

## 34. Closing rule

> Declare the design space. Do not prescribe the layout. Relationships and bounds are Brand Truth when the brand decides them. Coordinates remain renderer output.
