from __future__ import annotations

import copy
import hashlib
import json
import math
import unicodedata
from typing import Any


def _normalise_string(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
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
