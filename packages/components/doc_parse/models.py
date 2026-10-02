"""Data model and ports for document parsing (stack-map U6, S4; spec R6/R7).

A parser turns untrusted bytes into a ``ParsedDocument`` of *inert* text. It never raises on
hostile input: problems become ``flags`` (``unsupported:*``, ``rejected:*``, ``error:*``,
``neutralised:*``). It never fetches links and never executes anything in the document.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

Table = tuple[tuple[str, ...], ...]  # rows of inert cell strings


@dataclass(frozen=True)
class ParserLimits:
    max_bytes: int = 10 * 1024 * 1024
    max_pages: int = 50  # PDF pages / spreadsheet sheets
    max_chars: int = 400_000  # output text (inert_text itself caps at 500k)
    max_rows: int = 20_000  # per table
    max_cols: int = 200
    max_cell_chars: int = 2_000
    max_parts: int = 100  # MIME parts / attachments inspected
    max_unzipped_bytes: int = 50 * 1024 * 1024  # xlsx zip-bomb guard
    max_xml_part_bytes: int = 20 * 1024 * 1024  # xlsx XML part above this is rejected, not skipped


@dataclass(frozen=True)
class SourceSpan:
    """``text[start:end]`` came from ``part`` of the source (e.g. ``body``, ``page:2``,
    ``sheet:Parts``, ``header:subject``). Used by the grounding check."""

    start: int
    end: int
    part: str
    page: int | None = None


@dataclass(frozen=True)
class ParsedDocument:
    text: str
    pages: tuple[str, ...] = ()
    tables: tuple[Table, ...] = ()
    source_offsets: tuple[SourceSpan, ...] = ()
    flags: tuple[str, ...] = ()
    filename: str = ""
    sha256: str = ""
    attachments: tuple[str, ...] = field(default=())  # inert listing only; never parsed here

    @property
    def usable(self) -> bool:
        """True when no flag says the content is missing or unreadable."""
        return not any(f.startswith(("unsupported:", "rejected:", "error:")) for f in self.flags)


@runtime_checkable
class DocumentParser(Protocol):
    def parse(
        self, content: bytes, *, filename: str, content_type: str | None = None
    ) -> ParsedDocument: ...


class SandboxedParserClient(Protocol):
    """Future client for the isolated parsing service (stack-map S4). NOT implemented here.

    Contract for implementations: the remote runner has no network egress, no credentials, runs
    per-document with CPU/memory/time limits and is destroyed afterwards; the client sends bytes
    and receives a plain dict. Whatever comes back is untrusted: pass it through
    ``sandbox_result_to_document`` before use.
    """

    def parse_in_sandbox(
        self, content: bytes, *, filename: str, content_type: str | None, limits: ParserLimits
    ) -> dict[str, object]: ...
