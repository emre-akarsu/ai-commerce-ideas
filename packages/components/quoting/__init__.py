"""Quote for products (stage 2): job kits -> product matching -> offer pricing -> draft quote.

Ties the finished matching, pricing and job-kit components together; none of them imports this
package. Pure Python, offline, Decimal. Nothing is sent or ordered. See
docs/architecture/quoting.md.
"""

from .config import QuotingConfig
from .context import QuotingContext, TenantOffers
from .errors import QuotingConfigError, QuotingError
from .approvals import approve_match
from .export import FORMAT, dumps, quote_draft_ui
from .kit_lines import order_lines_from_kit
from .models import (
    Alternative,
    Bucket,
    CandidateView,
    KitOrderLines,
    KitRef,
    LineChoice,
    LineRequest,
    LineResult,
    LineTrace,
    QuoteResult,
    ReviewPayload,
    SkippedLine,
)
from .quote import build_quote
from .search import search_best_price

__all__ = [
    "FORMAT",
    "Alternative",
    "Bucket",
    "CandidateView",
    "KitOrderLines",
    "KitRef",
    "LineChoice",
    "LineRequest",
    "LineResult",
    "LineTrace",
    "QuoteResult",
    "QuotingConfig",
    "QuotingConfigError",
    "QuotingContext",
    "QuotingError",
    "ReviewPayload",
    "SkippedLine",
    "TenantOffers",
    "approve_match",
    "build_quote",
    "dumps",
    "order_lines_from_kit",
    "quote_draft_ui",
    "search_best_price",
]
