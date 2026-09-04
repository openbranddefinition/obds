# Case 10 — Conflicting source: two incomparable elements govern one subject

**Category:** numerical achievement

## Source statement (governed truth)

A second, differently scoped statement of the same KPI is introduced to simulate a competing internal source.

## What the governed model supports

Exactly one governed value per subject and scope.

## What the communication request asks for

> Publish the taxonomy-eligible revenue share.

## OBDS primitives exercised

Semantic subject (8.0); precedence and hard conflict (10.2)

## Expected governed decision

BLOCK

Two incomparable maximal elements are a hard conflict. Retrieval would rank one of them and answer confidently.

## Actual governed decision

**BLOCK** (compiler exit code 2; artefacts produced: build-report.yaml)

## Reproduce

```bash
PYTHONPATH=reference/foundation/src python -m obds_ref.cli build \
  research/governed-communications-benchmark/cases/10-conflicting-competing-truth/manifest.json \
  research/governed-communications-benchmark/cases/10-conflicting-competing-truth/build-plan.json \
  --out /tmp/obds-case-10
```
