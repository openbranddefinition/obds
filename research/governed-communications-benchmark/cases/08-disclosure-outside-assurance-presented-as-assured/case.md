# Case 08 — Disclosure outside limited assurance presented as assured

**Category:** required qualification

## Source statement (governed truth)

The transition plan and the actions disclosure are outside the assurance conclusion.

## What the governed model supports

The limited assurance conclusion names its exclusions.

## What the communication request asks for

> Our transition plan is independently assured.

## OBDS primitives exercised

requiresDefined (13.1); element absent (10.3)

## Expected governed decision

BLOCK

No element governs assurance of the transition plan, so the build fails closed rather than borrowing the report-level one.

## Actual governed decision

**BLOCK** (compiler exit code 1; artefacts produced: none)

## Reproduce

```bash
PYTHONPATH=reference/foundation/src python -m obds_ref.cli build \
  research/governed-communications-benchmark/cases/08-disclosure-outside-assurance-presented-as-assured/manifest.json \
  research/governed-communications-benchmark/cases/08-disclosure-outside-assurance-presented-as-assured/build-plan.json \
  --out /tmp/obds-case-08
```
