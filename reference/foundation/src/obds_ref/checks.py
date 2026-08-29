from __future__ import annotations

import re
import unicodedata

import regex as unicode_regex
from dataclasses import dataclass
from typing import Any


SUPPORTED_PRIMITIVES = {
    "term_prohibited",
    "term_required",
    "literal_required",
    "length_max",
}


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


def _normalised_whitespace(text: str) -> str:
    return " ".join(_nfc(text).split())


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
    raise ValueError(f"unsupported match mode: {match}")


def validate_check(check: dict[str, Any]) -> list[str]:
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
        if params.get("match", "case_insensitive") not in {"exact", "case_insensitive", "word_boundary_ci"}:
            errors.append("invalid match mode")
    elif primitive == "literal_required":
        if not isinstance(params.get("literal"), str) or not params["literal"]:
            errors.append("compiled literal_required needs a non-empty literal")
        if params.get("match", "exact") not in {"exact", "normalized_whitespace"}:
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

    for check in checks:
        check_phase = check.get("phase", "postflight")
        if check_phase != phase:
            continue

        primitive = check["primitive"]
        params = check["params"]
        enforcement = check.get("enforcement", "block")
        rule_id = check.get("ruleElementId", "unknown-rule")
        applies_to = params.get("appliesTo", "output")
        expected_target = "task_input" if phase == "preflight" else "output"
        if applies_to != expected_target:
            continue

        if primitive == "term_prohibited":
            match = params.get("match", "case_insensitive")
            found = [term for term in params["terms"] if _contains(text, term, match)]
            passed = not found
            message = "no prohibited term found" if passed else f"prohibited term found: {found[0]}"
        elif primitive == "term_required":
            match = params.get("match", "case_insensitive")
            present = [term for term in params["terms"] if _contains(text, term, match)]
            mode = params.get("mode", "all")
            passed = bool(present) if mode == "any" else len(present) == len(params["terms"])
            message = "required terms present" if passed else "required term missing"
        elif primitive == "literal_required":
            passed = _contains(text, params["literal"], params.get("match", "exact"))
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
