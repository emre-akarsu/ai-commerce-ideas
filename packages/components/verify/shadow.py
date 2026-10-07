"""Shadow diff: compare two independent readings of the same quote on the critical fields.

`a` is the deterministic regex reading and `b` the model reading. The output is findings only:
nothing here picks a reading or returns a merged value. Pure and deterministic.

Each field is compared by its kind (see `_KIND`):
- money: `parse_money`; amounts must be equal, and currency tokens equal when both are present.
- lead time, validity: the days read by `parse_lead_time_days` / `parse_validity_days`.
- unit of measure: `parse_uom_divisor`; the text itself when the parser returns None.
- part number: upper case with whitespace removed.
- anything else: case-insensitive text with whitespace collapsed.

A blank reading counts as missing, and so does a value its parser cannot read while the other
reading can (`reading_missing`). Two readable values that differ give `readings_disagree`.
Values reach findings only through `Finding.of`, which hides anything that is not plain text.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import TypeAlias

from components.core.domain import ExtractedQuote
from components.rfq.quotes.normalise import (
    Money,
    parse_lead_time_days,
    parse_money,
    parse_uom_divisor,
    parse_validity_days,
)
from components.verify.findings import Finding

__all__ = ["CRITICAL_FIELDS", "diff_readings"]

# Every ExtractedQuote string field is decision-critical: none is free text or a snippet.
CRITICAL_FIELDS: tuple[str, ...] = (
    "unit_price",
    "currency",
    "uom",
    "quantity_available",
    "moq",
    "lead_time",
    "freight",
    "validity",
    "offered_mpn",
    "condition",
    "authenticity_claim",
    "tax_text",
)


class _Kind(StrEnum):
    MONEY = "money"
    LEAD_TIME = "lead_time"
    VALIDITY = "validity"
    UOM = "uom"
    PART = "part"
    TEXT = "text"


_KIND: Mapping[str, _Kind] = {
    "unit_price": _Kind.MONEY,
    "freight": _Kind.MONEY,
    "lead_time": _Kind.LEAD_TIME,
    "validity": _Kind.VALIDITY,
    "uom": _Kind.UOM,
    "offered_mpn": _Kind.PART,
    "currency": _Kind.TEXT,
    "quantity_available": _Kind.TEXT,
    "moq": _Kind.TEXT,
    "condition": _Kind.TEXT,
    "authenticity_claim": _Kind.TEXT,
    "tax_text": _Kind.TEXT,
}

# A normalised reading: equal values agree. `None` from a parser means it could not read the text.
_Value: TypeAlias = Money | int | str


def diff_readings(a: ExtractedQuote, b: ExtractedQuote) -> tuple[Finding, ...]:
    """Findings for the critical fields where the readings disagree or only one has a value."""
    found = (_diff_field(name, _text(a, name), _text(b, name)) for name in CRITICAL_FIELDS)
    return tuple(sorted((f for f in found if f is not None), key=_order))


def _order(finding: Finding) -> tuple[str, str]:
    return finding.field, finding.code


def _text(reading: ExtractedQuote, name: str) -> str | None:
    value: str | None = getattr(reading, name)
    return value


def _present(raw: str | None) -> str | None:
    return raw if raw is not None and raw.strip() else None


def _diff_field(name: str, a_raw: str | None, b_raw: str | None) -> Finding | None:
    a, b = _present(a_raw), _present(b_raw)
    if a is None:
        return None if b is None else _missing(name, b)
    if b is None:
        return _missing(name, a)
    return _compare(name, _KIND[name], a, b)


def _compare(name: str, kind: _Kind, a: str, b: str) -> Finding | None:
    a_val, b_val = _read(kind, a), _read(kind, b)
    if a_val is None and b_val is None:
        same = _squash(a) == _squash(b)  # neither parser reads it: compare the text itself
    elif a_val is None or b_val is None:
        return _missing(name, b if a_val is None else a)  # one unreadable counts as blank
    else:
        same = _same(a_val, b_val)
    return None if same else _disagree(name, a, b)


def _read(kind: _Kind, text: str) -> _Value | None:
    """What the parser for `kind` reads from `text`, or None when it cannot read it."""
    if kind is _Kind.MONEY:
        return parse_money(text)
    if kind is _Kind.LEAD_TIME:
        return parse_lead_time_days(text)[0]
    if kind is _Kind.VALIDITY:
        return parse_validity_days(text)[0]
    if kind is _Kind.UOM:
        divisor = parse_uom_divisor(text)
        return _squash(text) if divisor is None else divisor
    if kind is _Kind.PART:
        return "".join(text.split()).upper()
    return _squash(text)


def _same(a: _Value, b: _Value) -> bool:
    if isinstance(a, Money) and isinstance(b, Money):
        return _same_money(a, b)
    return a == b


def _same_money(a: Money, b: Money) -> bool:
    if a.amount != b.amount:
        return False
    if a.currency_token is None or b.currency_token is None:
        return True  # a missing token is compatible; the amounts already agree
    return a.currency_token.casefold() == b.currency_token.casefold()


def _squash(text: str) -> str:
    """Case-insensitive text with runs of whitespace collapsed."""
    return " ".join(text.split()).casefold()


def _missing(name: str, text: str) -> Finding:
    return Finding.of("reading_missing", name, name=name, first=text)


def _disagree(name: str, a: str, b: str) -> Finding:
    return Finding.of("readings_disagree", name, name=name, first=a, other=b)
