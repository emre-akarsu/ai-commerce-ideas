# ruff: noqa: E501
"""Findings: what a verification check noticed, how serious it is, and its plain-language text.

A finding carries a code, a severity, the field it is about and a few short string values. Its
explanation comes from a fixed template table over those values (rule R3: templated, no model
text). Values may originate in vendor content, so they are shown only when plain (no link, markup
or control character) and capped in length; anything else is replaced by `NOT_SHOWN`.

Severity: `info` is a note, `flag` asks the person to look, `review` keeps the line out of
"clean" until a person has decided. Nothing here approves anything.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from string import Formatter

NOT_SHOWN = "[not shown]"
VALUE_MAX = 60
_KEY = re.compile(r"[a-z][a-z0-9_]{0,31}")
_BAD = re.compile(r"[<>\[\]{}`|\\@]|://|\bwww\.|\bmailto:", re.IGNORECASE)


class Severity(StrEnum):
    INFO = "info"
    FLAG = "flag"
    REVIEW = "review"


# code -> (default severity, plain-language template over the finding's own value keys)
CATALOGUE: dict[str, tuple[Severity, str]] = {
    # number checks
    "line_total_mismatch": (Severity.REVIEW, "The line total {total} is not {quantity} x {unit_price} ({expected})."),
    "pack_arithmetic_mismatch": (Severity.REVIEW, "{packs} packs of {pack_size} is {expected} units, but the quote says {units}."),
    "vat_arithmetic_mismatch": (Severity.REVIEW, "The price with VAT {inc} does not match the price without VAT {ex} at {rate} VAT."),
    "currency_inconsistent": (Severity.REVIEW, "The quote mixes currencies: {first} and {other}."),
    "unit_inconsistent": (Severity.FLAG, "The quote prices the same item in different units: {first} and {other}."),
    "validity_before_quote_date": (Severity.REVIEW, "The quote says it is valid until {valid_until}, which is before its date {quote_date}."),
    "negative_value": (Severity.REVIEW, "The quote has a negative {name}: {value}."),
    "absurd_value": (Severity.REVIEW, "The {name} {value} is outside a believable range."),
    # shadow diff between two readings of the same quote
    "readings_disagree": (Severity.REVIEW, "The two readings of this quote disagree on {name}: {first} and {other}. A person must check the quote text."),
    "reading_missing": (Severity.FLAG, "Only one reading found a value for {name}: {first}. Check it against the quote text."),
    # plausibility against the customer's own history
    "price_jump_vs_last_paid": (Severity.FLAG, "The price {price} is {ratio} times the last price you paid ({last_paid})."),
    "unit_basis_shift": (Severity.FLAG, "The price {price} looks like a different unit from the one you usually buy ({usual_unit}). Check the unit."),
    "quantity_unusual": (Severity.FLAG, "The quantity {quantity} is {ratio} times your usual order ({usual})."),
}


def _check_catalogue() -> None:
    for code, (_, template) in CATALOGUE.items():
        if _BAD.search(template.replace("{", "").replace("}", "")):
            raise ValueError(f"{code}: template holds a link or markup")
        for _, name, spec, conv in Formatter().parse(template):
            if name is not None and (not _KEY.fullmatch(name) or spec or conv):
                raise ValueError(f"{code}: bad placeholder {name!r}")


_check_catalogue()


def safe_value(text: object) -> str:
    """The value as short plain text, or `NOT_SHOWN` when it is not plain."""
    s = " ".join(str(text).split())
    if not s or len(s) > VALUE_MAX or _BAD.search(s) or any(ord(c) < 32 or ord(c) == 127 for c in s):
        return NOT_SHOWN
    return s


@dataclass(frozen=True)
class Finding:
    code: str
    severity: Severity
    field: str
    values: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if self.code not in CATALOGUE:
            raise ValueError(f"unknown finding code {self.code!r}")
        if not isinstance(self.severity, Severity):
            raise ValueError("severity must be a Severity")
        if not _KEY.fullmatch(self.field):
            raise ValueError("field must be a plain token")
        for key, value in self.values:
            if not _KEY.fullmatch(key) or safe_value(value) != value:
                raise ValueError(f"value {key!r} is not plain text; build findings with Finding.of")

    @classmethod
    def of(cls, code: str, field: str, severity: Severity | None = None, **values: object) -> Finding:
        """Build a finding with its catalogue severity (unless given) and sanitised values."""
        if code not in CATALOGUE:
            raise ValueError(f"unknown finding code {code!r}")
        sev = CATALOGUE[code][0] if severity is None else severity
        return cls(code, sev, field, tuple(sorted((k, safe_value(v)) for k, v in values.items())))

    def value(self, key: str) -> str | None:
        return dict(self.values).get(key)


def explain(finding: Finding) -> str:
    """Plain-language text for a finding, from the template table. Missing values show as NOT_SHOWN."""
    template = CATALOGUE[finding.code][1]
    have = dict(finding.values)
    names = {n for _, n, _, _ in Formatter().parse(template) if n}
    return template.format(**{n: have.get(n, NOT_SHOWN) for n in names})
