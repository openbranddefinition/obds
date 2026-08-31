from __future__ import annotations

import copy
import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
import jsonschema

from .canonical import _utf16_sort_key, artefact_hash, canonical_json_bytes, manifest_content_hash, sha256_id, value_shape_hash
from .checks import SUPPORTED_PRIMITIVES, validate_check


VALID_STATES = {"defined", "unknown", "not_defined", "not_applicable"}
VALID_FAMILIES = {"structure", "identity", "design", "rules", "context", "stance"}
VALID_NATURES = {"fact", "knowledge"}
SUPPORTED_TOKENIZERS = {("obds:whitespace-v1", "1.0.0")}

# Section 14.4: an implementation records its own compiler identity and never
# stamps one it did not execute. Before OBDS 1.1 this copied the Build Plan's
# declared identity straight into the artefact, so a plan naming any other
# compiler produced an artefact claiming provenance that never happened.
COMPILER_ID = "org.openbranddefinition.reference-compiler"
COMPILER_VERSION = "1.0.0"

# OBDS 1.1 section 9: the closed scope vocabulary, nine dimensions. `brands` was
# accepted by the reference but appeared nowhere in the specification;
# `contentPurposes` appeared in the section 9 example but was rejected here. Both
# are fixed by stating one set. Widening the accepted set is compatible.
SCOPE_DIMENSIONS = {
    "brands",
    "markets",
    "locales",
    "jurisdictions",
    "channels",
    "audiences",
    "productFamilies",
    "outputTypes",
    "contentPurposes",
}


@dataclass
class BuildError:
    code: str
    message: str
    element_id: str | None = None


@dataclass
class TargetResult:
    target_id: str
    status: str
    artefact: dict[str, Any] | None = None
    token_counts: dict[str, int] = field(default_factory=dict)
    requirements: list[dict[str, Any]] = field(default_factory=list)
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    errors: list[BuildError] = field(default_factory=list)


class ValidationFailure(Exception):
    def __init__(self, errors: list[str]):
        super().__init__("\n".join(errors))
        self.errors = errors


class _StrictJSONDuplicate(ValueError):
    pass


def _strict_pairs(pairs):
    result = {}
    seen = set()
    for key, value in pairs:
        nkey = unicodedata.normalize("NFC", key)
        if nkey in seen:
            raise _StrictJSONDuplicate(f"duplicate object key: {key}")
        seen.add(nkey)
        result[key] = value
    return result


class _OBDSSafeLoader(yaml.SafeLoader):
    pass


# YAML 1.2 boolean semantics: only true/false are booleans. Values such as NO
# remain strings instead of becoming false.
for ch, resolvers in list(_OBDSSafeLoader.yaml_implicit_resolvers.items()):
    _OBDSSafeLoader.yaml_implicit_resolvers[ch] = [
        item for item in resolvers if item[0] != "tag:yaml.org,2002:bool"
    ]
_OBDSSafeLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|false|True|False|TRUE|FALSE)$"),
    list("tTfF"),
)


def _construct_mapping(loader, node, deep=False):
    mapping = {}
    seen = set()
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise yaml.constructor.ConstructorError(None, None, "mapping keys must be strings", key_node.start_mark)
        nkey = unicodedata.normalize("NFC", key)
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


def _reject_constant(text: str):
    raise ValueError(f"non-finite JSON number is invalid: {text}")


def load_data(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    try:
        if path.suffix.lower() == ".json":
            data = json.loads(text, object_pairs_hook=_strict_pairs, parse_int=_strict_parse_int, parse_constant=_reject_constant)
        else:
            data = yaml.load(text, Loader=_OBDSSafeLoader)
    except (json.JSONDecodeError, _StrictJSONDuplicate, yaml.YAMLError) as exc:
        raise ValidationFailure([f"{path}: parse error: {exc}"]) from exc
    if not isinstance(data, dict):
        raise ValidationFailure([f"{path}: root must be an object"])
    try:
        canonical_json_bytes(data)
    except (TypeError, ValueError) as exc:
        raise ValidationFailure([f"{path}: canonical data error: {exc}"]) from exc
    return data


def save_json(path: str | Path, data: dict[str, Any]) -> None:
    Path(path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def save_yaml(path: str | Path, data: dict[str, Any]) -> None:
    Path(path).write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=110),
        encoding="utf-8",
    )


def _normalised_scope_values(values: list[str]) -> set[str]:
    return {unicodedata.normalize("NFC", value) for value in values}


def _check_scope(scope: Any, *, target: bool) -> list[str]:
    errors: list[str] = []
    if scope is None:
        return errors
    if not isinstance(scope, dict):
        return ["scope must be an object"]
    for dimension, values in scope.items():
        if dimension not in SCOPE_DIMENSIONS:
            errors.append(f"unsupported scope dimension: {dimension}")
            continue
        if not isinstance(values, list) or not values:
            errors.append(f"scope.{dimension} must be a non-empty array")
            continue
        if not all(isinstance(item, str) and item for item in values):
            errors.append(f"scope.{dimension} values must be non-empty strings")
            continue
        if len(_normalised_scope_values(values)) != len(values):
            errors.append(f"scope.{dimension} contains duplicate values after Unicode NFC normalisation")
        if target and len(values) != 1:
            errors.append(f"target scope.{dimension} must contain exactly one value")
    return errors


def _hex_to_rgb(value: str) -> list[int] | None:
    if not isinstance(value, str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        return None
    return [int(value[index:index + 2], 16) for index in (1, 3, 5)]


def _validate_colour_value(element_id: str, value: Any) -> list[str]:
    if not isinstance(value, dict):
        return []
    errors: list[str] = []
    candidates: list[tuple[str, dict[str, Any]]] = []
    if "hex" in value or "rgb" in value:
        candidates.append(("value", value))
    expressions = value.get("expressions")
    if isinstance(expressions, dict):
        for name, expression in expressions.items():
            if isinstance(expression, dict) and (expression.get("colourSpace") == "srgb" or "hex" in expression or "rgb" in expression):
                candidates.append((f"value.expressions.{name}", expression))
    for location, expression in candidates:
        parsed = _hex_to_rgb(expression.get("hex")) if "hex" in expression else None
        if "hex" in expression and parsed is None:
            errors.append(f"{element_id}: {location}.hex must be #RRGGBB")
        rgb = expression.get("rgb") if "rgb" in expression else None
        if rgb is not None and (not isinstance(rgb, list) or len(rgb) != 3 or any(not isinstance(item, int) or isinstance(item, bool) or item < 0 or item > 255 for item in rgb)):
            errors.append(f"{element_id}: {location}.rgb must contain three integers from 0 to 255")
            rgb = None
        if parsed is not None and rgb is not None and parsed != rgb:
            errors.append(f"{element_id}: {location}.hex and {location}.rgb describe different sRGB values")
    return errors


def _manifest_internal_references(element: dict[str, Any]) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    if element.get("family") == "rules" and element.get("state") == "defined":
        value = element.get("value")
        if isinstance(value, dict):
            references = value.get("references", [])
            if isinstance(references, list):
                for index, ref in enumerate(references):
                    if isinstance(ref, str) and ref:
                        refs.append((f"value.references[{index}]", ref))
            required_refs = value.get("requiresDefinedRefs", [])
            if isinstance(required_refs, list):
                for index, ref in enumerate(required_refs):
                    if isinstance(ref, str) and ref:
                        refs.append((f"value.requiresDefinedRefs[{index}]", ref))
            checks = value.get("checks", [])
            if isinstance(checks, list):
                for index, check in enumerate(checks):
                    if not isinstance(check, dict): continue
                    params = check.get("params")
                    if not isinstance(params, dict): continue
                    value_ref = params.get("elementValueRef")
                    if isinstance(value_ref, dict):
                        element_id = value_ref.get("elementId")
                        if isinstance(element_id, str) and element_id:
                            refs.append((f"value.checks[{index}].params.elementValueRef.elementId", element_id))
    return refs


def validate_plan_against_manifest(plan: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    ids = {element.get("id") for element in manifest.get("elements", []) if isinstance(element, dict) and isinstance(element.get("id"), str)}
    for target in plan.get("targets", []):
        if not isinstance(target, dict): continue
        target_id = target.get("id", "<target>")
        for element_id in target.get("requiresDefined", []):
            if element_id not in ids:
                errors.append(f"{target_id}: requiresDefined reference not found: {element_id}")
        style = target.get("styleTexture", {})
        if isinstance(style, dict) and style.get("mode") == "selected":
            for element_id in style.get("elementIds", []):
                if element_id not in ids:
                    errors.append(f"{target_id}: styleTexture reference not found: {element_id}")
        assembly = target.get("contextAssembly", {})
        if isinstance(assembly, dict):
            for element_id in assembly.get("eligibleGuidanceIds", []):
                if element_id not in ids:
                    errors.append(f"{target_id}: contextAssembly.eligibleGuidanceIds reference not found: {element_id}")
    return errors


def _value_contract_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for contract in manifest.get("valueContracts", []):
        if isinstance(contract, dict) and isinstance(contract.get("id"), str):
            result[contract["id"]] = contract
    return result


def _element_contract(manifest: dict[str, Any], element: dict[str, Any]):
    ref = element.get("valueContractRef")
    if not isinstance(ref, str):
        return None
    return _value_contract_map(manifest).get(ref)


def _value_schema_path(schema_ref: str) -> Path | None:
    prefix = "https://openbranddefinition.org/value-schemas/1.0.0/"
    if not isinstance(schema_ref, str) or not schema_ref.startswith(prefix):
        return None
    filename = schema_ref[len(prefix):]
    if not filename or "/" in filename or "\\" in filename:
        return None
    return Path(__file__).resolve().parents[2] / "value-schemas" / filename


def _validate_contract_value(contract: dict[str, Any], element_id: str, value: Any) -> list[str]:
    errors: list[str] = []
    schema_ref = contract.get("schemaRef")
    schema_hash = contract.get("schemaHash")
    path = _value_schema_path(schema_ref)
    if path is None or not path.is_file():
        return [f"{element_id}: unresolved value-contract schemaRef: {schema_ref}"]
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{element_id}: cannot read value-contract schema {schema_ref}: {exc}"]
    actual_schema_hash = sha256_id(schema)
    if actual_schema_hash != schema_hash:
        errors.append(
            f"{element_id}: value-contract schemaHash mismatch for {schema_ref}: "
            f"expected {schema_hash}, got {actual_schema_hash}"
        )
        return errors
    try:
        jsonschema.validate(value, schema)
    except jsonschema.ValidationError as exc:
        errors.append(f"{element_id}: value fails contract schema {schema_ref}: {exc.message}")
        return errors

    validator_ref = contract.get("validatorRef")
    if validator_ref == "obds:validator:colour-consistency-v1":
        errors.extend(_validate_colour_value(element_id, value))
    elif validator_ref not in {None, ""}:
        errors.append(f"{element_id}: unresolved value-contract validatorRef: {validator_ref}")
    return errors


def _optional_hash(value: Any, present: bool):
    return sha256_id(value) if present else None


def _field_changed(old: dict[str, Any], new: dict[str, Any], field: str) -> bool:
    return old.get(field) != new.get(field)


def _semver(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", value or "")
    if not match:
        raise ValueError(f"invalid semantic version: {value}")
    return tuple(int(x) for x in match.groups())

def manifest_change_report(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    old_elements = {
        element["id"]: element
        for element in old.get("elements", [])
        if isinstance(element, dict) and isinstance(element.get("id"), str)
    }
    new_elements = {
        element["id"]: element
        for element in new.get("elements", [])
        if isinstance(element, dict) and isinstance(element.get("id"), str)
    }

    added = [
        {"elementId": element_id, "newHash": sha256_id(new_elements[element_id])}
        for element_id in sorted(new_elements.keys() - old_elements.keys())
    ]
    removed = [
        {"elementId": element_id, "oldHash": sha256_id(old_elements[element_id])}
        for element_id in sorted(old_elements.keys() - new_elements.keys())
    ]

    changed = []
    shape_ids = []
    contract_ids = []
    for element_id in sorted(old_elements.keys() & new_elements.keys()):
        old_element = old_elements[element_id]
        new_element = new_elements[element_id]
        old_hash = sha256_id(old_element)
        new_hash = sha256_id(new_element)
        if old_hash == new_hash:
            continue

        old_has_value = "value" in old_element
        new_has_value = "value" in new_element
        old_value_hash = _optional_hash(old_element.get("value"), old_has_value)
        new_value_hash = _optional_hash(new_element.get("value"), new_has_value)
        old_shape_hash = value_shape_hash(old_element["value"]) if old_has_value else None
        new_shape_hash = value_shape_hash(new_element["value"]) if new_has_value else None
        old_contract = _element_contract(old, old_element)
        new_contract = _element_contract(new, new_element)
        old_contract_id = old_contract.get("id") if old_contract else None
        new_contract_id = new_contract.get("id") if new_contract else None

        kinds = []
        if old_value_hash != new_value_hash:
            kinds.append("value")
        if old_shape_hash != new_shape_hash:
            kinds.append("value_shape")
            shape_ids.append(element_id)
        if (
            old_contract_id != new_contract_id
            or (old_contract or {}).get("shapeHash") != (new_contract or {}).get("shapeHash")
            or (old_contract or {}).get("schemaRef") != (new_contract or {}).get("schemaRef")
            or (old_contract or {}).get("schemaHash") != (new_contract or {}).get("schemaHash")
            or (old_contract or {}).get("validatorRef") != (new_contract or {}).get("validatorRef")
        ):
            kinds.append("contract")
            contract_ids.append(element_id)
        if _element_subject(old_element) != _element_subject(new_element):
            kinds.append("subject")
        for field_name, label in [
            ("state", "state"),
            ("scope", "scope"),
            ("sourceRefs", "sources"),
            ("validity", "validity"),
            ("annotations", "annotations"),
        ]:
            if _field_changed(old_element, new_element, field_name):
                kinds.append(label)
        if any(
            _field_changed(old_element, new_element, field_name)
            for field_name in ("family", "kind", "nature")
        ):
            kinds.append("classification")

        known = {
            "id", "subject", "family", "kind", "nature", "state", "value",
            "scope", "sourceRefs", "validity", "annotations",
        }
        old_metadata = {key: value for key, value in old_element.items() if key not in known}
        new_metadata = {key: value for key, value in new_element.items() if key not in known}
        if old_metadata != new_metadata:
            kinds.append("metadata")

        changed.append({
            "elementId": element_id,
            "oldHash": old_hash,
            "newHash": new_hash,
            "changeKinds": sorted(set(kinds)),
            "oldValueHash": old_value_hash,
            "newValueHash": new_value_hash,
            "oldValueShapeHash": old_shape_hash,
            "newValueShapeHash": new_shape_hash,
            "oldContractId": old_contract_id,
            "newContractId": new_contract_id,
        })

    patch_eligible = (
        not added
        and not removed
        and all(
            set(item["changeKinds"]).issubset({"sources", "annotations"})
            for item in changed
        )
    )
    return {
        "kind": "obds-manifest-change-report",
        "schemaVersion": "1.0.0",
        "oldManifest": {
            "id": old.get("id"),
            "version": old.get("version"),
            "contentHash": manifest_content_hash(old),
        },
        "newManifest": {
            "id": new.get("id"),
            "version": new.get("version"),
            "contentHash": manifest_content_hash(new),
        },
        "added": added,
        "changed": changed,
        "removed": removed,
        "compatibility": {
            "patchEligible": patch_eligible,
            "shapeChangedElementIds": sorted(set(shape_ids)),
            "contractChangedElementIds": sorted(set(contract_ids)),
        },
    }

def validate_manifest_version_transition(old: dict[str, Any], new: dict[str, Any]) -> list[str]:
    try: ov,nv=_semver(old.get('version','')),_semver(new.get('version',''))
    except ValueError as exc:return [str(exc)]
    if nv[0]==ov[0] and nv[1]==ov[1] and nv[2]>ov[2]:
        report=manifest_change_report(old,new)
        if not report['compatibility']['patchEligible']:
            ids=sorted(set(report['compatibility']['shapeChangedElementIds'])|set(report['compatibility']['contractChangedElementIds']))
            return ['PATCH manifest transition contains semantic or structural changes and is not patch-eligible']
    return []


SUPPORTED_BRAND_PROFILES = {"obds-foundation"}


def _parse_timestamp(raw: str, *, field_name: str) -> datetime:
    if not isinstance(raw, str) or not raw:
        raise ValueError(f"{field_name} must be a non-empty date-time string")
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be ISO 8601 date-time") from exc
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")
    return value.astimezone(timezone.utc)


def _element_subject(element: dict[str, Any]) -> str:
    subject = element.get("subject")
    return subject if isinstance(subject, str) and subject else element["id"]


def _valid_at(element: dict[str, Any], as_of: datetime) -> bool:
    validity = element.get("validity") or {}
    raw_from = validity.get("from")
    raw_to = validity.get("to")
    if raw_from and as_of < _parse_timestamp(raw_from, field_name=f"{element['id']}.validity.from"):
        return False
    if raw_to and as_of >= _parse_timestamp(raw_to, field_name=f"{element['id']}.validity.to"):
        return False
    return True


def _scope_more_specific(a: dict[str, list[str]], b: dict[str, list[str]]) -> bool:
    """Return True when a is strictly more restrictive than b."""
    strict = False
    for dimension, b_values in b.items():
        if dimension not in a:
            return False
        a_set = _normalised_scope_values(a[dimension])
        b_set = _normalised_scope_values(b_values)
        if not a_set.issubset(b_set):
            return False
        if a_set != b_set:
            strict = True
    for dimension in a:
        if dimension not in b:
            strict = True
    return strict


def _resolve_subject_precedence(applicable: list[dict[str, Any]]):
    groups: dict[str, list[dict[str, Any]]] = {}
    for element in applicable:
        groups.setdefault(_element_subject(element), []).append(element)
    selected = []
    conflicts = []
    for subject in sorted(groups):
        candidates = groups[subject]
        maximal = []
        for candidate in candidates:
            if any(
                other is not candidate
                and _scope_more_specific(other.get("scope", {}), candidate.get("scope", {}))
                for other in candidates
            ):
                continue
            maximal.append(candidate)
        if len(maximal) == 1:
            selected.append(maximal[0])
        elif len(maximal) > 1:
            conflicts.append({
                "subject": subject,
                "elementIds": sorted(item["id"] for item in maximal),
                "reason": "incomparable_maximal_elements",
            })
    return selected, conflicts


def governed_result_payload(
    manifest: dict[str, Any],
    target: dict[str, Any],
    as_of: str,
    applicable: list[dict[str, Any]],
) -> dict[str, Any]:
    """The OBDS 1.1 governed result: the interoperable governance decision.

    Section 14.3a. Two independent implementations given the same manifest and
    the same build plan MUST produce the same payload, and therefore the same
    `governedResultHash`, regardless of their rendered prose, compiler identity,
    tokenizer or token counts.

    The payload is deliberately small. It carries the decision, not the artefact:

    - `manifest.id` only. The manifest `version` is excluded by ruling R-14: a
      version bump that changes no element value must not move the hash.
    - the build-plan target object minus `maxTokens`, which is capacity and
      therefore implementation-facing.
    - one entry per applicable element with a `valueHash` over the element value
      under section 14.3. Content integrity comes from these hashes, not from
      `manifest.contentHash`, so the payload does not depend on how the manifest
      document was serialised.

    Excluded, with reasons: `sourceRefs` and `annotations`, because a section
    27.2 governance-neutral PATCH must not move the hash; `compiledChecks`,
    because they are derived from the RULE element values already bound here;
    `validFrom`/`validTo`, because they are derived from the selection and
    `asOf`, both present; compiler and tokenizer identity, slots, token counts
    and `artifactHash`, all implementation-facing.
    """
    plan_target = {k: v for k, v in target.items() if k != "maxTokens"}
    selection = []
    for element in sorted(applicable, key=lambda item: _utf16_sort_key(item["id"])):
        defined = element.get("state") == "defined"
        selection.append({
            "elementId": element["id"],
            "subject": element.get("subject", element["id"]),
            "state": element["state"],
            "valueHash": sha256_id(element.get("value")) if defined else None,
        })
    return {
        "kind": "obds-governed-result",
        "schemaVersion": "1.1.0",
        "manifest": {"id": manifest["id"]},
        "target": copy.deepcopy(plan_target),
        "asOf": as_of,
        "selection": selection,
    }


def governed_result_hash(
    manifest: dict[str, Any],
    target: dict[str, Any],
    as_of: str,
    applicable: list[dict[str, Any]],
) -> str:
    return sha256_id(governed_result_payload(manifest, target, as_of, applicable))


def _conflict_is_decision_relevant(
    conflict: dict[str, Any],
    by_id: dict[str, Any],
    target: dict[str, Any],
    rule_required_ids: set[str],
) -> bool:
    """Section 10.2a: would resolving this conflict change what the target gets?

    A hard conflict is a property of a subject. It fails a target only when one
    of its incomparable maximal elements would, if it won, reach that target's
    requirements or its compiled context. Before 1.1.3 every conflict anywhere in
    the scope-matching set failed every target, so a manifest defect on a subject
    a target never reads blocked that target — fail-arbitrary rather than
    fail-closed.
    """
    required = set(target.get("requiresDefined", [])) | rule_required_ids
    style = target.get("styleTexture", {"mode": "all", "elementIds": []})
    style_mode = style.get("mode", "all")
    style_ids = set(style.get("elementIds", []))
    state_policy = target.get("stateMap", {"mode": "none", "kinds": []})
    state_mode = state_policy.get("mode", "none")
    state_kinds = set(state_policy.get("kinds", []))

    for element_id in conflict.get("elementIds", []):
        element = by_id.get(element_id)
        if element is None:
            continue

        # 1. named in requiresDefined. A target cannot opt out of its own
        #    requirements.
        if element_id in required:
            return True

        state = element.get("state")
        family = element.get("family")
        nature = element.get("nature")

        # 2. a blocking or approval-requiring RULE belongs in HARD_BOUNDARIES,
        #    unconditionally.
        if (
            family == "rules"
            and state == "defined"
            and (element.get("value") or {}).get("enforcement")
            in {"block", "require_approval"}
        ):
            return True

        # 3. a defined non-rules fact belongs in FACT_GROUNDING, unconditionally.
        if state == "defined" and nature == "fact" and family != "rules":
            return True

        # 4. carried into STATE_MAP by the target's declared policy.
        if state in {"unknown", "not_defined", "not_applicable"}:
            if state_mode == "all_applicable":
                return True
            if state_mode == "kinds" and element.get("kind") in state_kinds:
                return True

        # 5. carried into STYLE_TEXTURE by the target's declared policy.
        if state == "defined" and (nature == "knowledge" or family == "stance"):
            if style_mode == "all":
                return True
            if style_mode == "selected" and element_id in style_ids:
                return True

    return False


def _selection_validity_window(scope_matching: list[dict[str, Any]], as_of: datetime):
    boundaries = []
    for element in scope_matching:
        validity = element.get("validity") or {}
        for key in ("from", "to"):
            raw = validity.get(key)
            if raw:
                boundaries.append(_parse_timestamp(raw, field_name=f"{element['id']}.validity.{key}"))
    prior = [value for value in boundaries if value <= as_of]
    future = [value for value in boundaries if value > as_of]
    valid_from = max(prior).isoformat().replace("+00:00", "Z") if prior else None
    valid_to = min(future).isoformat().replace("+00:00", "Z") if future else None
    return valid_from, valid_to


def validate_manifest(manifest: dict[str, Any], *, verify_hash: bool = True) -> list[str]:
    errors: list[str] = []

    for key in ("id", "kind", "name", "schemaVersion", "version", "status", "owner", "elements"):
        if key not in manifest:
            errors.append(f"manifest missing: {key}")

    if manifest.get("kind") != "brand-manifest":
        errors.append("manifest kind must be brand-manifest")
    if manifest.get("schemaVersion") != "1.0.0":
        errors.append("manifest schemaVersion must be 1.0.0")
    if manifest.get("status") not in {"draft", "approved", "archived"}:
        errors.append("invalid manifest status")
    if not isinstance(manifest.get("elements"), list):
        errors.append("elements must be an array")
        return errors

    profiles = manifest.get("profiles")
    if not isinstance(profiles, list) or "obds-foundation" not in profiles:
        errors.append("profiles must include obds-foundation")
    elif any(profile not in SUPPORTED_BRAND_PROFILES for profile in profiles):
        unsupported = sorted(profile for profile in profiles if profile not in SUPPORTED_BRAND_PROFILES)
        errors.append("unsupported declared Brand Profile(s): " + ", ".join(unsupported))

    contracts = manifest.get("valueContracts")
    if not isinstance(contracts, list):
        errors.append("valueContracts must be an array")
        contracts = []
    contract_ids: set[str] = set()
    contract_map: dict[str, dict[str, Any]] = {}
    for index, contract in enumerate(contracts):
        prefix = f"valueContracts[{index}]"
        if not isinstance(contract, dict):
            errors.append(f"{prefix} must be an object")
            continue
        contract_id = contract.get("id")
        family = contract.get("family")
        kind = contract.get("kind")
        shape_hash = contract.get("shapeHash")
        schema_ref = contract.get("schemaRef")
        schema_hash = contract.get("schemaHash")
        if not isinstance(contract_id, str) or not contract_id:
            errors.append(f"{prefix}.id must be a non-empty string")
        elif contract_id in contract_ids:
            errors.append(f"duplicate value contract id: {contract_id}")
        else:
            contract_ids.add(contract_id)
            contract_map[contract_id] = contract
        if family not in VALID_FAMILIES:
            errors.append(f"{prefix}.family is invalid: {family}")
        if not isinstance(kind, str) or not kind:
            errors.append(f"{prefix}.kind must be a non-empty string")
        if not isinstance(shape_hash, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", shape_hash):
            errors.append(f"{prefix}.shapeHash must be sha256")
        if not isinstance(schema_ref, str) or not schema_ref:
            errors.append(f"{prefix}.schemaRef must be a non-empty string")
        if not isinstance(schema_hash, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", schema_hash):
            errors.append(f"{prefix}.schemaHash must be sha256")
        if isinstance(schema_ref, str) and schema_ref and isinstance(schema_hash, str):
            schema_path = _value_schema_path(schema_ref)
            if schema_path is None or not schema_path.is_file():
                errors.append(f"{prefix}.schemaRef is unresolved: {schema_ref}")
            else:
                try:
                    schema_payload = json.loads(schema_path.read_text(encoding="utf-8"))
                    actual_schema_hash = sha256_id(schema_payload)
                    if actual_schema_hash != schema_hash:
                        errors.append(
                            f"{prefix}.schemaHash mismatch: expected {schema_hash}, got {actual_schema_hash}"
                        )
                except Exception as exc:
                    errors.append(f"{prefix}.schemaRef cannot be read: {exc}")

    approval = manifest.get("approval")
    if manifest.get("status") == "approved":
        if not isinstance(approval, dict):
            errors.append("approved manifest requires approval")
        else:
            for key in ("approvedBy", "approvedAt", "contentHash"):
                if not approval.get(key):
                    errors.append(f"approved manifest missing approval.{key}")
            if verify_hash and approval.get("contentHash"):
                expected = manifest_content_hash(manifest)
                if approval["contentHash"] != expected:
                    errors.append(
                        f"manifest contentHash mismatch: expected {expected}, got {approval['contentHash']}"
                    )

    seen: set[str] = set()
    for index, element in enumerate(manifest["elements"]):
        prefix = f"elements[{index}]"
        if not isinstance(element, dict):
            errors.append(f"{prefix} must be an object")
            continue

        element_id = element.get("id")
        if not isinstance(element_id, str) or not element_id:
            errors.append(f"{prefix}.id must be a non-empty string")
        elif element_id in seen:
            errors.append(f"duplicate element id: {element_id}")
        else:
            seen.add(element_id)

        subject = element.get("subject")
        if subject is not None and (not isinstance(subject, str) or not subject):
            errors.append(f"{element_id or prefix}: subject must be a non-empty string when declared")

        validity = element.get("validity") or {}
        if not isinstance(validity, dict):
            errors.append(f"{element_id or prefix}: validity must be an object")
        else:
            try:
                start = _parse_timestamp(validity["from"], field_name=f"{element_id}.validity.from") if validity.get("from") else None
                end = _parse_timestamp(validity["to"], field_name=f"{element_id}.validity.to") if validity.get("to") else None
                if start and end and start >= end:
                    errors.append(f"{element_id or prefix}: validity.from must be earlier than validity.to")
            except ValueError as exc:
                errors.append(str(exc))

        if element.get("family") not in VALID_FAMILIES:
            errors.append(f"{element_id or prefix}: invalid family {element.get('family')}")
        if element.get("nature") not in VALID_NATURES:
            errors.append(f"{element_id or prefix}: invalid nature {element.get('nature')}")
        if "supersedes" in element:
            errors.append(f"{element_id or prefix}: supersedes is not part of OBDS Foundation 1.0.0; use the Lineage Profile")

        state = element.get("state")
        if state not in VALID_STATES:
            errors.append(f"{element_id or prefix}: invalid state {state}")
        if state == "defined" and "value" not in element:
            errors.append(f"{element_id or prefix}: defined element requires value")
        if state != "defined" and "value" in element:
            errors.append(f"{element_id or prefix}: non-defined state must not carry value")

        errors.extend(f"{element_id or prefix}: {err}" for err in _check_scope(element.get("scope", {}), target=False))

        needs_contract = (
            state == "defined"
            and "value" in element
            and (
                element.get("nature") == "fact"
                or element.get("family") == "rules"
                or (element.get("family") == "stance" and element.get("kind") == "semantic-boundary")
            )
        )
        if needs_contract:
            contract_ref = element.get("valueContractRef")
            if not isinstance(contract_ref, str) or not contract_ref:
                errors.append(f"{element_id or prefix}: defined structured value requires valueContractRef")
            else:
                contract = contract_map.get(contract_ref)
                if contract is None:
                    errors.append(f"{element_id or prefix}: valueContractRef not found: {contract_ref}")
                else:
                    contract_matches = (
                        contract.get("family") == element.get("family")
                        and (
                            contract.get("kind") == element.get("kind")
                            or (element.get("family") == "rules" and contract.get("kind") == "rule")
                        )
                    )
                    if not contract_matches:
                        errors.append(
                            f"{element_id or prefix}: value contract family/kind does not match element"
                        )
                    actual = value_shape_hash(element.get("value"))
                    if actual != contract.get("shapeHash"):
                        errors.append(
                            f"{element_id or prefix}: value shape mismatch for contract {contract.get('id')}: "
                            f"expected {contract.get('shapeHash')}, got {actual}"
                        )
                    else:
                        errors.extend(_validate_contract_value(contract, element_id or prefix, element.get("value")))

        if element.get("family") == "rules" and state == "defined":
            value = element.get("value")
            if not isinstance(value, dict):
                errors.append(f"{element_id}: rule value must be an object")
                continue
            mode = value.get("validationMode")
            checks = value.get("checks", [])
            validator_ref = value.get("validatorRef")
            if mode == "deterministic" and not checks and not validator_ref:
                errors.append(f"{element_id}: deterministic rule requires checks or validatorRef")
            if checks:
                if not isinstance(checks, list):
                    errors.append(f"{element_id}: checks must be an array")
                else:
                    for check in checks:
                        if not isinstance(check, dict):
                            errors.append(f"{element_id}: check must be an object")
                            continue
                        errors.extend(f"{element_id}: {err}" for err in validate_check(check))

    ids = {element.get("id") for element in manifest.get("elements", []) if isinstance(element, dict) and isinstance(element.get("id"), str)}
    for element in manifest.get("elements", []):
        if not isinstance(element, dict): continue
        source_id = element.get("id", "<element>")
        for location, referenced_id in _manifest_internal_references(element):
            if referenced_id not in ids:
                errors.append(f"{source_id}: internal element reference not found at {location}: {referenced_id}")
    return errors


def validate_plan(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ("id", "kind", "schemaVersion", "asOf", "manifestRef", "compiler", "tokenizer", "targets"):
        if key not in plan:
            errors.append(f"build plan missing: {key}")
    if plan.get("kind") != "obds-build-plan":
        errors.append("build plan kind must be obds-build-plan")
    if plan.get("schemaVersion") != "1.0.0":
        errors.append("build plan schemaVersion must be 1.0.0")
    try:
        _parse_timestamp(plan.get("asOf"), field_name="build plan asOf")
    except ValueError as exc:
        errors.append(str(exc))
    tokenizer = plan.get("tokenizer")
    if not isinstance(tokenizer, dict):
        errors.append("tokenizer must be an object")
    elif (tokenizer.get("id"), tokenizer.get("version")) not in SUPPORTED_TOKENIZERS:
        errors.append(
            f"unsupported tokenizer: {tokenizer.get('id')}@{tokenizer.get('version')}"
        )
    targets = plan.get("targets")
    if not isinstance(targets, list) or not targets:
        errors.append("targets must be a non-empty array")
        return errors

    target_ids: set[str] = set()
    for index, target in enumerate(targets):
        prefix = f"targets[{index}]"
        if not isinstance(target, dict):
            errors.append(f"{prefix} must be an object")
            continue
        target_id = target.get("id")
        if not isinstance(target_id, str) or not target_id:
            errors.append(f"{prefix}.id must be a non-empty string")
        elif target_id in target_ids:
            errors.append(f"duplicate target id: {target_id}")
        else:
            target_ids.add(target_id)

        errors.extend(f"{target_id or prefix}: {err}" for err in _check_scope(target.get("scope", {}), target=True))

        requirements = target.get("requiresDefined", [])
        if not isinstance(requirements, list) or not all(isinstance(item, str) and item for item in requirements):
            errors.append(f"{target_id}: requiresDefined must be a string array")

        style = target.get("styleTexture", {"mode": "all", "elementIds": []})
        if not isinstance(style, dict) or style.get("mode", "all") not in {"all", "selected", "none"}:
            errors.append(f"{target_id}: invalid styleTexture.mode")
        elif style.get("mode") == "selected":
            ids = style.get("elementIds")
            if not isinstance(ids, list) or not ids or not all(isinstance(item, str) and item for item in ids):
                errors.append(f"{target_id}: selected styleTexture requires non-empty elementIds")

        state_map = target.get("stateMap", {"mode": "none", "kinds": []})
        if not isinstance(state_map, dict) or state_map.get("mode", "none") not in {"none", "kinds", "all_applicable"}:
            errors.append(f"{target_id}: invalid stateMap.mode")
        elif state_map.get("mode") == "kinds":
            kinds = state_map.get("kinds")
            if not isinstance(kinds, list) or not kinds or not all(isinstance(item, str) and item for item in kinds):
                errors.append(f"{target_id}: stateMap kinds mode requires non-empty kinds")

        assembly = target.get("contextAssembly")
        if assembly is not None:
            if not isinstance(assembly, dict):
                errors.append(f"{target_id}: contextAssembly must be an object")
            else:
                if assembly.get("deliveryMode") not in {"lookup", "reasoning", "full"}:
                    errors.append(f"{target_id}: invalid contextAssembly.deliveryMode")
                if assembly.get("applicationMode") not in {"create", "review", "compliance"}:
                    errors.append(f"{target_id}: invalid contextAssembly.applicationMode")
                eligible = assembly.get("eligibleGuidanceIds", [])
                if not isinstance(eligible, list) or not all(isinstance(item, str) and item for item in eligible):
                    errors.append(f"{target_id}: contextAssembly.eligibleGuidanceIds must be a string array")
                if assembly.get("noHitPolicy") not in {None, "resolve_before_answer"}:
                    errors.append(f"{target_id}: invalid contextAssembly.noHitPolicy")

        if not isinstance(target.get("maxTokens"), int) or target.get("maxTokens", -1) < 0:
            errors.append(f"{target_id}: maxTokens must be a non-negative integer")
    return errors


def scope_matches(element_scope: dict[str, list[str]], target_scope: dict[str, list[str]]) -> bool:
    for dimension, allowed_values in element_scope.items():
        target_values = target_scope.get(dimension)
        if not target_values:
            return False
        if not _normalised_scope_values(target_values).issubset(
            _normalised_scope_values(allowed_values)
        ):
            return False
    return True


def _format_value(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _rule_line(element: dict[str, Any]) -> str:
    value = element["value"]
    return (
        f"- `{element['id']}` — {value.get('statement', '')} "
        f"[{value.get('validationMode', 'unknown')}, {value.get('enforcement', 'inform')}]"
    )


def _fact_line(element: dict[str, Any]) -> str:
    return f"- `{element['id']}` — {_format_value(element['value'])}"


def _state_line(element: dict[str, Any]) -> str:
    note = ""
    annotations = element.get("annotations") or []
    if annotations:
        note = " " + str(annotations[0]).strip()
    return f"- `{element['id']}` — {element['state']}.{note}"


def _style_block(element: dict[str, Any]) -> str:
    return f"`{element['id']}`\n\n{_format_value(element['value'])}"


def _resolve_path(value: Any, path: str) -> Any:
    current = value
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            raise KeyError(path)
    return current


def _materialise_checks(
    applicable: list[dict[str, Any]],
    elements_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[BuildError]]:
    compiled: list[dict[str, Any]] = []
    errors: list[BuildError] = []

    for element in applicable:
        if element.get("family") != "rules" or element.get("state") != "defined":
            continue
        value = element["value"]
        for source_check in value.get("checks", []):
            check = copy.deepcopy(source_check)
            params = check.setdefault("params", {})
            ref = params.pop("elementValueRef", None)
            if ref is not None:
                if not isinstance(ref, dict) or not ref.get("elementId") or not ref.get("path"):
                    errors.append(BuildError(
                        "OBDS-CHECK-REF-INVALID",
                        "elementValueRef requires elementId and path",
                        element["id"],
                    ))
                    continue
                source_element = elements_by_id.get(ref["elementId"])
                if not source_element or source_element.get("state") != "defined":
                    errors.append(BuildError(
                        "OBDS-CHECK-REF-MISSING",
                        f"check reference is not defined: {ref['elementId']}",
                        element["id"],
                    ))
                    continue
                try:
                    literal = _resolve_path(source_element["value"], ref["path"])
                except KeyError:
                    errors.append(BuildError(
                        "OBDS-CHECK-REF-PATH",
                        f"check reference path not found: {ref['elementId']}:{ref['path']}",
                        element["id"],
                    ))
                    continue
                if not isinstance(literal, str):
                    errors.append(BuildError(
                        "OBDS-CHECK-REF-TYPE",
                        "resolved literal must be a string",
                        element["id"],
                    ))
                    continue
                params["literal"] = literal

            validation_errors = validate_check(check)
            if validation_errors:
                for message in validation_errors:
                    errors.append(BuildError("OBDS-CHECK-INVALID", message, element["id"]))
                continue

            compiled.append({
                "ruleElementId": element["id"],
                "primitive": check["primitive"],
                "phase": check.get("phase", "postflight"),
                "enforcement": value.get("enforcement", "block"),
                "params": params,
            })
    return compiled, errors


def _whitespace_tokens(text: str) -> int:
    return len(re.findall(r"\S+", text))


def build_target(
    manifest: dict[str, Any],
    plan: dict[str, Any],
    target: dict[str, Any],
) -> TargetResult:
    result = TargetResult(target_id=target["id"], status="failed")

    if manifest.get("status") != "approved":
        result.errors.append(BuildError("OBDS-BUILD-MANIFEST-NOT-APPROVED", "manifest is not approved"))
        return result

    expected_manifest_hash = manifest_content_hash(manifest)
    if manifest.get("approval", {}).get("contentHash") != expected_manifest_hash:
        result.errors.append(BuildError("OBDS-BUILD-MANIFEST-HASH", "manifest contentHash mismatch"))
        return result

    manifest_ref = plan["manifestRef"]
    if (
        manifest_ref.get("id") != manifest.get("id")
        or manifest_ref.get("version") != manifest.get("version")
        or manifest_ref.get("contentHash") != expected_manifest_hash
    ):
        result.errors.append(BuildError("OBDS-BUILD-MANIFEST-REF", "build plan does not reference this exact manifest"))
        return result

    target_scope = target.get("scope", {})
    elements = manifest["elements"]
    by_id = {element["id"]: element for element in elements}
    as_of = _parse_timestamp(plan["asOf"], field_name="build plan asOf")

    scope_matching = [
        element for element in elements
        if scope_matches(element.get("scope", {}), target_scope)
    ]
    time_applicable = [element for element in scope_matching if _valid_at(element, as_of)]
    applicable, conflicts = _resolve_subject_precedence(time_applicable)
    rule_requirements = [
        (required_id, element["id"])
        for element in applicable
        if element.get("family") == "rules" and element.get("state") == "defined"
        for required_id in element.get("value", {}).get("requiresDefinedRefs", [])
    ]
    rule_required_ids = {required_id for required_id, _ in rule_requirements}
    # Section 10.2a: a conflict fails this target only when the subject is
    # decision-relevant to it. An irrelevant conflict is still reported, marked,
    # so a manifest defect is never silently discarded.
    annotated_conflicts = []
    for conflict in conflicts:
        relevant = _conflict_is_decision_relevant(
            conflict, by_id, target, rule_required_ids
        )
        annotated_conflicts.append({**conflict, "decisionRelevant": relevant})
        if relevant:
            result.errors.append(BuildError(
                "OBDS-BUILD-SUBJECT-CONFLICT",
                f"semantic subject {conflict['subject']} has incomparable maximal elements: "
                + ", ".join(conflict["elementIds"]),
            ))
    result.conflicts = annotated_conflicts
    valid_from, valid_to = _selection_validity_window(scope_matching, as_of)
    applicable_ids = {element["id"] for element in applicable}

    # OBDS 1.1: the four causes of a failed requirement are reported with distinct
    # codes. Before 1.1 they all surfaced as OBDS-BUILD-REQUIRED-NOT-DEFINED with
    # actualState `not_applicable`, so an operator could not tell a mis-scoped
    # target from an expired fact from a truth that was never curated. Each needs
    # a different human response.
    scope_matching_ids = {element["id"] for element in scope_matching}
    time_applicable_ids = {element["id"] for element in time_applicable}

    requirements = [
        (element_id, None) for element_id in target.get("requiresDefined", [])
    ] + rule_requirements
    for element_id, requiring_rule_id in requirements:
        element = by_id.get(element_id)
        code = "OBDS-BUILD-REQUIRED-NOT-DEFINED"
        if element is None:
            actual = "missing"
            passed = False
            code = "OBDS-BUILD-REQUIRED-NOT-FOUND"
        elif element_id not in scope_matching_ids:
            actual = "not_applicable"
            passed = False
            code = "OBDS-BUILD-REQUIRED-OUT-OF-SCOPE"
        elif element_id not in time_applicable_ids:
            actual = "not_applicable"
            passed = False
            code = "OBDS-BUILD-REQUIRED-EXPIRED"
        elif element_id not in applicable_ids:
            # In scope and valid, but a more specific element won its subject.
            actual = "not_applicable"
            passed = False
        else:
            actual = element["state"]
            passed = actual == "defined"

        requirement = {
            "elementId": element_id,
            "expectedState": "defined",
            "actualState": actual,
            "result": "pass" if passed else "fail",
        }
        if requiring_rule_id is not None:
            requirement["requiringRuleElementId"] = requiring_rule_id
        result.requirements.append(requirement)
        if not passed:
            result.errors.append(BuildError(
                code,
                f"{element_id}: expected defined, got {actual}",
                element_id,
            ))

    style = target.get("styleTexture", {"mode": "all", "elementIds": []})
    if style.get("mode") == "selected":
        for element_id in style.get("elementIds", []):
            element = by_id.get(element_id)
            if (
                element is None
                or element_id not in applicable_ids
                or element.get("state") != "defined"
                or element.get("nature") != "knowledge"
            ):
                result.errors.append(BuildError(
                    "OBDS-BUILD-STYLE-SELECTION",
                    f"selected style element is not applicable defined KNOWLEDGE: {element_id}",
                    element_id,
                ))

    compiled_checks, check_errors = _materialise_checks(applicable, by_id)
    result.errors.extend(check_errors)

    if result.errors:
        return result

    hard_elements = [
        element for element in applicable
        if (
            element.get("family") == "rules"
            and element.get("state") == "defined"
            and element.get("value", {}).get("enforcement") in {"block", "require_approval"}
        )
    ]
    fact_elements = [
        element for element in applicable
        if (
            element.get("state") == "defined"
            and element.get("nature") == "fact"
            and element.get("family") != "rules"
        )
    ]

    state_policy = target.get("stateMap", {"mode": "none", "kinds": []})
    if state_policy.get("mode") == "all_applicable":
        state_elements = [
            element for element in applicable
            if element.get("state") in {"unknown", "not_defined", "not_applicable"}
        ]
        state_coverage = "complete"
    elif state_policy.get("mode") == "kinds":
        kinds = set(state_policy.get("kinds", []))
        state_elements = [
            element for element in applicable
            if element.get("state") in {"unknown", "not_defined", "not_applicable"}
            and element.get("kind") in kinds
        ]
        state_coverage = "partial"
    else:
        state_elements = []
        state_coverage = "none"

    knowledge = [
        element for element in applicable
        if element.get("state") == "defined"
        and (element.get("nature") == "knowledge" or element.get("family") == "stance")
    ]
    if style.get("mode", "all") == "selected":
        selected = set(style.get("elementIds", []))
        knowledge = [element for element in knowledge if element["id"] in selected]
    elif style.get("mode") == "none":
        knowledge = []

    # OBDS 1.1, D-5. Section 13.2: "HARD_BOUNDARIES and FACT_GROUNDING always
    # include every applicable element required by the target." Context selection
    # governs additional content only and MUST NOT remove a required element.
    #
    # Before 1.1 a knowledge-natured element named in requiresDefined was verified
    # as `defined`, the build succeeded, and the element was absent from the
    # artefact whenever styleTexture.mode was `none` or a `selected` list omitted
    # it. A build that verifies required truth as present and then ships a context
    # without it is the failure this rule closes.
    required_ids = list(target.get("requiresDefined", []))
    already_placed = {e["id"] for e in hard_elements + fact_elements + state_elements + knowledge}
    for element_id in required_ids:
        if element_id in already_placed:
            continue
        element = by_id.get(element_id)
        if element is None or element_id not in applicable_ids:
            continue
        if element.get("state") != "defined":
            continue
        knowledge.append(element)
        already_placed.add(element_id)

    hard_elements.sort(key=lambda item: item["id"])
    fact_elements.sort(key=lambda item: item["id"])
    state_elements.sort(key=lambda item: item["id"])
    knowledge.sort(key=lambda item: item["id"])
    compiled_checks.sort(key=lambda item: (item["ruleElementId"], item["primitive"], item["phase"]))

    slots = {
        "hardBoundaries": "\n".join(_rule_line(e) if e.get("family") == "rules" else _state_line(e) for e in hard_elements),
        "factGrounding": "\n".join(_fact_line(e) for e in fact_elements),
        "stateMap": "\n".join(_state_line(e) for e in state_elements),
        "styleTexture": "\n\n".join(_style_block(e) for e in knowledge),
    }
    token_counts = {
        "hardBoundaries": _whitespace_tokens(slots["hardBoundaries"]),
        "factGrounding": _whitespace_tokens(slots["factGrounding"]),
        "stateMap": _whitespace_tokens(slots["stateMap"]),
        "styleTexture": _whitespace_tokens(slots["styleTexture"]),
    }
    token_counts["total"] = sum(token_counts.values())
    token_counts["max"] = target["maxTokens"]
    result.token_counts = token_counts

    if token_counts["total"] > target["maxTokens"]:
        result.errors.append(BuildError(
            "OBDS-BUILD-TOKEN-OVERFLOW",
            f"target uses {token_counts['total']} tokens but allows {target['maxTokens']}",
        ))
        return result

    plan_hash = sha256_id(plan)
    artefact: dict[str, Any] = {
        "kind": "obds-compiled-brand-context",
        "schemaVersion": "1.1.0",
        "id": f"{manifest['id']}:context:{target['id']}",
        "targetId": target["id"],
        "manifest": {
            "id": manifest["id"],
            "version": manifest["version"],
            "contentHash": expected_manifest_hash,
        },
        "build": {
            "planId": plan["id"],
            "planHash": plan_hash,
            "compilerId": COMPILER_ID,
            "compilerVersion": COMPILER_VERSION,
            "asOf": plan["asOf"],
        },
        "scope": target_scope,
        "tokenBudget": {
            "tokenizerId": plan["tokenizer"]["id"],
            "tokenizerVersion": plan["tokenizer"]["version"],
            "max": target["maxTokens"],
            "actual": token_counts["total"],
        },
        "checkRegistryVersion": 1,
        "compiledChecks": compiled_checks,
        "stateMapCoverage": state_coverage,
        "stateMapEntryCount": len(state_elements),
        "validFrom": valid_from,
        "validTo": valid_to,
        "includedElementIds": sorted(
            {element["id"] for element in hard_elements + fact_elements + state_elements + knowledge}
        ),
        "availableElementIds": sorted(element["id"] for element in applicable),
        "elementRecords": copy.deepcopy(sorted(applicable, key=lambda item: item["id"])),
        "governedResultHash": governed_result_hash(manifest, target, plan["asOf"], applicable),
        "contextAssembly": copy.deepcopy(target.get("contextAssembly")),
        "slots": slots,
    }
    artefact["artifactHash"] = artefact_hash(artefact)

    result.status = "ready"
    result.artefact = artefact
    return result


def build_all(
    manifest: dict[str, Any],
    plan: dict[str, Any],
    *,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    manifest_errors = validate_manifest(manifest)
    plan_errors = validate_plan(plan)
    cross_errors = validate_plan_against_manifest(plan, manifest)
    if manifest_errors or plan_errors or cross_errors:
        raise ValidationFailure(manifest_errors + plan_errors + cross_errors)

    output = Path(output_dir) if output_dir else None
    if output:
        output.mkdir(parents=True, exist_ok=True)

    target_results = [build_target(manifest, plan, target) for target in plan["targets"]]
    report_targets: list[dict[str, Any]] = []

    for target_result in target_results:
        target_report = {
            "targetId": target_result.target_id,
            "status": target_result.status,
            "artifactRef": None,
            "artifactHash": None,
            "tokenCounts": target_result.token_counts,
            "budgetStatus": (
                "overflow"
                if any(error.code == "OBDS-BUILD-TOKEN-OVERFLOW" for error in target_result.errors)
                else "within_budget"
                if target_result.status == "ready"
                else "not_measured"
            ),
            "requirements": target_result.requirements,
            "conflicts": target_result.conflicts,
            "errors": [
                {
                    "code": error.code,
                    "message": error.message,
                    "elementId": error.element_id,
                }
                for error in target_result.errors
            ],
        }

        if target_result.artefact is not None and output:
            filename = f"{target_result.target_id}.context.json"
            save_json(output / filename, target_result.artefact)
            (output / f"{target_result.target_id}.context.md").write_text(
                render_markdown(target_result.artefact),
                encoding="utf-8",
            )
            target_report["artifactRef"] = filename
            target_report["artifactHash"] = target_result.artefact["artifactHash"]
        elif target_result.artefact is not None:
            target_report["artifactHash"] = target_result.artefact["artifactHash"]

        report_targets.append(target_report)

    report = {
        "kind": "obds-build-report",
        "schemaVersion": "1.0.0",
        "builtAt": datetime.now(timezone.utc).isoformat(),
        "planId": plan["id"],
        "planHash": sha256_id(plan),
        "manifestId": manifest["id"],
        "manifestVersion": manifest["version"],
        "manifestContentHash": manifest_content_hash(manifest),
        "compilerVersion": COMPILER_VERSION,
        "targets": report_targets,
    }
    if output:
        save_yaml(output / "build-report.yaml", report)
    return report


def render_markdown(artefact: dict[str, Any]) -> str:
    slots = artefact["slots"]
    return (
        f"<!-- generated from {artefact['artifactHash']} -->\n\n"
        f"[HARD_BOUNDARIES]\n{slots['hardBoundaries']}\n\n"
        f"[FACT_GROUNDING]\n{slots['factGrounding']}\n\n"
        f"[STATE_MAP]\n{slots['stateMap']}\n\n"
        f"[STYLE_TEXTURE]\n{slots['styleTexture']}\n"
    )
