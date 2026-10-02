"""Profile-driven money, tax basis and lead-time handling (offline, deterministic)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import yaml
from hypothesis import given
from hypothesis import strategies as st

from aiplat.profile import ResolvedProfile, load_profile
from components.core.domain import ExtractedQuote, Quote, Tier, Vendor
from components.imports import import_po_history
from components.rfq.comparison.compare import compare
from components.rfq.quotes.extractors import RegexQuoteExtractor
from components.rfq.quotes.grounding import ground
from components.rfq.quotes.normalise import (
    detect_tax_basis,
    inc_to_ex_tax,
    normalise_quote,
    parse_lead_time_days,
    working_days_to_calendar,
)

GOLDEN = Path(__file__).resolve().parents[2] / "evals" / "golden" / "money_cases.yaml"
FRI = date(2026, 10, 2)
UK = load_profile("uk")
US = load_profile("us")


def nq(ex: ExtractedQuote, profile: ResolvedProfile | None, **kw: Any) -> Quote:
    return normalise_quote(
        ex, quote_id="q1", tenant_id="t", rfq_id="r", vendor_id="v", offered_tier=Tier.A,
        dmarc_aligned=True, profile=profile, **kw,
    )


def with_holidays(profile: ResolvedProfile, holidays: list[date]) -> ResolvedProfile:
    loc = profile.profile.locale.model_copy(update={"holidays": tuple(holidays)})
    return profile.model_copy(
        update={"profile": profile.profile.model_copy(update={"locale": loc})}
    )


# ------------------------------------------------------------------ golden table

def _cases() -> list[dict[str, Any]]:
    return yaml.safe_load(GOLDEN.read_text(encoding="utf-8"))["cases"]


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c["id"])
def test_golden_money_case(case: dict[str, Any]) -> None:
    profile = load_profile(case["profile"])
    if case.get("holidays"):
        profile = with_holidays(profile, list(case["holidays"]))
    text = case["text"]
    grounded = ground(RegexQuoteExtractor().extract(text), text)
    q = nq(grounded.extracted, profile, received_on=case["start"],
           grounding_flags=grounded.flags, snippets=grounded.snippets)
    exp = case["expect"]
    assert q.currency == exp["currency"]
    if "tax_basis" in exp:
        assert q.tax_basis == exp["tax_basis"]
    if "unit_price_each" in exp:
        assert q.unit_price_each == Decimal(exp["unit_price_each"])
        assert isinstance(q.unit_price_each, Decimal)
    if "lead_time_days" in exp:
        assert q.lead_time_days == exp["lead_time_days"]
    for f in exp.get("flags", []):
        assert f in q.flags, (f, q.flags)
    for f in exp.get("absent_flags", []):
        assert f not in q.flags, (f, q.flags)


# ------------------------------------------------------------------ legacy equivalence

LEGACY_INPUTS = [
    ExtractedQuote(unit_price="4.20", currency="$", uom="each", lead_time="3 days"),
    ExtractedQuote(unit_price="£4.20 + VAT", lead_time="5 business days", freight="$12"),
    ExtractedQuote(unit_price="310", currency="USD", uom="per 100", lead_time="next day"),
    ExtractedQuote(unit_price="4.20", currency="CAD"),
    ExtractedQuote(unit_price="4.20", lead_time="2 calendar days"),
]


@pytest.mark.parametrize("ex", LEGACY_INPUTS)
def test_us_profile_equals_no_profile(ex: ExtractedQuote) -> None:
    assert nq(ex, US, received_on=FRI) == nq(ex, None, received_on=FRI)


# ------------------------------------------------------------------ tax basis

@pytest.mark.parametrize("text", ["+ VAT", "plus VAT", "ex VAT", "excl. VAT", "exc VAT",
                                  "ex-VAT", "exclusive of VAT"])
def test_ex_tax_wordings(text: str) -> None:
    assert detect_tax_basis(text) == "ex_tax"


@pytest.mark.parametrize("text", ["inc VAT", "incl. VAT", "including VAT", "VAT included",
                                  "inc. VAT", "VAT inclusive"])
def test_inc_tax_wordings(text: str) -> None:
    assert detect_tax_basis(text) == "inc_tax"


def test_conflicting_or_absent_wording_is_unknown() -> None:
    assert detect_tax_basis("ex VAT", "inc VAT") == "unknown"
    assert detect_tax_basis(None, "4.20") == "unknown"


def test_tax_text_from_field_converts() -> None:
    q = nq(ExtractedQuote(unit_price="£12.00", tax_text="inc. VAT"), UK)
    assert (q.unit_price_each, q.unit_price_quoted, q.tax_rate) == (
        Decimal("10.0000"), Decimal("12.00"), Decimal("0.20"))
    assert q.tax_basis == "inc_tax" and "tax_inc_converted" in q.flags


def test_price_text_with_vat_tail_parses() -> None:
    q = nq(ExtractedQuote(unit_price="£4.20 + VAT", uom="each"), UK)
    assert q.unit_price_each == Decimal("4.20") and q.tax_basis == "ex_tax"
    assert "unit_price_unparsed" not in q.flags


def test_unknown_basis_require_approval_policy() -> None:
    tax = UK.profile.tax.model_copy(update={"unknown_basis": "flag_require_approval"})
    prof = UK.model_copy(update={"profile": UK.profile.model_copy(update={"tax": tax})})
    q = nq(ExtractedQuote(unit_price="£4.20", currency="GBP"), prof)
    assert q.tax_basis == "unknown" and "tax_basis_unknown" in q.flags
    assert q.unit_price_each == Decimal("4.20") and "tax_basis_assumed" not in q.flags


def test_rounding_half_up() -> None:
    assert inc_to_ex_tax(Decimal("0.0001"), Decimal("0.20")) == Decimal("0.0001")
    assert inc_to_ex_tax(Decimal("1.00"), Decimal("0.20")) == Decimal("0.8333")
    assert inc_to_ex_tax(Decimal("1.0003"), Decimal("0.20")) == Decimal("0.8336")


@given(
    ex=st.decimals(min_value=Decimal("0.0100"), max_value=Decimal("100000"), places=4),
    rate=st.sampled_from([Decimal("0.05"), Decimal("0.20"), Decimal("0.075")]),
)
def test_inc_ex_roundtrip_within_rounding(ex: Decimal, rate: Decimal) -> None:
    inc = (ex * (1 + rate)).quantize(Decimal("0.0001"))
    back = inc_to_ex_tax(inc, rate)
    assert abs(back - ex) <= Decimal("0.0001")  # inc is rounded to 4dp, so error <= 1 ulp


# ------------------------------------------------------------------ currency

def test_uk_bare_dollar_is_ambiguous_not_assumed() -> None:
    q = nq(ExtractedQuote(unit_price="$4.20", uom="each"), UK)
    assert q.currency is None and "currency_ambiguous" in q.flags
    assert not any(f.startswith("currency_assumed") for f in q.flags)


def test_uk_assume_base_policy_flags() -> None:
    m = UK.profile.money.model_copy(update={"assumed_currency": "assume_base_flag"})
    prof = UK.model_copy(update={"profile": UK.profile.model_copy(update={"money": m})})
    q = nq(ExtractedQuote(unit_price="$4.20"), prof)
    assert q.currency == "GBP" and {"currency_ambiguous", "currency_assumed_gbp"} <= set(q.flags)


def test_uk_reject_policy_drops_price() -> None:
    m = UK.profile.money.model_copy(update={"assumed_currency": "reject"})
    prof = UK.model_copy(update={"profile": UK.profile.model_copy(update={"money": m})})
    q = nq(ExtractedQuote(unit_price="$4.20"), prof)
    assert q.unit_price_each is None and "currency_ambiguous" in q.flags


def test_uk_rejects_cad_symbol_us_accepts() -> None:
    ex = ExtractedQuote(unit_price="C$4.20")
    assert "currency_unrecognised" in nq(ex, UK).flags
    assert nq(ex, US).currency == "CAD"


# ------------------------------------------------------------------ lead time

def test_working_days_pure_function() -> None:
    assert working_days_to_calendar(2, FRI) == 4  # Fri -> Tue
    assert working_days_to_calendar(2, FRI, holidays=[date(2026, 10, 5)]) == 5
    assert working_days_to_calendar(0, FRI) == 0
    assert working_days_to_calendar(1, FRI, working_week=(0, 1, 2, 3, 4, 5)) == 1  # Saturday works


def test_lead_time_without_start_uses_approximation_and_flags() -> None:
    q = nq(ExtractedQuote(unit_price="£1", currency="GBP", lead_time="5 days"), UK)
    assert q.lead_time_days == 7 and "lead_time_working_days_assumed" in q.flags


def test_us_lead_time_untouched() -> None:
    assert parse_lead_time_days("3 days") == (3, ())
    assert parse_lead_time_days("next working day") == (None, ("lead_time_ambiguous",))


# ------------------------------------------------------------------ extractor + grounding

def test_extractor_tax_text_verbatim_and_grounded() -> None:
    src = "Hi,\nUnit price: £4.20 each + VAT\nRegards"
    ex = RegexQuoteExtractor().extract(src)
    assert ex.tax_text == "+ VAT"
    res = ground(ex, src)
    assert res.extracted.tax_text == "+ VAT" and res.snippets["tax_text"] == "+ VAT"


def test_ungrounded_tax_text_blanked() -> None:
    res = ground(ExtractedQuote(unit_price="4.20", tax_text="inc. VAT"), "Price 4.20 + VAT")
    assert res.extracted.tax_text is None and "ungrounded:tax_text" in res.flags


def test_extractor_conflicting_tax_wording_blank() -> None:
    src = "Price: £4.20 each + VAT\nTotal price £5.04 inc VAT"
    assert RegexQuoteExtractor().extract(src).tax_text is None


# ------------------------------------------------------------------ comparison

def _q(qid: str, price: str, *flags: str, tier: Tier = Tier.A) -> Quote:
    return Quote(id=qid, tenant_id="t", rfq_id="r", vendor_id=qid, version=1,
                 unit_price_each=Decimal(price), currency="GBP", offered_tier=tier,
                 flags=flags, freight=Decimal(0))


def test_clean_quote_preferred_over_cheaper_unknown_basis() -> None:
    cmp = compare("r", [_q("a", "1.00", "tax_basis_unknown"), _q("b", "2.00")],
                  need_by=None, today=FRI, quantity=10)
    assert cmp.recommended_quote_id == "b"
    assert "deprioritised:a:tax_basis_unknown" in cmp.reasons


def test_only_caveated_quote_recommended_with_reason() -> None:
    cmp = compare("r", [_q("a", "1.00", "tax_basis_unknown")], need_by=None, today=FRI, quantity=10)
    assert cmp.recommended_quote_id == "a" and "caveat:a:tax_basis_unknown" in cmp.reasons


def test_currency_ambiguous_never_recommended() -> None:
    q = normalise_quote(
        ExtractedQuote(unit_price="$4.20"), quote_id="a", tenant_id="t", rfq_id="r",
        vendor_id="a", offered_tier=Tier.A, dmarc_aligned=True, profile=UK)
    cmp = compare("r", [q], need_by=None, today=FRI, quantity=10)
    assert cmp.recommended_quote_id is None and "excluded:a:no_currency" in cmp.reasons


def test_tier_still_beats_clean() -> None:
    cmp = compare("r", [_q("a", "9", "tax_basis_unknown"), _q("b", "1", tier=Tier.B)],
                  need_by=None, today=FRI, quantity=1)
    assert cmp.recommended_quote_id == "a"


# ------------------------------------------------------------------ imports

CSV_UK = (
    "po_number,vendor,part_number,quantity,unit_price,currency,uom,po_date\n"
    "P1,Acme Ltd,6205,10,£4.20,,each,25/12/2025\n"
    "P2,Acme Ltd,6205,10,$4.20,,each,2025-12-25\n"
    "P3,Acme Ltd,6205,10,4.20,CAD,each,2025-12-25\n"
    "P4,Acme Ltd,6205,10,€4.20,GBP,each,2025-12-25\n"
)
VENDORS = [Vendor(id="v1", tenant_id="t", name="Acme Ltd", domain="acme.example", contact_email="s@acme.example")]


def test_import_uses_profile_currency_symbols_and_dates() -> None:
    res = import_po_history(CSV_UK.encode(), VENDORS, profile=UK)
    assert [(r.currency, r.unit_price, r.po_date) for r in res.accepted] == [
        ("GBP", Decimal("4.20"), date(2025, 12, 25))]
    reasons = {e.row: e.reason for e in res.errors}
    assert reasons == {3: "currency_ambiguous", 4: "unknown_currency", 5: "currency_conflict"}


def test_import_default_is_legacy() -> None:
    res = import_po_history(CSV_UK.encode(), VENDORS)
    assert {e.row: e.reason for e in res.errors} == {2: "currency_required", 3: "currency_required"}
    assert [r.currency for r in res.accepted] == ["CAD", "GBP"]  # legacy: CAD accepted
