"""VAT handling (CLAUDE.md: the rate and basis policy come from the deployment profile).

Conversion between ex-tax and inc-tax uses the CONFIGURED rate and is an exact rational: nothing
is rounded here. An offer whose basis is unknown is flagged `vat_basis_unknown` and excluded from
best-price selection (a person must say which basis it is), exactly as the UK profile asks
(`tax.unknown_basis: flag_require_approval`). With a zero configured rate there is nothing to
convert and nothing is flagged, as in `rfq.quotes.normalise`.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction

from .config import PricingConfig
from .decimals import as_money, frac_to_decimal
from .models import Price, VatBasis


@dataclass(frozen=True)
class VatOutcome:
    basis: VatBasis  # the effective basis of the price (UNKNOWN only when excluded)
    flags: tuple[str, ...] = ()
    exclusion: str | None = None  # reason code that keeps the offer out of best-price selection


def _compare_basis(cfg: PricingConfig) -> VatBasis:
    return VatBasis(cfg.compare_basis)


def convert(amount: Fraction, source: VatBasis, target: VatBasis, rate: Decimal) -> Fraction:
    """Exact conversion of `amount` between VAT bases at `rate` (a fraction, e.g. 0.20)."""
    if VatBasis.UNKNOWN in (source, target):
        raise ValueError("cannot convert an unknown VAT basis")
    if source is target:
        return amount
    factor = 1 + Fraction(rate)
    return amount / factor if source is VatBasis.INC_TAX else amount * factor


def resolve_basis(price: Price, cfg: PricingConfig) -> VatOutcome:
    """The basis to use for `price`, with any flag and the exclusion that sends it to a human."""
    target = _compare_basis(cfg)
    if not cfg.tax_active:
        return VatOutcome(basis=target)
    basis = price.vat_basis
    flags: tuple[str, ...] = ()
    if basis is VatBasis.UNKNOWN:
        default = cfg.quote_basis_default
        if cfg.unknown_basis == "assume_default_flag" and default != "unknown":
            basis, flags = VatBasis(default), ("vat_basis_assumed",)
        else:
            return VatOutcome(basis, ("vat_basis_unknown",), "vat_basis_unknown")
    stated = price.vat_rate
    if basis is not target and stated is not None and stated != cfg.vat_rate:
        return VatOutcome(basis, (*flags, "vat_rate_mismatch"), "vat_rate_mismatch")
    return VatOutcome(basis, flags)


@dataclass(frozen=True)
class VatSplit:
    net: Decimal
    vat: Decimal
    gross: Decimal


def split_total(total: Decimal, basis: VatBasis, rate: Decimal, places: int) -> VatSplit:
    """Show a money total on both bases. The derived figures are rounded once (half-up) and the
    parts always add up: net + vat == gross, with `total` itself unchanged."""
    if basis is VatBasis.UNKNOWN:
        raise ValueError("a total needs a known VAT basis")
    total = as_money(total, places)
    if basis is VatBasis.EX_TAX:
        vat = frac_to_decimal(Fraction(total) * Fraction(rate), places)
        return VatSplit(net=total, vat=vat, gross=total + vat)
    net = frac_to_decimal(Fraction(total) / (1 + Fraction(rate)), places)
    return VatSplit(net=net, vat=total - net, gross=total)
