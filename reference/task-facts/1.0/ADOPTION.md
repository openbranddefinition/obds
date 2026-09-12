> **Status: published.** Task Facts 1.0 became a published, optional OBDS capability with OBDS 4.1.0 on 9 September 2026 and is unchanged in every later release. This file is the adoption record and is kept as it was written before that publication: "prospective" and "internal candidate" below describe the state at the time of adoption, not the current one, and its file references name the 4.1.0 artefacts. The current specification and result files are linked from [README.md](README.md). No production integration is claimed; every published Task Facts conformance result carries `productionIntegration: false`.

# Prospective OBDS 4.1.0 adoption of optional Task Facts 1.0

Internal candidate, not published. Adoption becomes effective only on authorized OBDS 4.1.0 publication; no current public status is changed here.

OBDS 4.1.0 adopts the identified Task Facts contract and schema as the optional Task Facts 1.0 evaluator capability. Experimental titles, URNs and proposal status in the retained source record its provenance. They do not require rewriting payloads or change the adoption established here. Snapshot contractVersion remains 0.1; canonicalization remains TFJ-0.1. Existing OBDS governed hashes and Core conformance are unchanged.

The complete normative definitions, algorithms and requirements of TASK-FACTS-CONTRACT.md sections 1–8, NORMATIVE-DELTA.md and the proposed normative requirements of CONFORMANCE-IMPACT.md are materialised in [the single root specification, section 35](../../../../OBDS-4.1.0.md#35-optional-task-facts-10-normative-requirements), with conformance claims in section 26.10. Authority resides in that single current specification and its identified structural schema. This wrapper is an informative adoption and provenance guide. Non-root contract/proposal copies remain byte-identical provenance and evidence, not independently authoritative second specifications. The root section supersedes only source adoption-status wording for the identified normative requirements; research, hypothetical hosts, examples, provenance, supporting reviews and historical claims remain informative.

| Identity | Retained value |
| --- | --- |
| OBDS release | 4.1.0, prospective MINOR from 4.0.4 |
| Optional capability | Task Facts 1.0 / task-facts |
| Snapshot payload | contractVersion 0.1 |
| Canonicalization | TFJ-0.1 |
| Schema identity | urn:task-facts-experiment:0.2:schema |
| Suite | task-facts-1.0 revision 1; derived raw-inventory suiteHash in separate conformance result |
| Contract raw SHA-256 | a92b5a1de66365c81543d939d104975c5ee139d6b7396f532bbd0a1163014046 |
| Schema raw SHA-256 | acaa7a2157e9e5788cefd9f7b96d4f04e18d7b263119016c872ae316646d7646 |
| NORMATIVE-DELTA raw SHA-256 | 00558367da90281fff8bcfe53e9356ff5190b9f8072d9247205608c7bac21589 |
| CONFORMANCE-IMPACT raw SHA-256 | fe12b7413fa397b7e2a93f2a2a3474fa4b105d2fe3e1199276ba83f53d87b6f8 |

The companion OBDS-4.1.0-TASK-FACTS-SCHEMA-INDEX.json maps the preserved URN to local and public retrieval paths. Retrieval URL is not schema $id. `contract/schemas/task-facts.schema.json` is a second byte-identical copy preserving the frozen contract's relative link. Both work offline without a symlink.

Full support requires prose and schema together, all 66 fixture and 36 regression records, suite and implementation identity, exact six-field results and zero skipped/failed cases. Schema-only and partial support cannot claim full conformance. The repository registry advertises optional availability and does not claim compiler integration.

Existing valid 4.0.4 packages need no migration, installation, lookup, preflight or invocation. No new manifest, Build Plan, MIP, RDR or build-report fields are introduced. Consumers retain exact snapshots, conditions, host-supplied verifier contexts and decisions. Presence and accepted hashes do not prove truth. UNKNOWN, CONTRADICTORY and INVALID never grant permission; false conditions cannot remove static requirements. Trusted verifier boundary, artifact/package rebinding, retention and compiler/runtime integration require a separate review before any production integration claim.

Raw provenance is in [EVIDENCE-README.md](EVIDENCE-README.md), which distinguishes non-public immutable audit trees from public fresh reports and runnable source dependencies. This is tested-set interoperability, not exhaustive proof, certification, rights/legal verification or production readiness.
