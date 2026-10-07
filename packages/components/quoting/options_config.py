"""Configuration of the quote-options engine: a plain dataclass the CALLER fills.

Every default below is a PLACEHOLDER, not evidence: no study of what buyers value has been done
here. The balanced weights (50/25/15/10) and the reference values are unsourced starting points.
They live in this dataclass (not in code constants) so that a deployment profile can own them
later (docs/architecture/quote-options.md, "config keys"). None of them can weaken a hard rule.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields
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
    # Balanced score weights (relative; they are normalised). Unsourced placeholder values.
    weight_total: Decimal = Decimal(50)
    weight_lead_time: Decimal = Decimal(25)  # latest delivery
    weight_deliveries: Decimal = Decimal(15)
    weight_preferred: Decimal = Decimal(10)
    # FIXED references of the balanced score (a score never depends on the other options shown):
    # cost anchor = the optimiser's cheapest total; score 0 at the anchor, 1 at +cost_span_pct.
    cost_span_pct: Decimal = Decimal(25)
    target_lead_time_days: int = 2  # score 0 at or under this latest lead time
    worst_lead_time_days: int = 14  # score 1 at or over this (and when a lead time is unknown)
    target_deliveries: int = 1
    worst_deliveries: int = 5
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
        set_(self, "cost_span_pct", _dec(self.cost_span_pct, "cost_span_pct", Decimal(0),
                                         Decimal(1000), lo_open=True))
        _int(self.target_lead_time_days, "target_lead_time_days", 0, 365)
        _int(self.worst_lead_time_days, "worst_lead_time_days", 1, 365)
        _int(self.target_deliveries, "target_deliveries", 1, 50)
        _int(self.worst_deliveries, "worst_deliveries", 2, 50)
        if self.target_lead_time_days >= self.worst_lead_time_days:
            raise OptionsError("target_lead_time_days must be below worst_lead_time_days")
        if self.target_deliveries >= self.worst_deliveries:
            raise OptionsError("target_deliveries must be below worst_deliveries")
        _int(self.max_options, "max_options", 1, 6)
        _int(self.max_search_merchants, "max_search_merchants", 1, 12)
        _int(self.max_solver_calls, "max_solver_calls", 1, 5000)

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
