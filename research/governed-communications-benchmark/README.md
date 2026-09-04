# Proof 2 — Governed Communications Benchmark

A reproducible benchmark that asks one question:

> Can current OBDS primitives stop unsafe external communication even when
> relevant source material exists and is retrieved correctly?

Every wrong claim in this benchmark is a *downstream transformation of a
correct statement*: a revenue share becomes a product share, an eligibility
figure becomes an alignment figure, a process comparison becomes a
whole-product claim, a fiscal-year fact becomes a present-tense one.

That is the failure mode retrieval cannot see. The retrieved passage is
correct. The claim built from it is not.

## Source and de-identification

```text
The benchmark cases are de-identified from real-world communication-governance
research. Source mapping is intentionally omitted from the public package to
preserve organisational and sector neutrality.
```

Organisation, sector, products, source titles and every figure have been
replaced with synthetic, internally consistent equivalents. Nothing in this
directory is an artefact of, or a statement about, any real organisation.

An external reviewer can therefore evaluate:

```text
the governance logic
the test construction
the expected decision
the OBDS behaviour
```

but **not** the omitted source mapping. This package does not claim that a
reviewer can independently verify the underlying corporate facts of the
original research.

## Run it

From the repository root:

```bash
PYTHONPATH=reference/foundation/src python \
  research/governed-communications-benchmark/run_benchmark.py
```

The script regenerates every manifest and Build Plan, runs the published 3.0.2
reference compiler against each case, and records the **actual** decision next
to the **expected** one. Expected decisions are not edited to match.

## Result

14 of 14 cases reach their expected governed decision under the 3.0.2 reference
compiler.

| # | Category | Case | Expected | Actual |
|---|---|---|---|---|
| 01 | numerical achievement | Metric transformation: a revenue share becomes a product share | BLOCK | BLOCK |
| 02 | certification or rating | Regulatory status: eligible presented as aligned | BLOCK | BLOCK |
| 03 | environmental claim | Semantic inflation: eligible presented as environmentally sustainable | BLOCK | BLOCK |
| 04 | environmental claim | System boundary: a process saving becomes a whole-product claim | BLOCK | BLOCK |
| 05 | numerical achievement | Entity scope: a group KPI applied to a non-consolidated entity | BLOCK | BLOCK |
| 06 | validity period | Validity period: a fiscal-year KPI presented as a current fact | BLOCK | BLOCK |
| 07 | required qualification | Assurance scope: report-level assurance projected onto an excluded disclosure | BLOCK | BLOCK |
| 08 | required qualification | Disclosure outside limited assurance presented as assured | BLOCK | BLOCK |
| 09 | certification or rating | Missing evidence dependency: a claim whose evidence element is absent | BLOCK | BLOCK |
| 10 | numerical achievement | Conflicting source: two incomparable elements govern one subject | BLOCK | BLOCK |
| 11 | historical status | Required truth not_defined, and it does not substitute | BLOCK | BLOCK |
| 12 | numerical achievement | ALLOW: the faithful claim, correctly scoped and dated | ALLOW | ALLOW |
| 13 | environmental claim | ALLOW: the process claim stated at its real system boundary | ALLOW | ALLOW |
| 14 | required qualification | ADVERSARIAL: an under-declared target | ALLOW | ALLOW |

Cases 12 and 13 are positive controls. A system that blocks everything fails
this benchmark. Case 13 allows the same number that case 04 blocks, because
case 13 states the system boundary and case 04 does not.

Case 14 is adversarial: it was written to defeat OBDS, and it does. Its
expected decision is ALLOW, meaning the false claim is **not** caught. See
[`../limits/`](../limits/).

## What each case contains

```text
cases/<NN>-<slug>/
    manifest.json      the governed truth model
    build-plan.json    the communication request as a build target
    case.md            source statement, requested claim, expected vs actual, reproduce command
    out/               build report, and the context artefact where one was produced
raw-results.json       verbatim compiler output per case
results-table.md       the summary table alone
```

Every `case.md` carries a single-case reproduce command.

## Reading the outcome

BLOCK is not "the compiler crashed". Each blocked case fails for the reason the
case was written to test, and the reason is machine-readable in
`out/build-report.yaml`. Examples from the current run:

| Case | Error code or signal |
|---|---|
| 01 | `requiresDefined reference not found` — the element does not exist |
| 05 | `OBDS-BUILD-REQUIRED-OUT-OF-SCOPE` |
| 06 | `OBDS-BUILD-REQUIRED-EXPIRED` |
| 10 | `conflicts[].decisionRelevant: true` — hard conflict, section 10.2a |

## Scope of the claim

This benchmark tests **governance decisions**, not source completeness.

It does not show that all communication governed by OBDS is safe. It shows that
for these fourteen constructed cases, the declared governance model reaches the
decision the case was designed to require — including the one case where the
correct answer is that OBDS fails.

No benchmark-specific semantics were added to OBDS. The fixture uses published
primitives only: claims and evidence are `nature: knowledge` CONTEXT elements,
and the Claims and Evidence Profile shape from section 17 is carried inside the
element `value` as descriptive content.
