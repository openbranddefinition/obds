# Case 11 — Required truth not_defined, and it does not substitute

**Category:** historical status

## Source statement (governed truth)

Waste collection covers the entity's own sites only, not the full value chain.

## What the governed model supports

1,240 t of waste, 806 t recycled, within the reported boundary.

## What the communication request asks for

> We recycle 65% of waste across our value chain.

## OBDS primitives exercised

Brand State not_defined (8.1); no inference (5.6)

## Expected governed decision

BLOCK

The value-chain rate is not_defined and must not be inferred from the site-level rate.

## Actual governed decision

**BLOCK** (compiler exit code 2; artefacts produced: build-report.yaml)

## Reproduce

```bash
PYTHONPATH=reference/foundation/src python -m obds_ref.cli build \
  research/governed-communications-benchmark/cases/11-required-truth-explicitly-unknown/manifest.json \
  research/governed-communications-benchmark/cases/11-required-truth-explicitly-unknown/build-plan.json \
  --out /tmp/obds-case-11
```
