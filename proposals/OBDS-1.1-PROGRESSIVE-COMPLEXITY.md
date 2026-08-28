# OBDS 1.1 proposal: progressive complexity as a first-class usability principle

    Status:      PROPOSAL / UNRATIFIED
    Target:      OBDS 1.1 (not scheduled, not committed)
    Applies to:  documentation, registry and tooling surface only
    Normative:   no
    Author:      Kill The Dragon GmbH
    Date:        2026-08-28

This note is not part of OBDS 1.0.1 and changes nothing in it. It records a
usability learning and explores one possible response. Nothing here is accepted
1.1 functionality.

---

## 1. What problem does this solve?

OBDS 1.0.1 is technically complete and, read cold, reads heavier than it is.

An unfamiliar reader or an unfamiliar language model opens the release package,
counts 27 schemas, nine Runtime Capabilities and eight optional Brand Profiles,
and concludes that an OBDS implementation means implementing all of it. Two
misreadings follow:

1. **"OBDS is a very elaborate machine-readable brandbook."**
   The governance model, which is the actual contribution, is read as metadata
   decoration on a brand asset store.

2. **"Every brand has to implement the whole stack."**
   Small and mid-sized implementations self-select out, and large ones plan a
   project an order of magnitude bigger than the one they need.

The specification already says the opposite. Section 4.1 states one Foundation
with optional layers. Section 4.2 gives a minimal implementation path and ends
with the sentence: *the number of schemas in the release package is not the
number of concepts a basic implementation must implement.*

The problem is therefore not the architecture. The problem is that the
architecture's progressiveness is discoverable only by reading two specific
subsections of a long normative document. Nothing in the artefact surface, the
registry or the tooling makes the sequence obvious.

**The learning:** progressive complexity should be a first-class usability
principle of OBDS, expressed in the artefacts a reader encounters first, not
only in prose that a reader encounters on page forty.

## 2. Why is this not a new architecture?

Because it introduces nothing that does not already exist.

The proposal is that three **convenience bundles** be given names, and that a
bundle be defined as an alias for a set of already-registered capability
identifiers.

    OBDS Foundation
      = obds-foundation
        (the required base, unchanged)

    OBDS Governed Context
      = OBDS Foundation
      + compiled-runtime
      + context-delivery
      + context-assembly

    OBDS Automated Production
      = OBDS Governed Context
      + composition
      + visual-operations

A bundle is a label for a set. It is explicitly **not**:

- a new Brand Profile;
- a new Runtime Capability;
- a new Brand State;
- a new Family;
- a new conformance level, tier or class;
- a new manifest kind;
- a second source of Brand Truth;
- a simplified or competing specification;
- an "OBDS Lite".

There is no bundle semantics. Resolving a bundle yields capability identifiers,
and those identifiers carry every rule they already carry in 1.0. A bundle can
be deleted from the specification without changing a single conformance
outcome. That property is the design constraint, not a side effect.

The three names are working names. **Foundation** is already the specification's
own term and must stay bound to `obds-foundation`. **Governed Context** and
**Automated Production** are new labels for existing sets and can be renamed
without consequence.

## 3. How could tools declare bundle support?

Three options, in ascending order of intrusiveness.

### Option A: no declaration at all (documentation only)

Bundles exist in prose, on the website and in the quickstart. Tools continue to
declare capability identifiers exactly as in 1.0. A tool "supports Governed
Context" as an English sentence in its README, never as a field.

- Cost: zero. Risk: zero. No specification change of any kind.
- Weakness: no machine-checkable shorthand, so registries and comparison tables
  keep listing raw identifiers.

### Option B: registry aliases, resolved before use (preferred)

The capability registry gains a non-normative `bundles` block:

```json
"bundles": [
  {
    "id": "obds-bundle-foundation",
    "normative": false,
    "expandsTo": ["obds-foundation"]
  },
  {
    "id": "obds-bundle-governed-context",
    "normative": false,
    "expandsTo": [
      "obds-foundation",
      "compiled-runtime",
      "context-delivery",
      "context-assembly"
    ]
  },
  {
    "id": "obds-bundle-automated-production",
    "normative": false,
    "expandsTo": [
      "obds-foundation",
      "compiled-runtime",
      "context-delivery",
      "context-assembly",
      "composition",
      "visual-operations"
    ]
  }
]
```

Rules that would keep this safe:

- A bundle identifier MUST NOT appear in a Brand Manifest `profiles[]` array.
- A bundle identifier MUST NOT appear in a conformance claim.
- A bundle identifier MUST be expanded to its member capability identifiers
  before any validation, conformance or runtime decision.
- An implementation that does not understand bundles MUST behave identically,
  because it never encounters one in governed data.
- `expandsTo` MUST list capability identifiers already registered in the same
  release. A bundle MUST NOT introduce an identifier of its own.

This keeps bundles entirely outside the data plane. They are a lookup table for
humans, tooling output and marketing surfaces.

### Option C: a declarable field in conformance claims

Rejected. A declarable bundle field would immediately become a second way to
express a conformance claim, two encodings of the same fact would drift, and
implementers would ask which one wins. That is exactly the parallel semantics
this proposal exists to avoid.

## 4. How should bundle membership map to existing capability IDs?

Directly and only to identifiers already registered in
`OBDS-1.0.2-CAPABILITY-REGISTRY.json`.

| Bundle | Member Runtime Capabilities | Related optional Brand Profiles |
|---|---|---|
| OBDS Foundation | none | none (`obds-foundation` is the required base) |
| OBDS Governed Context | `compiled-runtime`, `context-delivery`, `context-assembly` | none required |
| OBDS Automated Production | the above plus `composition`, `visual-operations` | `obds-composition`, `obds-visual-operations` where the manifest carries that data |

Three constraints on membership:

1. **Bundles are cumulative.** Governed Context contains Foundation.
   Automated Production contains Governed Context. A reader should never have to
   compute a set difference.

2. **Bundles are a subset, never a partition.** `text`, `claims`,
   `localisation` and `operations` deliberately belong to no bundle. They are
   orthogonal to the three-step scaling story and are added on their own merits.
   A bundle system that tried to place every capability would force arbitrary
   groupings and would become an architecture rather than a shorthand.

3. **Brand Profiles are not bundle members.** A profile describes brand data in
   a manifest; a capability describes engine behaviour. Mixing them into one
   bundle list would blur the distinction section 4.1 draws deliberately. The
   table above lists related profiles as guidance, not as membership.

## 5. What happens when capabilities evolve?

The rule that keeps bundles harmless: **capability identifiers are authoritative,
bundle membership is derived.**

- A new Runtime Capability in a future MINOR release joins no bundle by default.
  Adding it to a bundle is a separate, explicit, documented decision.
- Changing a bundle's membership is a documentation change, not a semantic one.
  It cannot break a manifest, because no manifest references a bundle.
- It can, however, change what a sentence like "we support Governed Context"
  means over time. Mitigation: bundle membership is versioned with the
  release that publishes it, and any human-readable bundle claim is expected
  to name the release, for example "OBDS 1.1 Governed Context".
- If a capability is ever deprecated, it is removed from any bundle in the same
  release that deprecates it. A bundle must never keep a dead identifier alive.
- If bundle membership and capability identifiers ever disagree, the identifiers
  win. This should be stated in the same sentence that introduces bundles.

## 6. Could bundles be purely documentation or registry aliases?

Yes, and that is the recommendation.

The honest summary of this proposal is that the strongest version of it is also
the smallest: Option A for the specification text, Option B for the registry so
that tooling and websites have one machine-readable source instead of each
inventing its own grouping.

Anything beyond that buys very little and costs the property that makes the idea
safe. The moment a bundle can be declared in governed data, it stops being an
alias and starts being a contract.

A useful test of whether the proposal has stayed honest: delete the `bundles`
block from the registry and re-run the full conformance suite. If a single
result changes, the proposal has failed.

## 7. What is the migration impact?

None, by design.

- No manifest changes. No manifest ever references a bundle.
- No schema changes. `brand-manifest.schema.json` is untouched, and `profiles[]`
  keeps accepting exactly the profile identifiers it accepts in 1.0.
- No conformance changes. The suite tests capabilities, not bundles.
- No hash changes to any published 1.0.x artefact. Bundles would appear only in
  a future registry, never retroactively.
- An implementation written against 1.0.1 remains fully conforming with no work.
- An implementation that has never heard of bundles is not disadvantaged,
  because bundles do not appear in data it reads.

If a proposed change to bundles would require any implementer to do anything,
the proposal is wrong and should be rejected on that basis alone.

## 8. What tests would prove they remain aliases?

The bundle idea is only acceptable if its harmlessness is mechanically checked.
Proposed additions to the conformance suite, all of which test the registry and
the tooling rather than brand data:

1. **Expansion is complete.** Every identifier in every `expandsTo` array
   resolves to a Runtime Capability or Brand Profile registered in the same
   release. Unknown identifier fails.

2. **Bundles introduce no identifiers.** The set union of all `expandsTo`
   arrays is a subset of the registered identifier set. A bundle identifier
   appearing inside another bundle's `expandsTo` fails.

3. **Bundles are rejected in governed data.** A Brand Manifest declaring
   `obds-bundle-governed-context` in `profiles[]` MUST fail validation with an
   unknown-profile error, exactly as any other unregistered identifier would.

4. **Bundles are rejected in conformance claims.** A conformance claim naming a
   bundle instead of capabilities MUST be rejected.

5. **Cumulative containment.** Foundation's expansion is a subset of Governed
   Context's expansion, which is a subset of Automated Production's expansion.
   A regression that breaks nesting fails.

6. **Deletion equivalence (the decisive test).** Run the complete conformance
   suite twice, once with the `bundles` block present and once with it removed.
   Every result, every hash and every decision record MUST be byte-identical.
   Any difference proves that bundle semantics have leaked into the data plane,
   and the feature must be reverted rather than patched.

7. **No parallel documentation truth.** A generated check that every bundle
   member listed in prose, on the website and in the registry agrees. Three
   places describing the same set is already two places too many; the test
   makes the drift visible instead of letting it accumulate.

8. **Registry round-trip.** The registry with the `bundles` block canonicalises
   and hashes deterministically, and the block's presence does not alter the
   schema surface fingerprint of the capability set itself.

Test 6 is the one that matters. If it ever fails, this proposal was a mistake.

---

## Explicitly out of scope

This note does not propose, and should not be read as proposing:

- new Brand States, Families, Profiles or Runtime Capabilities;
- new schema semantics or new schemas;
- changes to precedence, scope resolution, conflict handling or `asOf`;
- changes to the assembled model input slots;
- a certification or badging scheme built on bundles;
- any change to OBDS 1.0.0 or 1.0.1, both of which stay published as released.

## Open questions

1. Are three bundles the right number, or do Foundation and everything-else
   carry the message with less machinery?
2. Do the names "Governed Context" and "Automated Production" survive contact
   with implementers who have not read the specification?
3. Should `text` join Governed Context, given that most non-visual automation
   reaches for it immediately? The argument against is that it would make the
   bundle prescriptive about output type.
4. Is a registry block worth the drift risk at all, or is prose plus a website
   diagram sufficient?

These are open. The proposal is unratified and is recorded here so that the
learning is not lost, not because a decision has been made.
