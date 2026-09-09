"""Independent implementation of the frozen Task Facts 0.2 contract."""
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

class Invalid(Exception):
    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)

SCHEMA = json.loads(Path(__file__).with_name('task-facts.schema.json').read_text())

def tfj(value):
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if abs(value) <= 9007199254740991:
            return
    elif type(value) is str:
        if not any(0xD800 <= ord(c) <= 0xDFFF for c in value):
            return
    elif type(value) is list:
        for item in value:
            tfj(item)
        return
    elif type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise Invalid('NON_CANONICAL_INPUT')
            tfj(key)
            tfj(item)
        return
    raise Invalid('NON_CANONICAL_INPUT')

def canonical_bytes(value):
    tfj(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')

def digest(value):
    return 'sha256:' + hashlib.sha256(canonical_bytes(value)).hexdigest()

snapshot_hash = digest

def strict_load(raw):
    def pairs(items):
        out = {}
        for k, v in items:
            if k in out:
                raise ValueError('duplicate decoded key')
            out[k] = v
        return out
    def constant(value):
        raise ValueError('non-JSON constant')
    try:
        text = raw.decode('utf-8') if isinstance(raw, bytes) else raw
        # Oversized tokens remain JSON integers; classify them only after parsing.
        def integer(token):
            return int(token) if len(token.lstrip('-')) <= 16 else 9007199254740992
        result = json.loads(text, object_pairs_hook=pairs, parse_constant=constant, parse_int=integer)
    except (ValueError, UnicodeError):
        raise Invalid('JSON_PARSE_ERROR') from None
    tfj(result)
    return result

def schema_valid(value, schema):
    if '$ref' in schema:
        return schema_valid(value, SCHEMA['$defs'][schema['$ref'].split('/')[-1]])
    if 'oneOf' in schema:
        return sum(schema_valid(value, s) for s in schema['oneOf']) == 1
    if 'const' in schema and canonical_bytes(value) != canonical_bytes(schema['const']):
        return False
    if 'enum' in schema and not any(canonical_bytes(value) == canonical_bytes(v) for v in schema['enum']):
        return False
    typ = schema.get('type')
    types = {'object': dict, 'array': list, 'string': str, 'integer': int, 'boolean': bool}
    if typ and type(value) is not types[typ]:
        return False
    if type(value) is str:
        if len(value) < schema.get('minLength', 0):
            return False
        if 'pattern' in schema and not re.search(schema['pattern'], value):
            return False
    if type(value) is list:
        if len(value) < schema.get('minItems', 0):
            return False
        if schema.get('uniqueItems') and len({canonical_bytes(v) for v in value}) != len(value):
            return False
        if not all(schema_valid(v, schema.get('items', {})) for v in value):
            return False
    if type(value) is dict:
        if not set(schema.get('required', [])).issubset(value):
            return False
        props = schema.get('properties', {})
        for k, v in value.items():
            if not schema_valid(k, schema.get('propertyNames', {})):
                return False
            rule = props.get(k, schema.get('additionalProperties', True))
            if rule is False or (isinstance(rule, dict) and not schema_valid(v, rule)):
                return False
    return True

def validate(value, name):
    if not schema_valid(value, SCHEMA['$defs'][name]):
        raise Invalid('SCHEMA_INVALID')

def temporal(value, typ):
    if type(value) is not str:
        return None
    try:
        if typ == 'date' and re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value):
            return dt.date.fromisoformat(value)
        if typ == 'date-time' and re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(Z|[+-][0-9]{2}:[0-9]{2})', value):
            zone = value[19:]
            if zone != 'Z':
                hh, mm = int(zone[1:3]), int(zone[4:])
                if zone == '-00:00' or hh > 14 or mm > 59 or (hh == 14 and mm != 0):
                    return None
            return dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        pass
    return None

def valid_value(value, typ):
    if typ == 'string':
        return type(value) is str and len(value) > 0
    if typ == 'boolean':
        return type(value) is bool
    if typ == 'integer':
        return type(value) is int and abs(value) <= 9007199254740991
    if typ in ('date', 'date-time'):
        return temporal(value, typ) is not None
    if typ in ('string-set', 'association-set'):
        if type(value) is not list or not value:
            return False
        if typ == 'string-set':
            good = all(valid_value(v, 'string') for v in value)
        else:
            good = all(type(v) is list and len(v) == 2 and all(valid_value(x, 'string') for x in v) for v in value)
        return good and len({canonical_bytes(v) for v in value}) == len(value)
    return False

def validate_payload(snapshot, condition, context):
    validate(snapshot, 'snapshot')
    declarations, facts, evidence = (snapshot[k] for k in ('declarations', 'facts', 'evidence'))
    if set(facts) - set(declarations):
        raise Invalid('UNDECLARED_FACT')
    for key in sorted(facts):
        fact = facts[key]
        if fact['state'] == 'known' and not valid_value(fact['value'], declarations[key]['type']):
            raise Invalid('TYPE_MISMATCH')
    used = set()
    for key, fact in facts.items():
        for ref in fact['evidenceRefs']:
            if ref not in evidence or evidence[ref]['fact'] != key:
                raise Invalid('EVIDENCE_REFERENCE')
            used.add(ref)
    if used != set(evidence):
        raise Invalid('EVIDENCE_REFERENCE')
    validate(context, 'verificationContext')
    validate(condition, 'condition')
    for atom in condition['all']:
        if atom['fact'] not in declarations:
            raise Invalid('UNDECLARED_FACT')
        typ = declarations[atom['fact']]['type']
        op = atom['op']
        if op in ('present', 'absent'):
            continue
        value = atom['value']
        if op == 'contains':
            if typ not in ('string-set', 'association-set'):
                raise Invalid('OPERATOR_TYPE')
            if not valid_value([value], typ):
                raise Invalid('TYPE_MISMATCH')
        else:
            if typ in ('string-set', 'association-set'):
                raise Invalid('OPERATOR_TYPE')
            if typ in ('date', 'date-time'):
                good = valid_value(value, 'date') or valid_value(value, 'date-time')
            else:
                good = valid_value(value, typ)
            if not good:
                raise Invalid('TYPE_MISMATCH')

def atom_result(snapshot, atom, context, hash_value):
    key = atom['fact']
    fact = snapshot['facts'].get(key)
    if fact is None:
        return 'UNKNOWN', 'FACT_MISSING'
    task = snapshot['task']
    identity = {'taskId': task['id'], 'artifactHash': task['artifactHash'], 'inputPackageHash': task['inputPackageHash']}
    verified = context['snapshotHash'] == hash_value and all(context[k] == v for k, v in identity.items())
    assertion_hash = digest({k: v for k, v in fact.items() if k != 'evidenceRefs'})
    for ref in fact['evidenceRefs']:
        ev = snapshot['evidence'][ref]
        verified = verified and ev['status'] == 'verified' and context['acceptedEvidence'].get(ref) == digest(ev) and ev['assertionHash'] == assertion_hash and all(ev[k] == v for k, v in identity.items())
    if not verified:
        return 'UNKNOWN', 'EVIDENCE_UNVERIFIED'
    state = fact['state']
    if state == 'unknown':
        return 'UNKNOWN', 'FACT_UNKNOWN'
    if state == 'contradictory':
        return 'CONTRADICTORY', 'FACT_CONTRADICTORY'
    typ = snapshot['declarations'][key]['type']
    if state == 'known' and typ == 'association-set':
        sources = {}
        for source, target in fact['value']:
            if source in sources and sources[source] != target:
                return 'CONTRADICTORY', 'ASSOCIATION_CONFLICT'
            sources[source] = target
    op = atom['op']
    if op == 'present':
        truth = state == 'known'
    elif op == 'absent':
        truth = state == 'empty'
    elif state == 'empty':
        truth = False
    elif op == 'contains':
        truth = atom['value'] in fact['value']
    elif typ in ('date', 'date-time'):
        other_typ = 'date' if temporal(atom['value'], 'date') is not None else 'date-time'
        if other_typ != typ:
            return 'UNKNOWN', 'TIME_BASIS_UNRESOLVED'
        truth = temporal(fact['value'], typ) == temporal(atom['value'], typ)
    else:
        truth = fact['value'] == atom['value']
    return ('APPLIES', 'ALL_TRUE') if truth else ('DOES_NOT_APPLY', 'PREDICATE_FALSE')

def evaluate(snapshot, condition, verification_context):
    record = {'conditionId': None, 'snapshotHash': None, 'outcome': 'INVALID', 'reason': None}
    try:
        tfj([snapshot, condition, verification_context])
        validate(condition, 'routingCondition')
        record.update(conditionId=condition['id'], snapshotHash=digest(snapshot))
        validate_payload(snapshot, condition, verification_context)
        results = [atom_result(snapshot, atom, verification_context, record['snapshotHash']) for atom in condition['all']]
        ranks = {'APPLIES': 0, 'DOES_NOT_APPLY': 1, 'UNKNOWN': 2, 'CONTRADICTORY': 3}
        outcome = max((r[0] for r in results), key=ranks.get)
        reason = min(r[1] for r in results if r[0] == outcome)
        record.update(outcome=outcome, reason=reason)
    except Invalid as error:
        record['reason'] = error.reason
    return record

def unbound(reason):
    return dict(family=None, caseId=None, conditionId=None, snapshotHash=None, outcome='INVALID', reason=reason)

def evaluate_family(family):
    tfj(family)
    validate(family, 'routingFamily')
    cases = family['cases']
    if len({c['id'] for c in cases}) != len(cases):
        raise Invalid('DUPLICATE_ID')
    for case in cases:
        if len({c['id'] for c in case['conditions']}) != len(case['conditions']):
            raise Invalid('DUPLICATE_ID')
    results = []
    for case in cases:
        hash_value = digest(case['snapshot'])
        for condition in case['conditions']:
            record = dict(family=family['family'], caseId=case['id'], conditionId=condition['id'], snapshotHash=hash_value, outcome='INVALID', reason=None)
            try:
                validate(family, 'family')
                validate(case, 'case')
                record.update(evaluate(case['snapshot'], condition, case['verificationContext']))
            except Invalid as error:
                record['reason'] = error.reason
            results.append(record)
    return results

def evaluate_path(path):
    try:
        try:
            raw = Path(path).read_bytes()
        except OSError:
            raise Invalid('INPUT_IO_ERROR') from None
        return evaluate_family(strict_load(raw))
    except Invalid as error:
        return [unbound(error.reason)]

def main(argv=None):
    paths = sys.argv[1:] if argv is None else argv
    results = [r for path in paths for r in evaluate_path(path)]
    print(json.dumps({'results': results}, ensure_ascii=False, indent=2))
    return 2 if any(r['outcome'] == 'INVALID' for r in results) else 0

if __name__ == '__main__':
    sys.exit(main())
