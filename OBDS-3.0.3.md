# Open Brand Definition Specification (OBDS)

## OBDS 3.0: Stable Specification

**Version:** 3.0.3  
**Status:** Stable  
**Date:** 2026-09-04  
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

3.0.0 is the Semantic Closure release. It adds no Brand State, no profile, no
capability and no architecture. It closes five places where one governed
semantic was stated once and implemented twice, so that two conforming readers,
two entry points or two executors could reach different governed answers from
the same approved bytes:

- **A. Governed input.** One interchange contract at every governed reader,
  including the rule that a governed document has an object root (section 28.1).
- **B. Governed identity.** Where an artefact names a manifest it binds the
  manifest's `id`, `version` and `contentHash` together, and identity-bearing
  positions reject the characters that a canonical hash cannot tell apart
  (section 8.0b).
- **C. RULE enforcement.** A deterministic Foundation RULE declares at least one
  registered Foundation check, RULE-level `validatorRef` is removed, and a check
  is validated at the stage it is written as well as at the stage it is executed
  (sections 11.4, 11.5, 11.5a).
- **D. Runtime contract enforcement.** Every governed document is validated
  against its published 3.0 contract before any of its fields is read, and every
  required hash is reproduced from the payload rather than compared between two
  supplied claims (sections 14.3d, 15.11).
- **E. Conflict relevance.** One relevance model governs the compiler, Context
  Assembly and the runtime (section 10.2a).

Each of these is a breaking correction to an existing normative contract, which
is why 3.0.0 is MAJOR under section 27.1.

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
createdAt: '2026-07-20T10:00:00+02:00'
updatedAt: '2026-07-20T10:00:00+02:00'
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
  approvedAt: '2026-07-20T10:00:00+02:00'
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

### 8.0a Canonical identity

An element `id` and an effective `subject` are semantic identities: they decide
which truth is selected, which element a reference resolves to, and in what
order the governed result of section 14.3a is hashed.

Every governed string is compared after Unicode NFC. Identities are no
exception:

- two identity strings are the same identity exactly when their NFC forms are equal;
- element `id` uniqueness under section 8.6, subject grouping and comparison under section 10.2, every internal element reference under section 7, `requiresDefined`, `requiresDefinedRefs`, `elementValueRef` and the `selection` ordering of section 14.3a MUST all compare and sort the NFC form; and
- an implementation MUST reject a manifest in which two elements carry canonically equivalent ids, exactly as section 9 rejects canonically equivalent duplicates in a scope collection.

Only NFC. The line-ending folding of section 14.3 step 2 is a serialisation
rule for canonical bytes and does not apply to identity: `a\rb` and `a\nb` are
two identities, and an implementation that folded them here would reject two
distinct elements as one duplicate.

This is a comparison rule, not a rewriting rule. The stored representation of an
approved manifest is unchanged, and `approval.contentHash` is unaffected,
because it is computed over canonical bytes, which are already NFC.

The same rule governs the other governed strings that are compared rather than
rendered: value contract ids and the `valueContractRef` that names one, and the
vocabulary values a target matches against, such as `stateMap.kinds` against an
element `kind`. Section 9 already states it for scope values.

Without it one approved manifest can produce two different governed results: the
same `contentHash` covers an NFD and an NFC spelling of one subject, while raw
byte comparison treats them as two subjects, so a broad value and the narrower
override meant to replace it both survive as governed truth.

Elements MAY carry an optional `classification`: an opaque identifier string.
OBDS assigns it no meaning, defines no vocabulary for it and enforces no policy
from it. It is governed metadata: section 13.6 change reports track it and
section 27.2 forbids changing it in a PATCH release. A runtime MAY consume it for
access policy, which OBDS does not define.

### 8.0b Identity-bearing positions and identity binding

Section 8.0a says how two identity strings are compared. This section says
**where** an identity string appears and **what an artefact that names another
artefact's identity has to bind**. Both were left to the implementation, and
both are places where the same approved bytes reached two governed answers.

**One coordinate system.** A governed document position is written as the path
to it inside that document, and the same path means the same thing in every
governed artefact that carries it. `manifest.id` is the identity of the manifest
this document is about, in a Compiled Brand Context, in a Model Input Package and
in a Brand Manifest alike. Naming the manifest's own identity `id` in one
artefact and `manifest.id` in another is what made the four enumerations below
impossible to compare.

The identity-bearing positions are:

| Artefact | Positions |
|---|---|
| Brand Manifest | `id`, `version`, `valueContracts[].id`, `elements[].id`, `elements[].subject`, `elements[].kind`, `elements[].valueContractRef`, `elements[].scope`, `elements[].value.references[]`, `elements[].value.requiresDefinedRefs[]`, `elements[].value.checks[].params.elementValueRef.elementId` |
| Build Plan | `id`, `version`, `manifestRef.id`, `manifestRef.version`, `targets[].id`, `targets[].requiresDefined[]`, `targets[].scope`, `targets[].contextAssembly.eligibleGuidanceIds[]`, `targets[].styleTexture.elementIds[]`, `targets[].stateMap.kinds[]` |
| Compiled Brand Context | `id`, `targetId`, `manifest.id`, `manifest.version`, `build.planId`, `build.compilerId`, `includedElementIds[]`, `availableElementIds[]`, `elementRecords[].id`, `elementRecords[].kind` |
| Model Input Package | `id`, `targetId`, `manifest.id`, `manifest.version`, `selection.*[]` |

**A position that bears identity in one artefact bears identity in every
artefact that carries the same path.** `manifest.version` decides which approved
brand release a governed decision was made against; it was an identity position
in a received Model Input Package and not in the Manifest or the Build Plan that
produced it, so a `version` differing only in line ending passed validation and
build with an identical `contentHash`, `planHash` and `artifactHash`, and the
runtime then refused what the compiler had approved.

**Admissible characters.** An identity string MUST NOT contain U+000D CARRIAGE
RETURN or U+000A LINE FEED. Section 14.3 step 2 folds line endings when it
computes canonical bytes, so two identities differing only there are one hash
and two strings: whichever way an implementation compares them, one of the two
comparisons is wrong. Rejecting them is the only answer that is right in both.

U+0085 NEXT LINE, U+2028 LINE SEPARATOR and U+2029 PARAGRAPH SEPARATOR are
**preserved**. They survive step 2 unchanged, they are ordinary characters under
section 28.1, and section 14.3b escapes two of them. They are admissible in an
identity and MUST NOT be rejected or folded.

```text
CR   rejected
LF   rejected
NEL  preserved
LS   preserved
PS   preserved
```

This set is closed. An implementation MUST NOT reject a further character at an
identity position, because doing so would refuse a manifest another conforming
implementation accepts.

**Identity binding.** Where a governed artefact names the manifest another
artefact is about, naming it is not enough. All three of

```text
manifest.id
manifest.version
manifest.contentHash
```

MUST agree between the two artefacts before either is used for a governed
decision, and `manifest.id` is compared on its canonical form under section 8.0a.

```text
same approval.contentHash
→ cannot resolve to different governed identity
```

Reproducing the hashes of two documents proves each is intact. It does not tie
them to each other: a Model Input Package naming another brand, another approved
version or another target, with every one of its own hashes correctly recomputed,
is internally perfect and about something else. Section 15.11 states where the
binding is enforced.

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
  productFamilies: [example-family]
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

1. named in the target's `requiresDefined`, in its
   `contextAssembly.eligibleGuidanceIds`, or named as a dependency by an
   applicable RULE through `requiresDefinedRefs` or `elementValueRef`;
2. a `defined` RULES element that would govern this build if it won, which it
   does when its `enforcement` is `block` or `require_approval`, or when its
   `obligation` is `prohibit`, because section 14.1 places both in
   HARD_BOUNDARIES; when it declares `requiresDefinedRefs`, so it would add
   requirements this target must satisfy; or when it declares `checks`, so it
   would contribute compiled checks;
3. a `defined` element of `nature: fact` outside `family: rules`, so it belongs
   in FACT_GROUNDING;
4. carried into STATE_MAP by the target's declared `stateMap` policy; or
5. carried into STYLE_TEXTURE by the target's declared `styleTexture` policy.

The first three are unconditional: a target cannot opt out of its own
requirements, its hard boundaries or its fact grounding. The last two follow the
policy the target declared, so a target that selects narrowly is not failed by a
conflict it never reads.

The list is a reading of the rule above it, never a narrowing of it. Where the
list and the rule disagree, the rule governs: if resolving the conflict the
other way would change what this target requires, blocks, prohibits or checks,
the subject is decision-relevant. Reading the list as the whole rule left a case
open until 1.1.6, in which two competing non-blocking RULES cancelled a declared
dependency between them: the target built while its dependency was `unknown`,
and deleting one of the two conflicting RULES made the same target fail.
Repairing a manifest defect must never make a governed build less valid.

**An irrelevant conflict MUST NOT be silently discarded.** The Build Report MUST
still carry it in `conflicts[]`, marked as not decision-relevant for this target,
so an operator sees a manifest-level defect that this particular target happened
not to touch. It is a manifest problem either way; it is only this target's
problem when the target reads it.

Failing a target on a conflict it cannot observe is not fail-closed, it is
fail-arbitrary: the same manifest would block or build depending on which
unrelated subject a curator happened to leave unresolved.

**One relevance model.** The rule above is the only conflict-relevance model in
OBDS, and it is decided once, at build time, by the compiler. A Compiled Brand
Context therefore cannot carry an unresolved decision-relevant conflict: either
the subject was decision-relevant to the target and no artefact was written, or
it was not and the artefact is complete. Context Assembly and the runtime
consume that decision and MUST NOT re-derive it, re-weigh it or relax it. A
projection of the compiled artefact, a Search Card, a Reasoning Chapter or a
rendered slot, cannot change relevance, because relevance was settled before
the projection existed.

The materialisation of section 13.5a happens after this decision and MUST NOT
alter it. A default that a compiler writes into a compiled check is a value the
target already had; it never makes a subject decision-relevant that was not, and
never removes relevance from one that was.

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
condition: {}
requirement: {}
references: []
requiresDefinedRefs: []
```

`enforcement` defines what happens when the rule is violated. `validationMode` defines how the violation is established.

`references[]` explains or links a rule. It does not automatically make the referenced element a prerequisite.

`requiresDefinedRefs[]` is explicit policy. When an applicable rule lists an element there, that referenced element MUST resolve to one applicable `defined` value before the rule can be used. If it does not, the target fails rather than pretending that the rule's extension is known.

This is intentionally separate from `references[]`: explanation does not create dependency, but an explicitly declared dependency does.

- `deterministic` requires at least one registered Foundation `check`. The
  published RULE value contract states this, and the compiler enforces it.
- A RULE value MUST NOT carry `validatorRef`. Foundation Validator Registry v1
  is closed, has one entry, and that entry applies to value contracts of kind
  `colour` with the element value as its input (section 11.5a), so the set of
  rule-level references that could ever resolve was empty. A contract whose
  `deterministic`-with-no-checks branch depends on an unsatisfiable alternative
  is not a branch, it is a hole: `validationMode: deterministic` with
  `checks: []` validated in 1.x and 2.x and produced a rule nothing enforced.
  The property is removed in 3.0; a value that carries it is rejected.
- `checks[]` is typed. Every entry MUST name a registered Foundation Check
  Registry v1 primitive with parameters that primitive accepts. An unregistered
  primitive or an unregistered parameter value is refused where the rule is
  written, not only where it is compiled.
- A structured `condition` alone is not a validator.
- Rules without a registered check MUST use `semantic`, `human` or `external`.
- A semantic or human-reviewed rule MAY block output, but tooling MUST NOT report it as mechanically proven.

Qualitative principles without a defined violation belong in STANCE or KNOWLEDGE.

**Single prohibition rule:** Brand prohibition is represented only here, through `obligation: prohibit`. `state: prohibited` is not part of OBDS 1.0 Brand States. This keeps prohibition, enforcement, evidence and scope in one machine-readable place.

### 11.5 Foundation Check Registry v1

The Foundation registry is deliberately small and closed. Rule authors write data, not code.

Every check is a pure function of its declared phase input and parameters. Implementations MUST use Unicode NFC normalization before text comparison. `case_insensitive` uses Unicode default case folding.

| Primitive | Default phase | Fails when | Parameters |
|---|---|---|---|
| `term_prohibited` | postflight | a prohibited term occurs | `terms[]`, `match: exact \| case_insensitive \| word_boundary_ci \| normalized_whitespace_ci`, `appliesTo: output \| task_input` |
| `term_required` | postflight | required terms are absent | `terms[]`, `mode: any \| all`, `match` |
| `literal_required` | postflight | a required literal is absent | `literal` or `elementValueRef`, `match: exact \| normalized_whitespace \| normalized_whitespace_ci` |
| `length_max` | postflight | text exceeds the limit | `max`, `unit: characters`, `appliesTo: output \| task_input` |

**Match modes.** The registry defines five, and each is a different question:

| Mode | Comparison |
|---|---|
| `exact` | NFC substring |
| `case_insensitive` | NFC, then Unicode default case folding |
| `word_boundary_ci` | NFC, case-insensitive, anchored at Unicode word boundaries |
| `normalized_whitespace` | NFC, then whitespace collapsed to a single space |
| `normalized_whitespace_ci` | NFC, then the pinned invisible code points removed, then whitespace collapsed, then case folded |

`word_boundary_ci` and `normalized_whitespace_ci` are distinct modes and neither
is a relaxation of the other. `word_boundary_ci` answers "does this term occur as
a word"; it does not see a term whose separator was widened. `normalized_whitespace_ci`
answers "does this term occur once separators and invisible characters are
disregarded"; it has no word boundary. An author picks the one that matches the
obligation.

**Pinned word segmentation.** `word_boundary_ci` is the one mode whose meaning is
delegated to a segmentation implementation, so the contract is *one declared
Unicode version plus normative fixtures*, not the name of an algorithm. An
implementation MUST declare the Unicode version its segmentation implements. That
is the version the *engine* implements, which is a different question from the
canonicalisation version section 14.3c pins and may have a different answer. It
MUST reproduce the normative fixtures published with the release. A dependency
that supplies the segmentation tables MUST be pinned exactly; an unbounded
dependency is an unpinned normative contract, because two conforming installs
could then disagree about what the mode means.

A term whose first or last character is not a word character makes the
corresponding boundary anchor vacuous, so such a term MUST be refused where it is
written rather than compiled into a check that behaves unpredictably. The
forbidden edge set is a closed set of code points, published in the RULE value
contract and enforced by the compiler from the same definition. `_` LOW LINE is a
word character under every reading and is deliberately admissible.

**Pinned invisible code points.** `normalized_whitespace_ci` removes exactly this
closed set before comparing:

```text
U+00AD SOFT HYPHEN            U+200E LEFT-TO-RIGHT MARK
U+200B ZERO WIDTH SPACE       U+200F RIGHT-TO-LEFT MARK
U+200C ZERO WIDTH NON-JOINER  U+2060 WORD JOINER
U+200D ZERO WIDTH JOINER      U+FEFF ZERO WIDTH NO-BREAK SPACE
```

The set is written down rather than expressed as the Unicode
`Default_Ignorable_Code_Point` property, which moves between Unicode versions and
would make the mode's meaning depend on the host database again. **The stripping
applies to this mode and to no other.** Extending it to `exact`,
`case_insensitive`, `word_boundary_ci` or `normalized_whitespace` would
reinterpret checks authors have already written.

Rules:

- `elementValueRef` is resolved during the build against the governed selection for this target and this `asOf`, not against the raw approved manifest snapshot. A check binds truth that this execution is entitled to use, so the referenced element MUST resolve to the one applicable `defined` element of its subject, under the same resolution as `requiresDefinedRefs`: it MUST exist, match the target scope, be valid at the Build Plan `asOf`, win its semantic subject, be free of an unresolved subject conflict, and be `defined`. If it does not, the target fails with the section 13.1a cause that applies and no production artefact is written. The check is never silently omitted, and a value that has expired, does not apply to this target, or lost its subject is never compiled into an active check.
- **A check is validated at two stages, under one contract.** The *authored*
  stage is the Brand Manifest. There, a `literal_required` check MAY carry
  `elementValueRef` instead of `literal`, because the build is what resolves it,
  and the reference's own shape, `elementId` and `path` both present and
  non-empty, MUST be validated where it is written rather than surfacing first
  as a build failure. The *compiled* stage is the Compiled Brand Context. There,
  the resolved value MUST be present, because nothing downstream will resolve it.
  Running the compiled-stage rule over the authored form demands a literal the
  author deliberately deferred, which made a branch the published RULE contract
  admits unusable through the governed build path while a direct compiler call
  materialised it: one contract, two answers.
- Unsupported primitives, invalid parameters or unsupported registry versions fail the target build, and are refused at the authored stage as well.
- Runtime MUST execute every compiled Foundation check natively or reject the artefact.
- Foundation Check Registry v1 excludes regex, general expression languages and token-length checks.
- More complex deterministic logic uses `validatorRef` or an optional namespaced profile.
- `appliesTo: task_input` requires `phase: preflight`; `appliesTo: output` requires `phase: postflight`. A mismatched pair is invalid and MUST fail validation.
- Every defined element in the RULES family MUST validate against a rule value contract regardless of its `nature`.
Canonical Rule values retain explicit empty structural fields such as `checks`, `condition`, `requirement` and `references` in 1.0 so one rule contract has a stable machine shape. Runtime model projections MAY omit empty validator plumbing.

### 11.5a Foundation Validator Registry v1

`validatorRef` names a deterministic invariant that JSON Schema alone cannot
prove. It is a **value contract** property. It is not a RULE value property, and
since 3.0 a RULE value that carries one is rejected (section 11.4).

The registry is closed, like the Foundation Check Registry, and contains one
entry.

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
schemaVersion: 3.0.0
asOf: '2026-08-27T00:00:00Z'
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

### 13.0a The 3.0 Build Plan contract

A 3.0 Build Plan declares `schemaVersion: 3.0.0` and is validated against
`schemas/3.0.0/build-plan.schema.json`. It MUST NOT be validated against a
frozen historical contract: the 1.0.0 contract is published, immutable and
describes a different document.

Every target MUST declare `stateMap` and `styleTexture`. Both decide what reaches
the compiled context, so an absent one is a governed decision made by whichever
implementation supplied the default. Stating them is one line per target and
removes the question.

```yaml
stateMap:
  mode: all_applicable   # none | kinds | all_applicable
  kinds: []              # required only when mode = kinds

styleTexture:
  mode: all              # all | selected | none
  elementIds: []         # required only when mode = selected
```

`requiresDefined`, `contextAssembly` and `releasePolicy` remain optional: an
absent one denies rather than grants, so it carries no hidden decision.

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

### 13.5a Decision-bearing parameters are materialised

A compiled check MUST carry every parameter that changes its outcome, with the
value this build decided. Where the Foundation Check Registry names a default for
`match`, `mode`, `appliesTo` or `unit`, the compiler MUST write the effective
value into `compiledChecks[].params` rather than leave the field absent.

**The runtime MUST NOT supply a missing parameter.** A runtime that fills an
absent `match` with `case_insensitive` is not applying a default, it is making a
governed decision the artefact never stated, and two runtimes filling it
differently reach two governed answers from one artefact. A compiled check whose
outcome depends on a parameter that is not present in the artefact MUST be
refused, and the runtime MUST fail closed as section 15.11 requires.

This is one sentence in two halves and neither half is worth anything alone:
the compiler materialises, and the runtime refuses to invent. Materialisation
happens after the selection of section 10 and after the relevance decision of
section 10.2a, and changes neither.

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
  "schemaVersion": "3.0.0",
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

**The 3.0 contract.** A 3.0 Compiled Brand Context declares
`schemaVersion: 3.0.0` and is validated against
`schemas/3.0.0/compiled-context.schema.json`. Frozen historical contracts remain
published and immutable and MUST NOT be used to validate a 3.0 artefact.

The 3.0 contract constrains the fields consumers actually read, because a
contract that stops where the code starts is a contract that proves nothing about
the document a consumer is about to execute. Two schema-valid artefacts crashed a
consumer under the 1.1 contract: `elementRecords[0]` with no `id`, and a validity
timestamp that was not a timestamp.

- `elementRecords[]` items MUST carry `id`, `family`, `kind`, `nature`, `state`,
  `scope`, `validity`, `sourceRefs` and `annotations`. These are the nine fields
  governed consumers read. Further properties are permitted, because an element
  record carries its `value` and its `valueContractRef` beside them.
- `validFrom` and `validTo` are `null` or an RFC 3339 date-time, constrained by a
  pattern in the contract itself rather than by a `format` annotation, which no
  validator is obliged to enforce. A self-carrying pattern needs no optional
  format checker and no additional dependency.
- A pattern constrains shape, not the calendar. `2026-13-45T99:99:99Z` satisfies
  it and is still not a time, so section 15.11 requires the runtime to treat a
  validity window it cannot read as a window that has not opened.

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

Every parameter that changes the outcome is present, with the value this build
decided (section 13.5a). `match` and `appliesTo` above are written out even
though the registry names a default for both, because the artefact, not the
runtime that reads it, is where a governed decision is recorded.

### 14.3 Canonical hash

`artifactHash` is SHA-256 over a canonical JSON payload.

The payload is the complete Compiled Brand Context except `artifactHash`.

Canonicalisation is:

0. reject the payload if any string or object key contains a code point outside the pinned Unicode version, as section 14.3c specifies;
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

### 14.3c Pinned Unicode version

Step 1 of section 14.3 normalises to NFC. NFC is only deterministic once the
Unicode version performing it is fixed. A code point that is unassigned in one
version and is given a non-zero canonical combining class in a later one
reorders against its neighbours, so two implementations running byte-identical
code on runtimes with different Unicode databases produce different canonical
bytes, and therefore different `manifestContentHash`, `governedResultHash` and
`artifactHash` values, for the same document. They may also disagree on whether
a document is valid at all, because two object keys can become equal only in the
later version.

OBDS therefore pins the version:

```text
Unicode 15.1.0
```

Rules:

- an implementation MUST use a Unicode database of version 15.1.0 or later to perform the normalisation in section 14.3 step 1;
- a governed string or object key MUST consist only of code points that are assigned in Unicode 15.1.0, or that are Unicode noncharacters, and MUST NOT contain a surrogate code point; and
- an implementation MUST reject a document containing any other code point, before normalising it.

Noncharacters are admitted because the Unicode Character Encoding Stability
Policy guarantees that they are never assigned, so their combining class and
decomposition can never change and they are normalisation-stable in every
version. Surrogates are excluded because they are not characters: they cannot be
encoded as UTF-8, which step 5 requires, and an implementation that emitted them
as an escape instead would produce different bytes for the same document.

Within the admitted set the Unicode Normalization Stability Policy guarantees
that NFC is identical on every database at or after the pinned version. That is
what makes the canonical bytes, and every hash derived from them, reproducible
across implementations and across time.

The release ships the pinned assignment set as machine-readable data so that an
implementation on a newer Unicode database can apply the rule without carrying
its own copy of Unicode 15.1.0:

```text
reference/foundation/src/obds_ref/unicode-pin-15.1.0.json
```

Raising the pinned version is a normative change and MUST NOT happen in a PATCH
release, because it widens the set of admissible documents.

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

A subject in hard conflict contributes no `selection` entry, because no element
won it. What that means for the build depends on section 10.2a:

- a **decision-relevant** conflict fails the target. Section 13.5 produces no
  artefact for a failed target, so no `governedResultHash` exists for that build
  at all.
- a conflict that is **not decision-relevant** for this target does not fail it.
  The build proceeds, the conflicted subject contributes nothing to the governed
  selection, and a `governedResultHash` exists.

In the second case that hash is deliberately the same as it would be for a
manifest in which the subject has no applicable element, because in both cases
the target's governed result is the same: nothing from that subject applies.
**`governedResultHash` identifies the governed result, not the diagnostic
history that produced it.** Two builds that agree on every applied truth agree
on the hash, whatever else the manifest contains.

That is a statement about the hash, not permission to lose the distinction.
Section 13.7 requires the Build Report to carry the conflict in `conflicts[]`,
marked as not decision-relevant, so an operator sees a manifest defect that this
target happened not to read. An audit reads the Build Report; the hash answers a
narrower question.

The exclusions are the contract. A section 27.2 governance-neutral PATCH, which
rotates source references or corrects annotations without changing Brand Truth,
MUST NOT move `governedResultHash`. A change to any selected element value MUST
move it.

`governedResultHash` is present in the Compiled Brand Context and is inside the
`artifactHash` payload, like every other artefact field. It does not replace
`artifactHash` and does not change its meaning.

### 14.3d A declared hash is not verified integrity

Every hash in OBDS is written into a document by whoever produced that document.
Reading it back proves nothing at all: a caller who can edit a payload can also
edit the hash printed beside it. Two documents each declaring the same value, and
neither of them checked, is not verification either. It is agreement between two
claims.

Where this specification requires a hash to be **verified**, the sequence is:

```text
canonical governed payload
→ recompute the hash from that payload
→ compare with the supplied hash
→ only then trust the binding
```

An implementation MUST NOT describe a comparison between two supplied values as
verification. Where a document merely repeats a value some other boundary has
already reproduced from its payload, that is a **comparison**, and the boundary
that did reproduce it MUST be identifiable; where nothing reproduced it, the
value is a **declaration** and carries no integrity claim.

Reproduction proves the payload is intact. It does not prove the payload is the
one this decision is about. That is what section 8.0b binds. A governed decision
needs both, and they are two questions:

| Question | Answered by |
|---|---|
| Is this document intact? | recomputing its hash from its own payload |
| Is it the document this decision is about? | binding its identity to the artefact upstream |

Section 15.11 lists where each is required.

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
assembledAt: '2026-07-31T09:00:00Z'
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

**The rendering is derived, not asserted.** The five slots render in the fixed
order above, by one deterministic renderer, and the renderer is total: a missing
slot is refused, not rendered as an empty string. A slot that renders as empty
because nobody supplied it is a governed decision made by whichever
implementation happened to render it.

**Exact task-input binding.** These four are one value, not two pairs:

```text
checked task input
=
package.slots.taskInput
=
deterministically rendered TASK_INPUT
=
bytes covered by modelInputHash
```

A runtime MUST derive the model input from the slots it has verified and compare
it byte for byte against the text it is about to send. It MUST NOT accept the
rendered text as a parameter it merely hashes.

Verifying `modelInputHash` against the text the caller supplied, and
`slots.taskInput` against the preflight argument, is two independent pairs and
leaves the middle open: edit the `[TASK_INPUT]` block inside the rendered text,
recompute `modelInputHash` and `assemblyHash`, leave the slot and the preflight
argument benign, and every check passes while the model receives text that was
never checked. The chain closes only when one renderer produces the bytes both
ends agree on.

The Model Input Package is validated against its published contract,
`schemas/1.0.0/model-input-package.schema.json`, before any of its fields is
read (section 15.11).

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

### 15.11 Governed runtime documents are contract-validated before use

A governed runtime document is any document a consumer derives a governed
decision from:

```text
Compiled Brand Context
Model Input Package
Review Result
```

**Every consumer that derives a governed decision from one of these MUST run the
full sequence, in this order, before it reads any field of it:**

```text
governed parse                    (section 28.1)
→ the published contract for that document
→ every required hash reproduced   (section 14.3d)
→ every required identity bound    (section 8.0b)
→ governed field access / decision
```

"Every consumer" is the whole surface, not the entry point an implementation
thinks of first. A runtime that validated the published contract while the
command-line validator beside it did not reported the same re-sealed
schema-invalid artefact as valid from one path and refused it from the other.

The contracts are:

| Document | Contract |
|---|---|
| Compiled Brand Context | `schemas/3.0.0/compiled-context.schema.json` |
| Model Input Package | `schemas/1.0.0/model-input-package.schema.json` |
| Review Result | `schemas/1.0.0/review-result.schema.json` |

**Order matters.** The contract decides whether the document is that kind of
document at all, so it runs before the first field read, including the fields a
Runtime Decision Record copies as evidence. Asked afterwards, a non-object
artefact raises out of the runtime and the record section 15.9 requires for that
attempt is never written.

**Fail closed, with a record.** An invalid governed document produces a governed
rejection, never an uncontrolled exception, and never a model call:

```text
invalid governed document
→ governed rejection
→ no uncontrolled exception
→ no model call
```

A validity window the runtime cannot read is not a window it may ignore. An
unparseable `validFrom` or `validTo` means the artefact is not valid, whatever
the contract's pattern permitted.

**Where identity is bound.** A Review Result validator reproduces
`artifactHash`, `compiledContextHash`, `assemblyHash`, `modelInputHash` and
`reviewHash` from their own payloads, and binds the manifest triple of section
8.0b and `targetId` between the package, the review and the compiled context it
claims to be about. Reproducing five hashes without binding those identities
accepts a package naming another brand, another approved version or another
target, correctly re-sealed throughout.

The runtime additionally binds what the package declares about the build it came
from: `sources.compiledContextHash` against the loaded artefact, and `targetId`,
`deliveryMode` and `applicationMode` against the artefact's own
`contextAssembly` policy. Verifying only hashes leaves those declarations
unchecked, so a re-sealed package could claim a mode the artefact does not permit
and the Runtime Decision Record would carry the claim as governed evidence.

**What this does not claim.** OBDS defines no signature. A caller holding every
document of a decision can produce a mutually consistent set of them, and no
boundary inside that set can tell. What section 15.11 guarantees is that a
document is intact, is the kind it says it is, and is about the artefact it says
it is about. Provenance beyond that is an operational control, not an OBDS one.

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

From 3.0 it also requires the governed input contract of section 28.1 at every
governed reader and every entry point of each, the identity rules of section
8.0b, and a RULE value contract that refuses `validatorRef` and refuses
`validationMode: deterministic` with no registered check.

### 26.2 OBDS Compiled Runtime

Additionally requires exact Build Plans, `requiresDefined`, every required element present in the produced context, explicit context selection, no artefact for a failed target, canonical JSON artefacts, reproducible hashes, a `governedResultHash` that matches section 14.3a for the same manifest and Build Plan, Foundation Check Registry v1, exact target loading, Runtime Decision Records, zero instrumented model calls after failed build or blocking preflight, withheld output after blocking postflight, per-slot token reporting, the governed input contract at every governed reader, identity binding of the manifest triple wherever an artefact names a manifest, two-stage validation of Foundation RULE checks, exact task-input binding, contract validation of every governed runtime document before governed field use and governed hashes reproduced rather than declared.

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

OBDS 2.0 was that release, and it was deliberately narrow. It corrected one interchange defect, stated in section 28.1: governed YAML had no pinned reading, so the same bytes could produce two different governed values and two different canonical hashes depending on which YAML version the reader carried. Closing that rejects documents 1.x accepted and changes how one form resolves, which is a breaking change to an existing normative contract and therefore MAJOR by the rule above.

OBDS 3.0 is the Semantic Closure release and is MAJOR for the same reason,
five times over. Each of the five closures listed in section 1 rejects a document
or an execution path an earlier release accepted:

| Closure | What 3.0 now rejects |
|---|---|
| A, section 28.1 | a governed document with a non-object root, at every reader rather than one |
| B, section 8.0b | CR or LF at an identity position; an artefact that names a manifest without binding all three of `id`, `version` and `contentHash` |
| C, sections 11.4 and 11.5 | a RULE value carrying `validatorRef`; `validationMode: deterministic` with no registered check; an unregistered check primitive or parameter at the authored stage |
| D, sections 13.0a, 13.5a, 15.11 | a 3.0 Build Plan target without `stateMap` or `styleTexture`; a compiled check missing a decision-bearing parameter; a governed runtime document used before its contract is validated |
| E, section 10.2a | a consumer that re-derives conflict relevance after the compiler decided it |

Nothing else in 3.0 is new: no Brand State, no profile, no capability, no
architecture. The migration notes list what a 2.x manifest and Build Plan have to
change, which for most manifests is the Build Plan and nothing else.

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

### 28.1 Governed input contract

Section 28 makes JSON the canonical interchange format and allows YAML where it
produces an equivalent JSON document. Which JSON document a YAML file produces
depends on how it is read, and that was left to the implementation. It is pinned
here, because a governed document whose meaning depends on the reader has no
canonical hash.

**One contract, every reader.** This section is the whole governed input
contract. It applies to every governed reader in an implementation, and to every
entry point of every one of them:

```text
same governed bytes
→ same governed interpretation
independent of entry point
```

A reader that takes a file path and a reader that takes bytes already in hand are
one contract with two doors, not two contracts. A release gate that scrapes
governed YAML out of published HTML, a conformance runner that reads a fixture, a
packaging tool that reads its own metadata and the compiler itself all read under
this section. So does a test that produces or blesses published evidence: a suite
that reads the corpus with a different reader can bless a document the compiler
refuses and refuse one it accepts.

Each rule below is stated once, where every entry point reaches it. A rule
enforced in one entry point and not in another is the defect this section exists
to close. The root rule in the paragraph that follows was stated in one of five
readers, and the other four returned a document the first one refuses.

**A governed document has an object root.** A JSON or YAML document whose root is
an array, a scalar or null is not a governed document and MUST be rejected. An
empty document has no object root and is rejected for the same reason.

**The bounds are the contract's, not the format's.** The nesting bound and the
duplicate-key rule below apply to the data model, so they apply identically to a
document that arrived as JSON and to one that arrived as YAML. Stated in the YAML
path alone, the same data model had two answers depending on which format carried
it.

**Governed YAML is a subset of YAML 1.2, defined by this section.** Where YAML
1.1 and YAML 1.2 disagree, YAML 1.2 governs; where this section restricts YAML
1.2 further, this section governs. The restrictions are listed here in full so
that "the subset" is a closed statement and not an invitation to guess:

- U+0085, U+2028 and U+2029 are line breaks in YAML 1.1 and ordinary characters
  in YAML 1.2, so a governed YAML document MUST NOT contain one of them raw.
  They remain valid governed content and section 14.3b escapes two of them;
  write them as an escape in a double-quoted scalar, where every YAML version
  agrees what they are.
- A tab MUST NOT be used as separation between a key and its value. YAML 1.2
  permits it and YAML 1.1 does not, and a governed document gains nothing from
  the difference. Use a space.
- An explicit tag MUST be rejected, including the non-specific `!`. A tag
  suppresses or overrides resolution, which is another way to reach a value the
  rules below would not produce.
- The merge key `<<` written as a plain scalar MUST be rejected. It is a YAML
  1.1 construct that other readers expand and this one would not, so one
  document would carry two data models. A quoted `"<<"` is an ordinary string
  key and is accepted.
- Anchors and aliases are permitted. An alias expands to the same node in every
  YAML version, so it produces one data model, and the duplicate-key rules below
  apply to the expansion exactly as they apply to anything else. A recursive
  alias MUST be rejected. An implementation MUST also bound how large an alias
  expansion may be and MUST reject a document that exceeds its bound, because
  nested aliases expand multiplicatively: eight aliases per level, nine levels
  deep, is 425 bytes of governed YAML and 175,304,795 nodes once expanded. The
  bound MUST be documented. The reference implementation rejects above one
  million expanded nodes.
- An implementation MUST bound how deeply a governed document nests and MUST
  reject a document that exceeds its bound, and the bound MUST be documented.
  Left unstated it is whatever the reader's call stack allows, which differs
  between runtimes and between versions of the same runtime, so two conforming
  implementations would disagree about which documents are governable. The bound
  applies to the data model and therefore to JSON and YAML alike. A level is one
  nested collection, counting the outermost: `{"a": [1]}` is two. The reference
  implementation accepts one hundred levels and rejects the hundred and first.

**Resolution.** A plain scalar resolves to the first of these that matches, and
the rules are exhaustive:

| Plain scalar | Resolves to |
|---|---|
| `null`, `Null`, `NULL` | null |
| `true`, `True`, `TRUE`, `false`, `False`, `FALSE` | boolean |
| a JSON number literal, `-?(0\|[1-9][0-9]*)(\.[0-9]+)?([eE][-+]?[0-9]+)?` | that number |
| a form in the rejection table below | nothing: the document is rejected |
| anything else | string |

The number row is the JSON grammar, not a YAML one. A plain scalar that resolves
to null, a boolean or a number therefore denotes exactly what the same
characters denote read as a JSON literal, which is what makes the same bytes
mean the same thing in both formats. `1e3` is the number 1000.

`yes`, `no`, `on`, `off`, `y` and `n` are strings, as OBDS 1.0 already required.

**Rejection.** A plain scalar in any of these forms MUST be rejected rather than
resolved. Each is a form that some YAML version reads as a value the JSON
grammar above does not produce, so accepting it under either reading would make
a governed document's meaning depend on which YAML version an implementation
carries. The table is closed: a form not listed and not matching the resolution
table is a string.

| Rejected form | Because |
|---|---|
| `017`, `-017`, `017.5`, `017e3` | octal in YAML 1.1, decimal in YAML 1.2, not a JSON number |
| `+42`, `+1.5`, `+0` | an integer in YAML 1.2, not a JSON number |
| `1.`, `1.e3`, `.5`, `.5e3`, `-.5` | a float in YAML 1.2, not a JSON number |
| `1_000` | a number in YAML 1.1, a string in YAML 1.2 |
| `12:30`, `1:2:3` | sexagesimal in YAML 1.1, a string in YAML 1.2 |
| `2026-09-01`, `2026-09-01T00:00:00Z` | a timestamp in YAML 1.1, a string in YAML 1.2 |
| `0x1f`, `0o17`, `0b1010` | alternative number bases, which JSON does not have |
| `~` | the YAML 1.1 null shorthand; write `null` |
| `.inf`, `.nan`, `-.inf` | outside the OBDS numeric domain of section 14.3 |
| the empty plain scalar | null in YAML, absent in JSON; write `null` |

Quoting always resolves a rejection, because a quoted scalar is a string in
every YAML version. A governed timestamp is therefore written quoted, and every
example in this specification writes it that way.

**Notation.** Many YAML blocks in this specification show the shape of a record
rather than a document: a key with no value names a field and leaves the value
to the author, in the same way that `status: ready | failed` on the next line
names a choice rather than carries one. Those blocks are field-shape sketches
and are not governed documents. A governed document has no empty plain scalar;
a field that is present and has no value is written `null`.

**Nodes that are not plain scalars.** A quoted scalar, single or double, is a
string. A block scalar is a string. A mapping key resolves under the same rules
and must be a string, so `1: x` is rejected as a non-string key. What is refused
among non-plain constructs is listed above and nowhere else.

**Everything else is unchanged.** Duplicate mapping keys are rejected, including
keys equal after the section 14.3 normalisation. Numbers are finite IEEE-754
binary64 values as section 14.3 defines, so a value outside that domain is
rejected wherever it is written. Scope values are strings. Section 14.3c pins
the Unicode version.

A conforming implementation MUST reach the same JSON data model, and therefore
the same canonical bytes and the same hashes, for a governed document whether it
reads it as JSON or as YAML, and whether it reads it from a file or from bytes it
already holds.

**Writing.** The rules above apply to what an implementation writes as well as to
what it reads. An emitter that decides quoting with YAML 1.1 resolvers writes the
string `1e3` as a plain `1e3`, which this reader reads back as the number 1000. A
writer and a reader that disagree are the same defect in the other direction, so
a conforming implementation MUST NOT emit a governed document its own reader
would refuse or reinterpret.

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

## 33. Release files

A credible OBDS release includes:

1. one normative specification: `OBDS-3.0.3.md`;
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
