# Case 13 — ALLOW: the process claim stated at its real system boundary

**Category:** environmental claim

## Source statement (governed truth)

Manufacturing the recycled input material results in a 62% saving in carbon emissions compared with virgin raw material.

## What the governed model supports

Same.

## What the communication request asks for

> Manufacturing the recycled input material results in a 62% saving in carbon emissions compared with virgin raw material.

## OBDS primitives exercised

requiresDefined (13.1); scope (9); evidence (17.2)

## Expected governed decision

ALLOW

Positive control. The same number that is blocked in case 04 is allowed when the boundary is stated.

## Actual governed decision

**ALLOW** (compiler exit code 0; artefacts produced: build-report.yaml, case-13.context.json, case-13.context.md)

## Reproduce

```bash
PYTHONPATH=reference/foundation/src python -m obds_ref.cli build \
  research/governed-communications-benchmark/cases/13-allow-process-claim-at-its-boundary/manifest.json \
  research/governed-communications-benchmark/cases/13-allow-process-claim-at-its-boundary/build-plan.json \
  --out /tmp/obds-case-13
```
