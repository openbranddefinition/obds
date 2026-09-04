# Case 04 — System boundary: a process saving becomes a whole-product claim

**Category:** environmental claim

## Source statement (governed truth)

Manufacturing the recycled input material results in a 62% saving in carbon emissions compared with virgin raw material.

## What the governed model supports

The 62% saving applies to the input-material manufacturing process.

## What the communication request asks for

> This product has 62% lower carbon emissions.

## OBDS primitives exercised

Brand State unknown (8.1); requiresDefined (13.1)

## Expected governed decision

BLOCK

No whole-product lifecycle figure exists. The retrieved number is right; the system boundary it is applied to is not.

## Actual governed decision

**BLOCK** (compiler exit code 2; artefacts produced: build-report.yaml)

## Reproduce

```bash
PYTHONPATH=reference/foundation/src python -m obds_ref.cli build \
  research/governed-communications-benchmark/cases/04-system-boundary-process-to-whole-product/manifest.json \
  research/governed-communications-benchmark/cases/04-system-boundary-process-to-whole-product/build-plan.json \
  --out /tmp/obds-case-04
```
