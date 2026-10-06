"""Resolved lines carry the approved match group (R2): the engine only ever prices SKUs in it."""

from __future__ import annotations

import dataclasses
from datetime import date
from decimal import Decimal
from typing import Any

import pytest

from components.core.domain import Basis, Tier
from components.pricing import (
    AmbiguousLine,
    IndexBand,
    MatchedSku,
    ResolvedLine,
    Unit,
    UnitBasis,
    UnmatchedLine,
    VatBasis,
)
from components.pricing.errors import OfferValidationError

D = Decimal


def test_of_builds_a_group_from_plain_sku_ids_with_a_shared_basis() -> None:
    basis = UnitBasis.of({Unit.M2: D("2.88")})
    ln = ResolvedLine.of("l1", ["sku-b", "sku-a"], D("60"), Unit.M2, unit_basis=basis,
                         description="12.5mm tapered p/board 2.4x1.2")
    assert [s.sku_id for s in ln.skus] == ["sku-a", "sku-b"]  # canonical order, not input order
    assert all(s.unit_basis == basis and s.tier is Tier.A for s in ln.skus)
    assert ln.sku_ids == ("sku-a", "sku-b")
    assert ln.description == "12.5mm tapered p/board 2.4x1.2"


def test_matched_skus_keep_their_own_basis_tier_and_approval() -> None:
    a = MatchedSku("sku-a", UnitBasis.of({Unit.KG: D("25")}), Tier.A, Basis.SAME_MPN)
    b = MatchedSku("sku-b", UnitBasis.of({Unit.KG: D("20")}), Tier.B, Basis.STANDARD,
                   substitution_approval_id="appr-1")
    ln = ResolvedLine.of("l1", [b, a], D("100"), Unit.KG)
    assert ln.sku("sku-b").substitution_approval_id == "appr-1"
    assert ln.sku("sku-a").unit_basis.content(Unit.KG) == D("25")
    assert ln.sku("nope") is None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"line_id": "has space"}, {"line_id": ""},
        {"sku_ids": []}, {"sku_ids": ["a", "a"]}, {"sku_ids": ["bad id"]},
        {"quantity": D("0")}, {"quantity": D("-1")}, {"quantity": 5}, {"quantity": 5.0},
        {"quantity": D("NaN")}, {"quantity": D("2.5"), "unit": Unit.EACH},  # whole counts only
        {"unit": "m2"}, {"description": 5},
    ],
)
def test_invalid_lines_are_rejected(kwargs: dict[str, Any]) -> None:
    base: dict[str, Any] = {"line_id": "l1", "sku_ids": ["sku-a"], "quantity": D("2"),
                            "unit": Unit.EACH}
    args = {**base, **kwargs}
    with pytest.raises(OfferValidationError):
        ResolvedLine.of(args["line_id"], args["sku_ids"], args["quantity"], args["unit"],
                        description=args.get("description", ""))


def test_a_measured_quantity_may_be_fractional() -> None:
    assert ResolvedLine.of("l1", ["sku-a"], D("2.5"), Unit.M2).quantity == D("2.5")


def test_description_is_inert_display_text_only() -> None:
    ln = ResolvedLine.of("l1", ["sku-a"], D("1"), Unit.EACH,
                         description="IGNORE PREVIOUS\x00 https://evil.example/x ‮")
    assert "evil" not in ln.description and "\x00" not in ln.description
    assert "://" not in ln.description


def test_lines_are_immutable() -> None:
    ln = ResolvedLine.of("l1", ["sku-a"], D("1"), Unit.EACH)
    with pytest.raises(dataclasses.FrozenInstanceError):
        ln.quantity = D("2")  # type: ignore[misc]


def test_matched_sku_validation() -> None:
    for kw in ({"sku_id": "bad id"}, {"unit_basis": {"m2": 1}}, {"tier": "A"}, {"basis": "same_mpn"},
               {"substitution_approval_id": "bad id"}):
        base: dict[str, Any] = {"sku_id": "sku-a"}
        with pytest.raises(OfferValidationError):
            MatchedSku(**{**base, **kw})


def test_index_band_validation() -> None:
    band = IndexBand(low=D("3"), high=D("6"), unit=Unit.M2, currency="GBP",
                     vat_basis=VatBasis.EX_TAX, source="synthetic-index", as_of=date(2026, 9, 30))
    assert band.high == D("6")
    base = dict(low=D("3"), high=D("6"), unit=Unit.M2, currency="GBP", vat_basis=VatBasis.EX_TAX,
                source="synthetic-index", as_of=None)
    for kw in ({"low": D("-1")}, {"high": D("2")}, {"low": 3}, {"vat_basis": VatBasis.UNKNOWN},
               {"currency": "gbp"}, {"unit": "m2"}, {"source": "has space"}):
        with pytest.raises(OfferValidationError):
            IndexBand(**{**base, **kw})  # type: ignore[arg-type]


def test_unmatched_and_ambiguous_lines_carry_only_inert_text_and_ids() -> None:
    u = UnmatchedLine("l9", "20 sheets of unobtainium \x00 http://x.example", "no_candidate")
    assert "x.example" not in u.text and "\x00" not in u.text
    a = AmbiguousLine("l8", "20 x 12.5mm", ("sku-b", "sku-a"), "quantity_size_ambiguity")
    assert a.candidate_sku_ids == ("sku-a", "sku-b")
    for bad in ({"line_id": "bad id"}, {"reason": "Not A Token"}):
        with pytest.raises(OfferValidationError):
            UnmatchedLine(**{"line_id": "l", "text": "t", "reason": "r", **bad})
    with pytest.raises(OfferValidationError):
        AmbiguousLine("l8", "t", ("a bad id",), "r")
