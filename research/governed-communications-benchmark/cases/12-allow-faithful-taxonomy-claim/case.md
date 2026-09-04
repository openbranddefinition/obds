# Case 12 — ALLOW: the faithful claim, correctly scoped and dated

**Category:** numerical achievement

## Source statement (governed truth)

84.6% of consolidated fiscal-year 2025 revenue was taxonomy-eligible.

## What the governed model supports

Same.

## What the communication request asks for

> 84.6% of the group's consolidated revenue in fiscal year 2025 was taxonomy-eligible.

## OBDS primitives exercised

requiresDefined (13.1); scope (9); asOf (10.1)

## Expected governed decision

ALLOW

Positive control. A system that blocks everything must not pass this benchmark.

## Actual governed decision

**ALLOW** (compiler exit code 0; artefacts produced: build-report.yaml, case-12.context.json, case-12.context.md)

## Reproduce

```bash
PYTHONPATH=reference/foundation/src python -m obds_ref.cli build \
  research/governed-communications-benchmark/cases/12-allow-faithful-taxonomy-claim/manifest.json \
  research/governed-communications-benchmark/cases/12-allow-faithful-taxonomy-claim/build-plan.json \
  --out /tmp/obds-case-12
```
