# Optional Task Facts 1.0 evaluator suite

Task Facts 1.0 is a published, optional OBDS capability. It was adopted in OBDS 4.1.0 and is unchanged in every later release. The normative requirements are section 35 of the root specification, [OBDS-4.1.3.md](../../../OBDS-4.1.3.md#35-optional-task-facts-10-normative-requirements), and conformance claims are section 26.10. Section 35 still contains the adoption sentence written before publication, which says the candidate awaits authorised publication; it is normative text, so this PATCH release leaves it unchanged, and the publication it refers to is OBDS 4.1.0. [ADOPTION.md](ADOPTION.md) is the adoption record, with exact authority, identities and limitations. Existing OBDS consumers require no adoption or migration. This suite does not add production integration to the reference compiler: every published Task Facts conformance result carries `productionIntegration: false`.

Run from the repository or extracted package root with Python 3.11+ and Node:

```sh
python3 reference/task-facts/1.0/run-suite.py --result /tmp/task-facts-python.json --implementation-name research-python --implementation-version frozen-cycle-1 -- python3 reference/task-facts/1.0/evidence/interop/cycles/cycle-1/implementation-python/evaluate.py
python3 reference/task-facts/1.0/run-suite.py --result /tmp/task-facts-node.json --implementation-name research-node --implementation-version frozen-cycle-1 -- node reference/task-facts/1.0/evidence/interop/cycles/cycle-1/implementation-node/evaluate.mjs
```

Each child intentionally exits 2 when any outcome is INVALID. A successful harness exits 0 after exact ordered comparisons of all 66 fixtures and 36 regressions. Harness exit 1 means a protocol/conformance mismatch; 2 means an infrastructure/identity failure. Both write machine-readable results including implementation/version and executable digests, suiteHash, raw stdout/stderr and exact records. See [RUNNER-CONTRACT.md](RUNNER-CONTRACT.md) for retained-output comparison via compare.py. RUNNER-CONTRACT.md is one of the suite identity files listed in `SUITE.json`, so its bytes are part of the suite hash and stay frozen. Its opening sentence was written before the OBDS 4.1.0 publication and still describes the suite as waiting for it. It is retained unchanged; that publication took place on 9 September 2026. The evaluator CLI authority is contract section **6**, correcting A-N1.

The six fields are family (file family ID), caseId, conditionId, snapshotHash (complete TFJ snapshot identity), outcome and reason. Unbound errors carry null routing fields and hash. Bound malformed snapshots retain their canonical identity. Do not sort records or repair malformed raw inputs. Examples deliberately include invalid and unresolved outcomes.

Retain complete snapshots, conditions, verifier contexts and decisions. Trusted hosts supply contexts independently of callers; accepted digests and fact presence do not prove truth. UNKNOWN, CONTRADICTORY and INVALID never grant permission. False conditions cannot remove static requirements. See [evidence reproduction](EVIDENCE-README.md).
