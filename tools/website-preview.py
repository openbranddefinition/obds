#!/usr/bin/env python3
"""Local candidate preview respecting .vercelignore; never a production server.

Usage: python3 tools/website-preview.py --port 8765
Only binds loopback. No directory listing; omitted material gets the actual 404.
"""
import argparse
import fnmatch
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def pathmatch(path, pattern):
    """Match a root-relative glob without letting a single * cross a slash."""
    names, patterns = path.split('/'), pattern.split('/')
    return len(names) == len(patterns) and all(fnmatch.fnmatchcase(n, p) for n, p in zip(names, patterns))


def excluded(path):
    parts = Path(path).parts
    if any(p.startswith('.') for p in parts):
        return True
    for line in (ROOT / '.vercelignore').read_text().splitlines():
        pattern = line.strip()
        if not pattern or pattern.startswith('#'):
            continue
        if pattern.startswith('!'):
            raise ValueError('Preview requires explicit exclusion patterns, not negations')
        anchored = pattern.startswith('/')
        pattern = pattern.lstrip('/')
        if pattern.endswith('/'):
            folder = pattern.rstrip('/')
            prefixes = ['/'.join(parts[:i]) for i in range(1, len(parts) + 1)]
            if any(pathmatch(p, folder) for p in prefixes) or (not anchored and '/' not in folder and any(fnmatch.fnmatchcase(p, folder) for p in parts)):
                return True
        elif (pathmatch(path, pattern) if anchored or '/' in pattern else any(fnmatch.fnmatchcase(p, pattern) for p in parts)):
            return True
    return False


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_head(self):
        path = unquote(urlsplit(self.path).path).lstrip('/')
        if '..' in Path(path).parts or excluded(path):
            self.send_error(404)
            return None
        return super().send_head()

    def list_directory(self, path):
        self.send_error(404)
        return None

    def send_error(self, code, message=None, explain=None):
        if code != 404:
            return super().send_error(code, message, explain)
        raw = (ROOT / '404.html').read_bytes()
        self.send_response(404)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(raw)

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'OBDS candidate: http://127.0.0.1:{args.port}', flush=True)
    server.serve_forever()
