import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import evaluate as e


def example(typ='string', value='yes', state='known'):
    fact = {'state': state, 'evidenceRefs': ['ev']}
    if state == 'known':
        fact['value'] = value
    task = {'id': 't', 'action': 'inspect', 'artifactHash': 'sha256:' + 'a'*64, 'inputPackageHash': 'sha256:' + 'b'*64}
    ev = dict(supplier='s', sourceRef='r', method='m', verifier='v', status='verified', fact='f', assertionHash=e.digest({k:v for k,v in fact.items() if k != 'evidenceRefs'}), taskId='t', artifactHash=task['artifactHash'], inputPackageHash=task['inputPackageHash'])
    snap = dict(contractVersion='0.1', task=task, declarations={'f': {'type':typ}}, facts={'f':fact}, evidence={'ev':ev})
    ctx = dict(taskId='t', artifactHash=task['artifactHash'], inputPackageHash=task['inputPackageHash'], snapshotHash=e.digest(snap), acceptedEvidence={'ev':e.digest(ev)})
    cond = dict(id='c', all=[{'fact':'f','op':'present'}], requiresDefined=[])
    return {'family':'family','cases':[dict(id='case', snapshot=snap, verificationContext=ctx, conditions=[cond])]}

class Tests(unittest.TestCase):
    def result(self, f):
        return e.evaluate_family(f)[0]
    def test_canonical(self):
        self.assertEqual(e.canonical_bytes({'z': '\b\t\n\f\r\x00/é', 'a':0}), b'{"a":0,"z":"\\b\\t\\n\\f\\r\\u0000/\xc3\xa9"}')
        self.assertEqual(e.strict_load(b'-0'), 0)
        self.assertEqual(e.canonical_bytes({'\U00010000':1,'\ue000':2}), '{"\ue000":2,"\U00010000":1}'.encode())
    def test_transport_precedence(self):
        for raw in [b'[1.0, NaN]', b'{"a":1,"\\u0061":2}', b'\xef\xbb\xbf{}', b'{} trailing']:
            with self.subTest(raw=raw), self.assertRaises(e.Invalid) as caught:
                e.strict_load(raw)
            self.assertEqual(caught.exception.reason, 'JSON_PARSE_ERROR')
        for raw in [b'1.0', b'1e0', b'9007199254740992', b'9'*5000, b'"\\ud800"']:
            with self.subTest(raw=raw), self.assertRaises(e.Invalid) as caught:
                e.strict_load(raw)
            self.assertEqual(caught.exception.reason, 'NON_CANONICAL_INPUT')
    def test_known_false_and_zero_present(self):
        for typ,value in [('boolean',False),('integer',0),('string','yes')]:
            self.assertEqual(self.result(example(typ,value))['outcome'], 'APPLIES')
    def test_empty_absent_and_unknown(self):
        f=example(state='empty')
        self.assertEqual(self.result(f)['outcome'], 'DOES_NOT_APPLY')
        f['cases'][0]['conditions'][0]['all'][0]['op']='absent'
        self.assertEqual(self.result(f)['outcome'], 'APPLIES')
        self.assertEqual(self.result(example(state='unknown'))['reason'], 'FACT_UNKNOWN')
    def test_missing(self):
        f=example(); c=f['cases'][0]; c['snapshot']['facts']={}; c['snapshot']['evidence']={}
        self.assertEqual(self.result(f)['reason'],'FACT_MISSING')
    def test_hash_binding_and_evidence_tampering(self):
        for mutation in ['action','accepted','assertion','status']:
            f=example(); c=f['cases'][0]
            if mutation=='action': c['snapshot']['task']['action']='other'
            elif mutation=='accepted': c['verificationContext']['acceptedEvidence']={}
            else: c['snapshot']['evidence']['ev'][{'assertion':'assertionHash','status':'status'}[mutation]] = 'sha256:'+'c'*64 if mutation=='assertion' else 'asserted'
            self.assertEqual(self.result(f)['reason'],'EVIDENCE_UNVERIFIED')
    def test_routing_before_duplicates(self):
        f=example(); f['cases'].append(copy.deepcopy(f['cases'][0])); del f['cases'][1]['snapshot']
        with self.assertRaises(e.Invalid) as caught:e.evaluate_family(f)
        self.assertEqual(caught.exception.reason,'SCHEMA_INVALID')
    def test_duplicate_ids(self):
        for case_dup in [True,False]:
            f=example()
            if case_dup:f['cases'].append(copy.deepcopy(f['cases'][0]))
            else:f['cases'][0]['conditions']*=2
            with self.assertRaises(e.Invalid) as caught:e.evaluate_family(f)
            self.assertEqual(caught.exception.reason,'DUPLICATE_ID')
    def test_bound_bad_snapshot(self):
        for snap in [None, [], 42, {'contractVersion':'0.2'}]:
            f=example(); f['cases'][0]['snapshot']=snap
            r=self.result(f)
            self.assertEqual(r['snapshotHash'],e.digest(snap)); self.assertEqual(r['reason'],'SCHEMA_INVALID'); self.assertEqual(r['caseId'],'case')
    def test_condition_isolation(self):
        f=example(); conditions=f['cases'][0]['conditions']; conditions.append(copy.deepcopy(conditions[0])); conditions[1]['id']='other'; conditions[0]['extra']=1
        self.assertEqual([r['outcome'] for r in e.evaluate_family(f)], ['INVALID','APPLIES'])
    def test_layer_precedence(self):
        f=example('integer',True); f['cases'][0]['verificationContext']=None
        self.assertEqual(self.result(f)['reason'],'TYPE_MISMATCH')
        f['cases'][0]['snapshot']['facts']['undeclared']={'state':'empty','evidenceRefs':['ev']}
        self.assertEqual(self.result(f)['reason'],'UNDECLARED_FACT')
    def test_association(self):
        self.assertEqual(self.result(example('association-set',[['a','b'],['a','c']]))['reason'],'ASSOCIATION_CONFLICT')
        self.assertEqual(self.result(example('association-set',[['a','b'],['a','b']]))['reason'],'TYPE_MISMATCH')
    def test_temporal(self):
        f=example('date-time','2026-10-01T00:00:00+02:00'); a=f['cases'][0]['conditions'][0]['all'][0]; a.update(op='equals',value='2026-09-30T22:00:00Z')
        self.assertEqual(self.result(f)['outcome'],'APPLIES')
        a['value']='2026-10-01'; self.assertEqual(self.result(f)['reason'],'TIME_BASIS_UNRESOLVED')
        for v in ['2026-02-30T00:00:00Z','2026-01-01T00:00:00-00:00','2026-01-01T00:00:00+14:01']:
            self.assertEqual(self.result(example('date-time',v))['reason'],'TYPE_MISMATCH')
    def test_conservative_conjunction(self):
        f=example(); c=f['cases'][0]; c['snapshot']['declarations']['g']={'type':'boolean'}
        c['verificationContext']['snapshotHash']=e.digest(c['snapshot'])
        c['conditions'][0]['all']=[{'fact':'f','op':'absent'},{'fact':'g','op':'present'}]
        self.assertEqual(self.result(f)['reason'],'FACT_MISSING')
        c['conditions'][0]['all'].reverse();self.assertEqual(self.result(f)['reason'],'FACT_MISSING')
    def test_cli_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'valid.json';p.write_text(json.dumps(example()))
            completed=subprocess.run([sys.executable,str(Path(e.__file__)),str(p),str(p.parent/'missing')], capture_output=True,text=True)
            self.assertEqual(completed.returncode,2)
            rows=json.loads(completed.stdout)['results'];self.assertEqual(len(rows),2);self.assertEqual(rows[0]['outcome'],'APPLIES');self.assertEqual(rows[1],e.unbound('INPUT_IO_ERROR'))
    def test_single_api_unbound(self):
        f=example()['cases'][0]
        for cond,reason in [({},'SCHEMA_INVALID'),({'id':'x','bad':1.0},'NON_CANONICAL_INPUT')]:
            r=e.evaluate(f['snapshot'],cond,f['verificationContext']);self.assertIsNone(r['snapshotHash']);self.assertIsNone(r['conditionId']);self.assertEqual(r['reason'],reason)

if __name__=='__main__':unittest.main()
