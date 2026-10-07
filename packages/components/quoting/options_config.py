"""Configuration of the quote-options engine: a plain dataclass the CALLER fills.

Every default below is a PLACEHOLDER, not evidence: no study of what buyers value has been done
here. The balanced weights (50/25/15/10) are unsourced starting points; the references (budget,
required-by date, delivery cap) have no default at all: they come from the buyer.
They live in this dataclass (not in code constants) so that a deployment profile can own them
later (docs/architecture/quote-options.md, "config keys"). None of them can weaken a hard rule.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from components.pricing.errors import OfferValidationError
from components.pricing.text import check_id

from .errors import QuotingError

KINDS = ("cheapest", "single_supplier", "fewest_deliveries", "fastest", "preferred", "balanced")
DEFAULT_KINDS = ("cheapest", "fewest_deliveries", "fastest", "preferred", "balanced")
WEIGHTS_STATUS = "unsourced_placeholder"


class OptionsError(QuotingError):
    """Invalid input to the quote-options engine (config, preferred list, tenant mismatch)."""


def _dec(value: object, name: str, lo: Decimal, hi: Decimal, *, lo_open: bool = False) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, Decimal | str | int):
        raise OptionsError(f"{name} must be a Decimal")
    try:
        out = Decimal(value) if not isinstance(value, Decimal) else value
    except Exception as exc:
        raise OptionsError(f"{name} must be a Decimal") from exc
    if not out.is_finite() or out < lo or out > hi or (lo_open and out == lo):
        raise OptionsError(f"{name} must be between {lo} and {hi}")
    return out


def _int(value: object, name: str, lo: int, hi: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
        raise OptionsError(f"{name} must be an integer between {lo} and {hi}")
    return value


@dataclass(frozen=True)
class OptionsConfig:
    """What to produce and how to score. Defaults are documented placeholders."""

    kinds: tuple[str, ...] = DEFAULT_KINDS  # which options may be shown, in this display order
    tolerance_pct: Decimal = Decimal(5)  # fewest/preferred: total at most cheapest + this percent
    fastest_tolerance_pct: Decimal | None = None  # None: use tolerance_pct
    # Balanced option. A composite score is computed ONLY when the buyer supplies at least one of
    # budget_total, required_by, max_deliveries (fixed references from the buyer, never taken from
    # the generated options, so adding or removing an option cannot reorder the others).
    budget_total: Decimal | None = None  # target total on the configured VAT basis
    required_by: date | None = None  # latest acceptable delivery date (days counted from the clock)
    max_deliveries: int | None = None  # most deliveries (merchant orders) the buyer will accept
    # Weights over the ACTIVE criteria (renormalised). Unsourced placeholder values.
    weight_total: Decimal = Decimal(50)
    weight_lead_time: Decimal = Decimal(25)  # latest delivery date
    weight_deliveries: Decimal = Decimal(15)
    weight_preferred: Decimal = Decimal(10)
    max_options: int = 5  # most options shown
    max_search_merchants: int = 8  # merchants enumerated in subset searches (the rest are not)
    max_solver_calls: int = 64  # basket-optimiser calls allowed per search

    def __post_init__(self) -> None:
        kinds = self.kinds
        if (not isinstance(kinds, tuple) or len(set(kinds)) != len(kinds)
                or any(k not in KINDS for k in kinds)):
            raise OptionsError(f"kinds must be unique members of {KINDS}")
        set_ = object.__setattr__
        set_(self, "kinds", tuple(k for k in KINDS if k in kinds))
        set_(self, "tolerance_pct", _dec(self.tolerance_pct, "tolerance_pct",
                                         Decimal(0), Decimal(100)))
        if self.fastest_tolerance_pct is not None:
            set_(self, "fastest_tolerance_pct", _dec(
                self.fastest_tolerance_pct, "fastest_tolerance_pct", Decimal(0), Decimal(100)))
        weights = ("weight_total", "weight_lead_time", "weight_deliveries", "weight_preferred")
        for name in weights:
            set_(self, name, _dec(getattr(self, name), name, Decimal(0), Decimal(1000)))
        if sum((getattr(self, n) for n in weights), Decimal(0)) <= 0:
            raise OptionsError("at least one balanced weight must be positive")
        if self.budget_total is not None:
            set_(self, "budget_total", _dec(self.budget_total, "budget_total", Decimal(0),
                                            Decimal(10) ** 12, lo_open=True))
        if self.required_by is not None and (
                not isinstance(self.required_by, date) or isinstance(self.required_by, datetime)):
            raise OptionsError("required_by must be a date")
        if self.max_deliveries is not None:
            _int(self.max_deliveries, "max_deliveries", 1, 50)
        _int(self.max_options, "max_options", 1, 6)
        _int(self.max_search_merchants, "max_search_merchants", 1, 12)
        _int(self.max_solver_calls, "max_solver_calls", 1, 5000)

    @property
    def composite(self) -> bool:
        """True when the buyer gave a reference, so a composite (balanced) score may be computed."""
        return (self.budget_total is not None or self.required_by is not None
                or self.max_deliveries is not None)

    @property
    def fast_tolerance(self) -> Decimal:
        return self.tolerance_pct if self.fastest_tolerance_pct is None \
            else self.fastest_tolerance_pct

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> OptionsConfig:
        known = {f.name for f in fields(cls)}
        unknown = sorted(set(raw) - known)
        if unknown:
            raise OptionsError(f"unknown options keys: {unknown}")
        data = dict(raw)
        if "kinds" in data:
            data["kinds"] = tuple(data["kinds"])
        return cls(**data)


def check_preferred(preferred: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """The tenant's preferred merchants, most preferred first: validated ids, no duplicates."""
    out: list[str] = []
    for m in preferred:
        try:
            check_id(m, "preferred merchant")
        except OfferValidationError as exc:
            raise OptionsError(str(exc)) from exc
        if m in out:
            raise OptionsError(f"preferred merchant {m!r} is listed twice")
        out.append(m)
    return tuple(out)
