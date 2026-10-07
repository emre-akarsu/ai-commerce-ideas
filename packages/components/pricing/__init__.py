"""Offer and best-price engine (stage 2 after product matching). Pure Python, offline, Decimal.

See docs/architecture/pricing-engine.md. Nothing here reads a network, a file or a clock: data is
handed in, time comes from an injected `Clock`, and nothing is sent or ordered.
"""

from .best_price import price_line, price_line_from_offers
from .config import PricingConfig
from .errors import (
    DuplicateOfferError,
    OfferValidationError,
    PricingConfigError,
    PricingError,
    RepositoryError,
    SourceError,
    TenantScopeError,
)
from .lines import AmbiguousLine, IndexBand, MatchedSku, ResolvedLine, UnmatchedLine
from .models import (
    DeliveryTerms,
    DeliveryTier,
    Offer,
    PackSize,
    Price,
    PricePer,
    Provenance,
    SourceKind,
    StockStatus,
    VatBasis,
    Visibility,
)
from .repository import (
    InMemoryOfferStore,
    OfferFilter,
    OfferRepository,
    SharedOfferWriter,
    TenantOfferRepository,
)
from .results import ExcludedOffer, IndicativeRange, LineStatus, PricedLine, PricedOffer
from .units import Unit, UnitBasis

__all__ = [
    "AmbiguousLine",
    "DeliveryTerms",
    "DeliveryTier",
    "DuplicateOfferError",
    "ExcludedOffer",
    "InMemoryOfferStore",
    "IndexBand",
    "IndicativeRange",
    "LineStatus",
    "MatchedSku",
    "Offer",
    "OfferFilter",
    "OfferRepository",
    "OfferValidationError",
    "PackSize",
    "Price",
    "PricePer",
    "PricedLine",
    "PricedOffer",
    "PricingConfig",
    "PricingConfigError",
    "PricingError",
    "Provenance",
    "RepositoryError",
    "ResolvedLine",
    "SharedOfferWriter",
    "SourceError",
    "SourceKind",
    "StockStatus",
    "TenantOfferRepository",
    "TenantScopeError",
    "Unit",
    "UnitBasis",
    "UnmatchedLine",
    "VatBasis",
    "Visibility",
    "price_line",
    "price_line_from_offers",
]
