# Optional Task Facts / Conditional Applicability proposal

Candidate-v1, 2026-09-08. PROPOSED FOR INDEPENDENT REVIEW. This package does not ratify, modify or release OBDS.

Recommend the proven evaluator as an optional runtime contract, proposed capability ID `task-facts`, designation `Task Facts 1.0` only upon approval. These names are not currently registered. Preserve snapshot payload 0.1 and TFJ-0.1: changing them would invalidate existing wire identities and require renewed interoperability evidence.

The problem is the portable handoff from verified observations about a concrete artifact/action to conditional applicability and selected governed dependencies. Multiple claims, assets, partner presence and campaign context must coexist without cross-attribution. Stable Brand Scope remains separate. Task-fact presence is not proof of truth; accepted digests bind observations but do not establish entitlement, legal truth or semantic completeness.

TASK-FACTS-CONTRACT.md and schemas/task-facts.schema.json fully specify the proposed normative evaluator. NORMATIVE-DELTA.md specifies the addition and boundaries. CONFORMANCE-IMPACT.md identifies proposed conformance requirements. Other documents are informative. The schema and canonical example/regression vectors retain their frozen bytes and experimental provenance; none is represented as currently official OBDS material.

Included capabilities are typed scalar/set facts, simultaneous facts, presence/absence, equality, membership, flat conjunction, missing/empty/unknown/contradictory distinctions, provenance/verification binding, limited partial-function associations, deterministic complete snapshot hashing, date/instant distinction, unresolved timezone preservation, and deterministic validation/routing/reasons.

Non-goals: generic policy languages, arbitrary boolean expressions, regex policy logic, arbitrary code, workflow engines, NLP claim detection, legal/rights truth engines, new brand ontology, Core redesign, general relations/joins, interval predicates and timezone databases. No authentication protocol, inventory extraction or production integration is proven. A false sibling never hides an unknown conjunction member.

The pinned published baseline is OBDS 4.0.4 at commit e3464b5f863897260118b6c338a1061e9382c845. The website and repository VERSION identify 4.0.4; GitHub releases/latest reports older v2.0.0 and was not used as the normative baseline. BASELINE-SOURCES.json records exact URLs and raw SHA-256 digests; baseline/ preserves inspected sources. Attribution: Open Brand Definition contributors, https://openbranddefinition.org/ and https://github.com/openbranddefinition/obds. Specification licensing is CC BY 4.0; implementation layer Apache 2.0. Baseline copies are unmodified. This proposal is new/adapted material, not a published OBDS release.

After the compatibility analysis in BACKWARD-COMPATIBILITY.md, recommend MINOR (prospectively 4.1.0 from this baseline). A new optional capability is more than a PATCH clarification. No existing normative contract changes, so MAJOR is unnecessary for this bounded addition. Mandatory adoption or changed existing hashes/semantics would require renewed version analysis.

Author recommendation: approve the bounded optional evaluator proposal for council consideration. This is not a reviewer/ratifier verdict. Official registration, conformance packaging and production adapter implementation remain separate governed work; adoption does not authorize publishing a release.
