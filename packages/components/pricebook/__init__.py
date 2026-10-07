"""Price book: per tenant and merchant, how current the tenant's prices are (strategy phase 1,
steps 1.2, 1.4 and 1.6), plus the request-a-price-file drafts and the gap list for RFQs.

Pure Python, offline, Decimal; time comes from an injected `Clock`. Nothing is fetched, sent or
ordered. See docs/architecture/pricebook.md.
"""

from .book import LoadReportLike, TenantOffers, build_price_book, summaries_from_reports
from .errors import PriceBookError, RequestTemplateError
from .export import FORMAT, dumps, price_books_ui
from .gaps import RfqGapGroup, RfqGapItem, compute_gaps, rfq_for_gaps
from .ladder import BUILT_LEVELS, LEVEL_LABELS, ladder_level
from .models import (
    Coverage,
    FreshnessSummary,
    GapLine,
    ImportSummary,
    MerchantBook,
    MerchantInfo,
    MerchantStatus,
    OfferState,
    PriceBook,
    SpendBasis,
    VatSummary,
)
from .requests import (
    ACCOUNT_REFERENCE_MISSING,
    PLACEHOLDERS,
    RequestContext,
    RequestDraft,
    RequestTemplate,
    draft_request,
    draft_requests,
)
from .rfq_messages import RfqMessage, RfqMode, RfqTemplate, draft_rfq_messages

__all__ = [
    "ACCOUNT_REFERENCE_MISSING",
    "BUILT_LEVELS",
    "FORMAT",
    "LEVEL_LABELS",
    "PLACEHOLDERS",
    "Coverage",
    "FreshnessSummary",
    "GapLine",
    "ImportSummary",
    "LoadReportLike",
    "MerchantBook",
    "MerchantInfo",
    "MerchantStatus",
    "OfferState",
    "PriceBook",
    "PriceBookError",
    "RequestContext",
    "RequestDraft",
    "RequestTemplate",
    "RequestTemplateError",
    "RfqGapGroup",
    "RfqGapItem",
    "RfqMessage",
    "RfqMode",
    "RfqTemplate",
    "SpendBasis",
    "TenantOffers",
    "VatSummary",
    "build_price_book",
    "compute_gaps",
    "draft_request",
    "draft_requests",
    "draft_rfq_messages",
    "dumps",
    "ladder_level",
    "price_books_ui",
    "rfq_for_gaps",
    "summaries_from_reports",
]
