# Contributing

Contributions are welcome. The bar is deliberately different for the two kinds of
change.

## Two kinds of change

**Editorial, tooling and documentation.** Typos, unclear prose, broken links,
example fixes, additional tests, tooling improvements. Open a pull request. No
proposal needed.

**Normative.** Anything that changes what an implementation must do: schema
fields, states, precedence, conformance requirements, capability semantics.
Start with a proposal, not a pull request.

## Proposing a normative change

Add a note to `proposals/`, named `OBDS-<target>-<TOPIC>.md`, marked
`Status: PROPOSAL / UNRATIFIED`, answering:

1. What problem does this solve, with a concrete case that fails today?
2. Why can it not be solved with what already exists?
3. What is the migration impact for existing manifests and implementations?
4. What tests would prove it works, and what tests would prove it did not break
   anything?

A proposal that cannot answer 3 and 4 is not ready. Nothing in `proposals/` is
part of a release, and adding a note is not a commitment to ship it.

See [`GOVERNANCE.md`](GOVERNANCE.md) for how a proposal becomes a release.

## Ground rules for the specification

These are the constraints a change has to respect, not preferences:

- **Unknown stays unknown.** No change may let a system infer a value for
  something the brand has not defined.
- **Fail closed.** When required truth is missing, ambiguous or in conflict, the
  build stops. A change that turns a failure into a warning needs a very good
  argument.
- **Prohibition is a Rule**, not a state. The four Brand States describe
  knowledge status only.
- **Guidance is not compliance.** Qualitative direction must not silently become
  a blocking checklist.
- **No layout coordinates in Brand Truth.** OBDS declares the permissible design
  space; the renderer produces a solution inside it.
- **The Foundation stays small.** New capability goes into an optional capability,
  not into the required base.

## Running the suite

The repository root is the package root, so a clone is directly runnable:

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python reference/run_all.py        # 429 passed, 0 failed, 0 skipped
.venv/bin/python reference/release-gate.py   # metadata, contract identity, licences, junk
```

Node.js 21 or later must be on `PATH`. That order needs no cleanup step: the
gate treats `__pycache__`, `.pytest_cache`, `*.pyc` and a local `.venv` as
generated caches, not as package junk.

Before opening a pull request, also run:

```bash
python3 tools/docs-smoke-test.py
```

It executes every command documented in `README.md`, `CONTRIBUTING.md` and
`examples/README.md`. If you change a documented command, change it there too.

A pull request that touches the implementation layer has to keep all three
green. Zero skipped cases is part of the gate, not a nice-to-have.

If you changed a file that ships in the release archive, regenerate the manifest
and the archive, or the release gate will fail on a stale hash:

```bash
python3 tools/build-release.py
```

## Licensing of contributions

Inbound equals outbound. By contributing you agree that your contribution is
licensed under the licence that already covers the material you changed:

- specification and documentation: **CC BY 4.0**
- schemas, tests, reference implementation and examples: **Apache License 2.0**

Apache 2.0 section 5 governs contributions to the implementation layer. There is
no separate contributor agreement to sign and no copyright assignment.

Do not contribute material you do not have the right to license, and do not paste
in text from another standard or another codebase without saying where it came
from and under what licence.

## Reporting a problem

Specification defects, schema defects and reproducible test failures:
lets@killthedragon.com, or an issue on the repository.

For a security-relevant defect in the reference implementation, write to the
address above first rather than opening a public issue.
