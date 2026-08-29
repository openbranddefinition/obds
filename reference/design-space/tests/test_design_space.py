from pathlib import Path
import importlib.util
import json
import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location("ref", ROOT / "design_space_ref.py")
ref = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ref)


def data(name):
    return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))


def schema(name):
    return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))


def test_measurement_floor():
    m = data("measurement-floor.json")
    jsonschema.validate(m, schema("measurement-v2.schema.json"))
    result = ref.resolve_measurement(m, basis_amount=8, basis_unit="px")
    assert result["amount"] == 9
    assert result["quantityKind"] == "cap-height"


def test_measurement_ceiling():
    m = data("measurement-ceiling.json")
    result = ref.resolve_measurement(m, basis_amount=20, basis_unit="px")
    assert result["amount"] == 18


def test_absolute_measurement_does_not_scale():
    m = data("measurement-absolute.json")
    result = ref.resolve_measurement(m, basis_amount=999, basis_unit="px")
    assert result["amount"] == 40


def test_additive_relation():
    r = data("relation-additive.json")
    jsonschema.validate(r, schema("composition-relation.schema.json"))
    assert ref.resolve_relation(7.2, 7.2, r) == 14.4


def test_subsuming_relation():
    r = data("relation-subsuming.json")
    assert ref.resolve_relation(7.2, 14.4, r) == 14.4


def test_exclusive_relation_refuses_coapplication():
    r = data("relation-exclusive.json")
    with pytest.raises(ValueError, match="exclusive"):
        ref.resolve_relation(1, 1, r)


def test_min_size():
    g = data("render-geometry-record.json")
    jsonschema.validate(g, schema("render-geometry-record.schema.json"))
    result = ref.run_visual_check(
        g,
        {
            "primitive": "visual.min_size",
            "enforcement": "block",
            "params": {"role": "headline", "metric": "cap-height", "min": 12},
        },
    )
    assert result["passed"] is True


def test_clear_zone_detects_intrusion():
    g = data("render-geometry-record.json")
    result = ref.run_visual_check(
        g,
        {
            "primitive": "visual.clear_zone",
            "enforcement": "block",
            "params": {
                "protectedRole": "brand-logo",
                "intruderRoles": ["partner-logo"],
                "zone": 25,
            },
        },
    )
    assert result["passed"] is False


def test_contains():
    g = data("render-geometry-record.json")
    result = ref.run_visual_check(
        g,
        {
            "primitive": "visual.contains",
            "enforcement": "block",
            "params": {
                "childRole": "headline",
                "container": "canvas",
                "inset": 10,
            },
        },
    )
    assert result["passed"] is True


def test_no_overlap():
    g = data("render-geometry-record.json")
    result = ref.run_visual_check(
        g,
        {
            "primitive": "visual.no_overlap",
            "enforcement": "block",
            "params": {"aRole": "brand-logo", "bRole": "partner-logo"},
        },
    )
    assert result["passed"] is True


def test_complete_coverage_rejects_unassessed_figures():
    c = data("coverage-complete-invalid.json")
    jsonschema.validate(c, schema("curation-coverage.schema.json"))
    with pytest.raises(ValueError, match="figures"):
        ref.validate_coverage(c)


def test_partial_coverage_accepts_partial_figures():
    c = data("coverage-partial-valid.json")
    assert ref.validate_coverage(c) is True


def test_rule_dependency_unknown_fails():
    manifest = {
        "elements": [
            {"id": "design.template.registry", "state": "unknown"},
            {
                "id": "rule.special-template.locked",
                "state": "defined",
                "value": {
                    "requiresDefinedRefs": ["design.template.registry"]
                },
            },
        ]
    }
    rule = manifest["elements"][1]
    with pytest.raises(ValueError, match="unknown"):
        ref.validate_rule_dependencies(manifest, rule)


def test_unresolved_contradiction_requires_unknown():
    manifest = {
        "elements": [
            {"id": "design.frame.thickness", "state": "unknown"}
        ]
    }
    records = [data("source-contradiction-record.json")]
    assert ref.validate_contradictions(manifest, records) is True


def test_unresolved_contradiction_rejects_defined_current_value():
    manifest = {
        "elements": [
            {"id": "design.frame.thickness", "state": "defined"}
        ]
    }
    records = [data("source-contradiction-record.json")]
    with pytest.raises(ValueError, match="unknown current state"):
        ref.validate_contradictions(manifest, records)


def test_composition_role_hierarchy_and_omission_refs():
    roles = data("composition-role-system.json")
    hierarchy = data("identity-hierarchy.json")
    omission = data("omission-priority.json")
    jsonschema.validate(roles, schema("composition-role-system.schema.json"))
    jsonschema.validate(hierarchy, schema("identity-hierarchy.schema.json"))
    jsonschema.validate(omission, schema("omission-priority.schema.json"))
    assert ref.validate_composition_profile(roles, hierarchy, omission) is True


def test_measurement_observation_is_non_authoritative():
    obs = data("measurement-observation.json")
    jsonschema.validate(obs, schema("measurement-observation.schema.json"))
    assert obs["authority"] == "non-authoritative"


def test_curation_assessment_schema():
    assessment = data("curation-assessment.json")
    jsonschema.validate(assessment, schema("curation-assessment.schema.json"))
    assert "figures" in assessment["searchedModalities"]
