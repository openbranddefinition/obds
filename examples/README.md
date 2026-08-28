# Examples

Two minimal, runnable examples. Both are Foundation only, and both are verified
against the reference implementation shipped in the release package.

Licensed under the Apache License 2.0. See [`../LICENSE.md`](../LICENSE.md).

## Running them

From the unpacked release package root, with the reference implementation on the
path:

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
export PYTHONPATH=reference/foundation/src
.venv/bin/python -m obds_ref.cli validate examples/foundation-minimal/manifest.yaml
.venv/bin/python -m obds_ref.cli build \
  --manifest examples/foundation-minimal/manifest.yaml \
  --plan examples/foundation-minimal/build-plan.yaml \
  --out /tmp/obds-out
```

## `foundation-minimal/`

The smallest thing that is a valid OBDS implementation.

One manifest declaring `obds-foundation` and nothing else. One element,
`structure.brand`, a `brand-identity` fact in state `defined`, with its value
contract pinning the shape hash, the schema reference and the schema hash. One
build plan with one target that requires that element to be defined.

It compiles:

```
status             ready
artifactRef        brand-query-global-en.context.json
artifactHash       valid, and reproducible across runs
requirements       structure.brand  defined  pass
```

There is no Compiled Runtime configuration, no Context Delivery, no Context
Assembly, no Composition and no Visual Operations. This is the whole minimum.

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
