"""Delivery terms compiled to an integer step function on the comparison basis.

`FeeSchedule` maps a merchant order's goods spend (in minor units, on the configured comparison
basis) to the delivery fee (minor units). Thresholds stated on the other VAT basis are converted as
exact rationals and then turned into the first whole minor unit that satisfies the condition, so a
threshold is never rounded the wrong way ("free over 50.00 inc VAT" at 20% is spend ex above
41.666..., i.e. from 41.67). Fees are converted and rounded once, half-up. Integers keep the
basket search fast and exact.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction

from .config import PricingConfig
from .decimals import CTX, as_money, round_half_up_int
from .models import DeliveryTerms, VatBasis
from .vat import convert


@dataclass(frozen=True, slots=True)
class FeeSchedule:
    """`bands` are (first spend in minor units, fee in minor units), ascending, first at 0."""

    places: int
    bands: tuple[tuple[int, int], ...]

    def fee_minor(self, spend_minor: int) -> int:
        if spend_minor < 0:
            raise ValueError("spend must not be negative")
        fee = self.bands[0][1]
        for start, band_fee in self.bands:
            if spend_minor < start:
                break
            fee = band_fee
        return fee

    def fee(self, spend: Decimal) -> Decimal:
        minor = int(as_money(spend, self.places).scaleb(self.places, context=CTX))
        return Decimal(self.fee_minor(minor)).scaleb(-self.places, context=CTX)

    def min_fee_between(self, lo: int, hi: int) -> int:
        """Smallest fee for any spend in [lo, hi] (a lower bound for branch and bound)."""
        if lo < 0 or hi < lo:
            raise ValueError("need 0 <= lo <= hi")
        best = self.fee_minor(lo)
        for start, fee in self.bands:
            if lo < start <= hi:
                best = min(best, fee)
        return best

    def thresholds(self) -> tuple[int, ...]:
        return tuple(start for start, _ in self.bands)


def _canonical(raw: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    out: list[tuple[int, int]] = []
    for start, fee in raw:
        if out and out[-1][0] == start:
            out.pop()  # two thresholds fell on the same minor unit: the later band governs
        if out and out[-1][1] == fee:
            continue
        out.append((start, fee))
    return tuple(out)


def _first_spend(threshold: Fraction, strict: bool, places: int) -> int:
    scaled = threshold * 10**places
    return math.floor(scaled) + 1 if strict else math.ceil(scaled)


def compile_terms(
    terms: DeliveryTerms, price_basis: VatBasis, cfg: PricingConfig
) -> FeeSchedule | None:
    """The terms as a schedule on the comparison basis; None when the terms' VAT basis is unknown
    (so the fee cannot be put on the comparison basis). With no tax configured nothing converts."""
    target = VatBasis(cfg.compare_basis)
    basis = terms.vat_basis or price_basis
    if cfg.tax_active and basis is VatBasis.UNKNOWN:
        return None
    needs_conversion = cfg.tax_active and basis is not target
    raw: list[tuple[int, int]] = []
    for band in terms.bands():
        start, fee = Fraction(band.start), Fraction(band.fee)
        if needs_conversion:
            start = convert(start, basis, target, cfg.vat_rate)
            fee = convert(fee, basis, target, cfg.vat_rate)
        raw.append((_first_spend(start, band.strict, cfg.minor_unit_places),
                    round_half_up_int(fee * 10**cfg.minor_unit_places)))
    return FeeSchedule(cfg.minor_unit_places, _canonical(raw))


def combine(schedules: Sequence[FeeSchedule]) -> FeeSchedule:
    """The pointwise larger fee of several schedules: never understates delivery."""
    if not schedules:
        raise ValueError("nothing to combine")
    places = schedules[0].places
    if any(s.places != places for s in schedules):
        raise ValueError("schedules use different minor units")
    if len(schedules) == 1:
        return schedules[0]
    starts = sorted({t for s in schedules for t in s.thresholds()})
    raw = [(t, max(s.fee_minor(t) for s in schedules)) for t in starts]
    return FeeSchedule(places, _canonical(raw))
