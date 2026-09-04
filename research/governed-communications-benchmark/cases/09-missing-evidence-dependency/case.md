# Case 09 — Missing evidence dependency: a claim whose evidence element is absent

**Category:** certification or rating

## Source statement (governed truth)

A claim is usable only when its required evidence is valid for the same scope (17.1).

## What the governed model supports

The process claim is backed by process data.

## What the communication request asks for

> This product line is certified climate neutral.

## OBDS primitives exercised

Claims and Evidence Profile (17.1, 17.2); requiresDefined (13.1)

## Expected governed decision

BLOCK

The required evidence element does not exist. A certification claim without a certification artefact must not build.

## Actual governed decision

**BLOCK** (compiler exit code 1; artefacts produced: none)

## Reproduce

```bash
PYTHONPATH=reference/foundation/src python -m obds_ref.cli build \
  research/governed-communications-benchmark/cases/09-missing-evidence-dependency/manifest.json \
  research/governed-communications-benchmark/cases/09-missing-evidence-dependency/build-plan.json \
  --out /tmp/obds-case-09
```
