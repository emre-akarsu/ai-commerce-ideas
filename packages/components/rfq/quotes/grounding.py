"""Deterministic grounding check for the quarantined extractor (ADR-004, spec R6).

Every non-None field of an `ExtractedQuote` must appear verbatim in the source text after
whitespace and thousands-separator normalisation. Ungrounded fields become None and are flagged
`ungrounded:<field>`. For each grounded field the matching source text is returned as a snippet
(shown beside the value to the buyer).

The comparison is made against `inert_text(source)`: the text a human can actually see, with
hidden/zero-width/HTML-comment/CSS-hidden content and links already removed. A value that exists
only in hidden text therefore cannot be grounded.

Instruction-like phrases in the source additionally raise the `injection_suspected` flag. The
flag never changes what is extracted, blanked or shown; downstream code (comparison) decides what
a flagged quote may do.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict

from components.core.domain import ExtractedQuote

from .inert import fold_text, inert_text, reveal_text

__all__ = [
    "INJECTION_FLAG",
    "GroundingResult",
    "detect_injection",
    "ground",
    "normalise_for_match",
    "ungrounded_flag",
]

INJECTION_FLAG = "injection_suspected"


def ungrounded_flag(field: str) -> str:
    return f"ungrounded:{field}"


class GroundingResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    extracted: ExtractedQuote
    flags: tuple[str, ...] = ()
    snippets: dict[str, str] = {}


# ------------------------------------------------------------------ normalisation


_DIGITS = frozenset("0123456789")


def _digit_run_before(text: str, i: int) -> int:
    n = 0
    j = i - 1
    while j >= 0 and text[j] in _DIGITS and n < 5:
        n += 1
        j -= 1
    return n


def _is_thousands_comma(text: str, i: int) -> bool:
    """text[i] is a comma between a 1-3 digit group and exactly three digits."""
    if text[i] != "," or i == 0 or text[i - 1] not in _DIGITS:
        return False
    if not (1 <= _digit_run_before(text, i) <= 3):
        return False
    tail = text[i + 1 : i + 5]
    return (
        len(tail) >= 3
        and all(c in _DIGITS for c in tail[:3])
        and not (len(tail) == 4 and tail[3] in _DIGITS)
    )


def _norm_with_map(text: str) -> tuple[str, list[int]]:
    """Collapse whitespace to single spaces and drop thousands commas; return the normalised
    string and, for each of its characters, the index of the originating character."""
    chars: list[str] = []
    idx: list[int] = []
    for i, ch in enumerate(text):
        if ch.isspace():
            if chars and chars[-1] != " ":
                chars.append(" ")
                idx.append(i)
            continue
        if ch == "," and _is_thousands_comma(text, i):
            continue
        chars.append(ch)
        idx.append(i)
    while chars and chars[-1] == " ":
        chars.pop()
        idx.pop()
    return "".join(chars), idx


def normalise_for_match(text: str) -> str:
    """Whitespace-collapsed, thousands-separator-free form used by the grounding comparison."""
    return _norm_with_map(text)[0]


_STRICT_FIELDS = frozenset({"offered_mpn"})


def _boundary_pattern(value: str, *, strict: bool) -> re.Pattern[str]:
    """Match `value` as a whole token: it may not be a fragment of a longer word or number.
    `strict` (identifiers such as part numbers) also refuses to match when a joiner continues
    the token, so "6205-2RS1" is not grounded by "6205-2RS1/C3" and "6205" not by "6205-2RS1"."""
    pre = ""
    post = ""
    first, last = value[0], value[-1]
    if first.isalnum():
        pre += r"(?<!\w)"
        if strict:
            pre += r"(?<!\w[-/+.])"
    if first.isdigit():
        pre += r"(?<![0-9][.,])"
    if last.isalnum():
        post += r"(?!\w)"
        if strict:
            post += r"(?![-/+.]\w)"
    if last.isdigit():
        post += r"(?![.,][0-9])"
    return re.compile(pre + re.escape(value) + post)


# ------------------------------------------------------------------ injection detection

_INJECTION_RES = tuple(
    re.compile(p)
    for p in (
        r"\b(?:ignore|disregard|forget|override)\s+(?:(?:all|any|the|your|my|these|those)\s+)*"
        r"(?:previous|prior|above|earlier|preceding|former)\s+"
        r"(?:instructions?|prompts?|rules?|messages?|directions?|context)\b",
        r"\b(?:ignore|disregard|forget)\s+(?:(?:all|any|the|your|these|those)\s+)*"
        r"(?:instructions?|rules|guidelines|system\s+prompt)\b",
        r"\bsystem\s+(?:prompt|message|instruction)s?\b",
        r"\bdeveloper\s+(?:message|mode|instruction)s?\b",
        r"\bnew\s+instructions?\s*:",
        r"\byou\s+are\s+now\s+(?:the|a|an|my)\b",
        r"\bsend\s+(?:(?:the|a|this|that|any)\s+)?(?:po|p\.o\.|purchase\s+order)\b",
        r"\bwire\s+(?:transfer|funds?|payments?|money|instructions?|\$|usd|eur|\d)",
        r"\bwire\s+(?:the|this|that|your)\s+(?:money|funds?|payments?|amount)\b",
        r"\bwiring\s+(?:instructions?|details)\b",
        r"\bbank\s+(?:account\s+)?(?:details?|info(?:rmation)?|number|account)\s+"
        r"(?:(?:have|has|had|is|are|was|were)\s+)?(?:been\s+)?(?:chang|updat|new)",
        r"\b(?:new|changed|updated|different)\s+(?:bank(?:ing)?|remit(?:tance)?(?:[- ]to)?)\s+"
        r"(?:account\s+)?(?:details?|info(?:rmation)?|instructions?|account|number)\b",
        r"\bchange\s+(?:of|in|to)\s+(?:our\s+|the\s+|your\s+)?(?:bank|banking|remit)",
    )
)


def detect_injection(text: str) -> bool:
    """True if the text (including content hidden from a human reader) contains instruction-like
    phrases aimed at an AI assistant or a payment redirect. Detection only: it never changes
    what is extracted."""
    folded = fold_text(reveal_text(text))
    return any(p.search(folded) for p in _INJECTION_RES)


# ------------------------------------------------------------------ grounding


def _ground_value(
    field: str, value: str, haystack: str, hay_idx: list[int], raw: str
) -> str | None:
    needle, _ = _norm_with_map(value)
    if not needle:
        return None
    m = _boundary_pattern(needle, strict=field in _STRICT_FIELDS).search(haystack)
    if m is None:
        return None
    return raw[hay_idx[m.start()] : hay_idx[m.end() - 1] + 1]


def ground(extracted: ExtractedQuote, source_text: str) -> GroundingResult:
    """Apply the ADR-004 grounding check. See the module docstring."""
    inert = inert_text(source_text)
    haystack, hay_idx = _norm_with_map(inert)
    updates: dict[str, str | None] = {}
    flags: list[str] = []
    snippets: dict[str, str] = {}
    for field in ExtractedQuote.model_fields:
        value = getattr(extracted, field)
        if value is None:
            continue
        value = value.strip()
        if not value:
            updates[field] = None
            continue
        snippet = _ground_value(field, value, haystack, hay_idx, inert)
        if snippet is None:
            updates[field] = None
            flags.append(ungrounded_flag(field))
        else:
            updates[field] = value
            snippets[field] = snippet
    if detect_injection(source_text):
        flags.append(INJECTION_FLAG)
    return GroundingResult(
        extracted=extracted.model_copy(update=updates), flags=tuple(flags), snippets=snippets
    )


def dedupe(flags: Iterable[str]) -> tuple[str, ...]:
    """Order-preserving de-duplication (shared by the normaliser)."""
    return tuple(dict.fromkeys(flags))
