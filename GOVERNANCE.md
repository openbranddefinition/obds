# Governance

Open Brand Definition is published by Kill The Dragon GmbH, Vienna. This document
says how decisions are made and how the specification changes. It is short on
purpose.

## Current state

The project is maintained by its publisher. There is no foundation, no steering
committee and no vendor council. Saying so plainly is more useful than describing
a governance structure that does not exist yet.

What the publisher commits to instead:

- the specification and the implementation layer are under standard open licences
  (see [`LICENSE.md`](LICENSE.md)), so the work cannot be withdrawn from anyone
  who already has it;
- normative changes are published with a changelog, a migration note and tests;
- a released version is never edited in place.

## Versioning

OBDS follows semantic versioning at the level of the normative contract.

- **PATCH** (1.0.1, 1.0.2, 1.0.3): licensing, packaging, documentation, developer
  experience and editorial
  changes. No normative contract changes. The public schema surface stays
  byte-identical, and every schema `$id` keeps resolving at the same address.
- **MINOR** (1.1.0): a backwards-compatible capability, profile or optional
  field. Existing manifests stay valid, and existing implementations stay
  conforming for what they already claim.
- **MAJOR** (2.0.0): breaking semantics. Required for any change that would
  reinterpret an existing 1.0 field.

Two version numbers exist and they are not the same thing. The **release
version** identifies the package. The **schema contract version** identifies the
data contract, and it is `1.0.0` for the whole 1.0 line. A patch release does not
move the schema contract.

## Frozen releases

A published release directory is never modified. `spec/1.0.0/` and `spec/1.0.1/`
stay exactly as released, including their hashes, their test outputs and the
licensing wording that was current at the time.

Where a released document has been superseded, the current release says so. The
old document is not rewritten to agree with the new one.

## How a change gets made

1. **Proposal.** A non-normative note in `proposals/`, marked
   PROPOSAL / UNRATIFIED, stating the problem, the options and the migration
   impact. Anyone may open one. See [`CONTRIBUTING.md`](CONTRIBUTING.md).
2. **Discussion.** In the open, on the proposal.
3. **Decision.** By the publisher, recorded in the proposal.
4. **Implementation.** Specification text, schemas, tests and migration notes
   land together. A normative change without a test does not land.
5. **Release.** The release gate has to pass, and the conformance suite has to be
   green with zero skipped cases.

An idea that is accepted in principle but not scheduled stays in `proposals/` as
an unratified note. Nothing in `proposals/` is part of any release.

## Conformance

Conformance is tested, not declared. An implementation may say it uses OBDS
concepts at any time. It may say it is OBDS conformant once the official suite
for that exact version and the capabilities it claims runs green, and the result
is retained and reproducible.

No certification programme is live, and no badge exists. See
[`TRADEMARKS.md`](TRADEMARKS.md).

## If the publisher stops

The licences are irrevocable for material already published. Anyone may fork the
specification and the implementation layer under CC BY 4.0 and Apache 2.0, and
continue the work under a different name. See `TRADEMARKS.md` for what a fork may
call itself.

## Contact

lets@killthedragon.com
