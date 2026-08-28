# Open Brand Definition website

Static bilingual one-page website for `openbranddefinition.org`.

## Public status

- Current release: OBDS 1.0.2 (stable)
- Previous releases: OBDS 1.0.1 and OBDS 1.0.0, published as released and not modified
- Stable release date shown on the site: 28 August 2026
- Initial public publication shown on the site: 22 July 2026
- Conformance suite: 107 tests passed, 0 failed, 0 skipped
- Public downloads: the specification, the package and the schemas are published under `/spec/`, `/schemas/` and `/value-schemas/`

## Files

- `LICENSE.md`: which licence applies to which material
- `LICENSES/`: the unmodified CC BY 4.0 and Apache 2.0 texts
- `NOTICE`: Apache attribution notice
- `TRADEMARKS.md`, `GOVERNANCE.md`, `CONTRIBUTING.md`
- `examples/`: minimal Foundation example and fail-closed example
- `index.html`: complete bilingual site, CSS and JavaScript included
- `llms.txt`: non-normative orientation file for AI crawlers and agents. Navigation only, never a source of Brand Truth
- `proposals/`: non-normative, unratified notes. Not part of any release
- `publication-record.json`: machine-readable publication metadata and index hash
- `VERSION`: visible deployment version
- `favicon.svg`: site icon
- `404.html`: error page
- `robots.txt`: search engine rules
- `sitemap.xml`: homepage sitemap
- `CNAME`: GitHub Pages custom domain file

## Deployment

Upload every file to the public root of the domain. No build step is required.

The page uses:

- no external fonts
- no framework
- no analytics
- no tracking scripts
- no cookies set by the page itself

## Important publication note

The page states an initial public publication date of 22 July 2026, a stable release date of 27 August 2026 for OBDS 1.0.0 and OBDS 1.0.1, and 28 August 2026 for OBDS 1.0.2. Keep the visible dates, JSON-LD, sitemap and `publication-record.json` in sync before deployment.

A website publication records public disclosure. It does not by itself create ownership of an abstract idea or replace legal advice.

## Before publishing

- Confirm the legal notice and disclosure details.
- Recompute `websiteIndexSha256` in `publication-record.json` whenever `index.html` changes.
- Configure HTTPS.
- Configure the preferred `www` redirect.
- Keep a copy of the deployed files and hosting or Git commit timestamps.

## Licensing

- Specification and documentation: **CC BY 4.0**
- Schemas, release metadata, reference implementation, conformance suite and examples: **Apache License 2.0**

Commercial implementation is permitted and requires no separate permission. See
`LICENSE.md` for the mapping and `TRADEMARKS.md` for what is governed separately.

## Building a release

The reference implementation and the conformance suite ship inside the release
package. From an unpacked package root:

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python reference/run_all.py        # 107 passed, 0 failed, 0 skipped
.venv/bin/python reference/release-gate.py   # metadata, contract identity, licences, junk
```

The release gate proves that the normative contract fingerprints are identical to
the previous release and that the two standard licence texts are unmodified.
