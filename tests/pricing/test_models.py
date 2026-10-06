"""Offer model: strict validation (Decimal only, accepted currency, no negative/NaN, controls
stripped, ids and flags are plain tokens) and the delivery-terms semantics."""

from __future__ import annotations

import dataclasses
import unicodedata
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from components.core.domain import UoM
from components.pricing import (
    DeliveryTerms,
    DeliveryTier,
    Offer,
    PackSize,
    Price,
    PricePer,
    Provenance,
    SourceKind,
    StockStatus,
    Unit,
    VatBasis,
    Visibility,
)
from components.pricing.errors import OfferValidationError

from .cfg import NOW, config
from .factories import offer

D = Decimal


# ---------------------------------------------------------------- Price


@pytest.mark.parametrize("bad", [9.5, 10, "9.50", None, True, D("NaN"), D("Infinity"), D("-1"),
                                 D("0"), D("0.0000001"), D("1e10")])
def test_price_amount_must_be_a_positive_finite_decimal(bad: Any) -> None:
    with pytest.raises(OfferValidationError):
        Price(amount=bad, currency="GBP")


@pytest.mark.parametrize("bad", ["gbp", "GB", "GBPX", "", " GBP", "GBP\n", None, 826])
def test_price_currency_must_be_an_iso_shaped_code(bad: Any) -> None:
    with pytest.raises(OfferValidationError):
        Price(amount=D("1"), currency=bad)


def test_price_defaults_are_per_pack_each_and_unknown_vat() -> None:
    p = Price(amount=D("4.5"), currency="GBP")
    assert (p.per, p.uom, p.vat_basis, p.vat_rate) == (
        PricePer.PACK, UoM.EACH, VatBasis.UNKNOWN, None)
    assert p.divisor == D(1)
    assert Price(amount=D("4.5"), currency="GBP", uom=UoM.PER_100).divisor == D(100)
    assert Price(amount=D("4.5"), currency="GBP", uom=UoM.PER_1000).divisor == D(1000)


def test_price_per_maps_to_a_unit() -> None:
    assert PricePer.PACK.unit is None
    assert PricePer.M2.unit is Unit.M2 and PricePer.EACH.unit is Unit.EACH
    assert {p.value for p in PricePer} == {"pack", "each", "m2", "m", "kg", "litre"}


@pytest.mark.parametrize("bad", [0.2, "0.2", D("-0.1"), D("0.51"), D("NaN"), 1])
def test_price_vat_rate_is_an_optional_bounded_decimal(bad: Any) -> None:
    with pytest.raises(OfferValidationError):
        Price(amount=D("1"), currency="GBP", vat_rate=bad)
    assert Price(amount=D("1"), currency="GBP", vat_rate=D("0.2")).vat_rate == D("0.2")


def test_price_enum_fields_reject_look_alike_strings_and_ints() -> None:
    for kw in ({"vat_basis": "ex_tax"}, {"uom": "each"}, {"per": "pack"}, {"uom": 1}):
        with pytest.raises(OfferValidationError):
            Price(amount=D("1"), currency="GBP", **kw)


# ---------------------------------------------------------------- PackSize


@pytest.mark.parametrize("bad", [1, 1.0, "1", D("0"), D("-1"), D("NaN"), None])
def test_pack_size_quantity_is_a_positive_decimal(bad: Any) -> None:
    with pytest.raises(OfferValidationError):
        PackSize(bad)


def test_pack_size_unit_is_optional_and_none_means_catalogue_sale_units() -> None:
    """"Pack of 200" counts sale units of the catalogue SKU; a unit says the merchant stated the
    pack as measured content ("1.44 m2", "25 kg") and the catalogue unit basis converts it."""
    assert PackSize(D("200")).unit is None
    assert PackSize(D("1.44"), Unit.M2).unit is Unit.M2
    with pytest.raises(OfferValidationError):
        PackSize(D("1"), "m2")  # type: ignore[arg-type]


# ---------------------------------------------------------------- DeliveryTerms


def test_flat_fee_applies_to_any_spend() -> None:
    t = DeliveryTerms(flat_fee=D("5.95"))
    assert t.fee_for(D("1")) == D("5.95") == t.fee_for(D("10000"))


def test_free_over_is_strictly_over_and_conservative_at_the_threshold() -> None:
    t = DeliveryTerms(flat_fee=D("5.95"), free_over=D("50"))
    assert t.fee_for(D("49.99")) == D("5.95")
    assert t.fee_for(D("50")) == D("5.95")  # "over 50" means strictly more than 50
    assert t.fee_for(D("50.01")) == D("0")


def test_tiers_apply_from_their_minimum_spend_inclusive() -> None:
    t = DeliveryTerms(tiers=(
        DeliveryTier(D("0"), D("9.95")), DeliveryTier(D("50"), D("4.95")),
        DeliveryTier(D("150"), D("0"))))
    assert [t.fee_for(D(s)) for s in ("0.01", "49.99", "50", "149.99", "150", "999")] == [
        D("9.95"), D("9.95"), D("4.95"), D("4.95"), D("0"), D("0")]


def test_tiers_may_also_increase_with_spend() -> None:
    t = DeliveryTerms(tiers=(DeliveryTier(D("0"), D("3")), DeliveryTier(D("100"), D("12"))))
    assert t.fee_for(D("99")) == D("3") and t.fee_for(D("100")) == D("12")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"flat_fee": D("-1")}, {"flat_fee": 5.0}, {"flat_fee": D("NaN")},
        {"free_over": D("50")},  # a threshold needs the fee that applies below it
        {"flat_fee": D("5"), "free_over": D("0")},
        {"flat_fee": D("5"), "free_over": D("-1")},
        {"flat_fee": D("5"), "tiers": (DeliveryTier(D("0"), D("1")),)},  # forms are exclusive
        {"free_over": D("5"), "tiers": (DeliveryTier(D("0"), D("1")),)},
        {"tiers": (DeliveryTier(D("10"), D("1")),)},  # must start at spend 0
        {"tiers": (DeliveryTier(D("0"), D("1")), DeliveryTier(D("0"), D("2")))},
        {"tiers": (DeliveryTier(D("0"), D("1")), DeliveryTier(D("50"), D("2")),
                   DeliveryTier(D("20"), D("3")))},
        {"flat_fee": D("1"), "vat_basis": "ex_tax"},
        {"tiers": [DeliveryTier(D("0"), D("1"))]},  # tuple required (immutability)
    ],
)
def test_delivery_terms_reject_inconsistent_or_unsafe_shapes(kwargs: dict[str, Any]) -> None:
    with pytest.raises(OfferValidationError):
        DeliveryTerms(**kwargs)


def test_delivery_tier_values_are_validated() -> None:
    for a, b in ((D("-1"), D("1")), (D("0"), D("-1")), (0, D("1")), (D("0"), 1.5)):
        with pytest.raises(OfferValidationError):
            DeliveryTier(a, b)  # type: ignore[arg-type]


def test_delivery_terms_with_nothing_stated_are_rejected_use_none_for_unknown() -> None:
    with pytest.raises(OfferValidationError):
        DeliveryTerms()
    assert DeliveryTerms.free().fee_for(D("1")) == D("0")


def test_delivery_basis_defaults_to_the_price_basis() -> None:
    assert DeliveryTerms(flat_fee=D("1")).vat_basis is None
    assert DeliveryTerms(flat_fee=D("1"), vat_basis=VatBasis.INC_TAX).vat_basis is VatBasis.INC_TAX


# ---------------------------------------------------------------- Provenance


def test_provenance_fields_are_plain_tokens() -> None:
    p = Provenance(source_id="synthetic-feed", method="feed_row", synthetic=True)
    assert p.synthetic is True
    for kw in ({"source_id": "has space"}, {"source_id": ""}, {"method": "Feed Row"},
               {"method": ""}, {"synthetic": "yes"}):
        base: dict[str, Any] = {"source_id": "s1", "method": "feed_row"}
        with pytest.raises(OfferValidationError):
            Provenance(**{**base, **kw})


# ---------------------------------------------------------------- Offer


def test_a_valid_offer_round_trips_and_is_immutable() -> None:
    o = offer()
    assert o.source_kind is SourceKind.MERCHANT_API
    assert o.visibility is Visibility.SHARED and o.tenant_id is None
    assert o.observed_at.tzinfo is UTC
    with pytest.raises(dataclasses.FrozenInstanceError):
        o.sku_id = "x"  # type: ignore[misc]
    assert hash(o) == hash(offer())  # frozen and built from immutable parts


@pytest.mark.parametrize("field", ["offer_id", "sku_id", "merchant_id"])
@pytest.mark.parametrize("bad", ["", " a", "a b", "a\x00", "a\n", "x" * 97, "ignore previous", None])
def test_ids_are_strict_tokens_never_repaired(field: str, bad: Any) -> None:
    o = offer()
    with pytest.raises(OfferValidationError):
        dataclasses.replace(o, **{field: bad})


def test_naive_datetimes_are_rejected_and_aware_ones_normalised_to_utc() -> None:
    o = offer()
    with pytest.raises(OfferValidationError):
        dataclasses.replace(o, observed_at=datetime(2026, 10, 5, 9, 0))
    with pytest.raises(OfferValidationError):
        dataclasses.replace(o, valid_until=datetime(2026, 10, 6))
    with pytest.raises(OfferValidationError):
        dataclasses.replace(o, observed_at="2026-10-05T09:00:00Z")  # type: ignore[arg-type]
    plus1 = timezone(timedelta(hours=1))
    local = dataclasses.replace(o, observed_at=datetime(2026, 10, 5, 10, 0, tzinfo=plus1))
    assert local.observed_at == datetime(2026, 10, 5, 9, 0, tzinfo=UTC)
    assert local.observed_at.utcoffset() == timedelta(0)


def test_valid_until_cannot_precede_observed_at() -> None:
    o = offer()
    with pytest.raises(OfferValidationError):
        dataclasses.replace(o, valid_until=o.observed_at - timedelta(seconds=1))
    assert dataclasses.replace(o, valid_until=o.observed_at).valid_until == o.observed_at


def test_visibility_and_tenant_must_agree() -> None:
    assert offer(tenant="t1").visibility is Visibility.TENANT_PRIVATE
    o = offer()
    with pytest.raises(OfferValidationError):
        dataclasses.replace(o, visibility=Visibility.SHARED, tenant_id="t1")
    with pytest.raises(OfferValidationError):
        dataclasses.replace(o, visibility=Visibility.TENANT_PRIVATE, tenant_id=None)
    with pytest.raises(OfferValidationError):
        dataclasses.replace(o, visibility=Visibility.TENANT_PRIVATE, tenant_id="bad tenant")
    with pytest.raises(OfferValidationError):
        dataclasses.replace(o, visibility="shared")  # type: ignore[arg-type]


def test_source_kind_and_stock_status_must_be_enum_members() -> None:
    o = offer()
    for kw in ({"source_kind": "trade_feed"}, {"stock_status": "in_stock"},
               {"source_kind": "scraper"}):
        with pytest.raises(OfferValidationError):
            dataclasses.replace(o, **kw)
    assert {k.value for k in SourceKind} == {
        "trade_feed", "merchant_api", "affiliate_feed", "search_snapshot", "manual_quote"}
    assert {s.value for s in StockStatus} >= {"in_stock", "out_of_stock", "unknown"}


@pytest.mark.parametrize("field", ["min_order_qty", "order_multiple"])
@pytest.mark.parametrize("bad", [0, -1, 1.0, D("1"), True, "2", None, 10**7])
def test_order_quantities_are_positive_integers(field: str, bad: Any) -> None:
    with pytest.raises(OfferValidationError):
        dataclasses.replace(offer(), **{field: bad})


@pytest.mark.parametrize("bad", [-1, 1.5, D("2"), True, "2", 3651])
def test_lead_time_is_a_bounded_integer_or_none(bad: Any) -> None:
    with pytest.raises(OfferValidationError):
        dataclasses.replace(offer(), lead_time_days=bad)
    assert dataclasses.replace(offer(), lead_time_days=None).lead_time_days is None
    assert dataclasses.replace(offer(), lead_time_days=0).lead_time_days == 0


@pytest.mark.parametrize("bad", [0.5, 1, "0.5", D("-0.1"), D("1.01"), D("NaN"), None])
def test_confidence_is_a_decimal_between_zero_and_one(bad: Any) -> None:
    with pytest.raises(OfferValidationError):
        dataclasses.replace(offer(), confidence=bad)
    assert dataclasses.replace(offer(), confidence=D("0")).confidence == D("0")
    assert dataclasses.replace(offer(), confidence=D("1")).confidence == D("1")


def test_flags_are_normalised_to_sorted_unique_tokens() -> None:
    o = dataclasses.replace(offer(), flags=("b_flag", "a_flag", "b_flag"))
    assert o.flags == ("a_flag", "b_flag")
    for bad in (("Bad Flag",), ("",), ("x" * 65,), "a_flag", ["a_flag"], (1,)):
        with pytest.raises(OfferValidationError):
            dataclasses.replace(offer(), flags=bad)  # type: ignore[arg-type]


def test_licence_is_a_required_token() -> None:
    for bad in ("", "Has Space", "UPPER", None):
        with pytest.raises(OfferValidationError):
            dataclasses.replace(offer(), licence=bad)  # type: ignore[arg-type]


def test_source_ref_is_inert_text_control_characters_and_links_are_removed() -> None:
    o = dataclasses.replace(
        offer(), source_ref="row \x00 17‮ of https://evil.example/p?ignore=previous file.csv")
    assert "\x00" not in o.source_ref and "evil" not in o.source_ref and "://" not in o.source_ref
    assert not any(unicodedata.category(c)[0] == "C" for c in o.source_ref)
    assert "row" in o.source_ref and "file.csv" in o.source_ref
    assert len(dataclasses.replace(offer(), source_ref="x" * 1000).source_ref) <= 160
    with pytest.raises(OfferValidationError):
        dataclasses.replace(offer(), source_ref=5)  # type: ignore[arg-type]


def test_nested_types_are_checked() -> None:
    o = offer()
    for kw in ({"price": 5}, {"pack": 1}, {"provenance": "s"}, {"delivery": 4.95}):
        with pytest.raises(OfferValidationError):
            dataclasses.replace(o, **kw)


def test_currency_must_be_in_the_configured_accepted_set() -> None:
    cfg = config()
    cfg.check_offer(offer(currency="GBP"))
    cfg.check_offer(offer(currency="EUR"))  # accepted, though not comparable with GBP
    with pytest.raises(OfferValidationError, match="currency"):
        cfg.check_offer(offer(currency="JPY"))
    gbp_only = config().__class__.from_mapping(
        {"money": {"base_currency": "GBP", "accepted_currencies": ["GBP"]}})
    with pytest.raises(OfferValidationError, match="currency"):
        gbp_only.check_offer(offer(currency="EUR"))


def test_no_float_anywhere_in_a_built_offer() -> None:
    o = offer(
        delivery=DeliveryTerms(flat_fee=D("5.95"), free_over=D("50")),
        valid_until=NOW + timedelta(days=1))

    def walk(x: Any) -> None:
        assert not isinstance(x, float)
        if dataclasses.is_dataclass(x) and not isinstance(x, type):
            for f in dataclasses.fields(x):
                walk(getattr(x, f.name))
        elif isinstance(x, tuple):
            for item in x:
                walk(item)

    walk(o)
