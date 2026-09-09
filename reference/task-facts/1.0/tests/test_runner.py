import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
P = module('comparison', ROOT / 'compare.py')
R = module('runner', ROOT / 'run-suite.py')

class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.suite, self.root, self.identity = P.load_suite(ROOT / 'SUITE.json')
        self.wanted = P.expected(self.root, self.suite['groups'][0])
    def payload(self, rows=None):
        return json.dumps({'results': self.wanted if rows is None else rows}).encode()
    def test_all_expected_records_and_identity(self):
        self.assertEqual([len(P.expected(self.root, g)) for g in self.suite['groups']], [66,36])
        self.assertEqual(len(self.identity),64)
        self.assertEqual(P.compare(self.payload(),2,self.wanted)[1],[])
    def test_outcome_hash_reorder_missing_duplicate(self):
        for kind in ['outcome','snapshotHash','reorder','missing','duplicate']:
            with self.subTest(kind=kind):
                rows=json.loads(self.payload())['results']
                if kind=='outcome': rows[0][kind]='UNKNOWN'
                elif kind=='snapshotHash': rows[0][kind]='sha256:'+'0'*64
                elif kind=='reorder': rows[0],rows[1]=rows[1],rows[0]
                elif kind=='missing': rows.pop()
                else: rows.append(rows[0])
                self.assertTrue(P.compare(self.payload(rows),2,self.wanted)[1])
    def test_protocol_refusals(self):
        cases=[b'garbage', b'{"results":[],"extra":0}', b'[]', b'{"results":[],"results":[]}',b'{"results":NaN}',b'{"results":[]} trailing']
        for field in ['extra','missing','type','surrogate']:
            rows=json.loads(self.payload())['results']
            if field=='extra':rows[0]['basis']='unallowed'
            elif field=='missing':del rows[0]['family']
            elif field=='type':rows[0]['family']=1
            else:rows[0]['family']='\ud800'
            cases.append(self.payload(rows))
        for raw in cases:
            with self.subTest(raw=raw[:60]),self.assertRaises(P.ProtocolError):P.records(raw)
    def test_unexpected_exit(self):
        for code in [0,1,3,-9]:self.assertTrue(P.compare(self.payload(),code,self.wanted)[1])
    def test_suite_digest_and_missing_file_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'suite';shutil.copytree(ROOT,target,ignore=shutil.ignore_patterns('evidence'))
            p=target/self.suite['groups'][0]['inputs'][0]['path'];p.write_bytes(p.read_bytes()+b' ')
            with self.assertRaises(P.IdentityError):P.load_suite(target/'SUITE.json')
            p.unlink()
            with self.assertRaises(OSError):P.load_suite(target/'SUITE.json')
    def test_timeout_report(self):
        args=argparse.Namespace(suite=ROOT/'SUITE.json',command=[sys.executable,'-c','import time; time.sleep(2)'],implementation_name='timeout',implementation_version='1',timeout=.01)
        report=R.run(args);self.assertEqual(report['exitCode'],2);self.assertFalse(report['passed']);self.assertEqual(report['groups'][0]['error'],'timeout')
    def test_raw_protocol_no_repair(self):
        raw_inputs=[b'{"a":1,"a":2}',b'\xff',b'1.0',b'NaN',b'9007199254740992',b'"\\ud800"']
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'raw'
            script='import pathlib,sys; sys.stdout.buffer.write(pathlib.Path(sys.argv[1]).read_bytes())'
            for raw in raw_inputs:
                p.write_bytes(raw);before=P.digest(p)
                output=subprocess.run([sys.executable,'-c',script,str(p)],capture_output=True,check=True)
                self.assertEqual(output.stdout,raw);self.assertEqual(P.digest(p),before)
    def test_invalid_routing_records_are_literal(self):
        g=self.suite['groups'][1];expected=P.expected(self.root,g)
        duplicate=[r for r in expected if r['reason']=='DUPLICATE_ID']
        self.assertGreaterEqual(len(duplicate),2)
        for r in duplicate:self.assertTrue(all(r[k] is None for k in P.FIELDS[:4]))
        self.assertTrue(any(r['outcome']=='INVALID' and r['snapshotHash'] is not None for r in expected))

if __name__=='__main__':unittest.main()
