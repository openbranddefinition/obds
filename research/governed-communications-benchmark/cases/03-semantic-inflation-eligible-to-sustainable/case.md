# Case 03 — Semantic inflation: eligible presented as environmentally sustainable

**Category:** environmental claim

## Source statement (governed truth)

Eligibility describes activities covered by the taxonomy, not demonstrated environmental sustainability.

## What the governed model supports

84.6% of consolidated fiscal-year 2025 revenue was taxonomy-eligible.

## What the communication request asks for

> 84.6% of our business is environmentally sustainable.

## OBDS primitives exercised

requiresDefined (13.1); unknown (8.1); never invent (5.6)

## Expected governed decision

BLOCK

The sustainability conclusion depends on alignment, which is unknown. The vocabulary shift is the whole failure.

## Actual governed decision

**BLOCK** (compiler exit code 2; artefacts produced: build-report.yaml)

## Reproduce

```bash
PYTHONPATH=reference/foundation/src python -m obds_ref.cli build \
  research/governed-communications-benchmark/cases/03-semantic-inflation-eligible-to-sustainable/manifest.json \
  research/governed-communications-benchmark/cases/03-semantic-inflation-eligible-to-sustainable/build-plan.json \
  --out /tmp/obds-case-03
```
