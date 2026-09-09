import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('experiment', ROOT / 'reference/evaluate.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)
FAMILIES = [json.loads(p.read_text()) for p in sorted((ROOT / 'fixtures').glob('*.json'))]
CASES = {c['id']: c for family in FAMILIES for c in family['cases']}


def copied(id):
    return copy.deepcopy(CASES[id])


def run(case, condition=0):
    return e.evaluate(case['snapshot'], case['conditions'][condition], case['verificationContext'])


def attest(case, key):
    """Simulate a new verifier acceptance for tests that change valid facts."""
    s = case['snapshot']
    f = s['facts'][key]
    for eid in f['evidenceRefs']:
        record = s['evidence'][eid]
        record['assertionHash'] = e.snapshot_hash({k: v for k, v in f.items() if k != 'evidenceRefs'})
        case['verificationContext']['acceptedEvidence'][eid] = e.snapshot_hash(record)
    case['verificationContext']['snapshotHash'] = e.snapshot_hash(s)


class ExperimentTests(unittest.TestCase):
    def assertDecision(self, case, outcome, reason=None, condition=0):
        result = run(case, condition)
        self.assertEqual(result['outcome'], outcome, result)
        if reason:
            self.assertEqual(result['reason'], reason, result)
        return result

    def test_frozen_vectors(self):
        expected = json.loads((ROOT / 'expected-results.json').read_text())['results']
        actual = [r for family in FAMILIES for r in e.evaluate_family(family)]
        self.assertEqual(len(FAMILIES), 6)
        self.assertEqual(len(CASES), 28)
        self.assertEqual(len(actual), 66)
        self.assertEqual(actual, [{k: v for k, v in r.items() if k != 'basis'} for r in expected])
        self.assertEqual({r['outcome'] for r in actual}, {'APPLIES', 'DOES_NOT_APPLY', 'UNKNOWN', 'CONTRADICTORY', 'INVALID'})
        self.assertTrue(all(r['basis'] for r in expected))

    def test_schema_is_valid_and_closed(self):
        e.Draft202012Validator.check_schema(e.SCHEMA)
        c = copied('claims-both')
        c['snapshot']['unrecognized'] = 'x'
        self.assertDecision(c, 'INVALID', 'SCHEMA_INVALID')

    def test_ordinary_type_mutations_never_mean_false(self):
        for bad in ['C06', True, 2, None, {}, [], ['C06', 1], ['C06', 'C06']]:
            with self.subTest(value=bad):
                c = copied('claims-both')
                c['snapshot']['facts']['claimsUsed']['value'] = bad
                result = self.assertDecision(c, 'INVALID', 'TYPE_MISMATCH')
                self.assertIsNotNone(result['snapshotHash'])

    def test_boolean_and_integer_do_not_coerce(self):
        c = copied('partner-portrait')
        c['snapshot']['facts']['portraitPresent']['value'] = 1
        self.assertDecision(c, 'INVALID', 'TYPE_MISMATCH', condition=1)
        for value, outcome in [(0, 'APPLIES'), (1, 'DOES_NOT_APPLY'), (True, 'INVALID')]:
            c = copied('partner-portrait')
            c['snapshot']['declarations']['portraitPresent']['type'] = 'integer'
            c['snapshot']['facts']['portraitPresent']['value'] = value
            c['conditions'][1]['all'][0]['value'] = 0
            attest(c, 'portraitPresent')
            self.assertDecision(c, outcome, condition=1)

    def test_false_and_zero_are_present(self):
        for value, typ in [(False, 'boolean'), (0, 'integer')]:
            c = copied('partner-mark-only')
            c['snapshot']['declarations']['portraitPresent']['type'] = typ
            c['snapshot']['facts']['portraitPresent']['value'] = value
            c['conditions'][1]['all'] = [{'fact': 'portraitPresent', 'op': 'present'}]
            attest(c, 'portraitPresent')
            self.assertDecision(c, 'APPLIES', condition=1)

    def test_set_permutation_semantics_and_identity(self):
        c = copied('claims-both')
        original_hash = run(c)['snapshotHash']
        c['snapshot']['facts']['claimsUsed']['value'].reverse()
        attest(c, 'claimsUsed')
        self.assertDecision(c, 'APPLIES')
        self.assertNotEqual(original_hash, run(c)['snapshotHash'])

    def test_malformed_unused_fact_invalidates_snapshot(self):
        c = copied('claims-both')
        c['snapshot']['facts']['claimProducts']['value'] = 3
        self.assertDecision(c, 'INVALID', 'TYPE_MISMATCH', condition=1)

    def test_unused_conflict_does_not_poison_independent_rule(self):
        self.assertDecision(copied('claims-conflicting-product'), 'APPLIES', condition=1)
        self.assertDecision(copied('campaign-conflict'), 'APPLIES', condition=1)

    def test_false_does_not_hide_unknown_or_conflict(self):
        for source, outcome in [('fact-unknown', 'UNKNOWN'), ('fact-contradictory', 'CONTRADICTORY')]:
            c = copied(source)
            # The two presence predicates cannot both be true, but unresolved facts stay unresolved.
            c['conditions'][0]['all'].append({'fact': 'claimsUsed', 'op': 'absent'})
            # Add an independently verified false atom using a genuine empty record.
            s = c['snapshot']
            s['declarations']['emptyFact'] = {'type': 'string-set'}
            s['facts']['emptyFact'] = {'state': 'empty', 'evidenceRefs': ['emptyFact:0']}
            ev = copy.deepcopy(next(iter(s['evidence'].values())))
            ev.update(fact='emptyFact', assertionHash=e.snapshot_hash({'state': 'empty'}))
            s['evidence']['emptyFact:0'] = ev
            c['verificationContext']['acceptedEvidence']['emptyFact:0'] = e.snapshot_hash(ev)
            c['verificationContext']['snapshotHash'] = e.snapshot_hash(s)
            c['conditions'][0]['all'].append({'fact': 'emptyFact', 'op': 'present'})
            self.assertDecision(c, outcome)
            c['conditions'][0]['all'].reverse()
            self.assertDecision(c, outcome)

    def test_reason_selection_is_order_independent(self):
        c = copied('fact-unknown')
        c['snapshot']['declarations']['other'] = {'type': 'boolean'}
        c['verificationContext']['snapshotHash'] = e.snapshot_hash(c['snapshot'])
        c['conditions'][0]['all'].append({'fact': 'other', 'op': 'present'})
        self.assertDecision(c, 'UNKNOWN', 'FACT_MISSING')
        c['conditions'][0]['all'].reverse()
        self.assertDecision(c, 'UNKNOWN', 'FACT_MISSING')

    def test_untrusted_verified_label_and_empty_cannot_clear(self):
        for name in ['claims-both', 'fact-empty', 'fact-contradictory']:
            c = copied(name)
            c['verificationContext']['acceptedEvidence'] = {}
            self.assertDecision(c, 'UNKNOWN', 'EVIDENCE_UNVERIFIED')

    def test_fact_and_evidence_tampering(self):
        c = copied('claims-both')
        c['snapshot']['facts']['claimsUsed']['value'] = ['C99']
        self.assertDecision(c, 'UNKNOWN', 'EVIDENCE_UNVERIFIED')
        c = copied('claims-both')
        c['snapshot']['evidence']['claimsUsed:0']['supplier'] = 'forged'
        self.assertDecision(c, 'UNKNOWN', 'EVIDENCE_UNVERIFIED')

    def test_replay_to_other_identity_is_unverified(self):
        for key in ['id', 'artifactHash', 'inputPackageHash']:
            c = copied('claims-both')
            c['snapshot']['task'][key] = 'task:other' if key == 'id' else 'sha256:' + 'f' * 64
            self.assertDecision(c, 'UNKNOWN', 'EVIDENCE_UNVERIFIED')
        c = copied('claims-both')
        c['verificationContext']['taskId'] = 'task:other'
        self.assertDecision(c, 'UNKNOWN', 'EVIDENCE_UNVERIFIED')

    def test_complete_snapshot_verifier_binding(self):
        for mutation in [lambda s: s['task'].update(action='publish'),
                         lambda s: s['declarations'].update(newFact={'type': 'boolean'}),
                         lambda s: s['declarations']['campaignId'].update(type='date')]:
            c = copied('campaign-claim')
            mutation(c['snapshot'])
            # Malformed reinterpretations fail validation; all other changes invalidate trust.
            self.assertIn(run(c)['outcome'], ['UNKNOWN', 'INVALID'])

    def test_all_conflict_evidence_must_be_accepted(self):
        c = copied('fact-contradictory')
        del c['verificationContext']['acceptedEvidence']['claimsUsed:1']
        self.assertDecision(c, 'UNKNOWN', 'EVIDENCE_UNVERIFIED')

    def test_dangling_cross_fact_and_orphan_evidence(self):
        for kind in ['dangling', 'cross-fact', 'orphan']:
            c = copied('claims-both')
            if kind == 'dangling':
                del c['snapshot']['evidence']['claimsUsed:0']
            elif kind == 'cross-fact':
                c['snapshot']['facts']['claimsUsed']['evidenceRefs'] = ['claimProducts:0']
            else:
                c['snapshot']['evidence']['orphan'] = copy.deepcopy(c['snapshot']['evidence']['claimsUsed:0'])
            self.assertDecision(c, 'INVALID', 'EVIDENCE_REFERENCE')

    def test_undeclared_fact_is_invalid_not_missing(self):
        c = copied('fact-missing')
        c['snapshot']['declarations'] = {}
        self.assertDecision(c, 'INVALID', 'UNDECLARED_FACT')

    def test_operand_and_operator_errors(self):
        for atom, reason in [({'fact': 'claimsUsed', 'op': 'equals', 'value': ['C06']}, 'OPERATOR_TYPE'),
                             ({'fact': 'claimsUsed', 'op': 'contains', 'value': True}, 'TYPE_MISMATCH'),
                             ({'fact': 'claimsUsed', 'op': 'regex', 'value': '.*'}, 'SCHEMA_INVALID'),
                             ({'fact': 'claimsUsed', 'op': 'present', 'value': True}, 'SCHEMA_INVALID')]:
            c = copied('claims-both')
            c['conditions'][0]['all'] = [atom]
            self.assertDecision(c, 'INVALID', reason)

    def test_empty_condition_and_duplicate_atom_invalid(self):
        for atoms in [[], [{'fact': 'claimsUsed', 'op': 'present'}] * 2]:
            c = copied('claims-both')
            c['conditions'][0]['all'] = atoms
            self.assertDecision(c, 'INVALID', 'SCHEMA_INVALID')

    def test_time_syntax_calendar_and_unknown_offset(self):
        for bad in ['2026-02-30T12:00:00Z', '2026-09-30T24:00:00Z', '2026-09-30T12:00:60Z',
                    '2026-09-30T12:00:00-00:00', '2026-09-30T12:00:00+14:01',
                    '2026-09-30T12:00:00+00:60', '2026-09-30T12:00:00.1Z', '2026-09-30T12:00:00']:
            c = copied('time-explicit-instant')
            c['snapshot']['facts']['publicationTime']['value'] = bad
            self.assertDecision(c, 'INVALID', 'TYPE_MISMATCH')

    def test_time_domains_are_symmetric(self):
        c = copied('time-explicit-instant')
        c['conditions'][0]['all'][0]['value'] = '2026-09-30'
        self.assertDecision(c, 'UNKNOWN', 'TIME_BASIS_UNRESOLVED')
        self.assertDecision(copied('time-date-vs-instant'), 'UNKNOWN', 'TIME_BASIS_UNRESOLVED')

    def test_date_validity(self):
        c = copied('time-same-civil-date')
        c['snapshot']['facts']['publicationTime']['value'] = '2026-02-29'
        self.assertDecision(c, 'INVALID', 'TYPE_MISMATCH')
        c['snapshot']['facts']['publicationTime']['value'] = '2024-02-29'
        c['conditions'][0]['all'][0]['value'] = '2024-02-29'
        attest(c, 'publicationTime')
        self.assertDecision(c, 'APPLIES')

    def test_canonical_known_bytes(self):
        value = {'z': [False, None, 0, '\b\t\n\f\r\x00\\"/'], 'é': 'e\u0301', 'a': -7}
        expected = '{"a":-7,"z":[false,null,0,"\\b\\t\\n\\f\\r\\u0000\\\\\\"/"],"é":"é"}'.encode('utf-8')
        self.assertEqual(e.canonical_bytes(value), expected)
        self.assertEqual(e.snapshot_hash(value), 'sha256:' + hashlib.sha256(expected).hexdigest())
        self.assertNotEqual(e.snapshot_hash('é'), e.snapshot_hash('e\u0301'))

    def test_object_key_order_does_not_change_hash(self):
        c = copied('claims-both')
        s = c['snapshot']
        reordered = {k: s[k] for k in reversed(list(s))}
        self.assertEqual(e.snapshot_hash(s), e.snapshot_hash(reordered))

    def test_every_snapshot_component_affects_hash(self):
        original = CASES['claims-both']['snapshot']
        for field, change in [('task', lambda s: s['task'].update(action='another-action')),
                              ('declarations', lambda s: s['declarations'].update(extra={'type': 'string'})),
                              ('facts', lambda s: s['facts']['claimsUsed'].update(value=['C99'])),
                              ('evidence', lambda s: s['evidence']['claimsUsed:0'].update(method='other'))]:
            with self.subTest(field=field):
                s = copy.deepcopy(original)
                change(s)
                self.assertNotEqual(e.snapshot_hash(original), e.snapshot_hash(s))

    def test_noncanonical_inputs_reject(self):
        for value in [1.0, float('nan'), 9007199254740992, '\ud800', {1: 'x'}]:
            with self.assertRaises(e.Invalid):
                e.canonical_bytes(value)
        c = copied('claims-both')
        c['snapshot']['facts']['claimsUsed']['value'] = 1.0
        result = self.assertDecision(c, 'INVALID', 'NON_CANONICAL_INPUT')
        self.assertIsNone(result['snapshotHash'])

    def test_json_parser_duplicates_nonfinite_and_syntax(self):
        for content in ['{"a":1,"a":2}', '{"a":NaN}', '{']:
            with tempfile.TemporaryDirectory() as td:
                p = Path(td) / 'bad.json'
                p.write_text(content)
                with self.assertRaises(e.Invalid):
                    e.load_json(p)

    def test_duplicate_routing_ids_rejected(self):
        for which in ['case', 'condition']:
            family = copy.deepcopy(FAMILIES[0])
            if which == 'case':
                family['cases'].append(copy.deepcopy(family['cases'][0]))
            else:
                family['cases'][0]['conditions'].append(copy.deepcopy(family['cases'][0]['conditions'][0]))
            with self.assertRaisesRegex(e.Invalid, 'DUPLICATE_ID'):
                e.evaluate_family(family)

    def test_manifest_inventory_and_raw_hashes(self):
        manifest = json.loads((ROOT / 'PACKAGE-MANIFEST.json').read_text())
        paths = {str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        self.assertEqual(paths, set(manifest['files']) | {'PACKAGE-MANIFEST.json'})
        for relative, digest in manifest['files'].items():
            self.assertEqual('sha256:' + hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), digest, relative)
        self.assertFalse((ROOT / 'schemas/conditional-applicability.schema.json').exists())

    def test_relocated_cli_does_not_read_expected_results(self):
        with tempfile.TemporaryDirectory() as td:
            relocated = Path(td) / 'experiment'
            shutil.copytree(ROOT, relocated, ignore=shutil.ignore_patterns('__pycache__'))
            (relocated / 'expected-results.json').unlink()
            result = subprocess.run([sys.executable, str(relocated / 'reference/evaluate.py'),
                                     *map(str, sorted((relocated / 'fixtures').glob('*.json')))],
                                    cwd=td, capture_output=True, text=True,
                                    env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(result.stderr, '')
            self.assertEqual(len(json.loads(result.stdout)['results']), 66)

    def test_cli_parse_error_is_machine_readable(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'invalid.json'
            p.write_text('{')
            result = subprocess.run([sys.executable, str(ROOT / 'reference/evaluate.py'), str(p)],
                                    capture_output=True, text=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout), {'results': [e.unbound('JSON_PARSE_ERROR')]})


if __name__ == '__main__':
    unittest.main()
