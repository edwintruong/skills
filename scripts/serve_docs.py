#!/usr/bin/env python3
"""Serve the documentation site locally so in-page edits write back to the .md files.

``build_site.py`` produces a portable file you can email; this serves the same
page from the folder itself, which buys two things a ``file://`` page cannot
have:

* **Save writes the real file.** The editor POSTs to ``/__save`` and the
  Markdown on disk is updated in place — no downloads, no copying files over
  each other, no second copy of the truth.
* **A change on disk arrives without a refresh.** The page polls ``/__poll``
  for modification times and pulls a changed document back through
  ``/__source``, so editing a ``.md`` in your editor — or having the assistant
  rewrite one — updates the open page. A document with unsaved edits in the
  browser is left alone and says so rather than being overwritten.

Usage:
    python3 scripts/serve_docs.py docs/ --title "Loan Platform Docs"
    python3 scripts/serve_docs.py docs/ --port 8899 --no-open

Only ``.md`` files inside the served folder can be written, and the server binds
to localhost unless you deliberately pass ``--host``. It is a writing tool for
one person on one machine, not something to expose to a network.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from build_site import collect_docs, render_html  # noqa: E402

SAVE_PATH = "/__save"
POLL_PATH = "/__poll"
SOURCE_PATH = "/__source"


class DocsHandler(BaseHTTPRequestHandler):
    docs_root: pathlib.Path
    title: str
    phase_names: pathlib.Path | None

    def log_message(self, fmt: str, *args) -> None:  # quieter than the default
        if self.path == SAVE_PATH:
            sys.stderr.write("  %s\n" % (fmt % args))

    # -- shared guards ---------------------------------------------------
    def _md_target(self, rel: str) -> pathlib.Path:
        """Resolve a client-supplied path, or refuse to.

        Two guards, both necessary and both used by reads and writes: stay
        inside the served folder, and only ever touch Markdown. An endpoint that
        can reach any path is a local file primitive, not a docs tool.
        """
        target = (self.docs_root / rel).resolve()
        root = self.docs_root.resolve()
        if not str(target).startswith(str(root) + "/") and target != root:
            raise ValueError(f"refusing to touch a path outside {root}: {rel}")
        if target.suffix.lower() != ".md":
            raise ValueError(f"refusing to touch a non-Markdown file: {rel}")
        return target

    # -- GET -------------------------------------------------------------
    def do_GET(self) -> None:
        path = self.path.split("?")[0]
        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        if path == POLL_PATH:
            # Modification times only. The page compares them against its own
            # copy and asks for the bodies it actually needs, so the poll stays
            # a few hundred bytes however large the set gets.
            root = self.docs_root.resolve()
            stamps = {}
            for p in sorted(self.docs_root.rglob("*.md")):
                try:
                    stamps[p.resolve().relative_to(root).as_posix()] = p.stat().st_mtime_ns
                except (OSError, ValueError):
                    continue
            self._json(200, stamps)
            return
        if path == SOURCE_PATH:
            query = urllib.parse.parse_qs(self.path.partition("?")[2])
            rel = (query.get("path") or [""])[0]
            try:
                body = self._md_target(rel).read_text(encoding="utf-8").encode("utf-8")
            except Exception as exc:
                self._json(404, {"ok": False, "error": str(exc)})
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        if path not in ("/", "/index.html"):
            self.send_error(404, "Only the docs site is served here")
            return
        try:
            docs = collect_docs(self.docs_root)
            if not docs:
                self.send_error(404, f"No .md documents under {self.docs_root}")
                return
            html = render_html(
                docs, self.title, self.phase_names, save_endpoint=SAVE_PATH
            ).encode("utf-8")
        except Exception as exc:  # a broken build should say why, in the browser
            body = f"<pre>Build failed: {exc}</pre>".encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(html)

    # -- POST ------------------------------------------------------------
    def do_POST(self) -> None:
        if self.path != SAVE_PATH:
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            rel = str(payload["path"])
            content = payload["content"]
            if not isinstance(content, str):
                raise ValueError("content must be a string")

            target = self._md_target(rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            print(f"  saved {rel} ({len(content)} chars)")
            self._json(200, {"ok": True, "path": rel, "bytes": len(content.encode('utf-8'))})
        except Exception as exc:
            self._json(400, {"ok": False, "error": str(exc)})

    def _json(self, code: int, obj: dict) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    ap = argparse.ArgumentParser(description="Serve the docs site with save-to-file editing")
    ap.add_argument("docs_root", help="Folder containing the .md documents")
    ap.add_argument("--title", default="Documentation", help="Site title shown in the top bar")
    ap.add_argument("--port", type=int, default=8777)
    ap.add_argument("--host", default="127.0.0.1", help="Bind address; localhost by default")
    ap.add_argument("--phase-names", help="Optional JSON file overriding phase labels")
    ap.add_argument("--no-open", action="store_true", help="Do not open a browser")
    args = ap.parse_args()

    docs_root = pathlib.Path(args.docs_root)
    if not docs_root.is_dir():
        print(f"Not a directory: {docs_root}", file=sys.stderr)
        sys.exit(1)

    DocsHandler.docs_root = docs_root
    DocsHandler.title = args.title
    DocsHandler.phase_names = pathlib.Path(args.phase_names) if args.phase_names else None

    url = f"http://{args.host}:{args.port}/"
    server = ThreadingHTTPServer((args.host, args.port), DocsHandler)
    print(f"Serving {docs_root} at {url}")
    print("Edits made in the page save straight back to the .md files. Ctrl+C to stop.")
    if not args.no_open:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
