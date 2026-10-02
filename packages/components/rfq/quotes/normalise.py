"""Quote normalisation: raw extracted strings -> a typed `Quote` (spec R5, R9, R12).

Pure and deterministic. Money is `Decimal` only (never float) with an explicit currency; prices
are converted to a per-each unit price; anything that cannot be parsed safely becomes `None` plus
a flag. Nothing here trusts vendor text: values are matched against strict patterns and dropped
(with a flag) when they do not fit.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping
from datetime import date
from decimal import Decimal, InvalidOperation

from pydantic import BaseModel, ConfigDict

from components.core.domain import Authenticity, ExtractedQuote, Quote, Tier

from .grounding import dedupe
from .inert import inert_text

__all__ = [
    "Money",
    "is_quarantined",
    "normalise_quote",
    "parse_lead_time_days",
    "parse_money",
    "parse_uom_divisor",
    "parse_validity_days",
]

MAX_SNIPPET_CHARS = 200
MAX_LEAD_TIME_DAYS = 1095
MAX_VALIDITY_DAYS = 3650
MAX_DIGITS = 15
QUARANTINE_FLAGS = frozenset({"dmarc_fail"})

_ISO = {"USD", "EUR", "GBP", "CAD", "MXN"}
_SYMBOLS = {"US$": "USD", "€": "EUR", "£": "GBP", "C$": "CAD", "CA$": "CAD"}
_BARE_DOLLAR_OK = {"USD", "CAD", "MXN"}


class Money(BaseModel):
    model_config = ConfigDict(frozen=True)

    amount: Decimal
    currency_token: str | None = None


# ---------------------------------------------------------------- money

_TOKEN = r"(?:US\$|CA\$|C\$|[€£$]|[A-Za-z]{3})"  # noqa: S105
_NUM = r"(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+,\d{1,2}|\d+(?:\.\d+)?|\.\d+)"
_MONEY_RE = re.compile(
    rf"(?P<neg>-)?(?P<pre>{_TOKEN})?\s*(?P<num>{_NUM})\s*(?P<post>{_TOKEN})?", re.ASCII
)


def _to_decimal(num: str) -> Decimal | None:
    if re.fullmatch(r"\d+,\d{1,2}", num):
        num = num.replace(",", ".")
    else:
        num = num.replace(",", "")
    if sum(c.isdigit() for c in num) > MAX_DIGITS:
        return None
    try:
        return Decimal(num)
    except InvalidOperation:
        return None


def parse_money(raw: str) -> Money | None:
    """Parse a plain decimal amount with an optional currency token; anything else is None."""
    text = raw.strip()
    paren = text.startswith("(") and text.endswith(")")
    if paren:
        text = text[1:-1].strip()
    m = _MONEY_RE.fullmatch(text)
    if m is None:
        return None
    pre, post = m["pre"], m["post"]
    if pre and post:
        return None
    amount = _to_decimal(m["num"])
    if amount is None:
        return None
    if m["neg"] or paren:
        amount = -amount
    return Money(amount=amount, currency_token=pre or post)


def _iso(token: str) -> str | None:
    if token in _SYMBOLS:
        return _SYMBOLS[token]
    up = token.upper()
    return up if up in _ISO else None


# ---------------------------------------------------------------- UoM

_UOM_PREFIX = re.compile(r"(?:per\s+|/\s*)", re.IGNORECASE)
_EACH_WORDS = frozenset({"each", "ea", "piece", "pc", "pcs", "unit", "pieces", "units"})


def parse_uom_divisor(uom: str) -> int | None:
    """Divisor that turns a quoted price into a per-each price; None if unsupported/ambiguous."""
    text = uom.strip().rstrip(".").strip()
    m = _UOM_PREFIX.match(text)
    rest = text[m.end():].strip() if m else text
    if rest.lower() in _EACH_WORDS:
        return 1
    if rest in {"C", "100"} or rest.lower() == "hundred":
        return 100
    if rest in {"M", "1000", "1,000"} or rest.lower() == "thousand":
        return 1000
    return None


# ---------------------------------------------------------------- lead time

_WORDS = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7",
    "eight": "8", "nine": "9", "ten": "10", "eleven": "11", "twelve": "12",
}
_WORD_RE = re.compile(r"\b(" + "|".join(_WORDS) + r")\b")
_NEGATIVE = re.compile(r"not in stock|out of stock|backorder|no stock|tbd|call|vary|varies|soon")
_DURATION = re.compile(
    r"(?P<lo>\d+(?:\.\d+)?)(?:\s*(?:-|–|—|to)\s*(?P<hi>\d+(?:\.\d+)?))?\s*"
    r"(?P<unit>business\s+days?|working\s+days?|days?|weeks?|wks?|months?|mos?|hours?|hrs?)\b"
)
_INSTANT = re.compile(r"same day|today|immediately")
_NEXT_DAY = re.compile(r"next day|overnight")
_AMBIGUOUS = (None, ("lead_time_ambiguous",))


def _unit_days(n: Decimal, unit: str) -> Decimal:
    if unit.startswith(("business", "working")):
        return n * 7 / 5
    if unit.startswith("d"):
        return n
    if unit.startswith(("w",)):
        return n * 7
    if unit.startswith("mo"):
        return n * 30
    return n / 24


def parse_lead_time_days(text: str | None) -> tuple[int | None, tuple[str, ...]]:
    """Lead-time text -> (days, flags). Ambiguous text gives (None, ('lead_time_ambiguous',))."""
    if text is None or not text.strip():
        return None, ()
    t = _WORD_RE.sub(lambda m: _WORDS[m[1]], text.strip().lower())
    if _NEGATIVE.search(t):
        return _AMBIGUOUS
    items: list[tuple[int, tuple[str, ...]]] = []
    for m in _DURATION.finditer(t):
        lo = Decimal(m["lo"])
        hi = Decimal(m["hi"]) if m["hi"] else lo
        if hi < lo:
            return _AMBIGUOUS
        unit = m["unit"]
        flags: list[str] = []
        if unit.startswith(("business", "working")):
            flags.append("lead_time_business_days")
        if hi != lo:
            flags.append("lead_time_range_upper_bound")
        days = math.ceil(_unit_days(hi, unit))
        items.append((days, tuple(flags)))
    items += [(0, ())] * len(_INSTANT.findall(t)) + [(1, ())] * len(_NEXT_DAY.findall(t))
    if not items:
        return (0, ()) if "in stock" in t else _AMBIGUOUS
    if len(items) > 1:
        return _AMBIGUOUS
    days, flags_t = items[0]
    if days > MAX_LEAD_TIME_DAYS:
        return _AMBIGUOUS
    return days, flags_t


# ---------------------------------------------------------------- validity

_MONTHS = {
    m: i for i, m in enumerate(
        ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1
    )
}
_VALID_DURATION = re.compile(r"(\d{1,4})\s*(?:calendar\s+)?(days?|weeks?|months?)", re.ASCII)
_ISO_DATE = re.compile(r"(\d{4})-(\d{2})-(\d{2})", re.ASCII)
_MDY = re.compile(r"([A-Za-z]{3,9})\.?\s+(\d{1,2}),?\s+(\d{4})", re.ASCII)
_DMY = re.compile(r"(\d{1,2})\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})", re.ASCII)


def _find_date(t: str) -> tuple[bool, date | None]:
    """(looked like a date, parsed date)."""
    try:
        if m := _ISO_DATE.search(t):
            return True, date(int(m[1]), int(m[2]), int(m[3]))
        if m := _MDY.search(t):
            mon = _MONTHS.get(m[1][:3].lower())
            return (True, date(int(m[3]), mon, int(m[2]))) if mon else (False, None)
        if m := _DMY.search(t):
            mon = _MONTHS.get(m[2][:3].lower())
            return (True, date(int(m[3]), mon, int(m[1]))) if mon else (False, None)
    except ValueError:
        return True, None
    return False, None


def parse_validity_days(
    raw: str | None, *, received_on: date | None = None
) -> tuple[int | None, tuple[str, ...]]:
    """Validity text -> (days from receipt, flags)."""
    if raw is None or not raw.strip():
        return None, ()
    t = raw.strip()
    if m := _VALID_DURATION.fullmatch(t.lower()):
        n, unit = int(m[1]), m[2]
        days = n * (7 if unit.startswith("w") else 30 if unit.startswith("m") else 1)
        return (days, ()) if days <= MAX_VALIDITY_DAYS else (None, ("validity_unparsed",))
    looked, when = _find_date(t)
    if when is None:
        return None, ("validity_unparsed",)
    if received_on is None:
        return None, ("validity_date_unresolved",)
    delta = (when - received_on).days
    if delta < 0:
        return None, ("validity_expired",)
    return delta, ()


# ---------------------------------------------------------------- small fields

_MOQ_RE = re.compile(
    r"(\d{1,3}(?:,\d{3})+|\d+)(?:\s*(?:pcs?|pieces?|units?|each|ea))?", re.IGNORECASE | re.ASCII
)
_MPN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ./_-]{0,39}", re.ASCII)
_FREE_RE = re.compile(
    r"(?:free(?:\s+(?:shipping|freight))?|prepaid|included|no\s+charge)\.?", re.IGNORECASE
)
_CONDITIONS = {
    "new": "new", "brand new": "new", "factory new": "new",
    "remanufactured": "remanufactured", "reman": "remanufactured",
    "refurbished": "remanufactured", "nos": "surplus", "new old stock": "surplus",
    "surplus": "surplus", "used": "used",
}


def _parse_moq(raw: str) -> int | None:
    m = _MOQ_RE.fullmatch(raw.strip())
    if m is None:
        return None
    n = int(m[1].replace(",", ""))
    return n if 0 < n < 10**9 else None


def _parse_mpn(raw: str) -> str | None:
    text = raw.strip()
    if _MPN_RE.fullmatch(text) and text.count(" ") <= 2:
        return text
    return None


def _parse_freight(raw: str, currency: str | None) -> tuple[Decimal | None, tuple[str, ...]]:
    text = raw.strip()
    if _FREE_RE.fullmatch(text):
        return Decimal(0), ()
    m = parse_money(text)
    if m is None:
        return None, ("freight_unparsed",)
    if m.amount < 0:
        return None, ("freight_negative",)
    if m.currency_token and m.currency_token != "$":  # noqa: S105
        iso = _iso(m.currency_token)
        if iso is None or (currency is not None and iso != currency):
            return None, ("freight_currency_mismatch",)
    return m.amount, ()


# ---------------------------------------------------------------- price + currency


def _resolve_price(ex: ExtractedQuote) -> tuple[Decimal | None, str | None, list[str]]:
    flags: list[str] = []
    money = parse_money(ex.unit_price) if ex.unit_price and ex.unit_price.strip() else None
    has_price = bool(ex.unit_price and ex.unit_price.strip())
    if has_price and money is None:
        flags.append("unit_price_unparsed")
    raw_tokens = (ex.currency, money.currency_token if money else None)
    tokens = [t.strip() for t in raw_tokens if t and t.strip()]
    currency: str | None = None
    conflict = False
    if tokens:
        isos = [_iso(t) for t in tokens]
        for t, i in zip(tokens, isos, strict=True):
            if i is None and t != "$":
                flags.append("currency_unrecognised")
        explicit = {i for i in isos if i}
        if len(explicit) > 1:
            conflict = True
        elif explicit:
            currency = next(iter(explicit))
            if "$" in tokens and currency not in _BARE_DOLLAR_OK:
                conflict = True
        elif "$" in tokens:
            currency = "USD"
            flags.append("currency_assumed_usd")
        if conflict:
            currency = None
            flags.append("currency_conflict")
    elif has_price:
        flags.append("currency_missing")
    if money is None or conflict:
        return None, currency, flags
    if money.amount <= 0:
        flags.append("unit_price_nonpositive")
        return None, currency, flags
    return money.amount, currency, flags


def _unit_price_each(
    ex: ExtractedQuote, amount: Decimal | None
) -> tuple[Decimal | None, list[str]]:
    if amount is None:
        return None, []
    if ex.uom is None or not ex.uom.strip():
        return amount, ["uom_assumed_each"]
    divisor = parse_uom_divisor(ex.uom)
    if divisor is None:
        return None, ["uom_unrecognised"]
    return amount / divisor, []


# ---------------------------------------------------------------- public


def is_quarantined(quote: Quote) -> bool:
    """True when the quote's sender failed DMARC alignment (R12)."""
    return bool(QUARANTINE_FLAGS.intersection(quote.flags))


def _snippets(ex: ExtractedQuote, snippets: Mapping[str, str] | None) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in (snippets or {}).items():
        if key in ExtractedQuote.model_fields and getattr(ex, key) is not None:
            out[key] = inert_text(value)[:MAX_SNIPPET_CHARS]
    return out


def normalise_quote(
    extracted: ExtractedQuote,
    *,
    quote_id: str,
    tenant_id: str,
    rfq_id: str,
    vendor_id: str,
    offered_tier: Tier,
    dmarc_aligned: bool,
    authenticity_claim_verified: bool = False,
    grounding_flags: Iterable[str] = (),
    snippets: Mapping[str, str] | None = None,
    version: int = 1,
    received_on: date | None = None,
) -> Quote:
    """Build the typed `Quote`. Tier is the caller's classification and is passed through."""
    ex = extracted
    flags: list[str] = list(grounding_flags)
    amount, currency, f = _resolve_price(ex)
    flags += f
    price_each, f = _unit_price_each(ex, amount)
    flags += f

    lead, f = parse_lead_time_days(ex.lead_time)
    flags += f
    validity, f = parse_validity_days(ex.validity, received_on=received_on)
    flags += f

    freight: Decimal | None = None
    if ex.freight and ex.freight.strip():
        freight, f = _parse_freight(ex.freight, currency)
        flags += f

    moq: int | None = None
    if ex.moq and ex.moq.strip():
        moq = _parse_moq(ex.moq)
        if moq is None:
            flags.append("moq_unparsed")

    mpn: str | None = None
    if ex.offered_mpn is not None:
        mpn = _parse_mpn(ex.offered_mpn)
        if mpn is None:
            flags.append("offered_mpn_invalid")

    condition: str | None = None
    if ex.condition and ex.condition.strip():
        condition = _CONDITIONS.get(" ".join(ex.condition.lower().split()))
        if condition is None:
            flags.append("condition_unrecognised")
        elif condition != "new":
            flags.append("condition_not_new")

    if authenticity_claim_verified:
        authenticity = Authenticity.VERIFIED
    elif ex.authenticity_claim and ex.authenticity_claim.strip():
        authenticity = Authenticity.VENDOR_CLAIMED
    else:
        authenticity = Authenticity.UNKNOWN

    if not dmarc_aligned:
        flags.append("dmarc_fail")

    return Quote(
        id=quote_id, tenant_id=tenant_id, rfq_id=rfq_id, vendor_id=vendor_id, version=version,
        unit_price_each=price_each, currency=currency, uom_raw=ex.uom, moq=moq,
        lead_time_days=lead, freight=freight, validity_days=validity, offered_mpn=mpn,
        condition=condition, authenticity=authenticity, offered_tier=offered_tier,
        source_snippets=_snippets(ex, snippets), flags=dedupe(flags),
    )
