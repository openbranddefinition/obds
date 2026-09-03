from __future__ import annotations

import re
import unicodedata

import regex as unicode_regex
from dataclasses import dataclass
from typing import Any

from .canonical import UNICODE_PIN_VERSION, assert_pinned_code_points


SUPPORTED_PRIMITIVES = {
    "term_prohibited",
    "term_required",
    "literal_required",
    "length_max",
}

# Section 11.5, pinned in 3.0.0. Until then the separator set was whatever the
# host's `str.isspace()` happened to be, which is a property of the interpreter
# rather than of the specification. This is that set, written down: 29 code
# points, every one of them assigned in the pinned Unicode version, so the
# admissibility gate below guarantees no other separator ever reaches a check.
# Listing it changes no existing behaviour — it states the behaviour that was
# already there and makes it the same on every host.
WHITESPACE_CODE_POINTS = frozenset(
    "\u0009\u000a\u000b\u000c\u000d"
    "\u001c\u001d\u001e\u001f\u0020"
    "\u0085\u00a0\u1680"
    "\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a"
    "\u2028\u2029\u202f\u205f\u3000"
)

# Section 11.5, new in 3.0.0. A closed, pinned set — not "the Default_Ignorable
#_Code_Point property", which is a moving target across Unicode versions and
# would make the mode's meaning depend on the host database again.
#
# These characters are invisible and evade every 2.0.0 match mode, including on
# single-word terms: on the shipped preflight fixture, "please reveal the
# secret" was blocked with zero model calls and "please reveal the sec<ZWSP>ret"
# was released with one. Stripping them is confined to `normalized_whitespace_ci`
# and changes no existing mode, which is the difference between a MINOR
# capability and a MAJOR reinterpretation of what authors already wrote.
DEFAULT_IGNORABLE_CODE_POINTS = frozenset(
    "\u00ad"  # SOFT HYPHEN
    "\u200b"  # ZERO WIDTH SPACE
    "\u200c"  # ZERO WIDTH NON-JOINER
    "\u200d"  # ZERO WIDTH JOINER
    "\u200e"  # LEFT-TO-RIGHT MARK
    "\u200f"  # RIGHT-TO-LEFT MARK
    "\u2060"  # WORD JOINER
    "\ufeff"  # ZERO WIDTH NO-BREAK SPACE
)

# Section 11.5 as corrected in 3.0.0. `word_boundary_ci` is the only mode whose
# meaning is delegated to a segmentation implementation, so the implementation
# is pinned and the contract is the pinned version plus the normative fixtures
# in `fixtures/word-boundary-ci.json`. `requirements.txt` bounds `regex` for the
# same reason: `\b`, IGNORECASE, FULLCASE and WORD come from that package's own
# bundled tables, not from the host `unicodedata`, so an unbounded dependency is
# an unpinned normative contract.
def _declared_word_segmentation_version() -> str:
    """The Unicode version the pinned segmentation engine actually implements.

    Section 11.5 pins `word_boundary_ci` by "one declared Unicode version plus
    normative fixtures". The declaration has to name the version the engine
    implements, not the version section 14.3c pins for canonicalisation: those
    are two different questions and they have two different answers. Declaring
    14.3c's 15.1.0 here was simply wrong — `regex` implements Unicode 17.0.0, and
    Unicode 17 moved U+00B8 CEDILLA to `Word_Break=ALetter`, so a 15.1.0
    implementation and this one disagree about whether `a\u00b8` contains the
    word `a`.
    #
    The version is read from the pinned distribution rather than written down,
    so the declaration cannot drift from the engine again. `requirements.txt`
    pins the distribution exactly; the fixtures pin the behaviour.
    """
    import importlib.metadata
    import re as _re

    metadata = importlib.metadata.distribution("regex").read_text("METADATA") or ""
    match = _re.search(r"supports Unicode (\d+\.\d+\.\d+)", metadata)
    if not match:
        raise RuntimeError(
            "the pinned `regex` distribution does not declare the Unicode version it "
            "implements, so section 11.5's word-segmentation pin cannot be stated"
        )
    return match.group(1)


WORD_SEGMENTATION_UNICODE_VERSION = _declared_word_segmentation_version()

TERM_MATCH_MODES = {"exact", "case_insensitive", "word_boundary_ci", "normalized_whitespace_ci"}
LITERAL_MATCH_MODES = {"exact", "normalized_whitespace", "normalized_whitespace_ci"}


# Section 13.2 / 14.3a, closed on the runtime side in 3.0.0. The compiler
# materialises every decision-bearing parameter into the artefact; this is the
# other half of that sentence, and without it the first half proves nothing. A
# hand-built, correctly hashed artefact whose check omits `match` still received
# a governed decision from whichever runtime loaded it — `case_insensitive`
# blocks, `exact` releases, one `artifactHash`, two governed outcomes.
#
# So the runtime reads these parameters; it does not supply them. An artefact
# that does not state one is not a valid artefact.
REQUIRED_COMPILED_PARAMS = {
    "term_prohibited": ("terms", "match", "appliesTo"),
    "term_required": ("terms", "match", "mode", "appliesTo"),
    "literal_required": ("literal", "match", "appliesTo"),
    "length_max": ("max", "unit", "appliesTo"),
}


# The enforcement vocabulary is the RULE's: the compiler copies whichever value
# the rule states, so the runtime, the compiler and the published contract all
# accept the same four and no others.
COMPILED_ENFORCEMENT_VALUES = ("block", "require_approval", "warn", "inform")


class CompiledCheckContractError(ValueError):
    """A compiled check leaves a decision-bearing parameter to the runtime."""


def assert_materialised(check: dict[str, Any]) -> None:
    primitive = check.get("primitive")
    if primitive not in REQUIRED_COMPILED_PARAMS:
        raise CompiledCheckContractError(f"unsupported primitive: {primitive}")
    if "phase" not in check:
        raise CompiledCheckContractError(f"{primitive}: compiled check must state its phase")
    # `enforcement` decides whether a failed check withholds the output, so it is
    # as decision-bearing as `match`. The compiler materialises it and the
    # published contract requires it; the runtime defaulted it to `block`, which
    # means an artefact the contract rejects still reached a governed decision.
    if "enforcement" not in check:
        raise CompiledCheckContractError(
            f"{primitive}: compiled check does not state enforcement — a runtime must "
            "not supply a governed decision the artefact left open"
        )
    if check["enforcement"] not in COMPILED_ENFORCEMENT_VALUES:
        raise CompiledCheckContractError(
            f"{primitive}: unsupported enforcement {check['enforcement']!r}"
        )
    params = check.get("params")
    if not isinstance(params, dict):
        raise CompiledCheckContractError(f"{primitive}: compiled check params must be an object")
    missing = [name for name in REQUIRED_COMPILED_PARAMS[primitive] if name not in params]
    if missing:
        raise CompiledCheckContractError(
            f"{primitive}: compiled check does not state " + ", ".join(missing)
            + " — a runtime must not supply a governed decision the artefact left open"
        )
    # Presence is not enough. A parameter that is present and *unrecognised* was
    # worse than one that was absent: `execute_checks` skipped a check whose
    # `appliesTo` matched no phase, so a deterministic prohibition disappeared
    # from the artefact's enforcement with no finding and no failure.
    errors = validate_check({"primitive": primitive, "phase": check["phase"], "params": params})
    if errors:
        raise CompiledCheckContractError(f"{primitive}: " + "; ".join(errors))


class UnicodeAdmissibilityError(ValueError):
    """Section 14.3c: a text input a deterministic check may not evaluate.

    Between Unicode 15.1.0 and 16.0.0, 12 code points gain a non-zero combining
    class and 27 gain a case-folding mapping. Both hosts conform to section
    14.3c's "15.1.0 or later", and 408 of 2160 observations differed across two
    real interpreters — in both directions, so this is not a conservative
    approximation either way.

    Every one of the 39 divergent code points is unassigned in the pinned
    version. Admitting check input under the pin therefore turns three cross-host
    divergences into one fail-closed rejection. Before 3.0.0 the pin was applied
    exactly backwards: the term was gated, the task input was gated only as a
    side effect of `text_hash` and raised out of the runtime uncaught, and the
    model output — the surface where the divergence is exploitable — was not
    gated at all.
    """


# Section 14.3 step 2 folds CR and CRLF to LF, and `text_hash` applies it. So a
# runtime text carrying a CR does not hash to itself: `BLOCK\rMARKER` and
# `BLOCK\nMARKER` share one `taskInputHash`, one `modelInputHash` and one
# `assemblyHash`, while a `term_prohibited exact` check matches one and not the
# other. Two governed task inputs, one set of hashes, opposite governed
# decisions — which is Class B's invariant, restated at the runtime layer, and
# it was still open there after Class B closed it for documents.
#
# The document rule refuses CR *and* LF because an identity is a key. A task
# input is prose and may legitimately contain LF, so the runtime rule refuses
# only the character the fold rewrites. That is enough: with no CR present the
# fold is the identity, and `text_hash` identifies exactly the bytes that were
# checked.
RUNTIME_FOLDED_CHARACTERS = {
    "\r": "U+000D CARRIAGE RETURN",
}


def assert_check_input_admissible(text: str, *, where: str) -> None:
    if not isinstance(text, str):
        raise UnicodeAdmissibilityError(f"{where} must be a string")
    try:
        assert_pinned_code_points(text)
    except ValueError as exc:
        raise UnicodeAdmissibilityError(f"{where}: {exc}") from exc
    for character, name in RUNTIME_FOLDED_CHARACTERS.items():
        if character in text:
            raise UnicodeAdmissibilityError(
                f"{where} must not contain {name}: section 14.3 folds it before "
                "hashing, so the Runtime Decision Record would not identify the "
                "bytes that were checked"
            )


@dataclass(frozen=True)
class CheckFinding:
    rule_element_id: str
    primitive: str
    enforcement: str
    phase: str
    passed: bool
    message: str


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _collapse_whitespace(text: str) -> str:
    """Every run of pinned separators becomes one space; ends are trimmed.

    Identical in result to `" ".join(text.split())` on the pinned set, and
    unlike it, identical on every host.
    """
    out: list[str] = []
    pending = False
    for character in text:
        if character in WHITESPACE_CODE_POINTS:
            pending = bool(out)
            continue
        if pending:
            out.append(" ")
            pending = False
        out.append(character)
    return "".join(out)


def _normalised_whitespace(text: str) -> str:
    return _collapse_whitespace(_nfc(text))


def _strip_default_ignorables(text: str) -> str:
    return "".join(character for character in text if character not in DEFAULT_IGNORABLE_CODE_POINTS)


def _normalised_whitespace_ci(text: str) -> str:
    """Section 11.5, new in 3.0.0.

    Foundation Check Registry v1 could not express a whitespace-robust
    multi-word prohibition at all: 22 of 24 separator variants evaded all three
    `term_prohibited` modes, the one folding mode in the registry was bound to
    `literal_required` — a positive obligation — and was case-sensitive, and no
    composition of the existing modes reached the missing semantics. Regex is
    not the answer and is deliberately not introduced: the required semantics
    are a normalisation, not a pattern language.
    """
    return _collapse_whitespace(_strip_default_ignorables(_nfc(text))).casefold()


def _contains(text: str, term: str, match: str) -> bool:
    text = _nfc(text)
    term = _nfc(term)

    if match == "exact":
        return term in text
    if match == "case_insensitive":
        return term.casefold() in text.casefold()
    if match == "word_boundary_ci":
        pattern = r"\b" + unicode_regex.escape(term) + r"\b"
        return unicode_regex.search(
            pattern,
            text,
            flags=unicode_regex.IGNORECASE
            | unicode_regex.FULLCASE
            | unicode_regex.WORD
            | unicode_regex.VERSION1,
        ) is not None
    if match == "normalized_whitespace":
        return _normalised_whitespace(term) in _normalised_whitespace(text)
    if match == "normalized_whitespace_ci":
        return _normalised_whitespace_ci(term) in _normalised_whitespace_ci(text)
    raise ValueError(f"unsupported match mode: {match}")


# Section 11.5, pinned in 3.0.0. A term whose first or last character is not a
# word character makes the corresponding `\b` anchor vacuous, so `.com` and
# terms with punctuation at an edge behaved in ways no author would predict and
# `validate_check` accepted all of them.
#
# The set is written down rather than delegated to `\w`, and for the same reason
# the whitespace set is: `\w` means one thing in Python's `re`, another in
# ECMA-262 without the `u` flag, and a third in the `regex` package's tables. A
# published JSON Schema has to state the same rule as the compiler, and it can
# only do that if the rule is a closed set of code points instead of a property
# lookup. `_` is deliberately *not* forbidden: it is a word character under every
# reading, and `very_cheap_now` must keep the meaning it has.
def _edge_ranges():
    ranges = [
        (0x0021, 0x002F),  # ! through /
        (0x003A, 0x0040),  # : through @
        (0x005B, 0x005E),  # [ through ^   (0x005F LOW LINE is a word character)
        (0x0060, 0x0060),  # GRAVE ACCENT
        (0x007B, 0x007E),  # { through ~
        (0x2010, 0x2027),  # General Punctuation: dashes, quotes, bullets
        (0x2030, 0x205E),  # General Punctuation: the rest
    ]
    points = {code for start, end in ranges for code in range(start, end + 1)}
    points |= {ord(character) for character in WHITESPACE_CODE_POINTS}
    points |= {ord(character) for character in DEFAULT_IGNORABLE_CODE_POINTS}
    return points


WORD_BOUNDARY_FORBIDDEN_EDGE = frozenset(chr(code) for code in _edge_ranges())


def word_boundary_edge_pattern() -> str:
    """The same set as an ECMA-262 character class, for the published contract.

    Derived from `WORD_BOUNDARY_FORBIDDEN_EDGE` rather than written twice, so the
    schema and the compiler cannot drift into two answers — which is exactly what
    an independent review found when the compiler held this rule alone.
    """
    codes = sorted(ord(character) for character in WORD_BOUNDARY_FORBIDDEN_EDGE)
    spans = []
    for code in codes:
        if spans and code == spans[-1][1] + 1:
            spans[-1][1] = code
        else:
            spans.append([code, code])

    def escape(code):
        return "\\u%04x" % code

    body = "".join(
        escape(start) if start == end else f"{escape(start)}-{escape(end)}"
        for start, end in spans
    )
    return f"^[^{body}]([\\s\\S]*[^{body}])?$"


def _word_boundary_term_error(term: str) -> str | None:
    """Section 11.5, stated in 3.0.0: what `word_boundary_ci` may be given.

    The mode's matching semantics are unchanged; what changes is that a term with
    no predictable meaning under it is refused at authoring time instead of
    degrading silently at runtime.
    """
    if not term:
        return "word_boundary_ci term must not be empty"
    for position, character in ((0, term[0]), (-1, term[-1])):
        if character in WORD_BOUNDARY_FORBIDDEN_EDGE:
            edge = "begin" if position == 0 else "end"
            return (
                f"word_boundary_ci term {term!r} must not {edge} with "
                f"U+{ord(character):04X}: a punctuation or separator edge makes the "
                "boundary anchor vacuous. Use normalized_whitespace_ci for a term "
                "with punctuation at its edge."
            )
    return None


def _element_value_ref_errors(ref: Any) -> list[str]:
    """The deferred form's own shape, checked where the rule is authored."""
    if not isinstance(ref, dict):
        return ["elementValueRef must be an object"]
    errors = []
    for field in ("elementId", "path"):
        value = ref.get(field)
        if not isinstance(value, str) or not value:
            errors.append(f"elementValueRef requires a non-empty {field}")
    return errors


def validate_check(check: dict[str, Any], *, stage: str = "compiled") -> list[str]:
    """One contract, two stages.

    A RULE may defer its literal to another element's value through
    `elementValueRef`; `_materialise_checks` resolves it and the artefact carries
    the resolved literal. `validate_manifest` ran the *compiled*-stage rule over
    the *authored* form, so it demanded a literal the author had deliberately
    deferred: a branch the published RULE contract admits could not pass the
    governed build path at all, while `build_target` called directly accepted it.

    `stage="authored"` is the manifest's stage. `stage="compiled"` is the
    artefact's, and there the value must be present, because nothing downstream
    will resolve it.
    """
    errors: list[str] = []
    primitive = check.get("primitive")
    if primitive not in SUPPORTED_PRIMITIVES:
        errors.append(f"unsupported primitive: {primitive}")
        return errors

    phase = check.get("phase", "postflight")
    if phase not in {"preflight", "postflight"}:
        errors.append(f"unsupported phase: {phase}")

    params = check.get("params")
    if not isinstance(params, dict):
        errors.append("params must be an object")
        return errors

    if primitive in {"term_prohibited", "term_required"}:
        terms = params.get("terms")
        if not isinstance(terms, list) or not terms or not all(isinstance(t, str) and t for t in terms):
            errors.append("terms must be a non-empty string array")
        if primitive == "term_required" and params.get("mode", "all") not in {"all", "any"}:
            # `execute_checks` implements `any` explicitly and everything else as
            # `all`, so an unregistered value silently became a governed decision
            # the artefact never stated.
            errors.append("invalid term_required mode")
        match = params.get("match", "case_insensitive")
        if match not in TERM_MATCH_MODES:
            errors.append("invalid match mode")
        elif match == "word_boundary_ci" and isinstance(terms, list):
            for term in terms:
                if isinstance(term, str):
                    reason = _word_boundary_term_error(term)
                    if reason:
                        errors.append(reason)
    elif primitive == "literal_required":
        deferred = params.get("elementValueRef")
        if deferred is not None and stage == "authored":
            # The reference is the governed value here; `_materialise_checks`
            # resolves it and the artefact carries the result. A literal beside
            # it is a placeholder the resolution overwrites, deterministically,
            # so it is not narrowed here — this closure has no reason to.
            errors.extend(_element_value_ref_errors(deferred))
        elif not isinstance(params.get("literal"), str) or not params["literal"]:
            errors.append("compiled literal_required needs a non-empty literal")
        if params.get("match", "exact") not in LITERAL_MATCH_MODES:
            errors.append("invalid match mode")
    elif primitive == "length_max":
        maximum = params.get("max")
        if not isinstance(maximum, int) or maximum < 0:
            errors.append("max must be a non-negative integer")
        if params.get("unit", "characters") != "characters":
            errors.append("Foundation Check Registry v1 supports characters only")

    applies_to = params.get("appliesTo", "output")
    if applies_to not in {"output", "task_input"}:
        errors.append("appliesTo must be output or task_input")
    expected_phase = "preflight" if applies_to == "task_input" else "postflight"
    if phase != expected_phase:
        errors.append(f"phase {phase} is incompatible with appliesTo {applies_to}; expected {expected_phase}")
    return errors


def execute_checks(
    checks: list[dict[str, Any]],
    *,
    phase: str,
    text: str,
) -> list[CheckFinding]:
    findings: list[CheckFinding] = []

    # Section 14.3c, extended in 3.0.0 to every input of a deterministic
    # compiled check. The gate runs once, before any matching, and it runs even
    # when no check applies to this phase: "this text may not be evaluated" is a
    # property of the text, not of which rules happen to be listed. Violation
    # fails closed — the caller turns this into a Runtime Decision Record.
    #
    # It used to run only `if checks`, which is the same sentence with the
    # opposite meaning: an artefact carrying no deterministic checks — the
    # ordinary case, not the exotic one — evaluated inadmissible text and
    # released inadmissible output.
    assert_check_input_admissible(text, where=f"{phase} check input")

    # Every compiled check is contract-checked before any of them runs, and
    # before the phase filter: an artefact carrying one unmaterialised check is
    # invalid whatever phase is executing.
    for check in checks:
        assert_materialised(check)

    for check in checks:
        check_phase = check["phase"]
        if check_phase != phase:
            continue

        primitive = check["primitive"]
        params = check["params"]
        enforcement = check["enforcement"]
        rule_id = check.get("ruleElementId", "unknown-rule")
        applies_to = params["appliesTo"]
        expected_target = "task_input" if phase == "preflight" else "output"
        if applies_to != expected_target:
            continue

        for index, term in enumerate(params.get("terms", []) or []):
            assert_check_input_admissible(term, where=f"{rule_id}: term[{index}]")
        if isinstance(params.get("literal"), str):
            assert_check_input_admissible(params["literal"], where=f"{rule_id}: literal")

        if primitive == "term_prohibited":
            match = params["match"]
            found = [term for term in params["terms"] if _contains(text, term, match)]
            passed = not found
            message = "no prohibited term found" if passed else f"prohibited term found: {found[0]}"
        elif primitive == "term_required":
            match = params["match"]
            present = [term for term in params["terms"] if _contains(text, term, match)]
            mode = params["mode"]
            passed = bool(present) if mode == "any" else len(present) == len(params["terms"])
            message = "required terms present" if passed else "required term missing"
        elif primitive == "literal_required":
            passed = _contains(text, params["literal"], params["match"])
            message = "required literal present" if passed else "required literal missing"
        elif primitive == "length_max":
            passed = len(_nfc(text)) <= params["max"]
            message = "length within limit" if passed else f"length exceeds {params['max']} characters"
        else:
            raise ValueError(f"unsupported primitive: {primitive}")

        findings.append(CheckFinding(
            rule_element_id=rule_id,
            primitive=primitive,
            enforcement=enforcement,
            phase=phase,
            passed=passed,
            message=message,
        ))
    return findings
