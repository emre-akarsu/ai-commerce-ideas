"""Thresholds for the verification checks. They come from the resolved deployment profile
(`verification:` block); callers pass that block to `VerifyConfig.from_mapping`. The defaults here
exist so the component can be tested alone: a deployment never relies on them (CLAUDE.md: never
hard-code thresholds)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class VerifyConfig:
    arith_abs_tolerance: Decimal = Decimal("0.01")   # currency units: rounding on a line total
    arith_rel_tolerance: Decimal = Decimal("0.005")  # share of the expected value
    vat_rel_tolerance: Decimal = Decimal("0.005")    # share, on the VAT arithmetic
    price_jump_ratio: Decimal = Decimal("1.5")       # flag above last paid x ratio or below / ratio
    unit_basis_tolerance: Decimal = Decimal("0.05")  # how close a price must be to a unit factor
    quantity_ratio: Decimal = Decimal("5")           # flag above usual x ratio or below / ratio
    min_history_points: int = 2                      # history needed before any plausibility flag

    def __post_init__(self) -> None:
        for name in ("arith_abs_tolerance", "arith_rel_tolerance", "vat_rel_tolerance",
                     "unit_basis_tolerance"):
            if not isinstance(getattr(self, name), Decimal) or getattr(self, name) < 0:
                raise ValueError(f"{name} must be a Decimal >= 0")
        for name in ("price_jump_ratio", "quantity_ratio"):
            if not isinstance(getattr(self, name), Decimal) or getattr(self, name) <= 1:
                raise ValueError(f"{name} must be a Decimal > 1")
        if not isinstance(self.min_history_points, int) or self.min_history_points < 1:
            raise ValueError("min_history_points must be an int >= 1")

    @classmethod
    def from_mapping(cls, block: Mapping[str, object]) -> VerifyConfig:
        """Build from a profile `verification` block; unknown keys are refused."""
        known = {f.name for f in fields(cls)}
        extra = sorted(set(block) - known)
        if extra:
            raise ValueError(f"unknown verification keys: {extra}")
        kwargs: dict[str, object] = {}
        for key, raw in block.items():
            if key == "min_history_points":
                kwargs[key] = int(str(raw))
            else:
                try:
                    kwargs[key] = Decimal(str(raw))
                except InvalidOperation as exc:
                    raise ValueError(f"{key}: not a number") from exc
        return cls(**kwargs)  # type: ignore[arg-type]
