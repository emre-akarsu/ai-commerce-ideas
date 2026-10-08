"""Resolved lines: the input to pricing (CLAUDE.md rule 2, no auto-substitution).

A `ResolvedLine` is what the matching stage hands over: a match group of catalogue SKUs it has
approved for one order line, plus the required quantity in a unit. The engine only ever prices
offers for SKUs in that group and never widens it. Each member carries its tier and match basis
(for provenance), the catalogue `UnitBasis`, and, when it is not a Tier A same-part match, the id
of the recorded substitution approval (verified by the caller, not by the engine).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from components.core.domain import Basis, Tier

from .decimals import CTX, check_decimal
from .errors import OfferValidationError
from .models import MAX_LEAD_TIME_DAYS, VatBasis, _enum, _set
from .text import check_id, check_token, clean_text
from .units import Unit, UnitBasis

MAX_SKUS_PER_LINE = 50
DESCRIPTION_MAX = 200


@dataclass(frozen=True, slots=True)
class MatchedSku:
    sku_id: str
    unit_basis: UnitBasis = UnitBasis()
    tier: Tier = Tier.A
    basis: Basis | None = None
    substitution_approval_id: str | None = None

    def __post_init__(self) -> None:
        check_id(self.sku_id, "sku_id")
        if not isinstance(self.unit_basis, UnitBasis):
            raise OfferValidationError("unit_basis must be a UnitBasis")
        _enum(self.tier, Tier, "tier")
        if self.basis is not None:
            _enum(self.basis, Basis, "basis")
        if self.substitution_approval_id is not None:
            check_id(self.substitution_approval_id, "substitution_approval_id")

    @property
    def approved_for_selection(self) -> bool:
        """Tier A (same part) is approved by the match; any other tier needs a recorded
        substitution approval (R2)."""
        return self.tier is Tier.A or self.substitution_approval_id is not None


@dataclass(frozen=True, slots=True)
class IndexBand:
    """Optional external sanity band for one unit price, used RELATIVELY only.

    `reference_unit_price` is a price for this line seen earlier (for example the tenant's last
    paid unit price) on a stated VAT basis. `index_ratio` is how far a published price index says
    prices moved since then (1 = no movement known). The expected price is their product and an
    offer is flagged when it is more than `tolerance` times above or below it. An index LEVEL is
    never an acceptable price here: the construction-material indices are factory-gate indices that
    exclude merchant discounts, so they can only say how prices MOVED."""

    reference_unit_price: Decimal
    unit: Unit
    currency: str
    vat_basis: VatBasis
    source: str
    tolerance: Decimal
    as_of: date | None = None
    index_ratio: Decimal = Decimal(1)

    def __post_init__(self) -> None:
        _set(self, "reference_unit_price", check_decimal(
            self.reference_unit_price, "index_band.reference_unit_price", minimum=Decimal(0),
            min_exclusive=True))
        _set(self, "tolerance", check_decimal(
            self.tolerance, "index_band.tolerance", minimum=Decimal(1), maximum=Decimal(10)))
        _set(self, "index_ratio", check_decimal(
            self.index_ratio, "index_band.index_ratio", minimum=Decimal("0.2"),
            maximum=Decimal(5)))
        _enum(self.unit, Unit, "index_band.unit")
        _enum(self.vat_basis, VatBasis, "index_band.vat_basis")
        if self.vat_basis is VatBasis.UNKNOWN:
            raise OfferValidationError("an index band must state its VAT basis")
        if not (isinstance(self.currency, str) and len(self.currency) == 3
                and self.currency.isascii() and self.currency.isupper()):
            raise OfferValidationError("index_band.currency must be a 3-letter upper-case code")
        check_token(self.source, "index_band.source")
        if self.as_of is not None and (
            not isinstance(self.as_of, date) or isinstance(self.as_of, datetime)
        ):
            raise OfferValidationError("index_band.as_of must be a date")

    @property
    def expected(self) -> Decimal:
        """The reference price moved by the index (exact)."""
        return self.reference_unit_price * self.index_ratio

    @property
    def low(self) -> Decimal:
        return CTX.divide(self.expected, self.tolerance)

    @property
    def high(self) -> Decimal:
        return self.expected * self.tolerance


@dataclass(frozen=True, slots=True)
class ResolvedLine:
    line_id: str
    skus: tuple[MatchedSku, ...]
    quantity: Decimal
    unit: Unit
    description: str = ""
    index_band: IndexBand | None = None
    # Days from now by which the packs must arrive (None: no deadline). Offers that state their
    # availability are checked against it; offers that do not are flagged, never guessed at.
    need_by_days: int | None = None

    def __post_init__(self) -> None:
        check_id(self.line_id, "line_id")
        if not isinstance(self.skus, tuple) or not self.skus:
            raise OfferValidationError("a line needs at least one approved SKU")
        if len(self.skus) > MAX_SKUS_PER_LINE:
            raise OfferValidationError(f"a line may hold at most {MAX_SKUS_PER_LINE} SKUs")
        if not all(isinstance(s, MatchedSku) for s in self.skus):
            raise OfferValidationError("skus must hold MatchedSku values")
        ids = [s.sku_id for s in self.skus]
        if len(set(ids)) != len(ids):
            raise OfferValidationError("a match group must not repeat a SKU")
        _set(self, "skus", tuple(sorted(self.skus, key=lambda s: s.sku_id)))
        _enum(self.unit, Unit, "unit")
        qty = check_decimal(self.quantity, "quantity", minimum=Decimal(0), min_exclusive=True)
        if self.unit is Unit.EACH and qty != qty.to_integral_value():
            raise OfferValidationError("a count of pieces must be a whole number")
        _set(self, "quantity", qty)
        _set(self, "description", clean_text(self.description, "description", DESCRIPTION_MAX))
        if self.index_band is not None and not isinstance(self.index_band, IndexBand):
            raise OfferValidationError("index_band must be an IndexBand")
        if self.need_by_days is not None and (
            isinstance(self.need_by_days, bool) or not isinstance(self.need_by_days, int)
            or not 0 <= self.need_by_days <= MAX_LEAD_TIME_DAYS
        ):
            raise OfferValidationError(
                f"need_by_days must be None or whole days from 0 to {MAX_LEAD_TIME_DAYS}")

    @classmethod
    def of(
        cls,
        line_id: str,
        skus: Iterable[str | MatchedSku],
        quantity: Decimal,
        unit: Unit,
        *,
        unit_basis: UnitBasis | None = None,
        description: str = "",
        index_band: IndexBand | None = None,
        need_by_days: int | None = None,
    ) -> ResolvedLine:
        """Build a line from SKU ids (sharing `unit_basis`) and/or ready `MatchedSku` values."""
        group = tuple(
            s if isinstance(s, MatchedSku) else MatchedSku(s, unit_basis or UnitBasis())
            for s in skus
        )
        return cls(line_id, group, quantity, unit, description, index_band, need_by_days)

    @property
    def sku_ids(self) -> tuple[str, ...]:
        return tuple(s.sku_id for s in self.skus)

    def sku(self, sku_id: str) -> MatchedSku | None:
        return next((s for s in self.skus if s.sku_id == sku_id), None)


@dataclass(frozen=True, slots=True)
class UnmatchedLine:
    """An order line the matching stage could not resolve (listed separately in the quote)."""

    line_id: str
    text: str
    reason: str

    def __post_init__(self) -> None:
        check_id(self.line_id, "line_id")
        _set(self, "text", clean_text(self.text, "text", DESCRIPTION_MAX))
        check_token(self.reason, "reason")


@dataclass(frozen=True, slots=True)
class AmbiguousLine:
    """An order line that needs a person to choose (listed separately; never priced)."""

    line_id: str
    text: str
    candidate_sku_ids: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        check_id(self.line_id, "line_id")
        _set(self, "text", clean_text(self.text, "text", DESCRIPTION_MAX))
        if not isinstance(self.candidate_sku_ids, tuple):
            raise OfferValidationError("candidate_sku_ids must be a tuple")
        for sku in self.candidate_sku_ids:
            check_id(sku, "candidate_sku_id")
        _set(self, "candidate_sku_ids", tuple(sorted(set(self.candidate_sku_ids))))
        check_token(self.reason, "reason")
