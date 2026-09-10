# OBDS 4.1.1 migration

Existing valid 4.0.4 packages require no migration. All prior schemas, governed hashes, Foundation and existing capability obligations retain their meaning. Existing consumers can continue without installing or invoking Task Facts.

Voluntary Task Facts evaluator implementers read [the complete adopted prose and schema](reference/task-facts/1.0/ADOPTION.md), preserve raw transport and run the exact optional suite. Publish implementation/version, suiteHash, all ordered six-field results and limitations. Partial and schema-only support cannot claim full conformance. Do not insert sidecars in closed schemas, rename contractVersion 0.1 or replace governed identities with TFJ-0.1 hashes.

Retain exact snapshots, conditions, verifier contexts and decisions outside existing governed objects. Future production adapters require separate review, including trusted verification, rebinding, retention and static/selected dependencies. No production integration conformance is introduced.
