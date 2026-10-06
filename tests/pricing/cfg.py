"""Configuration helpers for the pricing tests (kept free of other pricing imports)."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from components.pricing import PricingConfig

NOW = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)


def config_mapping(
    *, pricing: Mapping[str, Any] | None = None, tax: Mapping[str, Any] | None = None,
    **engine: Any,
) -> dict[str, Any]:
    """A UK-like deployment (GBP, 20% VAT, unknown VAT goes to a human, ex-VAT comparison)."""
    return {
        "money": {
            "base_currency": "GBP",
            "accepted_currencies": ["GBP", "EUR", "USD"],
            "symbol_map": {"£": "GBP", "€": "EUR", "US$": "USD"},
        },
        "tax": {
            "standard_rate": "0.20",
            "quote_basis_default": "ex_tax",
            "unknown_basis": "flag_require_approval",
            **(tax or {}),
        },
        "pricing": dict(pricing or {}),
        "engine": dict(engine),
    }


def config(
    *, pricing: Mapping[str, Any] | None = None, tax: Mapping[str, Any] | None = None,
    **engine: Any,
) -> PricingConfig:
    return PricingConfig.from_mapping(config_mapping(pricing=pricing, tax=tax, **engine))
