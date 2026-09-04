# Case 06 — Validity period: a fiscal-year KPI presented as a current fact

**Category:** validity period

## Source statement (governed truth)

The disclosure covers 2025-01-01 to 2025-12-31.

## What the governed model supports

84.6% of fiscal-year 2025 revenue was taxonomy-eligible.

## What the communication request asks for

> 84.6% of our revenue is taxonomy-eligible. (stated in August 2026)

## OBDS primitives exercised

asOf and validity half-open interval (10.1)

## Expected governed decision

BLOCK

The element is not valid at the build asOf timestamp. The tense change is the whole failure.

## Actual governed decision

**BLOCK** (compiler exit code 2; artefacts produced: build-report.yaml)

## Reproduce

```bash
PYTHONPATH=reference/foundation/src python -m obds_ref.cli build \
  research/governed-communications-benchmark/cases/06-validity-period-asof-mismatch/manifest.json \
  research/governed-communications-benchmark/cases/06-validity-period-asof-mismatch/build-plan.json \
  --out /tmp/obds-case-06
```
