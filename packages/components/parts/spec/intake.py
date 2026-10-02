"""Deterministic parsing of the free-text parts of a request (F1): quantity, need-by, urgency.

Regex only, no LLM. The text is untrusted (R6): phrases that look like instructions to an AI are
*flagged* in ``raw_instruction_flags`` for the reviewer, but flags never change any parsed field or
any behaviour. The criticality hint can only raise caution (it forces Tier D downstream); no text
can lower it.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

from pydantic import BaseModel, ConfigDict

_WEEKDAYS = {
    "monday": 0, "mon": 0,
    "tuesday": 1, "tue": 1, "tues": 1,
    "wednesday": 2, "wed": 2,
    "thursday": 3, "thu": 3, "thur": 3, "thurs": 3,
    "friday": 4, "fri": 4,
    "saturday": 5, "sat": 5,
    "sunday": 6, "sun": 6,
}  # fmt: skip

_QTY_PATTERNS = (
    re.compile(r"\b(?:qty|quantity)\.?\s*[:=]?\s*(\d{1,6})\b", re.IGNORECASE),
    re.compile(r"\b(\d{1,6})\s*(?:pcs?|pieces?|ea|each|units?|off)\b", re.IGNORECASE),
    # "x10" only when glued to the number and not part of a dimension like 25x52x15
    re.compile(r"(?<![\w.])x(\d{1,6})\b(?!\s*(?:x|mm))", re.IGNORECASE),
)

_DATE_LEAD = r"(?:need(?:ed)?\s+by|required\s+by|due(?:\s+by)?|no\s+later\s+than|by)"
_WEEKDAY_RE = re.compile(
    rf"\b{_DATE_LEAD}\s+({'|'.join(sorted(_WEEKDAYS, key=len, reverse=True))})\b", re.IGNORECASE
)
_RELATIVE_RE = re.compile(rf"\b{_DATE_LEAD}\s+(today|tomorrow)\b", re.IGNORECASE)
_ISO_DATE_RE = re.compile(rf"\b{_DATE_LEAD}\s+(\d{{4}})-(\d{{2}})-(\d{{2}})\b", re.IGNORECASE)

_DOWN_NOW_RE = re.compile(
    r"\basap\b|\bdown\s+now\b"
    r"|\b(?:line|machine|production|plant|press|conveyor|pump)\s+(?:is\s+)?down\b",
    re.IGNORECASE,
)
_CRITICAL_RE = re.compile(
    r"\b(?:safety|critical(?:ity)?|hoist|crane|lifting|elevator|regulated|atex|explosion)\b",
    re.IGNORECASE,
)

_INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (name, re.compile(pattern, re.IGNORECASE))
    for name, pattern in (
        ("ignore previous", r"\bignore\s+(?:all\s+|any\s+)?(?:previous|prior|above)\b"),
        ("disregard", r"\bdisregard\s+(?:all\s+|any\s+)?(?:previous|prior|above|the)\b"),
        ("system prompt", r"\bsystem\s+prompt\b"),
        ("send po", r"\bsend\s+(?:the\s+|a\s+)?po\b"),
        ("place order", r"\bplace\s+(?:the\s+|an\s+)?order\b"),
        ("you are now", r"\byou\s+are\s+now\b"),
        ("new instructions", r"\bnew\s+instructions\b"),
        ("approve", r"\b(?:auto[- ]?)?approve\s+(?:this|it|the|all)\b"),
    )
)


class ParsedRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    quantity: int | None = None
    need_by: date | None = None
    down_now: bool = False
    criticality_hint: bool = False  # hint only: a human sets Request.criticality
    raw_instruction_flags: tuple[str, ...] = ()  # informational; never changes behaviour


def _parse_quantity(text: str) -> int | None:
    values: set[int] = set()
    for pattern in _QTY_PATTERNS:
        for m in pattern.finditer(text):
            n = int(m.group(1))
            if n > 0:
                values.add(n)
    # conflicting quantities are never guessed
    return next(iter(values)) if len(values) == 1 else None


def _next_weekday_after(today: date, weekday: int) -> date:
    delta = (weekday - today.weekday()) % 7 or 7  # strictly after today
    return today + timedelta(days=delta)


def _parse_need_by(text: str, today: date) -> date | None:
    found: list[date] = []
    for m in _WEEKDAY_RE.finditer(text):
        found.append(_next_weekday_after(today, _WEEKDAYS[m.group(1).lower()]))
    for m in _RELATIVE_RE.finditer(text):
        found.append(today if m.group(1).lower() == "today" else today + timedelta(days=1))
    for m in _ISO_DATE_RE.finditer(text):
        try:
            found.append(date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
        except ValueError:
            continue  # impossible dates are ignored, not repaired
    return min(found) if found else None  # several dates: the earliest is the safe reading


def injection_flags(text: str) -> tuple[str, ...]:
    return tuple(name for name, pattern in _INJECTION_PATTERNS if pattern.search(text))


def parse_request_text(text: str, today: date) -> ParsedRequest:
    return ParsedRequest(
        quantity=_parse_quantity(text),
        need_by=_parse_need_by(text, today),
        down_now=bool(_DOWN_NOW_RE.search(text)),
        criticality_hint=bool(_CRITICAL_RE.search(text)),
        raw_instruction_flags=injection_flags(text),
    )
