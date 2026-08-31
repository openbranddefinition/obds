# OBDS 1.0 Reference Suites

Suites:

- Foundation
- Context Delivery
- Context Assembly
- Design Space
- Integration
- Golden end-to-end
- Adversarial

Run all suites from the package root, which in this repository is the
repository root:

```bash
python reference/run_all.py
```

Expected: 199 passed, 0 failed, 0 skipped. `release-gate.py` is a package
check, not a suite; see `OBDS-1.0.4-TEST-REQUIREMENTS.md`.

The Golden suite exercises Manifest, Build Plan, Compiled Brand Context, Context Delivery, Context Assembly, Review and Runtime Decision in one chain.
