"""Freshness (per-source-kind age limits from config) and sanity (outliers vs the median of
comparable offers, optional external index band)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from components.pricing import IndexBand, SourceKind, Unit, VatBasis
from components.pricing.freshness import assess_freshness
from components.pricing.sanity import find_outliers, index_band_flag

from .cfg import NOW, config
from .factories import offer

D = Decimal
PROP = settings(max_examples=200, deadline=None, derandomize=True, database=None,
                suppress_health_check=[HealthCheck.too_slow])


# ---------------------------------------------------------------- freshness


@pytest.mark.parametrize(
    ("kind", "limit"),
    [(SourceKind.TRADE_FEED, 168), (SourceKind.MERCHANT_API, 24), (SourceKind.AFFILIATE_FEED, 48),
     (SourceKind.SEARCH_SNAPSHOT, 24), (SourceKind.MANUAL_QUOTE, 720)],
)
def test_each_source_kind_has_its_own_age_limit_and_the_limit_itself_is_still_fresh(
    kind: SourceKind, limit: int
) -> None:
    cfg = config()
    at_limit = assess_freshness(offer(kind=kind, age_hours=limit), cfg, NOW)
    assert at_limit.max_age_hours == limit and not at_limit.stale
    just_over = offer(kind=kind, observed_at=NOW - timedelta(hours=limit, seconds=1))
    assert assess_freshness(just_over, cfg, NOW).stale


def test_limits_come_from_the_configuration() -> None:
    cfg = config(pricing={"max_offer_age_hours": {"merchant_api": 2}})
    assert assess_freshness(offer(age_hours=3), cfg, NOW).stale
    assert not assess_freshness(offer(age_hours=2), cfg, NOW).stale


def test_expiry_uses_valid_until_and_is_independent_of_age() -> None:
    cfg = config()
    o = offer(age_hours=1, valid_until=NOW - timedelta(seconds=1))
    assert assess_freshness(o, cfg, NOW).expired and not assess_freshness(o, cfg, NOW).stale
    assert not assess_freshness(offer(valid_until=NOW), cfg, NOW).expired
    assert not assess_freshness(offer(), cfg, NOW).expired


def test_an_offer_dated_in_the_future_is_flagged_beyond_the_clock_skew_allowance() -> None:
    cfg = config()
    inside = offer(observed_at=NOW + timedelta(minutes=5))
    assert not assess_freshness(inside, cfg, NOW).from_future
    assert assess_freshness(inside, cfg, NOW).age == timedelta(0)
    assert assess_freshness(offer(observed_at=NOW + timedelta(minutes=6)), cfg, NOW).from_future
    wide = config(future_skew_minutes=60)
    assert not assess_freshness(offer(observed_at=NOW + timedelta(minutes=59)), wide, NOW).from_future


def test_now_must_be_timezone_aware() -> None:
    with pytest.raises(ValueError):
        assess_freshness(offer(), config(), datetime(2026, 10, 5, 9, 0))
    assert assess_freshness(offer(), config(), NOW.astimezone(UTC)).age == timedelta(hours=1)


# ---------------------------------------------------------------- outliers


def prices(*values: str) -> dict[str, Decimal]:
    return {f"o{i}": D(v) for i, v in enumerate(values)}


def test_a_price_far_above_the_median_is_a_high_outlier() -> None:
    assert find_outliers(prices("10", "11", "100"), config()) == {"o2": "price_outlier_high"}


def test_a_price_far_below_the_median_is_a_low_outlier() -> None:
    assert find_outliers(prices("1", "10", "11"), config()) == {"o0": "price_outlier_low"}


def test_exactly_at_the_ratio_is_not_an_outlier() -> None:
    # ratio 3: with median 10, 30 is not above 30; with median 9, 3 is not below 9 / 3
    assert find_outliers(prices("10", "10", "30"), config()) == {}
    assert find_outliers(prices("10", "10", "30.000001"), config()) == {"o2": "price_outlier_high"}
    assert find_outliers(prices("9", "9", "3"), config()) == {}
    assert find_outliers(prices("9", "9", "2.99"), config()) == {"o2": "price_outlier_low"}


def test_even_counts_use_the_exact_mean_of_the_middle_pair() -> None:
    # middle pair 10 and 11 -> median 10.5; ratio 3 -> limit 31.5
    assert find_outliers(prices("9", "10", "11", "31.5"), config()) == {}
    assert find_outliers(prices("9", "10", "11", "31.51"), config()) == {"o3": "price_outlier_high"}


def test_too_few_comparable_offers_means_no_judgement() -> None:
    assert find_outliers(prices("1", "100"), config()) == {}
    assert find_outliers(prices("1"), config()) == {}
    assert find_outliers({}, config()) == {}
    assert find_outliers(prices("1", "100"), config(outlier_min_peers=2)) != {}


def test_the_ratio_and_peer_count_come_from_the_configuration() -> None:
    tight = config(pricing={"price_outlier_ratio": "1.5"})
    assert find_outliers(prices("10", "10", "16"), tight) == {"o2": "price_outlier_high"}
    assert find_outliers(prices("10", "10", "16"), config()) == {}


@PROP
@given(st.lists(st.integers(1, 10**6), min_size=3, max_size=12), st.integers(1, 1000))
def test_outlier_detection_is_scale_free_and_order_free(cents: list[int], k: int) -> None:
    base = {f"o{i}": D(c) / 100 for i, c in enumerate(cents)}
    scaled = {name: v * k for name, v in base.items()}
    shuffled = dict(reversed(list(base.items())))
    cfg = config()
    assert find_outliers(base, cfg) == find_outliers(scaled, cfg) == find_outliers(shuffled, cfg)


# ---------------------------------------------------------------- index band (relative only)


def band(ref: str = "4", ratio: str = "1", tol: str = "1.5", basis: VatBasis = VatBasis.EX_TAX,
         unit: Unit = Unit.M2, currency: str = "GBP") -> IndexBand:
    return IndexBand(reference_unit_price=D(ref), unit=unit, currency=currency, vat_basis=basis,
                     source="synthetic-last-paid", tolerance=D(tol), index_ratio=D(ratio))


def test_a_price_inside_the_scaled_reference_band_passes_and_the_edges_are_inclusive() -> None:
    cfg = config()  # expected 4 x 1.05 = 4.20; factor 1.5 -> 2.80 .. 6.30
    b = band(ratio="1.05")
    for p in ("2.80", "4.2", "6.30"):
        assert index_band_flag(D(p), Unit.M2, b, cfg) is None


def test_outside_the_band_is_flagged_low_or_high() -> None:
    cfg = config()
    b = band(ratio="1.05")
    assert index_band_flag(D("2.79"), Unit.M2, b, cfg) == "index_band_low"
    assert index_band_flag(D("6.31"), Unit.M2, b, cfg) == "index_band_high"


def test_the_index_only_moves_the_reference_it_never_sets_a_level() -> None:
    cfg = config()
    flat = band(ratio="1")  # 4.00 +/- 1.5x: 2.6667 .. 6.00
    assert index_band_flag(D("6.01"), Unit.M2, flat, cfg) == "index_band_high"
    assert index_band_flag(D("6.01"), Unit.M2, band(ratio="1.1"), cfg) is None  # prices rose 10%


def test_a_reference_on_another_vat_basis_is_compared_exactly_on_that_basis() -> None:
    cfg = config()  # offers compare ex VAT; the reference was paid inc VAT: 4.80, factor 1.5
    inc = band("4.80", "1", "1.5", VatBasis.INC_TAX)  # inc band 3.20 .. 7.20 = ex 2.6667 .. 6.00
    assert index_band_flag(D("6"), Unit.M2, inc, cfg) is None
    assert index_band_flag(D("6.0001"), Unit.M2, inc, cfg) == "index_band_high"
    assert index_band_flag(D("2.6667"), Unit.M2, inc, cfg) is None
    assert index_band_flag(D("2.6666"), Unit.M2, inc, cfg) == "index_band_low"


def test_a_band_for_another_unit_or_currency_does_not_apply() -> None:
    cfg = config()
    assert index_band_flag(D("100"), Unit.M2, band(unit=Unit.KG), cfg) is None
    assert index_band_flag(D("100"), Unit.M2, band(currency="EUR"), cfg) is None
    assert index_band_flag(D("100"), Unit.M2, None, cfg) is None


def test_with_no_tax_configured_the_bases_are_not_converted() -> None:
    cfg = config(tax={"standard_rate": "0"})
    inc = band("4.80", "1", "1.5", VatBasis.INC_TAX)
    assert index_band_flag(D("7.2"), Unit.M2, inc, cfg) is None
    assert index_band_flag(D("7.21"), Unit.M2, inc, cfg) == "index_band_high"
