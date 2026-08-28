# Open Brand Definition website

Static bilingual one-page website for `openbranddefinition.org`.

## Public status

- Current release: OBDS 1.0.1 (stable)
- Previous release: OBDS 1.0.0, published as released and not modified
- Stable release date shown on the site: 27 August 2026
- Initial public publication shown on the site: 22 July 2026
- Conformance suite: 105 tests passed, 0 failed
- Public downloads: the specification, the package and the schemas are published under `/spec/`, `/schemas/` and `/value-schemas/`

## Files

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

The page states an initial public publication date of 22 July 2026 and a stable release date of 27 August 2026 for OBDS 1.0.0 and OBDS 1.0.1. Keep the visible dates, JSON-LD, sitemap and `publication-record.json` in sync before deployment.

A website publication records public disclosure. It does not by itself create ownership of an abstract idea or replace legal advice.

## Before publishing

- Confirm the legal notice and disclosure details.
- Publish the licence documents for the licensing model described in section 11 of the page. Until they exist, the page states an intended model and grants nothing.
- Recompute `websiteIndexSha256` in `publication-record.json` whenever `index.html` changes.
- Configure HTTPS.
- Configure the preferred `www` redirect.
- Keep a copy of the deployed files and hosting or Git commit timestamps.
