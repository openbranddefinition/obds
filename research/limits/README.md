# Proof 3 — What OBDS does not prove

A governance standard that cannot state its own boundary is a marketing claim.
This is the boundary.

## The boundary in one line

```text
OBDS can govern declared truth.
It cannot prove undeclared truth does not exist.
```

## OBDS does NOT prove

- that approved truth is **factually correct**. Governance decides what is
  authoritative, applicable and current. It does not decide what is true;
- that **every relevant source has been captured**. A source nobody added is a
  source OBDS cannot see;
- that **curation is complete**. An empty manifest is a valid manifest;
- that **every obligation has been modelled**. Requirements are declared by
  authors, and authors miss things;
- that **external authorities are correct**. An assurance report, a
  certification or a regulatory classification enters OBDS as evidence, not as
  verified fact;
- that **a model will follow semantic guidance**. OBDS governs what reaches the
  model and whether execution may proceed. It does not control generation;
- that **no uninstrumented external model call occurred**. A call that bypasses
  the governed path leaves no governed trace, by construction.

## The worked example: case 14

Case 14 of the [Governed Communications Benchmark](../governed-communications-benchmark/)
is adversarial. It was written to defeat OBDS, and it does.

The construction: a build target whose declared requirement is the brand name
and nothing else, used to request a claim that depends on a governed truth the
target never asks for. Every requirement the target declares is satisfied. The
build succeeds. The false claim is not caught.

Section 13.1 already forbids this — a target name or description MUST NOT imply
a capability its declared requirements cannot support — but that requirement is
**normative and not mechanically enforceable**. No check can decide whether a
declared requirement set is the requirement set the claim actually depends on.
That is an authoring judgement.

Stated neutrally:

> OBDS can determine whether declared requirements are satisfied. It cannot
> prove that every relevant requirement has been discovered and modelled.

Case 14 is published with an expected decision of ALLOW, and it is counted as a
match when OBDS lets the false claim through. It is kept in the benchmark on
purpose.

## What follows from this

The honest scope of the mechanism:

- OBDS raises the cost of an **undetected** governance failure, because a
  governed decision is reproducible and auditable;
- it does not raise the cost of a **badly declared** governance model, because
  it has no view of what was left out;
- so completeness of the model remains a human and organisational
  responsibility, and OBDS makes that responsibility explicit rather than
  removing it.

## Distinctions kept throughout the research

- **normative guarantee** vs **experimental evidence** — the specification
  states the first; this directory only ever offers the second;
- **PASS** vs **NOT ASSESSABLE** — a skipped check is reported as a skip and
  fails the run; it is never reported as a pass;
- **tested limitation** vs **future research** — case 14 is a tested
  limitation. Mechanical enforcement of section 13.1 is future research, and is
  not claimed here.
