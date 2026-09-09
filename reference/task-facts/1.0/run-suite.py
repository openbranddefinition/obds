#!/usr/bin/env python3
"""Run a language-neutral Task Facts evaluator without transforming input bytes."""
import argparse
import base64
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

_spec = importlib.util.spec_from_file_location('task_facts_compare', Path(__file__).with_name('compare.py'))
protocol = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(protocol)

def transport(raw):
    return {'base64': base64.b64encode(raw).decode('ascii'), 'text': raw.decode('utf-8', errors='replace')}

def subject(argv, name, version):
    executable = shutil.which(argv[0])
    if executable is None:
        raise OSError('Executable not found: ' + argv[0])
    files = [{'argument': 0, 'path': executable, 'sha256': protocol.digest(executable)}]
    for i, arg in enumerate(argv[1:], 1):
        if Path(arg).is_file():
            files.append({'argument': i, 'path': str(Path(arg).resolve()), 'sha256': protocol.digest(arg)})
    runtime = subprocess.run([executable, '--version'], capture_output=True, timeout=10)
    return {'name': name or Path(argv[-1]).name, 'version': version or 'raw-sha256:' + files[-1]['sha256'], 'argv': argv, 'executables': files, 'runtimeVersion': transport(runtime.stdout + runtime.stderr), 'harnessPython': platform.python_version()}

def run(args):
    result = {'kind': 'task-facts-conformance-result', 'passed': False, 'exitCode': 2, 'suiteId': None, 'suiteHash': None, 'implementation': {}, 'groups': [], 'failed': 0, 'skipped': 0, 'limitations': ['Tested-set evaluator interoperability only; no Foundation, Compiled Runtime, production integration or certification claim.', 'Trusted host boundary, artifact/package rebinding and retention integration require separate review.']}
    try:
        suite, root, suite_hash = protocol.load_suite(args.suite)
        result.update(suiteId=suite['suiteId'], suiteRevision=suite['revision'], suiteHash=suite_hash, contract=suite['contract'], schema=suite['schema'], payloadVersion='0.1', canonicalization='TFJ-0.1')
        argv = args.command[1:] if args.command[:1] == ['--'] else args.command
        if not argv:
            raise ValueError('Missing evaluator command after --')
        result['implementation'] = subject(argv, args.implementation_name, args.implementation_version)
        for group in suite['groups']:
            wanted = protocol.expected(root, group)
            paths = [protocol.local(root, e['path']) for e in group['inputs']]
            before = [protocol.digest(p) for p in paths]
            record = {'name': group['name'], 'expectedCount': len(wanted), 'actual': [], 'mismatches': [], 'passed': False, 'argv': argv + [str(p) for p in paths]}
            result['groups'].append(record)
            try:
                child = subprocess.run(record['argv'], capture_output=True, timeout=args.timeout, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
                record.update(stdout=transport(child.stdout), stderr=transport(child.stderr), processExit=child.returncode)
                actual, mismatches = protocol.compare(child.stdout, child.returncode, wanted)
                record.update(actual=actual, mismatches=mismatches, passed=not mismatches)
            except protocol.ProtocolError as exc:
                record['mismatches'].append({'kind': 'protocol', 'message': str(exc)})
            except subprocess.TimeoutExpired as exc:
                record.update(stdout=transport(exc.stdout or b''), stderr=transport(exc.stderr or b''), processExit=None, error='timeout')
                raise OSError('Evaluator timed out') from exc
            finally:
                if before != [protocol.digest(p) for p in paths]:
                    raise protocol.IdentityError('Evaluator changed raw input bytes')
            if not record['passed']:
                result['failed'] += max(1, len(record['mismatches']))
        if protocol.load_suite(args.suite)[2] != suite_hash:
            raise protocol.IdentityError('Suite identity changed during execution')
        for file in result['implementation']['executables']:
            if protocol.digest(file['path']) != file['sha256']:
                raise protocol.IdentityError('Subject changed during execution')
        result['passed'] = result['failed'] == 0
        result['exitCode'] = 0 if result['passed'] else 1
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        result.update(error=str(exc), passed=False, exitCode=2)
        result['failed'] = max(1, result['failed'])
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', default=str(Path(__file__).with_name('SUITE.json')))
    parser.add_argument('--result', required=True)
    parser.add_argument('--implementation-name')
    parser.add_argument('--implementation-version')
    parser.add_argument('--timeout', type=float, default=30)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    result = run(args)
    try:
        Path(args.result).write_text(json.dumps(result, indent=2, ensure_ascii=True) + '\n')
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps({'passed': result['passed'], 'exitCode': result['exitCode'], 'suiteHash': result['suiteHash'], 'counts': {g['name']: len(g['actual']) for g in result['groups']}}))
    return result['exitCode']

if __name__ == '__main__':
    raise SystemExit(main())
