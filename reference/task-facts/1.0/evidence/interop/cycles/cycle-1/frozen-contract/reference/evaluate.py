#!/usr/bin/env python3
"""Non-normative applicability only. Never loads expected-results.json."""
import argparse
import hashlib
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / 'schemas/task-facts.schema.json').read_text())
SAFE_INTEGER = 9007199254740991
DATE = re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}\Z')
INSTANT = re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(Z|[+-][0-9]{2}:[0-9]{2})\Z')


class Invalid(ValueError):
    pass


def canonical_bytes(value):
    """TFJ-0.1: Unicode scalar strings, safe integers, no floating point."""
    def check(x):
        if x is None or type(x) is bool:
            return
        if type(x) is int and abs(x) <= SAFE_INTEGER:
            return
        if type(x) is str and not any(0xD800 <= ord(c) <= 0xDFFF for c in x):
            return
        if type(x) is list:
            for item in x:
                check(item)
            return
        if type(x) is dict and all(type(k) is str for k in x):
            for k, v in x.items():
                check(k)
                check(v)
            return
        raise Invalid('NON_CANONICAL_INPUT')
    check(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def snapshot_hash(value):
    return 'sha256:' + hashlib.sha256(canonical_bytes(value)).hexdigest()


def validate_shape(value, definition):
    schema = {**SCHEMA, '$ref': '#/$defs/' + definition}
    if not Draft202012Validator(schema).is_valid(value):
        raise Invalid('SCHEMA_INVALID')


def temporal(value):
    if type(value) is not str:
        raise Invalid('TYPE_MISMATCH')
    try:
        if DATE.fullmatch(value):
            return 'date', date.fromisoformat(value)
        if INSTANT.fullmatch(value) and not value.endswith('-00:00'):
            if int(value[11:13]) > 23 or int(value[14:16]) > 59 or int(value[17:19]) > 59:
                raise ValueError('time outside profile')
            if value[-1] != 'Z':
                hh, mm = int(value[-5:-3]), int(value[-2:])
                if hh > 14 or mm > 59 or (hh == 14 and mm):
                    raise ValueError('offset outside profile')
            return 'date-time', datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        pass
    raise Invalid('TYPE_MISMATCH')


def string(value):
    return type(value) is str and len(value) > 0


def pair(value):
    return type(value) is list and len(value) == 2 and all(string(v) for v in value)


def check_value(t, value):
    if t in ('date', 'date-time'):
        valid = temporal(value)[0] == t
    elif t == 'string':
        valid = string(value)
    elif t == 'boolean':
        valid = type(value) is bool
    elif t == 'integer':
        valid = type(value) is int and abs(value) <= SAFE_INTEGER
    else:
        valid = (type(value) is list and len(value) > 0
                 and all((string if t == 'string-set' else pair)(v) for v in value))
        if valid:
            valid = len({canonical_bytes(v) for v in value}) == len(value)
    if not valid:
        raise Invalid('TYPE_MISMATCH')


def validate_snapshot(snapshot):
    validate_shape(snapshot, 'snapshot')
    declarations, facts = snapshot['declarations'], snapshot['facts']
    if any(k not in declarations for k in facts):
        raise Invalid('UNDECLARED_FACT')
    for key in sorted(facts):
        fact = facts[key]
        if fact['state'] == 'known':
            check_value(declarations[key]['type'], fact['value'])
    for key in sorted(facts):
        for eid in facts[key]['evidenceRefs']:
            if eid not in snapshot['evidence'] or snapshot['evidence'][eid]['fact'] != key:
                raise Invalid('EVIDENCE_REFERENCE')
    for eid, evidence in snapshot['evidence'].items():
        key = evidence['fact']
        if key not in facts or eid not in facts[key]['evidenceRefs']:
            raise Invalid('EVIDENCE_REFERENCE')


def validate_condition(snapshot, condition):
    validate_shape(condition, 'condition')
    for atom in condition['all']:
        key, op = atom['fact'], atom['op']
        if key not in snapshot['declarations']:
            raise Invalid('UNDECLARED_FACT')
        t = snapshot['declarations'][key]['type']
        if op in ('present', 'absent'):
            continue
        if op == 'contains':
            if t not in ('string-set', 'association-set'):
                raise Invalid('OPERATOR_TYPE')
            if not (string if t == 'string-set' else pair)(atom['value']):
                raise Invalid('TYPE_MISMATCH')
        elif t in ('string-set', 'association-set'):
            raise Invalid('OPERATOR_TYPE')
        elif t in ('date', 'date-time'):
            temporal(atom['value'])  # A valid date/instant mismatch remains UNKNOWN.
        else:
            check_value(t, atom['value'])


def verified(snapshot, key, context):
    task, fact = snapshot['task'], snapshot['facts'][key]
    if context['snapshotHash'] != snapshot_hash(snapshot):
        return False
    for k, source in [('taskId', 'id'), ('artifactHash', 'artifactHash'), ('inputPackageHash', 'inputPackageHash')]:
        if context[k] != task[source]:
            return False
    assertion = {k: v for k, v in fact.items() if k != 'evidenceRefs'}
    for eid in fact['evidenceRefs']:
        e = snapshot['evidence'][eid]
        if (e['status'] != 'verified' or context['acceptedEvidence'].get(eid) != snapshot_hash(e)
                or e['assertionHash'] != snapshot_hash(assertion)
                or e['taskId'] != task['id'] or e['artifactHash'] != task['artifactHash']
                or e['inputPackageHash'] != task['inputPackageHash']):
            return False
    return True


def atom_result(snapshot, atom, context):
    key, op = atom['fact'], atom['op']
    fact = snapshot['facts'].get(key)
    if fact is None:
        return 'UNKNOWN', 'FACT_MISSING'
    if not verified(snapshot, key, context):
        return 'UNKNOWN', 'EVIDENCE_UNVERIFIED'
    state = fact['state']
    if state == 'unknown':
        return 'UNKNOWN', 'FACT_UNKNOWN'
    if state == 'contradictory':
        return 'CONTRADICTORY', 'FACT_CONTRADICTORY'
    t = snapshot['declarations'][key]['type']
    if state == 'known' and t == 'association-set':
        targets = {}
        for left, right in fact['value']:
            if left in targets and targets[left] != right:
                return 'CONTRADICTORY', 'ASSOCIATION_CONFLICT'
            targets[left] = right
    if op in ('present', 'absent'):
        truth = (state == 'known') if op == 'present' else (state == 'empty')
    elif state == 'empty':
        truth = False
    elif op == 'contains':
        truth = atom['value'] in fact['value']
    elif t in ('date', 'date-time'):
        left_kind, left = temporal(fact['value'])
        right_kind, right = temporal(atom['value'])
        if left_kind != right_kind:
            return 'UNKNOWN', 'TIME_BASIS_UNRESOLVED'
        truth = left == right
    else:
        truth = fact['value'] == atom['value']
    return ('APPLIES', 'ALL_TRUE') if truth else ('DOES_NOT_APPLY', 'PREDICATE_FALSE')


def evaluate(snapshot, condition, verification_context):
    """verification_context MUST originate from the verifier, not the task caller."""
    result = {'conditionId': condition.get('id') if type(condition) is dict else None,
              'snapshotHash': None}
    try:
        canonical_bytes([snapshot, condition, verification_context])
        validate_shape(condition, 'routingCondition')
        result['snapshotHash'] = snapshot_hash(snapshot)
        validate_snapshot(snapshot)
        validate_shape(verification_context, 'verificationContext')
        validate_condition(snapshot, condition)
        decisions = [atom_result(snapshot, atom, verification_context) for atom in condition['all']]
        # Conservative conjunction; never short-circuit around unknowns/conflicts.
        priority = {'CONTRADICTORY': 0, 'UNKNOWN': 1, 'DOES_NOT_APPLY': 2, 'APPLIES': 3}
        outcome, reason = min(decisions, key=lambda d: (priority[d[0]], d[1]))
    except Invalid as exc:
        outcome, reason = 'INVALID', str(exc)
    result.update(outcome=outcome, reason=reason)
    return result


def load_json(path):
    def pairs(items):
        obj = {}
        for k, v in items:
            if k in obj:
                raise Invalid('JSON_PARSE_ERROR')
            obj[k] = v
        return obj
    def constant(_):
        raise Invalid('JSON_PARSE_ERROR')
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs,
                          parse_constant=constant)
    except (ValueError, UnicodeError) as exc:
        if isinstance(exc, Invalid):
            raise
        raise Invalid('JSON_PARSE_ERROR') from exc


def evaluate_family(document):
    """Atomic family routing gate; typed failures are isolated per decision."""
    canonical_bytes(document)
    validate_shape(document, 'routingFamily')
    if len({c['id'] for c in document['cases']}) != len(document['cases']):
        raise Invalid('DUPLICATE_ID')
    for case in document['cases']:
        if len({c['id'] for c in case['conditions']}) != len(case['conditions']):
            raise Invalid('DUPLICATE_ID')
    results = []
    for case in document['cases']:
        for condition in case['conditions']:
            binding = {'family': document['family'], 'caseId': case['id'],
                       'conditionId': condition['id'],
                       'snapshotHash': snapshot_hash(case['snapshot'])}
            try:
                validate_shape(document, 'family')
                validate_shape(case, 'case')
                decision = evaluate(case['snapshot'], condition, case.get('verificationContext'))
            except Invalid as exc:
                decision = {'outcome': 'INVALID', 'reason': str(exc)}
            results.append({**binding, **decision})
    return results


def unbound(reason):
    return {'family': None, 'caseId': None, 'conditionId': None,
            'snapshotHash': None, 'outcome': 'INVALID', 'reason': reason}


def evaluate_path(path):
    """One transport document yields bound decisions or one unbound record."""
    try:
        return evaluate_family(load_json(path))
    except (Invalid, OSError) as exc:
        return [unbound(str(exc) if isinstance(exc, Invalid) else 'INPUT_IO_ERROR')]


def main():
    parser = argparse.ArgumentParser(description='Evaluate synthetic experiment fixtures; no brand approval.')
    parser.add_argument('fixtures', nargs='+', type=Path)
    args = parser.parse_args()
    results = []
    for path in args.fixtures:
        results.extend(evaluate_path(path))
    print(json.dumps({'results': results}, indent=2, ensure_ascii=False))
    return 2 if any(r['outcome'] == 'INVALID' for r in results) else 0


if __name__ == '__main__':
    sys.exit(main())
