# OBDS implementer experience: a note on tooling

    Status:      NOTE / NON-NORMATIVE
    Applies to:  tooling and developer experience
    Normative:   no
    Roadmap:     none. No release date is implied or committed.
    Author:      Kill The Dragon GmbH
    Date:        2026-08-28

This note records an implementation principle and sketches the tooling shape it
suggests. It proposes no change to OBDS 1.0.1 and no change to any published
contract. Companion note: `OBDS-1.1-PROGRESSIVE-COMPLEXITY.md`.

---

## The principle

**Start with Foundation. Add only the capabilities you need.**

This is already section 4.2 of the specification. What is missing is not the
principle but the path of least resistance. Today the shortest route to a first
working implementation runs through a 27-schema package, and a first-time
implementer has to decide, unaided, which of those schemas are irrelevant to
them. Most of them usually are.

The structural complexity of OBDS is real and is doing real work. The point is
that an implementer should not have to face all of it on day one in order to
find out whether the standard is worth their time.

## What tooling should do

Hide structural complexity behind a command. Do not remove governance from the
standard.

The distinction matters, because the obvious way to make OBDS approachable is
also the wrong one: publish a reduced dialect that drops conflict handling,
`asOf` or fail-closed behaviour. That would produce something easy to adopt and
worthless to rely on, and it would split the format. Tooling can make the same
surface reachable in stages without weakening any of it.

Three concrete jobs:

1. **Generate the smallest correct starting point.** A valid Foundation-only
   manifest, with `profiles: [obds-foundation]` and nothing else.
2. **Report only what is relevant.** Validation output scoped to the profiles
   and capabilities actually declared, rather than to the full release package.
3. **Make the next step visible.** When an implementer's data starts to need a
   capability, say so, name it, and say what it costs.

## Possible commands

Sketches. Names are illustrative and nothing here is committed.

```
obds init
```

Creates a minimal, valid Foundation manifest and the smallest useful directory
layout. No optional profiles. No runtime configuration. The generated artefact
should be readable end to end in under a minute.

```
obds validate
```

Validates a manifest against Foundation plus exactly the profiles it declares.
Errors name the element, its subject and its scope. Unsupported declared
profiles are an error, never a silent skip. Nothing that is not declared is
checked, and nothing that is declared is skipped.

```
obds build
```

Compiles a Build Plan into a Compiled Brand Context for a declared target and
`asOf`. Stops on missing required truth, on ambiguity and on conflict, and says
which element and which subject caused it. Stopping early is the behaviour, not
an inconvenience to be flagged away.

```
obds inspect
```

Explains a resolution. For a given subject, target and moment: which candidates
existed, which scope won, why, what was omitted and with what reason. This is
the command that turns precedence from a specification concept into something
an implementer can see happening.

## What tooling must not do

- Emit a manifest that would not validate.
- Guess a value for an element in the `unknown` state.
- Downgrade a conflict to a warning to keep a build green.
- Introduce configuration that changes governed semantics.
- Add a manifest field, a state or a capability of its own.
- Present a subset of OBDS as a separate or simpler specification.

Tooling output is convenience. It is not Brand Truth, and it never becomes a
second place where brand truth is decided.

## Relationship to the bundle proposal

The bundle names explored in `OBDS-1.1-PROGRESSIVE-COMPLEXITY.md` would give
these commands a natural vocabulary, for example a flag selecting the Governed
Context capability set instead of naming three identifiers. That is a
convenience for the command line and nothing more. The commands sketched here
work identically without bundles, using capability identifiers directly, and
should be designed on that assumption.

## Status

No commitment is made to build any of this, and no release date is implied.
The note exists so that the principle is written down where an implementer can
find it, and so that a future tooling effort starts from the right constraint:
make the first step small, and leave the governance intact.
