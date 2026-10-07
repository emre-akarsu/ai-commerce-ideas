"""Quote for products (stage 2): job kits -> product matching -> offer pricing -> draft quote.

Ties the finished matching, pricing and job-kit components together; none of them imports this
package. Pure Python, offline, Decimal. Nothing is sent or ordered. See
docs/architecture/quoting.md.
"""

from .approvals import approve_match
from .config import QuotingConfig
from .context import QuotingContext, TenantOffers
from .errors import QuotingConfigError, QuotingError
from .export import FORMAT, dumps, quote_draft_ui
from .kit_lines import order_lines_from_kit
from .options import build_options, quote_options
from .options_config import OptionsConfig, OptionsError
from .options_export import OPTIONS_FORMAT, options_dumps, quote_options_ui
from .options_models import OptionSet, QuoteOption
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
    "OPTIONS_FORMAT",
    "Alternative",
    "Bucket",
    "CandidateView",
    "KitOrderLines",
    "KitRef",
    "LineChoice",
    "LineRequest",
    "LineResult",
    "LineTrace",
    "OptionSet",
    "OptionsConfig",
    "OptionsError",
    "QuoteOption",
    "QuoteResult",
    "QuotingConfig",
    "QuotingConfigError",
    "QuotingContext",
    "QuotingError",
    "ReviewPayload",
    "SkippedLine",
    "TenantOffers",
    "approve_match",
    "build_options",
    "build_quote",
    "dumps",
    "options_dumps",
    "order_lines_from_kit",
    "quote_draft_ui",
    "quote_options",
    "quote_options_ui",
    "search_best_price",
]
