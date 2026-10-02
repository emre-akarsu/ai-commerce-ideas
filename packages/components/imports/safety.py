"""Formula-injection and echo safety for imported cell values (spec R6, OWASP CSV injection)."""

from __future__ import annotations

from components.rfq.quotes.inert import inert_text

_TRIGGERS = ("=", "+", "-", "@", "\t", "\r", "\n")
ECHO_MAX = 80


def neutralise(value: str) -> str:
    """Prefix an apostrophe when a spreadsheet would read the value as a formula.

    Leading whitespace/control characters are looked through, because Excel ignores them."""
    stripped = value.lstrip(" \t\r\n\x00\x0b\x0c ")
    if value.startswith(_TRIGGERS) or stripped.startswith(_TRIGGERS):
        return "'" + value
    return value


def clean_text(value: str, *, limit: int = 500) -> str:
    """Untrusted free text: inert (no html/links/invisible chars), single line, formula-safe."""
    one_line = " ".join(inert_text(value[: limit * 4]).split())[:limit]
    return neutralise(one_line)


def echo(value: object) -> str:
    """The only way a raw input value may appear in an error entry."""
    return neutralise(" ".join(inert_text(str(value)[:400]).split())[:ECHO_MAX])
