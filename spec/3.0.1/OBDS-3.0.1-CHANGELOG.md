# OBDS Changelog

## Release

**Version:** OBDS 3.0.1  
**Status:** Stable  
**Date:** 2026-09-03

## 3.0.1

**Packaging correction. PATCH.**

OBDS 3.0.1 is a packaging and distribution correction. No normative OBDS
contract changed. The release ZIP now includes the tooling required to reproduce
the documented standalone conformance and release-gate checks.

### What was wrong

The 3.0.0 archive omitted `tools/`. The Semantic Closure surface registries name
`tools/build-release.py` and `tools/docs-smoke-test.py`, which in the repository
is correct: the packager computes governed hashes and resolves contract paths, so
it belongs to the surface mechanism 2 and mechanism 5 enumerate. In an unpacked
archive those files were absent, eight enumeration guards refused a release the
repository had passed, and the two commands `README.md` and the test requirements
document for the archive layout did not run.

Nothing caught it before publication. The release gate and the suite both run in
the repository, where the files exist. Only the post-deployment docs smoke test
unpacks the archive, and it runs after the deployment.

### What changed

- `tools/` is part of the release package. The directory list has one definition,
  in `reference/release-gate.py`; the packager imports it instead of keeping a
  second copy, for the same reason it already imports `contract_directories()`.
- One new packaging test asserts the invariant directly: every path a surface
  registry names is a path the packager ships. It fails when `tools/` is removed
  from the package, which is the state 3.0.0 shipped in.
- The two smoke-test docstrings that described `tools/` as outside the package
  are corrected, and one description in `tools/deploy-smoke-test.py` was reworded
  because the gate refuses pre-release wording anywhere in the package.

### What did not change

No Brand State, no profile, no capability, no architecture, and no normative
contract. Governed-input semantics, identity semantics, RULE enforcement, Unicode
behaviour, Build Plan semantics, runtime contract enforcement, conflict relevance,
Context Assembly semantics and hash verification semantics are byte-identical to
3.0.0. The public schemas, the value schemas and the versioned 3.0.0 contracts are
byte-identical. The specification text differs from 3.0.0 in two mechanical lines:
its own version stamp and the release-file name in section 33.

`spec/3.0.0/` is untouched.

**Conformance.** 1068 cases pass, 0 fail, 0 skip, one more than 3.0.0 because of
the packaging test above. The declared Foundation conformance suite is green at 23
of 23 declared cases. The same suite and the same release gate now also pass from
an unpacked release archive, which is the defect this release exists to correct.

| Suite | Cases |
|---|---|
| foundation | 962 |
| context-delivery | 3 |
| context-assembly | 24 |
| design-space | 20 |
| integration | 15 |
| golden | 6 |
| adversarial | 38 |

## 3.0.0

**Semantic Closure. MAJOR.**

3.0.0 is not a redesign. It adds no Brand State, no profile, no capability and
no architecture. It closes five places where one governed semantic was stated
once and implemented twice, so that two conforming readers, two entry points or
two executors could reach different governed answers from the same approved
bytes.

Every one of the five is a breaking correction to an existing normative
contract, which is what makes this MAJOR under section 27.1. Each was found by
reproducing it on a clean checkout before any code was written, and each is
closed by a test that fails when the correction is removed.

### Breaking contract corrections

**Class A, section 28.1: one governed input contract at every reader.** The rule
that a governed document has an object root lived in one of five readers. The
other four returned the sequence, the JavaScript reader refused it, and the
declared conformance case `governed-input-sequence-root` said a sequence root is
not governable. The rule now lives in the shared reader, so a file path and bytes
already in hand are one contract with two doors. The nesting bound and the
duplicate-key rule are stated where both formats reach them, so a document that
arrived as JSON and one that arrived as YAML are bounded identically.

**Class B, section 8.0b: identity positions and identity binding.** Two
corrections in one class.

`manifest.version` was an identity position in a received Model Input Package
and not in the Manifest or the Build Plan that produced it. A `version`
differing only in line ending therefore passed validation and build with an
identical `contentHash`, `planHash` and `artifactHash`, and the runtime then
refused what the compiler had approved. The four enumerations now speak one
coordinate system, the position is the path in the document itself, and a
position that bears identity in one artefact bears it in every artefact carrying
the same path. CR and LF are rejected at an identity position because section
14.3 step 2 folds them into one hash; NEL, LINE SEPARATOR and PARAGRAPH
SEPARATOR are preserved, and the set is closed in both directions.

Reproducing an artefact's hashes proves it is intact and nothing more. Where a
governed artefact names the manifest another is about, `manifest.id`,
`manifest.version` and `manifest.contentHash` MUST all agree before either is
used. A Model Input Package naming another brand, another approved version or
another target, with every one of its own hashes correctly recomputed, validated
before this release.

**Class C, sections 11.4, 11.5 and 11.5a: the RULE contract.** RULE-level
`validatorRef` is removed. Foundation Validator Registry v1 is closed, has one
entry, and that entry applies to value contracts of kind `colour` with the
element value as its input, so the set of rule-level references that could
resolve was empty and `validationMode: deterministic` with `checks: []` was a
rule nothing enforced. A deterministic Foundation RULE now declares at least one
registered Foundation check, in the published value contract as well as in the
compiler, and `checks[]` is typed rather than an untyped array.

`validate_check` gained a stage. The compiled-stage rule ran over the authored
form and demanded a literal the author had deliberately deferred through
`elementValueRef`, so a branch the published RULE contract admits was unusable
through the governed build path while a direct compiler call materialised it.
The authored stage now accepts the deferred form and validates the reference's
own shape where it is written; the compiled stage still requires the resolved
value, because nothing downstream will resolve it.

`normalized_whitespace_ci` joins the registry as a distinct match mode, and the
pinned invisible code points it removes are stripped there and nowhere else.
`word_boundary_ci` is pinned to one declared Unicode version plus normative
fixtures, and the version declared is the one the segmentation engine
implements rather than the one section 14.3c pins for canonicalisation.

**Class D, sections 13.0a, 13.5a, 14 and 15.11: runtime contract enforcement.**
A 3.0 Build Plan declares `schemaVersion: 3.0.0` and every target states
`stateMap` and `styleTexture`, because both decide what reaches the compiled
context and an absent one is a governed decision made by whichever
implementation supplied the default. The compiler materialises every
decision-bearing check parameter, and the runtime refuses to invent a missing
one.

The 3.0 Compiled Brand Context contract constrains the fields consumers read.
Two schema-valid artefacts crashed a consumer under the 1.1 contract: an element
record with no `id`, and a validity timestamp that was not a timestamp.
`elementRecords[]` items now require the nine fields consumers read, and
`validFrom` and `validTo` carry an RFC 3339 pattern rather than a `format`
annotation no validator is obliged to enforce.

Every consumer that derives a governed decision from a Compiled Brand Context, a
Model Input Package or a Review Result validates that document against its
published contract before reading any field of it. A package declaring another
`kind` at another `schemaVersion` was re-sealed and released with a model call
before this release.

**Class E, section 10.2a: one relevance model.** Conflict relevance is decided
once, at build time, by the compiler. Context Assembly and the runtime consume
that decision and MUST NOT re-derive it, and a projection cannot change it. The
materialisation of section 13.5a happens afterwards and alters nothing.

### Runtime fail-closed corrections

- A validity window the runtime cannot read is not a window it may ignore. An
  unparseable `validFrom` or `validTo` means the artefact is not valid,
  independent of what the contract's pattern permitted.
- The published contract is executed before the first field read, including the
  fields a Runtime Decision Record copies as evidence. Asked afterwards, a
  non-object artefact raised out of the runtime and the record section 15.9
  requires was never written.
- `run_assembled_with_model` executes the Model Input Package contract, and the
  review validator executes all three: Compiled Brand Context, Model Input
  Package and Review Result.

### Interoperability fixes

- The one deterministic Model Input renderer moved into Foundation, and the
  assembler imports it. The runtime derives the expected bytes from the slots it
  verified and compares them byte for byte, so the rendered text stopped being
  an assertion the caller makes.
- `governed_io.py`, `canonical.py` and `model_input.py` ship byte-identical in
  every package, and the release gate proves it.
- The governed writer will not emit a document its own reader would reinterpret.

### Test and conformance expansion

**Conformance.** 1067 cases pass, 0 fail, 0 skip. The declared Foundation
conformance suite is green at 23 of 23 declared cases.

| Suite | Cases |
|---|---|
| foundation | 961 |
| context-delivery | 3 |
| context-assembly | 24 |
| design-space | 20 |
| integration | 15 |
| golden | 6 |
| adversarial | 38 |

Section 26.2 gained six requirements, each naming executed cases the release
gate resolves against the run it performs itself.

The suite gained five systemic mechanisms. Each enumerates a surface from a
machine-readable registry and fails when a new code path joins the surface
without an entry, so the *shape* of a defect is closed rather than one instance
of it. The strongest is the call-site proof for governed hash verification: for
each verifier call site the registry names the exact source line of its gate,
the test neutralises that one gate in a copy of the release, runs that one
driver against the copy in a subprocess, and requires the driver to stop
refusing. A driver that does not reach its site does not notice, and fails
there.

### Packaging and documentation

- `schemas/3.0.0/` publishes the Build Plan, Compiled Brand Context and Runtime
  Decision Record contracts; `value-schemas/3.0.0/` publishes the RULE value
  contract. The frozen 1.0.0 surface and the 1.1.0 contract beside it are
  unchanged.
- The three release-document readers in the suite derive the release from the
  specification the package ships instead of naming a file that is renamed every
  time.
- Migration notes for 2.x are in `OBDS-3.0.0-MIGRATION.md`.

### Non-blocking review finding, recorded not closed

The independent approval of this implementation was
`APPROVE WITH NON-BLOCKING FINDINGS`. The finding concerns a development label
in the hash-proof registry, not a normative contract: the reseal expectation
recorded for one `validate_review` hash boundary claims a stronger property than
that boundary proves. No Class A to E invariant is affected, the boundary itself
reproduces its hash correctly, and the identity binding described above holds
under attack. It is recorded here so that no release document claims more than
the reproducible evidence supports, and it is not a release blocker.

## 2.0.0

**Interchange correction. MAJOR.**

Three defects, all reported by a final outreach gate against the published
1.1.6 and each reproduced on a clean checkout before any code was written. Two
are specification defects and one is a conformance-evidence defect. Closing the
first of them is a breaking change, which is why this is 2.0; the reasoning is
below, under "Why this is 2.0 and not 1.1.7". The
reference implementation behaved correctly in that gate at every place it was
probed, and the five blockers 1.1.6 closed remained closed under attack.

### Section 28.1, governed YAML scalar resolution is pinned

Section 28 has always made JSON the canonical interchange format and allowed
YAML where it produces an equivalent JSON document. It never said how a YAML
plain scalar becomes a JSON value, and the reference loader inherited PyYAML's
YAML 1.1 implicit resolvers with only the boolean set replaced.

The consequence, measured on the published 1.1.6:

```text
input bytes    {"a": 1e3}

read as .json  {'a': 1000.0}   canonical sha256:ac51767992e3cb03...
read as .yaml  {'a': '1e3'}    canonical sha256:0504fb0fff0e8f1a...
```

One byte sequence, two governed values, two canonical hashes. The canonical hash
of a governed document depended on its filename, and two conforming
implementations reading the same approved manifest could compute different
`manifestContentHash`, `valueHash` and `governedResultHash` values. Every
governed artefact this project ships is YAML.

Section 28.1 now states the whole contract in two tables. Plain scalars resolve
under the YAML 1.2 Core Schema, and a plain scalar that resolves to null, a
boolean or a number must denote the same value when the same characters are read
as a JSON literal. `1e3` is therefore the number 1000, as JSON always said.

The second table is the part that matters for determinism. A plain scalar in a
form that YAML 1.1 silently turns into something the Core Schema does not is
**rejected**, not resolved either way: `017`, `1_000`, `12:30`, `2026-09-01`,
`0x1f`, `0o17`, `0b1010`, `~`, `.inf` and `.nan`. Accepting any of them under
either reading would leave a document's meaning dependent on which YAML version
the reader carries, which is the defect. Quoting always resolves it, and every
timestamp in this specification was already quoted.

`yes`, `no`, `on`, `off`, `y` and `n` remain strings, as OBDS 1.0 already
required. The reference no longer subtracts one resolver from PyYAML's YAML 1.1
table; it replaces the table, so one constructor owns the whole decision.

### Section 26.2 evidence is resolved, not counted

The release gate asserted `len(requirementsExercised) >= 12`. It never checked
that the named cases exist, are unique, executed or passed. Replacing all
fourteen case names with `no_such_test_0` through `no_such_test_13` and
rehashing the package manifest, as a release author would, left the gate green.
Four of the fourteen requirements named prose rather than a case at all.

That is the same failure the 1.1.5 validity guard had, and the same failure this
project fixed in 1.1.6 one guard away: a guard advertising a protection it
cannot give.

Each requirement now names one or more executed case identifiers of the form
`<suite>/<module>::<test>`. Guard 20 runs the seven conformance suites itself,
collects what actually executed, and fails when a declared identifier does not
exist, did not pass, was skipped, or is reused to satisfy a second requirement.
It also pins the fourteen requirement names, so removing one shrinks the claim
loudly instead of silently. There is no threshold left to raise.

Four requirements had no resolvable evidence, and the evidence for *explicit
context selection* was weak enough that four separate single-line inversions of
the projection logic survived the whole suite. The tests those four requirements
now point at assert the expected contents of a governed decision rather than a
relative property between two runs, which was the anti-pattern behind both this
defect and the 1.1.5 one.

### Section 14.3a is aligned with section 10.2a

Section 14.3a still argued from the pre-1.1.3 rule: "section 10.2 makes an
unresolved conflict a target failure ... so no `governedResultHash` exists for
such a build at all." Section 10.2a replaced that premise in 1.1.3. A conflict
that is not decision-relevant for a target does not fail it, and a hash does
exist. An implementer following 14.3a and one following 10.2a disagreed about
the one value section 26.2 makes an interoperability MUST.

The paragraph now distinguishes the two cases and states what the hash means:
**`governedResultHash` identifies the governed result, not the diagnostic
history that produced it.** A build whose irrelevant conflict contributes
nothing hashes the same as a build where that subject has no element at all,
because both apply exactly the same truth. The distinction is not lost: section
13.7 keeps the conflict in the Build Report, marked as not decision-relevant, so
an audit still sees the manifest defect. The reference implementation was
already right; only the text moved.

### Why this is 2.0 and not 1.1.7

It was drafted as 1.1.7 and that was wrong. Section 27.1 allows PATCH only for a
backwards-compatible clarification or defect fix, and section 28.1 is neither.

The argument for PATCH was that a document relying on the old reading was
already outside section 28, which requires YAML to produce an equivalent JSON
document. That holds for `1e3`, which was the string `"1e3"` as YAML and the
number 1000 as JSON: such a document never had one canonical identity. It does
not hold for the rejection table. `017` was the number 15, and a manifest
containing it produced a perfectly good equivalent JSON document, `{"a": 15}`.
Section 28 was satisfied. Rejecting it now is not a clarification, it is a
breaking change, and section 27.1 has one sentence for that case: "A 1.x
implementation MUST NOT silently reinterpret an existing 1.0 field with
incompatible meaning. Breaking semantics require OBDS 2.0."

MINOR was not available either: section 27.1 defines it as a backwards-compatible
capability, profile or optional field, and this is none of those.

So the honest classification is MAJOR. A standard that argues its own rules do
not quite apply to it is worth less than one that follows them and says why.

**2.0 is deliberately narrow.** No new Brand State, no new profile, no new
capability, no architectural change, no redesign of the hash model. One
interchange correction, one evidence correction, one specification correction,
and a migration table. Section 30 states what a 1.x manifest has to change,
which for almost every manifest is nothing: all 29 governed YAML documents this
release ships resolve identically under both readings, every published example
hash is unchanged, and the frozen OBDS 1.0.0 contract surface is byte-identical
at `sha256:517683bb3496867daa2346ceb2f7844e46015f926ff757a9c23da90cf1e5f469`.

### Conformance and compatibility

Conformance rises from 279 to 429 passing tests, the one hundred and fifty
added being regression coverage for these three defects, for the defects a
third, a fourth, a fifth, a sixth and a seventh independent review found in the
candidate itself,
and the evidence four section 26.2 requirements now point at.

The first draft of section 28.1 moved the ambiguity instead of removing it, and
two independent reviews said so. An empty scalar became the empty string rather
than null, `!!str 1e3` reached a number through an explicit tag, a merge key
became a literal `<<` key, the writer emitted plain `1e3` for a string its own
reader then read as a number, and an anchor rule invalidated a Build Plan this
repository ships. The section now pins the YAML version and not only the scalar
rules, refuses explicit tags including the non-specific `!`, refuses the merge
key while leaving anchors and aliases alone, refuses a raw U+0085, U+2028 or
U+2029, and the writer quotes anything that would not survive its own reader.

A third independent review found four more, all in the same section, and all
fixed before publication. The rejection table listed `1.` and `017` but not
`1.e3` and `017e3`, which are YAML 1.2 core floats and not JSON numbers, so they
fell through to the string rule and reproduced the exact defect the section
exists to close. The anchors-and-aliases rule called itself closed while
bounding only recursion: eight aliases per level over nine levels is 425 bytes
of governed YAML and 175,304,795 nodes expanded, so the section
now requires a documented expansion bound and the reference implementation
rejects above one million nodes. Fifteen YAML blocks in this specification carry
keys with no value, which the new rejection table refuses, so section 28.1 now
names that spelling as shape-sketch notation and a test holds every block in the
document to the rule. And the migration section claimed one form changed
meaning when the class is every plain scalar in exponent notation: `1e3`, `1E3`,
`2E-2`, `-1.5e3` and the rest, minus the spellings a YAML 1.1 reader already
read as numbers. That is the only silent change in this release, it is the only
one no validator can report, and it now has its own named check.

A fourth independent review found five more, and they are why the rejection
table stopped enumerating spellings. Two rows named a class and matched only
part of it: a digit separator combined with a decimal point or a sexagesimal
colon (`1_000.0`, `1_0.5`, `1_0:30`) was a number to a YAML 1.1 reader and a
string here, and a timestamp written with a space before its zone
(`2026-09-01 00:00:00 Z`) was a datetime there and a string here. The first is a
value that moves with no diagnostic; the second is a form 1.1.6 refused outright
and this release would have started accepting. The table now carries a final row
that rejects on the class: any plain scalar a YAML 1.1 reader resolves to a
number that the JSON grammar does not produce. Exponent notation is now the only
remaining form whose value differs between the 1.1.6 reader and this one.

A fifth, a sixth and a seventh independent review then showed the reverse failure, which
matters more: stating the class in hand-written patterns made the table
over-reach and refuse strings. `._5`, `2026-9-1`, `0__8`, `0:07`, `+0o7`, `0X1f`
and `-.nan` are strings under YAML 1.1 and under YAML 1.2, and every one of them
was being rejected as an ambiguous scalar. Section 28.1 says a form not listed
and not matching the resolution table is a string, and the reference
implementation is the section 26.2 oracle, so over-reaching here would have made
an independent implementation that read the table literally non-interoperable
with it. The YAML 1.1 rows are now the resolver itself rather than a paraphrase
of it, and the YAML 1.2 rows are spelled as YAML 1.2 spells them: only `inf`
takes a sign, the octal `0o` form takes none, and a timestamp's date-only
spelling needs two-digit fields. That the table is closed is now a conformance
case rather than an assertion:
`test_the_rejection_table_is_closed_against_the_real_yaml_resolvers` drives
PyYAML's own resolver and a written-out YAML 1.2 core schema over every short
string on a numeric alphabet, and requires a form to be rejected exactly when
some YAML version reads it as a value the JSON grammar does not produce. The
only accepted exceptions are `yes`, `no`, `on`, `off`, `y` and `n`, which
section 28.1 has required to be strings since OBDS 1.0.

Nesting is bounded for the same reason as alias expansion, and by the seventh
review's argument: unstated, the limit is whatever the reader's call stack
allows. The 2.0.0 candidate read 327 levels where 1.1.6 read 491, and past that
both crashed rather than refused. Section 28.1 now requires a documented nesting
bound over the data model, so JSON and YAML cannot disagree about it. A level is
one nested collection, counting the outermost; the reference implementation
accepts one hundred and rejects the hundred and first. The deepest governed
document this project ships nests ten.

The migration table also stated YAML 1.2 readings in a column headed by what
1.1.6 did, which would have told a migrator to rewrite the string `017e3` as the
number `17000` and move the hash the section exists to protect. The column is
now the 1.1.6 reading throughout and says so. The published grep for exponent
notation missed flow mappings, inline sequences and trailing comments; it now
matches the value wherever it sits on the line.

The generator for `OBDS-2.0.0-TEST-RESULT.json` described this release as a
maintenance release with no normative contract change, a sentence 1.1.0 shipped
by copying 1.0.4 and this release nearly shipped over a MAJOR. The release kind
and the byte-identity list are now derived from the version and the publication
record rather than written twice.

No schema in the frozen surface changed. `release-schemas/release-test-result.schema.json`
changed, because the evidence array now carries resolvable identifiers instead
of prose; it is release metadata, not part of the OBDS 1.0.0 contract surface,
whose fingerprint is unchanged at
`sha256:517683bb3496867daa2346ceb2f7844e46015f926ff757a9c23da90cf1e5f469`.
No Brand State was added, no capability was added, and no published example hash
moved.

Explicitly out of scope, and not touched: the authored-form `elementValueRef`
validation issue, the CR/LF identity and hash injectivity observation, the
`llms.txt` previous-release list, the homepage freeze enumeration, the
`.gitignore` `.env` pattern, `scope: null`, the unreachable `-NOT-FOUND`
diagnostic, stale artefacts in reused output directories, `OBDS-CHECK-*`
documentation, the `/README.md` live route, and authoring wording.

## 1.1.6

**Hardening release. PATCH, with one normative addition.**

Five defects, all reported by a final outreach gate against the published 1.1.5
and each reproduced on a clean checkout before any code was written. They fall
into three classes: canonical identity and Unicode determinism, RULE
applicability and conflict relevance, and conformance boundary evidence.

Unlike 1.1.4 and 1.1.5 this release is not purely behavioural. Section 14.3c is
new normative text, and it narrows the set of admissible documents. That is
stated plainly rather than described as no normative change, because a reader
comparing 1.1.5 to 1.1.6 would find the difference themselves.

### Section 14.3c, the Unicode version is pinned

`Unicode 15.1.0`. A governed string or object key must consist only of code
points assigned in that version, or Unicode noncharacters, and must contain no
surrogate. Anything else is rejected before normalisation.

Section 14.3 step 1 normalises to NFC, and never said which Unicode version
performs it. NFC is only stable for code points already assigned: a code point
unassigned in one version and given a non-zero canonical combining class in the
next reorders against its neighbours. Forty-six code points are unassigned in
15.1.0 and are such marks from 16.0.0 onward, and the number grows with every
version.

The consequence was measured, not argued. Byte-identical `canonical.py` on
CPython 3.13, which carries Unicode 15.1.0, and on CPython 3.14, which carries
16.0.0, produced different canonical bytes for `{"s":"ạࢗz"}`:
`7b2273223a2261e0a297cca37a227d` against `7b2273223a22e1baa1e0a2977a227d`. The
two runtimes also disagreed on whether a two-key document was valid at all, one
canonicalising two keys where the other rejected a duplicate. Through the
compiler that moved `manifestContentHash`, `governedResultHash` and
`artifactHash`, so a manifest approved under one runtime no longer built under
the other. Section 14.3a calls `governedResultHash` the value two independent
implementations must agree on; without a pinned version they could not.

The published vector suite could not detect it. Its highest code point is
U+1F600 and none of the forty-six appears in it, so both implementations passed
all fifty-nine vectors and still diverged.

Noncharacters are admitted deliberately. Unicode guarantees they are never
assigned, so their combining class and decomposition can never change; U+FFFF
appears in the published canonical vectors and keeps working. Within the
admitted set the Unicode Normalization Stability Policy makes NFC identical on
every database at or after the pinned version.

The release ships the pinned assignment set as data,
`reference/foundation/src/obds_ref/unicode-pin-15.1.0.json`, 715 ranges, so an
implementation on a newer Unicode database can apply the rule without carrying
its own copy of 15.1.0. Raising the pinned version widens the admissible set and
is therefore not a PATCH.

### Section 8.0a, canonical identity for `id` and `subject`

Every governed string is compared after NFC. Element ids and semantic subjects
were the exception: they were compared and sorted as raw document bytes, in
subject grouping, in id uniqueness, in every reference resolution and in the
`selection` ordering that section 14.3a hashes.

`approval.contentHash` is computed over canonical bytes, which are NFC, so an
NFD and an NFC spelling of one subject are the same approved snapshot. Raw
comparison made them two subjects. A manifest with `approval.contentHash`
`sha256:b0b98703…` therefore produced `governedResultHash`
`sha256:3ca674eb…` in its NFD spelling and `sha256:0be5151c…` in its NFC
spelling, and in the first the broad value and the narrow override meant to
replace it both survived as governed truth, with `status: ready` and an empty
`conflicts[]`. One approved manifest, two governed results, and an artefact
asserting that one semantic subject resolved to two values.

1.1.4 pinned NFC where the defect was found, in scope comparison. 1.1.6 pins it
at the two remaining places that decide which truth is selected and in what
order it is hashed. Two canonically equivalent element ids are now a duplicate,
exactly as section 9 already treats canonically equivalent scope values. This is
a comparison rule: the stored representation is untouched.

### Section 11.5, `elementValueRef` resolves through the governed selection

A check binding another element's value through `elementValueRef` was resolved
against the raw approved manifest snapshot, gated on `state: defined` alone.
Scope, validity, precedence and conflict resolution were all skipped.

Reproduced: an element with `validity.to` of 2026-06-01, a Build Plan `asOf` of
2026-08-28, and a RULE with `obligation: require`, `enforcement: block` and a
`literal_required` check referencing it. The element was correctly absent from
`availableElementIds`, and its withdrawn text was compiled into an active
blocking check with `status: ready`. Time alone triggered it; no authoring error
was needed. End to end, `obds check` then passed the superseded text and blocked
the current governed value, while `governedResultHash` did not move at all, so
two conforming implementations could agree on the section 26.2 governance hash
and disagree on whether output was blocked.

`elementValueRef` now runs through the same requirement resolution as
`requiresDefinedRefs` and carries the same four causes,
`OBDS-BUILD-REQUIRED-NOT-FOUND`, `-OUT-OF-SCOPE`, `-EXPIRED` and
`-NOT-DEFINED`. The check is never silently omitted, and no production artefact
is written.

### Section 10.2a, conflict relevance reads the rule, not only the list

Section 10.2a states a rule and then illustrates it with five concrete cases.
The list was read as the whole rule, and it had not been revisited when 1.1.5
made RULES elements requirement-bearing.

The result was a build that got better when the manifest got worse. Two
competing RULES on one subject, both `inform`, one declaring a
`requiresDefinedRefs` dependency that was `unknown`: the conflict was marked
`decisionRelevant: false`, the RULE never bound, and the target built and wrote
an artefact. Deleting the rival RULE let the surviving one bind, and the same
target then failed with `OBDS-BUILD-REQUIRED-NOT-DEFINED`. Repairing a manifest
defect must never make a governed build less valid.

Case 2 now counts a `defined` RULE that would govern this build if it won:
`enforcement` of `block` or `require_approval` as before, and additionally a
declared `requiresDefinedRefs` or declared `checks`. Case 1 now also counts an
element named in the target's `contextAssembly.eligibleGuidanceIds`, and
dependencies named through `elementValueRef`. The section now says explicitly
that where the list and the rule disagree, the rule governs.

A prohibition counts as well, because section 14.1 says `hardBoundaries`
contains applicable prohibitions **and** rules with `enforcement: block` or
`require_approval`, and repeats it a paragraph down: "Prohibition appears in
`hardBoundaries` through applicable explicit RULE elements." An applicable
prohibition therefore always reaches the compiled context, whatever its
enforcement, so a conflict over one is always decision-relevant.

It took three attempts, and the third is worth recording too: the compiler slot
was corrected while Context Assembly rebuilt the same list downstream with the
same enforcement-only filter, so the prohibition reached the artefact and then
vanished again on the way to the model input. Both filters now read section
14.1, and every other place naming `require_approval` was checked and is
enforcement-specific by design.

The first two attempts: The arm was first added, then withdrawn on the argument
that a prohibition with advisory enforcement reaches nothing, and the fifth
review showed why the argument was wrong: it was reading the reference
implementation rather than section 14.1. The slot filter selected on enforcement
alone, so an applicable `obligation: prohibit` RULE with advisory enforcement
appeared nowhere in the artefact. That is corrected here too; it is a
consequence of getting the conflict rule right, not a separate change.

A conflict that genuinely changes nothing this target reads still builds, and is
still reported in `conflicts[]`. Not every conflict is a blocker.

### The half-open validity boundary is proved by execution

Section 10.1 defines validity as `[from, to)`. Three shipped mechanisms claimed
to pin it: a changelog sentence, `test_validity_window_interval_is_half_open`,
and a release-gate guard whose failure message read "the validity fixture no
longer pins the half-open boundary at validTo".

None of them executed the implementation. The test read three timestamps out of
a fixture and asserted they agreed with each other; the guard asserted that the
fixture agreed with itself. No fixture placed `asOf` on a boundary instant. All
four boundary comparisons, `<` and `>=` in the compiler's `_valid_at` and in the
runtime's `_artifact_valid_at`, could be inverted simultaneously and every test
in the suite still reported a pass.

1.1.6 adds tests that call `_valid_at`, `_artifact_valid_at` and
`run_with_model` at `from` minus one second, `from`, `to` minus one second and
`to` exactly, in `Z`, offset and fractional-second spellings, and through a
complete build. Each of the four mutations is now killed. The release gate no
longer asserts fixture self-consistency alone: it executes those tests and fails
if they do not run or do not pass. A guard must not advertise protection it
cannot give.

### What the independent review caught

The first implementation of section 14.3c was wrong twice, and an independent
reviewer who had not written it found both before release.

The guard located a code point by the parity of a single binary search over the
flattened range bounds. That is correct inside a range and wrong on its upper
endpoint, so all 715 upper endpoints were rejected as unassigned, U+0377 and
U+10FFFF among them. No published vector and no shipped example uses one, so the
whole suite stayed green. The lookup now carries starts and ends separately and
both bounds are inclusive; a test walks every range endpoint and both
neighbours, and a second test cross-checks the entire shipped table against the
15.1.0 database when the host carries that version.

Admitting only code points assigned in 15.1.0 makes NFC identical on every
database at or after 15.1.0. It says nothing about an older one, which does not
know those code points and gives them combining class zero. The package
documented Python 3.11, whose Unicode 14 database therefore produced different
canonical bytes for an admitted 15.0 character. `canonical.py` now refuses to
import on a host below the pinned version, and the documented minimum is
CPython 3.13, the first release carrying Unicode 15.1.0.

A second round of review, and a separate adversarial audit of the three
corrected classes, found five more. The pin admitted the surrogate range,
because a surrogate's Unicode category is not `Cn`: Python rejected it later
when encoding UTF-8 while the JavaScript oracle emitted an escape, so the two
disagreed on a document neither should have accepted. The oracle did not check
its own Unicode floor, and the package documented Node 18. `elementValueRef`,
`requiresDefined` and the governed selection were normalised while the four
rendered slots, the compiled checks, the `stateMap.kinds` vocabulary and value
contract ids were not, so two canonically equivalent manifests agreed on
`governedResultHash` and disagreed on `artifactHash`, and an element could drop
out of STATE_MAP silently. Context Assembly and Context Delivery still indexed
`elementRecords` by the raw id, so a valid 1.1.6 artefact whose ids were not
already NFC was refused by the same release's own consumer. And the new
`obligation: prohibit` arm of conflict relevance failed targets that could not
observe the prohibition at all, which is the fail-arbitrary behaviour section
10.2a forbids; it was withdrawn.

All five are closed, each with a test. The pinned table now excludes surrogates,
the minimum is CPython 3.13 and Node 21, and every identity path named in
section 8.0a is normalised, including the rendered slots, so an artefact
presents one identity throughout.

A third and a fourth round found five more, all in the same class and all in
code this release had already touched. `identity_key` reused the
canonicalisation helper and therefore folded CR and CRLF to LF, which section
8.0a does not ask for: `a\rb` and `a\nb` are two identities, and merging them
rejected two distinct elements as one duplicate. Context Assembly sorted the
fact, gap and guidance elements after their text had been rendered, so the
emitted id arrays looked correctly ordered while `stateMap`, `guidanceContext`
and `modelInputHash` still carried the request's selection order. The assembly
request `targetId` and the `manifest_checked` resolution manifest id were still
compared raw. And a version stamp edit on the authoring page had rewritten a
historical sentence, which the scope freeze forbids; it is restored.

The pattern is worth stating plainly, because it is the same one the outreach
gate reported. Three times the fix went to the line that was reported rather
than to the class behind it, and each round found the class one level further
down. The fourth round swept every identity comparison, index, ordering and
emitted value in the reference implementation at once, and each one is now
pinned by a test that fails when the normalisation is removed.

### Conformance and compatibility

Conformance rises from 199 to 279 passing tests, the eighty added being
regression coverage for these five defects, each verified to fail against the
1.1.5 implementation.

No schema changed. No Brand State was added. No capability was added. The
frozen OBDS 1.0.0 contract surface is byte-identical, fingerprint
`sha256:517683bb3496867daa2346ceb2f7844e46015f926ff757a9c23da90cf1e5f469`,
unchanged since 1.0.0.

Every shipped example is ASCII, so no published example hash moves for that
reason. `governedResultHash` semantics are unchanged for every document that was
already unambiguous; it changes only where 1.1.5 produced two different values
for one approved manifest, which is the defect.

Explicitly out of scope, and not touched: the YAML octal resolver, stale
artefacts left in a reused output directory, historical publication-record
entries, withdrawn drafts in the public Git history, authoring wording, and the
broader mutation-coverage gaps found by the same gate.

One change outside the five defects is deliberate and authorised separately, so
it is named here rather than left for a reader to find. `tools/deploy-smoke-test.py`
pins the current release archive instead of the previous one, probes the local
virtualenv under the name it actually has, adds `/.env.local` and
`/.vercel/project.json`, and drops the three probes that named a client's source
documents. The tool is served from the deployed site, so those three published
the inventory the probe exists to keep private. It ships in `tools/`, which is
not part of the release package, so it moves no release hash.

## 1.1.5

**Maintenance release. PATCH. No new capability.**

An applicable RULE may now be used only when every element it names in
`requiresDefinedRefs[]` resolves to exactly one applicable `defined` Brand
Element. A dependency that is missing, out of scope for the target, invalid at
the Build Plan `asOf`, lost to a more specific element in its subject, in an
unresolved subject conflict, or in any state other than `defined` now fails the
target build, as section 13 already required. No production artefact is written.

Before this, the Foundation compiler contained no reference to the field at all.
A RULE with `obligation: prohibit` and `enforcement: block` whose declared
dependency did not exist, or existed as `unknown`, still compiled into an active
check and the target built successfully. That is fail-open in the one place the
specification is most explicit about failing closed.

The fix reuses the existing requirement resolution, so the four established
causes stay distinguishable: `OBDS-BUILD-REQUIRED-NOT-FOUND`,
`-OUT-OF-SCOPE`, `-EXPIRED` and `-NOT-DEFINED`. The Build Report names the
requiring RULE in `requirements[].requiringRuleElementId`. A dangling
`requiresDefinedRefs` entry is now a manifest validation error, because
section 7 already counts the field as a Foundation internal reference.

`references[]` is unchanged and remains non-blocking: it is explanatory
material, not an execution prerequisite. A RULE that loses its subject to a
more specific RULE does not bind its dependencies, because it is never used.

Conformance rises from 184 to 199 passing tests, the fifteen added tests being
regression coverage for this defect. All five shipped example artefacts are
byte-identical to 1.1.4 apart from the `builtAt` timestamp, no published hash
moved, and no schema, Brand State, capability or `governedResultHash` semantic
changed.

## 1.1.4

**Maintenance release. PATCH. No new capability.**

Scope comparison now normalises values to Unicode NFC before comparing them, as
section 9 already required. Scope collections compare as sets and array order is
not significant. Duplicate scope values, including canonically equivalent NFC/NFD
pairs, now make the document invalid.

Before this, `canonical.py` NFC-normalised every string before hashing while the
scope decision logic compared raw strings. Two manifests differing only in the
Unicode form of a scope value therefore carried an identical `approval.contentHash`
yet produced different governed build decisions: a stale broader value could win a
subject over its narrower override, and an `obligation: prohibit` /
`enforcement: block` RULE could silently stop applying, with `compiledChecks`
dropping from 1 to 0 and no error anywhere.

The fix is one helper applied at three comparison sites in the reference compiler:
scope matching, scope specificity and scope validation. Normalisation happens at
comparison time, so no stored Brand Truth is mutated and no published hash moves.
All five shipped example artefacts are byte-identical to 1.1.3 apart from the
`builtAt` timestamp. No schema changed, no Brand State was added, no capability was
added and `governedResultHash` semantics are unchanged.

**Conformance.** 184 cases pass, 0 fail, 0 skip. Foundation grew from 81 to 89
with eight Unicode NFC scope-comparison regression cases.

## 1.1.3

**Maintenance release. PATCH. No new capability.**

Five defects from the final outreach gate. One corrects a behaviour; the rest
are text, vectors and tooling. No published example hash moved.

**A hard conflict now fails a target only when the target can read it.** Section
10.2 said a conflict is a conflict and stopped there, so the reference failed
every target whenever any subject anywhere in the scope-matching set was
unresolved, including subjects the target neither requires nor selects. That is
fail-arbitrary, not fail-closed: the same manifest blocked or built depending on
which unrelated subject a curator happened to leave open.

New section 10.2a states when a conflict is decision-relevant: the element is
named in `requiresDefined`, or is a blocking or approval-requiring RULE bound
for HARD_BOUNDARIES, or is a defined non-rules fact bound for FACT_GROUNDING, or
is carried into STATE_MAP or STYLE_TEXTURE by the target's own declared policy.
The first three are unconditional; the last two follow what the target declared.
An irrelevant conflict is **not** discarded: it stays in `conflicts[]` marked
`decisionRelevant: false`, because it remains a manifest defect even when this
target does not touch it. Five fixture cases pin it, including the two the
default policies make relevant without the target naming anything.

**Key ordering says one thing.** Step 3 of section 14.3 cited "RFC 8785 /
ECMAScript property sorting" as if those were the same algorithm. They are not:
`Object.keys({"10":1,"2":2})` yields `["2","10"]`, code-unit order yields
`["10","2"]`. The step now states lexicographic UTF-16 code-unit order, names
the ECMAScript enumeration order as explicitly not it, and gives the worked
case. Nine ordering vectors were added; none existed.

**`selection` is applicability then precedence, and nothing after it.** Section
14.3a named three filters and never said that `styleTexture` and `stateMap` are
not among them, so an implementer building `selection` from `includedElementIds`
would produce a different governed result. It now says so, and says the part
that is easy to get wrong in the other direction: both policies do sit inside
`target`, which the payload carries verbatim, so changing one still moves
`governedResultHash` legitimately. Two plans asking for different projections
are different governed requests. What is forbidden is the projection changing
which truth was resolved. A four-variant fixture pins the identical selection
across policies that render nothing in common.

**The cross-language vectors are now an oracle.** `canonical-vectors.json`
carried inputs only, so it could prove two implementations agreed with each
other and nothing more. Every vector now carries its canonical text, the
lowercase hex of its canonical UTF-8 bytes and their SHA-256, and the
must-reject documents are listed separately. A third-party implementation
validates itself against the published file without running Python or
JavaScript beside it. `canonicalHex` is authoritative because it survives
transports that mangle `U+2028`, `U+2029` and line endings.

**Current-release surfaces.** `/authoring/` shipped through all of 1.1.2
announcing OBDS 1.1.0 in its title, status badge and subtitle, while its own
deep links pointed at the current release. The home page said "Previous release:
OBDS 1.1.0" when it was 1.1.1, and gave both 27 and 28 as the public contract
count. All corrected. The release gate's version guard read `index.html` alone;
it now reads every HTML page in the tree, `llms.txt`, and the publication
metadata.

**Conformance.** 176 cases pass, 0 fail, 0 skip. Foundation grew from 75 to 81
with the conflict-relevance and governed-selection cases; adversarial from 33 to
38 with the vector-oracle and key-ordering cases.

**Section 27.1 classification.** The conflict correction changes behaviour in
exactly one direction: a build that failed only because of a conflict the target
could not observe now succeeds. No previously succeeding build fails, no
previously valid artefact becomes invalid, and no published hash moved. Every
other change is a clarification, a fixture, a vector or tooling. PATCH.

## 1.1.2

**Maintenance release. PATCH. No breaking change, no new capability.**

Five defects, all found by fresh external readers against published 1.1.1. Both
changes to normative text write down behaviour the shipped reference already
had; neither changes a byte any implementation produces.

**The string escape set is now stated.** Section 14.3 resolved line endings in
1.1.1 and still named no escape set: step 7 covered non-ASCII only. A tab could
be serialised as `\t` or as `\u0009`, both valid JSON, and the two hash
differently — the same defect class as the carriage-return divergence 1.1.1
fixed, one layer down. New section 14.3b states the full table, identical for
string values and object keys: short escapes for quote, reverse solidus,
backspace, tab, line feed, form feed and carriage return; lowercase
six-character escapes for the rest of `U+0000` to `U+001F`; everything else
emitted directly. Solidus is not escaped, `U+007F` is not escaped, `U+2028` and
`U+2029` are emitted directly, and hex digits are lowercase.

Both shipped canonicalisers were measured first: they already agreed on all 38
value and key cases. 14.3b records that behaviour rather than choosing a new
one. Thirty-two new cross-language vectors cover every row of the table in both
positions; the suite now compares **51 vectors with zero byte differences**.

One test-harness defect fell out of the measurement: `canonical_js.mjs` printed
canonical text with `console.log`, and `U+2028` and `U+2029` are line
terminators for Python's `splitlines()`, so adding those vectors would have
silently misaligned the comparison. The harness now emits one line of hex per
vector.

**The validity window has one rule.** Section 14.0 said both "the interval in
which **the compiled selection** remains valid" and "the nearest surrounding
validity boundaries of **all target-scope-matching elements**". Those are
different sets, and the two readings give different `validTo` values, so two
conforming runtimes would accept and reject the same artefact.

The shipped behaviour was measured before anything was written: the window comes
from every scope-matching element, taken before the `asOf` filter and before
precedence. Section 14.0 now says exactly that, and says why — a losing
candidate whose validity begins tomorrow changes the selection tomorrow, so the
window has to end there. Six fixture cases pin it, including a future-starting
element, an expiring element, a losing precedence candidate, a non-applicable
element and the half-open boundary at `validTo`.

**Version stamps.** The 1.1.1 specification stamped itself `**Version:** 1.1.0`,
the public README announced 1.1.0, and the website `<title>`, description and
`og:description` all said 1.1.0 while the page body said 1.1.1. Corrected.

**Changelog history.** The 1.1.0 section had been rewritten with 1.1.1's
conformance numbers. It is restored to what 1.1.0 actually ran:
1.1.0 ran 123 cases with foundation 43.

**Four new release-gate guards**, one per regression above: the specification's
own `**Version:**` line must equal the release; the website title and current
release labels must match; a historical changelog section must not carry the
current release's counts; and the canonical string vectors and the
validity-window fixture must both agree with the normative rule.

**Conformance.** 165 cases pass, 0 fail, 0 skip. Foundation grew from 49 to 75
with the escape-table and validity-window cases.

**Section 27.1 classification.** Every change is a clarification, a defect fix
in a document or a test, or a correction to release metadata. No published hash
of any published example moved. PATCH.

## 1.1.1

**Maintenance release. PATCH. No breaking change, no new capability.**

Every change here fixes a defect an external reader found in 1.1.0. Nothing was
added, nothing was designed, and no normative contract moved.

**Canonicalisation, the one that mattered.** Section 14.3 step 1 said "every
string and object key"; step 2 said only "inside strings". The two
canonicalisers shipped in 1.1.0 read the asymmetry differently: the Python
reference normalised CR inside object keys, `canonical_js.mjs` did not. The same
manifest therefore produced two different `governedResultHash` values, which is
exactly what section 14.3a says MUST NOT happen. Step 2 now reads "inside every
string and object key to LF, CRLF first and then any remaining CR", the
JavaScript canonicaliser uses one normalisation function for keys and values,
and six cross-language vectors cover CR and CRLF in values, in keys, mixed and
nested. A key collision created by the normalisation, such as `a\rb` beside
`a\nb`, must be rejected rather than silently collapsed, and both
implementations now are tested to reject it. No published hash moved: no
governed payload in any published example or fixture contains a carriage return.

**The section 14 example.** The normative Compiled Brand Context example still
carried `schemaVersion: 1.0.0` and no `governedResultHash`, so an implementer
who followed it emitted an artefact the release's own contract rejected. It is
now a valid 1.1 artefact, and the release gate validates it against
`schemas/1.1.0/compiled-context.schema.json` on every run.

**The context id rule.** `context-id.json` asserted a rule and cited section 14
for it; section 14 did not contain the rule, and its example contradicted the
fixture. Section 14 now states it: `{manifest.id}:context:{targetId}`, neither
part escaped, trimmed or case-folded. The example follows it.

**The `asOf` representation.** Section 14.3a pinned `target` as verbatim and
said nothing about `asOf` beside it. It now says `asOf` is the timezone-aware
ISO 8601 string exactly as the validated Build Plan carries it, never parsed and
re-serialised. Two spellings of one instant are two documents.

**`requiresDefined`.** The `OBDS-BUILD-REQUIRED-NOT-DEFINED` description was
two-valued about an element that lost its subject to a more specific override,
and the two readings disagreed about whether the build succeeds. Section 13.1
now states one: `requiresDefined` is an element-ID requirement, the listed
element must itself be the `defined` winner of its subject, and an override does
not satisfy a requirement naming the element it displaced. This is the behaviour
the reference already had. Subject-level reusable requirements stay deferred
target-governance research. Four fixture cases pin it.

**Release metadata drift.** 1.1.0 stated three different conformance numbers
across its own documents, shipped a `TEST-REQUIREMENTS.md` that was a verbatim
1.0.4 file, and omitted its only new contract from both the schema index and the
publication map. All corrected. `TEST-RESULT.json` notes and `promotedFrom` are
now generated rather than carried forward, and `requirementsExercised` enumerates
all fourteen section 26.2 requirements rather than twelve.

**The release gate now fails on this class.** Six new checks: documents that
disagree on the case counts; a release document that names another release;
`TEST-RESULT.json` contradicting itself or promising a field it does not carry;
a served contract missing from the index or the map, or a mapped contract the
release does not serve; `publication-record.json` or the website disagreeing
with the built artefacts; and a normative or published example that fails its
own published schema. Every one exists because a human reader found the defect
and no mechanical check did.

**Authoring page.** Its only worked example failed two published schemas:
`sourceRefs` was an array of objects against `items: {type: string}`, and the
colour value omitted the required `name`. Both fixed, and the gate now validates
every published structured example.

**Conformance.** 139 cases pass, 0 fail, 0 skip. The foundation suite grew to 49
with the `requiresDefined` precedence cases, the `asOf` case and the section 14
example check; adversarial grew to 33 with the line-ending vectors.

**Section 27.1 classification.** Every change above is a clarification or a
defect fix in a document, an example, a test or the gate. `schemas/1.1.0/` and
the 27 public 1.0.0 contracts are byte-identical to 1.1.0. No published hash of
any published example moved. PATCH.

**Known and deliberately not fixed.** The `title` of
`schemas/1.1.0/compiled-context.schema.json` reads "OBDS Compiled Brand Context
1.0.0 1.1.0". Correcting it would change the bytes of a contract already
published at a versioned URL, which is the one thing this project's own rules
forbid, so it stands until the next contract version.

## 1.1.0

**Independent implementability completion. MINOR. No breaking change.**

An independent TypeScript implementation, written blind from the public
documents, reproduced eight published OBDS hashes on its first attempt and then
could not reproduce `artifactHash`. The reason was not a defect in the
canonicaliser. It was that OBDS defined no payload two implementations were
required to produce identically. Section 14.3 says an implementation must
reproduce the same hash *for the same payload*; two implementations that render
governed truth differently have different payloads, so different hashes were
always correct behaviour. There was simply nothing to be interoperable about.

1.1 adds that missing thing and changes nothing that exists.

**`governedResultHash`, section 14.3a.** A new field on the Compiled Brand
Context, carrying SHA-256 over a small payload: the manifest id, the Build Plan
target minus `maxTokens`, `asOf`, and one entry per applicable element with its
id, subject, state and a hash of its value. Two independent implementations
given the same manifest and the same Build Plan produce the same value,
whatever their prose, compiler identity, tokenizer or token counts.

The exclusions are the contract. `sourceRefs`, `annotations` and the manifest
`version` are excluded, so a section 27.2 governance-neutral PATCH does not move
the hash. Compiler identity, tokenizer identity, slots and token counts are
excluded because they are implementation facts. Content integrity comes from the
per-element value hashes rather than from the manifest content hash, so the
payload does not depend on how the manifest document was serialised.

**`artifactHash` is unchanged.** It still identifies this exact artefact,
including its rendered slots and its provenance, and it may legitimately differ
across implementations. Section 14.3 is not modified. Section 16.1 approvals and
section 30 audit trails keep the meaning they had.

**Section 10.2 precedence is now decidable.** "A strict superset of scope
restrictions" admitted two readings that produced opposite build outcomes on an
ordinary multi-market manifest: the reference resolved a winner, and an
independent implementer reading the same sentence raised a hard conflict. The
rule is now stated once, semantically: an element is more specific when the set
of build targets it matches is a strict subset of the set the other matches.
That is a strict partial order, and it reproduces shipped 1.0.4 behaviour on
every discriminating case, including both conflict outcomes.

**The scope vocabulary is closed at nine dimensions.** `brands` was accepted by
the reference and appeared nowhere in the specification; `contentPurposes`
appeared in the section 9 example and was rejected by the reference. Both are
fixed. Scope values compare as NFC-normalised sets, and an element restricting a
dimension the target does not declare is not applicable, which is the
fail-closed reading and what the reference already did.

**Required truth now reaches the artefact.** Section 13.2 said HARD_BOUNDARIES
and FACT_GROUNDING always include every applicable element required by the
target. A knowledge-natured element named in `requiresDefined` was nonetheless
dropped when `styleTexture.mode` was `none`: the build verified it as `defined`,
succeeded, and shipped a context without it. That is a behaviour correction, not
a clarification, and it changes `artifactHash` for targets that were previously
producing an incomplete context.

**Four build failures now have four codes.** `OBDS-BUILD-REQUIRED-NOT-FOUND`,
`-OUT-OF-SCOPE`, `-EXPIRED` and `-NOT-DEFINED`. Before 1.1 all four printed
`actualState: not_applicable` and an operator could not tell "never curated"
from "mis-scoped target" from "expired fact", though each needs a different
response. Section 13.1a is the registry.

**`obds:whitespace-v1@1.0.0` is defined.** It was stamped into every artefact
and specified nowhere. Its separator set is the Unicode `White_Space` property
plus U+001C, U+001D, U+001E and U+001F; those four are not `White_Space` and
specifying the property alone would have silently changed token counts.

**Foundation Validator Registry v1, section 11.5a.** Section 26.1 required
executing every declared `validatorRef` and the specification never defined the
namespace, a registry, resolution or an input contract, so no independent
implementer could satisfy it. The registry is closed and has one entry,
`obds:validator:colour-consistency-v1`, whose rule section 12.1 already stated
normatively. Section 26.1 is scoped to registry validators.

**`classification` is defined**, minimally: an optional opaque identifier string
with no OBDS-assigned meaning, no vocabulary and no policy. Sections 13.6, 27.2
and 29 referenced it normatively and nothing defined it.

**Editorial.** The section 12.1 colour example now validates against the
published `colour.schema.json`, which it did not. Section 11.8 states that
DECISIONS is a record kind and not an element `family`. Section 14.4 gains the
compiler-identity rule beside the tokenizer rule.

**Contract surface.** OBDS 1.1 publishes exactly one new contract,
`schemas/1.1.0/compiled-context.schema.json`. The 21 schemas and 6 value schemas
of the 1.0.0 surface are byte-identical to 1.0.0 and untouched. A 1.1
implementation reads 1.0.0 manifests and produces 1.1.0 compiled contexts.

The claim that all public contracts are byte-identical since 1.0.0 is retired
and replaced by: the OBDS 1.0.0 contract surface remains frozen and
byte-identical across 1.0.0 through 1.0.4, and OBDS 1.1 adds one versioned
contract beside it and changes none of them.

**Conformance.** 123 cases pass, 0 fail, 0 skip. Foundation grew from 27 to 43
with the 1.1 normative cases. The official declared Foundation conformance suite
remains 15 of 15 and is still not aggregated into that total.

## 1.0.4

**Hygiene release. No normative contract change.**

An external research pass on 1.0.3 found two things that a sceptical evaluator
reaches within minutes, and both were about the material around the
specification rather than the specification itself. 1.0.4 closes exactly those
two and nothing else.

**The published conformance result now satisfies section 26 in its own right.**
Section 26 lets an implementation claim conformance only when the result
identifies implementation name and version, suite hash, profile and the passed
and failed counts, and states that no required case was skipped or changed.
`OBDS-1.0.3-TEST-RESULT.json` published the counts and none of the rest, and
the missing identifiers appeared in no other release artefact either. So the
project's own release did not meet the rule it places on every other
implementer. `OBDS-1.0.4-TEST-RESULT.json` now carries:

- `implementation`, with name, version, language and repository;
- `obdsVersion`, the exact version the claim is made for;
- `suiteHash`, a stable identity for the conformance suite that produced the
  result. It covers the suite runner, the seven suite directories and their
  fixtures, and deliberately excludes `reference/foundation/src/`, which is the
  implementation under test and is identified separately;
- `suiteFileCount`;
- `conformanceProfiles`, naming only the profiles this release can defend:
  `obds-foundation` on the declared suite that names it, and `compiled-runtime`
  with a named executed case for every requirement section 26.2 lists. No
  profile is claimed for Context Delivery, Context Assembly, Visual Operations
  or Composition, because those suites exercise modules other than the named
  reference compiler;
- `executedSuites`, reporting every suite the release ran as coverage only,
  with no conformance claim attached;
- `requiredCasesSkippedOrChanged: false`, section 26 clause 4;
- `claimScope`, stating plainly that this is a suite result and not an
  independent certification.

`release-schemas/release-test-result.schema.json` makes every one of these
required, and `reference/release-gate.py` checks them, recomputes the suite
hash from the suite on disk and verifies that the declared profiles account for
every suite with the right case counts. The result cannot quietly fall short of
section 26 again.

**The public material no longer implies that fail-closed is Foundation
behaviour.** The README stated that Foundation is the minimum and nothing
beyond it is mandatory, placed Compiled Runtime in the optional tier, and then
demonstrated `requiresDefined`, the failed target and the absent Compiled Brand
Context under the heading "Foundation minimal". Every mechanism in that
sequence is section 26.2, not 26.1. Section 4.2 of the specification was always
correct; the surrounding material was not.

Corrected in `README.md`, `examples/README.md`, the website and the release
documents:

- Foundation, section 26.1, governs Brand Truth: Brand Elements, the four Brand
  States, semantic subjects, scope, validity, value contracts, reference
  resolution, approved snapshots and canonical hashes;
- Compiled Runtime, section 26.2, adds Build Plans, `requiresDefined`, explicit
  context selection, the rule that a failed target produces no artefact,
  reproducible artefact hashes and Runtime Decision Records;
- both shipped examples carry a Foundation manifest and exercise Compiled
  Runtime. The directory keeps the name `foundation-minimal` because it holds
  the smallest manifest, not because `build` is a Foundation operation.

The fail-closed guarantee itself is unchanged and still mechanically tested: a
failed target writes no artefact, and the instrumented model records zero
calls. Only the capability label was wrong.

**The official Foundation conformance suite was failing, and nothing ran it.**
Found while grounding the profile claim above. `reference/foundation/conformance-suite.yaml`
declares `profile: foundation` and is the only artefact in the package that
names a section 26 profile. It had one failing case, `canonical-hashes`, and the
same failure reproduces from the published 1.0.3 archive. Nothing in the release
path executed it: `run_all.py` runs seven pytest directories and never invokes
`obds conformance`, and the fixture it uses is referenced from nowhere else.

The cause was stale fixture data, not the canonicaliser. Both documents in
`fixtures/canonical-hash-vectors.json` predated the 1.0.0 contract shape: the
manifest was missing `profiles` and `valueContracts`, the artefact was missing
`artifactHash`, `availableElementIds`, `elementRecords` and `contextAssembly`.
Neither would validate against the published schemas, so their stored expected
hashes could not match.

The fixture is now derived from the published `examples/simple` documents in
their current shape. Its expected manifest hash is independently pinned in two
other places the 107-case run already verifies, `approval.contentHash` in the
manifest and `manifestRef.contentHash` in the build plan, so the vector is
cross-checked rather than self-confirming. Its expected artefact hash is the
`artifactHash` the compiler stamps, which `artefact_hash()` excludes from its
own input, so the vector asserts the stamp is self-consistent.

The suite now passes 15 of 15. Three things stop it being omitted again:
`tools/build-release.py` executes it and publishes
`OBDS-1.0.4-FOUNDATION-CONFORMANCE.json`; `reference/release-gate.py`
re-executes it directly and compares the fresh result against the published one
case by case; and the gate's own suite hash covers the fixtures, which the
declarative suite hash does not.

**The two results are not added together.** Fourteen of the fifteen declared
cases exercise the same examples and fixtures as the pytest suites, through the
`obds conformance` harness instead of pytest, so aggregating them would
double-count the same coverage. The 107 stays 107 and the Foundation result is
published separately with its own profile, counts and suite hash. The one
non-duplicated case is `canonical-hashes`.

Unchanged in 1.0.4:

- the normative specification text, apart from its version and filename;
- all 27 public contracts, byte-identical to 1.0.0, 1.0.1, 1.0.2 and 1.0.3;
- `schemaVersion`, which stays `1.0.0`;
- the four Brand States, the capability set and every runtime semantic;
- the 107-case suite and its per-suite counts;
- `spec/1.0.0/`, `spec/1.0.1/`, `spec/1.0.2/` and `spec/1.0.3/`.

## 1.0.3

**Documentation, packaging and developer-experience release. No normative contract change.**

1.0.2 shipped a correct implementation with incorrect prose. The conformance
suite ran 107 cases with 27 in foundation, and several documents kept describing
the 105-case result of 1.0.1. Two documented commands could not be executed at
all. 1.0.3 fixes the documentation and the packaging around an unchanged
contract, and makes the repository itself runnable.

Changed in 1.0.3:

- the reference implementation and the conformance suite are now part of the
  public repository. A clone can install the dependencies, run both examples,
  run all seven suites and run the release gate with no download step;
- the repository root is the package root. The suite and the release gate
  resolve the public schemas in either layout, `schemas/1.0.0/` as published on
  the web or flat `schemas/` as shipped in the release archive, and behave
  identically in both;
- the release gate no longer treats generated local caches as package junk.
  `__pycache__`, `.pytest_cache`, `*.pyc` and a local virtualenv are what
  running the suite produces, so `run_all.py` followed by `release-gate.py`
  now succeeds with no manual cleanup. Shipped junk still fails the gate:
  `.DS_Store`, `Thumbs.db`, editor backups, `__MACOSX`, and any cache file
  listed in `PACKAGE-MANIFEST.json`;
- the release gate judges the package rather than the whole working tree, and
  now verifies every file in `PACKAGE-MANIFEST.json` against its recorded
  sha256 and byte count;
- `examples/README.md` documented `obds build --manifest X --plan Y`, which the
  CLI has never accepted. The correct form is positional,
  `obds build <manifest> <plan> --out <dir>`, and both examples are now
  documented with the exit codes they actually produce;
- `tools/docs-smoke-test.py` executes every command in `README.md`,
  `CONTRIBUTING.md` and `examples/README.md` against the released package and
  fails if a documented command drifts from the CLI or a documented count
  drifts from the release metadata;
- `tools/build-release.py` builds `PACKAGE-MANIFEST.json` and the release
  archive from one file list, so the manifest cannot fall behind the package.

Corrections to statements published in 1.0.2. The 1.0.2 section below is
reproduced as published and is not rewritten; these are the statements it got
wrong, corrected here:

- `OBDS-1.0.2-TEST-REQUIREMENTS.md` was titled `OBDS 1.0.0 Test and Runtime
  Requirements` and declared the run as 105/105 in its introduction, its
  expected output, its release-gate section and its suite-composition table,
  where foundation was listed as 25. The 1.0.2 run was 107 with 27 in
  foundation, as `OBDS-1.0.2-TEST-OUTPUT.txt` and
  `OBDS-1.0.2-TEST-RESULT.json` both record;
- the 1.0.2 changelog lists "the 105-case conformance result" among the things
  1.0.2 did not change. 1.0.2 did change it, from 105 to 107, and its own test
  result says so;
- `README.md` and `CONTRIBUTING.md` printed `# 105 passed` and documented
  running the suite before the release gate, with the virtualenv inside the
  package root. In that order the gate failed on the caches the suite had just
  written and on the virtualenv itself;
- `OBDS-1.0.2-IMPLEMENTER-QUICKSTART.md` was titled `OBDS 1.0.0 Implementer
  Quickstart`.

Not changed in 1.0.3:

- every normative contract;
- all 21 public schemas and all 6 public value schemas, byte for byte, identical
  to 1.0.0, 1.0.1 and 1.0.2;
- every schema `$id`, which continues to resolve under `/schemas/1.0.0/` and
  `/value-schemas/1.0.0/`;
- `schemaVersion`, which remains `1.0.0` because the schema contract did not move;
- the capability registry, the Brand States, precedence, scope resolution,
  conflict handling, `asOf`, the assembled model input slots and the fail-closed
  behaviour;
- the licensing position established in 1.0.2;
- the conformance result: 107 passed, 0 failed, 0 skipped, with the same seven
  suite counts.

`spec/1.0.0/`, `spec/1.0.1/` and `spec/1.0.2/` remain published exactly as
released. None of them is rewritten.

## 1.0.2

**Licensing, packaging and documentation release. No normative contract change.**

1.0.1 replaced the CC BY 4.0 and Apache License 2.0 recommendation with a custom
model: free use for a listed set of purposes, and a separate written commercial
licence for everything else. Those licence documents were drafted but never
published, so the practical effect was that nobody could tell what they were
allowed to build. A specification that cannot be implemented commercially without
asking is not a standard.

1.0.2 replaces that model with two standard licences and publishes them.

Changed in 1.0.2:

- section 32.1 is rewritten. The specification and the documentation are licensed
  under **CC BY 4.0**. The schemas, the release metadata, the reference
  implementation, the conformance suite and the machine-readable examples are
  licensed under the **Apache License 2.0**;
- commercial implementation is permitted and requires no separate permission.
  There is no commercial licence to obtain, no evaluation period and no
  distinction between commercial and non-commercial users;
- the custom Free Use grant and the separate commercial licence requirement are
  removed. So is the draft certification programme as a gate on anything;
- section 32.1 states the modification rule explicitly: a modified specification
  or conformance suite must say it was modified, must not be presented as a
  published OBDS release, and must not reuse a published version identifier;
- the trademark position is separated from the copyright position. Truthful
  compatibility statements need no permission; project naming, logo use and any
  future certification claim are governed by the published trademark policy;
- the package now carries `LICENSE.md`, `LICENSES/CC-BY-4.0.txt`,
  `LICENSES/Apache-2.0.txt`, `NOTICE`, `TRADEMARKS.md`, `GOVERNANCE.md` and
  `CONTRIBUTING.md`. Neither standard licence text is modified;
- the package now carries `examples/`, with a minimal Foundation example and a
  fail-closed example in which required truth is unresolved, no Compiled Brand
  Context is produced and no model is called;
- the release gate additionally proves normative contract identity against 1.0.1,
  not only against 1.0.0.

Not changed in 1.0.2:

- every normative contract;
- all 21 public schemas and all 6 public value schemas, byte for byte, identical
  to both 1.0.0 and 1.0.1;
- every schema `$id`, which continues to resolve under `/schemas/1.0.0/` and
  `/value-schemas/1.0.0/`;
- `schemaVersion`, which remains `1.0.0` because the schema contract did not move;
- the capability registry, the Brand States, precedence, scope resolution,
  conflict handling, `asOf`, the assembled model input slots and the fail-closed
  behaviour;
- the reference implementation and the conformance suite, apart from renamed file
  references and the extended release gate;
- the 105-case conformance result.

`spec/1.0.0/` and `spec/1.0.1/` remain published exactly as released. Section 32
of the 1.0.0 document still carries its original recommendation and section 32.1
of the 1.0.1 document still carries the custom model. Neither is rewritten.

## 1.0.1

**Licensing clarification. No normative contract change.**

Section 32 previously recommended CC BY 4.0 for the specification and documentation and
Apache License 2.0 for schemas, fixtures and reference software. That recommendation did not
match the licensing model under which OBDS is actually published, and it could be read as a
grant of unrestricted commercial use.

Changed in 1.0.1:

- section 32 is renamed from "How the open project is governed" to "How the project is governed";
- OBDS is described as a publicly available, vendor-neutral specification rather than an open standard;
- "reference tooling is open where practical" becomes "reference tooling is published together with the specification";
- the CC BY 4.0 and Apache License 2.0 recommendation is removed;
- a new section 32.1 states the actual use and licensing model: free use for personal,
  educational, academic, non-profit, testing, evaluation and non-production proof-of-concept work,
  including internal evaluation by a commercial organisation; a separate commercial licence for
  paid client work, agency services, consulting, production use, managed services, commercial
  products, commercial redistribution and the sale of OBDS-based deliverables;
- section 32.1 records that the licensing covers the published materials only, not the underlying
  ideas, principles or methods, and that trademarks are reserved separately;
- section 33 and the release artefacts are renamed from 1.0.0 to 1.0.1.

Not changed in 1.0.1:

- every normative contract;
- all 21 public schemas and all 6 public value schemas, byte for byte;
- every schema `$id`, which continues to resolve under `/schemas/1.0.0/` and
  `/value-schemas/1.0.0/`;
- `schemaVersion`, which remains `1.0.0` because the schema contract did not move;
- the reference implementation and the conformance suite, apart from the renamed file
  references they read.

The release gate enforces this: it recomputes a fingerprint over all 27 public contracts and
fails if it differs from the frozen 1.0.0 surface.

OBDS 1.0.0 remains published exactly as released.

## The 1.0 decision

OBDS has one normative specification, one required Foundation and optional capabilities. The separate CORE specification is retired.

> **One specification. One Foundation. Optional capabilities.**

## Changed from 0.9.9

- `OBDS-CORE` is no longer a separate normative document.
- `CORE Check Registry v1` is renamed `Foundation Check Registry v1`.
- every 1.0 manifest declares `obds-foundation`.
- existing Context Delivery, Design Space and Visual Operations concepts remain part of the single specification.

## Pre-release history

The sections below record the pre-release hardening cycles that led to 1.0.0. They are history. The released contract is OBDS 1.0.0 stable.

### RC3 integrity and decision hardening

- Brand States now describe knowledge only: `defined`, `unknown`, `not_defined`, `not_applicable`.
- prohibition has one Brand Truth path: an explicit RULE with `obligation: prohibit`.
- Context Assembly now starts from the validated Compiled Brand Context and cannot reconstruct normal target truth from the manifest.
- Compiled Brand Context carries target-scoped `elementRecords`, `availableElementIds` and its Context Assembly policy.
- Model Input Packages require a non-null `compiledContextHash`.
- Runtime Decision Record schema and reference runtime now agree on `assembly_failed`, `assemblyHash` and `modelInputHash`.
- Value Contracts now bind `valueContractRef`, `shapeHash`, `schemaRef`, `schemaHash` and optional `validatorRef`.
- `stance / semantic-boundary` standardises qualitative IS / IS NOT guidance without turning guidance into compliance.
- the release suite includes enum synchronisation tests and a Golden end-to-end pipeline test.

## Release safety

- canonical hashes prove approved bytes;
- shape hashes prove machine structure;
- schema hashes pin the semantic contract;
- validators prove additional deterministic invariants; and
- PATCH releases are limited to source-reference or annotation corrections and cannot change Brand Truth or runtime applicability.

Breaking contract changes after publication require OBDS 2.0.

### RC4 deterministic execution hardening

- added explicit Build Plan `asOf`; compiler selection no longer depends on wall-clock time;
- Compiled Brand Context now carries `build.asOf` and a runtime-enforced validity window;
- added an effective element `subject` key for machine-decidable precedence and conflict resolution; omitted `subject` defaults to the element ID;
- implemented scope-specific winner selection and hard conflicts for incomparable maximal elements of one subject;
- pinned OBDS Canonical Number v1 and added Python-to-JavaScript interoperability vectors;
- strict JSON and YAML loaders reject duplicate keys; YAML uses 1.2 boolean semantics; scope scalars are strings only;
- failed `require_approval` checks now withhold output and route to `approval_required`;
- invalid `phase` / `appliesTo` combinations fail validation;
- every defined RULES element requires a rule value contract regardless of nature;
- unsupported declared Brand Profiles fail closed;
- PATCH eligibility now rejects value, scope, state, validity, subject, classification, contract, addition and removal changes;
- measurement `min > max` fails;
- Composition conformance requires every `neverOmit` role in geometry evidence;
- aligned rule obligation vocabulary on `permit`;
- added root dependency declaration and removed platform metadata from release packaging;
- added 16 adversarial regression tests covering the RC3 review findings.

### RC5 final hardening

- unified Canonical JSON code across Foundation, Context Delivery and Context Assembly and added byte-drift tests;
- aligned canonical number serialisation with ECMAScript / RFC 8785 thresholds;
- pinned object-key ordering to UTF-16 code units and added non-BMP vectors;
- rejected wider integers that cannot round-trip through IEEE-754 binary64;
- made unsupported tokenizer declarations fail closed;
- internalised the legacy `colour-hex` fixture schema;
- compacted Reasoning Chapter rendering and model-facing HARD_BOUNDARIES;
- removed duplicated exact chapter blocks from the model input projection;
- retained explicit empty Rule fields in canonical Brand Truth because exact value-shape contracts make omission structurally significant; empty plumbing is removed only from the runtime model projection;
- added canonicalisation, tokenizer and payload regression tests.

## 1.0.0 stable promotion

The final pre-release contract was promoted to stable 1.0.0 after the complete release gate passed. No normative changes were made during promotion.
