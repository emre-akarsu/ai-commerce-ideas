"""Job-kit templates: job type -> scope -> module -> line, with a small question budget.

Pure Python, offline, Decimal quantities. See docs/architecture/job-kits.md.
"""

from .library import JobKitLibrary, export_ui_json, load_library, resolve
from .model import (
    Assumption,
    KitError,
    ResolvedKit,
    ResolvedLine,
    ResolvedOption,
    RuleResult,
)

__all__ = [
    "Assumption",
    "JobKitLibrary",
    "KitError",
    "ResolvedKit",
    "ResolvedLine",
    "ResolvedOption",
    "RuleResult",
    "export_ui_json",
    "load_library",
    "resolve",
]
