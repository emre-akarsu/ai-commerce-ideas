"""Deterministic number checks on quote lines (verification layer, item 9.1 of the v0.3 triage).

The checks read a `QuoteLineFacts` (what the quote says about one line) and return `Finding`s. A
finding only sends a line to review or raises a flag: nothing here approves a line, picks between
two readings, fills a blank or changes an amount (hard rules R5 and R6).

Money is Decimal only. A float, int, bool or non-finite value is refused when the facts are built.
Arithmetic is exact to 400 significant digits, so the only rounding that matters is the tolerance
in `VerifyConfig`. A number shown in a finding is plain text: at most 4 decimal places, half-up, no
trailing zeros, no exponent.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, fields
from datetime import date, datetime
from decimal import MAX_EMAX, MIN_EMIN, ROUND_HALF_UP, Context, Decimal

from components.verify.config import VerifyConfig
from components.verify.findings import NOT_SHOWN, VALUE_MAX, Finding

# Sanity bound on one quoted number (a price, quantity, count or total). It is far above any real
# line, so a larger value is almost always a slipped decimal point or a pasted digit run. This is a
# code bound, not policy: it is not read from the profile and it never gates an approval.
ABSURD_MAX = Decimal("1000000000")

# Exact arithmetic for add, subtract and multiply, to a fixed 400 significant digits: far beyond any
# quoted number. The bound matters: with an unbounded precision, 1E+999999999 minus 1E-999999999
# would need a coefficient of a billion digits. Division is never used.
_PRECISION = 400
_EXACT = Context(prec=_PRECISION, Emax=MAX_EMAX, Emin=MIN_EMIN)
_ONE = Decimal(1)
_HUNDRED = Decimal(100)
_FOUR_PLACES = Decimal("0.0001")

_NON_NEGATIVE = ("quantity", "unit_price", "line_total", "pack_size", "packs", "units",
                 "price_ex_vat", "price_inc_vat")
_ZERO_IS_ABSURD = ("quantity", "unit_price")
_DECIMAL_FIELDS = (*_NON_NEGATIVE, "vat_rate")
_DATE_FIELDS = ("quote_date", "valid_until")


def _check_field(name: str, value: object) -> None:
    if value is None:
        return
    if name in _DECIMAL_FIELDS:
        if not isinstance(value, Decimal):
            raise TypeError(f"{name} must be a Decimal, got {type(value).__name__}")
        if not value.is_finite():
            raise ValueError(f"{name} must be a finite Decimal")
    elif name in _DATE_FIELDS:
        if not isinstance(value, date) or isinstance(value, datetime):
            raise TypeError(f"{name} must be a date, got {type(value).__name__}")
    elif not isinstance(value, str):
        raise TypeError(f"{name} must be a str, got {type(value).__name__}")


@dataclass(frozen=True)
class QuoteLineFacts:
    """What a quote says about one line. Every field except `line_id` may be absent (None).

    `vat_rate` is a share: Decimal("0.20") is 20%."""

    line_id: str
    item_key: str | None = None
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    line_total: Decimal | None = None
    pack_size: Decimal | None = None
    packs: Decimal | None = None
    units: Decimal | None = None
    price_ex_vat: Decimal | None = None
    price_inc_vat: Decimal | None = None
    vat_rate: Decimal | None = None
    currency: str | None = None
    unit: str | None = None
    quote_date: date | None = None
    valid_until: date | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.line_id, str):
            raise TypeError(f"line_id must be a str, got {type(self.line_id).__name__}")
        for field in fields(self):
            if field.name != "line_id":
                _check_field(field.name, getattr(self, field.name))


# --- arithmetic and text helpers -------------------------------------------------------------

def _gap(a: Decimal, b: Decimal) -> Decimal:
    """|a - b|, exact."""
    return _EXACT.subtract(a, b).copy_abs()


def _tolerance(absolute: Decimal, relative: Decimal, expected: Decimal) -> Decimal:
    """The allowed gap: the absolute tolerance, or the relative share of |expected| if larger."""
    return max(absolute, _EXACT.multiply(relative, expected.copy_abs()))


def _plain(value: Decimal) -> str:
    """The value as plain text. A value that is not zero never shows as zero: it shows as the
    smallest step at 4 places, with its sign. A value too long to show is NOT_SHOWN, which is what
    `Finding.of` would make of it anyway; deciding that first avoids writing out a huge exponent."""
    if value.adjusted() >= VALUE_MAX:
        return NOT_SHOWN
    rounded = value.quantize(_FOUR_PLACES, rounding=ROUND_HALF_UP, context=_EXACT)
    if not rounded.is_zero():
        return format(rounded.normalize(_EXACT), "f")
    if value.is_zero():
        return "0"
    return "-0.0001" if value < 0 else "0.0001"


def _percent(rate: Decimal) -> str:
    return f"{_plain(_EXACT.multiply(rate, _HUNDRED))}%"


def _text(value: str | None) -> str | None:
    """The value without surrounding space, or None when it is absent or blank."""
    if value is None:
        return None
    return value.strip() or None


# --- rules on one line -----------------------------------------------------------------------

def _line_total_mismatch(facts: QuoteLineFacts, cfg: VerifyConfig) -> list[Finding]:
    if facts.quantity is None or facts.unit_price is None or facts.line_total is None:
        return []
    expected = _EXACT.multiply(facts.quantity, facts.unit_price)
    allowed = _tolerance(cfg.arith_abs_tolerance, cfg.arith_rel_tolerance, expected)
    if _gap(facts.line_total, expected) <= allowed:
        return []
    return [Finding.of(
        "line_total_mismatch", "line_total", total=_plain(facts.line_total),
        quantity=_plain(facts.quantity), unit_price=_plain(facts.unit_price),
        expected=_plain(expected),
    )]


def _pack_mismatch(facts: QuoteLineFacts) -> list[Finding]:
    if facts.packs is None or facts.pack_size is None or facts.units is None:
        return []
    expected = _EXACT.multiply(facts.packs, facts.pack_size)
    if facts.units == expected:
        return []
    return [Finding.of(
        "pack_arithmetic_mismatch", "units", packs=_plain(facts.packs),
        pack_size=_plain(facts.pack_size), units=_plain(facts.units), expected=_plain(expected),
    )]


def _vat_mismatch(facts: QuoteLineFacts, cfg: VerifyConfig) -> list[Finding]:
    if facts.price_ex_vat is None or facts.price_inc_vat is None or facts.vat_rate is None:
        return []
    expected = _EXACT.multiply(facts.price_ex_vat, _EXACT.add(_ONE, facts.vat_rate))
    allowed = _tolerance(cfg.arith_abs_tolerance, cfg.vat_rel_tolerance, expected)
    if _gap(facts.price_inc_vat, expected) <= allowed:
        return []
    return [Finding.of(
        "vat_arithmetic_mismatch", "price_inc_vat", inc=_plain(facts.price_inc_vat),
        ex=_plain(facts.price_ex_vat), rate=_percent(facts.vat_rate),
    )]


def _validity(facts: QuoteLineFacts) -> list[Finding]:
    if facts.quote_date is None or facts.valid_until is None:
        return []
    if facts.valid_until >= facts.quote_date:
        return []
    return [Finding.of(
        "validity_before_quote_date", "valid_until", valid_until=facts.valid_until.isoformat(),
        quote_date=facts.quote_date.isoformat(),
    )]


def _present_non_negative(facts: QuoteLineFacts) -> dict[str, Decimal]:
    values = {name: getattr(facts, name) for name in _NON_NEGATIVE}
    return {name: value for name, value in values.items() if value is not None}


def _negative(facts: QuoteLineFacts) -> list[Finding]:
    return [
        Finding.of("negative_value", name, name=name, value=_plain(value))
        for name, value in _present_non_negative(facts).items()
        if value < 0
    ]


def _absurd(facts: QuoteLineFacts) -> list[Finding]:
    found: list[Finding] = []
    for name, value in _present_non_negative(facts).items():
        if value < 0:
            continue  # a negative value is reported by negative_value, never as absurd too
        if value > ABSURD_MAX or (value == 0 and name in _ZERO_IS_ABSURD):
            found.append(Finding.of("absurd_value", name, name=name, value=_plain(value)))
    return found


def _ordered(found: Iterable[Finding]) -> tuple[Finding, ...]:
    """Each finding once, in a fixed order: field, then code, then values."""
    return tuple(sorted(set(found), key=lambda f: (f.field, f.code, f.values)))


def check_line(facts: QuoteLineFacts, cfg: VerifyConfig) -> tuple[Finding, ...]:
    """The number findings for one line. A rule whose inputs are absent is skipped."""
    return _ordered([
        *_line_total_mismatch(facts, cfg),
        *_pack_mismatch(facts),
        *_vat_mismatch(facts, cfg),
        *_validity(facts),
        *_negative(facts),
        *_absurd(facts),
    ])


# --- consistency across the lines of one quote -----------------------------------------------

def _reading_order(line: QuoteLineFacts) -> tuple[str, str, str, str]:
    return (line.line_id, _text(line.item_key) or "", _text(line.currency) or "",
            _text(line.unit) or "")


def _currency_findings(ordered: Sequence[QuoteLineFacts]) -> list[Finding]:
    currencies: list[str] = []
    for line in ordered:
        text = _text(line.currency)
        if text is not None:
            currencies.append(text.upper())
    if not currencies:
        return []
    first = currencies[0]
    others = {code for code in currencies if code != first}
    return [
        Finding.of("currency_inconsistent", "currency", first=first, other=other)
        for other in others
    ]


def _unit_findings(ordered: Sequence[QuoteLineFacts]) -> list[Finding]:
    units_by_item: dict[str, dict[str, str]] = {}
    for line in ordered:
        item, unit = _text(line.item_key), _text(line.unit)
        if item is not None and unit is not None:
            units_by_item.setdefault(item, {}).setdefault(unit.casefold(), unit)
    found: list[Finding] = []
    for distinct in units_by_item.values():
        if len(distinct) > 1:
            first, other, *_ = distinct.values()
            found.append(Finding.of("unit_inconsistent", "unit", first=first, other=other))
    return found


def check_consistency(lines: Sequence[QuoteLineFacts]) -> tuple[Finding, ...]:
    """Currency and unit agreement across the lines of one quote.

    The reference currency, and the two units reported for an item, are the first ones in line
    order. Lines are read in (line_id, item_key, currency, unit) order, so "first" does not depend
    on the order the caller passes the lines in: the output is the same for any permutation.
    """
    ordered = sorted(lines, key=_reading_order)
    return _ordered([*_currency_findings(ordered), *_unit_findings(ordered)])
