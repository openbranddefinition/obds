import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from test_experiment import ROOT, e, FAMILIES

VECTORS = json.loads((ROOT / 'regressions/expected-results.json').read_text())['vectors']


class ContractV02Tests(unittest.TestCase):
    def test_original_bytes_and_all_decisions_preserved(self):
        manifest = json.loads((ROOT / 'PACKAGE-MANIFEST.json').read_text())
        for relative, digest in manifest['preservedV01Files'].items():
            self.assertEqual('sha256:' + hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), digest)
        expected = json.loads((ROOT / 'expected-results.json').read_text())['results']
        actual = [row for family in FAMILIES for row in e.evaluate_family(family)]
        self.assertEqual(len(actual), 66)
        self.assertEqual(actual, [{k: v for k, v in row.items() if k != 'basis'} for row in expected])

    def test_multi_file_errors_preserve_other_family_results(self):
        paths = [ROOT / 'fixtures/01-two-claims.json', ROOT / 'regressions/inputs/nan.json',
                 ROOT / 'regressions/inputs/empty-all.json']
        result = subprocess.run([sys.executable, str(ROOT / 'reference/evaluate.py'), *map(str, paths)],
                                capture_output=True, text=True,
                                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stderr, '')
        self.assertEqual(json.loads(result.stdout)['results'],
                         [row for path in paths for row in e.evaluate_path(path)])


def regression(vector):
    def test(self):
        path = ROOT / 'regressions' / vector['input']
        self.assertEqual(e.evaluate_path(path), vector['expected'])
        result = subprocess.run([sys.executable, str(ROOT / 'reference/evaluate.py'), str(path)],
                                capture_output=True, text=True,
                                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stderr, '')
        self.assertEqual(json.loads(result.stdout), {'results': vector['expected']})
    return test


for vector in VECTORS:
    setattr(ContractV02Tests, 'test_regression_' + vector['id'].replace('-', '_'), regression(vector))
