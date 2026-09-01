# OBDS 0.9.9 to 1.0.0 Migration

1. Set `schemaVersion` to `1.0.0`.
2. Use the single current specification document.
3. Remove dependencies on a separate `OBDS-CORE` document.
4. Keep `obds-foundation` in every manifest.
5. Treat optional profiles and runtime capabilities as parts of the same specification.
6. Rename references to `CORE Check Registry v1` to `Foundation Check Registry v1`.
7. Re-run the 1.0 schemas and every claimed capability suite.

## Brand State migration

OBDS 1.0 Brand States are:

- `defined`
- `unknown`
- `not_defined`
- `not_applicable`

A pre-1.0 `state: prohibited` element must become an explicit RULE with `obligation: prohibit`, exact scope, enforcement and validation mode. Do not silently map it to another knowledge state.

## Value Contract migration

Every defined FACT value declares `valueContractRef`. The referenced contract carries:

- `shapeHash`;
- `schemaRef`;
- `schemaHash`; and
- optional `validatorRef`.

Several contracts may exist for the same family and kind when approved shapes or contract versions differ. Recompute approval hashes after migration.

A pre-1.0 PATCH-style release that changed value shape or value contract must be reviewed as a compatibility event rather than carried forward automatically.

## Context Assembly migration

Compile targets before assembly. The Compiled Brand Context carries the target-scoped element records and Context Assembly policy. Normal assembly no longer scans the Brand Manifest. Manifest access is reserved for explicit `manifest_checked` no-hit resolution.

## Semantic Boundary migration

Qualitative prose may remain prose. Where a precise IS / IS NOT decision boundary materially improves review, use `family: stance`, `kind: semantic-boundary`, `nature: knowledge` and the standard semantic-boundary contract.

## Pre-publication hardening carried into 1.0.0

Before publishing 1.0:

1. add `asOf` to every Build Plan;
2. assign a shared element `subject` wherever multiple scoped elements are alternatives for the same decision; elements without an override relationship may omit it and default to their ID;
3. ensure scope values are strings;
4. validate governed JSON and YAML with duplicate-key rejection and YAML 1.2 boolean semantics;
5. replace rule obligation `allow` with `permit`;
6. ensure every defined RULES element resolves to a rule value contract;
7. confirm every declared Brand Profile is supported by the consuming implementation;
8. reclassify any PATCH containing value, subject, state, scope, validity, classification, addition or removal changes as MINOR or MAJOR as appropriate; and
9. regenerate approval, plan, compiled-context and derived-view hashes after migration.

## 1.1.6 to 2.0.0

**This is the only OBDS release so far that can invalidate a manifest you already
have.** Almost certainly it does not. Run the check at the end of this section
and you will know in a second.

No schema changed. No Brand State was added. No capability, profile or field was
added or removed. `schemaVersion` stays `1.0.0` for manifests and `1.1.0` for
compiled contexts. If your documents pass the check below **and contain no plain
scalar written in exponent notation**, an OBDS 2.0 implementation reads them
exactly as 1.1.6 did, and every hash you have stays valid. Exponent notation is
the one change the check cannot report, because the document stays valid and
only its value moves; it has its own check below.

### What changed

Section 28 always made JSON the canonical interchange format and allowed YAML
where it produces an equivalent JSON document. It never said how a YAML plain
scalar becomes a JSON value. Section 28.1 now says, and that pins two things
that were previously left to the parser.

**One class of form changes meaning: exponent notation.** An unquoted scalar
written with an `e` or `E` exponent — `1e3`, `1E3`, `2E-2`, `1.5e3`, `-2e-2`,
`9e9` — was the *string* under a YAML 1.1 reader and is the *number* under 2.0,
which is what the same characters have always meant read as JSON. The class is
every plain scalar matching the JSON number grammar with an exponent, except the
spellings a YAML 1.1 reader already read as a number, which are those carrying
both a decimal point and a signed exponent (`1.0e+3`, `1.23e-4`); those are
unchanged. This is the only change in the release that is silent: the document
stays valid and the value moves under it, so a hash computed over it moves too.

**The rejected forms.** Each is a form some YAML version reads as a value the
JSON grammar does not produce, so leaving it accepted meant a document whose
meaning depended on its reader. **Was** is what the OBDS 1.1.6 reference reader
did with it, which is not always what YAML 1.2 does; the two disagreeing is the
whole reason the form is rejected. Write the **Write instead** cell exactly: a
form that was a string must stay a string, or your `approval.contentHash` moves.

| Written in your YAML | Was, under 1.1.6 | Is now | Write instead |
|---|---|---|---|
| `017` | the number 15 | rejected | `15`, or `'017'` for the string |
| `017.5` | the number 17.5 | rejected | `17.5`, or `'017.5'` for the string |
| `017e3` | the string `"017e3"` | rejected | `'017e3'` |
| `+42` | the number 42 | rejected | `42` |
| `1.` | the number 1.0 | rejected | `1.0` |
| `1.e3` | the string `"1.e3"` | rejected | `'1.e3'` |
| `.5` | the number 0.5 | rejected | `0.5` |
| `1_000` | the number 1000 | rejected | `1000` |
| `1_000.0`, `1_0.5`, `.5_0`, `0.0_` | the numbers 1000.0, 10.5, 0.5, 0.0 | rejected | `1000.0`, `10.5`, `0.5`, `0.0` |
| `12:30` | the number 750 | rejected | `'12:30'` |
| `1_0:30`, `40_:3`, `4_:1:2` | the numbers 630, 2403, 14462 | rejected | quote them, or write the number you meant |
| `2026-09-01` | already rejected: a date object, which governed JSON has no type for | rejected, with a message that names it | `'2026-09-01'` |
| `2026-09-01 00:00:00 Z` | already rejected: a datetime object | rejected, with a message that names it | `'2026-09-01T00:00:00Z'` |
| `0x1f`, `0b1010` | the numbers 31, 10 | rejected | `31`, `10` |
| `0o17` | the string `"0o17"` | rejected | `'0o17'` |
| `~` | null | rejected | `null` |
| an empty value | null | rejected | `null` |
| a document nesting more than 100 collections deep, counting the outermost | read, up to whatever the reader's stack allowed | rejected | flatten it; the deepest document this release ships nests 10 |
| any exponent form: `1e3`, `1E3`, `2E-2`, `-1.5e3` | the string | **the number** | `'1e3'` for the string; nothing for the number |

Every row above except the last is loud: the document is rejected and the
message names the value. The last row is the only silent one in this release.

**A form carrying an exponent needs one more look before you rewrite it.** The
1.1.6 reader used the YAML 1.1 float grammar, which required the exponent to
carry a sign, so within a single row the 1.1.6 value flips with that sign:
`1.e3` was the string `"1.e3"` but `1.e+3` was the number `1000.0`; `.5e3` was a
string but `.5e+3` was `500.0`; `+1.5e3` was a string but `+1.5e+3` was `1500.0`;
`017e3` was a string but `017.5e+3` was `17500.0`. Quote the unsigned spellings
and write the plain number for the signed ones. Getting this backwards is the
one way to follow this table and still move a hash.

A raw U+0085, U+2028 or U+2029 is also rejected, because YAML 1.1 counts them as
line breaks and YAML 1.2 does not. Write them as an escape in a double-quoted
scalar; section 14.3b already escapes two of them, so they remain ordinary
governed content.

Explicit tags such as `!!str` and `!!int` are rejected, as is the merge key
`<<`. Anchors and aliases keep working: an alias expands to the same node in
every YAML version, so it was never ambiguous.

Nothing here applies to JSON. If you author in JSON, 2.0 reads your documents
exactly as 1.1.6 did.

### What to do

Two checks, because the release has two kinds of change and one command cannot
report both.

**1. The rejected forms, which are loud.** Validate every governed YAML document
you have, not only manifests: a Build Plan carries no self-hash and its target is
hashed verbatim into `governedResultHash`, so an ambiguous scalar there moves a
hash with nothing to compare against.

```bash
python -m obds_ref.cli validate path/to/manifest.yaml
```

If it validates, no rejected form is present. If it reports an ambiguous plain
scalar, the message names the value and the reason, and the table above says what
to write instead.

**2. Exponent notation, which is silent.** Nothing rejects it, so list the
occurrences and read them:

```bash
grep -rnE '(^|[^0-9A-Za-z_.+-])[-+]?[0-9]+(\.[0-9]*)?[eE][-+]?[0-9]+([^0-9A-Za-z_.]|$)' \
  path/to/governed/*.yaml
```

Every scalar in exponent notation is on a line it prints. The reverse does not
hold: it also prints lines where the pattern appears inside a comment
(`# see 1e3 below`), a URL or another string, because it matches text and not
YAML structure. Read the lines; under 2.0 every unquoted occurrence is a
number. If you meant the number, nothing changes. If you meant
the string, quote it. The pattern deliberately over-reports: it prints quoted
occurrences too, and the two spellings that were already numbers (`1.0e+3`,
`1.23e-4`). It matches the value wherever it sits on the line, so flow mappings
(`{a: 1e3}`), inline sequences (`[1e3, 2e4]`) and a scalar with a trailing
comment are all reported. A list you read is safer than a verdict you trust.

Only after both checks pass does the promise at the top of this section hold.

If a value did change, quote it or rewrite it, then recompute
`approval.contentHash` and re-approve the manifest, exactly as for any other
change to governed content. A changed hash means the governed truth changed, and
that is a decision a named human makes, not a migration script.

The reference implementation ships 29 governed YAML documents. All 29 were
checked against both readings, and against the exponent pattern above, and none
of them changed.

## 1.1.5 to 1.1.6

No schema changed and no manifest change is required. Four observable changes,
each of which only affects a manifest that was already outside the
specification.

**One new normative rule, section 14.3c.** A governed string or object key must
consist only of code points assigned in Unicode 15.1.0, or Unicode
noncharacters, and must contain no surrogate. A document containing a code point
assigned only in a later Unicode version is now rejected. An implementation must
also run on a Unicode database at or after 15.1.0: the reference compiler needs
CPython 3.13 and the JavaScript oracle needs Node 21. This is what makes NFC, and therefore every
hash derived from it, identical on every conforming runtime. If you author in a
script added after Unicode 15.1.0, you cannot govern it under OBDS 1.1.6; raise
the pinned version in a later MINOR release rather than diverging locally. The
pinned assignment set ships with the release as
`reference/foundation/src/obds_ref/unicode-pin-15.1.0.json`.

**Element ids and semantic subjects are compared after NFC, section 8.0a.** Two
canonically equivalent ids are now one identity, so a manifest carrying both is
rejected as a duplicate, and an NFD and an NFC spelling of one subject now
resolve as one subject. `approval.contentHash` is unaffected, because it was
always computed over canonical, and therefore NFC, bytes. If your manifest ids
come from macOS paths or a DAM export they may be NFD; nothing needs to change,
because the comparison is now on the canonical form either way.

**`elementValueRef` resolves through the governed selection, section 11.5.** A
check that binds another element's value now fails the target when that element
has expired, is out of scope, lost its subject, sits in an unresolved conflict
or is not `defined`, with the section 13.1a cause that applies. Previously the
reference resolved it against the raw approved snapshot on `state` alone, so a
withdrawn value could still be compiled into an active blocking check. A target
that relied on that behaviour was enforcing text that was not governed truth.

**Conflict relevance counts more RULES, section 10.2a.** An unresolved subject
conflict is decision-relevant when one of the competing elements is a `defined`
RULE that would add requirements or compiled checks if it won, and when the
conflicted element is named in the target's `contextAssembly.eligibleGuidanceIds`,
not only when its enforcement is `block` or `require_approval`. A build that
succeeded while two competing non-blocking RULES cancelled a declared
dependency now fails, which is the outcome the same manifest already produced
once the conflict was resolved.

## 1.1.4 to 1.1.5

No schema changed and no manifest change is required.

The one observable change is that a manifest whose applicable RULE declares a
`requiresDefinedRefs` dependency that does not resolve to `defined` now fails
manifest validation or the target build. Such a manifest was already outside the
specification; the reference compiler simply did not say so.

## 1.1.3 to 1.1.4

No migration work. No schema changed and no manifest change is required.

Scope values are now normalised to Unicode NFC when they are compared, as section
9 already required. A consumer can observe a behavioural change only if a manifest
currently relies on an NFD scope value failing to match its canonically equivalent
NFC value. That manifest was already broken; 1.1.4 makes the required comparison.

## 1.0.4 to 1.1

No migration work for a manifest. Manifests stay at `schemaVersion: 1.0.0` and no
element contract changed.

For an implementation, four things:

1. **Emit `governedResultHash`** per section 14.3a and declare
   `schemaVersion: 1.1.0` on the Compiled Brand Context. Validate it against
   `schemas/1.1.0/compiled-context.schema.json`. The 1.0.0 contract is unchanged
   and 1.0 artefacts remain valid 1.0 artefacts.
2. **Check your precedence reading.** Section 10.2 now states the rule as strict
   subset inclusion on matched targets. If you read the old wording as
   "restricts more dimensions" you resolved some manifests as hard conflicts that
   1.1 resolves to a winner. Run `precedence-vectors` before assuming you agree.
3. **Check that required truth reaches your artefact.** If your context
   selection could drop an element named in `requiresDefined`, it was producing
   an incomplete context. Section 13.2 now says so explicitly.
4. **Adopt the four required-truth error codes** from section 13.1a if you
   report build failures.

`artifactHash` for an unchanged manifest and plan will move, because the artefact
gained a field and a schema version. That is expected across a version change.
Section 16.1 approvals bind the artefacts they were issued against; a rebuild
under 1.1 is a new artefact and needs its own approval.

## 1.0.3 to 1.0.4

No migration work. 1.0.4 changes release metadata and documentation only.

- No schema, no `$id`, no `schemaVersion` and no capability semantic changed.
- The public schema surface is byte-identical to 1.0.0, 1.0.1, 1.0.2 and 1.0.3.
- An implementation that conforms to 1.0.3 conforms to 1.0.4 with no work.

Two things are worth knowing.

First, if you publish your own conformance result, section 26 requires it to
identify the implementation by name and version, the suite by hash, the profile
and the counts, and to state that no required case was skipped or changed.
`OBDS-1.0.4-TEST-RESULT.json` is now a worked example of a result that meets
that rule, and `release-schemas/release-test-result.schema.json` is the shape
to validate against. A 1.0.3-era result that carried only counts should be
reissued.

Second, if your documentation repeated the OBDS pitch, check the same thing
1.0.4 corrected. `requiresDefined`, a failed target producing no Compiled Brand
Context and therefore no model call is Compiled Runtime, section 26.2. It is
not Foundation-only behaviour. Foundation, section 26.1, governs Brand Truth.
Nothing about the guarantee changed; only its label.

## 1.0.2 to 1.0.3

No migration work. 1.0.3 changes documentation, packaging and developer
experience only.

- No schema, no `$id`, no `schemaVersion` and no capability semantic changed.
- The public schema surface is byte-identical to 1.0.0, 1.0.1 and 1.0.2.
- An implementation that conforms to 1.0.2 conforms to 1.0.3 with no work.
- The only thing an implementer has to know is that documented commands have
  changed: `obds build` takes the manifest and the plan positionally, and the
  release gate now runs cleanly after the conformance suite.

## 1.0.1 to 1.0.2

No migration work. 1.0.2 changes licensing, packaging and documentation only.

- No manifest changes. No schema changes. No `$id` changes.
- `schemaVersion` stays `1.0.0`.
- An implementation that conforms to 1.0.1 conforms to 1.0.2 with no work.
- What changed for you is permission, not code: the specification and the
  documentation are now CC BY 4.0, and the schemas, the reference implementation,
  the conformance suite and the examples are now Apache License 2.0. Commercial
  implementation needs no separate permission.
- If you were waiting on a commercial licence before shipping, you are not
  waiting on anything any more.
