# Proposed normative delta

Status: proposed requirements; no current OBDS file is changed.

1. Add one optional runtime capability, proposed ID `task-facts`. Implementations MAY implement it; existing Foundation and other capability claims MUST NOT require it. A claim MUST identify the exact adopted revision and payload/canonicalization profiles. Until adoption, candidate-v1 identifies a proposal only.
2. Include TASK-FACTS-CONTRACT.md and its schema as the evaluator contract. A claimant MUST implement all required types, states, operators, stages, reasons and hashes. Partial support MUST NOT be called full Task Facts conformance.
3. Preserve v0.2 evaluation semantics and snapshot 0.1 identities. Consumers MUST NOT rewrite payload versions, silently replace TFJ with OBDS canonicalization, or substitute snapshotHash for an existing governed hash.
4. Consumers MUST retain the exact snapshot, conditions, verifier context and decisions. Condition IDs alone are not immutable rule versions. UNKNOWN, CONTRADICTORY and INVALID MUST remain unresolved and MUST NOT grant permission. A trusted host MUST supply verificationContext independently of the task caller; verified labels alone are insufficient.
5. Add the separately tested evaluator claim in CONFORMANCE-IMPACT.md. Existing official profile requirements remain unchanged.

No delta is proposed to manifest elements, Brand States, Scope matching, subject precedence, requiresDefined's exact-element meaning, Value Contracts, Build Plans, Model Input Packages, Runtime Decision Records, build reports, or existing governed hashing. No new fields are inserted into them. A false condition MUST NOT remove an existing static requirement.

Host adapter discussion is informative compatibility guidance. No automatic build adapter, registry wire field, signature protocol or integrated production conformance is standardized. Any future official wire binding requires separate schema review and integration evidence; this proposal reserves no fields in closed schemas.
