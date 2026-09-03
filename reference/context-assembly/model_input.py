"""Section 15.10 / 26.2: the one deterministic Model Input renderer.

Until 3.0.0 the rendering lived only in the Context Assembly package, and the
runtime accepted the rendered text as a parameter. That left the audit anchor
open in a way no hash could close: the runtime verified `modelInputHash` against
the text it was handed and `package.slots.taskInput` against the preflight
argument — two pairs, not a chain. Nothing tied the rendered text to the slots
it claimed to render.

The attack that follows is not subtle. Change the `[TASK_INPUT]` block inside the
rendered text, recompute `modelInputHash` and `assemblyHash`, leave the package
slot and the preflight argument benign, and every check the runtime performs
passes while the model receives text that was never checked:

    decision released · model called True · blocked text reached model True

The capsule states the invariant as three equal things, not two pairs:

    preflight task input = package.slots.taskInput = rendered [TASK_INPUT] bytes

A chain needs one renderer that both ends agree on, so the renderer lives here,
in Foundation, and the assembler imports it. It is copied verbatim next to each
flat package's `canonical.py` and `governed_io.py`, under the same rule: the
release gate asserts every copy is byte-identical, so the two ends cannot drift
apart.

The module is a leaf. It imports nothing from the project.
"""

from __future__ import annotations

from typing import Any, Mapping

# The slot order is part of the rendering, so it is part of the contract. A
# renderer that emits the same slots in a different order produces different
# bytes and therefore a different `modelInputHash`, which is the point.
SLOT_ORDER = [
    ("HARD_BOUNDARIES", "hardBoundaries"),
    ("FACT_GROUNDING", "factGrounding"),
    ("STATE_MAP", "stateMap"),
    ("GUIDANCE_CONTEXT", "guidanceContext"),
    ("TASK_INPUT", "taskInput"),
]

SLOT_KEYS = tuple(key for _, key in SLOT_ORDER)


class ModelInputContractError(ValueError):
    """The package's slots cannot be rendered, so nothing may be sent."""


def render_model_input(slots: Mapping[str, Any]) -> str:
    """Render the Model Input Package's slots. Deterministic, total, or refuse.

    Refusing rather than defaulting matters here for the same reason it matters
    for compiled check parameters: a missing slot that renders as an empty
    string is a governed decision made by whichever implementation happened to
    render it.
    """
    if not isinstance(slots, Mapping):
        raise ModelInputContractError("model input slots must be an object")
    missing = [key for key in SLOT_KEYS if key not in slots]
    if missing:
        raise ModelInputContractError("model input slots are incomplete: " + ", ".join(missing))
    unknown = [key for key in slots if key not in SLOT_KEYS]
    if unknown:
        raise ModelInputContractError("model input slots carry unknown keys: " + ", ".join(sorted(unknown)))
    for key in SLOT_KEYS:
        if not isinstance(slots[key], str):
            raise ModelInputContractError(f"model input slot {key} must be a string")
    return "\n\n".join(f"[{label}]\n{slots[key]}" for label, key in SLOT_ORDER)
