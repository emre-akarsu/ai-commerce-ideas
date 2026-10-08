"""The seeded set: clean quotes and injected errors, generated deterministically.

No randomness: every case is picked from small fixed pools by index arithmetic, so the set is the
same on every run and every Python version. `set_hash()` is the digest recorded in
`FROZEN.json`; changing the generator changes the hash and the test fails until a person updates
the record on purpose (spec F28 clause 6: built and frozen before any recall figure is reported).

A case is a vendor reply text, what the second reader (standing in for the model) returns when
it differs from the deterministic reading, the customer's price history for the part, and the
answer: the values the final quote must hold. "Neutralised" (the error was dropped before it
could matter) and "caught" (a flag) both count as safe; an error is an ESCAPE only when the final
quote holds a wrong value and carries no flag.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from components.core.domain import ExtractedQuote
from components.rfq.quotes.extractors import RegexQuoteExtractor

GENERATOR_VERSION = "1"
PART = "AL6205-2RS"  # the part the harness's requests ask for (synthetic)
VENDORS = tuple(f"v{n:02d}" for n in range(1, 31))
PRICES = tuple(Decimal(p) for p in (
    "3.80", "3.95", "4.05", "4.20", "4.35", "4.50", "4.65", "4.80", "4.95", "5.10", "5.25", "5.40"))
LEADS = (2, 3, 4, 5, 7)
FREIGHT = ("9.50", "12.00", "15.00", "18.50")
UK_VAT = Decimal("1.20")
HISTORY_DAYS_AGO = (10, 40, 90)  # three earlier purchases of the part from the vendor

ERROR_TYPES = (
    "decimal_slip", "wrong_pack", "vat_swap", "unit_swap", "wrong_currency",
    "transposed_quantity", "expired_validity",
)
Kind = Literal["clean", "injected"]
_REGEX = RegexQuoteExtractor()


@dataclass(frozen=True)
class Case:
    case_id: str
    kind: Kind
    error_type: str  # "" for a clean case
    mechanism: str
    vendor: str
    text: str
    reading: ExtractedQuote | None  # None: the second reader agrees with the deterministic one
    history_prices: tuple[Decimal, ...]  # earlier prices of PART from this vendor, GBP each, ex VAT
    answer: Mapping[str, object]  # Quote attribute -> the value it must hold

    def canonical(self) -> dict[str, object]:
        return {
            "id": self.case_id, "kind": self.kind, "type": self.error_type,
            "mechanism": self.mechanism, "vendor": self.vendor, "text": self.text,
            "reading": self.reading.model_dump() if self.reading else None,
            "history": [str(p) for p in self.history_prices],
            "answer": {k: str(v) for k, v in sorted(self.answer.items())},
        }


def _money(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"


def reply(price: Decimal, *, lead: int, valid: str, freight: str, basis: str = "ex",
          per: str = "each", extra: str = "") -> str:
    """A clean vendor reply in the shape the deterministic reader understands. `price` is what
    the text states: ex VAT for basis "ex", inc VAT for "inc"."""
    tax = {"ex": "+ VAT", "inc": "inc VAT"}[basis]
    return (f"Hello,\nPart number: {PART}\nUnit price: £{_money(price)} {per} {tax}\n"
            f"Lead time: {lead} days\nFreight: £{freight}\nQuote valid {valid}\n"
            f"Condition: new\n{extra}")


def _answer(each_ex: Decimal, *, validity: int | None = 30,
            tax_basis: str = "ex_tax") -> dict[str, object]:
    """The values the final quote must hold: the price per piece ex VAT, whatever basis the vendor
    stated, and the basis the vendor stated."""
    return {"unit_price_each": each_ex, "currency": "GBP", "tax_basis": tax_basis,
            "validity_days": validity}


def _pick(i: int) -> tuple[str, Decimal, int, str]:
    """Vendor, price, lead time and freight for variant `i`, with different strides so the
    pools do not line up."""
    return (VENDORS[i % len(VENDORS)], PRICES[(i * 5) % len(PRICES)], LEADS[(i * 3) % len(LEADS)],
            FREIGHT[(i * 7) % len(FREIGHT)])


def _history(price: Decimal) -> tuple[Decimal, ...]:
    """Three earlier purchases within a few percent of the right price."""
    return (price, (price * Decimal("1.03")).quantize(Decimal("0.01")),
            (price * Decimal("0.97")).quantize(Decimal("0.01")))


def _regex(text: str) -> ExtractedQuote:
    return _REGEX.extract(text)


def _case(kind: Kind, etype: str, mech: str, i: int, text: str, answer: dict[str, object], *,
          reading: ExtractedQuote | None = None, history: tuple[Decimal, ...] = (),
          vendor: str) -> Case:
    cid = f"{kind[:1]}-{etype or 'clean'}-{mech}-{i:03d}"
    return Case(cid, kind, etype, mech, vendor, text, reading, history, answer)


# ------------------------------------------------------------------ clean cases


def _clean_variants() -> list[Case]:
    """Clean quotes. One in three is read by a second reader that copies a different but
    equivalent stretch of the text (the symbol kept on the price, the symbol left off the freight):
    a safety net that flags these cries wolf."""
    cases: list[Case] = []
    valid_pool = ("14 days", "30 days", "45 days", "60 days")
    for i in range(300):
        vendor, price, lead, fr = _pick(i)
        valid = valid_pool[i % 4]
        days = int(valid.split()[0])
        shape = i % 3
        if shape == 0:
            text, truth = reply(price, lead=lead, valid=valid, freight=fr), price
        elif shape == 1:
            inc = (price * UK_VAT).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            text = reply(inc, lead=lead, valid=valid, freight=fr, basis="inc")
            truth = (inc / UK_VAT).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        else:
            text = reply(price * 100, lead=lead, valid=valid, freight=fr, per="per 100")
            truth = price
        base = _regex(text)
        reading: ExtractedQuote | None = None
        variant = i % 6
        if variant == 4:  # the symbol stays on the price: still a stretch of the text
            reading = base.model_copy(update={"unit_price": f"£{base.unit_price}"})
        elif variant == 5:  # the symbol is left off the freight: still a stretch of the text
            reading = base.model_copy(update={"freight": fr})
        basis = "inc_tax" if shape == 1 else "ex_tax"
        cases.append(_case("clean", "", f"shape{shape}v{variant}", i, text,
                           _answer(truth, validity=days, tax_basis=basis), reading=reading,
                           vendor=vendor))
    return cases


# ------------------------------------------------------------------ injected errors


def _decimal_slip() -> list[Case]:
    out: list[Case] = []
    for i in range(10):  # the vendor's own typo: 10 times the usual price, history on file
        vendor, price, lead, fr = _pick(i)
        text = reply(price * 10, lead=lead, valid="30 days", freight=fr)
        out.append(_case("injected", "decimal_slip", "vendor_typo_history", i, text,
                         _answer(price), history=_history(price), vendor=vendor))
    for i in range(10, 20):  # the same typo with no history to compare with
        vendor, price, lead, fr = _pick(i)
        text = reply(price * 10, lead=lead, valid="30 days", freight=fr)
        out.append(_case("injected", "decimal_slip", "vendor_typo_no_history", i, text,
                         _answer(price), vendor=vendor))
    for i in range(20, 25):  # the second reader writes a slipped price that is not in the text
        vendor, price, lead, fr = _pick(i)
        text = reply(price, lead=lead, valid="30 days", freight=fr)
        slipped = _regex(text).model_copy(update={"unit_price": _money(price * 10)})
        out.append(_case("injected", "decimal_slip", "reading_not_in_text", i, text,
                         _answer(price), reading=slipped, vendor=vendor))
    for i in range(25, 30):  # the second reader takes the freight figure for the price
        vendor, price, lead, fr = _pick(i)
        text = reply(price, lead=lead, valid="30 days", freight=fr)
        wrong = _regex(text).model_copy(update={"unit_price": fr})
        out.append(_case("injected", "decimal_slip", "reading_takes_freight", i, text,
                         _answer(price), reading=wrong, vendor=vendor))
    return out


def _wrong_pack() -> list[Case]:
    out: list[Case] = []
    for i in range(30, 40):  # price per 100, second reader drops the unit
        vendor, price, lead, fr = _pick(i)
        text = reply(price * 100, lead=lead, valid="30 days", freight=fr, per="per 100")
        dropped = _regex(text).model_copy(update={"uom": None})
        out.append(_case("injected", "wrong_pack", "unit_dropped", i, text, _answer(price),
                         reading=dropped, vendor=vendor))
    for i in range(40, 45):  # price per 100, second reader says "each" (not in the text)
        vendor, price, lead, fr = _pick(i)
        text = reply(price * 100, lead=lead, valid="30 days", freight=fr, per="per 100")
        each = _regex(text).model_copy(update={"uom": "each"})
        out.append(_case("injected", "wrong_pack", "unit_not_in_text", i, text, _answer(price),
                         reading=each, vendor=vendor))
    for i in range(45, 55):  # the vendor quotes per 100 by mistake; history is per piece
        vendor, price, lead, fr = _pick(i)
        text = reply(price, lead=lead, valid="30 days", freight=fr, per="per 100")
        out.append(_case("injected", "wrong_pack", "vendor_typo_history", i, text, _answer(price),
                         history=_history(price), vendor=vendor))
    for i in range(55, 60):  # the same, no history
        vendor, price, lead, fr = _pick(i)
        text = reply(price, lead=lead, valid="30 days", freight=fr, per="per 100")
        out.append(_case("injected", "wrong_pack", "vendor_typo_no_history", i, text,
                         _answer(price), vendor=vendor))
    return out


def _vat_swap() -> list[Case]:
    out: list[Case] = []
    for i in range(60, 70):  # the text says inc VAT, the second reader says "+ VAT"
        vendor, price, lead, fr = _pick(i)
        inc = (price * UK_VAT).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        text = reply(inc, lead=lead, valid="30 days", freight=fr, basis="inc")
        truth = (inc / UK_VAT).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        wrong = _regex(text).model_copy(update={"tax_text": "+ VAT"})
        out.append(_case("injected", "vat_swap", "basis_not_in_text", i, text,
                         _answer(truth, tax_basis="inc_tax"), reading=wrong, vendor=vendor))
    for i in range(70, 80):  # the second reader leaves the VAT wording out
        vendor, price, lead, fr = _pick(i)
        inc = (price * UK_VAT).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        text = reply(inc, lead=lead, valid="30 days", freight=fr, basis="inc")
        truth = (inc / UK_VAT).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        silent = _regex(text).model_copy(update={"tax_text": None})
        out.append(_case("injected", "vat_swap", "basis_dropped", i, text,
                         _answer(truth, tax_basis="inc_tax"), reading=silent, vendor=vendor))
    for i in range(80, 90):  # the text lists both; the second reader pairs inc price with "ex VAT"
        vendor, price, lead, fr = _pick(i)
        inc = (price * UK_VAT).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        text = (f"Hello,\nPart number: {PART}\nUnit price: £{_money(price)} each ex VAT "
                f"(£{inc} each inc VAT)\nLead time: {lead} days\nFreight: £{fr}\n"
                f"Quote valid 30 days\nCondition: new\n")
        crossed = _regex(text).model_copy(update={"unit_price": _money(inc), "tax_text": "ex VAT"})
        out.append(_case("injected", "vat_swap", "paired_wrongly", i, text, _answer(price),
                         reading=crossed, vendor=vendor))
    return out


def _unit_swap() -> list[Case]:
    out: list[Case] = []
    for i in range(90, 100):  # price per metre, second reader drops the unit
        vendor, price, lead, fr = _pick(i)
        text = reply(price, lead=lead, valid="30 days", freight=fr, per="per metre")
        dropped = _regex(text).model_copy(update={"uom": None})
        out.append(_case("injected", "unit_swap", "unit_dropped", i, text, _answer(price),
                         reading=dropped, vendor=vendor))
    for i in range(100, 110):  # the vendor prices per metre where history is per piece
        vendor, price, lead, fr = _pick(i)
        text = reply(price, lead=lead, valid="30 days", freight=fr, per="per metre")
        out.append(_case("injected", "unit_swap", "vendor_basis_change", i, text, _answer(price),
                         history=_history(price), vendor=vendor))
    for i in range(110, 120):  # the second reader says "each" for a per-metre price
        vendor, price, lead, fr = _pick(i)
        text = reply(price, lead=lead, valid="30 days", freight=fr, per="per metre")
        each = _regex(text).model_copy(update={"uom": "each"})
        out.append(_case("injected", "unit_swap", "unit_not_in_text", i, text, _answer(price),
                         reading=each, vendor=vendor))
    return out


def _wrong_currency() -> list[Case]:
    out: list[Case] = []
    for i in range(120, 130):  # the text says GBP, the second reader says USD
        vendor, price, lead, fr = _pick(i)
        text = reply(price, lead=lead, valid="30 days", freight=fr)
        wrong = _regex(text).model_copy(update={"currency": "USD"})
        out.append(_case("injected", "wrong_currency", "currency_not_in_text", i, text,
                         _answer(price), reading=wrong, vendor=vendor))
    for i in range(130, 140):  # the vendor types a dollar sign where history is in pounds
        vendor, price, lead, fr = _pick(i)
        text = reply(price, lead=lead, valid="30 days", freight=fr).replace("£", "$")
        out.append(_case("injected", "wrong_currency", "vendor_symbol_typo", i, text,
                         _answer(price), history=_history(price), vendor=vendor))
    for i in range(140, 150):  # the second reader writes a euro sign on the price
        vendor, price, lead, fr = _pick(i)
        text = reply(price, lead=lead, valid="30 days", freight=fr)
        wrong = _regex(text).model_copy(update={"unit_price": f"€{_money(price)}"})
        out.append(_case("injected", "wrong_currency", "symbol_not_in_text", i, text,
                         _answer(price), reading=wrong, vendor=vendor))
    return out


def _transposed_quantity() -> list[Case]:
    out: list[Case] = []
    for i in range(150, 160):  # minimum order 12 in the text, the second reader says 21
        vendor, price, lead, fr = _pick(i)
        text = reply(price, lead=lead, valid="30 days", freight=fr, extra="MOQ 12\n")
        swapped = _regex(text).model_copy(update={"moq": "21"})
        answer = {**_answer(price), "moq": 12}
        out.append(_case("injected", "transposed_quantity", "moq_not_in_text", i, text, answer,
                         reading=swapped, vendor=vendor))
    for i in range(160, 170):  # the second reader takes "30 days" for the minimum order
        vendor, price, lead, fr = _pick(i)
        text = reply(price, lead=lead, valid="30 days", freight=fr, extra="MOQ 12\n")
        wrong = _regex(text).model_copy(update={"moq": "30"})
        answer = {**_answer(price), "moq": 12}
        out.append(_case("injected", "transposed_quantity", "moq_taken_from_validity", i, text,
                         answer, reading=wrong, vendor=vendor))
    for i in range(170, 180):  # quantity available 120 in the text, the second reader says 210
        vendor, price, lead, fr = _pick(i)
        text = reply(price, lead=lead, valid="30 days", freight=fr, extra="Qty available: 120\n")
        swapped = _regex(text).model_copy(update={"quantity_available": "210"})
        out.append(_case("injected", "transposed_quantity", "available_not_in_text", i, text,
                         _answer(price), reading=swapped, vendor=vendor))
    return out


def _expired_validity() -> list[Case]:
    out: list[Case] = []
    for i in range(180, 190):  # the text gives a validity date that has passed
        vendor, price, lead, fr = _pick(i)
        text = reply(price, lead=lead, valid="until 2026-09-01", freight=fr)
        out.append(_case("injected", "expired_validity", "date_has_passed", i, text,
                         {**_answer(price, validity=None), "refused": True}, vendor=vendor))
    for i in range(190, 200):  # the second reader says "30 days" for a passed date
        vendor, price, lead, fr = _pick(i)
        text = reply(price, lead=lead, valid="until 2026-09-01", freight=fr)
        fresh = _regex(text).model_copy(update={"validity": "30 days"})
        out.append(_case("injected", "expired_validity", "reading_not_in_text", i, text,
                         {**_answer(price, validity=None), "refused": True}, reading=fresh,
                         vendor=vendor))
    for i in range(200, 210):  # the second reader says the date is next year (not in the text)
        vendor, price, lead, fr = _pick(i)
        text = reply(price, lead=lead, valid="until 2026-09-01", freight=fr)
        later = _regex(text).model_copy(update={"validity": "2027-09-01"})
        out.append(_case("injected", "expired_validity", "date_changed", i, text,
                         {**_answer(price, validity=None), "refused": True}, reading=later,
                         vendor=vendor))
    return out


_GENERATORS: tuple[Callable[[], list[Case]], ...] = (
    _decimal_slip, _wrong_pack, _vat_swap, _unit_swap, _wrong_currency, _transposed_quantity,
    _expired_validity,
)


def build_cases() -> tuple[Case, ...]:
    """Every case, injected first then clean, in a fixed order with unique ids."""
    cases = [c for gen in _GENERATORS for c in gen()] + _clean_variants()
    ids = [c.case_id for c in cases]
    if len(set(ids)) != len(ids):
        raise ValueError("case ids must be unique")
    return tuple(cases)


def set_hash(cases: tuple[Case, ...] | None = None) -> str:
    """SHA-256 of the canonical JSON of the whole set and the generator version."""
    body = json.dumps(
        {"version": GENERATOR_VERSION, "cases": [c.canonical() for c in cases or build_cases()]},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()
