#!/usr/bin/env python3
"""Strict raw-output protocol and positional Task Facts comparison (stdlib)."""
import argparse
import hashlib
import json
from pathlib import Path

FIELDS = ('family', 'caseId', 'conditionId', 'snapshotHash', 'outcome', 'reason')
OUTCOMES = {'APPLIES', 'DOES_NOT_APPLY', 'UNKNOWN', 'CONTRADICTORY', 'INVALID'}

class IdentityError(ValueError):
    pass

class ProtocolError(ValueError):
    pass

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def strict_json(raw):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ProtocolError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    def reject(value):
        raise ProtocolError('Nonstandard JSON number: ' + value)
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=reject)
        json.dumps(value, ensure_ascii=False).encode('utf-8')
        return value
    except (ValueError, UnicodeError) as exc:
        raise ProtocolError(str(exc)) from exc

def local(root, relative):
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts or '\\' in relative:
        raise IdentityError('Unsafe suite path: ' + relative)
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise IdentityError('Suite path escapes root: ' + relative)
    return resolved

def load_suite(path):
    path = Path(path).resolve()
    root = path.parent
    suite = strict_json(path.read_bytes())
    if suite['suiteId'] != 'task-facts-1.0' or suite['revision'] != 1:
        raise IdentityError('Unsupported suite identity')
    if [(g['name'], g['expectedCount']) for g in suite['groups']] != [('fixtures', 66), ('regressions', 36)]:
        raise IdentityError('Unexpected suite groups/counts')
    inventory = set(suite['identityFiles']) | {path.name}
    entries = [suite['contract'], suite['schema']]
    for group in suite['groups']:
        paths = [i['path'] for i in group['inputs']]
        if len(paths) != len(set(paths)) or paths != sorted(paths):
            raise IdentityError('Input order/uniqueness mismatch')
        entries += group['inputs'] + [group['expectations']]
    for entry in entries:
        p = local(root, entry['path'])
        if digest(p) != entry['sha256']:
            raise IdentityError('Raw file digest mismatch: ' + entry['path'])
        inventory.add(entry['path'])
    encoded = b''.join((rel + '\0' + digest(local(root, rel)) + '\n').encode('utf-8') for rel in sorted(inventory))
    suite_hash = hashlib.sha256(encoded).hexdigest()
    return suite, root, suite_hash

def records(raw):
    envelope = strict_json(raw)
    if not isinstance(envelope, dict) or set(envelope) != {'results'} or not isinstance(envelope['results'], list):
        raise ProtocolError('Envelope must contain only results array')
    for i, record in enumerate(envelope['results']):
        if not isinstance(record, dict) or set(record) != set(FIELDS):
            raise ProtocolError(f'Record {i}: expected exactly six fields')
        for field in FIELDS[:4]:
            if record[field] is not None and not isinstance(record[field], str):
                raise ProtocolError(f'Record {i}: invalid {field} type')
        if not isinstance(record['outcome'], str) or record['outcome'] not in OUTCOMES:
            raise ProtocolError(f'Record {i}: invalid outcome')
        if not isinstance(record['reason'], str) or not record['reason']:
            raise ProtocolError(f'Record {i}: invalid reason')
    return envelope['results']

def expected(root, group):
    path = local(root, group['expectations']['path'])
    obj = strict_json(path.read_bytes())
    if group['name'] == 'fixtures':
        wanted = [{k: v for k, v in row.items() if k != 'basis'} for row in obj['results']]
    else:
        mapping = {}
        for vector in obj['vectors']:
            key = (path.parent / vector['input']).resolve()
            if key in mapping:
                raise IdentityError('Duplicate regression expectation mapping')
            mapping[key] = vector['expected']
        inputs = [local(root, i['path']) for i in group['inputs']]
        if set(mapping) != set(inputs):
            raise IdentityError('Missing/extra regression expectation mapping')
        wanted = [record for p in inputs for record in mapping[p]]
    records(json.dumps({'results': wanted}).encode())
    if len(wanted) != group['expectedCount']:
        raise IdentityError('Expected record count mismatch')
    return wanted

def compare(raw, code, wanted):
    actual = records(raw)
    mismatch = []
    required_exit = 2 if any(r['outcome'] == 'INVALID' for r in actual) else 0
    if code != required_exit:
        mismatch.append({'kind': 'exit', 'expected': required_exit, 'actual': code})
    if len(actual) != len(wanted):
        mismatch.append({'kind': 'count', 'expected': len(wanted), 'actual': len(actual)})
    for i, (a, e) in enumerate(zip(actual, wanted)):
        for field in FIELDS:
            if type(a[field]) is not type(e[field]) or a[field] != e[field]:
                mismatch.append({'kind': 'record', 'index': i, 'field': field, 'expected': e[field], 'actual': a[field]})
    return actual, mismatch

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', required=True)
    parser.add_argument('--group', choices=['fixtures', 'regressions'], required=True)
    parser.add_argument('--stdout', required=True)
    parser.add_argument('--exit-code', type=int, required=True)
    parser.add_argument('--result', required=True)
    args = parser.parse_args()
    result = {'passed': False, 'exitCode': 2, 'mode': 'retained-output-comparison'}
    try:
        suite, root, suite_hash = load_suite(args.suite)
        group = next(g for g in suite['groups'] if g['name'] == args.group)
        actual, mismatch = compare(Path(args.stdout).read_bytes(), args.exit_code, expected(root, group))
        result.update(suiteId=suite['suiteId'], suiteHash=suite_hash, actual=actual, mismatches=mismatch, passed=not mismatch, exitCode=1 if mismatch else 0)
    except ProtocolError as exc:
        result.update(error=str(exc), exitCode=1)
    except (IdentityError, OSError, ValueError, KeyError, TypeError) as exc:
        result.update(error=str(exc))
    Path(args.result).write_text(json.dumps(result, indent=2) + '\n')
    return result['exitCode']

if __name__ == '__main__':
    raise SystemExit(main())
