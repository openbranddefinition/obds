from __future__ import annotations

import bisect
import copy
import hashlib
import json
import math
import unicodedata
from pathlib import Path
from typing import Any

# Section 14.3c. NFC is only stable for code points already assigned in the
# Unicode version that performs it: a code point unassigned in one version and
# given a non-zero combining class in the next reorders, so two runtimes with
# different Unicode databases produce different canonical bytes for the same
# document. OBDS therefore pins one version and admits only code points assigned
# in it, plus the 66 permanent noncharacters, which Unicode guarantees will
# never be assigned and which therefore stay normalisation-stable for ever.
# Within that set the Unicode Normalization Stability Policy makes NFC identical
# on every database at or after the pinned version.
UNICODE_PIN_VERSION = "15.1.0"
_UNICODE_PIN_PATH = Path(__file__).with_name(f"unicode-pin-{UNICODE_PIN_VERSION}.json")


def _version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split("."))


def _assert_host_unicode_is_at_least_pinned() -> None:
    """Section 14.3c: the host database must be at or after the pinned version.

    Admitting only code points assigned in 15.1.0 makes NFC identical on every
    database at or after 15.1.0, by the Unicode Normalization Stability Policy.
    It says nothing about an older database, which does not know those code
    points at all and gives them combining class zero, so it normalises admitted
    documents differently. An implementation that cannot satisfy the contract
    must say so rather than produce a hash no one else reproduces.
    """
    host = unicodedata.unidata_version
    if _version_tuple(host) < _version_tuple(UNICODE_PIN_VERSION):
        raise RuntimeError(
            f"this runtime carries Unicode {host}; OBDS section 14.3c pins "
            f"Unicode {UNICODE_PIN_VERSION} and requires a database at or after "
            "it. CPython 3.13 or later satisfies this."
        )


_assert_host_unicode_is_at_least_pinned()


def _load_unicode_pin() -> tuple[list[int], list[int]]:
    with _UNICODE_PIN_PATH.open(encoding="utf-8") as handle:
        document = json.load(handle)
    if document.get("unicodeVersion") != UNICODE_PIN_VERSION:
        raise ValueError(
            f"unicode pin table declares {document.get('unicodeVersion')!r}, "
            f"expected {UNICODE_PIN_VERSION!r}"
        )
    starts: list[int] = []
    ends: list[int] = []
    for start, end in document["assignedRanges"]:
        if start > end or (starts and start <= ends[-1]):
            raise ValueError("unicode pin ranges must be sorted and disjoint")
        starts.append(start)
        ends.append(end)
    return starts, ends


_UNICODE_PIN_STARTS, _UNICODE_PIN_ENDS = _load_unicode_pin()


def _assigned_in_pinned_unicode(code_point: int) -> bool:
    # Both ends of every range are inclusive.
    index = bisect.bisect_right(_UNICODE_PIN_STARTS, code_point) - 1
    return index >= 0 and code_point <= _UNICODE_PIN_ENDS[index]


def assert_pinned_code_points(value: str) -> None:
    """Section 14.3c: reject any code point outside the pinned Unicode version."""
    if value.isascii():
        return
    for character in value:
        code_point = ord(character)
        if code_point < 0x80:
            continue
        if not _assigned_in_pinned_unicode(code_point):
            raise ValueError(
                f"code point U+{code_point:04X} is not assigned in Unicode "
                f"{UNICODE_PIN_VERSION}, the version pinned by section 14.3c"
            )


def _normalise_string(value: str) -> str:
    assert_pinned_code_points(value)
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    if value.isascii():
        return value
    return unicodedata.normalize("NFC", value)


def identity_key(value: str) -> str:
    """Section 8.0a: the canonical comparison key for a semantic identity.

    Element ids and semantic subjects decide which truth is selected and in what
    order the governed result is hashed. Every other governed string is compared
    after NFC; these two were compared as raw document bytes until 1.1.6, so two
    canonically equivalent identities counted as two identities and one approved
    manifest could produce two governed results. The stored representation is
    left untouched: this key exists for comparison, grouping and ordering.
    """
    if not isinstance(value, str):
        raise TypeError("semantic identity must be a string")
    assert_pinned_code_points(value)
    # NFC only. Section 14.3 step 2 folds CR and CRLF to LF for canonical bytes,
    # which is a serialisation rule; section 8.0a says two identities are equal
    # exactly when their NFC forms are equal. Folding here as well would merge
    # `a\rb` and `a\nb`, which NFC keeps distinct, and reject two separate
    # elements as one duplicate.
    if value.isascii():
        return value
    return unicodedata.normalize("NFC", value)


def _utf16_sort_key(value: str) -> bytes:
    # RFC 8785/JCS ordering uses UTF-16 code units. OBDS applies NFC/LF first.
    try:
        return value.encode("utf-16-be")
    except UnicodeEncodeError as exc:
        raise ValueError("unpaired Unicode surrogate is not canonical") from exc


def _number_token(value: int | float) -> str:
    if isinstance(value, bool):
        raise TypeError("boolean is not a JSON number")
    if isinstance(value, int):
        try:
            as_float = float(value)
        except OverflowError as exc:
            raise ValueError("integer is outside IEEE-754 binary64") from exc
        if not math.isfinite(as_float) or int(as_float) != value:
            raise ValueError("integer is not exactly representable as IEEE-754 binary64")
        value = as_float
    if not isinstance(value, float):
        raise TypeError("canonical JSON numbers must be int or float")
    if not math.isfinite(value):
        raise ValueError("non-finite JSON numbers are not canonical")
    if value == 0:
        return "0"

    # Python repr gives a shortest round-trippable decimal for binary64.
    # Reformat that decimal using ECMAScript / RFC 8785 thresholds:
    # fixed notation for 1e-6 <= abs(x) < 1e21, scientific otherwise.
    sign = "-" if value < 0 else ""
    raw = repr(abs(value)).lower()
    if "e" in raw:
        coefficient, exp_text = raw.split("e", 1)
        exp = int(exp_text)
    else:
        coefficient, exp = raw, 0

    if "." in coefficient:
        whole, frac = coefficient.split(".", 1)
        digits = whole + frac
        exp10 = exp - len(frac)
    else:
        digits = coefficient
        exp10 = exp

    digits = digits.lstrip("0") or "0"
    while len(digits) > 1 and digits.endswith("0"):
        digits = digits[:-1]
        exp10 += 1

    k = len(digits) + exp10
    magnitude = abs(value)
    if 1e-6 <= magnitude < 1e21:
        if k <= 0:
            body = "0." + ("0" * (-k)) + digits
        elif k >= len(digits):
            body = digits + ("0" * (k - len(digits)))
        else:
            body = digits[:k] + "." + digits[k:]
        return sign + body

    exponent = k - 1
    mantissa = digits[0]
    if len(digits) > 1:
        mantissa += "." + digits[1:]
    exp_token = f"+{exponent}" if exponent >= 0 else str(exponent)
    return f"{sign}{mantissa}e{exp_token}"


def _canonical_text(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _number_token(value)
    if isinstance(value, str):
        normal = _normalise_string(value)
        try:
            normal.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ValueError("unpaired Unicode surrogate is not canonical") from exc
        return json.dumps(normal, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, list):
        return "[" + ",".join(_canonical_text(item) for item in value) + "]"
    if isinstance(value, dict):
        normalised: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("canonical JSON object keys must be strings")
            nkey = _normalise_string(key)
            if nkey in normalised:
                raise ValueError(f"duplicate object key after NFC normalisation: {nkey}")
            normalised[nkey] = item
        keys = sorted(normalised, key=_utf16_sort_key)
        return "{" + ",".join(
            json.dumps(key, ensure_ascii=False, separators=(",", ":")) + ":" + _canonical_text(normalised[key])
            for key in keys
        ) + "}"
    raise TypeError(f"unsupported JSON value type: {type(value)}")


def canonical_json_bytes(value: Any) -> bytes:
    return _canonical_text(value).encode("utf-8")


def sha256_id(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def manifest_content_hash(manifest: dict[str, Any]) -> str:
    payload = copy.deepcopy(manifest)
    payload.pop("approval", None)
    return sha256_id(payload)


def artefact_hash(artefact: dict[str, Any]) -> str:
    payload = copy.deepcopy(artefact)
    payload.pop("artifactHash", None)
    return sha256_id(payload)


def text_hash(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("text_hash requires a string")
    normalised = _normalise_string(value)
    return "sha256:" + hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def value_shape(value: Any) -> Any:
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        _number_token(value)  # validate numeric domain
        return {"type": "number"}
    if isinstance(value, str):
        return {"type": "string"}
    if isinstance(value, list):
        unique = {}
        for item in value:
            shape = value_shape(item)
            key = _canonical_text(shape)
            unique[key] = shape
        return {"type": "array", "items": [unique[key] for key in sorted(unique, key=_utf16_sort_key)]}
    if isinstance(value, dict):
        normalised = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("value shape object keys must be strings")
            nkey = _normalise_string(key)
            if nkey in normalised:
                raise ValueError(f"duplicate object key after NFC normalisation: {nkey}")
            normalised[nkey] = item
        return {
            "type": "object",
            "properties": {
                key: value_shape(normalised[key])
                for key in sorted(normalised, key=_utf16_sort_key)
            },
        }
    raise TypeError(f"unsupported JSON value type: {type(value)}")


def value_shape_hash(value: Any) -> str:
    return sha256_id(value_shape(value))
