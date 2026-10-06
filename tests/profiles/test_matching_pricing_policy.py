"""Profile checks for the stage-2 product matching gate and offer pricing policy."""

from __future__ import annotations

from decimal import Decimal

import pytest

from aiplat.profile import (
    MatchingPolicy,
    PricingPolicy,
    ProfileError,
    load_profile,
    resolve,
)

ALL = ("uk", "uk-scotland", "uk-ni", "us")


@pytest.mark.parametrize("pid", ALL)
def test_every_profile_carries_the_v1_matching_defaults(pid: str) -> None:
    m = load_profile(pid).profile.matching
    assert (m.auto_accept_min_score, m.auto_accept_min_lead, m.reject_below_score) == (
        Decimal("0.75"), Decimal("0.05"), Decimal("0.35"))
    assert (m.retrieve_top_k, m.judge_top_k, m.judge_examples, m.review_show_top) == (50, 5, 3, 3)
    assert m.require_zero_failed_checks is True and m.quantity_size_ambiguity_forces_review is True


@pytest.mark.parametrize("pid", ALL)
def test_search_snapshots_are_off_and_stale_offers_never_win(pid: str) -> None:
    p = load_profile(pid).profile.pricing
    assert p.allow_search_snapshot_sources is False
    assert p.stale_offers == "exclude_from_best"
    assert p.compare_basis == "ex_tax"
    assert p.max_offer_age_hours["search_snapshot"] <= p.max_offer_age_hours["merchant_api"]


def test_thresholds_must_be_ordered() -> None:
    with pytest.raises(ValueError):
        MatchingPolicy(reject_below_score=Decimal("0.7"), auto_accept_min_score=Decimal("0.6"))
    with pytest.raises(ValueError):
        MatchingPolicy(judge_top_k=10, retrieve_top_k=5)


def test_the_attribute_check_gate_has_no_off_switch() -> None:
    with pytest.raises(ValueError):
        MatchingPolicy(require_zero_failed_checks=False)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        MatchingPolicy(quantity_size_ambiguity_forces_review=False)  # type: ignore[arg-type]


def test_offer_age_limits_reject_unknown_kinds_and_silly_values() -> None:
    with pytest.raises(ValueError):
        PricingPolicy(max_offer_age_hours={"scraper": 5})
    with pytest.raises(ValueError):
        PricingPolicy(max_offer_age_hours={"trade_feed": 0})


def test_a_tenant_cannot_loosen_the_gate_or_enable_snapshots() -> None:
    from aiplat.profile import PROFILES_DIR, _chain

    chain = _chain("uk", PROFILES_DIR)
    for key in ({"matching": {"auto_accept_min_score": "0.6"}},
                {"pricing": {"allow_search_snapshot_sources": True}}):
        with pytest.raises(ProfileError):
            resolve(chain, tenant_overrides=key, tenant_id="t1")
