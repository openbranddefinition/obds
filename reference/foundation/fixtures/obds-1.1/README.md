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
| `precedence-vectors.json` | the subset precedence rule, including both conflict outcomes |
| `absent-dimension.json` | an element restricting a dimension the target does not declare is not applicable |
| `scope-nfc.json` | scope values compare as NFC-normalised sets |
| `whitespace-v1.json` | the exact separator set, including U+001C to U+001F |
| `build-error-codes.json` | one vector per build-failure code |
| `context-id.json` | the context identifier construction rule |
