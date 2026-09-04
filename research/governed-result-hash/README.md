# Proof 1 — Deterministic governed result

The strongest thing OBDS can currently demonstrate:

```text
same governed inputs
→ independent implementations
→ same governed decision, same result hash
```

and the mirror of it, which matters more in practice:

```text
same governed inputs that do not support the request
→ same refusal, same error code, no artefact
```

## Run it

From the repository root, against public 3.0.2 artefacts only:

```bash
PYTHONPATH=reference/foundation/src python research/governed-result-hash/verify.py
```

Node.js is required for the cross-language half. Without it the script reports a
SKIP and exits non-zero; it never reports a silent pass.

Current output:

```text
[PASS] cross-language canonicalisation, 59 vectors — 59 of 59 byte-identical
[PASS] published sha256 re-derived from those bytes, 59 vectors
[PASS] governed result hash is stable across two independent builds — sha256:5adbc8e7ddf1962a46b7a9aed614cab8a698098d620095d34ecdb59434c95d83
[PASS] governed refusal is stable across two independent builds — OBDS-BUILD-REQUIRED-EXPIRED, OBDS-BUILD-STYLE-SELECTION; no context artefact produced
```

## What each check uses

### Cross-language canonicalisation, 59 vectors

- vector document: [`reference/adversarial/canonical-vectors.json`](../../reference/adversarial/canonical-vectors.json)
- second implementation: [`reference/adversarial/canonical_js.mjs`](../../reference/adversarial/canonical_js.mjs) (Node.js)
- first implementation: `obds_ref.canonical` in [`reference/foundation/src/`](../../reference/foundation/src/obds_ref/canonical.py)
- specification: OBDS 3.0.2 sections 14.3, 14.3b, 14.3c, 28.1

Each vector carries `input`, `canonical`, `canonicalHex` and `sha256`. Because
the expected output travels with the input, the document is an oracle: an
implementation in any language validates itself against it without a second
implementation running beside it. `canonicalHex` is authoritative — it survives
transports that mangle U+2028, U+2029 and line endings, which the `canonical`
text does not.

The Node implementation is deliberately not a port. It reads the pinned Unicode
assignment table from the release rather than trusting its own runtime, and it
parses governed JSON with a reader that refuses duplicate keys instead of using
`JSON.parse`, which is last-wins on a duplicate.

### Governed result hash

- case: [`../governed-communications-benchmark/cases/12-allow-faithful-taxonomy-claim/`](../governed-communications-benchmark/cases/12-allow-faithful-taxonomy-claim/)
- the same `manifest.json` and `build-plan.json` are compiled twice into two
  different output directories
- the compared value is `artifactHash` in `build-report.yaml`

### Governed refusal

- case: [`../governed-communications-benchmark/cases/06-validity-period-asof-mismatch/`](../governed-communications-benchmark/cases/06-validity-period-asof-mismatch/)
- compiled twice; both runs must fail with the same error codes and produce no
  `*.context.json`

The refusal check exists because a governance system that is deterministic only
when it says yes is not a governance system.

## What the hash proves

- the canonical byte form of a governed document is the same in two independent
  implementations, for all 59 published vectors;
- the published digest is derivable from those bytes rather than asserted
  beside them;
- a governed build over fixed inputs produces a byte-identical artefact, so the
  result hash identifies the artefact and the decision that produced it;
- a governed refusal is equally reproducible, with a stable machine-readable
  error code;
- therefore a governed decision can be recorded, transported, re-executed
  elsewhere and audited against the original.

## What the hash does NOT prove

- **not** that the governed value is factually correct. The hash is over the
  bytes, and wrong facts hash exactly as well as right ones;
- **not** that every relevant source was captured, or that curation is complete;
- **not** that the requirements declared for a target are the requirements the
  claim actually depends on. That gap is Proof 3, and case 14 of the benchmark
  is the worked example;
- **not** anything about implementations other than the two named above;
- **not** that a model consuming the compiled context will obey it. OBDS governs
  what reaches the model and whether execution may proceed, not what the model
  then writes.
