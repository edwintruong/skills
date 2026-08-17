#!/usr/bin/env python3
"""Render a single Markdown document to a self-contained HTML file.

This is ``build_site.py`` with one document and the sidebar hidden — deliberately
the same renderer, not a second one. Two templates drifting apart is how a
diagram ends up displaying correctly in the site build and wrongly in the
one-off export.

Everything the site build gives you applies here: Mermaid and images sized to
the page, wide tables scrolling inside their own box, an editor that writes back
to the ``.md``, offline rendering with no CDN.

Usage:
    python3 scripts/export_html.py docs/system/4.1-design.md
    python3 scripts/export_html.py input.md -o out.html --title "Container diagram"
    python3 scripts/export_html.py docs/api/*.md --outdir build/
"""

from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from build_site import parse_doc, render_html  # noqa: E402


def render(md_path: pathlib.Path, out_path: pathlib.Path, title: str | None) -> None:
    doc = parse_doc(md_path, md_path.parent)
    html = render_html([doc], title or doc["title"], single=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"{md_path}  ->  {out_path}  ({out_path.stat().st_size / 1024:.0f} KB)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Markdown -> self-contained HTML")
    ap.add_argument("inputs", nargs="+", help="Markdown file(s)")
    ap.add_argument("-o", "--output", help="Output file (single input only)")
    ap.add_argument("--outdir", help="Output directory (defaults to alongside input)")
    ap.add_argument("--title", help="Override the <title>; defaults to the H1")
    args = ap.parse_args()

    paths = [pathlib.Path(p) for p in args.inputs]
    missing = [p for p in paths if not p.is_file()]
    if missing:
        for p in missing:
            print(f"No such file: {p}", file=sys.stderr)
        return 1

    if args.output and len(paths) > 1:
        print("--output takes a single input; use --outdir for several.", file=sys.stderr)
        return 1

    for p in paths:
        if args.output:
            out = pathlib.Path(args.output)
        elif args.outdir:
            out = pathlib.Path(args.outdir) / (p.stem + ".html")
        else:
            out = p.with_suffix(".html")
        render(p, out, args.title)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
