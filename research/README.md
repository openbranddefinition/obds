# OBDS Research

Open Brand Definition Standard, release 3.0.2. This directory is the public
research surface: the evidence, and the boundary of the evidence. It is not a
second specification. Nothing here changes a normative artefact.

## Question

Can an AI system retrieve the right evidence and still make the wrong governed
decision?

## Hypothesis

Yes, and the two are different problems.

Retrieval answers one question:

```text
what information looks relevant?
```

Governance has to answer six more:

```text
which truth is authoritative?
which scope applies?
is it valid now?
is required truth missing?
is there a relevant conflict?
may execution proceed?
```

The central claim in one line:

> Retrieval can find the right source and still use the wrong truth.

The distinction the whole standard rests on:

```text
knowledge access  ≠  governed applicability
```

## Three proofs

### 1. Deterministic governed result

Same governed inputs, independent implementations, same governed result hash —
and the same refusal when the inputs do not support the request.

→ [`governed-result-hash/`](governed-result-hash/)

One command, four checks, all currently passing:

```bash
PYTHONPATH=reference/foundation/src python research/governed-result-hash/verify.py
```

### 2. Governed Communications Benchmark

Fourteen cases in which the retrieved source fact is correct and the
communication built from it is not. Eleven must block, two are positive
controls that must be allowed, and one is adversarial and defeats OBDS.

→ [`governed-communications-benchmark/`](governed-communications-benchmark/)

```bash
PYTHONPATH=reference/foundation/src python \
  research/governed-communications-benchmark/run_benchmark.py
```

Current result: 14 of 14 cases reach their expected governed decision under the
3.0.2 reference compiler, including case 14, whose expected decision is that
OBDS fails to catch a false claim.

### 3. Stated limits

Where the mechanism stops. Case 14 is the worked example.

→ [`limits/`](limits/)

## Evidence discipline

Every claim in this directory points at a public artefact in this repository
and, where practical, at a command that reproduces it. Three distinctions are
kept explicit throughout:

- a normative guarantee is not experimental evidence;
- a PASS is not a NOT ASSESSABLE;
- a tested limitation is not future research.

No internal review, audit or evaluation is offered here as technical proof. The
proofs are executable or they are not proofs.

## Normative artefacts

The research does not modify them. It links to them.

- specification: [`OBDS-3.0.2.md`](../OBDS-3.0.2.md)
- schemas: [`schemas/`](../schemas/), [`value-schemas/`](../value-schemas/)
- reference implementation: [`reference/`](../reference/)
- conformance result: [`OBDS-3.0.2-FOUNDATION-CONFORMANCE.json`](../OBDS-3.0.2-FOUNDATION-CONFORMANCE.json)
- full suite result: [`OBDS-3.0.2-TEST-RESULT.json`](../OBDS-3.0.2-TEST-RESULT.json)
