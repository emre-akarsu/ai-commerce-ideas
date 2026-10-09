#!/usr/bin/env python3
"""Builds the documentation portal (one HTML page plus the screenshots) from the repository's markdown.

    python3 build.py <git-ref-for-links>

Writes ./out/index.html and ./out/files.json (published path -> source path for the images).
Mermaid diagrams are the pre-rendered SVGs in ./svg (see render_portal.mjs); their colours are mapped to CSS
variables so they follow the viewer's theme.
"""
from __future__ import annotations

import html
import json
import pathlib
import re
import struct
import sys
import urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, "/tmp/claude-0/pylibs")
sys.path.insert(0, str(HERE))

from markdown_it import MarkdownIt  # noqa: E402
from markdown_it.token import Token  # noqa: E402
from registry import REGISTRY  # noqa: E402

REPO = pathlib.Path("/home/user/ai-commerce-ideas")
GH = "https://github.com/emre-akarsu/ai-commerce-ideas"
REF = sys.argv[1] if len(sys.argv) > 1 else "main"
BUILD_DATE = "2026-10-09"

BY_PATH = {path: (did, label, sec) for did, sec, label, path in REGISTRY}
BY_ID = {did: (sec, label, path) for did, sec, label, path in REGISTRY}
IMAGES: dict[str, str] = {}  # published path -> source path (relative to the repo)


# ----------------------------------------------------------------------------- helpers
def slug(text: str) -> str:
    h = re.sub(r"`", "", text)
    h = re.sub(r"<[^>]+>", "", h)
    h = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", h)
    h = h.strip().lower()
    return "".join("-" if ch == " " else ch for ch in h if ch.isalnum() or ch in "-_ ")


def png_size(path: pathlib.Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as f:
            head = f.read(24)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            w, h = struct.unpack(">II", head[16:24])
            return w, h
    except OSError:
        pass
    return None


def resolve(doc_path: str, target: str) -> str:
    """Repo-relative path of a link target written relative to the document."""
    base = pathlib.PurePosixPath(doc_path).parent
    parts: list[str] = []
    for seg in (base / target).parts:
        if seg == "..":
            if parts:
                parts.pop()
        elif seg != ".":
            parts.append(seg)
    return "/".join(parts)


# ----------------------------------------------------------------------------- svg theming
SVG_MAP = [
    # activity-diagram classes (human, rule, ai, optimisation, check, record)
    ("#ffe9b3", "var(--human-bg)"), ("#8a5a00", "var(--human-line)"), ("#2a1c00", "var(--human-ink)"),
    ("#eef0f2", "var(--rule-bg)"), ("#6b7280", "var(--rule-line)"), ("#111827", "var(--rule-ink)"),
    ("#e9e3ff", "var(--ai-bg)"), ("#5b3fc4", "var(--ai-line)"), ("#1e1050", "var(--ai-ink)"),
    ("#d8f3e4", "var(--opt-bg)"), ("#1b7a4a", "var(--opt-line)"), ("#0b2e1b", "var(--opt-ink)"),
    ("#fde3e1", "var(--gate-bg)"), ("#b02b2b", "var(--gate-line)"), ("#3a0d0d", "var(--gate-ink)"),
    ("#dbeafe", "var(--data-bg)"), ("#1d4ed8", "var(--data-line)"), ("#0b1f4d", "var(--data-ink)"),
    ("#374151", "var(--bar-line)"), ("#f6f3ff", "var(--sandbox-bg)"),
    # base theme of the system diagrams
    ("#e6edf7", "var(--mm-node)"), ("#5b7ba6", "var(--mm-line)"), ("#10203a", "var(--fg)"),
    ("#44546a", "var(--mm-edge)"), ("#f3e6c4", "var(--mm-alt)"), ("#a9822d", "var(--mm-alt-line)"),
    ("#f4f6f9", "var(--mm-cluster)"), ("#b7c0cc", "var(--mm-cluster-line)"), ("#d6e0f0", "var(--mm-activation)"),
    ("#7d8ba0", "var(--mm-actor-line)"), ("#edf2ae", "var(--mm-alt)"),
    ("#ffffff", "var(--surface)"), ("#000000", "var(--fg)"), ("#000", "var(--fg)"),
    ("#666", "var(--fg-muted)"), ("#eaeaea", "var(--mm-node)"), ("#999", "var(--mm-actor-line)"),
    ("#f5f5f5", "var(--mm-cluster)"), ("#e0e0e0", "var(--mm-cluster-line)"),
    ("rgba(255, 255, 255, 0.5)", "var(--mm-label-bg)"),
]


def themed_svg(svg: str, label: str) -> str:
    for old, new in SVG_MAP:
        svg = re.sub(re.escape(old) + r"(?![0-9a-fA-F])", new, svg, flags=re.I)
    svg = re.sub(r"(?<![\w-])gray(?![\w-])", "var(--mm-cluster-line)", svg)
    svg = re.sub(r"(?<![\w-])white(?![\w-])", "var(--surface)", svg)
    svg = re.sub(r"font-family:[^;}]*;", "font-family:var(--sans);", svg)
    svg = re.sub(r'font-family="[^"]*"', 'font-family="var(--sans)"', svg)
    svg = svg.replace(' role="graphics-document document"', ' role="img"', 1)
    svg = re.sub(r"<svg\b", "<svg", svg, count=1)
    # a text alternative: the nearest heading
    svg = re.sub(r"(<svg[^>]*>)", lambda m: m.group(1) + "<title>" + html.escape(label) + "</title>", svg, count=1)
    return svg


def svg_natural_width(svg: str) -> int:
    m = re.search(r'viewBox="[-\d.]+ [-\d.]+ ([\d.]+) ([\d.]+)"', svg)
    return int(float(m.group(1))) if m else 1000


def strip_svg_size(svg: str) -> str:
    def fix(m: re.Match) -> str:
        tag = m.group(0)
        tag = re.sub(r'\swidth="[^"]*"', "", tag, count=1)
        tag = re.sub(r'\sheight="[^"]*"', "", tag, count=1)
        tag = re.sub(r'\sstyle="[^"]*"', "", tag, count=1)
        return tag
    return re.sub(r"<svg\b[^>]*>", fix, svg, count=1)


# ----------------------------------------------------------------------------- markdown
def make_md() -> MarkdownIt:
    md = MarkdownIt("commonmark", {"html": False, "linkify": False, "typographer": False})
    md.enable("table").enable("strikethrough")
    return md


MD = make_md()


def render_doc(did: str, path: str) -> tuple[str, list[tuple[int, str, str]], str]:
    """Returns (html, toc entries [(level, id, text)], first heading text)."""
    src = (REPO / path).read_text()
    src = re.sub(r'^<a id="([^"]+)"></a>\s*$', r"\n@@ANCHOR:\1@@\n", src, flags=re.M)
    tokens = MD.parse(src)
    out: list[Token] = []
    toc: list[tuple[int, str, str]] = []
    seen: dict[str, int] = {}
    first_heading = ""
    diagram_no = 0
    last_heading = ""
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t.type == "heading_open":
            inline = tokens[i + 1]
            text = inline.content
            s = slug(text)
            n = seen.get(s, 0)
            seen[s] = n + 1
            hid = s if n == 0 else f"{s}-{n}"
            t.attrSet("id", hid)
            level = int(t.tag[1])
            plain = re.sub(r"[`*_]", "", text)
            last_heading = plain
            if not first_heading:
                first_heading = plain
            if level in (2, 3):
                toc.append((level, hid, plain))
        elif t.type == "fence" and t.info.strip() == "mermaid":
            diagram_no += 1
            key = f"{did}_{diagram_no}"
            svg_file = HERE / "svg" / f"{key}.svg"
            ht = Token("html_block", "", 0)
            if svg_file.exists():
                raw = svg_file.read_text()
                natural = svg_natural_width(raw)
                label = f"Diagram: {last_heading}" if last_heading else "Diagram"
                svg = strip_svg_size(themed_svg(raw, label))
                default_w = natural if natural <= 1100 else max(1100, int(natural * 0.62))
                ht.content = (
                    f'<figure class="diagram" style="--w:{natural}px;--dw:{default_w}px" data-w="{natural}">'
                    f'<div class="diagram-bar"><span class="diagram-cap">{html.escape(label)}</span>'
                    f'<span class="diagram-btns"><button type="button" class="dfit" aria-pressed="false">Fit to width</button>'
                    f'<button type="button" class="dfull" aria-pressed="false">Full size</button></span></div>'
                    f'<div class="diagram-scroll" tabindex="0" role="region" aria-label="{html.escape(label)} (scrollable)">{svg}</div></figure>\n'
                )
            else:
                ht.content = '<p class="missing">Diagram not available.</p>\n'
            out.append(ht)
            i += 1
            continue
        elif t.type == "fence":
            lang = t.info.strip().split()[0] if t.info.strip() else ""
            ht = Token("html_block", "", 0)
            ht.content = f'<pre class="code" tabindex="0"><code{(" data-lang=" + chr(34) + html.escape(lang) + chr(34)) if lang else ""}>{html.escape(t.content)}</code></pre>\n'
            out.append(ht)
            i += 1
            continue
        elif t.type == "table_open":
            w = Token("html_block", "", 0)
            w.content = '<div class="tablewrap" tabindex="0" role="region" aria-label="Table (scrollable)">'
            out.append(w)
        elif t.type == "table_close":
            out.append(t)
            w = Token("html_block", "", 0)
            w.content = "</div>\n"
            out.append(w)
            i += 1
            continue
        elif t.type == "inline" and t.children:
            for c in t.children:
                if c.type == "link_open":
                    rewrite_link(c, did, path)
                elif c.type == "image":
                    rewrite_image(c, path)
        out.append(t)
        i += 1
    body = MD.renderer.render(out, MD.options, {})
    body = re.sub(r"<p>@@ANCHOR:([^@]+)@@</p>", r'<span id="\1" class="anchor-target"></span>', body)
    body = re.sub(
        r'(<h([1-6]) id="([^"]+)">)(.*?)(</h\2>)',
        lambda m: f'{m.group(1)}{m.group(4)}<a class="permalink" href="#{did}~{m.group(3)}" data-doc="{did}" data-anchor="{m.group(3)}" aria-label="Link to this section">#</a>{m.group(5)}',
        body, flags=re.S)
    return body, toc, first_heading


def rewrite_link(tok: Token, did: str, path: str) -> None:
    href = tok.attrGet("href") or ""
    if re.match(r"^(https?:|mailto:|tel:)", href):
        tok.attrSet("target", "_blank")
        tok.attrSet("rel", "noopener noreferrer")
        tok.attrSet("class", "external")
        return
    href = urllib.parse.unquote(href)
    target, _, frag = href.partition("#")
    if target == "":
        tok.attrSet("href", f"#{did}~{frag}" if frag else f"#{did}")
        tok.attrSet("data-doc", did)
        if frag:
            tok.attrSet("data-anchor", frag)
        return
    resolved = resolve(path, target)
    if resolved in BY_PATH:
        dest = BY_PATH[resolved][0]
        tok.attrSet("href", f"#{dest}~{frag}" if frag else f"#{dest}")
        tok.attrSet("data-doc", dest)
        if frag:
            tok.attrSet("data-anchor", frag)
        return
    # a file or folder of the repository that the portal does not carry: link to it in the repository
    p = REPO / resolved
    kind = "tree" if p.is_dir() else "blob"
    tok.attrSet("href", f"{GH}/{kind}/{REF}/{urllib.parse.quote(resolved)}{('#' + frag) if frag else ''}")
    tok.attrSet("target", "_blank")
    tok.attrSet("rel", "noopener noreferrer")
    tok.attrSet("class", "external repo")


def rewrite_image(tok: Token, path: str) -> None:
    src = urllib.parse.unquote(tok.attrGet("src") or "")
    resolved = resolve(path, src)
    src_file = REPO / resolved
    name = "img/" + pathlib.PurePosixPath(resolved).name
    if src_file.exists():
        IMAGES[name] = resolved
        tok.attrSet("src", name)
        size = png_size(src_file)
        if size:
            tok.attrSet("width", str(size[0]))
            tok.attrSet("height", str(size[1]))
    tok.attrSet("loading", "lazy")
    tok.attrSet("decoding", "async")


# ----------------------------------------------------------------------------- page
CSS = (HERE / "portal.css").read_text()
JS = (HERE / "portal.js").read_text()


def build() -> None:
    docs_html: list[str] = []
    meta: dict[str, dict] = {}
    for did, sec, label, path in REGISTRY:
        body, toc, h1 = render_doc(did, path)
        meta[did] = {"label": label, "section": sec, "path": path, "toc": toc, "title": h1}
        docs_html.append(f'<template id="t-{did}"><article class="doc" data-doc="{did}">{body}</article></template>')

    nav: list[str] = []
    cur = None
    for did, sec, label, path in REGISTRY:
        if sec != cur:
            if cur is not None:
                nav.append("</ul></section>")
            nav.append(f'<section class="navsec"><h2>{html.escape(sec)}</h2><ul>')
            cur = sec
        nav.append(f'<li><a href="#{did}" data-doc="{did}">{html.escape(label)}</a></li>')
    nav.append("</ul></section>")

    order = [d for d, *_ in REGISTRY]
    boot = json.dumps({"order": order, "meta": {k: {"label": v["label"], "section": v["section"], "path": v["path"]} for k, v in meta.items()}, "gh": f"{GH}/blob/{REF}/", "ref": REF})

    page = f"""<title>Buy-side RFQ Docs</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=JetBrains+Mono:wght@400;500&family=Source+Sans+3:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap">
<style>
{CSS}
</style>
<a class="skip" href="#ui-doc">Skip to the document</a>
<div class="shell">
  <header class="top">
    <button type="button" class="menu" id="ui-menu" aria-controls="ui-side" aria-expanded="false">Menu</button>
    <a class="brand" href="#hub" data-doc="hub"><span class="brand-mark" aria-hidden="true"></span><span class="brand-text">Buy-side RFQ Docs</span></a>
    <div class="search">
      <label class="sr" for="ui-q">Search the documentation</label>
      <input id="ui-q" type="search" placeholder="Search the documentation" autocomplete="off" spellcheck="false">
    </div>
  </header>
  <div class="body">
    <nav id="ui-side" class="side" aria-label="Documentation">
      {"".join(nav)}
      <p class="fine">Built {BUILD_DATE} from the repository's markdown (<a class="external" target="_blank" rel="noopener noreferrer" href="{GH}/tree/{REF}/docs">docs/</a>, ref <code>{html.escape(REF[:12])}</code>). The markdown in the repository is the source of truth. Product-market fit is unproven; all data is synthetic.</p>
    </nav>
    <main id="ui-main" class="main">
      <div id="ui-results" class="results" hidden></div>
      <div class="content-row">
        <div id="ui-doc" class="docwrap" tabindex="-1"></div>
        <aside id="ui-toc" class="toc" aria-label="On this page"></aside>
      </div>
      <nav id="ui-pager" class="pager" aria-label="Previous and next page"></nav>
    </main>
  </div>
</div>
{"".join(docs_html)}
<script id="ui-boot" type="application/json">{boot}</script>
<script>
{JS}
</script>
"""
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    (out / "index.html").write_text(page)
    (out / "files.json").write_text(json.dumps(IMAGES, indent=1))
    print("pages", len(REGISTRY), "html bytes", len(page.encode()), "images", len(IMAGES))


if __name__ == "__main__":
    build()
