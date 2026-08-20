#!/usr/bin/env python3
"""Build one self-contained documentation website from a folder of Markdown docs.

Every document is rendered client-side (marked.js + mermaid.js, both inlined from
``assets/vendor/``) inside a single HTML file: a phase-grouped sidebar on the
left, the document in the middle, an on-page table of contents on the right.
Images referenced from Markdown (``![caption](path.svg)`` — draw.io exports,
PNGs, whatever) are read from disk and inlined as base64 data URIs at build time.
The result is fully portable and fully offline: no server, no relative paths, no
CDN.

The page can also *edit* the documents it shows. Markdown stays the source of
truth — the editor writes back to the ``.md`` file rather than becoming a second
copy of it. Where a save lands depends on how the page is being viewed:

* served by ``scripts/serve_docs.py`` — the save writes the real file on disk;
* opened as ``file://`` in Chrome/Edge — the File System Access API writes the
  file you pick;
* anywhere else — the ``.md`` downloads and you drop it over the original.

Expected input layout — any folder of ``.md`` files, ideally named with the
phase-numbered convention this skill uses (``4.3-detailed-design.md``):

    docs/
      README.md                 the overview page — becomes the landing page
      1.1-problem-survey.md
      1.2-business-rules.md
      4.1-design.md
      diagrams/
        c4-container.svg
        erd-orders.svg
      ...

Files without a numeric prefix are still included, grouped under "misc".
``README.md`` (or ``index.md``) at the root is the exception: it opens as the
front page under an *Overview* link above the phase groups, and the relative
``.md`` links in its routing tables are rewritten to in-page links.

Usage:
    python3 scripts/build_site.py docs/ -o site.html --title "Loan Platform Docs"
    python3 scripts/build_site.py references/ -o software-docs-site.html
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import pathlib
import re
import sys
import urllib.parse
import unicodedata

ASSETS = pathlib.Path(__file__).resolve().parent.parent / "assets"
TEMPLATE = ASSETS / "site-template.html"
VENDOR = ASSETS / "vendor"
DEFAULT_PHASE_NAMES = ASSETS / "phase-names.json"

# marked and mermaid are vendored so a built page never needs the network.
# If a vendor file is missing the build still works, falling back to a CDN tag
# and saying so — an offline reader would then see an empty page, which is worth
# one loud line at build time.
VENDOR_LIBS = [
    ("marked.min.js", "https://cdn.jsdelivr.net/npm/marked@12/marked.min.js"),
    ("mermaid.min.js", "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"),
]

# A phase-numbered name — "4.3-detailed-design.md". The leading number is the
# lifecycle phase, and it is a single digit: 4.3 is phase 4.
PHASE_FILENAME_RE = re.compile(r"^(\d(?:\.\d+)*)-(.+)\.md$")
# A feature spec named by date — "2026-08-15-ai-shopping-assistant.md".
DATED_FILENAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)\.md$")
# A sequence-numbered decision record — "0001-two-independent-databases.md".
SEQ_FILENAME_RE = re.compile(r"^(\d{3,})-(.+)\.md$")

# Documents that carry no phase number in the filename are placed by the folder
# they live in. Without this, an ADR (0001-…) and a dated feature spec (2026-…)
# each invent a phase of their own and the sidebar grows junk groups.
FOLDER_PHASE = {
    "standards": "0", "conventions": "0",
    "business": "1", "brd": "1", "process": "1", "rules": "1",
    "requirements": "2", "features": "2", "feature": "2", "specs": "2", "spec": "2",
    "analysis": "3", "behaviour": "3", "behavior": "3",
    "system": "4", "design": "4", "architecture": "4", "api": "4", "contracts": "4",
    "ui": "4", "wireframes": "4", "data": "4",
    "dev": "5", "build": "5", "ops": "5", "operations": "5", "adr": "5", "runbook": "5",
    "test": "6", "tests": "6", "qa": "6", "uat": "6",
    "guides": "7", "guide": "7", "usage": "7", "manual": "7",
}
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
META_ROW_RE = re.compile(
    r"\|\s*\*\*(Status|Owner|Last updated|Applies to)\*\*\s*\|\s*(.*?)\s*\|"
)
IMG_RE = re.compile(r"(!\[[^\]]*\]\()([^)\s]+)(\))")

IMAGE_MIME_EXT = {
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


def slugify(stem: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")


def folder_phase(md_path: pathlib.Path, docs_root: pathlib.Path) -> str | None:
    """Phase implied by the folders a document sits in, deepest folder first."""
    try:
        parts = md_path.relative_to(docs_root).parts[:-1]
    except ValueError:
        parts = md_path.parts[:-1]
    for part in reversed(parts):
        phase = FOLDER_PHASE.get(part.lower())
        if phase:
            return phase
    return None


def strip_id_prefix(title: str, doc_id: str) -> str:
    number = doc_id.split()[-1]  # "ADR 0001" -> "0001"
    for prefix in (doc_id, number):
        if prefix and title.startswith(prefix):
            rest = title[len(prefix):].lstrip(" \t—–-:·.")
            if rest:
                return rest
    return title


def classify(md_path: pathlib.Path, docs_root: pathlib.Path) -> tuple[str, str]:
    """Return the (id, phase) a document is listed under in the sidebar."""
    name = md_path.name

    m = PHASE_FILENAME_RE.match(name)
    if m:
        doc_id = m.group(1)
        return doc_id, doc_id.split(".")[0]

    m = DATED_FILENAME_RE.match(name)
    if m:
        return m.group(1), folder_phase(md_path, docs_root) or "2"

    m = SEQ_FILENAME_RE.match(name)
    if m:
        in_adr = any(p.lower() == "adr" for p in md_path.parts)
        return (f"ADR {m.group(1)}" if in_adr else m.group(1)), folder_phase(md_path, docs_root) or "5"

    return md_path.stem, folder_phase(md_path, docs_root) or "misc"


def parse_doc(md_path: pathlib.Path, docs_root: pathlib.Path) -> dict:
    text = md_path.read_text(encoding="utf-8")

    doc_id, phase = classify(md_path, docs_root)

    h1 = H1_RE.search(text)
    title = h1.group(1).strip() if h1 else md_path.stem
    # The id is shown next to the title in the sidebar, so drop it from the
    # title when the H1 repeats it ("# 0001 — Two databases" -> "Two databases").
    title = strip_id_prefix(title, doc_id)

    meta = {}
    for key, val in META_ROW_RE.findall(text[:2000]):
        meta[key.lower().replace(" ", "_")] = val.strip()

    try:
        rel_path = md_path.relative_to(docs_root).as_posix()
    except ValueError:
        rel_path = md_path.name

    return {
        "id": doc_id,
        "phase": phase,
        "home": False,
        "title": title,
        "slug": slugify(md_path.stem),
        "status": meta.get("status", ""),
        "owner": meta.get("owner", ""),
        "updated": meta.get("last_updated", ""),
        # The Markdown is embedded verbatim, relative image paths and all. The
        # page swaps those paths for data URIs at render time using the map
        # below — so what the in-page editor round-trips back to disk is the
        # source you wrote, never a base64 blob.
        "source": text,
        "images": collect_images(text, md_path.parent),
        "rel_path": rel_path,
    }


def collect_images(text: str, base_dir: pathlib.Path) -> dict[str, str]:
    """Map every relative image path in the document to a base64 data URI."""
    images: dict[str, str] = {}
    for _prefix, src, _suffix in IMG_RE.findall(text):
        if src.startswith(("http://", "https://", "data:")) or src in images:
            continue
        img_path = (base_dir / src).resolve()
        ext = img_path.suffix.lower()
        mime = IMAGE_MIME_EXT.get(ext) or mimetypes.guess_type(str(img_path))[0]
        if not mime or not img_path.is_file():
            print(f"  ! image not found or unsupported, left as-is: {src}", file=sys.stderr)
            continue
        data = base64.b64encode(img_path.read_bytes()).decode("ascii")
        images[src] = f"data:{mime};base64,{data}"
    return images


# A relative link out of one document into another: "[x](4.2-data-model.md#erd)".
# Absolute URLs, mail links and pure images are not this script's business.
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*$", re.MULTILINE)
FENCE_RE = re.compile(r"^(?:```|~~~).*?^(?:```|~~~)", re.MULTILINE | re.DOTALL)

# The in-page table of contents collects h2 and h3 only, and past roughly this
# many entries it stops being navigable and starts being a second document.
TOC_BUDGET = 40


def strip_fences(text: str) -> str:
    """Drop fenced blocks — a link inside a template block is an example, not a link."""
    return FENCE_RE.sub("", text)


def anchor_key(text: str) -> str:
    """Normalise a heading or a fragment the way the page's fallback lookup does.

    Diacritics are stripped on both sides, so a hand-written Vietnamese
    fragment ("#211-xac-dinh-tac-nhan" or "#211-xác-định-tác-nhân") matches the
    heading it was written for either way.
    """
    text = urllib.parse.unquote(text)
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", text.replace("\u0111", "d"))


def check_links(docs: list[dict], docs_root: pathlib.Path) -> int:
    """Report dead .md links, dead #fragments, invisible headings and fat pages.

    A dead link inside an internal documentation set is never reported by a
    reader — the set is small enough that everyone assumes someone else noticed.
    So it is reported here, at the one moment the whole set is in memory at once.
    """
    by_rel = {d["rel_path"]: d for d in docs}
    anchors = {}
    problems = []

    for d in docs:
        body = strip_fences(d["source"])
        keys = set()
        toc = 0
        for hashes, title in HEADING_RE.findall(body):
            keys.add(anchor_key(title))
            level = len(hashes)
            if level in (2, 3):
                toc += 1
            elif level >= 4:
                problems.append(
                    f"  ! {d['rel_path']}: H{level} heading is invisible — the page's "
                    f"contents list collects h2 and h3 only: {title.strip()[:60]}"
                )
        anchors[d["rel_path"]] = keys
        if toc > TOC_BUDGET:
            problems.append(
                f"  ! {d['rel_path']}: {toc} entries in the in-page contents "
                f"(budget ~{TOC_BUDGET}) — split the file rather than demoting headings"
            )

    for d in docs:
        here = pathlib.PurePosixPath(d["rel_path"]).parent
        for target in MD_LINK_RE.findall(strip_fences(d["source"])):
            if target.startswith(("http://", "https://", "mailto:", "data:", "//")):
                continue
            path, _, frag = target.partition("#")
            if not path:
                if frag and anchor_key(frag) not in anchors[d["rel_path"]]:
                    problems.append(f"  ! {d['rel_path']}: no heading for in-page link #{frag}")
                continue
            if not path.endswith(".md"):
                continue
            rel = os.path.normpath(str(here / urllib.parse.unquote(path))).replace(os.sep, "/")
            rel = rel[2:] if rel.startswith("./") else rel
            if rel in by_rel:
                if frag and anchor_key(frag) not in anchors[rel]:
                    problems.append(f"  ! {d['rel_path']}: no heading {path}#{frag}")
            elif not (docs_root / here / urllib.parse.unquote(path)).exists():
                # A target outside the built set still counts as alive if the
                # file is on disk — only its fragments cannot be checked here.
                problems.append(f"  ! {d['rel_path']}: dead link -> {target}")

    for line in sorted(set(problems)):
        print(line, file=sys.stderr)
    return len(set(problems))


def find_home(docs_root: pathlib.Path) -> pathlib.Path | None:
    """The overview page: the set's landing page, not a sidebar entry.

    It is the one document a reader is guaranteed to open, so it is rendered as
    the front page rather than dropped — a generated grid of phase cards says
    how many documents exist and nothing about which one to read.
    """
    for name in ("README.md", "readme.md", "index.md"):
        p = docs_root / name
        if p.is_file():
            return p
    return None


def escape_for_script_tag(text: str) -> str:
    return text.replace("</script", "<\\/script")


def vendor_block() -> str:
    """Inline marked and mermaid as base64 `data:` scripts.

    Pasting a minified bundle straight into a <script> element looks simpler and
    is wrong: mermaid's source contains the literal ``<!--``, which pushes the
    HTML tokenizer into script-data-escaped state, and everything after the real
    </script> is then parsed as markup. The symptom is not a blank page — the
    library still mostly runs — but a few hundred junk elements laid out
    off-screen, which is what a stray horizontal scrollbar on a docs page
    usually turns out to be. A data: URI is parsed as JavaScript from the first
    byte, so no escaping question arises at all.
    """
    parts = []
    for filename, cdn in VENDOR_LIBS:
        path = VENDOR / filename
        if path.is_file():
            b64 = base64.b64encode(path.read_bytes()).decode("ascii")
            parts.append(
                f'<script id="{path.stem}" src="data:text/javascript;base64,{b64}"></script>'
            )
        else:
            print(
                f"  ! {path} missing — falling back to the CDN, the page will need "
                f"internet access on first view",
                file=sys.stderr,
            )
            parts.append(f'<script src="{cdn}"></script>')
    return "\n".join(parts)


def collect_docs(docs_root: pathlib.Path, inputs: list[pathlib.Path] | None = None) -> list[dict]:
    if inputs is not None:
        md_files = sorted(inputs)
        home = None
    else:
        md_files = sorted(docs_root.rglob("*.md"))
        home = find_home(docs_root)

    docs = []
    for p in md_files:
        if home is not None and p == home:
            continue
        print(f"  + {p.relative_to(docs_root) if inputs is None else p}")
        docs.append(parse_doc(p, docs_root))

    if home is not None:
        # Parsed like any other document, so the in-page editor can write it
        # back; flagged so the page pins it above the phase groups instead of
        # inventing a phase to file it under.
        print(f"  + {home.relative_to(docs_root)} (overview page)")
        overview = parse_doc(home, docs_root)
        overview.update({"home": True, "id": "", "phase": "home"})
        docs.insert(0, overview)
    return docs


def render_html(
    docs: list[dict],
    title: str,
    phase_names_path: pathlib.Path | None = None,
    save_endpoint: str | None = None,
    single: bool = False,
) -> str:
    if not TEMPLATE.exists():
        raise SystemExit(f"Template not found: {TEMPLATE}")

    manifest = [
        {k: d[k] for k in ("id", "phase", "home", "title", "slug", "status", "owner", "updated", "rel_path")}
        for d in docs
    ]

    phase_names = json.loads(DEFAULT_PHASE_NAMES.read_text(encoding="utf-8"))
    if phase_names_path and phase_names_path.is_file():
        phase_names.update(json.loads(phase_names_path.read_text(encoding="utf-8")))
    for ph in {d["phase"] for d in docs if not d.get("home")}:
        phase_names.setdefault(ph, {"vi": "Khác", "en": "Other"})

    doc_scripts = "\n".join(
        f'<script type="text/plain" id="doc-{i}">{escape_for_script_tag(d["source"])}</script>'
        for i, d in enumerate(docs)
    )

    images = {d["slug"]: d["images"] for d in docs if d["images"]}

    config = {
        "site_key": slugify(title) or "docs",
        "save_endpoint": save_endpoint,
        "single": single,
    }

    template = TEMPLATE.read_text(encoding="utf-8")
    return (
        template.replace("__TITLE__", title)
        .replace("__MANIFEST__", json.dumps(manifest, ensure_ascii=False))
        .replace("__PHASES__", json.dumps(phase_names, ensure_ascii=False))
        .replace("__IMAGES__", escape_for_script_tag(json.dumps(images, ensure_ascii=False)))
        .replace("__CONFIG__", json.dumps(config, ensure_ascii=False))
        .replace("__DOC_SCRIPTS__", doc_scripts)
        .replace("__VENDOR__", vendor_block())
    )


def build(
    docs_root: pathlib.Path,
    out_path: pathlib.Path,
    title: str,
    phase_names_path: pathlib.Path | None,
    save_endpoint: str | None = None,
) -> None:
    docs = collect_docs(docs_root)
    if not docs:
        print(f"No documents to include under {docs_root}", file=sys.stderr)
        sys.exit(1)

    html = render_html(docs, title, phase_names_path, save_endpoint)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")

    problems = check_links(docs, docs_root)

    phases = {d["phase"] for d in docs if not d.get("home")}
    has_overview = any(d.get("home") for d in docs)
    size_kb = out_path.stat().st_size / 1024
    print(
        f"\n{len(docs) - has_overview} documents across {len(phases)} phases "
        f"-> {out_path} ({size_kb:.0f} KB)"
    )
    if problems:
        print(
            f"  ! {problems} link or structure problem(s) above — fix them before "
            f"calling the set done",
            file=sys.stderr,
        )
    if not has_overview:
        print(
            "  ! no README.md/index.md in the folder — the front page falls back to "
            "a phase grid. See references/0.1-visual-style.md#the-overview-page",
            file=sys.stderr,
        )


def main() -> None:
    ap = argparse.ArgumentParser(description="Build a single-file documentation site")
    ap.add_argument("docs_root", help="Folder containing the .md documents")
    ap.add_argument("-o", "--output", default="site.html", help="Output HTML file")
    ap.add_argument("--title", default="Documentation", help="Site title shown in the top bar")
    ap.add_argument(
        "--phase-names",
        help="Optional JSON file overriding phase labels, same shape as assets/phase-names.json",
    )
    ap.add_argument(
        "--save-endpoint",
        help="URL the in-page editor POSTs saves to (set automatically by serve_docs.py)",
    )
    args = ap.parse_args()

    docs_root = pathlib.Path(args.docs_root)
    if not docs_root.is_dir():
        print(f"Not a directory: {docs_root}", file=sys.stderr)
        sys.exit(1)

    build(
        docs_root=docs_root,
        out_path=pathlib.Path(args.output),
        title=args.title,
        phase_names_path=pathlib.Path(args.phase_names) if args.phase_names else None,
        save_endpoint=args.save_endpoint,
    )


if __name__ == "__main__":
    main()
