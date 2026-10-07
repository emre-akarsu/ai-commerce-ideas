"""Price sanity: outliers against the median of comparable offers, and an optional external band.

Both checks work on unit prices on the comparison basis, so different pack sizes compare fairly.
Both are RELATIVE: the median of comparable offers, and an optional band built from a reference
price moved by a published index ratio (an index level is never used as a price).
A price is a high outlier when it is above `median * ratio`, a low outlier when `price * ratio` is
below the median (both strict, exact Decimal arithmetic); the ratio comes from the configuration
(`pricing.price_outlier_ratio`). With fewer than `outlier_min_peers` comparable offers there is no
basis for a judgement and nothing is flagged. A suspiciously low price is as likely a data error
(wrong pack size or unit) as a bargain, so by default such an offer is held back for a person
(`engine.outlier_offers`).
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from fractions import Fraction

from .config import PricingConfig
from .decimals import median
from .lines import IndexBand
from .models import VatBasis
from .units import Unit
from .vat import convert

OUTLIER_LOW = "price_outlier_low"
OUTLIER_HIGH = "price_outlier_high"
BAND_LOW = "index_band_low"
BAND_HIGH = "index_band_high"


def find_outliers(unit_prices: Mapping[str, Decimal], cfg: PricingConfig) -> dict[str, str]:
    """offer id -> `price_outlier_low` / `price_outlier_high` for the prices that deviate."""
    if len(unit_prices) < cfg.outlier_min_peers:
        return {}
    mid = median(list(unit_prices.values()))
    ratio = cfg.price_outlier_ratio
    flags: dict[str, str] = {}
    for offer_id in sorted(unit_prices):
        price = unit_prices[offer_id]
        if price > mid * ratio:
            flags[offer_id] = OUTLIER_HIGH
        elif price * ratio < mid:
            flags[offer_id] = OUTLIER_LOW
    return flags


def index_band_flag(
    unit_price: Decimal, unit: Unit, band: IndexBand | None, cfg: PricingConfig
) -> str | None:
    """`index_band_low` / `index_band_high` when `unit_price` (comparison basis, per `unit`) is
    more than the band's tolerance factor below / above the reference price moved by the index;
    None when inside, or when the band does not apply (other unit or currency). Exact arithmetic,
    edges inclusive."""
    if band is None or band.unit is not unit or band.currency != cfg.base_currency:
        return None
    price = Fraction(unit_price)
    if cfg.tax_active:
        price = convert(price, VatBasis(cfg.compare_basis), band.vat_basis, cfg.vat_rate)
    expected = Fraction(band.expected)
    tolerance = Fraction(band.tolerance)
    if price * tolerance < expected:
        return BAND_LOW
    if price > expected * tolerance:
        return BAND_HIGH
    return None
