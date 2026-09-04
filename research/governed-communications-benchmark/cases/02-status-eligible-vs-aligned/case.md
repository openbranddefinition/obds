# Case 02 — Regulatory status: eligible presented as aligned

**Category:** certification or rating

## Source statement (governed truth)

The alignment assessment was still in progress; no aligned share was reported.

## What the governed model supports

84.6% of consolidated fiscal-year 2025 revenue was taxonomy-eligible.

## What the communication request asks for

> 85% of our revenue is taxonomy-aligned.

## OBDS primitives exercised

Brand State unknown (8.1); requiresDefined (13.1)

## Expected governed decision

BLOCK

The aligned share is explicitly unknown. Unknown is a governed state, not an absence to be filled in.

## Actual governed decision

**BLOCK** (compiler exit code 2; artefacts produced: build-report.yaml)

## Reproduce

```bash
PYTHONPATH=reference/foundation/src python -m obds_ref.cli build \
  research/governed-communications-benchmark/cases/02-status-eligible-vs-aligned/manifest.json \
  research/governed-communications-benchmark/cases/02-status-eligible-vs-aligned/build-plan.json \
  --out /tmp/obds-case-02
```
