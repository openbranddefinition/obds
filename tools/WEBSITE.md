# Current website checks

The explanatory website is validated separately from the frozen OBDS 4.1.3 release.
The existing release gate, deployment checker, release archives, frozen inventories,
package manifests and historical publication record are unchanged.

From the repository root:

```sh
python3 tools/website-check.py
python3 tools/test-website-publication.py
python3 tools/website-preview.py --port 8765
```

The preview binds only to `127.0.0.1`. It applies `.vercelignore` exclusions,
does not list directories, and serves the existing 404 body with status 404.
It is a review server, not a production deployment.

In another terminal, check the delivered candidate:

```sh
python3 tools/website-check.py --base http://127.0.0.1:8765
```

The same `--base` option checks an authorised deployment: exact current-page,
asset and release-artifact bytes; required historical public paths; private-path
exclusions; and missing-route behaviour. A local pass does not certify a remote
deployment that has not been checked.

After reviewing deliberate website changes, regenerate only the new website record:

```sh
python3 tools/website-check.py --write-manifest
```

`website-publication.json` describes the current informative website. It is not
a normative OBDS artifact, a release manifest or evidence of production enforcement.
The checker compares protected tracked files with pre-reframe commit
`fd5f6f73be00ba40eef13625d7c5949831fd44c1` before writing that record. Adding a new
editorial route requires updating its explicit route inventory and sitemap.

For share cards, use the existing generator with the environment containing the
release dependencies and `rsvg-convert`:

```sh
.venv/bin/python tools/build-og-images.py --render-only
python3 tools/website-check.py --write-manifest
```

Existing identity and favicon are preserved. Cards carry the current OBDS release
stamp; the website checker verifies their dimensions and stamps independently.

## Historical verification

The original `v4.1.3` tag resolves to
`8c6d056ee7fb256fc78e469d4c8fe385dcf175f9`. Verify its publication using its own
`reference/release-gate.py` and frozen inventory in an isolated tag checkout.
The release download can be extracted separately and checked with its unmodified
`reference/release-gate.py` from the extracted package root.

Do not run a release rebuild or rewrite `publication-record.json`,
`PACKAGE-MANIFEST.json` or `release-work/4.1.3/RC-INVENTORY.json` to accept the new
HTML. The historical homepage hash intentionally describes the earlier website.
The historical deployment checker is for that historical publication, not the
current reframe. Its endpoint lists are reused by the new current-site checker.

Local planning, review reports and browser screenshots live in ignored `md/`.
