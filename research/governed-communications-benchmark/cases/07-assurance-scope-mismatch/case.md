# Case 07 — Assurance scope: report-level assurance projected onto an excluded disclosure

**Category:** required qualification

## Source statement (governed truth)

Progress against greenhouse-gas reduction targets is explicitly excluded from the limited assurance conclusion.

## What the governed model supports

An independent limited assurance report exists for the disclosure as a whole, with named exclusions.

## What the communication request asks for

> Our independently assured 61% Scope 3 reduction progress demonstrates our leadership.

## OBDS primitives exercised

Brand State not_applicable (8.1); requiresDefined (13.1)

## Expected governed decision

BLOCK

Assurance for this specific disclosure is not_applicable. Report-level assurance is not disclosure-level assurance.

## Actual governed decision

**BLOCK** (compiler exit code 2; artefacts produced: build-report.yaml)

## Reproduce

```bash
PYTHONPATH=reference/foundation/src python -m obds_ref.cli build \
  research/governed-communications-benchmark/cases/07-assurance-scope-mismatch/manifest.json \
  research/governed-communications-benchmark/cases/07-assurance-scope-mismatch/build-plan.json \
  --out /tmp/obds-case-07
```
