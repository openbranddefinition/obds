#!/usr/bin/env python3
"""Mandatory Task Facts release mutation checks; temporary copies only."""
import importlib.util
from pathlib import Path
import shutil
import tempfile

ROOT=Path(__file__).resolve().parents[1]
TF=ROOT/'reference/task-facts/1.0'
spec=importlib.util.spec_from_file_location('tf_comparison',TF/'compare.py')
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)


def verify_large_piped_reader_parity():
    """F3: both CLI modes must finish large responses captured through a pipe."""
    import json
    import subprocess
    import sys
    sys.path.insert(0, str(ROOT / 'reference/foundation/src'))
    from obds_ref.canonical import canonical_json_bytes
    from obds_ref.governed_io import load_data
    reader = ROOT / 'reference/adversarial/canonical_js.mjs'
    results = []
    with tempfile.TemporaryDirectory() as d:
        synthetic = Path(d) / 'large.json'
        # Much larger than a pipe buffer, with Unicode and line normalization
        # making the parser-stage and canonical-stage expectations distinct.
        synthetic.write_text(json.dumps({'payload': 'é e\u0301\r\n' * 32768}), encoding='utf-8')
        for label, source in [('evidence-manifest', TF / 'EVIDENCE-MANIFEST.json'),
                              ('large-synthetic', synthetic)]:
            document = load_data(source)
            expected_by_mode = {
                '--read': canonical_json_bytes(document),
                '--read-parse': json.dumps(document, ensure_ascii=True, sort_keys=True,
                                           separators=(',', ':')).encode('ascii'),
            }
            for mode, expected in expected_by_mode.items():
                expected_wire = expected.hex().encode('ascii') + b'\n'
                assert len(expected_wire) > 65536, 'Regression must exceed the observed pipe truncation'
                child = subprocess.run(['node', str(reader), mode, str(source)],
                                       capture_output=True, timeout=30)
                assert child.returncode == 0, child.stderr.decode(errors='replace')
                assert child.stderr == b'', child.stderr
                assert child.stdout == expected_wire, (label, mode, len(child.stdout), len(expected_wire))
                results.append({'input': label, 'mode': mode, 'canonicalOrParsedBytes': len(expected),
                                'pipedBytes': len(child.stdout), 'passed': True})
    return results


def verify_bom_reader_parity():
    """The decoder must leave a BOM for the strict JSON parser to refuse."""
    import subprocess
    import sys
    sys.path.insert(0, str(ROOT / 'reference/foundation/src'))
    from obds_ref.governed_io import ValidationFailure, load_data
    reader = ROOT / 'reference/adversarial/canonical_js.mjs'
    results = []
    with tempfile.TemporaryDirectory() as d:
        source = Path(d) / 'bom.json'
        source.write_bytes(b'\xef\xbb\xbf{}')
        try:
            load_data(source)
        except ValidationFailure:
            pass
        else:
            raise AssertionError('Python unexpectedly accepts the BOM')
        for mode in ['--read', '--read-parse']:
            child = subprocess.run(['node', str(reader), mode, str(source)],
                                   capture_output=True, timeout=30)
            assert child.returncode != 0 and child.stdout == b'', (mode, child.stdout)
            assert b'governed JSON' in child.stderr, child.stderr
            results.append({'mode': mode, 'bomRefused': True, 'passed': True})
    return results


def verify_publication_occurrences():
    """Independent mutations rehash the complete site inventory for every trial."""
    import json
    import re
    spec = importlib.util.spec_from_file_location('publication_gate', ROOT / 'reference/release-gate.py')
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    results = []
    with tempfile.TemporaryDirectory() as d:
        site = Path(d)
        originals = {}
        for rel in gate.PUBLICATION_URLS:
            destination = site / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, destination)
            originals[rel] = destination.read_text(encoding='utf-8')

        def trial(label, rel=None, replacement=None, accepted=False):
            if rel is not None:
                (site / rel).write_text(replacement, encoding='utf-8')
            inventory = {'publication': [
                {'path': path, 'url': url, 'sha256': gate.sha256_file(site / path).removeprefix('sha256:')}
                for path, url in gate.PUBLICATION_URLS.items()]}
            try:
                gate.verify_publication(site, inventory)
            except (AssertionError, ValueError, KeyError, OSError) as exc:
                assert not accepted, (label, str(exc))
                diagnostic = str(exc)
            else:
                assert accepted, 'Stale/missing publication field accepted: ' + label
                diagnostic = 'accepted'
            finally:
                if rel is not None:
                    (site / rel).write_text(originals[rel], encoding='utf-8')
            results.append({'case': label, 'passed': True, 'inventoryRecomputed': True,
                            'expected': 'ACCEPT' if accepted else 'REJECT', 'diagnostic': diagnostic})

        def structured(rel, edit):
            original = originals[rel]
            match = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', original, re.S)
            document = json.loads(match[2])
            edit(document)
            return original[:match.start(2)] + json.dumps(document, sort_keys=True) + original[match.end(2):]

        trial('both homepage objects current', accepted=True)
        homepage = 'index.html'
        for kind in ['SoftwareSourceCode', 'TechArticle']:
            def stale(document, kind=kind):
                next(node for node in document['@graph'] if node.get('@type') == kind)['version'] = '4.1.0'
            trial(kind + ' stale, other current', homepage, structured(homepage, stale))
            def missing(document, kind=kind):
                del next(node for node in document['@graph'] if node.get('@type') == kind)['version']
            trial(kind + ' version missing', homepage, structured(homepage, missing))
        def stale_download(document):
            next(node for node in document['@graph'] if node.get('@type') == 'SoftwareSourceCode')['url'] = 'https://openbranddefinition.org/spec/4.1.0/OBDS-4.1.0-FINAL.zip'
        trial('download stale with current versions', homepage, structured(homepage, stale_download))
        trial('homepage reordered keys and graph', homepage,
              structured(homepage, lambda document: document['@graph'].reverse()), accepted=True)
        companion = 'what-is-obds/index.html'
        trial('companion reordered keys', companion, structured(companion, lambda document: None), accepted=True)
        trial('companion about stale', companion,
              structured(companion, lambda document: document['about'].update(version='4.1.0')))
        trial('companion decoy current version cannot satisfy about', companion,
              structured(companion, lambda document: (document['about'].update(version='4.1.0'), document.update(version='4.1.1'))))
        for rel in [homepage, companion]:
            original = originals[rel]
            trial(rel + ' malformed JSON-LD', rel, original.replace('"@context":', '"@context" invalid:', 1))
            trial(rel + ' unterminated JSON-LD', rel, original.replace('</script>', '', 1))
            trial(rel + ' duplicate JSON key', rel, original.replace('"version": "4.1.1"', '"version": "4.1.0", "version": "4.1.1"', 1))
            trial(rel + ' non-JSON constant', rel, original.replace('"@context":', '"invalid": NaN, "@context":', 1))
        def duplicate_identity(document):
            document['@graph'].append(dict(next(node for node in document['@graph'] if node.get('@type') == 'SoftwareSourceCode')))
        trial('duplicate semantic identity', homepage, structured(homepage, duplicate_identity))
        trial('duplicate identity in separate script', homepage,
              originals[homepage].replace('</head>', '<script type="application/ld+json">{"@id":"https://openbranddefinition.org/#implementation","@type":"SoftwareSourceCode","version":"4.1.1"}</script></head>'))
        status = '<div class="status">OBDS / 4.1.1 stable</div>'
        stale_status = originals[homepage].replace(status, status.replace('4.1.1', '4.1.0'), 1)
        trial('stale status plus current comment decoy', homepage,
              stale_status.replace('</body>', '<!--' + status + '--></body>'))
        trial('stale status plus current element decoy', homepage,
              stale_status.replace('</body>', status + '</body>'))
        # This is the pre-existing explicitly historical footer sentence, not a
        # new whole-page historical exemption. The baseline retains it exactly.
        assert '4.1.0' in originals['llms.txt']
        trial('existing intentional 4.1.0 history remains valid', accepted=True)
        current_line = 'Current release: 4.1.1 (stable, 10 September 2026)'
        trial('llms stale declaration plus current copy in other section', 'llms.txt',
              originals['llms.txt'].replace(current_line, current_line.replace('4.1.1', '4.1.0'), 1) + '\n' + current_line + '\n')
        anchor = '<a href="/spec/4.1.1/OBDS-4.1.1.md">'
        positions = [match.start() for match in re.finditer(re.escape(anchor), originals[homepage])]
        assert len(positions) > 1
        for index, offset in enumerate(positions):
            original = originals[homepage]
            replacement = original[:offset] + anchor.replace('4.1.1', '4.1.0') + original[offset + len(anchor):]
            trial('repeated anchor occurrence ' + str(index), homepage, replacement)
    return results


def verify_repository_gate_closure():
    """Exercise the production licensing scanner and all bound homepage claims."""
    spec = importlib.util.spec_from_file_location('closure_gate', ROOT / 'reference/release-gate.py')
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    records = []
    homepage = (ROOT / 'index.html').read_text(encoding='utf-8')
    phrase = '35 existing public contracts plus optional Task Facts'
    gate.verify_homepage_contracts(homepage)
    records.append({'case': 'approved four count claims', 'passed': True})
    parsed = gate._ContractClaims(homepage)
    for path in gate.HOMEPAGE_CONTRACT_PATHS:
        _, start, end = parsed.claims[path]
        for replacement in [phrase.replace('35', '34'), phrase.replace('35', '36'),
                            'existing public contracts plus optional Task Facts',
                            '35 public contracts including Task Facts',
                            '35 existing public contracts plus required Task Facts',
                            phrase + ', including Task Facts in that total',
                            phrase + ', but Task Facts is required',
                            phrase + ' and 36 existing public contracts',
                            '<!--' + phrase + '-->',
                            '<script>' + phrase + '</script>']:
            changed = homepage[:start] + homepage[start:end].replace(phrase, replacement) + homepage[end:]
            changed = changed.replace('</body>', '<p>35</p></body>')
            try:
                gate.verify_homepage_contracts(changed)
            except AssertionError:
                records.append({'case': repr(path) + ': ' + replacement, 'passed': True, 'expected': 'REJECT'})
            else:
                raise AssertionError('Invalid count claim accepted: ' + replacement)
        missing = homepage[:start] + homepage[end:]
        try:
            gate.verify_homepage_contracts(missing.replace('</body>', '<p data-copy="en">' + phrase + '</p></body>'))
        except AssertionError:
            records.append({'case': repr(path) + ': relocated decoy', 'passed': True, 'expected': 'REJECT'})
        else:
            raise AssertionError('Relocated claim accepted')
    formatted = homepage.replace(phrase, '<strong>35</strong> existing public <em>contracts</em> plus optional <span>Task Facts</span>')
    gate.verify_homepage_contracts(formatted)
    with tempfile.TemporaryDirectory() as d:
        site = Path(d)
        for rel in gate.PUBLICATION_URLS:
            destination = site / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, destination)
        (site / 'index.html').write_text(formatted, encoding='utf-8')
        gate.verify_publication(site)
        records.append({'case': 'inline formatting through full publication validator', 'passed': True})
        historical = site / gate.HISTORICAL_CHANGELOG
        shutil.copy2(ROOT / gate.HISTORICAL_CHANGELOG, historical)
        assert not gate.retired_licensing_failures(site, [historical])
        records.append({'case': 'preserved historical changelog accepted', 'passed': True})
        historical.write_bytes(historical.read_bytes() + b'\n')
        assert gate.retired_licensing_failures(site, [historical])
        records.append({'case': 'historical byte drift refused', 'passed': True})
        for rel in ['OBDS-4.1.1-CHANGELOG.md', 'OBDS-4.1.1-IMPLEMENTER-QUICKSTART.md',
                    'README.md', *gate.PUBLICATION_URLS]:
            target = site / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            for retired in gate.RETIRED_LICENSING_WORDING:
                target.write_text(retired, encoding='utf-8')
                scan = gate.current_licensing_paths(site, [] if rel in gate.PUBLICATION_URLS else [target], "repository")
                assert set(site / name for name in gate.PUBLICATION_URLS) <= set(scan)
                diagnostics = gate.retired_licensing_failures(site, scan)
                assert any(rel in diagnostic for diagnostic in diagnostics), (rel, retired)
                records.append({'case': rel + ': ' + retired, 'passed': True, 'expected': 'REJECT'})
            target.write_text('', encoding='utf-8')
    return records


def verify_changelog_history():
    """Production scanner regressions with immutable historical suffix binding."""
    spec = importlib.util.spec_from_file_location('changelog_gate', ROOT / 'reference/release-gate.py')
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    name = 'OBDS-4.1.1-CHANGELOG.md'
    original = (ROOT / name).read_bytes()
    history = (ROOT / gate.HISTORICAL_CHANGELOG).read_bytes()
    assert original.endswith(history)
    prefix = original[:-len(history)]
    records = []
    with tempfile.TemporaryDirectory() as directory:
        site = Path(directory)
        target = site / name

        def trial(label, content, accepted=False, rel=name, wording=False):
            path = site / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            scan = gate.current_licensing_paths(site, [path], 'repository')
            failures = gate.retired_licensing_failures(site, scan)
            relevant = [failure for failure in failures if rel in failure]
            assert bool(relevant) != accepted, (label, failures)
            if wording:
                assert any('retired licensing wording' in failure for failure in relevant), (label, failures)
            records.append({'case': label, 'passed': True,
                            'expected': 'ACCEPT' if accepted else 'REJECT',
                            'diagnostics': relevant})

        trial('clean current section and complete verified history', original, True)
        # Independently locate both records, then exercise the whole production
        # scanner: acceptance cannot rely on a matching phrase in isolation.
        for version, phrase in [('1.0.1', 'Free Use'),
                                ('1.0.2', 'separate commercial licence')]:
            section = history.split(('## ' + version + '\n').encode(), 1)[1].split(b'\n## ', 1)[0]
            offset = section.lower().index(phrase.lower().encode())
            historical_phrase = section[offset:offset + len(phrase)]
            trial(version + ' truthful historical record accepted', original, True)
            trial(version + ' historical claim copied into current section',
                  prefix + historical_phrase + b'\n\n' + history, wording=True)
            trial(version + ' historical claim moved into current section',
                  prefix + historical_phrase + b'\n\n' + history.replace(historical_phrase, b'', 1))
        for phrase in gate.RETIRED_LICENSING_WORDING:
            encoded = phrase.encode()
            trial('current section rejects ' + phrase, prefix + encoded + b'\n\n' + history, wording=True)
            trial('unclassified preamble rejects ' + phrase,
                  prefix.replace(b'## 4.1.1', encoded + b'\n\n## 4.1.1', 1) + history, wording=True)
            trial('verified historical heading cannot shelter new ' + phrase,
                  prefix + history.replace(b'## 1.0.2\n', b'## 1.0.2\n' + encoded + b'\n', 1))
            for rel in ['README.md', 'OBDS-4.1.1-IMPLEMENTER-QUICKSTART.md', *gate.PUBLICATION_URLS]:
                base = (ROOT / rel).read_bytes()
                trial(rel + ' intact current surface rejects ' + phrase,
                      base + b'\n' + encoded + b'\n', rel=rel, wording=True)
                (site / rel).write_bytes(base)
        for heading in [b'', b'## 4.1.1\n\n## 4.1.1', b'### 4.1.1', b'##4.1.1',
                        b'## 4.1', b'## 4.1.1 trailing', b'## 4.1.1 ##', b' ## 4.1.1',
                        b'## 4.1.0', b'## 4.2.0', b'4.1.1\n------']:
            trial('missing/malformed/conflicting current heading ' + repr(heading),
                  prefix.replace(b'## 4.1.1', heading, 1) + history)
        for label, mutation in [
            ('duplicate document title', prefix + b'# OBDS changelog\n\n' + history),
            ('unknown historical heading before boundary', prefix + b'## 3.9.0\n\nFree Use\n\n' + history),
            ('non-version section before boundary', prefix + b'## History\n\nFree Use\n\n' + history),
            ('duplicate historical boundary', original + history),
            ('missing history', prefix),
            ('malformed historical title', original.replace(b'# OBDS 4.1.0 -', b'## OBDS 4.1.0 -', 1)),
            ('malformed historical version', original.replace(b'## 1.0.2\n', b'### 1.0.2\n', 1)),
            ('duplicate historical version', original.replace(b'## 1.0.2\n', b'## 1.0.2\n\n## 1.0.2\n', 1)),
            ('unrelated historical record altered', original.replace(b'## 3.0.3\n', b'## 3.0.3\nNew note\n', 1)),
            ('history truncated', original[:-1]),
            ('trailing current claim', original + b'\nFree Use\n'),
            ('trailing clean unclassified text', original + b'\nNew note\n'),
            ('history hidden by code fence', prefix + b'```\n\n' + history),
            ('history hidden by HTML comment', prefix + b'<!--\n\n' + history),
            ('history hidden by HTML container', prefix + b'<div>\n\n' + history),
            ('invalid UTF-8 current section', prefix + b'\xff\n\n' + history),
            ('normalized historical line endings', prefix + history.replace(b'\n', b'\r\n')),
        ]:
            trial(label, mutation)
        trial('ordinary current subsection remains fully scanned',
              prefix + b'### Licensing\n\nFree Use\n\n' + history, wording=True)
        trial('clean current subsection accepted', prefix + b'### Packaging\n\nMeasured release tools.\n\n' + history, True)
        # All version records, unrelated prose, and legacy headings stay intact.
        trial('complete unrelated historical records preserved', original, True)
        assert (ROOT / name).read_bytes() == original
        assert (ROOT / gate.HISTORICAL_CHANGELOG).read_bytes() == history
    return records


def verify_licensing_test_source():
    """Content-authenticated executable role, with claim precedence and drift."""
    spec = importlib.util.spec_from_file_location('source_role_gate', ROOT / 'reference/release-gate.py')
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    source_rel = 'tools/test-task-facts-release.py'
    source = (ROOT / source_rel).read_bytes()
    records = []
    with tempfile.TemporaryDirectory() as directory:
        site = Path(directory)

        def trial(label, rel, content, accepted=False):
            target = site / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            failures = gate.retired_licensing_failures(site, [target])
            assert bool(failures) != accepted, (label, failures)
            records.append({'case': label, 'expected': 'ACCEPT' if accepted else 'REJECT',
                            'passed': True, 'diagnostics': failures})

        trial('reviewed executable negative-test material', source_rel, source, True)
        for label, content in [
            ('marker alone', b'# non-claim executable release regression\n'),
            ('malformed executable', b'def broken(\n'),
            ('empty executable', b''),
            ('removed rejection assertion', source.replace(b'assert bool(relevant) != accepted', b'assert True #', 1)),
            ('disabled entry point', source.replace(b'raise SystemExit(main())', b'pass', 1)),
            ('mixed module documentation', source + b'\n"""Current licence: Free Use"""\n'),
            ('mixed comment claim', source + b'\n# Current licence: Free Use\n'),
        ]:
            trial(label, source_rel, content)
        # Neither a reviewed filename nor an executable-looking new source can
        # move the role to unknown bytes or to documentation in a tools folder.
        for rel in ['tools/test-other.py', 'tests/test-other.py', 'tools/README.md',
                    'tests/README.md', 'README.md', 'RELEASE-NOTES.md',
                    'OBDS-4.1.1-IMPLEMENTER-QUICKSTART.md', *gate.PUBLICATION_URLS]:
            trial('copied test source into ' + rel, rel, source)
        for retired in gate.RETIRED_LICENSING_WORDING:
            for rel in ['README.md', 'RELEASE-NOTES.md', 'tools/README.md', 'tests/README.md',
                        'OBDS-4.1.1-IMPLEMENTER-QUICKSTART.md', *gate.PUBLICATION_URLS]:
                trial('moved payload into ' + rel + ': ' + retired, rel, retired.encode())
        original_registry = gate.NON_CLAIM_EXECUTABLE_SOURCES
        try:
            for record in [None, {}, {'role': 'current claim', 'sha256': original_registry[source_rel]['sha256']},
                           {**original_registry[source_rel], 'claim': True},
                           {**original_registry[source_rel], 'sha256': 'invalid'}]:
                gate.NON_CLAIM_EXECUTABLE_SOURCES = {source_rel: record}
                trial('ambiguous registration ' + repr(record), source_rel, source)
            gate.NON_CLAIM_EXECUTABLE_SOURCES = {}
            trial('absent affirmative role', source_rel, source)
            # Even exactly authenticated executable bytes cannot overrule a
            # current publication identity or a documentation file type.
            for rel in ['index.html', 'README.md']:
                gate.NON_CLAIM_EXECUTABLE_SOURCES = {rel: original_registry[source_rel]}
                trial('claim role takes precedence ' + rel, rel, source)
            gate.NON_CLAIM_EXECUTABLE_SOURCES = original_registry
            previous_urls = gate.PUBLICATION_URLS
            try:
                gate.PUBLICATION_URLS = {**previous_urls, source_rel: 'https://example.invalid/current'}
                trial('conflicting current publication on executable path', source_rel, source)
            finally:
                gate.PUBLICATION_URLS = previous_urls
        finally:
            gate.NON_CLAIM_EXECUTABLE_SOURCES = original_registry
        missing = site / source_rel
        missing.unlink()
        assert gate.retired_licensing_failures(site, [missing])
        records.append({'case': 'missing reviewed executable fails closed', 'expected': 'REJECT', 'passed': True})
        trial('reviewed executable still accepted after mutations', source_rel, source, True)
    return records


def main():
    records=[]
    for missing in ['run-suite.py','schemas/task-facts.schema.json','examples/01-two-claims.json']:
        with tempfile.TemporaryDirectory() as d:
            dst=Path(d)/'suite';shutil.copytree(TF,dst,ignore=shutil.ignore_patterns('evidence'))
            (dst/missing).unlink()
            try:P.load_suite(dst/'SUITE.json')
            except (OSError,ValueError):records.append({'mutation':missing,'rejected':True})
            else:raise AssertionError('Missing suite content accepted: '+missing)
    import json
    print(json.dumps({'passed':True,'mutations':records,
                      'largePipedReaderParity':verify_large_piped_reader_parity(),
                      'bomReaderParity':verify_bom_reader_parity(),
                      'publicationOccurrences':verify_publication_occurrences(),
                      'repositoryGateClosure':verify_repository_gate_closure(),
                      'changelogHistory':verify_changelog_history(),
                      'licensingTestSource':verify_licensing_test_source()},indent=2))
    return 0

if __name__=='__main__':raise SystemExit(main())
