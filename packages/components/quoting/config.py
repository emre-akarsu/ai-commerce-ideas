"""Quoting configuration: a plain dataclass the CALLER fills from the resolved profile.

Components never import `aiplat`. The market behaviour that matters here (currency, VAT basis,
staleness, thresholds) lives in `PricingConfig` and `GatePolicy`, which the caller builds from the
profile; this dataclass only holds presentation limits of the quoting step. Keys have no profile
counterpart yet (proposals), and none of them can weaken a hard rule.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields
from typing import Any

from .errors import QuotingConfigError

_BOUNDS = {"review_top": (1, 10), "alternatives_max": (0, 10)}


@dataclass(frozen=True)
class QuotingConfig:
    review_top: int = 3  # candidates shown for a line that needs a person
    alternatives_max: int = 3  # "suggested alternative, needs approval" entries for a named line
    quote_id_prefix: str = "quote"

    def __post_init__(self) -> None:
        for key, (lo, hi) in _BOUNDS.items():
            value = getattr(self, key)
            if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
                raise QuotingConfigError(f"{key} must be an integer between {lo} and {hi}")
        prefix = self.quote_id_prefix
        if not (isinstance(prefix, str) and prefix.isascii() and prefix.replace("-", "").isalnum()
                and 1 <= len(prefix) <= 24):
            raise QuotingConfigError("quote_id_prefix must be 1-24 letters, digits or hyphens")

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> QuotingConfig:
        known = {f.name for f in fields(cls)}
        unknown = sorted(set(raw) - known)
        if unknown:
            raise QuotingConfigError(f"unknown quoting keys: {unknown}")
        return cls(**dict(raw))
