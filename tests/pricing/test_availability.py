"""Optional stock availability on an Offer: how many packs can be supplied within N days.

`availability` is a tuple of `Tranche` values, strictly increasing in `in_days`. An empty tuple
means availability is unknown, and then nothing about the offer changes.
"""

from __future__ import annotations

import dataclasses
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import components.pricing as pricing
from components.pricing import (
    CsvPriceFileSource,
    Offer,
    OfferQuery,
    OfferValidationError,
    Tranche,
    ingest,
)
from components.quoting.loading import specs_from_manifest

from .cfg import config
from .factories import offer

D = Decimal
DEMO = Path(__file__).resolve().parents[2] / "profiles" / "data" / "quoting"
THREE = (Tranche(2, 0), Tranche(10, 3), Tranche(40, 14))  # 2 now, 12 by day 3, 52 by day 14


def with_tranches(*tranches: Any) -> Offer:
    return dataclasses.replace(offer(), availability=tuple(tranches))


def demo_offers() -> list[Offer]:
    """Every synthetic demo price file, ingested the way scripts/demo_quote.py ingests it."""
    manifest = json.loads((DEMO / "manifest.json").read_text(encoding="utf-8"))
    texts = {f["file"]: (DEMO / f["file"]).read_text(encoding="utf-8") for f in manifest["files"]}
    found: list[Offer] = []
    for spec in specs_from_manifest(manifest, texts):
        source = CsvPriceFileSource(spec.text, spec.mapping, source_id=spec.source_id,
                                    kind=spec.kind, origin=spec.origin)
        found += ingest(source, OfferQuery(), spec.declaration, config()).offers
    return found


# ---------------------------------------------------------------- Tranche


@pytest.mark.parametrize("packs", [0, -1, 1.0, "2", None, True, D("2")])
def test_tranche_packs_must_be_a_positive_int(packs: Any) -> None:
    with pytest.raises(OfferValidationError):
        Tranche(packs, 0)


@pytest.mark.parametrize("in_days", [-1, 1.5, "3", None, True, False, D("1")])
def test_tranche_in_days_must_be_a_non_negative_int(in_days: Any) -> None:
    with pytest.raises(OfferValidationError):
        Tranche(1, in_days)


def test_tranche_accepts_day_zero_and_is_an_immutable_value() -> None:
    t = Tranche(1, 0)
    assert (t.packs, t.in_days) == (1, 0)
    assert t == Tranche(1, 0) and hash(t) == hash(Tranche(1, 0))
    with pytest.raises(dataclasses.FrozenInstanceError):
        t.packs = 5  # type: ignore[misc]


def test_tranche_is_exported_from_the_pricing_package() -> None:
    assert pricing.Tranche is Tranche and "Tranche" in pricing.__all__


# ---------------------------------------------------------------- Offer.availability


def test_availability_is_the_last_field_and_defaults_to_unknown() -> None:
    assert [f.name for f in dataclasses.fields(Offer)][-1] == "availability"
    o = offer()
    assert o.availability == ()
    assert o.packs_available_by(0) is None and o.packs_available_by(10**9) is None


def test_demo_offers_keep_unknown_availability() -> None:
    found = demo_offers()
    assert found, "the demo price files should yield offers"
    assert all(o.availability == () and o.packs_available_by(0) is None for o in found)


def test_strictly_increasing_tranches_up_to_ten_are_accepted() -> None:
    assert with_tranches(*THREE).availability == THREE
    ten = tuple(Tranche(1, days) for days in range(10))
    assert with_tranches(*ten).availability == ten
    same_packs = (Tranche(1, 0), Tranche(1, 1))
    assert with_tranches(*same_packs).availability == same_packs


@pytest.mark.parametrize("bad", [
    [Tranche(2, 0)],                                    # a list, not a tuple
    None,
    (2, 5),                                             # not a Tranche
    ({"packs": 2, "in_days": 5},),                      # a dict, not a Tranche
    (Tranche(2, 0), (10, 3)),                           # one element is a plain tuple
    (Tranche(10, 3), Tranche(2, 0)),                    # not sorted
    (Tranche(2, 0), Tranche(10, 3), Tranche(40, 3)),    # duplicate in_days at the end
    (Tranche(2, 3), Tranche(10, 3)),                    # duplicate in_days at the start
    tuple(Tranche(1, days) for days in range(11)),      # more than ten
])
def test_availability_must_be_a_sorted_tuple_of_at_most_ten_tranches(bad: Any) -> None:
    with pytest.raises(OfferValidationError):
        dataclasses.replace(offer(), availability=bad)


def test_tranches_take_part_in_equality_and_hashing() -> None:
    assert with_tranches(*THREE) == with_tranches(*THREE)
    assert hash(with_tranches(*THREE)) == hash(with_tranches(*THREE))
    assert with_tranches(*THREE) != offer()
    assert with_tranches(Tranche(2, 0)) != with_tranches(Tranche(2, 1))


# ---------------------------------------------------------------- Offer.packs_available_by


@pytest.mark.parametrize(("days", "packs"), [
    (0, 2),         # the first tranche is due now
    (2, 2),         # between tranches
    (3, 12),        # exactly on a boundary: the tranche due in 3 days counts
    (13, 12),
    (14, 52),       # exactly on the last boundary
    (10**9, 52),    # large day counts: everything is due
])
def test_packs_available_by_sums_the_tranches_due_by_that_day(days: int, packs: int) -> None:
    assert with_tranches(*THREE).packs_available_by(days) == packs


def test_packs_available_by_is_zero_not_none_before_the_first_tranche() -> None:
    assert with_tranches(Tranche(5, 4)).packs_available_by(3) == 0


@pytest.mark.parametrize("bad", [-1, 1.0, True, "3", D("3"), None])
def test_packs_available_by_needs_a_non_negative_int_day_count(bad: Any) -> None:
    with pytest.raises(OfferValidationError):
        with_tranches(*THREE).packs_available_by(bad)
    with pytest.raises(OfferValidationError):  # refused even when availability is unknown
        offer().packs_available_by(bad)
