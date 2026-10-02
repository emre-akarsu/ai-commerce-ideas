"""Quote normalisation: raw extracted strings -> a typed `Quote` (spec R5, R9, R12).

Pure and deterministic. Money is `Decimal` only (never float) with an explicit currency; prices
are converted to a per-each unit price; anything that cannot be parsed safely becomes `None` plus
a flag. Nothing here trusts vendor text: values are matched against strict patterns and dropped
(with a flag) when they do not fit.
"""

from __future__ import annotations

import math
import re
from collections.abc import Collection, Iterable, Mapping
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from pydantic import BaseModel, ConfigDict

from aiplat.profile import ResolvedProfile
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
    "working_days_to_calendar",
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


def _iso(
    token: str,
    symbols: Mapping[str, str] = _SYMBOLS,
    accepted: Collection[str] = _ISO,
) -> str | None:
    if token in symbols:
        return symbols[token]
    up = token.upper()
    return up if up in accepted else None


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
_NEXT_WORKING_DAY = re.compile(r"next (?:working|business) day")
_CALENDAR_DAYS = re.compile(r"calendar\s+(days?)")
_AMBIGUOUS = (None, ("lead_time_ambiguous",))


def working_days_to_calendar(
    n: int,
    start: date,
    working_week: Collection[int] = (0, 1, 2, 3, 4),
    holidays: Collection[date] = (),
) -> int:
    """Calendar days from `start` until `n` working days have elapsed (start itself not counted;
    weekend days and listed holidays are skipped). Pure and deterministic."""
    if n < 0 or not working_week:
        raise ValueError("n must be >= 0 and working_week non-empty")
    day, counted = start, 0
    while counted < n:
        day += timedelta(days=1)
        if day.weekday() in working_week and day not in holidays:
            counted += 1
    return (day - start).days


class _LeadCtx(BaseModel):
    """Profile-derived lead-time calendar (only built when the default unit is working days)."""

    model_config = ConfigDict(frozen=True)

    start: date | None
    working_week: tuple[int, ...]
    holidays: tuple[date, ...]

    def to_calendar(self, n: int) -> int:
        if self.start is None:
            return math.ceil(Decimal(n) * 7 / 5)
        return working_days_to_calendar(n, self.start, self.working_week, self.holidays)


def _lead_ctx(profile: ResolvedProfile | None, start: date | None) -> _LeadCtx | None:
    if profile is None or profile.profile.lead_time.default_unit != "working_days":
        return None
    loc = profile.profile.locale
    return _LeadCtx(start=start, working_week=loc.working_week, holidays=loc.holidays)


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


def parse_lead_time_days(
    text: str | None, *, _ctx: _LeadCtx | None = None
) -> tuple[int | None, tuple[str, ...]]:
    """Lead-time text -> (days, flags). Ambiguous text gives (None, ('lead_time_ambiguous',)).

    `_ctx` (built from a working-days profile by `normalise_quote`) makes bare "N days" mean
    working days and converts working days to calendar days; without it the legacy rules apply."""
    if text is None or not text.strip():
        return None, ()
    t = _WORD_RE.sub(lambda m: _WORDS[m[1]], text.strip().lower())
    if _NEGATIVE.search(t):
        return _AMBIGUOUS
    calendar_explicit = False
    if _ctx is not None:
        calendar_explicit = bool(_CALENDAR_DAYS.search(t))
        t = _CALENDAR_DAYS.sub(r"\1", t)
    items: list[tuple[int, tuple[str, ...]]] = []
    for m in _DURATION.finditer(t):
        lo = Decimal(m["lo"])
        hi = Decimal(m["hi"]) if m["hi"] else lo
        if hi < lo:
            return _AMBIGUOUS
        unit = m["unit"]
        flags: list[str] = []
        explicit_wd = unit.startswith(("business", "working"))
        if explicit_wd:
            flags.append("lead_time_business_days")
        if hi != lo:
            flags.append("lead_time_range_upper_bound")
        if _ctx is not None and (explicit_wd or (unit.startswith("d") and not calendar_explicit)):
            if not explicit_wd:
                flags.append("lead_time_working_days_assumed")
            days = _ctx.to_calendar(math.ceil(hi))
        else:
            days = math.ceil(_unit_days(hi, unit))
        items.append((days, tuple(flags)))
    items += [(0, ())] * len(_INSTANT.findall(t))
    if _ctx is None:
        items += [(1, ())] * len(_NEXT_DAY.findall(t))
    else:
        nwd = len(_NEXT_WORKING_DAY.findall(t))
        nd = len(_NEXT_DAY.findall(t))
        items += [(_ctx.to_calendar(1), ())] * nwd
        items += [(_ctx.to_calendar(1), ("lead_time_working_days_assumed",))] * nd
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


def _parse_freight(
    raw: str, currency: str | None, pol: _CurrencyPolicy | None = None
) -> tuple[Decimal | None, tuple[str, ...]]:
    pol = pol or _LEGACY_POLICY
    text = raw.strip()
    if _FREE_RE.fullmatch(text):
        return Decimal(0), ()
    m = parse_money(text)
    if m is None:
        return None, ("freight_unparsed",)
    if m.amount < 0:
        return None, ("freight_negative",)
    if m.currency_token and m.currency_token != "$":  # noqa: S105
        iso = _iso(m.currency_token, pol.symbols, pol.accepted)
        if iso is None or (currency is not None and iso != currency):
            return None, ("freight_currency_mismatch",)
    return m.amount, ()


# ---------------------------------------------------------------- price + currency


class _CurrencyPolicy(BaseModel):
    """What currency tokens mean. The default instance reproduces the pre-profile (US) rules."""

    model_config = ConfigDict(frozen=True)

    symbols: dict[str, str]
    accepted: frozenset[str]
    bare_dollar: str | None  # what a lone "$" means; None = ambiguous
    assumed: str = "flag_require_approval"
    base: str = "USD"

    @property
    def bare_dollar_ok(self) -> frozenset[str]:
        return frozenset(_BARE_DOLLAR_OK & self.accepted)


_LEGACY_POLICY = _CurrencyPolicy(
    symbols=_SYMBOLS, accepted=frozenset(_ISO), bare_dollar="USD"
)


def _currency_policy(profile: ResolvedProfile | None) -> _CurrencyPolicy:
    if profile is None:
        return _LEGACY_POLICY
    m = profile.profile.money
    return _CurrencyPolicy(
        symbols=dict(m.symbol_map), accepted=frozenset(m.accepted_currencies),
        bare_dollar=m.bare_dollar_currency, assumed=m.assumed_currency, base=m.base_currency,
    )


def _ambiguous_dollar(pol: _CurrencyPolicy, flags: list[str]) -> tuple[str | None, bool]:
    """A lone "$" where the profile has no default meaning. Returns (currency, drop_price)."""
    flags.append("currency_ambiguous")
    if pol.assumed == "assume_base_flag":
        flags.append(f"currency_assumed_{pol.base.lower()}")
        return pol.base, False
    return None, pol.assumed == "reject"


def _resolve_price(
    ex: ExtractedQuote, pol: _CurrencyPolicy = _LEGACY_POLICY, price_text: str | None = None
) -> tuple[Decimal | None, str | None, list[str]]:
    flags: list[str] = []
    raw_price = ex.unit_price if price_text is None else price_text
    money = parse_money(raw_price) if raw_price and raw_price.strip() else None
    has_price = bool(raw_price and raw_price.strip())
    if has_price and money is None:
        flags.append("unit_price_unparsed")
    raw_tokens = (ex.currency, money.currency_token if money else None)
    tokens = [t.strip() for t in raw_tokens if t and t.strip()]
    currency: str | None = None
    conflict = False
    drop = False
    if tokens:
        isos = [_iso(t, pol.symbols, pol.accepted) for t in tokens]
        for t, i in zip(tokens, isos, strict=True):
            if i is None and t != "$":
                flags.append("currency_unrecognised")
        explicit = {i for i in isos if i}
        if len(explicit) > 1:
            conflict = True
        elif explicit:
            currency = next(iter(explicit))
            if "$" in tokens and currency not in pol.bare_dollar_ok:
                conflict = True
        elif "$" in tokens:
            if pol.bare_dollar:
                currency = pol.bare_dollar
                flags.append(f"currency_assumed_{currency.lower()}")
            else:
                currency, drop = _ambiguous_dollar(pol, flags)
        if conflict:
            currency = None
            flags.append("currency_conflict")
    elif has_price:
        flags.append("currency_missing")
        if pol.assumed == "assume_base_flag" and pol is not _LEGACY_POLICY:
            currency = pol.base
            flags.append(f"currency_assumed_{pol.base.lower()}")
    if money is None or conflict or drop:
        return None, currency, flags
    if money.amount <= 0:
        flags.append("unit_price_nonpositive")
        return None, currency, flags
    return money.amount, currency, flags


# ---------------------------------------------------------------- tax basis

_TAX_WORD = r"(?:vat|gst|(?:sales\s+)?tax)"
EX_TAX_RE = re.compile(
    rf"(?:\+|\bplus\b|\bex\b|\bexc\b|\bexcl\b|\bexcluding\b|\bexclusive\s+of\b|"
    rf"\bbefore\b)[.\-\s]*{_TAX_WORD}\b|\b{_TAX_WORD}\s+(?:excluded|extra|exclusive)\b",
    re.IGNORECASE,
)
INC_TAX_RE = re.compile(
    rf"(?:\binc\b|\bincl\b|\bincluding\b|\binclusive\s+of\b|\bwith\b)[.\-\s]*{_TAX_WORD}\b|"
    rf"\b{_TAX_WORD}\s+(?:included|inclusive|incl\.?|inc\.?)(?!\w)",
    re.IGNORECASE,
)
_PRICE_TAX_TAIL_RE = re.compile(
    rf"\s*(?:\+|\bplus\b|\bex\.?|\bexcl?\.?|\binc\.?|\bincl?\.?|\bexcluding\b|"
    rf"\bincluding\b)\s*{_TAX_WORD}\b\.?\s*$|\s*\b{_TAX_WORD}\s+"
    rf"(?:included|inclusive|excluded|extra)\s*$",
    re.IGNORECASE,
)
_RATE_Q = Decimal("0.0001")


def detect_tax_basis(*texts: str | None) -> str:
    """'ex_tax' | 'inc_tax' | 'unknown' from wording such as '+ VAT' or 'inc. VAT'; contradictory
    wording is 'unknown'."""
    ex = inc = False
    for t in texts:
        if t:
            ex = ex or bool(EX_TAX_RE.search(t))
            inc = inc or bool(INC_TAX_RE.search(t))
    if ex == inc:
        return "unknown"
    return "ex_tax" if ex else "inc_tax"


def inc_to_ex_tax(price_inc: Decimal, rate: Decimal) -> Decimal:
    """Ex-tax price = inc-tax price / (1 + rate), 4 dp, half-up."""
    return (price_inc / (1 + rate)).quantize(_RATE_Q, rounding=ROUND_HALF_UP)


def _apply_tax(
    ex: ExtractedQuote, profile: ResolvedProfile, price_each: Decimal | None
) -> tuple[Decimal | None, Decimal | None, str, Decimal | None, list[str]]:
    """-> (ex-tax each, quoted each, basis, rate applied, flags)."""
    pol = profile.profile.tax
    if price_each is None:
        return None, None, "unknown", None, []
    flags: list[str] = []
    basis = detect_tax_basis(ex.tax_text, ex.unit_price)
    if basis == "unknown":
        if pol.unknown_basis == "assume_default_flag" and pol.quote_basis_default != "unknown":
            basis = pol.quote_basis_default
            flags.append("tax_basis_assumed")
        else:
            flags.append("tax_basis_unknown")
    if basis == "inc_tax":
        flags.append("tax_inc_converted")
        ex_price = inc_to_ex_tax(price_each, pol.standard_rate)
        return ex_price, price_each, basis, pol.standard_rate, flags
    return price_each, price_each, basis, None, flags


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


def _strip_tax_tail(raw: str | None) -> str | None:
    """Drop trailing tax wording ('+ VAT', 'inc VAT') so the amount can be parsed."""
    return _PRICE_TAX_TAIL_RE.sub("", raw).strip() if raw else raw


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
    profile: ResolvedProfile | None = None,
) -> Quote:
    """Build the typed `Quote`. Tier is the caller's classification and is passed through.

    `profile=None` is the legacy (US) behaviour. With a profile, money, tax-basis and lead-time
    rules come from it; a profile whose standard tax rate is 0 adds no tax handling at all."""
    ex = extracted
    flags: list[str] = list(grounding_flags)
    cur_pol = _currency_policy(profile)
    tax_active = profile is not None and profile.profile.tax.standard_rate > 0
    price_text = _strip_tax_tail(ex.unit_price) if tax_active else None
    amount, currency, f = _resolve_price(ex, cur_pol, price_text)
    flags += f
    price_each, f = _unit_price_each(ex, amount)
    flags += f
    quoted_each: Decimal | None = None
    basis, rate = "unknown", None
    if profile is not None and tax_active:
        price_each, quoted_each, basis, rate, f = _apply_tax(ex, profile, price_each)
        flags += f

    lead, f = parse_lead_time_days(ex.lead_time, _ctx=_lead_ctx(profile, received_on))
    flags += f
    validity, f = parse_validity_days(ex.validity, received_on=received_on)
    flags += f

    freight: Decimal | None = None
    if ex.freight and ex.freight.strip():
        freight, f = _parse_freight(ex.freight, currency, cur_pol)
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
        unit_price_each=price_each, unit_price_quoted=quoted_each, tax_basis=basis, tax_rate=rate,
        currency=currency, uom_raw=ex.uom, moq=moq,
        lead_time_days=lead, freight=freight, validity_days=validity, offered_mpn=mpn,
        condition=condition, authenticity=authenticity, offered_tier=offered_tier,
        source_snippets=_snippets(ex, snippets), flags=dedupe(flags),
    )
