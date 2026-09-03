"""Section 28.1: the one governed interchange contract.

Every path in the release that turns bytes into a governed value — YAML or
JSON, product code, gate or evidence — goes through this module, and no module
changes another module's parser.

Before 3.0.0 the release shipped four different governed input contracts across
seven readers, of which one conformed. The divergence was not visible in the
shipped corpus, which read identically under all of them, so the release was
internally consistent by accident of its data rather than by construction. One
of the non-conforming readers also mutated PyYAML's resolver tables in place,
process-wide, which changed what every other consumer in the process read and
what the governed writer emitted. Both defects are properties of *having more
than one reader*, so the correction is one reader rather than seven repairs.

This module is a leaf. It imports `canonical` lazily, inside the one function
that needs it, so that `canonical` may read its own Unicode pin through
`read_governed_document` without an import cycle. `read_governed_document`
parses; `load_data` parses and additionally admits the resulting data model
under the canonical form. Both use the same tables, so no reader can disagree
with another about what a document says.

The module is copied verbatim into every package that needs it, next to
`canonical.py` and under the same rule: the release gate asserts every copy is
byte-identical, so the contract cannot drift.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import yaml


def _canonical_json_bytes():
    """Imported here, not at module scope, so `canonical` can use this module.

    `canonical._load_unicode_pin()` runs while `canonical` is still executing,
    so a module-scope import would either cycle or bind a name that does not
    exist yet. Deferring it costs one dict lookup per document and keeps this
    module a leaf.
    """
    try:
        from .canonical import canonical_json_bytes
    except ImportError:
        from canonical import canonical_json_bytes
    return canonical_json_bytes


class ValidationFailure(Exception):
    def __init__(self, errors: list[str]):
        super().__init__("\n".join(errors))
        self.errors = errors


class _StrictJSONDuplicate(ValueError):
    pass


def _canonical_key(key: str) -> str:
    """Section 14.3 steps 1 and 2, applied where duplicates are decided.

    NFC alone is not the canonical comparison: step 2 folds CRLF and CR to LF, so
    `a\rb` and `a\nb` are one key in canonical form and two keys under NFC. A
    reader that deduplicates on NFC alone therefore accepts a document whose own
    canonical form has a duplicate key — which `load_data` catches through
    `canonical_json_bytes`, but `read_governed_document` does not, and
    `canonical._load_unicode_pin` uses that lower path to read the table behind
    every hash in the system.

    The fold is inlined rather than imported: this module is a leaf so that
    `canonical` can use it, and section 14.3 states the two steps in that order.
    """
    return unicodedata.normalize("NFC", key.replace("\r\n", "\n").replace("\r", "\n"))


def _strict_pairs(pairs):
    result = {}
    seen = set()
    for key, value in pairs:
        nkey = _canonical_key(key)
        if nkey in seen:
            raise _StrictJSONDuplicate(f"duplicate object key: {key}")
        seen.add(nkey)
        result[key] = value
    return result


class _OBDSSafeLoader(yaml.SafeLoader):
    """Section 28.1. Governed YAML is a JSON data model written in YAML.

    Every implicit resolver is removed, so a plain scalar reaches one
    constructor that owns the whole decision. An explicit tag is refused at
    compose time, before any constructor runs, and the merge key `<<` is
    refused where the mapping is built: each of them lets the same characters
    produce a different data model, which is the defect this section closes.
    `!!str 1e3` must not be a way to reach a value the plain rules would not
    produce, and `<<` must not mean one thing here and another in every other
    YAML reader.

    Anchors and aliases are permitted, because an alias expands to the same
    node in every YAML version. Their expansion is bounded by
    `_reject_unbounded_alias_expansion`, which also rejects a recursive alias.
    Nesting is bounded here, for the same reason and with the same argument: an
    unstated limit is whatever the runtime's stack happens to be, which is not a
    thing two implementations can agree on.
    """

    _depth = 0

    def compose_node(self, parent, index):
        event = self.peek_event()
        tag = getattr(event, "tag", None)
        if tag is not None:
            # Including the non-specific "!": it suppresses resolution, so it is
            # another way to reach a value the plain rules would not produce.
            raise yaml.constructor.ConstructorError(
                None, None,
                f"governed YAML must not use an explicit tag: {tag}",
                event.start_mark,
            )
        opens_collection = isinstance(
            event, (yaml.events.SequenceStartEvent, yaml.events.MappingStartEvent)
        )
        if opens_collection:
            if self._depth >= MAX_NESTING_DEPTH:
                raise yaml.constructor.ConstructorError(
                    None, None,
                    f"nesting exceeds {MAX_NESTING_DEPTH} levels",
                    event.start_mark,
                )
            self._depth += 1
        try:
            return super().compose_node(parent, index)
        finally:
            if opens_collection:
                self._depth -= 1


class _AmbiguousYAMLScalar(ValueError):
    pass


# Section 28.1. Governed YAML resolves plain scalars under the YAML 1.2 Core
# Schema, and a plain scalar that resolves to null, a boolean or a number must
# denote the same value read as a JSON literal. Everything else is a string.
#
# Before 2.0.0 the loader inherited PyYAML's YAML 1.1 implicit resolvers with
# only the boolean set replaced, so the same bytes meant different things
# depending on the file extension: `{"a": 1e3}` was the number 1000 as JSON and
# the string "1e3" as YAML, and therefore had two canonical hashes.
_YAML_NULL = re.compile(r"^(?:null|Null|NULL)$")
_YAML_BOOL = re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$")
# The JSON number grammar, not a YAML one. A plain scalar that resolves to a
# number therefore denotes what the same characters denote read as JSON.
_JSON_NUMBER = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?$")

# The YAML 1.1 int and float resolvers, in the shape PyYAML implements them.
# They are here to be rejected against, not resolved with: a scalar that YAML
# 1.1 reads as a number and the JSON grammar does not produce is exactly the
# form whose meaning depends on the reader.
_YAML11_INT = re.compile(r"""^(?:[-+]?0b[01_]+
                             |[-+]?0[0-7_]+
                             |[-+]?(?:0|[1-9][0-9_]*)
                             |[-+]?0x[0-9a-fA-F_]+
                             |[-+]?[1-9][0-9_]*(?::[0-5]?[0-9])+)$""", re.X)
_YAML11_FLOAT = re.compile(r"""^(?:[-+]?[0-9][0-9_]*\.[0-9_]*(?:[eE][-+][0-9]+)?
                               |\.[0-9][0-9_]*(?:[eE][-+][0-9]+)?
                               |[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\.[0-9_]*
                               |[-+]?\.(?:inf|Inf|INF)
                               |\.(?:nan|NaN|NAN))$""", re.X)


class _Yaml11NumberNotJson:
    """A pattern object for the rejection table: matches on the class, not a spelling."""

    def match(self, text: str):
        if _JSON_NUMBER.match(text):
            return None
        return _YAML11_INT.match(text) or _YAML11_FLOAT.match(text)


_YAML11_NUMBER_NOT_JSON = _Yaml11NumberNotJson()


def _yaml11_reason(text: str) -> str:
    """Name the YAML 1.1 spelling the author actually wrote."""
    if "_" in text:
        return "digit separator: a number in YAML 1.1, a string in YAML 1.2"
    if ":" in text:
        return "sexagesimal: a number in YAML 1.1, a string in YAML 1.2"
    return "a number in YAML 1.1, not a JSON number"


# Section 28.1, the rejection table. Each form is one some YAML version reads as
# a value the JSON grammar does not produce, so resolving it either way would
# make a governed document's meaning depend on which YAML version the reader
# carries. Quoting always resolves the rejection.
_YAML_AMBIGUOUS = (
    (re.compile(r"^[-+]?0[0-9]+(?:\.[0-9]*)?(?:[eE][-+]?[0-9]+)?$"), "leading zero: octal or a float in YAML 1.1, decimal in YAML 1.2, not a JSON number"),
    (re.compile(r"^\+(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?$"), "leading plus: a number in YAML 1.2, not a JSON number"),
    (re.compile(r"^[-+]?[0-9]+\.(?:[eE][-+]?[0-9]+)?$"), "bare decimal point: a float in YAML 1.2, not a JSON number"),
    (re.compile(r"^[-+]?\.[0-9]+(?:[eE][-+]?[0-9]+)?$"), "bare decimal point: a float in YAML 1.2, not a JSON number"),
    (re.compile(r"""^(?:[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]
                     |[0-9][0-9][0-9][0-9]-[0-9][0-9]?-[0-9][0-9]?
                      (?:[Tt]|[ \t]+)[0-9][0-9]?
                      :[0-9][0-9]:[0-9][0-9](?:\.[0-9]*)?
                      (?:[ \t]*(?:Z|[-+][0-9][0-9]?(?::[0-9][0-9])?))?)$""", re.X),
     "date or timestamp shaped: a timestamp in YAML 1.1, a string in YAML 1.2"),
    (re.compile(r"^[-+]?0b[01_]+$"), "alternative number base: JSON has none"),
    (re.compile(r"^0o[0-7]+$"), "alternative number base: JSON has none"),
    (re.compile(r"^[-+]?0x[0-9a-fA-F_]+$"), "alternative number base: JSON has none"),
    (re.compile(r"^~$"), "YAML 1.1 null shorthand: write null"),
    (re.compile(r"^(?:[-+]?\.(?:inf|Inf|INF)|\.(?:nan|NaN|NAN))$"), "non-finite number: outside the OBDS numeric domain"),
    (re.compile(r"^$"), "empty plain scalar: null in YAML, absent in JSON; write null"),
    # The rows above are the YAML 1.2 side: forms YAML 1.2 reads as a value the
    # JSON grammar does not produce. This one is the YAML 1.1 side, and it is
    # last so the specific messages win. It is stated as the class rather than
    # as spellings because the spellings were enumerated once and missed every
    # combination — `1_000.0`, `1_0:30`, `.5_0` — each a number in YAML 1.1 and
    # a string here, which is a value that changes with no diagnostic. Stating
    # the class also stops the table over-reaching: a hand-written digit
    # separator or sexagesimal pattern rejected `0__8` and `0:07`, which no
    # YAML version reads as anything but a string.
    (_YAML11_NUMBER_NOT_JSON, _yaml11_reason),
)


def _resolve_plain_scalar(text: str):
    """Section 28.1: resolve one plain YAML scalar, or reject it."""
    for pattern, why in _YAML_AMBIGUOUS:
        if pattern.match(text):
            reason = why(text) if callable(why) else why
            raise _AmbiguousYAMLScalar(
                f"ambiguous plain scalar {text!r}: {reason}. Quote it, or write "
                "it in a form JSON accepts."
            )
    if _YAML_NULL.match(text):
        return None
    if _YAML_BOOL.match(text):
        return text.lower() == "true"
    if _JSON_NUMBER.match(text):
        if "." in text or "e" in text or "E" in text:
            return float(text)
        return _strict_parse_int(text)
    return text


def _construct_plain_scalar(loader, node):
    if node.style is None:
        try:
            return _resolve_plain_scalar(node.value)
        except _AmbiguousYAMLScalar as exc:
            raise yaml.constructor.ConstructorError(
                None, None, str(exc), node.start_mark
            ) from exc
        except ValueError as exc:
            raise yaml.constructor.ConstructorError(
                None, None, str(exc), node.start_mark
            ) from exc
    return node.value


def _reject_non_plain_node(loader, node):
    """Section 28.1: no explicit tag and no merge key.

    No implicit resolver remains, so anything arriving at a typed constructor
    got its tag explicitly.
    """
    raise yaml.constructor.ConstructorError(
        None, None,
        f"governed YAML must not use {node.tag!r}: an explicit tag or a merge "
        "key lets the same characters produce different data",
        node.start_mark,
    )


# Every implicit resolver is replaced, not subtracted from: a plain scalar now
# reaches one constructor that owns the whole decision.
_OBDSSafeLoader.yaml_implicit_resolvers = {}
_OBDSSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_SCALAR_TAG,
    _construct_plain_scalar,
)
# Anything reaching a typed constructor did so through an explicit tag, since
# no implicit resolver remains. Merge keys arrive as tag:yaml.org,2002:merge.
for _tag in (
    "tag:yaml.org,2002:bool",
    "tag:yaml.org,2002:int",
    "tag:yaml.org,2002:float",
    "tag:yaml.org,2002:null",
    "tag:yaml.org,2002:binary",
    "tag:yaml.org,2002:timestamp",
    "tag:yaml.org,2002:merge",
    "tag:yaml.org,2002:set",
    "tag:yaml.org,2002:omap",
    "tag:yaml.org,2002:pairs",
):
    _OBDSSafeLoader.add_constructor(_tag, _reject_non_plain_node)


def _construct_mapping(loader, node, deep=False):
    mapping = {}
    seen = set()
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise yaml.constructor.ConstructorError(None, None, "mapping keys must be strings", key_node.start_mark)
        if key == "<<" and key_node.style is None:
            # Section 28.1: written plain, every other YAML reader merges this
            # key, so keeping it literal would mean one document, two data
            # models. Written quoted it is an ordinary string key everywhere,
            # and that is what save_yaml emits.
            raise yaml.constructor.ConstructorError(
                None, None, "governed YAML must not use a merge key", key_node.start_mark
            )
        nkey = _canonical_key(key)
        if nkey in seen:
            raise yaml.constructor.ConstructorError(None, None, f"duplicate mapping key: {key}", key_node.start_mark)
        seen.add(nkey)
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_OBDSSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


def _strict_parse_int(text: str) -> int:
    value = int(text)
    try:
        as_float = float(value)
    except OverflowError as exc:
        raise ValueError("integer is outside IEEE-754 binary64") from exc
    if not __import__("math").isfinite(as_float) or int(as_float) != value:
        raise ValueError("integer is not exactly representable as IEEE-754 binary64")
    return value


def _strict_parse_float(text: str) -> float:
    """Section 28.1: a spelling whose value is not finite is not a JSON number.

    `parse_constant` catches the literals `Infinity`, `-Infinity` and `NaN`, but
    not a finite *spelling* that overflows to infinity — `1e400` is a
    syntactically ordinary number that Python's default `parse_float` turns into
    `inf`. `load_data` refused it downstream through `canonical_json_bytes`;
    `read_governed_document` did not, and that is the path `canonical`'s own pin
    reader uses.
    """
    value = float(text)
    if value != value or value in (float("inf"), float("-inf")):
        raise ValueError(f"non-finite JSON number is invalid: {text}")
    return value


def _reject_constant(text: str):
    raise ValueError(f"non-finite JSON number is invalid: {text}")


# Section 28.1. YAML 1.1 counts these as line breaks and YAML 1.2 does not, so a
# raw one inside a scalar reads as a break in one parser and as a character in
# the other. PyYAML turns a raw U+0085 into a space; a YAML 1.2 parser keeps it.
# They are legitimate governed content, and section 14.3b escapes two of them, so
# they are not forbidden: they must be written as an escape in a double-quoted
# scalar, where every YAML version agrees on what they are.
_YAML_VERSION_SENSITIVE_BREAKS = {
    "\u0085": "U+0085 NEXT LINE",
    "\u2028": "U+2028 LINE SEPARATOR",
    "\u2029": "U+2029 PARAGRAPH SEPARATOR",
}


def _reject_raw_version_sensitive_breaks(text: str) -> None:
    for character, name in _YAML_VERSION_SENSITIVE_BREAKS.items():
        if character in text:
            raise ValidationFailure([
                f"governed YAML must not contain a raw {name}: YAML 1.1 reads it "
                "as a line break and YAML 1.2 does not. Write it as an escape in "
                "a double-quoted scalar."
            ])


# Section 28.1. Anchors and aliases are permitted because an alias expands to
# the same node in every YAML version, but "the same node" is not the same as
# "the same amount of data": eight aliases per level, nine levels deep, is
# 425 bytes of governed YAML and 175,304,795 nodes once expanded. A subset that
# calls itself closed has to say where the expansion stops, so it stops here.
MAX_EXPANDED_NODES = 1_000_000

# Section 28.1. Nesting has the same problem as alias expansion: left unstated,
# the limit is whatever the reader's stack allows, which differs per runtime and
# per version of this file. A level is one nested collection, counting the
# outermost, so `{"a": [1]}` is two and this bound accepts one hundred. The
# deepest governed document this project ships nests ten.
MAX_NESTING_DEPTH = 100


def _reject_unbounded_alias_expansion(node) -> int:
    """Section 28.1: reject a recursive alias, and bound alias expansion.

    The count is over the expanded data model, so an aliased node is counted
    once per use. Distinct nodes are memoised, so the walk itself stays linear
    in the size of the document as written.
    """

    memo: dict[int, int] = {}
    on_path: set[int] = set()

    def size(current) -> int:
        key = id(current)
        cached = memo.get(key)
        if cached is not None:
            return cached
        if key in on_path:
            raise ValidationFailure([
                "governed YAML must not use a recursive alias: it has no "
                "expansion, so it has no canonical form"
            ])
        on_path.add(key)
        if isinstance(current, yaml.MappingNode):
            total = 1 + sum(size(k) + size(v) for k, v in current.value)
        elif isinstance(current, yaml.SequenceNode):
            total = 1 + sum(size(item) for item in current.value)
        else:
            total = 1
        on_path.discard(key)
        if total > MAX_EXPANDED_NODES:
            raise ValidationFailure([
                f"governed YAML alias expansion exceeds {MAX_EXPANDED_NODES} "
                "nodes: write the document out rather than aliasing it"
            ])
        memo[key] = total
        return total

    return size(node)


def _reject_excessive_nesting(data) -> None:
    """Section 28.1: one bound for one data model, whichever format carried it.

    The composer refuses a deep YAML document before it builds it; this is the
    same rule stated where JSON arrives too, so the two formats cannot disagree
    about which documents are governable.
    """
    stack = [(data, 0)]
    while stack:
        node, depth = stack.pop()
        if isinstance(node, (dict, list)):
            if depth >= MAX_NESTING_DEPTH:
                raise ValidationFailure([
                    f"parse error: nesting exceeds {MAX_NESTING_DEPTH} levels"
                ])
            children = node.values() if isinstance(node, dict) else node
            stack.extend((child, depth + 1) for child in children)


def _load_governed_yaml(text: str):
    """Compose first, bound the expansion, then construct.

    `yaml.load` does both in one step, which would build the expansion this
    function exists to refuse.
    """
    loader = _OBDSSafeLoader(text)
    try:
        node = loader.get_single_node()
        if node is None:
            return None
        _reject_unbounded_alias_expansion(node)
        return loader.construct_document(node)
    finally:
        loader.dispose()


def load_data(path: str | Path) -> dict[str, Any]:
    # The root rule now belongs to the reader, so this is the canonical-form
    # check and nothing else.
    data = read_governed_document(path)
    try:
        _canonical_json_bytes()(data)
    except (TypeError, ValueError) as exc:
        raise ValidationFailure([f"{path}: canonical data error: {exc}"]) from exc
    return data


def save_json(path: str | Path, data: dict[str, Any]) -> None:
    Path(path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class _OBDSSafeDumper(yaml.SafeDumper):
    """Section 28.1 applies to what this project writes, not only what it reads.

    PyYAML's emitter decides whether a string needs quoting with YAML 1.1
    resolvers, so it wrote the string "1e3" as a plain `1e3`, which the governed
    reader now reads back as the number 1000. A writer and a reader that
    disagree are the same defect in the other direction.
    """


def _represent_governed_str(dumper, value):
    if any(character in value for character in _YAML_VERSION_SENSITIVE_BREAKS):
        # Only the double-quoted style escapes them; raw, this reader refuses
        # its own output.
        return dumper.represent_scalar("tag:yaml.org,2002:str", value, style='"')
    plain_is_faithful = False
    try:
        plain_is_faithful = _resolve_plain_scalar(value) == value
    except (ValueError, TypeError):
        plain_is_faithful = False
    style = None if plain_is_faithful else "'"
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


_OBDSSafeDumper.add_representer(str, _represent_governed_str)


def save_yaml(path: str | Path, data: dict[str, Any]) -> None:
    Path(path).write_text(
        yaml.dump(data, Dumper=_OBDSSafeDumper, sort_keys=False,
                  allow_unicode=True, width=110, default_flow_style=False),
        encoding="utf-8",
    )


def read_governed_text(text: str, *, is_json: bool):
    """Section 28.1 applied to bytes already in hand rather than a path.

    The release gate scrapes governed YAML out of published HTML, so the
    contract has to be reachable without a file. Same tables, same bounds.
    """
    try:
        if not is_json:
            _reject_raw_version_sensitive_breaks(text)
            data = _load_governed_yaml(text)
        else:
            data = json.loads(
                text,
                object_pairs_hook=_strict_pairs,
                parse_int=_strict_parse_int,
                parse_float=_strict_parse_float,
                parse_constant=_reject_constant,
            )
    except ValidationFailure as exc:
        raise ValidationFailure([f"parse error: {error}" for error in exc.errors]) from exc
    except RecursionError as exc:
        raise ValidationFailure(["parse error: document nests too deeply to read"]) from exc
    except (json.JSONDecodeError, _StrictJSONDuplicate, yaml.YAMLError, ValueError) as exc:
        raise ValidationFailure([f"parse error: {exc}"]) from exc
    # The bound belongs to the contract, not to the entry point. Stated here it
    # is reached by both readers; stated in `read_governed_document` alone it
    # was reached by one, and the same bytes had two answers.
    _reject_excessive_nesting(data)
    # Same argument, one rule further. The declared conformance case
    # `governed-input-sequence-root` says a sequence root is not governable, and
    # `load_data` said so — but `read_governed_document` and `read_governed_text`
    # returned the list, and the JavaScript reader refused it. Five readers, two
    # answers. A governed document is an object, stated once, where every entry
    # point reaches it.
    if not isinstance(data, dict):
        raise ValidationFailure(["root must be an object"])
    return data


def read_governed_document(path: str | Path) -> Any:
    """Parse under section 28.1 and bound the data model. No canonical check.

    This is what `canonical` itself uses to read the Unicode pin: at that point
    `canonical_json_bytes` does not exist yet, and the pin table is a question
    about *parsing*, not about whether its contents have a canonical form.
    Every other caller wants `load_data`.
    """
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
        return read_governed_text(text, is_json=path.suffix.lower() == ".json")
    except ValidationFailure as exc:
        # Every rejection is already stated by the shared reader. This adds the
        # path and nothing else, so the two entry points cannot disagree about
        # what is governable, only about how the failure is addressed.
        raise ValidationFailure([f"{path}: {error}" for error in exc.errors]) from exc
    except OSError as exc:
        raise ValidationFailure([f"{path}: parse error: {exc}"]) from exc
