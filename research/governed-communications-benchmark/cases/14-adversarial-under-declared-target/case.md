# Case 14 — ADVERSARIAL: an under-declared target that requires nothing the false claim depends on

**Category:** required qualification

## Source statement (governed truth)

Section 13.1: a target name or description MUST NOT imply a capability that its declared requirements cannot support.

## What the governed model supports

84.6% of fiscal-year 2025 revenue was taxonomy-eligible.

## What the communication request asks for

> 85% of our products are environmentally sustainable, requested through a target that only requires the brand name.

## OBDS primitives exercised

Target requirements (13.1) — normative but not mechanically enforceable

## Expected governed decision

ALLOW

OBDS builds successfully and the false claim is NOT caught. This is the boundary of the mechanism, kept in the benchmark on purpose. OBDS can determine whether declared requirements are satisfied. It cannot prove that every relevant requirement has been discovered and modelled.

## Actual governed decision

**ALLOW** (compiler exit code 0; artefacts produced: build-report.yaml, case-14.context.json, case-14.context.md)

## Reproduce

```bash
PYTHONPATH=reference/foundation/src python -m obds_ref.cli build \
  research/governed-communications-benchmark/cases/14-adversarial-under-declared-target/manifest.json \
  research/governed-communications-benchmark/cases/14-adversarial-under-declared-target/build-plan.json \
  --out /tmp/obds-case-14
```
