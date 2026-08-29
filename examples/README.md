# Examples

Two minimal, runnable examples, both verified against the reference
implementation shipped in the release package.

Both carry the smallest possible Foundation manifest and then exercise
**Compiled Runtime** on top of it. The manifest, its element, the four Brand
States and the value contract are Foundation, section 26.1. The build plan,
`requiresDefined`, the produced or withheld Compiled Brand Context and the
`build` command itself are Compiled Runtime, section 26.2. The directory is
named `foundation-minimal` for the manifest it holds, not because `build` is a
Foundation operation.

Licensed under the Apache License 2.0. See [`../LICENSE.md`](../LICENSE.md).

## Running them

The repository root is the package root. From a clone:

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
export PYTHONPATH=reference/foundation/src
.venv/bin/python -m obds_ref.cli validate examples/foundation-minimal/manifest.yaml
.venv/bin/python -m obds_ref.cli build examples/foundation-minimal/manifest.yaml examples/foundation-minimal/build-plan.yaml --out /tmp/obds-out
```

`build` takes the manifest and the build plan as positional arguments, in that
order. `--out` is the only option.

The fail-closed example runs the same way and is supposed to fail:

```bash
.venv/bin/python -m obds_ref.cli build examples/fail-closed/manifest.yaml examples/fail-closed/build-plan.yaml --out /tmp/obds-fail
```

It exits `2`, writes `build-report.yaml` and writes no Compiled Brand Context.

Both examples are also conformance cases. `reference/foundation/tests/test_examples.py`
asserts exactly the behaviour documented below, so an example that drifts from
the reference implementation fails the suite.

## `foundation-minimal/`

The smallest runnable example: one manifest, one element, one target.

One manifest declaring `obds-foundation` and nothing else. One element,
`structure.brand`, a `brand-identity` fact in state `defined`, with its value
contract pinning the shape hash, the schema reference and the schema hash. That
much is Foundation. One build plan with one target that requires that element to
be defined, which is Compiled Runtime.

It compiles:

```
status             ready
artifactRef        brand-query-global-en.context.json
artifactHash       valid, and reproducible across runs
requirements       structure.brand  defined  pass
```

The manifest is the whole Foundation minimum: one element and its value
contract, nothing else. Beyond the single build target there is no Context
Delivery, no Context Assembly, no Composition and no Visual Operations.

## `fail-closed/`

The same shape, with one difference that changes the outcome.

The manifest carries a second element, `context.efficacy-claim`, in state
`unknown`. The brand expects a value there and does not have one. The build plan
target requires both elements to be defined.

The build fails, and that is the correct result:

```
status             failed
artifactRef        None
context files      none written
requirements       structure.brand         defined  pass
                   context.efficacy-claim  unknown  fail
error              OBDS-BUILD-REQUIRED-NOT-DEFINED
```

No Compiled Brand Context exists, so there is nothing to assemble a model input
from, so no model is called:

```
model calls        0
decision           build_failed
```

The unknown element is never guessed, never widened to a neighbouring scope and
never quietly dropped to let the build succeed. It carries no `value` key at all,
because a non-defined state must not carry one.

This is what "fail closed" means in OBDS: the absence of required truth stops the
process before generation, rather than producing fluent output from an assumption
nobody approved.

The guarantee belongs to Compiled Runtime. Section 26.2 is what requires "no
artefact for a failed target" and "zero instrumented model calls after a failed
build". Foundation supplies the truth this gate reads — the element, its state
`unknown` and the rule that a non-defined state carries no value — but a
Foundation-only implementation does not run the gate.
