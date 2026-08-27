# OBDS 1.0.1 Stable Release

Start here:

1. `OBDS-PUBLIC-README-1.0.1.md`
2. `OBDS-1.0.1.md`
3. `OBDS-1.0.1-IMPLEMENTER-QUICKSTART.md`
4. `OBDS-1.0.1-CAPABILITY-REGISTRY.json`
5. `OBDS-1.0.1-SCHEMA-INDEX.json`
6. `OBDS-1.0.1-TEST-REQUIREMENTS.md`
7. `OBDS-1.0.1-TEST-RESULT.json`
8. `OBDS-1.0.1-TEST-OUTPUT.txt`
9. `OBDS-1.0.1-PUBLICATION-MAP.json`

OBDS 1.0.1 is stable. It clarifies licensing in section 32 and changes no normative contract. The public schema surface is byte-identical to 1.0.0, and every schema `$id` still resolves under `/schemas/1.0.0/` and `/value-schemas/1.0.0/`.

## Reproduce the release

`OBDS-1.0.1-TEST-REQUIREMENTS.md` declares every dependency needed to reproduce 105/105 and
separates OBDS consumer requirements from reference conformance-suite requirements.

```bash
python reference/run_all.py        # 105 passed, 0 failed, 0 skipped
python reference/release-gate.py   # package metadata and junk check
```

`release-schemas/` holds the two package metadata schemas used by the release gate. They are
package schemas, not OBDS Brand Truth contracts, and are deliberately outside the public OBDS
schema surface described in `OBDS-1.0.1-PUBLICATION-MAP.json`.

> One specification. One Foundation. Optional capabilities.
