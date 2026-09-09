# Optional Task Facts 1.0 evaluator suite

Prospective OBDS 4.1.0 internal candidate; see [ADOPTION.md](ADOPTION.md) for exact authority, identities and limitations. Existing OBDS consumers require no adoption or migration. This suite does not add production integration to the reference compiler.

Run from the repository or extracted package root with Python 3.11+ and Node:

```sh
python3 reference/task-facts/1.0/run-suite.py --result /tmp/task-facts-python.json --implementation-name research-python --implementation-version frozen-cycle-1 -- python3 reference/task-facts/1.0/evidence/interop/cycles/cycle-1/implementation-python/evaluate.py
python3 reference/task-facts/1.0/run-suite.py --result /tmp/task-facts-node.json --implementation-name research-node --implementation-version frozen-cycle-1 -- node reference/task-facts/1.0/evidence/interop/cycles/cycle-1/implementation-node/evaluate.mjs
```

Each child intentionally exits 2 when any outcome is INVALID. A successful harness exits 0 after exact ordered comparisons of all 66 fixtures and 36 regressions. Harness exit 1 means a protocol/conformance mismatch; 2 means an infrastructure/identity failure. Both write machine-readable results including implementation/version and executable digests, suiteHash, raw stdout/stderr and exact records. See [RUNNER-CONTRACT.md](RUNNER-CONTRACT.md) for retained-output comparison via compare.py. The evaluator CLI authority is contract section **6**, correcting A-N1.

The six fields are family (file family ID), caseId, conditionId, snapshotHash (complete TFJ snapshot identity), outcome and reason. Unbound errors carry null routing fields and hash. Bound malformed snapshots retain their canonical identity. Do not sort records or repair malformed raw inputs. Examples deliberately include invalid and unresolved outcomes.

Retain complete snapshots, conditions, verifier contexts and decisions. Trusted hosts supply contexts independently of callers; accepted digests and fact presence do not prove truth. UNKNOWN, CONTRADICTORY and INVALID never grant permission. False conditions cannot remove static requirements. See [evidence reproduction](EVIDENCE-README.md).
