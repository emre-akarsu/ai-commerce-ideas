"""VAT: conversion to the configured comparison basis with the configured rate (never 20% in code),
and "unknown basis goes to a human" (excluded from best-price selection)."""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from components.pricing import Price, VatBasis
from components.pricing.vat import convert, resolve_basis, split_total

from .cfg import config

D = Decimal
PROP = settings(max_examples=200, deadline=None, derandomize=True, database=None,
                suppress_health_check=[HealthCheck.too_slow])


def price(basis: VatBasis, rate: Decimal | None = None) -> Price:
    return Price(amount=D("10"), currency="GBP", vat_basis=basis, vat_rate=rate)


# ---------------------------------------------------------------- conversion


def test_inc_to_ex_and_back_use_the_configured_rate() -> None:
    assert convert(Fraction(12), VatBasis.INC_TAX, VatBasis.EX_TAX, D("0.20")) == Fraction(10)
    assert convert(Fraction(10), VatBasis.EX_TAX, VatBasis.INC_TAX, D("0.20")) == Fraction(12)
    assert convert(Fraction(105), VatBasis.INC_TAX, VatBasis.EX_TAX, D("0.05")) == Fraction(100)
    assert convert(Fraction(7), VatBasis.INC_TAX, VatBasis.INC_TAX, D("0.20")) == Fraction(7)


def test_conversion_is_exact_not_rounded() -> None:
    assert convert(Fraction(999, 100), VatBasis.INC_TAX, VatBasis.EX_TAX, D("0.20")) == (
        Fraction(8325, 1000))
    third = convert(Fraction(1), VatBasis.INC_TAX, VatBasis.EX_TAX, D("0.20"))
    assert third == Fraction(5, 6)  # an exact rational, no rounding at all


@PROP
@given(st.integers(1, 10**7), st.integers(0, 50))
def test_round_trip_is_exact(cents: int, rate_pct: int) -> None:
    rate = D(rate_pct) / D(100)
    x = Fraction(cents, 100)
    ex = convert(x, VatBasis.INC_TAX, VatBasis.EX_TAX, rate)
    assert convert(ex, VatBasis.EX_TAX, VatBasis.INC_TAX, rate) == x


def test_unknown_basis_cannot_be_converted() -> None:
    with pytest.raises(ValueError):
        convert(Fraction(1), VatBasis.UNKNOWN, VatBasis.EX_TAX, D("0.20"))


# ---------------------------------------------------------------- basis resolution


def test_known_basis_is_used_as_stated() -> None:
    cfg = config()
    for basis in (VatBasis.EX_TAX, VatBasis.INC_TAX):
        out = resolve_basis(price(basis), cfg)
        assert out.basis is basis and out.exclusion is None and out.flags == ()


def test_an_unknown_basis_is_flagged_and_excluded_so_it_goes_to_a_human() -> None:
    out = resolve_basis(price(VatBasis.UNKNOWN), config())
    assert out.basis is VatBasis.UNKNOWN
    assert out.exclusion == "vat_basis_unknown" and "vat_basis_unknown" in out.flags


def test_assume_default_policy_assumes_the_profile_default_and_says_so() -> None:
    cfg = config(tax={"unknown_basis": "assume_default_flag", "quote_basis_default": "inc_tax"})
    out = resolve_basis(price(VatBasis.UNKNOWN), cfg)
    assert out.basis is VatBasis.INC_TAX and out.exclusion is None
    assert out.flags == ("vat_basis_assumed",)


def test_assume_default_without_a_default_still_goes_to_a_human() -> None:
    cfg = config(tax={"unknown_basis": "assume_default_flag", "quote_basis_default": "unknown"})
    out = resolve_basis(price(VatBasis.UNKNOWN), cfg)
    assert out.exclusion == "vat_basis_unknown"


def test_with_a_zero_rate_there_is_no_vat_handling_at_all() -> None:
    cfg = config(tax={"standard_rate": "0"})
    out = resolve_basis(price(VatBasis.UNKNOWN), cfg)
    assert out.exclusion is None and out.flags == ()
    assert out.basis.value == cfg.compare_basis  # nothing to convert


def test_a_stated_rate_that_differs_blocks_conversion_but_not_a_same_basis_price() -> None:
    cfg = config()  # 20%, ex_tax comparison
    inc_5 = resolve_basis(price(VatBasis.INC_TAX, D("0.05")), cfg)
    assert inc_5.exclusion == "vat_rate_mismatch" and "vat_rate_mismatch" in inc_5.flags
    ex_5 = resolve_basis(price(VatBasis.EX_TAX, D("0.05")), cfg)  # no conversion needed
    assert ex_5.exclusion is None and ex_5.flags == ()
    same = resolve_basis(price(VatBasis.INC_TAX, D("0.20")), cfg)
    assert same.exclusion is None


def test_comparison_basis_decides_whether_a_conversion_is_needed() -> None:
    inc_cfg = config(pricing={"compare_basis": "inc_tax"})
    assert resolve_basis(price(VatBasis.INC_TAX, D("0.05")), inc_cfg).exclusion is None
    assert resolve_basis(price(VatBasis.EX_TAX, D("0.05")), inc_cfg).exclusion == (
        "vat_rate_mismatch")


# ---------------------------------------------------------------- presenting a total


def test_split_total_on_an_ex_tax_basis() -> None:
    s = split_total(D("100.00"), VatBasis.EX_TAX, D("0.20"), 2)
    assert (s.net, s.vat, s.gross) == (D("100.00"), D("20.00"), D("120.00"))


def test_split_total_on_an_inc_tax_basis() -> None:
    s = split_total(D("120.00"), VatBasis.INC_TAX, D("0.20"), 2)
    assert (s.net, s.vat, s.gross) == (D("100.00"), D("20.00"), D("120.00"))


def test_split_total_rounds_once_half_up_and_always_adds_up() -> None:
    inc = split_total(D("99.99"), VatBasis.INC_TAX, D("0.20"), 2)  # 83.325 -> 83.33
    assert (inc.net, inc.vat, inc.gross) == (D("83.33"), D("16.66"), D("99.99"))
    ex = split_total(D("83.33"), VatBasis.EX_TAX, D("0.20"), 2)  # 16.666 -> 16.67
    assert (ex.net, ex.vat, ex.gross) == (D("83.33"), D("16.67"), D("100.00"))


@PROP
@given(st.integers(0, 10**9), st.integers(0, 50), st.sampled_from([VatBasis.EX_TAX,
                                                                    VatBasis.INC_TAX]))
def test_split_total_is_exact_in_money_and_net_plus_vat_is_gross(
    cents: int, rate_pct: int, basis: VatBasis
) -> None:
    total = D(cents).scaleb(-2)
    s = split_total(total, basis, D(rate_pct) / D(100), 2)
    assert s.net + s.vat == s.gross
    assert all(x.as_tuple().exponent == -2 for x in (s.net, s.vat, s.gross))
    assert (s.net if basis is VatBasis.EX_TAX else s.gross) == total


def test_split_total_normalises_the_exponent_and_refuses_to_round_its_input() -> None:
    s = split_total(D("100"), VatBasis.EX_TAX, D("0.20"), 2)
    assert str(s.net) == "100.00" and str(s.vat) == "20.00" and str(s.gross) == "120.00"
    with pytest.raises(ValueError):
        split_total(D("100.005"), VatBasis.EX_TAX, D("0.20"), 2)
    with pytest.raises(ValueError):
        split_total(D("1"), VatBasis.UNKNOWN, D("0.20"), 2)
