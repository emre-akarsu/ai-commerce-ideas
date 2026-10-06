"""Delivery terms compiled to an integer step function on the comparison basis. Thresholds on a
different VAT basis are compared exactly (no rounded threshold), fees are rounded once."""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from components.pricing import DeliveryTerms, DeliveryTier, VatBasis
from components.pricing.delivery import FeeSchedule, combine, compile_terms

from .cfg import config

D = Decimal
PROP = settings(max_examples=250, deadline=None, derandomize=True, database=None,
                suppress_health_check=[HealthCheck.too_slow])
EX, INC, UNK = VatBasis.EX_TAX, VatBasis.INC_TAX, VatBasis.UNKNOWN


def sched(terms: DeliveryTerms, price_basis: VatBasis = EX, **kw: object) -> FeeSchedule:
    out = compile_terms(terms, price_basis, config(**kw))  # type: ignore[arg-type]
    assert out is not None
    return out


def test_flat_fee_is_one_band() -> None:
    s = sched(DeliveryTerms(flat_fee=D("5.95")))
    assert s.bands == ((0, 595),)
    assert s.fee(D("0.01")) == s.fee(D("9999.99")) == D("5.95")


def test_free_over_is_strictly_over_in_whole_minor_units() -> None:
    s = sched(DeliveryTerms(flat_fee=D("5.95"), free_over=D("50")))
    assert s.bands == ((0, 595), (5001, 0))
    assert s.fee(D("50.00")) == D("5.95") and s.fee(D("50.01")) == D("0.00")


def test_tiers_apply_from_their_minimum_inclusive() -> None:
    s = sched(DeliveryTerms(tiers=(DeliveryTier(D("0"), D("9.95")),
                                   DeliveryTier(D("50"), D("4.95")),
                                   DeliveryTier(D("150"), D("0")))))
    assert s.bands == ((0, 995), (5000, 495), (15000, 0))
    assert [s.fee_minor(m) for m in (1, 4999, 5000, 14999, 15000)] == [995, 995, 495, 495, 0]


def test_thresholds_and_fees_on_the_vat_inclusive_basis_are_converted_exactly() -> None:
    # terms stated inc VAT, comparison ex VAT: "free over 60.00 inc" = spend ex > 50.00
    s = sched(DeliveryTerms(flat_fee=D("7.20"), free_over=D("60")), INC)
    assert s.bands == ((0, 600), (5001, 0))


def test_a_threshold_that_does_not_convert_to_whole_pence_is_not_rounded_wrongly() -> None:
    # "free over 50.00 inc VAT" is spend ex > 41.6666...: 41.66 pays, 41.67 does not
    s = sched(DeliveryTerms(flat_fee=D("6"), free_over=D("50")), INC)
    assert s.bands == ((0, 500), (4167, 0))
    assert s.fee(D("41.66")) == D("5.00") and s.fee(D("41.67")) == D("0.00")


def test_ex_vat_terms_with_an_inc_vat_comparison() -> None:
    # "free over 50.00 ex" = spend inc > 60.00; a 5.00 ex fee is 6.00 inc
    cfg = config(pricing={"compare_basis": "inc_tax"})
    out = compile_terms(DeliveryTerms(flat_fee=D("5"), free_over=D("50")), EX, cfg)
    assert out is not None and out.bands == ((0, 600), (6001, 0))


def test_fee_conversion_rounds_once_half_up() -> None:
    s = sched(DeliveryTerms(flat_fee=D("4.99")), INC)  # 4.99 / 1.2 = 4.158333...
    assert s.bands == ((0, 416),)


def test_terms_with_their_own_basis_override_the_price_basis() -> None:
    terms = DeliveryTerms(flat_fee=D("6"), vat_basis=INC)
    assert sched(terms, EX).bands == ((0, 500),)
    assert sched(DeliveryTerms(flat_fee=D("6")), INC).bands == ((0, 500),)  # inherits
    assert sched(DeliveryTerms(flat_fee=D("6")), EX).bands == ((0, 600),)


def test_an_unknown_delivery_basis_cannot_be_compared_unless_no_tax_is_configured() -> None:
    cfg = config()
    assert compile_terms(DeliveryTerms(flat_fee=D("6"), vat_basis=UNK), EX, cfg) is None
    assert compile_terms(DeliveryTerms(flat_fee=D("6")), UNK, cfg) is None
    no_tax = config(tax={"standard_rate": "0"})
    assert compile_terms(DeliveryTerms(flat_fee=D("6"), vat_basis=UNK), UNK, no_tax) is not None


def test_no_tax_configured_means_no_conversion() -> None:
    no_tax = config(tax={"standard_rate": "0"})
    out = compile_terms(DeliveryTerms(flat_fee=D("6"), free_over=D("60")), INC, no_tax)
    assert out is not None and out.bands == ((0, 600), (6001, 0))


def test_fee_requires_a_money_amount() -> None:
    s = sched(DeliveryTerms(flat_fee=D("5")))
    with pytest.raises(ValueError):
        s.fee(D("1.005"))
    with pytest.raises(ValueError):
        s.fee_minor(-1)


def test_places_follow_the_configured_minor_unit() -> None:
    s = sched(DeliveryTerms(flat_fee=D("5"), free_over=D("50")), minor_unit_places=0)
    assert s.bands == ((0, 5), (51, 0)) and s.fee(D("51")) == D("0")


@PROP
@given(st.integers(0, 3000), st.integers(0, 3000), st.integers(1, 100_000),
       st.integers(0, 200_000))
def test_compiled_schedule_agrees_with_direct_evaluation_of_the_terms(
    flat_c: int, tier_c: int, thr_c: int, spend_c: int
) -> None:
    flat, spend = D(flat_c).scaleb(-2), D(spend_c).scaleb(-2)
    free = DeliveryTerms(flat_fee=flat, free_over=D(thr_c).scaleb(-2))
    tiers = DeliveryTerms(tiers=(DeliveryTier(D(0), flat),
                                 DeliveryTier(D(thr_c).scaleb(-2), D(tier_c).scaleb(-2))))
    for terms in (DeliveryTerms(flat_fee=flat), free, tiers):
        s = sched(terms)
        if spend_c > 0:
            assert s.fee(spend) == terms.fee_for(spend)


@PROP
@given(st.integers(0, 3000), st.integers(1, 100_000), st.integers(1, 200_000),
       st.sampled_from([INC, EX]))
def test_converted_thresholds_agree_with_exact_rational_evaluation(
    flat_c: int, thr_c: int, spend_c: int, basis: VatBasis
) -> None:
    """For terms on the other VAT basis, the integer schedule equals evaluating the terms at the
    exactly converted spend, then rounding the converted fee once."""
    flat, thr = D(flat_c).scaleb(-2), D(thr_c).scaleb(-2)
    terms = DeliveryTerms(flat_fee=flat, free_over=thr)
    cmp_basis = EX if basis is INC else INC
    cfg = config(pricing={"compare_basis": cmp_basis.value})
    s = compile_terms(terms, basis, cfg)
    assert s is not None
    rate = Fraction(1) + Fraction(D("0.20"))
    spend_cmp = Fraction(spend_c, 100)
    spend_terms = spend_cmp / rate if cmp_basis is INC else spend_cmp * rate
    exact_fee = Fraction(flat) if spend_terms <= Fraction(thr) else Fraction(0)
    fee_cmp = exact_fee * rate if cmp_basis is INC else exact_fee / rate
    expected = (2 * fee_cmp * 100 + 1) // 2
    assert s.fee_minor(spend_c) == int(expected)


# ---------------------------------------------------------------- combining and bounds


def test_combine_takes_the_larger_fee_at_every_spend() -> None:
    a = sched(DeliveryTerms(flat_fee=D("5"), free_over=D("50")))
    b = sched(DeliveryTerms(flat_fee=D("3"), free_over=D("20")))
    c = combine([a, b])
    for m in (1, 1999, 2000, 2001, 5000, 5001, 9999):
        assert c.fee_minor(m) == max(a.fee_minor(m), b.fee_minor(m))
    assert combine([a]) == a


@PROP
@given(st.lists(st.tuples(st.integers(0, 2000), st.integers(1, 20_000)), min_size=1, max_size=4),
       st.integers(1, 30_000))
def test_combined_schedule_is_the_pointwise_maximum(
    specs: list[tuple[int, int]], spend_c: int
) -> None:
    parts = [sched(DeliveryTerms(flat_fee=D(f).scaleb(-2), free_over=D(t).scaleb(-2)))
             for f, t in specs]
    assert combine(parts).fee_minor(spend_c) == max(p.fee_minor(spend_c) for p in parts)


@PROP
@given(st.integers(0, 3000), st.integers(1, 3000), st.integers(1, 400), st.integers(0, 400))
def test_min_fee_between_is_the_true_minimum_over_the_range(
    flat_c: int, thr_c: int, lo: int, span: int
) -> None:
    s = sched(DeliveryTerms(flat_fee=D(flat_c).scaleb(-2), free_over=D(thr_c).scaleb(-2)))
    hi = lo + span
    assert s.min_fee_between(lo, hi) == min(s.fee_minor(m) for m in range(lo, hi + 1))
