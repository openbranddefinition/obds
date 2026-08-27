# OBDS 1.0.0 Stable Release

Start here:

1. `OBDS-PUBLIC-README-1.0.0.md`
2. `OBDS-1.0.0.md`
3. `OBDS-1.0.0-IMPLEMENTER-QUICKSTART.md`
4. `OBDS-1.0.0-CAPABILITY-REGISTRY.json`
5. `OBDS-1.0.0-SCHEMA-INDEX.json`
6. `OBDS-1.0.0-TEST-REQUIREMENTS.md`
7. `OBDS-1.0.0-TEST-RESULT.json`
8. `OBDS-1.0.0-TEST-OUTPUT.txt`
9. `OBDS-1.0.0-PUBLICATION-MAP.json`

OBDS 1.0.0 is stable. The complete release gate passed without normative changes.

## Reproduce the release

`OBDS-1.0.0-TEST-REQUIREMENTS.md` declares every dependency needed to reproduce 105/105 and
separates OBDS consumer requirements from reference conformance-suite requirements.

```bash
python reference/run_all.py        # 105 passed, 0 failed, 0 skipped
python reference/release-gate.py   # package metadata and junk check
```

`release-schemas/` holds the two package metadata schemas used by the release gate. They are
package schemas, not OBDS Brand Truth contracts, and are deliberately outside the public OBDS
schema surface described in `OBDS-1.0.0-PUBLICATION-MAP.json`.

> One specification. One Foundation. Optional capabilities.
