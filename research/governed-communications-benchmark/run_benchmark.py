#!/usr/bin/env python3
"""
Governed Communications Benchmark v0.2 — case generator, runner and reporter.

One question:

    When retrieval gets the source fact right, does OBDS still stop the
    communication that is built from it going wrong?

The fixture is de-identified. It is derived from real-world
communication-governance research, but every organisation, product,
sector marker, source title and figure has been replaced. Nothing here
is an artefact of, or a statement about, any real organisation.

The manifest uses published OBDS primitives only. No benchmark-specific
semantics are added to OBDS. Claims and evidence are modelled as
`nature: knowledge` CONTEXT elements, which the published specification
already permits; the Claims and Evidence Profile (section 17) shape is
carried inside the element `value` as descriptive content.

Run from the repository root:

    PYTHONPATH=reference/foundation/src python \
        research/governed-communications-benchmark/run_benchmark.py
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "reference" / "foundation" / "src"))

from obds_ref.canonical import manifest_content_hash  # noqa: E402

CASES_DIR = HERE / "cases"
BRAND = "urn:obds:brand:gcb-research-fixture"

# Reporting period FY25 = 2025-01-01 to 2025-12-31, half-open per spec 10.1.
FY25_FROM = "2025-01-01T00:00:00Z"
FY25_TO = "2026-01-01T00:00:00Z"
AS_OF_IN_PERIOD = "2025-12-01T00:00:00Z"
AS_OF_AFTER_PERIOD = "2026-08-29T00:00:00Z"

CONTRACT = BRAND + "#value-contract:structure:brand-identity:2b7196d8"


def el(eid, *, state, value=None, scope=None, subject=None,
       validity=None, sources=None, kind="claim", nature="knowledge",
       family="context"):
    e = {
        "id": eid,
        "family": family,
        "kind": kind,
        "nature": nature,
        "state": state,
        "scope": scope or {},
        "sourceRefs": sources or [],
        "validity": validity or {"from": None, "to": None},
        "annotations": [],
    }
    if subject:
        e["subject"] = subject
    if state == "defined":
        e["value"] = value
    return e


# ---------------------------------------------------------------------------
# The governed truth model.
#
# Every value is de-identified. The figures are synthetic and internally
# consistent; they are not the figures of any real disclosure.
# ---------------------------------------------------------------------------

ELEMENTS = [
    # --- structure -------------------------------------------------------
    {
        "id": "structure.brand",
        "family": "structure",
        "kind": "brand-identity",
        "nature": "fact",
        "state": "defined",
        "scope": {},
        "sourceRefs": [],
        "validity": {"from": None, "to": None},
        "annotations": [],
        "value": {"name": "Governed Communications Research Fixture"},
        "valueContractRef": CONTRACT,
    },

    # --- SUPPORTED TRUTH -------------------------------------------------
    el("claim.taxonomy.eligible-revenue-share",
       state="defined",
       scope={"brands": ["entity-group"]},
       validity={"from": FY25_FROM, "to": FY25_TO},
       sources=["Reporting entity, FY25 disclosure, taxonomy KPI section"],
       value={
           "canonicalWording": "84.6% of the group's consolidated revenue in "
                               "fiscal year 2025 was taxonomy-eligible.",
           "claimType": "environmental",
           "riskLevel": "regulated",
           "conditions": [
               "applies to consolidated revenue, not to a product count",
               "eligible is not aligned",
               "2.4 pp taxonomy-ineligible",
               "13.0 pp unclassified for lack of data",
           ],
           "evidenceRefs": ["evidence.taxonomy.turnover-kpi"],
           "prohibitedVariants": [
               "85% of the group's products are environmentally sustainable "
               "under the taxonomy.",
               "85% of the group's products are taxonomy-aligned.",
           ],
       }),

    el("claim.recycled-input.process-emissions",
       state="defined",
       scope={"brands": ["entity-group"], "productFamilies": ["product-line-a"]},
       validity={"from": FY25_FROM, "to": FY25_TO},
       sources=["Reporting entity, FY25 disclosure, recycled-input section"],
       value={
           "canonicalWording": "Manufacturing the recycled input material "
                               "results in a 62% saving in carbon emissions "
                               "compared with virgin raw material.",
           "claimType": "comparative",
           "riskLevel": "regulated",
           "conditions": [
               "system boundary is the manufacturing process for the input material",
               "comparison baseline is virgin raw material",
               "not a whole-product lifecycle figure",
           ],
           "evidenceRefs": ["evidence.recycled-input.process-data"],
       }),

    el("claim.scope2.market-based-reduction",
       state="defined",
       scope={"brands": ["entity-group"]},
       validity={"from": FY25_FROM, "to": FY25_TO},
       sources=["Reporting entity, FY25 disclosure, climate section"],
       value={
           "canonicalWording": "Market-based Scope 2 emissions fell 19% from "
                               "2024 to 2025.",
           "claimType": "factual",
           "riskLevel": "regulated",
           "conditions": [
               "market-based Scope 2 only",
               "Scope 1 rose 11% in the same period",
               "material Scope 3 rose 2% in the same period",
           ],
           "evidenceRefs": ["evidence.assurance.limited-fy25"],
       }),

    el("evidence.taxonomy.turnover-kpi", kind="evidence",
       state="defined",
       scope={"brands": ["entity-group"]},
       validity={"from": FY25_FROM, "to": FY25_TO},
       sources=["Reporting entity, FY25 disclosure, taxonomy KPI tables"],
       value={
           "type": "dataset",
           "title": "Taxonomy turnover KPI, fiscal year 2025",
           "issuer": "Reporting entity",
           "methodologySummary": "Turnover KPI per the applicable taxonomy regulation.",
           "limitations": [
               "eligibility only; alignment assessment still in progress",
               "13.0 pp unclassified for lack of data",
           ],
       }),

    el("evidence.recycled-input.process-data", kind="evidence",
       state="defined",
       scope={"brands": ["entity-group"], "productFamilies": ["product-line-a"]},
       validity={"from": FY25_FROM, "to": FY25_TO},
       sources=["Reporting entity, FY25 disclosure, recycled-input section"],
       value={
           "type": "study",
           "title": "Recycled input material manufacturing comparison versus "
                    "virgin raw material",
           "issuer": "Reporting entity",
           "methodologySummary": "Process comparison over the manufacturing "
                                 "stage of the input material only.",
           "limitations": [
               "manufacturing process only",
               "not a product lifecycle assessment",
           ],
       }),

    el("evidence.assurance.limited-fy25", kind="evidence",
       state="defined",
       scope={"brands": ["entity-group"]},
       validity={"from": FY25_FROM, "to": FY25_TO},
       sources=["Reporting entity, FY25 disclosure, independent assurance report"],
       value={
           "type": "approval",
           "title": "Independent limited assurance report, fiscal year 2025",
           "issuer": "Independent auditor",
           "methodologySummary": "Limited assurance engagement.",
           "limitations": [
               "materially lower than reasonable assurance",
               "excludes the transition plan disclosure",
               "excludes the actions and resources disclosure",
               "excludes progress against greenhouse-gas reduction targets",
               "forward-looking disclosures are not assured as achievable",
           ],
       }),

    el("claim.scope3.target", kind="claim",
       state="defined",
       scope={"brands": ["entity-group"]},
       validity={"from": FY25_FROM, "to": FY25_TO},
       sources=["Reporting entity, FY25 disclosure, climate targets"],
       value={
           "canonicalWording": "The group targets a 55% reduction in material "
                               "Scope 3 emissions by 2032 against a 2019 base "
                               "year; 2025 progress is stated as 61%.",
           "claimType": "environmental",
           "riskLevel": "regulated",
           "conditions": [
               "forward-looking target",
               "progress disclosure is outside the limited assurance conclusion",
           ],
           "evidenceRefs": ["evidence.assurance.scope3-progress"],
       }),

    # --- EXPLICIT KNOWLEDGE GAPS ----------------------------------------
    el("claim.taxonomy.aligned-revenue-share",
       state="unknown",
       scope={"brands": ["entity-group"]},
       sources=["Alignment assessment still in progress; no aligned share reported"]),

    el("claim.recycled-input.whole-product-carbon-reduction",
       state="unknown",
       scope={"brands": ["entity-group"], "productFamilies": ["product-line-a"]},
       sources=["No whole-product lifecycle figure is reported"]),

    el("evidence.assurance.scope3-progress", kind="evidence",
       state="not_applicable",
       scope={"brands": ["entity-group"]},
       sources=["Progress against greenhouse-gas reduction targets is "
                "explicitly excluded from the limited assurance conclusion"]),

    el("claim.waste.value-chain-recycling-rate",
       state="not_defined",
       scope={"brands": ["entity-group"]},
       sources=["Waste collection covers the entity's own sites only, "
                "not the full value chain"]),

    # `claim.product.share-environmentally-sustainable` is deliberately ABSENT.
    # `evidence.assurance.transition-plan` is deliberately ABSENT.
    # `evidence.product-line-a.climate-neutral-certificate` is deliberately ABSENT.
    # `claim.*` for the non-consolidated subsidiary is deliberately ABSENT.
]

VALUE_CONTRACTS = [
    {
        "id": CONTRACT,
        "family": "structure",
        "kind": "brand-identity",
        "shapeHash": "sha256:2b7196d853bac7cea83330be9c2073848dedc10746eaf403bb5f73687531baf2",
        "schemaRef": "https://openbranddefinition.org/value-schemas/1.0.0/brand-identity.schema.json",
        "schemaHash": "sha256:c99a47a601388f9a855a4a6b006f10a3e5709bcfb1ab3073f7c5d63114c24c51",
        "validatorRef": None,
    }
]


def base_manifest(extra_elements=None):
    elements = copy.deepcopy(ELEMENTS)
    if extra_elements:
        elements.extend(copy.deepcopy(extra_elements))
    m = {
        "id": BRAND,
        "kind": "brand-manifest",
        "name": "Governed Communications Research Fixture",
        "owner": "OBDS research fixture, de-identified, not a real organisation",
        "schemaVersion": "1.0.0",
        "version": "1.0.0",
        "status": "approved",
        "createdAt": "2026-09-04T09:00:00+02:00",
        "updatedAt": "2026-09-04T09:00:00+02:00",
        "profiles": ["obds-foundation"],
        "elements": elements,
        "valueContracts": copy.deepcopy(VALUE_CONTRACTS),
    }
    m["approval"] = {
        "approvedBy": "role:brand-owner",
        "approvedAt": "2026-09-04T09:00:00+02:00",
        "contentHash": manifest_content_hash(m),
    }
    return m


def build_plan(target_id, requires, scope, as_of=AS_OF_IN_PERIOD,
               manifest=None, style="selected", state_map="all_applicable"):
    m = manifest
    return {
        "id": f"urn:obds:build-plan:{target_id}",
        "kind": "obds-build-plan",
        "schemaVersion": "3.0.0",
        "manifestRef": {
            "id": BRAND,
            "version": "1.0.0",
            "contentHash": m["approval"]["contentHash"],
        },
        "compiler": {"id": "org.openbranddefinition.reference-compiler",
                     "version": "1.0.0"},
        "tokenizer": {"id": "obds:whitespace-v1", "version": "1.0.0"},
        "targets": [{
            "id": target_id,
            "scope": scope,
            "requiresDefined": requires,
            "styleTexture": {"mode": style,
                             "elementIds": list(requires) if style == "selected" else []},
            "stateMap": {"mode": state_map, "kinds": []},
            "releasePolicy": "build_only",
            "maxTokens": 4000,
        }],
        "asOf": as_of,
    }


# ---------------------------------------------------------------------------
# The cases.
# ---------------------------------------------------------------------------

GROUP_SCOPE = {"brands": "entity-group", "outputTypes": "marketing-copy"}
PLA_SCOPE = {"brands": "entity-group", "productFamilies": "product-line-a",
             "outputTypes": "marketing-copy"}

CASE_DEFS = [
    dict(
        n="01", slug="metric-transformation-revenue-vs-products",
        category="numerical achievement",
        title="Metric transformation: a revenue share becomes a product share",
        source="84.6% of consolidated fiscal-year 2025 revenue was taxonomy-eligible.",
        supported="84.6% of the group's consolidated revenue in fiscal year 2025 "
                  "was taxonomy-eligible.",
        requested="85% of our products are environmentally sustainable under "
                  "the taxonomy.",
        primitives="requiresDefined (13.1); element absent (10.3); fail closed (5.6)",
        expected="BLOCK",
        rationale="No element governs a product-share truth. The revenue figure "
                  "is correct and retrievable; the transformation to a product "
                  "count is not governed by anything.",
        requires=["claim.product.share-environmentally-sustainable"],
        scope=GROUP_SCOPE,
    ),
    dict(
        n="02", slug="status-eligible-vs-aligned",
        category="certification or rating",
        title="Regulatory status: eligible presented as aligned",
        source="The alignment assessment was still in progress; no aligned "
               "share was reported.",
        supported="84.6% of consolidated fiscal-year 2025 revenue was taxonomy-eligible.",
        requested="85% of our revenue is taxonomy-aligned.",
        primitives="Brand State unknown (8.1); requiresDefined (13.1)",
        expected="BLOCK",
        rationale="The aligned share is explicitly unknown. Unknown is a "
                  "governed state, not an absence to be filled in.",
        requires=["claim.taxonomy.aligned-revenue-share"],
        scope=GROUP_SCOPE,
    ),
    dict(
        n="03", slug="semantic-inflation-eligible-to-sustainable",
        category="environmental claim",
        title="Semantic inflation: eligible presented as environmentally sustainable",
        source="Eligibility describes activities covered by the taxonomy, not "
               "demonstrated environmental sustainability.",
        supported="84.6% of consolidated fiscal-year 2025 revenue was taxonomy-eligible.",
        requested="84.6% of our business is environmentally sustainable.",
        primitives="requiresDefined (13.1); unknown (8.1); never invent (5.6)",
        expected="BLOCK",
        rationale="The sustainability conclusion depends on alignment, which "
                  "is unknown. The vocabulary shift is the whole failure.",
        requires=["claim.taxonomy.eligible-revenue-share",
                  "claim.taxonomy.aligned-revenue-share"],
        scope=GROUP_SCOPE,
    ),
    dict(
        n="04", slug="system-boundary-process-to-whole-product",
        category="environmental claim",
        title="System boundary: a process saving becomes a whole-product claim",
        source="Manufacturing the recycled input material results in a 62% "
               "saving in carbon emissions compared with virgin raw material.",
        supported="The 62% saving applies to the input-material manufacturing process.",
        requested="This product has 62% lower carbon emissions.",
        primitives="Brand State unknown (8.1); requiresDefined (13.1)",
        expected="BLOCK",
        rationale="No whole-product lifecycle figure exists. The retrieved "
                  "number is right; the system boundary it is applied to is not.",
        requires=["claim.recycled-input.whole-product-carbon-reduction"],
        scope=PLA_SCOPE,
    ),
    dict(
        n="05", slug="entity-scope-mismatch",
        category="numerical achievement",
        title="Entity scope: a group KPI applied to a non-consolidated entity",
        source="The subsidiary was not consolidated in fiscal year 2025 and is "
               "generally excluded from group KPIs.",
        supported="84.6% of consolidated group revenue was taxonomy-eligible.",
        requested="84.6% of the subsidiary's revenue was taxonomy-eligible.",
        primitives="Scope (9); element applicability (10.1)",
        expected="BLOCK",
        rationale="The element does not apply to this entity scope. Retrieval "
                  "has no notion of which legal entity a KPI covers.",
        requires=["claim.taxonomy.eligible-revenue-share"],
        scope={"brands": "entity-subsidiary", "outputTypes": "marketing-copy"},
    ),
    dict(
        n="06", slug="validity-period-asof-mismatch",
        category="validity period",
        title="Validity period: a fiscal-year KPI presented as a current fact",
        source="The disclosure covers 2025-01-01 to 2025-12-31.",
        supported="84.6% of fiscal-year 2025 revenue was taxonomy-eligible.",
        requested="84.6% of our revenue is taxonomy-eligible. (stated in August 2026)",
        primitives="asOf and validity half-open interval (10.1)",
        expected="BLOCK",
        rationale="The element is not valid at the build asOf timestamp. The "
                  "tense change is the whole failure.",
        requires=["claim.taxonomy.eligible-revenue-share"],
        scope=GROUP_SCOPE,
        as_of=AS_OF_AFTER_PERIOD,
    ),
    dict(
        n="07", slug="assurance-scope-mismatch",
        category="required qualification",
        title="Assurance scope: report-level assurance projected onto an excluded disclosure",
        source="Progress against greenhouse-gas reduction targets is explicitly "
               "excluded from the limited assurance conclusion.",
        supported="An independent limited assurance report exists for the "
                  "disclosure as a whole, with named exclusions.",
        requested="Our independently assured 61% Scope 3 reduction progress "
                  "demonstrates our leadership.",
        primitives="Brand State not_applicable (8.1); requiresDefined (13.1)",
        expected="BLOCK",
        rationale="Assurance for this specific disclosure is not_applicable. "
                  "Report-level assurance is not disclosure-level assurance.",
        requires=["claim.scope3.target", "evidence.assurance.scope3-progress"],
        scope=GROUP_SCOPE,
    ),
    dict(
        n="08", slug="disclosure-outside-assurance-presented-as-assured",
        category="required qualification",
        title="Disclosure outside limited assurance presented as assured",
        source="The transition plan and the actions disclosure are outside the "
               "assurance conclusion.",
        supported="The limited assurance conclusion names its exclusions.",
        requested="Our transition plan is independently assured.",
        primitives="requiresDefined (13.1); element absent (10.3)",
        expected="BLOCK",
        rationale="No element governs assurance of the transition plan, so the "
                  "build fails closed rather than borrowing the report-level one.",
        requires=["evidence.assurance.transition-plan"],
        scope=GROUP_SCOPE,
    ),
    dict(
        n="09", slug="missing-evidence-dependency",
        category="certification or rating",
        title="Missing evidence dependency: a claim whose evidence element is absent",
        source="A claim is usable only when its required evidence is valid for "
               "the same scope (17.1).",
        supported="The process claim is backed by process data.",
        requested="This product line is certified climate neutral.",
        primitives="Claims and Evidence Profile (17.1, 17.2); requiresDefined (13.1)",
        expected="BLOCK",
        rationale="The required evidence element does not exist. A certification "
                  "claim without a certification artefact must not build.",
        requires=["claim.recycled-input.process-emissions",
                  "evidence.product-line-a.climate-neutral-certificate"],
        scope=PLA_SCOPE,
    ),
    dict(
        n="10", slug="conflicting-competing-truth",
        category="numerical achievement",
        title="Conflicting source: two incomparable elements govern one subject",
        source="A second, differently scoped statement of the same KPI is "
               "introduced to simulate a competing internal source.",
        supported="Exactly one governed value per subject and scope.",
        requested="Publish the taxonomy-eligible revenue share.",
        primitives="Semantic subject (8.0); precedence and hard conflict (10.2)",
        expected="BLOCK",
        rationale="Two incomparable maximal elements are a hard conflict. "
                  "Retrieval would rank one of them and answer confidently.",
        requires=["claim.taxonomy.eligible-revenue-share"],
        scope=GROUP_SCOPE,
        variant="conflict",
    ),
    dict(
        n="11", slug="required-truth-explicitly-unknown",
        category="historical status",
        title="Required truth not_defined, and it does not substitute",
        source="Waste collection covers the entity's own sites only, not the "
               "full value chain.",
        supported="1,240 t of waste, 806 t recycled, within the reported boundary.",
        requested="We recycle 65% of waste across our value chain.",
        primitives="Brand State not_defined (8.1); no inference (5.6)",
        expected="BLOCK",
        rationale="The value-chain rate is not_defined and must not be inferred "
                  "from the site-level rate.",
        requires=["claim.waste.value-chain-recycling-rate"],
        scope=GROUP_SCOPE,
    ),
    dict(
        n="12", slug="allow-faithful-taxonomy-claim",
        category="numerical achievement",
        title="ALLOW: the faithful claim, correctly scoped and dated",
        source="84.6% of consolidated fiscal-year 2025 revenue was taxonomy-eligible.",
        supported="Same.",
        requested="84.6% of the group's consolidated revenue in fiscal year 2025 "
                  "was taxonomy-eligible.",
        primitives="requiresDefined (13.1); scope (9); asOf (10.1)",
        expected="ALLOW",
        rationale="Positive control. A system that blocks everything must not "
                  "pass this benchmark.",
        requires=["claim.taxonomy.eligible-revenue-share",
                  "evidence.taxonomy.turnover-kpi"],
        scope=GROUP_SCOPE,
    ),
    dict(
        n="13", slug="allow-process-claim-at-its-boundary",
        category="environmental claim",
        title="ALLOW: the process claim stated at its real system boundary",
        source="Manufacturing the recycled input material results in a 62% "
               "saving in carbon emissions compared with virgin raw material.",
        supported="Same.",
        requested="Manufacturing the recycled input material results in a 62% "
                  "saving in carbon emissions compared with virgin raw material.",
        primitives="requiresDefined (13.1); scope (9); evidence (17.2)",
        expected="ALLOW",
        rationale="Positive control. The same number that is blocked in case 04 "
                  "is allowed when the boundary is stated.",
        requires=["claim.recycled-input.process-emissions",
                  "evidence.recycled-input.process-data"],
        scope=PLA_SCOPE,
    ),
    dict(
        n="14", slug="adversarial-under-declared-target",
        category="required qualification",
        title="ADVERSARIAL: an under-declared target that requires nothing the "
              "false claim depends on",
        source="Section 13.1: a target name or description MUST NOT imply a "
               "capability that its declared requirements cannot support.",
        supported="84.6% of fiscal-year 2025 revenue was taxonomy-eligible.",
        requested="85% of our products are environmentally sustainable, "
                  "requested through a target that only requires the brand name.",
        primitives="Target requirements (13.1) — normative but not mechanically "
                   "enforceable",
        expected="ALLOW",
        rationale="OBDS builds successfully and the false claim is NOT caught. "
                  "This is the boundary of the mechanism, kept in the benchmark "
                  "on purpose. OBDS can determine whether declared requirements "
                  "are satisfied. It cannot prove that every relevant "
                  "requirement has been discovered and modelled.",
        requires=["structure.brand"],
        scope=GROUP_SCOPE,
        style="none",
    ),
]

CONFLICT_ELEMENT = [
    el("claim.taxonomy.eligible-revenue-share.competing",
       subject="claim.taxonomy.eligible-revenue-share",
       state="defined",
       scope={"outputTypes": ["marketing-copy"]},
       validity={"from": FY25_FROM, "to": FY25_TO},
       sources=["Competing internal summary, executive deck"],
       value={
           "canonicalWording": "85% of the portfolio was classified as "
                               "taxonomy-eligible.",
           "claimType": "environmental",
           "riskLevel": "regulated",
           "conditions": [],
       }),
]


def emit():
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    base = base_manifest()
    conflict = base_manifest(CONFLICT_ELEMENT)
    written = []
    for c in CASE_DEFS:
        d = CASES_DIR / f"{c['n']}-{c['slug']}"
        d.mkdir(parents=True, exist_ok=True)
        m = conflict if c.get("variant") == "conflict" else base
        target = f"case-{c['n']}"
        tscope = {k: [v] for k, v in c["scope"].items()}
        style = c.get("style", "selected")
        plan = build_plan(target, c["requires"], tscope,
                          as_of=c.get("as_of", AS_OF_IN_PERIOD), manifest=m,
                          style=style)
        (d / "manifest.json").write_text(json.dumps(m, indent=2) + "\n")
        (d / "build-plan.json").write_text(json.dumps(plan, indent=2) + "\n")
        written.append(d)
    return written


def decision(exit_code, artefacts):
    """A build that produces a context artefact is an ALLOW. Anything else is a BLOCK."""
    produced = any(a.endswith(".context.json") for a in artefacts)
    return "ALLOW" if exit_code == 0 and produced else "BLOCK"


def run():
    written = emit()
    results = []
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO / "reference" / "foundation" / "src")
    for c, d in zip(CASE_DEFS, written):
        out = d / "out"
        proc = subprocess.run(
            [sys.executable, "-m", "obds_ref.cli", "build",
             str(d / "manifest.json"), str(d / "build-plan.json"),
             "--out", str(out)],
            capture_output=True, text=True, env=env, cwd=str(REPO))
        artefacts = sorted(p.name for p in out.rglob("*")) if out.exists() else []
        actual = decision(proc.returncode, artefacts)
        results.append({
            "case": c["n"], "slug": c["slug"], "title": c["title"],
            "category": c["category"],
            "expected": c["expected"],
            "actual": actual,
            "match": actual == c["expected"],
            "exitCode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip()[:2000],
            "artefacts": artefacts,
        })
    (HERE / "raw-results.json").write_text(json.dumps(results, indent=2) + "\n")
    write_reports(results)
    for r in results:
        flag = "ok " if r["match"] else "MISMATCH"
        print(f"{r['case']}  expected={r['expected']:<5} actual={r['actual']:<5} "
              f"{flag}  {r['slug']}")
    print(f"\n{sum(1 for r in results if r['match'])}/{len(results)} cases "
          f"match their expected governed decision.")
    return results


def write_reports(results):
    by_n = {r["case"]: r for r in results}
    rows = ["| # | Category | Case | Expected | Actual | Match |",
            "|---|---|---|---|---|---|"]
    for c in CASE_DEFS:
        r = by_n[c["n"]]
        rows.append(f"| {c['n']} | {c['category']} | {c['title']} | "
                    f"{r['expected']} | {r['actual']} | "
                    f"{'yes' if r['match'] else 'NO'} |")
    (HERE / "results-table.md").write_text("\n".join(rows) + "\n")

    for c in CASE_DEFS:
        r = by_n[c["n"]]
        d = CASES_DIR / f"{c['n']}-{c['slug']}"
        md = f"""# Case {c['n']} — {c['title']}

**Category:** {c['category']}

## Source statement (governed truth)

{c['source']}

## What the governed model supports

{c['supported']}

## What the communication request asks for

> {c['requested']}

## OBDS primitives exercised

{c['primitives']}

## Expected governed decision

{c['expected']}

{c['rationale']}

## Actual governed decision

**{r['actual']}** (compiler exit code {r['exitCode']}; \
artefacts produced: {', '.join(r['artefacts']) if r['artefacts'] else 'none'})

## Reproduce

```bash
PYTHONPATH=reference/foundation/src python -m obds_ref.cli build \\
  research/governed-communications-benchmark/cases/{c['n']}-{c['slug']}/manifest.json \\
  research/governed-communications-benchmark/cases/{c['n']}-{c['slug']}/build-plan.json \\
  --out /tmp/obds-case-{c['n']}
```
"""
        (d / "case.md").write_text(md)


if __name__ == "__main__":
    run()
