from pathlib import Path
import json
import re
import yaml

ROOT=Path(__file__).resolve().parents[2]
def _schema_dir(root, name):
    """Resolve schemas/ and value-schemas/ in either supported layout: flat in an
    unpacked release archive, under 1.0.0/ in the working repository."""
    flat = root / name
    if any(flat.glob("*.json")):
        return flat
    versioned = flat / "1.0.0"
    if any(versioned.glob("*.json")):
        return versioned
    return flat
SCHEMAS=_schema_dir(ROOT,'schemas')
VALUE_SCHEMAS=_schema_dir(ROOT,'value-schemas')
SPEC=(ROOT/'OBDS-1.0.4.md').read_text(encoding='utf-8')


def test_single_normative_spec_no_core_file():
    assert (ROOT/'OBDS-1.0.4.md').exists()
    assert not (ROOT/'OBDS-CORE-1.0.0.md').exists()


def test_no_active_core_nomenclature_in_spec():
    prohibited=['OBDS FOUNDATION / CORE','CORE Check Registry v1','OBDS CORE does','CORE default','compiled CORE checks']
    for term in prohibited:
        assert term not in SPEC


def test_foundation_profile_is_explicit():
    schema=json.loads((SCHEMAS/'brand-manifest.schema.json').read_text())
    assert 'profiles' in schema['required']
    assert schema['properties']['profiles']['contains']['const']=='obds-foundation'


def test_all_schema_ids_are_1_0_0():
    for path in (SCHEMAS).glob('*.json'):
        obj=json.loads(path.read_text())
        if '$id' in obj:
            assert '/1.0.0/' in obj['$id'], path.name


def test_profile_contract_is_in_single_spec():
    for phrase in ['One specification. One Foundation. Optional capabilities.', 'obds-composition', 'obds-visual-operations', 'Foundation Check Registry v1']:
        assert phrase in SPEC


def test_spec_has_no_em_or_en_dash():
    assert '—' not in SPEC
    assert '–' not in SPEC


def test_reference_manifests_validate_as_1_0():
    import jsonschema
    schema=json.loads((SCHEMAS/'brand-manifest.schema.json').read_text())
    for suite in ['foundation','context-delivery','context-assembly']:
        if suite=='foundation':
            paths=(ROOT/'reference'/'foundation'/'examples').glob('*/manifest.yaml')
        else:
            paths=[ROOT/'reference'/suite/'examples'/'manifest.yaml']
        for path in paths:
            obj=yaml.safe_load(path.read_text())
            jsonschema.validate(obj,schema)


def test_no_pre_1_0_ground_rule_dependency():
    assert '0.9.6 Ground Rules' not in SPEC


def test_foundation_manifest_schema_requires_value_contracts():
    schema=json.loads((SCHEMAS/'brand-manifest.schema.json').read_text()); assert 'valueContracts' in schema['required']

def test_spec_declares_shape_integrity_gate():
    for phrase in ['OBDS JSON Shape v1','value_shape','PATCH transition','A canonical hash proves byte identity']: assert phrase in SPEC



def _canonical_hash(value):
    import hashlib
    payload=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")
    return "sha256:"+hashlib.sha256(payload).hexdigest()


def test_schema_index_capabilities_and_files_are_synchronised():
    registry=json.loads((ROOT/'OBDS-1.0.4-CAPABILITY-REGISTRY.json').read_text())
    index=json.loads((ROOT/'OBDS-1.0.4-SCHEMA-INDEX.json').read_text())
    allowed={'foundation'}
    allowed.update(item['id'] for item in registry['runtimeCapabilities'])
    allowed.update(item['id'] for item in registry['brandProfiles'])
    indexed_schema_files={item['file'] for item in index['schemas']}
    actual_schema_files={path.name for path in (SCHEMAS).glob('*.json')}
    assert indexed_schema_files==actual_schema_files
    indexed_value_files={item['file'] for item in index['valueSchemas']}
    actual_value_files={path.name for path in (VALUE_SCHEMAS).glob('*.json')}
    assert indexed_value_files==actual_value_files
    for item in index['schemas']+index['valueSchemas']:
        assert item['capability'] in allowed


def test_schema_index_ids_and_value_schema_hashes_match_files():
    index=json.loads((ROOT/'OBDS-1.0.4-SCHEMA-INDEX.json').read_text())
    seen_ids=set()
    for item in index['schemas']:
        obj=json.loads((SCHEMAS/item['file']).read_text())
        assert obj['$id']==item['id']
        assert item['id'] not in seen_ids
        seen_ids.add(item['id'])
    for item in index['valueSchemas']:
        obj=json.loads((VALUE_SCHEMAS/item['file']).read_text())
        assert obj['$id']==item['id']
        assert item['schemaHash']==_canonical_hash(obj)
        assert item['id'] not in seen_ids
        seen_ids.add(item['id'])


def test_foundation_standard_value_contract_registry_matches_public_value_schemas():
    registry=json.loads((ROOT/'OBDS-1.0.4-CAPABILITY-REGISTRY.json').read_text())
    declared=set(registry['foundation']['standardValueContracts'])
    public={path.name.removesuffix('.schema.json') for path in (VALUE_SCHEMAS).glob('*.json')}
    assert declared==public


def test_rc5_canonical_implementations_are_identical():
    paths=[
        ROOT/'reference'/'foundation'/'src'/'obds_ref'/'canonical.py',
        ROOT/'reference'/'context-assembly'/'canonical.py',
        ROOT/'reference'/'context-delivery'/'canonical.py',
    ]
    assert len({p.read_bytes() for p in paths})==1


def test_rc5_legacy_hex_fixture_is_not_public_schema_surface():
    index=json.loads((ROOT/'OBDS-1.0.4-SCHEMA-INDEX.json').read_text())
    assert all(x['file']!='colour-hex.schema.json' for x in index.get('valueSchemas',[]))
    helper=json.loads((ROOT/'reference'/'foundation'/'value-schemas'/'colour-hex.schema.json').read_text())
    assert '/reference/1.0.0/' in helper['$id']
