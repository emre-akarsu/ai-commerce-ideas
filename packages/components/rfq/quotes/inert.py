"""Inert rendering of untrusted vendor text (spec R6 "inert rendering", R7 "no link fetching").

`inert_text` turns arbitrary vendor text into plain text that carries no active or hidden
content: zero-width / bidi / control characters are removed, HTML (tags, comments, scripts,
CSS-hidden elements) is removed, and every URL is replaced with a marker. Nothing here ever
fetches anything. The result is plain text: a renderer must still HTML-escape it.

Everything the quarantined extractor sees, everything the grounding check compares against and
every snippet shown to a human goes through this function, so "what the model read" equals
"what the buyer sees".
"""

from __future__ import annotations

import html
import re
import unicodedata

__all__ = ["LINK_REMOVED", "fold_text", "inert_text", "reveal_text"]

LINK_REMOVED = "[link removed]"

MAX_CHARS = 500_000  # hard cap on input size; quote emails are tiny, this bounds work
_MAX_PASSES = 8
_MAX_STACK = 10_000

# ------------------------------------------------------------------ invisible characters

_EXTRA_INVISIBLE = frozenset(
    chr(c) for c in (0x034F, 0x115F, 0x1160, 0x17B4, 0x17B5, 0x2800, 0x3164, 0xFFA0)
)
_NEWLINE_LIKE = {"\r": "\n", "\x85": "\n", " ": "\n", " ": "\n"}
_SPACE_LIKE = {"\t": " ", "\x0b": " ", "\x0c": " "}


def _is_invisible(ch: str) -> bool:
    cat = unicodedata.category(ch)
    if cat in ("Cf", "Cs", "Co"):
        return True
    if cat == "Cc":
        return ch != "\n"
    code = ord(ch)
    return (
        ch in _EXTRA_INVISIBLE
        or 0xFE00 <= code <= 0xFE0F  # variation selectors
        or 0x180B <= code <= 0x180D
        or 0xE0100 <= code <= 0xE01EF  # variation selectors supplement
    )


def _strip_invisible(s: str) -> str:
    out: list[str] = []
    prev = ""
    for ch in s:
        if ch == "\n" and prev == "\r":  # CRLF -> single newline
            prev = ch
            continue
        prev = ch
        ch = _NEWLINE_LIKE.get(ch, ch)
        ch = _SPACE_LIKE.get(ch, ch)
        if not _is_invisible(ch):
            out.append(ch)
    return "".join(out)


# ------------------------------------------------------------------ html

_COMMENT_RE = re.compile(r"<!--.*?(?:-->|\Z)", re.S)
_DECL_RE = re.compile(r"<[!?][^>]*(?:>|\Z)", re.S)
_RAW_BLOCK_RE = re.compile(
    r"<(script|style|template|noscript|iframe|object|embed|svg|math|head|title)\b[^>]*"
    r"(?:>.*?(?:</\1\s*>|\Z)|\Z)",
    re.S | re.I,
)
# A tag start is "<" + letter or "</" + letter. "<5 days" and "<sam@vendor.example>" are text.
_TAG_RE = re.compile(
    r"<(?![^\s<>@]+@[^\s<>]+>)(/?)([A-Za-z][A-Za-z0-9:_-]*)"
    r"((?:\"[^\"]*\"|'[^']*'|[^>])*+)(?:>|\Z)",
    re.S,
)
_VOID = frozenset(
    "area base br col embed hr img input link meta param source track wbr".split()
)
_BLOCK = frozenset(
    "address article aside blockquote br dd div dl dt fieldset figure footer form h1 h2 h3 h4 h5 "
    "h6 header hr li main nav ol p pre section table tbody tfoot thead tr ul".split()
)
_CELL = frozenset({"td", "th"})
_HIDDEN_STYLE_RE = re.compile(
    r"display\s*:\s*none"
    r"|visibility\s*:\s*(?:hidden|collapse)"
    r"|font-size\s*:\s*0(?:\.0+)?\s*(?:px|pt|em|rem|%)?\s*(?:;|!|\Z|[\"'])"
    r"|opacity\s*:\s*0(?:\.0+)?\s*(?:;|!|\Z|[\"'])"
    r"|mso-hide\s*:\s*all"
    r"|text-indent\s*:\s*-\s*\d{3,}"
    r"|(?:left|top)\s*:\s*-\s*\d{3,}"
    r"|(?:max-)?(?:height|width)\s*:\s*0(?:px|pt|em|rem|%)?\s*(?:;|!|\Z|[\"'])",
    re.I,
)
_HIDDEN_ATTR_RE = re.compile(r"(?:^|\s)hidden(?=\s|=|/|\Z)|aria-hidden\s*=\s*[\"']?true", re.I)


def _is_hidden(attrs: str) -> bool:
    return bool(_HIDDEN_ATTR_RE.search(attrs) or _HIDDEN_STYLE_RE.search(attrs))


def _strip_html(s: str, *, reveal: bool) -> str:
    """Remove markup. With reveal=False hidden content (comments, scripts, CSS-hidden elements)
    is dropped; with reveal=True it is kept (used only for injection *detection*)."""
    if reveal:
        s = s.replace("<!--", " ").replace("-->", " ")
    else:
        s = _COMMENT_RE.sub("", s)
        s = _RAW_BLOCK_RE.sub("", s)
    s = _DECL_RE.sub("", s)
    out: list[str] = []
    stack: list[tuple[str, bool]] = []
    counts: dict[str, int] = {}
    hidden = 0
    pos = 0
    for m in _TAG_RE.finditer(s):
        if hidden == 0 or reveal:
            out.append(s[pos : m.start()])
        pos = m.end()
        closing, name, attrs = m.group(1), m.group(2).lower(), m.group(3)
        if closing:
            if counts.get(name, 0) > 0:
                while stack:
                    top, was_hidden = stack.pop()
                    counts[top] -= 1
                    hidden -= was_hidden
                    if top == name:
                        break
        elif name not in _VOID and not attrs.rstrip().endswith("/") and len(stack) < _MAX_STACK:
            is_hidden = (not reveal) and _is_hidden(attrs)
            stack.append((name, is_hidden))
            counts[name] = counts.get(name, 0) + 1
            hidden += is_hidden
        if hidden == 0 or reveal:
            if name in _BLOCK:
                out.append("\n")
            elif name in _CELL:
                out.append(" ")
    if hidden == 0 or reveal:
        out.append(s[pos:])
    return "".join(out)


# ------------------------------------------------------------------ urls

_URL_TOKEN_RE = re.compile(r"(?<!\S)\S*?://\S*")
_PSEUDO_URL_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:javascript|vbscript)\s*:\S*"
    r"|(?<![A-Za-z0-9])mailto:\S*"
    r"|(?<![A-Za-z0-9])data:[A-Za-z]+/[A-Za-z0-9.+-]+[;,]\S*"
    r"|(?<![A-Za-z0-9@.])www\.\S+",
    re.I,
)


def _defang_urls(s: str) -> str:
    s = _URL_TOKEN_RE.sub(LINK_REMOVED, s)
    return _PSEUDO_URL_RE.sub(LINK_REMOVED, s)


# ------------------------------------------------------------------ whitespace


def _tidy(s: str) -> str:
    s = re.sub(r"[ ]{2,}", " ", s)
    s = re.sub(r" ?\n ?", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


# ------------------------------------------------------------------ public API


def _once(s: str, *, reveal: bool) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = _strip_invisible(s)
    s = html.unescape(s)
    s = _strip_html(s, reveal=reveal)
    if not reveal:
        s = _defang_urls(s)
    return _tidy(s)


def _sanitise(s: str, *, reveal: bool) -> str:
    s = s[:MAX_CHARS]
    for _ in range(_MAX_PASSES):
        nxt = _once(s, reveal=reveal)
        if nxt == s:
            return s
        s = nxt
    # Adversarial nesting did not converge: drop the characters that could form markup.
    s = re.sub(r"[<>&]", " ", s)
    return _tidy(_defang_urls(_strip_invisible(s))) if not reveal else _tidy(s)


def inert_text(s: str) -> str:
    """Return `s` as inert plain text (idempotent): no invisible/control/bidi characters, no HTML
    (tags, comments, scripts, CSS-hidden content), no URLs (replaced by `[link removed]`)."""
    return _sanitise(s, reveal=False)


def reveal_text(s: str) -> str:
    """Like `inert_text` but keeps hidden content and URLs. For injection DETECTION only; never
    feed this to a model or render it."""
    return _sanitise(s, reveal=True)


def fold_text(s: str) -> str:
    """Case-folded, whitespace-collapsed, invisible-free form used for phrase matching."""
    s = unicodedata.normalize("NFKC", s)
    s = _strip_invisible(s)
    return re.sub(r"\s+", " ", s).strip().casefold()
