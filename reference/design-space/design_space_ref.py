from __future__ import annotations

import math


def resolve_measurement(measurement, basis_amount=None, basis_unit=None):
    mode = measurement["mode"]
    amount = float(measurement["amount"])

    system = measurement.get("system")
    if system:
        if system["type"] == "relative" and not system.get("id"):
            raise ValueError("relative measurement system requires id")
        if mode == "relative" and system["type"] != "relative":
            raise ValueError("relative measurement cannot declare absolute system")
        if mode == "absolute" and system["type"] != "absolute":
            raise ValueError("absolute measurement cannot declare relative system")

    if mode == "relative":
        if basis_amount is None:
            raise ValueError("relative measurement requires basis amount")
        value = amount * float(basis_amount)
        unit = basis_unit
    else:
        value = amount
        unit = measurement["unit"]

    lower = measurement.get("min")
    upper = measurement.get("max")
    if lower and upper:
        if lower["unit"] != upper["unit"]:
            raise ValueError("min/max unit mismatch")
        if float(lower["amount"]) > float(upper["amount"]):
            raise ValueError("measurement min exceeds max")

    for bound_name, fn in (("min", max), ("max", min)):
        bound = measurement.get(bound_name)
        if bound:
            if unit != bound["unit"]:
                raise ValueError("bound unit mismatch")
            value = fn(value, float(bound["amount"]))

    return {"amount": value, "unit": unit, "quantityKind": measurement.get("quantityKind")}


def resolve_relation(value_a, value_b, relation):
    mode = relation["relation"]
    if mode == "additive":
        return value_a + value_b
    if mode == "subsuming":
        dominant = relation["dominantElementId"]
        between = relation["between"]
        if dominant not in between:
            raise ValueError("dominantElementId must be one of between")
        return value_a if between[0] == dominant else value_b
    if mode == "exclusive":
        raise ValueError("exclusive relation cannot co-apply")
    raise ValueError("unsupported relation")


def _boxes_intersect(a, b):
    return not (
        a["x"] + a["width"] <= b["x"]
        or b["x"] + b["width"] <= a["x"]
        or a["y"] + a["height"] <= b["y"]
        or b["y"] + b["height"] <= a["y"]
    )


def _select(record, role):
    return [obj for obj in record["objects"] if role in obj["roles"]]


def check_min_size(record, params):
    role = params["role"]
    metric = params.get("metric", "height")
    minimum = float(params["min"])
    selected = _select(record, role)
    if not selected:
        return {"passed": False, "message": f"no object with role {role}"}

    failures = []
    for obj in selected:
        if metric in {"width", "height"}:
            value = float(obj["box"][metric])
        elif metric == "shorter_side":
            value = min(float(obj["box"]["width"]), float(obj["box"]["height"]))
        else:
            if metric not in obj.get("metrics", {}):
                failures.append(f"{obj['objectId']}: metric {metric} missing")
                continue
            value = float(obj["metrics"][metric])

        if value < minimum:
            failures.append(f"{obj['objectId']}: {value} < {minimum}")

    return {
        "passed": not failures,
        "message": "pass" if not failures else "; ".join(failures),
    }


def check_clear_zone(record, params):
    protected_role = params["protectedRole"]
    intruder_roles = set(params["intruderRoles"])
    zone = float(params["zone"])

    protected = _select(record, protected_role)
    intruders = [
        obj for obj in record["objects"]
        if intruder_roles.intersection(obj["roles"])
    ]
    failures = []

    for p in protected:
        expanded = {
            "x": p["box"]["x"] - zone,
            "y": p["box"]["y"] - zone,
            "width": p["box"]["width"] + 2 * zone,
            "height": p["box"]["height"] + 2 * zone,
        }
        for i in intruders:
            if i["objectId"] == p["objectId"]:
                continue
            if _boxes_intersect(expanded, i["box"]):
                failures.append(f"{i['objectId']} enters clear zone of {p['objectId']}")

    return {
        "passed": not failures,
        "message": "pass" if not failures else "; ".join(failures),
    }


def check_contains(record, params):
    child_role = params["childRole"]
    inset = float(params.get("inset", 0))
    children = _select(record, child_role)

    if params.get("container") == "canvas":
        container = {
            "x": inset,
            "y": inset,
            "width": record["canvas"]["width"] - 2 * inset,
            "height": record["canvas"]["height"] - 2 * inset,
        }
    else:
        role = params["containerRole"]
        containers = _select(record, role)
        if len(containers) != 1:
            return {"passed": False, "message": f"expected one container role {role}"}
        b = containers[0]["box"]
        container = {
            "x": b["x"] + inset,
            "y": b["y"] + inset,
            "width": b["width"] - 2 * inset,
            "height": b["height"] - 2 * inset,
        }

    failures = []
    for obj in children:
        b = obj["box"]
        inside = (
            b["x"] >= container["x"]
            and b["y"] >= container["y"]
            and b["x"] + b["width"] <= container["x"] + container["width"]
            and b["y"] + b["height"] <= container["y"] + container["height"]
        )
        if not inside:
            failures.append(f"{obj['objectId']} leaves container")

    return {"passed": not failures, "message": "pass" if not failures else "; ".join(failures)}


def check_no_overlap(record, params):
    a_role = params["aRole"]
    b_role = params["bRole"]
    aa = _select(record, a_role)
    bb = _select(record, b_role)
    failures = []

    for a in aa:
        for b in bb:
            if a["objectId"] == b["objectId"]:
                continue
            if _boxes_intersect(a["box"], b["box"]):
                failures.append(f"{a['objectId']} overlaps {b['objectId']}")

    return {"passed": not failures, "message": "pass" if not failures else "; ".join(failures)}


def run_visual_check(record, check):
    primitive = check["primitive"]
    params = check["params"]
    if primitive == "visual.min_size":
        return check_min_size(record, params)
    if primitive == "visual.clear_zone":
        return check_clear_zone(record, params)
    if primitive == "visual.contains":
        return check_contains(record, params)
    if primitive == "visual.no_overlap":
        return check_no_overlap(record, params)
    raise ValueError("unsupported visual primitive")


def validate_coverage(coverage):
    if coverage["coverage"] != "complete":
        return True
    for modality, state in coverage["modalities"].items():
        if state not in {"complete", "not_applicable"}:
            raise ValueError(f"complete coverage invalid: {modality} is {state}")
    return True


def validate_rule_dependencies(manifest, rule):
    by_id = {e["id"]: e for e in manifest["elements"]}
    for ref in rule.get("value", {}).get("requiresDefinedRefs", []):
        if ref not in by_id:
            raise ValueError(f"missing dependency {ref}")
        if by_id[ref]["state"] != "defined":
            raise ValueError(f"dependency {ref} is {by_id[ref]['state']}")
    return True


def validate_contradictions(manifest, contradiction_records):
    by_id = {e["id"]: e for e in manifest["elements"]}
    for record in contradiction_records:
        element = by_id[record["elementId"]]
        if record["status"] == "unresolved" and element["state"] != "unknown":
            raise ValueError(
                f"unresolved contradiction requires unknown current state: {element['id']}"
            )
    return True


def validate_composition_profile(role_system, hierarchy, omission):
    roles = [r["id"] for r in role_system["roles"]]
    if len(roles) != len(set(roles)):
        raise ValueError("duplicate composition role")
    known = set(roles)

    hierarchy_roles = [r for tier in hierarchy["tiers"] for r in tier]
    if not set(hierarchy_roles).issubset(known):
        raise ValueError("identity hierarchy references unknown role")

    never_omit = set(omission["neverOmit"])
    omit_order = set(omission["omitOrder"])
    if not never_omit.issubset(known) or not omit_order.issubset(known):
        raise ValueError("omission priority references unknown role")
    if never_omit.intersection(omit_order):
        raise ValueError("role cannot be both neverOmit and omitOrder")

    return True



def validate_never_omit_presence(record, omission):
    present = {role for obj in record.get("objects", []) for role in obj.get("roles", [])}
    missing = [role for role in omission.get("neverOmit", []) if role not in present]
    if missing:
        raise ValueError("neverOmit role missing from render geometry: " + ", ".join(sorted(missing)))
    return True
