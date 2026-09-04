# Case 05 — Entity scope: a group KPI applied to a non-consolidated entity

**Category:** numerical achievement

## Source statement (governed truth)

The subsidiary was not consolidated in fiscal year 2025 and is generally excluded from group KPIs.

## What the governed model supports

84.6% of consolidated group revenue was taxonomy-eligible.

## What the communication request asks for

> 84.6% of the subsidiary's revenue was taxonomy-eligible.

## OBDS primitives exercised

Scope (9); element applicability (10.1)

## Expected governed decision

BLOCK

The element does not apply to this entity scope. Retrieval has no notion of which legal entity a KPI covers.

## Actual governed decision

**BLOCK** (compiler exit code 2; artefacts produced: build-report.yaml)

## Reproduce

```bash
PYTHONPATH=reference/foundation/src python -m obds_ref.cli build \
  research/governed-communications-benchmark/cases/05-entity-scope-mismatch/manifest.json \
  research/governed-communications-benchmark/cases/05-entity-scope-mismatch/build-plan.json \
  --out /tmp/obds-case-05
```
