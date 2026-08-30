# OBDS 1.1 normative fixtures

Cross-language conformance vectors for the OBDS 1.1 additions. Every expected
value in this directory was derived twice, independently, and the two derivations
had to agree before the value was written:

1. by an OBDS Canonical JSON v1 implementation written from section 14.3 alone,
   which does not import the reference implementation; and
2. by the reference implementation.

They are then confirmed a third time by the independent TypeScript
implementation. A value produced by only one of the three is not a conformance
vector, it is a regression test of that one implementation. That distinction is
the direct lesson of the `canonical-hashes` defect, where a vector generated once
from the implementation under test drifted and went unnoticed for two releases.

| File | Proves |
|---|---|
| `governed-result-hash.json` | the section 14.3a payload and its hash for both published examples |
| `governed-result-invariance.json` | different prose, compiler identity and token counts, identical `governedResultHash`, different `artifactHash` |
| `governed-result-neutrality.json` | a section 27.2 governance-neutral PATCH leaves `governedResultHash` unchanged |
| `whitespace-v1.json` | the exact separator set, including U+001C to U+001F |
| `context-id.json` | the context identifier construction rule, now stated normatively in section 14 |
| `requires-defined-precedence.json` | section 13.1: `requiresDefined` is an element-ID requirement, and an override that wins the subject does not satisfy a requirement naming the element it displaced |

Six files, and this table lists exactly what the directory contains. OBDS 1.1.0
shipped a table naming nine, of which five existed: an independent implementer
looked for the four that were not there and reported it. The inventory is now
part of what the release gate checks.

Cross-language canonicalisation vectors, including CR and CRLF in both string
values and object keys, live beside the implementation that consumes them in
`reference/adversarial/canonical-vectors.json`.

Four fixtures named in the OBDS 1.1 design gate are **not yet published**:
`precedence-vectors.json`, `absent-dimension.json`, `scope-nfc.json` and
`build-error-codes.json`. The behaviours they would pin are covered by cases in
`reference/foundation/tests/test_obds_11.py`, but as tests of this
implementation rather than as cross-language vectors with independently derived
values. Promoting them is the next fixture work, and naming them here is
deliberate: an implementer should know what the package does not yet prove.
