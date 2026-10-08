"""Offer and best-price engine (stage 2 after product matching). Pure Python, offline, Decimal.

See docs/architecture/pricing-engine.md. Nothing here reads a network, a file or a clock: data is
handed in, time comes from an injected `Clock`, and nothing is sent or ordered.
"""

from .adapters import CsvMapping, CsvPriceFileSource, JsonShoppingResultsSource
from .basket import BasketChoice, BasketResult, MerchantOrder, optimise_basket
from .best_price import price_line, price_line_from_offers
from .config import PricingConfig
from .eligibility import PriceType, quote_line_eligible
from .errors import (
    DuplicateOfferError,
    OfferValidationError,
    PricingConfigError,
    PricingError,
    RepositoryError,
    SourceError,
    TenantScopeError,
)
from .feasibility import Feasibility, FeasibilityStatus, assess_feasibility
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
    Tranche,
    VatBasis,
    Visibility,
)
from .quote import QuoteDraft, build_quote_draft, quote_lines
from .repository import (
    InMemoryOfferStore,
    OfferFilter,
    OfferRepository,
    SharedOfferWriter,
    TenantOfferRepository,
)
from .results import ExcludedOffer, IndicativeRange, LineStatus, PricedLine, PricedOffer
from .sources import (
    HttpClient,
    OfferQuery,
    OfferSource,
    QuarantinedRecord,
    RawRecord,
    SourceDeclaration,
    ingest,
    parse_raw_offer,
)
from .units import Unit, UnitBasis

__all__ = [
    "AmbiguousLine",
    "BasketChoice",
    "BasketResult",
    "CsvMapping",
    "CsvPriceFileSource",
    "DeliveryTerms",
    "DeliveryTier",
    "DuplicateOfferError",
    "ExcludedOffer",
    "Feasibility",
    "FeasibilityStatus",
    "HttpClient",
    "InMemoryOfferStore",
    "IndexBand",
    "IndicativeRange",
    "JsonShoppingResultsSource",
    "LineStatus",
    "MatchedSku",
    "MerchantOrder",
    "Offer",
    "OfferFilter",
    "OfferQuery",
    "OfferRepository",
    "OfferSource",
    "OfferValidationError",
    "PackSize",
    "Price",
    "PricePer",
    "PriceType",
    "PricedLine",
    "PricedOffer",
    "PricingConfig",
    "PricingConfigError",
    "PricingError",
    "Provenance",
    "QuarantinedRecord",
    "QuoteDraft",
    "RawRecord",
    "RepositoryError",
    "ResolvedLine",
    "SharedOfferWriter",
    "SourceDeclaration",
    "SourceError",
    "SourceKind",
    "StockStatus",
    "TenantOfferRepository",
    "TenantScopeError",
    "Tranche",
    "Unit",
    "UnitBasis",
    "UnmatchedLine",
    "VatBasis",
    "Visibility",
    "assess_feasibility",
    "build_quote_draft",
    "ingest",
    "optimise_basket",
    "parse_raw_offer",
    "price_line",
    "price_line_from_offers",
    "quote_line_eligible",
    "quote_lines",
]
