#!/usr/bin/env python3
"""Generate one Open Graph preview image per public page and wire it in.

Every page that already carries `og:title` gets a 1200x630 card rendered from
that title, so the card and the page can never drift apart: the title is read
from the HTML, never from a second list kept alongside it.

The cards use the site's own vocabulary — black paper, white ink, Helvetica
Neue for the title, monospace for the machine-facing lines, and the frame and
letterforms of `favicon.svg` as the mark.

Rendering is done by `rsvg-convert` (Homebrew `librsvg`). The SVG sources are
temporary; only the PNGs under `og/` are kept, and `tools/` never ships to the
site, so the generator stays private while its output is public.

Every card is stamped with the release it was rendered for, in a PNG tEXt
chunk named `OBDS-Release`. The cards print the release in their top-right
corner, and the cards published with 4.1.0, 4.1.1 and 4.1.2 still printed 4.0.4
because nothing in the release process re-rendered them. The stamp makes that mechanical:
reference/release-gate.py reads it back and refuses a stale or unstamped card,
tools/build-release.py refuses to build with one, and tools/deploy-smoke-test.py
checks the cards the site actually serves.

Usage, from the repository root:

    python3 tools/build-og-images.py            # render og/*.png and patch the HTML
    python3 tools/build-og-images.py --render-only
    python3 tools/build-og-images.py --check    # report drift, change nothing
"""

from __future__ import annotations

import html
import importlib.util
import re
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OG_DIR = ROOT / "og"
SITE = "https://openbranddefinition.org"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

W, H = 1200, 630
INSET = 40              # frame inset, mirrors favicon.svg
PAD = 48                # text padding inside the frame
TITLE_MAX = 132
TITLE_MIN = 58
TITLE_LINES = 3

# Relative advance widths for Helvetica Neue Bold, good enough to break lines.
NARROW = set("iljItf.,;:!'|()[]/-")
WIDE = set("mwMW@")


def advance(ch: str) -> float:
    if ch == " ":
        return 0.28
    if ch in ("—", "–"):
        return 1.0
    if ch in NARROW:
        return 0.32
    if ch in WIDE:
        return 0.88
    if ch.isupper() or ch.isdigit():
        return 0.70
    return 0.57


def text_width(s: str, size: float) -> float:
    return sum(advance(c) for c in s) * size


def wrap(title: str, size: float, limit: float) -> list[str] | None:
    """Greedy wrap; None when a single word cannot fit on one line."""
    lines: list[str] = []
    current = ""
    for word in title.split():
        if text_width(word, size) > limit:
            return None
        candidate = f"{current} {word}".strip()
        if text_width(candidate, size) <= limit:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines if len(lines) <= TITLE_LINES else None


def fit(title: str, limit: float) -> tuple[float, list[str]]:
    for size in range(TITLE_MAX, TITLE_MIN - 1, -2):
        lines = wrap(title, size, limit)
        if lines:
            return float(size), lines
    return float(TITLE_MIN), wrap(title, TITLE_MIN, limit * 2) or [title]


MARK = (
    '<g transform="translate({x},{y}) scale({s})">'
    '<rect x="9" y="9" width="46" height="46" fill="none" stroke="#fff" stroke-width="2"/>'
    '<path d="M18 42V22h11c7 0 11 3.5 11 10s-4 10-11 10H18Zm7-6h4c3 0 4.5-1.3 4.5-4S32 28 29 28h-4v8Z" fill="#fff"/>'
    '<path d="M43 22h5v20h-5z" fill="#fff"/>'
    "</g>"
)


def card_svg(title: str, path: str) -> str:
    left = INSET + PAD
    limit = W - 2 * left
    size, lines = fit(title, limit)
    leading = size * 1.06
    block = leading * (len(lines) - 1)
    first = (H / 2) - block / 2 + size * 0.34

    rows = "".join(
        f'<text x="{left}" y="{first + i * leading:.0f}" class="t">{html.escape(line)}</text>'
        for i, line in enumerate(lines)
    )
    mark = MARK.format(x=W - INSET - PAD - 40, y=H - INSET - PAD - 34, s=0.62)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>
  .t {{ font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-weight: 700;
        font-size: {size:.0f}px; fill: #fff; letter-spacing: -0.02em; }}
  .m {{ font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; font-size: 19px;
        fill: #fff; letter-spacing: 0.14em; }}
  .dim {{ opacity: 0.58; }}
</style>
<rect width="{W}" height="{H}" fill="#000"/>
<rect x="{INSET}" y="{INSET}" width="{W - 2 * INSET}" height="{H - 2 * INSET}"
      fill="none" stroke="#fff" stroke-width="2"/>
<text x="{left}" y="{INSET + PAD + 18}" class="m dim">OPEN BRAND DEFINITION SPECIFICATION</text>
<text x="{W - left}" y="{INSET + PAD + 18}" class="m dim" text-anchor="end">{VERSION}</text>
{rows}
<text x="{left}" y="{H - INSET - PAD}" class="m">openbranddefinition.org{html.escape(path)}</text>
{mark}
</svg>
"""


def slug_for(page: Path) -> str:
    rel = page.parent.relative_to(ROOT).as_posix()
    return "home" if rel == "." else rel.replace("/", "-")


def meta(pattern: str, text: str) -> str | None:
    m = re.search(pattern, text)
    return m.group(1) if m else None


def pages() -> list[tuple[Path, str, str, str]]:
    found = []
    for page in sorted(ROOT.rglob("index.html")):
        if any(part in {"tools", "node_modules", "answers"} for part in page.parts):
            continue
        text = page.read_text(encoding="utf-8")
        title = meta(r'<meta property="og:title" content="([^"]*)"', text)
        if not title:
            continue
        url = meta(r'<meta property="og:url" content="([^"]*)"', text) or SITE + "/"
        found.append((page, html.unescape(title), url[len(SITE):] or "/", slug_for(page)))
    return found


IMAGE_BLOCK = (
    '  <meta property="og:image" content="{url}">\n'
    '  <meta property="og:image:width" content="1200">\n'
    '  <meta property="og:image:height" content="630">\n'
    '  <meta property="og:image:type" content="image/png">\n'
    '  <meta property="og:image:alt" content="{alt}">\n'
)


def patch(page: Path, slug: str, title: str) -> bool:
    text = page.read_text(encoding="utf-8")
    image = f"{SITE}/og/{slug}.png"
    block = IMAGE_BLOCK.format(
        url=image,
        alt=html.escape(f"{title} — Open Brand Definition Specification {VERSION}", quote=True),
    )

    text = re.sub(r'^[ \t]*<meta property="og:image[^>]*>\n', "", text, flags=re.M)
    text = re.sub(r'^[ \t]*<meta name="twitter:image[^>]*>\n', "", text, flags=re.M)

    anchor = re.search(r'^[ \t]*<meta property="og:(?:description|title)"[^>]*>\n', text, flags=re.M)
    if not anchor:
        return False
    text = text[: anchor.end()] + block + text[anchor.end():]

    # Rewritten from whatever is there, so a second run is a no-op rather than a
    # page that lost its twitter:image because the card had already been widened.
    text = re.sub(
        r'^([ \t]*)<meta name="twitter:card" content="[^"]*">\n',
        lambda m: f'{m.group(1)}<meta name="twitter:card" content="summary_large_image">\n'
        f'{m.group(1)}<meta name="twitter:image" content="{image}">\n',
        text,
        count=1,
        flags=re.M,
    )

    before = page.read_text(encoding="utf-8")
    if text == before:
        return False
    page.write_text(text, encoding="utf-8")
    return True


def _gate():
    spec = importlib.util.spec_from_file_location("og_release_gate", ROOT / "reference" / "release-gate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stamp(raw: bytes, release: str) -> bytes:
    """Insert one tEXt chunk `OBDS-Release` = release directly after IHDR."""
    gate = _gate()
    signature = gate.PNG_SIGNATURE
    if not raw.startswith(signature) or raw[12:16] != b"IHDR":
        raise ValueError("rsvg-convert did not produce a PNG with a leading IHDR")
    ihdr_end = len(signature) + 12 + struct.unpack(">I", raw[8:12])[0]
    body = gate.OG_STAMP_KEYWORD.encode("latin-1") + b"\0" + release.encode("latin-1")
    chunk = struct.pack(">I", len(body)) + b"tEXt" + body + struct.pack(">I", zlib.crc32(b"tEXt" + body))
    stamped = raw[:ihdr_end] + chunk + raw[ihdr_end:]
    assert gate.png_text_chunks(stamped).get(gate.OG_STAMP_KEYWORD) == release
    return stamped


def main() -> int:
    args = set(sys.argv[1:])
    check = "--check" in args
    render_only = "--render-only" in args

    if not check:
        OG_DIR.mkdir(exist_ok=True)

    missing, patched = [], []
    for page, title, path, slug in pages():
        png = OG_DIR / f"{slug}.png"
        if check:
            if not png.exists():
                missing.append(png.relative_to(ROOT).as_posix())
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False, encoding="utf-8") as tmp:
            tmp.write(card_svg(title, path))
            svg = tmp.name
        subprocess.run(
            ["rsvg-convert", "-w", str(W), "-h", str(H), "-o", str(png), svg],
            check=True,
        )
        Path(svg).unlink()
        png.write_bytes(stamp(png.read_bytes(), VERSION))
        print(f"og/{slug}.png  {title}")
        if not render_only and patch(page, slug, title):
            patched.append(page.relative_to(ROOT).as_posix())

    if check:
        for m in missing:
            print(f"missing: {m}")
        stale = [] if missing else _gate().og_card_problems(ROOT, VERSION)
        for problem in stale:
            print(f"stale: {problem}")
        return 1 if missing or stale else 0

    for p in patched:
        print(f"patched  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
