# OBDS 1.0.2 Stable Release

Start here:

1. `OBDS-PUBLIC-README-1.0.2.md`
2. `OBDS-1.0.2.md`
3. `OBDS-1.0.2-IMPLEMENTER-QUICKSTART.md`
4. `examples/`
5. `OBDS-1.0.2-CAPABILITY-REGISTRY.json`
6. `OBDS-1.0.2-SCHEMA-INDEX.json`
7. `OBDS-1.0.2-TEST-REQUIREMENTS.md`
8. `OBDS-1.0.2-TEST-RESULT.json`
9. `OBDS-1.0.2-TEST-OUTPUT.txt`
10. `OBDS-1.0.2-PUBLICATION-MAP.json`

OBDS 1.0.2 is stable. It is a licensing, packaging and documentation release. It
changes no normative contract. The public schema surface is byte-identical to
1.0.0 and 1.0.1, and every schema `$id` still resolves under `/schemas/1.0.0/`
and `/value-schemas/1.0.0/`.

## Licensing

Two standard licences, neither of them modified. See `LICENSE.md`.

- specification and documentation: **CC BY 4.0** (`LICENSES/CC-BY-4.0.txt`)
- schemas, release metadata, reference implementation, conformance suite and
  examples: **Apache License 2.0** (`LICENSES/Apache-2.0.txt`)

Commercial implementation is permitted and needs no separate permission.
Trademarks are governed separately in `TRADEMARKS.md`.

## Reproduce the release

`OBDS-1.0.2-TEST-REQUIREMENTS.md` declares every dependency needed to reproduce
105/105 and separates OBDS consumer requirements from reference conformance-suite
requirements.

```bash
python reference/run_all.py        # 105 passed, 0 failed, 0 skipped
python reference/release-gate.py   # package metadata, contract identity, junk check
```

The release gate also proves that the normative contract fingerprints are
identical to 1.0.1.

## Examples

`examples/foundation-minimal/` is the smallest valid OBDS implementation:
Foundation only, one element, one target, and it compiles.

`examples/fail-closed/` is the same shape with one required element in state
`unknown`. The build fails, no Compiled Brand Context is written, and no model is
called. See `examples/README.md`.

`release-schemas/` holds the two package metadata schemas used by the release
gate. They are package schemas, not OBDS Brand Truth contracts, and are
deliberately outside the public OBDS schema surface described in
`OBDS-1.0.2-PUBLICATION-MAP.json`.

> One specification. One Foundation. Optional capabilities.
