"""Gate thresholds as a plain dataclass.

Components never import `aiplat`, so the caller builds this from the resolved deployment profile
(`GatePolicy.from_mapping(profile.matching.model_dump())`). The defaults equal the profile's v1
defaults (docs/product/07-product-matching-engine-spec-v2.md), which must be re-tuned on real
order lines. `group_band` and `judge_margin` are extensions of this component (documented in
docs/architecture/matching-engine.md) and have no profile key yet.

Hard rules have no switch: `require_zero_failed_checks` and `quantity_size_ambiguity_forces_review`
are accepted in a mapping only as True.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields
from decimal import Decimal, InvalidOperation
from typing import Any

_INVARIANTS = ("require_zero_failed_checks", "quantity_size_ambiguity_forces_review")
_DECIMALS = ("auto_accept_min_score", "auto_accept_min_lead", "reject_below_score",
             "llm_cost_ceiling_per_1000_lines", "group_band", "judge_margin")
_INTS = ("retrieve_top_k", "judge_top_k", "judge_examples", "review_show_top")


class PolicyError(ValueError):
    """A gate policy value is out of range, mis-typed, unknown, or weakens a hard rule."""


def _decimal(key: str, value: Any) -> Decimal:
    if isinstance(value, float):
        raise PolicyError(f"{key}: pass a string or Decimal, not a float")
    try:
        d = Decimal(str(value))
    except InvalidOperation as exc:
        raise PolicyError(f"{key}: {value!r} is not a decimal") from exc
    if not d.is_finite():
        raise PolicyError(f"{key}: {value!r} is not finite")
    return d


@dataclass(frozen=True)
class GatePolicy:
    auto_accept_min_score: Decimal = Decimal("0.75")
    auto_accept_min_lead: Decimal = Decimal("0.05")
    reject_below_score: Decimal = Decimal("0.35")
    retrieve_top_k: int = 50
    judge_top_k: int = 5
    judge_examples: int = 3
    review_show_top: int = 3
    llm_cost_ceiling_per_1000_lines: Decimal = Decimal("1.50")
    group_band: Decimal = Decimal("0.10")
    judge_margin: Decimal = Decimal("0.05")

    def __post_init__(self) -> None:
        if not Decimal("0.5") <= self.auto_accept_min_score <= 1:
            raise PolicyError("auto_accept_min_score must be in 0.5..1")
        if not 0 <= self.auto_accept_min_lead <= Decimal("0.5"):
            raise PolicyError("auto_accept_min_lead must be in 0..0.5")
        if not 0 <= self.reject_below_score <= Decimal("0.7"):
            raise PolicyError("reject_below_score must be in 0..0.7")
        if self.reject_below_score >= self.auto_accept_min_score:
            raise PolicyError("reject_below_score must be below auto_accept_min_score")
        if not 5 <= self.retrieve_top_k <= 200:
            raise PolicyError("retrieve_top_k must be in 5..200")
        if not 2 <= self.judge_top_k <= 10 or self.judge_top_k > self.retrieve_top_k:
            raise PolicyError("judge_top_k must be in 2..10 and not exceed retrieve_top_k")
        if not 0 <= self.judge_examples <= 10:
            raise PolicyError("judge_examples must be in 0..10")
        if not 1 <= self.review_show_top <= 10:
            raise PolicyError("review_show_top must be in 1..10")
        if self.llm_cost_ceiling_per_1000_lines <= 0:
            raise PolicyError("llm_cost_ceiling_per_1000_lines must be positive")
        half = Decimal("0.5")
        if not 0 <= self.group_band <= half or not 0 <= self.judge_margin <= half:
            raise PolicyError("group_band and judge_margin must be in 0..0.5")

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> GatePolicy:
        known = {f.name for f in fields(cls)}
        unknown = set(raw) - known - set(_INVARIANTS)
        if unknown:
            raise PolicyError(f"unknown gate policy keys: {sorted(unknown)}")
        for key in _INVARIANTS:
            if key in raw and raw[key] is not True:
                raise PolicyError(f"{key} cannot be turned off (hard rule)")
        values: dict[str, Any] = {}
        for key, value in raw.items():
            if key in _INVARIANTS:
                continue
            if key in _DECIMALS:
                values[key] = _decimal(key, value)
            elif key in _INTS:
                if isinstance(value, bool) or not isinstance(value, int):
                    raise PolicyError(f"{key} must be an integer")
                values[key] = value
        return cls(**values)

    def snapshot(self) -> dict[str, str]:
        """Every value as text, for the audit trail of one decision."""
        return {f.name: str(getattr(self, f.name)) for f in fields(self)}
