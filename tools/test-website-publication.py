#!/usr/bin/env python3
"""Regression checks for separating current-site validation from frozen evidence."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


website = load('website', 'tools/website-check.py')
preview = load('preview', 'tools/website-preview.py')


class PublicationBoundaryTests(unittest.TestCase):
    def test_frozen_files_reject_mutation_or_missing_file(self):
        path = 'publication-record.json'
        tree = website.git('ls-tree', '-r', '-z', website.BASELINE, '--', path)
        original = (ROOT / path).read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'VERSION').write_text('4.1.3\n')
            (root / path).write_bytes(original)
            with patch.object(website, 'git', return_value=tree):
                self.assertEqual(website.protected_files(root), 1)
                (root / path).write_bytes(original + b'\n')
                with self.assertRaisesRegex(AssertionError, 'Protected artifact changed'):
                    website.protected_files(root)
                (root / path).unlink()
                with self.assertRaisesRegex(AssertionError, 'Protected artifact missing'):
                    website.protected_files(root)

    def test_public_artifacts_only_use_committed_schema_files(self):
        paths = {e['path'] for e in website.public_artifacts()}
        self.assertIn('spec/4.1.3/OBDS-4.1.3-FINAL.zip', paths)
        self.assertIn('schemas/1.0.0/brand-manifest.schema.json', paths)
        self.assertNotIn('schemas/.DS_Store', paths)
        self.assertNotIn('value-schemas/.DS_Store', paths)

    def test_root_archives_excluded_release_downloads_preserved(self):
        self.assertTrue(preview.excluded('openbranddefinition-site-0.9.5-public-draft.zip'))
        self.assertFalse(preview.excluded('spec/4.1.3/OBDS-4.1.3-FINAL.zip'))
        self.assertFalse(preview.excluded('spec/1.1.6/OBDS-1.1.6-FINAL.zip'))

    def test_directory_globs_and_deep_private_files(self):
        for path in ['openbranddefinition-site-0.9.5-public-draft/index.html',
                     'test.egg-info/PKG-INFO', 'md/OBDS-WEBSITE-IMPLEMENTATION-PLAN-v1.md',
                     'tools/website-check.py', '.git/config', '.env.local',
                     'reference/task-facts/1.0/evidence/interop/reports/FINAL-RESULT.md']:
            self.assertTrue(preview.excluded(path), path)
        self.assertFalse(preview.excluded('reference/task-facts/1.0/evidence/interop/cycles/cycle-1/implementation-python/evaluate.py'))

    def delivered(self, url):
        from urllib.parse import urlparse
        path = urlparse(url).path.lstrip('/')
        if not path or path.endswith('/'):
            path += 'index.html'
        file = ROOT / path
        if preview.excluded(path) or not file.is_file():
            return 404, (ROOT / '404.html').read_bytes()
        return 200, file.read_bytes()

    def test_current_site_delivery_independent_of_old_homepage_hash(self):
        record = json.loads((ROOT / website.RECORD).read_text())
        historical = json.loads((ROOT / 'release-work/4.1.3/RC-INVENTORY.json').read_text())
        self.assertNotEqual(record['publication'][0]['sha256'], historical['publication'][0]['sha256'])
        website.verify_deployment('https://candidate.example', record, get=self.delivered)

    def test_wrong_current_page_bytes_fail(self):
        record = json.loads((ROOT / website.RECORD).read_text())
        def get(url):
            if url == 'https://candidate.example/':
                return 200, b'<html>wrong candidate</html>'
            return self.delivered(url)
        with self.assertRaisesRegex(AssertionError, 'Delivered byte/status drift'):
            website.verify_deployment('https://candidate.example', record, get=get)

    def test_missing_release_download_fails(self):
        record = json.loads((ROOT / website.RECORD).read_text())
        def get(url):
            if url.endswith('/spec/4.1.3/OBDS-4.1.3-FINAL.zip'):
                return 404, b'missing'
            return self.delivered(url)
        with self.assertRaisesRegex(AssertionError, 'Delivered byte/status drift'):
            website.verify_deployment('https://candidate.example', record, get=get)

    def test_exposed_private_plan_fails(self):
        record = json.loads((ROOT / website.RECORD).read_text())
        def get(url):
            if url.endswith('/md/OBDS-WEBSITE-IMPLEMENTATION-PLAN-v1.md'):
                return 200, b'private plan'
            return self.delivered(url)
        with self.assertRaisesRegex(AssertionError, 'Private path exposed'):
            website.verify_deployment('https://candidate.example', record, get=get)


if __name__ == '__main__':
    unittest.main()
