#!/usr/bin/env python3
"""Validate the current explanatory website independently of frozen OBDS evidence.

  python3 tools/website-check.py --write-manifest  # new WEBSITE record only
  python3 tools/website-check.py                 # verify local candidate
  python3 tools/website-check.py --base http://127.0.0.1:8765

Historical tools/deploy-smoke-test.py and reference/release-gate.py are unchanged.
Run their historical-publication checks in the original release checkout, not
against a reframed website. Never regenerate historical hashes to accept HTML.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import struct
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = 'https://openbranddefinition.org'
BASELINE = 'fd5f6f73be00ba40eef13625d7c5949831fd44c1'
RELEASE_COMMIT = '8c6d056ee7fb256fc78e469d4c8fe385dcf175f9'
ROUTES = ['/', '/what-is-obds/', '/use-cases/', '/insights/', '/resources/',
          '/ecosystem/', '/authoring/', '/research/', '/research/supabrand/',
          '/machine-readable-brand-guidelines/', '/brand-governance-for-ai/',
          '/compare/machine-readable-brand-specifications/', '/examples/', '/legal/']
PAGES = [r.lstrip('/') + 'index.html' for r in ROUTES]
NAV = ['/what-is-obds/', '/use-cases/', '/insights/', '/resources/',
       'https://github.com/openbranddefinition/obds']
HISTORICAL = ['publication-record.json', 'PACKAGE-MANIFEST.json',
              'release-work/4.1.3/RC-INVENTORY.json', 'reference/release-gate.py',
              'tools/deploy-smoke-test.py', 'favicon.svg']
ASSETS = ['assets/site.css', 'assets/experience.css', 'assets/site.js']
RECORD = 'website-publication.json'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def git(*args, root=ROOT):
    return subprocess.check_output(['git', *args], cwd=root)


def protected_files(root=ROOT):
    """Use committed blobs, never a newly regenerated release manifest."""
    allowed = set(PAGES + ['llms.txt', 'sitemap.xml', '.gitignore', '.vercelignore'])
    records = git('ls-tree', '-r', '-z', BASELINE, root=root).split(b'\0')
    count = 0
    for record in records:
        if not record:
            continue
        meta, raw_path = record.split(b'\t', 1)
        path = raw_path.decode()
        if path in allowed or path.startswith('og/'):
            continue
        expected = meta.split()[2].decode()
        file = root / path
        require(file.is_file(), 'Protected artifact missing: ' + path)
        raw = file.read_bytes()
        actual = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        require(actual == expected, 'Protected artifact changed: ' + path)
        count += 1
    require((root / 'VERSION').read_text().strip() == '4.1.3', 'Release changed')
    return count


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids, self.links, self.metadata, self.canonicals = [], [], {}, []
        self.h1, self.nav, self.in_nav = 0, [], False
        self.lang = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.append(a['id'])
        if tag == 'html':
            self.lang = a.get('lang')
        if tag == 'h1':
            self.h1 += 1
        if tag == 'nav' and a.get('class') == 'primary-nav':
            self.in_nav = True
        if tag == 'a' and self.in_nav:
            self.nav.append(a.get('href'))
        if tag == 'meta':
            self.metadata[a.get('name', a.get('property'))] = a.get('content')
        if tag == 'link' and a.get('rel') == 'canonical':
            self.canonicals.append(a.get('href'))
        if tag in ('a', 'link') and 'href' in a:
            self.links.append(a['href'])
        if tag in ('script', 'img') and 'src' in a:
            self.links.append(a['src'])
        if tag == 'meta' and a.get('property') == 'og:image':
            self.links.append(a['content'])

    def handle_endtag(self, tag):
        if tag == 'nav':
            self.in_nav = False


def resolve_link(url, route):
    value = urllib.parse.urlparse(urllib.parse.urljoin(DOMAIN + route, url))
    if value.netloc != urllib.parse.urlparse(DOMAIN).netloc:
        return None
    path = urllib.parse.unquote(value.path).lstrip('/')
    if not path or path.endswith('/'):
        path += 'index.html'
    require('..' not in Path(path).parts, 'Unsafe local path')
    return path, urllib.parse.unquote(value.fragment)


def content_checks(root=ROOT):
    preview_spec = importlib.util.spec_from_file_location('website_preview', root / 'tools/website-preview.py')
    preview = importlib.util.module_from_spec(preview_spec)
    preview_spec.loader.exec_module(preview)
    tracked_or_new = git('ls-files', '--cached', '--others', '--exclude-standard', '-z', root=root).decode().split('\0')
    public_html = {p for p in tracked_or_new if p.endswith('.html') and not preview.excluded(p)}
    require(public_html == set(PAGES + ['404.html']), 'Public HTML inventory differs from current website routes')
    pages = {p: Page((root / p).read_text()) for p in PAGES}
    links = 0
    for route, path in zip(ROUTES, PAGES):
        page = pages[path]
        require(len(page.ids) == len(set(page.ids)), path + ': duplicate IDs')
        require(page.h1 == (2 if route in ['/', '/legal/'] else 1), path + ': heading count')
        require(page.lang == ('de' if route == '/legal/' else 'en'), path + ': default language')
        source = (root / path).read_text()
        numbers = [int(n) for n in re.findall(r'<div class="section-number">(?:<span>)?(\d+) /', source)]
        require(numbers == list(range(1, len(numbers) + 1)), path + ': section numbering')
        require('hreflang=' not in source, path + ': language toggles are not separate indexed translations')
        require('carries parallel English and German copy' not in source, path + ': inaccurate language disclosure')
        require(page.canonicals == [DOMAIN + route], path + ': canonical')
        require(page.nav == NAV, path + ': navigation differs')
        for key in ['description', 'og:title', 'og:description', 'og:image', 'og:image:alt', 'twitter:image']:
            require(bool(page.metadata.get(key)), path + ': missing ' + key)
        require(page.metadata['obds-version'] == '4.1.3', path + ': release metadata')
        require(page.metadata.get('robots') == 'index,follow', path + ': crawler policy')
        raw = (root / urllib.parse.urlparse(page.metadata['og:image']).path.lstrip('/')).read_bytes()
        require(raw[:8] == b'\x89PNG\r\n\x1a\n', path + ': invalid OG image')
        require(struct.unpack('>II', raw[16:24]) == (1200, 630), path + ': OG dimensions')
        offset, release_stamp = 8, None
        while offset + 12 <= len(raw):
            length = struct.unpack('>I', raw[offset:offset + 4])[0]
            kind, data = raw[offset + 4:offset + 8], raw[offset + 8:offset + 8 + length]
            if kind == b'tEXt' and data.startswith(b'OBDS-Release\0'):
                release_stamp = data.split(b'\0', 1)[1]
            offset += length + 12
        require(release_stamp == b'4.1.3', path + ': OG release stamp')
        for url in page.links:
            resolved = resolve_link(url, route)
            if not resolved:
                continue
            target, fragment = resolved
            require((root / target).is_file(), path + ': missing link ' + url)
            if fragment and target.endswith('.html'):
                target_page = pages.get(target) or Page((root / target).read_text())
                require(fragment in target_page.ids, path + ': missing fragment ' + url)
            links += 1
    home = (root / 'index.html').read_text()
    require(not re.search(r'<section\b[^>]*class="[^"]*\blegal\b', home), 'Legal notice must not be a homepage section')
    require('/legal/' in pages['index.html'].links, 'Separate legal page must be reachable')
    for anchor in ['top','why','scale','decide','distinctive','compile','create','prove','difference','challenged','open','licensing','release','legal']:
        require(anchor in pages['index.html'].ids, 'Historical homepage anchor missing: ' + anchor)
    for phrase in ['The right brand truth,', 'before AI acts.', 'ROUND 4 MIXED', '39/40', '93/93', '0/20', 'not 20 wrong decisions', 'Automatic candidate acceptance is not cleared for production']:
        require(phrase in home, 'Homepage boundary missing: ' + phrase)
    comparison = (root / 'compare/machine-readable-brand-specifications/index.html').read_text()
    for phrase in ['Open specifications / protocols.', 'Products / infrastructure.', 'Not a ranking.', 'Sameness']:
        require(phrase in comparison, 'Comparison grouping missing: ' + phrase)
    require('brandbook.md' not in comparison.lower(), 'Excluded comparison system present')
    sitemap = ET.parse(root / 'sitemap.xml')
    urls = [e.text for e in sitemap.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    require(len(urls) == len(set(urls)), 'Duplicate sitemap URL')
    for route in ROUTES:
        require(DOMAIN + route in urls, 'Route missing from sitemap: ' + route)
    for url in urls:
        require((root / resolve_link(url, '/')[0]).is_file(), 'Sitemap target missing: ' + url)
    llms = (root / 'llms.txt').read_text()
    require('Current release: 4.1.3' in llms, 'llms current release')
    for url in re.findall(r'https://openbranddefinition\.org/[^\s)\]>]+', llms):
        target = root / resolve_link(url, '/')[0]
        schema_base = urllib.parse.urlparse(url).path in ['/schemas/1.0.0/', '/value-schemas/1.0.0/']
        require(target.is_file() or (schema_base and target.parent.is_dir()), 'llms target missing: ' + url)
    for file in ['.gitignore', '.vercelignore']:
        require('md/' in (root / file).read_text().splitlines(), file + ': local notes exposed')
    return links


def public_artifacts(root=ROOT):
    # Current release documents and public schema trees are immutable inputs.
    # protected_files checks their committed bytes BEFORE this record is built.
    paths = set()
    tracked = git('ls-tree', '-r', '--name-only', BASELINE, root=root).decode().splitlines()
    for folder in ['spec/4.1.3', 'schemas', 'value-schemas', 'release-schemas']:
        paths.update(p for p in tracked if p.startswith(folder + '/'))
    for route, path in zip(ROUTES, PAGES):
        for url in Page((root / path).read_text()).links:
            target = resolve_link(url, route)
            if target and not target[0].endswith(('.html', '.css', '.js', '.png', '.svg')) and target[0] != RECORD:
                paths.add(target[0])
    return [{'path': p, 'url': '/' + p, 'status': 200, 'sha256': digest((root / p).read_bytes())}
            for p in sorted(paths)]


def build_record(root=ROOT):
    files = PAGES + ASSETS + ['llms.txt', 'sitemap.xml', '404.html', 'robots.txt', 'favicon.svg']
    files += sorted({urllib.parse.urlparse(Page((root / p).read_text()).metadata['og:image']).path.lstrip('/') for p in PAGES})
    entries = []
    for path in files:
        url = '/' + path
        if path.endswith('index.html'):
            url = url[:-10]
        entries.append({'path': path, 'url': url, 'status': 200, 'sha256': digest((root / path).read_bytes())})
    return {'kind': 'obds-current-website-publication', 'normative': False,
            'date': '2026-09-19', 'obdsRelease': '4.1.3',
            'historicalReleaseCommit': RELEASE_COMMIT, 'preReframeCommit': BASELINE,
            'note': 'Current explanatory website only. Frozen release evidence and historical publication-record.json are not refreshed by this record.',
            'publication': entries,
            'preservedEvidence': [{'path': p, 'sha256': digest((root / p).read_bytes())} for p in HISTORICAL],
            'publicArtifacts': public_artifacts(root)}


def verify_record(record, root=ROOT):
    require(record == build_record(root), 'Current website record differs; inspect edits before writing a new WEBSITE manifest')


def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=25) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def verify_deployment(base, record, root=ROOT, get=fetch):
    spec = importlib.util.spec_from_file_location('historical_deploy', root / 'tools/deploy-smoke-test.py')
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    checks = record['publication'] + record['publicArtifacts']
    checks += [{'url': '/' + p, 'status': 200, 'sha256': digest((root / p).read_bytes())}
               for p in [RECORD, 'publication-record.json']]
    def exact(entry):
        code, raw = get(base + entry['url'])
        require(code == entry['status'] and digest(raw) == entry['sha256'], 'Delivered byte/status drift: ' + entry['url'])
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(exact, checks))
    private = [p for p, _ in old.MUST_BE_ABSENT]
    private += ['/md/OBDS-WEBSITE-IMPLEMENTATION-PLAN-v1.md', '/tools/website-check.py', '/.git/config',
                '/openbranddefinition-site-0.9.5-public-draft/index.html']
    for path in private:
        code, _ = get(base + path)
        require(code in (403, 404), 'Private path exposed: ' + path)
    for path in old.MUST_BE_PRESENT:
        code, _ = get(base + path)
        require(code == 200, 'Required public file unavailable: ' + path)
    code, raw = get(base + '/__obds_website_missing__')
    require(code == 404 and raw == (root / '404.html').read_bytes(), 'Incorrect missing-route status/body')
    return len(checks), len(private)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-manifest', action='store_true')
    parser.add_argument('--base', help='Check delivered bytes and private-path exclusions too')
    args = parser.parse_args()
    count = protected_files()
    # The record itself is a link target, so first materialise only the new website record.
    if args.write_manifest:
        (ROOT / RECORD).write_text(json.dumps(build_record(), indent=2) + '\n')
    links = content_checks()
    record = json.loads((ROOT / RECORD).read_text())
    verify_record(record)
    print(f'CURRENT WEBSITE: PASS — {len(PAGES)} pages, {links} local links, {count} protected files unchanged')
    if args.base:
        public, private = verify_deployment(args.base.rstrip('/'), record)
        print(f'DELIVERY: PASS — {public} exact public files, {private} private paths excluded')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (AssertionError, OSError, ValueError, KeyError) as exc:
        print('CURRENT WEBSITE: FAIL —', exc, file=sys.stderr)
        raise SystemExit(1)
