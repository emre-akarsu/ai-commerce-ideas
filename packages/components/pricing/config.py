"""Pricing configuration: a plain dataclass the CALLER builds from the resolved deployment profile.

Components never import `aiplat`, so the profile's `money`, `tax` and `pricing` sections are read
from a mapping (`resolved.profile.model_dump()` or `model_dump(mode="json")` both work) and the
defaults below mirror `aiplat.profile.PricingPolicy` and `TaxPolicy`; tests/pricing/test_config.py
keeps the two in step. Nothing here hard-codes a currency or a tax rate: the VAT rate defaults to 0
exactly as the profile does, and the base currency has no default and must be supplied.

Keys the profile does not have yet live in the separate ``engine`` section (see ENGINE_KEYS); they
are tuning knobs of this engine, not market policy, and are proposals for profile keys.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Any, Literal, TypeVar, cast

from .decimals import check_decimal
from .errors import OfferValidationError, PricingConfigError
from .models import Offer, SourceKind

CompareBasis = Literal["ex_tax", "inc_tax"]
StalePolicy = Literal["exclude_from_best", "flag_only"]
UnknownBasisPolicy = Literal["flag_require_approval", "assume_default_flag"]
BasisDefault = Literal["ex_tax", "inc_tax", "unknown"]

# Mirrors aiplat.profile._default_offer_ages (kept equal by tests/pricing/test_config.py).
DEFAULT_MAX_OFFER_AGE_HOURS: Mapping[SourceKind, int] = MappingProxyType(
    {
        SourceKind.TRADE_FEED: 168,
        SourceKind.MERCHANT_API: 24,
        SourceKind.AFFILIATE_FEED: 48,
        SourceKind.SEARCH_SNAPSHOT: 24,
        SourceKind.MANUAL_QUOTE: 720,
    }
)

_MONEY_KEYS = frozenset(
    {"base_currency", "accepted_currencies", "symbol_map", "bare_dollar_currency",
     "assumed_currency"}
)
_TAX_KEYS = frozenset(
    {"name", "standard_rate", "quote_basis_default", "unknown_basis", "ask_basis_in_rfq"}
)
_PRICING_KEYS = frozenset(
    {"max_offer_age_hours", "stale_offers", "compare_basis", "include_delivery_in_comparison",
     "price_outlier_ratio", "allow_search_snapshot_sources"}
)
ENGINE_KEYS = frozenset(
    {"outlier_offers", "outlier_min_peers", "runner_up_count", "minor_unit_places",
     "basket_exact_max_lines", "basket_exact_max_merchants", "basket_node_budget",
     "future_skew_minutes"}
)

_T = TypeVar("_T")
_HALF = Decimal("0.5")


def _err(where: str, msg: str) -> PricingConfigError:
    return PricingConfigError(f"{where}: {msg}")


def _section(data: Mapping[str, Any], name: str, allowed: Collection[str]) -> Mapping[str, Any]:
    raw = data.get(name)
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        raise _err(name, "must be a mapping")
    unknown = sorted(str(k) for k in raw if k not in allowed)
    if unknown:
        raise _err(name, f"unknown keys {unknown}")
    return raw


def _decimal(value: object, where: str, lo: Decimal, hi: Decimal) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise _err(where, "must be a Decimal, an int or a decimal string, never a float")
    try:
        if isinstance(value, Decimal):
            parsed = value
        elif isinstance(value, int | str):
            parsed = Decimal(value)
        else:
            raise _err(where, "must be a Decimal, an int or a decimal string")
    except InvalidOperation:
        raise _err(where, f"{value!r} is not a number") from None
    return check_decimal(parsed, where, minimum=lo, maximum=hi, error=PricingConfigError)


def _int(value: object, where: str, lo: int, hi: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
        raise _err(where, f"must be an integer between {lo} and {hi}")
    return value


def _flag(value: object, where: str) -> bool:
    if not isinstance(value, bool):
        raise _err(where, "must be true or false")
    return value


def _choice(value: object, allowed: tuple[_T, ...], where: str) -> _T:
    if not isinstance(value, str) or value not in allowed:
        raise _err(where, f"must be one of {list(allowed)}")
    return cast(_T, value)


def _currency(value: object, where: str) -> str:
    if not isinstance(value, str) or len(value) != 3 or not value.isascii() or not value.isupper():
        raise _err(where, "must be a 3-letter upper-case currency code")
    return value


def _age_limits(raw: object) -> Mapping[SourceKind, int]:
    """Profile limits override the defaults per kind; a kind left out keeps its default, so no
    source kind is ever unlimited."""
    limits = dict(DEFAULT_MAX_OFFER_AGE_HOURS)
    if raw is None:
        return MappingProxyType(limits)
    if not isinstance(raw, Mapping):
        raise _err("pricing.max_offer_age_hours", "must be a mapping")
    for kind, hours in raw.items():
        try:
            key = SourceKind(kind)
        except ValueError:
            raise _err("pricing.max_offer_age_hours", f"unknown source kind {kind!r}") from None
        limits[key] = _int(hours, f"pricing.max_offer_age_hours[{key.value}]", 1, 24 * 365)
    return MappingProxyType(limits)


def _symbols(raw: object, accepted: frozenset[str]) -> Mapping[str, str]:
    if raw is None:
        return MappingProxyType({})
    if not isinstance(raw, Mapping):
        raise _err("money.symbol_map", "must be a mapping")
    out: dict[str, str] = {}
    for symbol, iso in raw.items():
        code = _currency(iso, f"money.symbol_map[{symbol!r}]")
        if code not in accepted:
            raise _err("money.symbol_map", f"{symbol!r} maps to a currency that is not accepted")
        out[str(symbol)] = code
    return MappingProxyType(out)


def _empty_symbols() -> Mapping[str, str]:
    return MappingProxyType({})


def _default_ages() -> Mapping[SourceKind, int]:
    return DEFAULT_MAX_OFFER_AGE_HOURS


@dataclass(frozen=True)
class PricingConfig:
    # money (profile.money). There is no default currency: the deployment must say.
    base_currency: str
    accepted_currencies: frozenset[str]
    # tax (profile.tax). The rate defaults to 0 as in the profile; the UK profile sets 0.20.
    vat_rate: Decimal = Decimal(0)
    unknown_basis: UnknownBasisPolicy = "flag_require_approval"
    quote_basis_default: BasisDefault = "unknown"
    # pricing (profile.pricing)
    compare_basis: CompareBasis = "ex_tax"
    include_delivery_in_comparison: bool = True
    stale_offers: StalePolicy = "exclude_from_best"
    max_offer_age_hours: Mapping[SourceKind, int] = field(default_factory=_default_ages)
    price_outlier_ratio: Decimal = Decimal(3)
    allow_search_snapshot_sources: bool = False
    symbol_map: Mapping[str, str] = field(default_factory=_empty_symbols)
    # engine-only knobs (not profile keys yet)
    outlier_offers: StalePolicy = "exclude_from_best"
    outlier_min_peers: int = 3
    runner_up_count: int = 3
    minor_unit_places: int = 2
    basket_exact_max_lines: int = 15
    basket_exact_max_merchants: int = 6
    basket_node_budget: int = 500_000
    future_skew_minutes: int = 5

    @property
    def tax_active(self) -> bool:
        """With a zero rate there is no VAT handling at all (as in rfq.quotes.normalise)."""
        return self.vat_rate > 0

    def max_age_hours(self, kind: SourceKind) -> int:
        return self.max_offer_age_hours[kind]

    def check_offer(self, offer: Offer) -> None:
        """The deployment-dependent part of offer validation (the model checks the rest)."""
        if offer.price.currency not in self.accepted_currencies:
            raise OfferValidationError(
                f"currency {offer.price.currency} is not accepted by this deployment"
            )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> PricingConfig:
        """Build from a profile-shaped mapping (`money`, `tax`, `pricing`, optional `engine`).

        Other top-level sections (`locale`, `legal`, ...) are ignored so a whole profile dump can
        be passed; unknown keys inside the four sections are errors so typos cannot go unnoticed.
        Missing keys take the profile defaults. Floats are rejected for every decimal."""
        if not isinstance(data, Mapping):
            raise PricingConfigError("config must be a mapping")
        money = _section(data, "money", _MONEY_KEYS)
        tax = _section(data, "tax", _TAX_KEYS)
        pricing = _section(data, "pricing", _PRICING_KEYS)
        engine = _section(data, "engine", ENGINE_KEYS)
        base, accepted = _money(money)
        return cls(
            base_currency=base,
            accepted_currencies=accepted,
            symbol_map=_symbols(money.get("symbol_map"), accepted),
            **_tax_kwargs(tax),
            **_pricing_kwargs(pricing),
            **_engine_kwargs(engine),
        )


def _money(money: Mapping[str, Any]) -> tuple[str, frozenset[str]]:
    if "base_currency" not in money:
        raise _err("money.base_currency", "is required (there is no default currency)")
    base = _currency(money["base_currency"], "money.base_currency")
    raw = money.get("accepted_currencies")
    if raw is None:
        return base, frozenset({base})
    if isinstance(raw, str) or not isinstance(raw, Collection):
        raise _err("money.accepted_currencies", "must be a list of currency codes")
    accepted = frozenset(_currency(c, "money.accepted_currencies") for c in raw)
    if base not in accepted:
        raise _err("money.accepted_currencies", "must include the base currency")
    return base, accepted


def _tax_kwargs(tax: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if "standard_rate" in tax:
        out["vat_rate"] = _decimal(tax["standard_rate"], "tax.standard_rate", Decimal(0), _HALF)
    if "unknown_basis" in tax:
        out["unknown_basis"] = _choice(
            tax["unknown_basis"], ("flag_require_approval", "assume_default_flag"),
            "tax.unknown_basis")
    if "quote_basis_default" in tax:
        out["quote_basis_default"] = _choice(
            tax["quote_basis_default"], ("ex_tax", "inc_tax", "unknown"),
            "tax.quote_basis_default")
    return out


def _pricing_kwargs(pricing: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {"max_offer_age_hours": _age_limits(pricing.get("max_offer_age_hours"))}
    if "stale_offers" in pricing:
        out["stale_offers"] = _choice(
            pricing["stale_offers"], ("exclude_from_best", "flag_only"), "pricing.stale_offers")
    if "compare_basis" in pricing:
        out["compare_basis"] = _choice(
            pricing["compare_basis"], ("ex_tax", "inc_tax"), "pricing.compare_basis")
    if "include_delivery_in_comparison" in pricing:
        out["include_delivery_in_comparison"] = _flag(
            pricing["include_delivery_in_comparison"], "pricing.include_delivery_in_comparison")
    if "price_outlier_ratio" in pricing:
        out["price_outlier_ratio"] = _decimal(
            pricing["price_outlier_ratio"], "pricing.price_outlier_ratio", Decimal("1.5"),
            Decimal(10))
    if "allow_search_snapshot_sources" in pricing:
        out["allow_search_snapshot_sources"] = _flag(
            pricing["allow_search_snapshot_sources"], "pricing.allow_search_snapshot_sources")
    return out


def _engine_kwargs(engine: Mapping[str, Any]) -> dict[str, Any]:
    bounds = {
        "outlier_min_peers": (2, 50), "runner_up_count": (0, 20), "minor_unit_places": (0, 6),
        "basket_exact_max_lines": (1, 40), "basket_exact_max_merchants": (1, 12),
        "basket_node_budget": (1_000, 50_000_000), "future_skew_minutes": (0, 1440),
    }
    out: dict[str, Any] = {}
    for key, (lo, hi) in bounds.items():
        if key in engine:
            out[key] = _int(engine[key], f"engine.{key}", lo, hi)
    if "outlier_offers" in engine:
        out["outlier_offers"] = _choice(
            engine["outlier_offers"], ("exclude_from_best", "flag_only"), "engine.outlier_offers")
    return out
