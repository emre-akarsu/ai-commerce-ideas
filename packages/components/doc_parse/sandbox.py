"""Validation of results coming back from a sandboxed parser (stack-map S4). No network here."""

from __future__ import annotations

from collections.abc import Mapping

from components.rfq.quotes.inert import inert_text

from .models import ParsedDocument, ParserLimits


def sandbox_result_to_document(raw: Mapping[str, object], limits: ParserLimits) -> ParsedDocument:
    """Treat a sandbox reply as untrusted: re-inert all text, cap sizes, keep only known fields."""
    text = inert_text(str(raw.get("text", ""))[: limits.max_chars])
    pages_raw = raw.get("pages", ())
    pages = tuple(
        inert_text(str(p)[: limits.max_chars]) for p in list(pages_raw)[: limits.max_pages]
    ) if isinstance(pages_raw, list | tuple) else ()
    flags_raw = raw.get("flags", ())
    flags = tuple(
        f"sandbox:{inert_text(str(f))[:80]}" for f in list(flags_raw)[:50]
    ) if isinstance(flags_raw, list | tuple) else ()
    return ParsedDocument(
        text=text,
        pages=pages,
        flags=(*flags, "parsed_in_sandbox"),
        filename=inert_text(str(raw.get("filename", "")))[:255],
        sha256=str(raw.get("sha256", ""))[:64],
    )
