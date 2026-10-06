"""PricingConfig: a plain dataclass the caller builds from the resolved profile. Components never
import aiplat, so the profile defaults are mirrored here and a conformance test keeps them equal."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from aiplat.profile import PROFILES_DIR, MoneyPolicy, PricingPolicy, TaxPolicy, load_profile
from components.pricing import PricingConfig, SourceKind
from components.pricing.errors import PricingConfigError

from .cfg import config_mapping

D = Decimal
MIN_MONEY = {"money": {"base_currency": "GBP", "accepted_currencies": ["GBP"]}}
PROFILE_IDS = sorted(
    p.stem for p in PROFILES_DIR.glob("*.yaml") if p.stem != "base" and not p.stem.startswith("_")
)


def test_defaults_equal_the_profile_defaults() -> None:
    cfg = PricingConfig.from_mapping(MIN_MONEY)
    pol, tax = PricingPolicy(), TaxPolicy()
    assert {k.value: v for k, v in cfg.max_offer_age_hours.items()} == pol.max_offer_age_hours
    assert cfg.stale_offers == pol.stale_offers
    assert cfg.compare_basis == pol.compare_basis
    assert cfg.include_delivery_in_comparison is pol.include_delivery_in_comparison
    assert cfg.price_outlier_ratio == pol.price_outlier_ratio
    assert cfg.allow_search_snapshot_sources is pol.allow_search_snapshot_sources
    assert cfg.vat_rate == tax.standard_rate == D("0")  # never a hard-coded 20%
    assert cfg.unknown_basis == tax.unknown_basis
    assert cfg.quote_basis_default == tax.quote_basis_default


def test_the_only_required_input_is_the_base_currency() -> None:
    with pytest.raises(PricingConfigError, match="base_currency"):
        PricingConfig.from_mapping({})
    with pytest.raises(PricingConfigError, match="base_currency"):
        PricingConfig.from_mapping({"money": {"accepted_currencies": ["GBP"]}})
    cfg = PricingConfig.from_mapping({"money": {"base_currency": "GBP"}})
    assert cfg.accepted_currencies == frozenset({"GBP"})  # base is always accepted


def test_base_currency_must_be_accepted_and_iso_shaped() -> None:
    with pytest.raises(PricingConfigError):
        PricingConfig.from_mapping({"money": {"base_currency": "GBP",
                                              "accepted_currencies": ["EUR"]}})
    with pytest.raises(PricingConfigError):
        PricingConfig.from_mapping({"money": {"base_currency": "gbp"}})
    with pytest.raises(PricingConfigError):
        PricingConfig.from_mapping({"money": {"base_currency": "GBP",
                                              "accepted_currencies": ["GBP", "pounds"]}})


@pytest.mark.parametrize("bad", [0.2, 0.20, True, [], "twenty", "-0.1", "0.51", "NaN", "Infinity"])
def test_vat_rate_must_be_a_bounded_decimal_never_a_float(bad: Any) -> None:
    with pytest.raises(PricingConfigError):
        PricingConfig.from_mapping({**MIN_MONEY, "tax": {"standard_rate": bad}})


def test_vat_rate_accepts_decimal_string_and_decimal() -> None:
    a = PricingConfig.from_mapping({**MIN_MONEY, "tax": {"standard_rate": "0.20"}})
    b = PricingConfig.from_mapping({**MIN_MONEY, "tax": {"standard_rate": D("0.20")}})
    assert a.vat_rate == b.vat_rate == D("0.20")


@pytest.mark.parametrize(
    "section",
    [{"pricing": {"stale_offers": "ignore"}}, {"pricing": {"compare_basis": "gross"}},
     {"pricing": {"price_outlier_ratio": "1.2"}}, {"pricing": {"price_outlier_ratio": "11"}},
     {"pricing": {"price_outlier_ratio": 3.0}}, {"pricing": {"unknown_key": 1}},
     {"pricing": {"max_offer_age_hours": {"scraper": 5}}},
     {"pricing": {"max_offer_age_hours": {"trade_feed": 0}}},
     {"pricing": {"max_offer_age_hours": {"trade_feed": 8761}}},
     {"pricing": {"max_offer_age_hours": {"trade_feed": 1.5}}},
     {"pricing": {"allow_search_snapshot_sources": "yes"}},
     {"pricing": {"include_delivery_in_comparison": 1}},
     {"tax": {"unknown_basis": "guess"}}, {"tax": {"quote_basis_default": "gross"}},
     {"engine": {"outlier_min_peers": 1}}, {"engine": {"minor_unit_places": 7}},
     {"engine": {"basket_exact_max_lines": 0}}, {"engine": {"nonsense": 1}},
     {"engine": {"outlier_offers": "drop"}}],
)
def test_invalid_values_and_unknown_keys_are_rejected(section: dict[str, Any]) -> None:
    with pytest.raises(PricingConfigError):
        PricingConfig.from_mapping({**MIN_MONEY, **section})


def test_partial_age_limits_fall_back_to_the_defaults_so_no_kind_is_unlimited() -> None:
    cfg = PricingConfig.from_mapping(
        {**MIN_MONEY, "pricing": {"max_offer_age_hours": {"trade_feed": 100}}}
    )
    assert cfg.max_age_hours(SourceKind.TRADE_FEED) == 100
    assert cfg.max_age_hours(SourceKind.MERCHANT_API) == 24
    assert set(cfg.max_offer_age_hours) == set(SourceKind)


def test_config_is_immutable_and_does_not_alias_the_input() -> None:
    raw = {**MIN_MONEY, "pricing": {"max_offer_age_hours": {"trade_feed": 100}}}
    cfg = PricingConfig.from_mapping(raw)
    raw["pricing"]["max_offer_age_hours"]["trade_feed"] = 1  # type: ignore[index]
    assert cfg.max_age_hours(SourceKind.TRADE_FEED) == 100
    with pytest.raises(AttributeError):
        cfg.vat_rate = D("0.5")  # type: ignore[misc]
    with pytest.raises(TypeError):
        cfg.max_offer_age_hours[SourceKind.TRADE_FEED] = 5  # type: ignore[index]


@pytest.mark.parametrize("pid", PROFILE_IDS)
def test_every_profile_dump_builds_a_config_that_mirrors_it(pid: str) -> None:
    """Conformance: the whole resolved profile (python or json dump) is accepted as-is and every
    pricing-relevant value is carried over, so profile and component cannot drift apart."""
    prof = load_profile(pid).profile
    for dump in (prof.model_dump(), prof.model_dump(mode="json")):
        cfg = PricingConfig.from_mapping(dump)
        assert cfg.base_currency == prof.money.base_currency
        assert cfg.accepted_currencies == frozenset(prof.money.accepted_currencies)
        assert cfg.vat_rate == prof.tax.standard_rate
        assert cfg.unknown_basis == prof.tax.unknown_basis
        assert cfg.quote_basis_default == prof.tax.quote_basis_default
        assert cfg.compare_basis == prof.pricing.compare_basis
        assert cfg.stale_offers == prof.pricing.stale_offers
        assert cfg.price_outlier_ratio == prof.pricing.price_outlier_ratio
        assert cfg.allow_search_snapshot_sources is prof.pricing.allow_search_snapshot_sources
        assert cfg.include_delivery_in_comparison is prof.pricing.include_delivery_in_comparison
        assert {k.value: v for k, v in cfg.max_offer_age_hours.items()} == (
            prof.pricing.max_offer_age_hours
        )
        assert dict(cfg.symbol_map) == prof.money.symbol_map


def test_the_uk_profile_supplies_the_vat_rate_not_the_component() -> None:
    cfg = PricingConfig.from_mapping(load_profile("uk").profile.model_dump(mode="json"))
    assert cfg.vat_rate == D("0.20") and cfg.base_currency == "GBP"
    assert cfg.unknown_basis == "flag_require_approval"
    us = PricingConfig.from_mapping(load_profile("us").profile.model_dump(mode="json"))
    assert us.vat_rate == D("0") and us.base_currency == "USD"


def test_money_policy_keys_the_config_does_not_use_are_still_accepted() -> None:
    keys = set(MoneyPolicy.model_fields)
    cfg = PricingConfig.from_mapping(
        {"money": {k: v for k, v in load_profile("uk").profile.model_dump().get("money", {}).items()
                   if k in keys}}
    )
    assert cfg.base_currency == "GBP"


def test_test_helper_builds_the_uk_like_config() -> None:
    cfg = PricingConfig.from_mapping(config_mapping())
    assert cfg.vat_rate == D("0.20") and cfg.compare_basis == "ex_tax"
    assert cfg.tax_active is True
    assert PricingConfig.from_mapping(MIN_MONEY).tax_active is False
