# Proposed optional Task Facts normative contract — candidate-v1

Status: PROPOSED, not an approved OBDS contract or release. This explicitly modified adaptation promotes frozen experimental v0.2 sections 2–7 to proposed normative text. All definitions, algorithms and outcomes below are requirements: a claimant MUST implement them. Examples and statements about research/hypothetical hosts are informative. MUST, MUST NOT, SHOULD and MAY express requirement, prohibition, recommendation with justified exceptions, and permission respectively.

## 1. Scope and authority

This optional evaluator MUST NOT change OBDS Foundation/Core, Brand States, Scope, precedence, Value Contracts or existing governed hashes. Task-fact presence is not proof of truth; verification and provenance remain separate. Stable Brand Scope is established outside this evaluator. Local fact identifiers are application vocabulary, not a new brand ontology.

The included schemas/task-facts.schema.json is normative for structure and required/closed members. Prose defines additional transport, semantics, ordering, hashing and decisions. Schema-only validation is insufficient. Any document conflict requires correction before adoption, not implementer discretion. The schema is an unchanged copy; its experimental URN describes its provenance, not official registration. Snapshot contractVersion 0.1 is a payload format identifier, separate from proposed capability designation Task Facts 1.0 and from any OBDS release number. No valid snapshot may be rewritten merely to rename a version.

## 2. Transport and schema

The root of `schemas/task-facts.schema.json` validates a snapshot. Local definitions separate `routingFamily`, `routingCase`, and `routingCondition` from typed `snapshot`, `verificationContext`, and `condition`. `family` and `case` validate shallow wrapper structure only; neither recursively validates typed payloads. The experimental schema URN is version 0.2; the payload version remains 0.1.

A family file has `family` and an ordered nonempty `cases` array. A case has `id`, `snapshot`, `verificationContext` and an ordered nonempty `conditions` array. Each condition has an `id`. Routing IDs use the schema's `identifier` constraints and are compared as decoded strings, without normalization. Case IDs are unique per family; condition IDs are unique per case. Identical IDs in different cases are allowed; files are separate family routing units.

Routing validation requires only valid family/case/condition identities, the nonempty arrays, and a present canonicalisable snapshot value. The snapshot may be null, scalar, array or malformed object: its typed shape is not a routing constraint. Missing snapshot or undecodable/invalid IDs prevent routing. A missing or malformed verification context does not prevent routing. Additional keys do not prevent routing; closed wrapper and typed schemas reject them at the bound validation layer. Routing schemas deliberately permit payload keys and are not complete validity schemas.

Before emitting any decisions, validate the entire family's routing skeleton, then case-ID uniqueness, then condition-ID uniqueness in case order. Any routing shape failure yields exactly one unbound `INVALID / SCHEMA_INVALID` for that family. Duplicate case IDs anywhere within the family, or duplicate condition IDs in any one case, yield exactly one unbound `INVALID / DUPLICATE_ID` for the entire family, suppressing all its decisions, including otherwise unique siblings. No partial family output is permitted. Routing shape failure takes precedence over duplicate-ID detection.

Every bound record has exactly `family`, `caseId`, `conditionId`, `snapshotHash`, `outcome`, and `reason`. Every unbound record has exactly those six fields with all three routing fields and `snapshotHash` null. No guessed or partial identities are emitted. Expected records may additionally carry `basis`; the evaluator never reads expectations. The single-condition API omits family/case fields; invalid condition identity or non-TFJ arguments cannot bind its hash.

All typed objects and wrappers remain closed. Schema validation is necessary but not sufficient: cross-field types, references, temporal syntax, canonical input restrictions and operand compatibility require semantic validation. A schema-only validator must not claim contract conformance.

## 3. Snapshot, identity and completeness

The complete snapshot consists of:

- `contractVersion`: exactly `0.1`. This is the frozen snapshot payload version, not the package revision. `"0.2"` remains a wrong payload version and yields a bound `SCHEMA_INVALID`; rewriting valid snapshots would change identity and is forbidden.
- `task`: an ID, action, SHA-256 artifact digest and SHA-256 model-input/package digest. Digests identify bytes of the exact inspected artifact and input package, excluding this sidecar; neither is computed from an object containing this snapshot's own hash.
- `declarations`: a map from local fact key to its declared type. These keys are application vocabulary, not standardized brand fields.
- `facts`: the present fact records. An omitted declared fact is missing; it is never an empty set.
- `evidence`: all provenance/verification records for those facts.

The snapshot hash covers **all five fields**, every unused fact, each declaration, evidence record, state, value and reference. No selective hashing or omission of unresolved facts is allowed. Omitted and explicit records therefore have different identities. Hashing binds the supplied snapshot to one task and exact artifact/input digests; it does not establish that the inventory actually lists every claim or asset. The verifier must attest inventory completeness for a `known` set or an `empty` record against that artifact. Known means a complete recorded value for that fact, not a partial observation. An incomplete inventory must be `unknown`.

Reuse after a change to task, action, artifact, input package or facts requires a new snapshot hash. A consumer must compare the returned snapshot hash to its stored snapshot and use the matching task/artifact/input package. The separate verifier context pins `snapshotHash` as well as task and artifact identities, preventing replay after changes to declarations, action or unused facts. A future adapter must also retain the exact condition document alongside the decision: condition IDs alone are not immutable rule versions. Condition and verifier-context changes can change decisions without changing the task-fact snapshot hash; this is deliberate separation of identities.

### TFJ-0.1 canonical bytes

This is a small standalone JSON profile, **not OBDS canonicalization or an RFC 8785 claim**:

1. Accept null, booleans, integers from −9007199254740991 through 9007199254740991, Unicode scalar strings, arrays and string-keyed objects. Reject floating-point tokens (even `1.0`), non-finite numbers, duplicate object keys and unpaired surrogates. JSON integer `-0` normalizes to `0`.
2. Sort object keys lexicographically by Unicode scalar value. No Unicode normalization. Preserve array order, including set serialization and evidence references; set order does not affect applicability but **does affect snapshot identity**. No sorting, deduplication or normalization of caller data is hidden in hashing.
3. Emit no whitespace or BOM, UTF-8, lowercase `true`, `false`, `null`, and base-10 integers without leading zeros. Escape quote and backslash; use `\b`, `\t`, `\n`, `\f`, `\r` for their controls and lowercase `\u00xx` for the other U+0000–U+001F controls. Emit other scalar characters literally, including slash and non-ASCII characters. No trailing newline.
4. `snapshotHash = "sha256:" + lowercase_hex(SHA256(canonical_bytes(snapshot)))`.

The same function hashes an evidence object and a fact assertion. A fact assertion is the entire fact object with only `evidenceRefs` removed. File digests in the manifest instead hash raw file bytes, including final newlines.

Once routing succeeds, canonicalisable malformed snapshots MUST receive their canonical hash and bound `INVALID` decisions. Transport, TFJ or routing failure instead yields one unbound record with null hash, even if some nested snapshot could independently be hashed. All frozen invalid type fixtures are canonicalisable and retain their real hashes.

## 4. Types and knowledge states

| Type | Known value |
| --- | --- |
| `string` | Nonempty Unicode scalar string; exact, case-sensitive comparison |
| `boolean` | JSON true or false, never strings or integers |
| `integer` | TFJ safe integer; booleans are not integers |
| `string-set` | Nonempty array of distinct nonempty strings |
| `association-set` | Nonempty array of distinct two-string arrays `[source, target]` |
| `date` | Valid Gregorian `YYYY-MM-DD`, years 0001–9999 |
| `date-time` | Valid Gregorian `YYYY-MM-DDTHH:MM:SSZ` or with `±HH:MM`; whole seconds, offsets at most ±14:00; no leap seconds or `-00:00` |

There are four explicit fact states. They are **not OBDS Brand States**:

| Representation | Meaning | Presence / absence |
| --- | --- | --- |
| Declared key omitted from `facts` | Missing observation | Both UNKNOWN / `FACT_MISSING` |
| `state: empty`, no value | Verified absence, e.g. inspected empty claim inventory or no scalar assignment | False / true |
| `state: known`, typed value | Complete observed value | True / false, even for `false` or `0` |
| `state: unknown`, no value | Observation explicitly unresolved | Both UNKNOWN / `FACT_UNKNOWN` |
| `state: contradictory`, no value | Curator/verifier reports incompatible evidence | Both CONTRADICTORY / `FACT_CONTRADICTORY` |

Every explicit record has nonempty unique `evidenceRefs`; contradictory requires at least two references. Null is not shorthand for unknown. Empty strings and known empty arrays are invalid: use `state: empty`. Missing records resolve their provenance status to “no observation”; they cannot acquire verification by default. Unknown and empty records require provenance just as known records do.

Associations are a **limited partial function within one declared fact**. Two different targets for the same source are `CONTRADICTORY / ASSOCIATION_CONFLICT` when that fact is consulted; duplicate identical pairs are invalid. This makes wrong claim→product and asset→rights cross-attribution testable without joins. It does not assert that a real claim can only concern one product or a campaign one placement. For these fixtures each relation represents one reviewed placement/use context; use an occurrence ID or a separate fact outside this compact fixture vocabulary if the source has several legitimate associations. General relations, joins and multi-target modeling are deferred.

The evaluator only detects this declared relation conflict and explicit contradictory states. It does not inspect renderings, detect undeclared semantic contradictions, derive portrait presence from images, or reconcile contradictory evidence automatically. Those findings must arrive as reviewed facts.

## 5. Provenance and verification boundary

Each evidence record carries `supplier`, `sourceRef`, `method`, `verifier`, `status`, `fact`, `assertionHash`, `taskId`, `artifactHash` and `inputPackageHash`. Every reference must resolve to evidence for the same fact. Every evidence record must be referenced by its fact. Dangling, orphaned or cross-fact references are invalid.

The independently supplied `verificationContext` has the exact `snapshotHash`, matching task/artifact/input identities and `acceptedEvidence`, a map of evidence ID to the digest of the exact evidence record accepted by the verifier. The reference evaluator does not fetch evidence or authenticate anyone. A production host, outside this experiment, would authenticate a verifier, check source/authority and artifact completeness, and construct this context. Caller control of this context defeats the boundary. Fixture files intentionally include a **synthetic trusted context** to make tests reproducible; that does not constitute real-world verification.

To use a fact, the complete snapshot hash must match the verifier context. Every referenced record must have `status: verified`, its digest must match the verifier's accepted map, its assertion digest must match the fact with references removed, and its task/artifact/input identities must match both snapshot and context. Failure yields `UNKNOWN / EVIDENCE_UNVERIFIED`, including on an empty or contradictory record. A mere `verified` label without an accepted digest is insufficient. Asserted facts remain unresolved. Changing the payload after attestation, or replaying it against another task/artifact/input package, cannot silently retain verification.

For an explicit contradiction, the references identify reviewed conflict evidence; the evaluator does not prove the referenced documents logically incompatible. No cryptographic signature protocol, automatic legal truth checking, semantic detection or workflow engine is specified. An asset hash identifies bytes, not entitlement. An accepted fact is usable under this declared verification context; its truth is not guaranteed by hashing.

## 6. Conditions and decision semantics

A condition has `id`, nonempty `all` (a flat conjunction), and `requiresDefined` (possibly empty). Each atom names one declared `fact` and one operation:

- `present` or `absent`: no operand; observes known/empty status, not mere key existence.
- `equals`: one scalar operand compatible with the declared scalar type; sets cannot use equality.
- `contains`: one string for `string-set`, or one exact `[source, target]` pair for `association-set`.

There is no OR, general NOT, nested expression, wildcard, regex, arbitrary function, inferred default or hidden brand rule. Absence is the single explicit absence predicate. All atoms are evaluated independently after validation. Duplicate identical atoms are invalid.

### Mandatory validation layers and error binding

Apply these layers in order, stopping at the first applicable error:

1. **Strict JSON transport parse** of the complete UTF-8 document. Reject malformed syntax, trailing content, BOM, duplicate decoded object keys and non-JSON constants (`NaN`, `Infinity`, `-Infinity`) with `JSON_PARSE_ERROR`. Finish syntax validation before TFJ validation. File access failure is `INPUT_IO_ERROR`.
2. **TFJ validation** of the complete decoded document, including metadata, conditions and verification contexts. Valid JSON float/exponent tokens (including `1.0`, `1e0`, `-0.0`), unsafe integers and unpaired Unicode surrogates yield `NON_CANONICAL_INPUT`. Parsers must preserve number-token category and integer precision for this check. Raw integer `-0` canonicalises as integer zero. The TFJ canonical byte algorithm is unchanged.
3. **Routing validation**, then uniqueness, exactly as section 2. Layers 1–3 yield one unbound record for the input file and no bound decisions from that file.
4. **Bound validation** for each condition in case/condition array order. Compute the canonical snapshot hash before typed validation. Validate the shallow family wrapper, shallow current-case wrapper, snapshot structural schema, undeclared snapshot fact keys, known fact values in sorted fact-key order, evidence-reference integrity, verification-context structure, condition structure, then operand/declaration checks in atom order. Structural schema failures yield `INVALID / SCHEMA_INVALID` and retain all routing fields and the hash. Existing value-level errors retain `TYPE_MISMATCH`, `UNDECLARED_FACT`, `EVIDENCE_REFERENCE`, and `OPERATOR_TYPE`; these are not reclassified as structural errors. A malformed snapshot or context invalidates all conditions in its case; a malformed condition invalidates only its own decision. A malformed unused fact still invalidates its snapshot. A malformed family wrapper affects every routed decision; a malformed case wrapper affects its own case only.
5. **Applicability evaluation** only after that decision passes validation. An unused well-typed unknown or conflict does not poison an independent condition. INVALID is never converted into false.

In particular, duplicate identical atoms, empty `all`, missing `requiresDefined`, extra condition keys, unknown operators and an operand on `absent` are bound `SCHEMA_INVALID` for only that condition. Extra snapshot keys, wrong `contractVersion`, missing evidence fields and raw `"action": -0` are bound `SCHEMA_INVALID` for each condition sharing that snapshot. Their hashes cover the actual malformed snapshot, with integer -0 canonicalised to 0; do not repair the payload or regenerate verifier attestations.

Transport examples: `{"x": NaN}` → unbound `JSON_PARSE_ERROR`; `{"x": 1.0}` or `{"x": 9007199254740992}` → unbound `NON_CANONICAL_INPUT`; `[1.0, NaN]` → `JSON_PARSE_ERROR` (syntax wins); `{"x": "\ud800"}` → `NON_CANONICAL_INPUT` (JSON escape syntax is valid, Unicode scalar profile fails). A top-level `[]` is TFJ but fails routing with `SCHEMA_INVALID`. Raw `-0` alone is TFJ integer zero but fails family routing; `-0` in an otherwise routable snapshot text field reaches bound schema validation.

For each atom: missing → UNKNOWN; otherwise verification failure → UNKNOWN; otherwise explicit unknown/contradictory or relation conflict → its unresolved result; otherwise evaluate the predicate. Empty yields false for equality and membership. Dates and instants obey section 7.

Combine the atom results using this conservative precedence:

`CONTRADICTORY > UNKNOWN > DOES_NOT_APPLY > APPLIES`

Thus false AND unknown is UNKNOWN, and false AND contradictory is CONTRADICTORY. This avoids using an unrelated false value to hide unresolved consulted evidence. It is an explicit experimental choice, not a general Boolean algebra. All-true yields APPLIES. If multiple atom reasons have the winning outcome, select the lexicographically smallest reason code. The outcome and reason are invariant under reordering valid atoms.

| Outcome | Reason codes |
| --- | --- |
| APPLIES | `ALL_TRUE` |
| DOES_NOT_APPLY | `PREDICATE_FALSE` |
| UNKNOWN | `EVIDENCE_UNVERIFIED`, `FACT_MISSING`, `FACT_UNKNOWN`, `TIME_BASIS_UNRESOLVED` |
| CONTRADICTORY | `ASSOCIATION_CONFLICT`, `FACT_CONTRADICTORY` |
| INVALID | `SCHEMA_INVALID`, `UNDECLARED_FACT`, `TYPE_MISMATCH`, `EVIDENCE_REFERENCE`, `OPERATOR_TYPE`, `NON_CANONICAL_INPUT`, `JSON_PARSE_ERROR`, `DUPLICATE_ID`, `INPUT_IO_ERROR` |

The CLI emits `{"results": [...]}` for every invocation, including errors. Process each file independently in argument order; retain other files' results when one file fails. Exit 2 if any emitted record is INVALID, otherwise 0. `evaluate_family` raises an `Invalid` exception for layers 2–3; `evaluate_path` converts transport, TFJ, routing and I/O failures to the prescribed single unbound record. The API receives already decoded values, so strict transport classification is the loader's responsibility.

### Declared effects

`requiresDefined` declares dependencies selected when this condition APPLIES. Consumers MUST retain unresolved decisions and MUST NOT interpret UNKNOWN, CONTRADICTORY or INVALID as permission. DOES_NOT_APPLY selects no dependency for that condition. APPLIES is not approval, rights clearance, legal compliance or permission to publish. Synthetic experimental IDs do not resolve in an OBDS manifest. Integration guidance is informative and no production adapter conformance is established here.

## 7. Time without invented instants

Civil dates compare only as dates. Offset-bearing instants compare by their absolute instant, so `2026-10-01T00:00:00+02:00` equals `2026-09-30T22:00:00Z`. A valid date compared to a valid instant, in either direction, returns `UNKNOWN / TIME_BASIS_UNRESOLVED`. This is not a false comparison and does not assign midnight, UTC, the machine timezone or Europe/Vienna.

Timezone-less date-time strings and `-00:00` do not establish an instant and are invalid as known date-time values. Preserve the source civil date separately and use an unknown instant/window fact if the source cannot establish a zone. No IANA timezone database, DST conversion or interval predicate is included. The frozen research calls for ambiguity preservation, not a general temporal policy language.

The sensitive-boundary fixture includes a publication instant, a source `validThrough` civil date, unknown source timezone and unknown `publicationWithinWindow` fact. The evaluator cannot derive a deadline from these. The claim-window condition consequently remains UNKNOWN. A future known window-status fact must arrive with its own accepted evidence establishing the time basis; a caller boolean alone cannot settle it. The remaining temporal variants probe date/instant type boundaries and exact equality, not an unimplemented expiry calculator.


## 8. Additional complete semantic details from the frozen evaluator

All maps use own decoded keys: inherited/prototype members do not count as declarations, facts, evidence or acceptedEvidence. Structural uniqueness compares JSON types and values recursively: object member order irrelevant, arrays ordered, boolean distinct from integer. Identifier and hash strings satisfy the included schema. Text is a nonempty Unicode-scalar string. Empty declaration/fact/evidence/acceptedEvidence maps are allowed by the schema.

Bound validation first rejects undeclared present facts with UNDECLARED_FACT, then checks known values in Unicode-scalar-sorted fact-key order. Null, wrong types, duplicate members and invalid temporal values yield TYPE_MISMATCH. Evidence references must resolve to the same fact and every evidence record must be referenced by its fact; failure is EVIDENCE_REFERENCE. Digest, assertion or accepted-context mismatch yields EVIDENCE_UNVERIFIED during evaluation, not EVIDENCE_REFERENCE. Extra acceptedEvidence entries do not imply observations and are permitted.

After condition schema validation, process atoms in array order. An undeclared fact yields UNDECLARED_FACT; present/absent have no operand type check. contains on a scalar or equals on a set yields OPERATOR_TYPE. Otherwise contains requires one nonempty string or exact two-nonempty-string pair as declared, failing with TYPE_MISMATCH. Scalar equals requires a compatible value. For temporal declarations, either a valid date or valid instant operand passes validation; different temporal bases yield TIME_BASIS_UNRESOLVED only during evaluation. No type coercion is allowed.

Association conflicts affect the whole consulted known relation, even for present/absent, after verification and explicit-state checks. Unused well-typed conflicts do not affect independent conditions. Gregorian leap years are divisible by four except centuries not divisible by 400; instant equality uses exact whole seconds. Platform datetime ranges must not silently narrow the specified local years 0001–9999.

A decoder API MAY be offered, but the loader remains responsible for original token categories and duplicate keys. Such an API cannot prove transport conformance from already-decoded objects. The file-oriented six-field records are the normative conformance interface. An optional single-condition API omits family/case fields; no bound hash is permitted if condition identity or TFJ validity is unavailable.

No resource-size ceiling is standardized by the evidence. Operational limits outside the evaluator may be documented, but an unevaluated input must not be reported as a successful contract decision or APPLIES. Host operational failures do not add standardized reason codes.
