# Case 01 — Metric transformation: a revenue share becomes a product share

**Category:** numerical achievement

## Source statement (governed truth)

84.6% of consolidated fiscal-year 2025 revenue was taxonomy-eligible.

## What the governed model supports

84.6% of the group's consolidated revenue in fiscal year 2025 was taxonomy-eligible.

## What the communication request asks for

> 85% of our products are environmentally sustainable under the taxonomy.

## OBDS primitives exercised

requiresDefined (13.1); element absent (10.3); fail closed (5.6)

## Expected governed decision

BLOCK

No element governs a product-share truth. The revenue figure is correct and retrievable; the transformation to a product count is not governed by anything.

## Actual governed decision

**BLOCK** (compiler exit code 1; artefacts produced: none)

## Reproduce

```bash
PYTHONPATH=reference/foundation/src python -m obds_ref.cli build \
  research/governed-communications-benchmark/cases/01-metric-transformation-revenue-vs-products/manifest.json \
  research/governed-communications-benchmark/cases/01-metric-transformation-revenue-vs-products/build-plan.json \
  --out /tmp/obds-case-01
```
