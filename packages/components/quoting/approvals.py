"""The approval loop: a person's choice is stored tenant-scoped, and the next run uses it.

`approve_match` writes through the matching engine's public API (`MatchingEngine.learn`), which
stores the choice in the tenant-scoped `ApprovedMatchStore`. The next time the same normalised
line is matched for that tenant, the matching engine returns `previously_approved` straight away
(after re-running its own deterministic checks, so an approval can never override a failed check),
and the quote trace says "previously approved". Another tenant's store is never read or written.

A match approval says "this product satisfies this line". It is not a substitution approval: for
a line that names a brand, MPN or GTIN, approving a product that does not carry that identity is
refused here (that needs a recorded `SubstitutionApproval`, hard rule 2).
"""

from __future__ import annotations

from collections.abc import Sequence

from components.matching.approvals import ApprovalRecord
from components.matching.models import OrderLine

from .context import QuotingContext
from .errors import QuotingError
from .identity import carries_identity, is_named
from .models import LineRequest, inert_text


def approve_match(
    ctx: QuotingContext, tenant_id: str, line: LineRequest | OrderLine,
    sku_id: str | Sequence[str], approver: str,
) -> ApprovalRecord:
    """Record that `approver` chose `sku_id` (or this group of SKUs) for `line`, for this tenant."""
    order = line.order_line if isinstance(line, LineRequest) else line.model_copy(
        update={"text": inert_text(line.text)})
    skus = [sku_id] if isinstance(sku_id, str) else list(sku_id)
    if not skus:
        raise QuotingError("approve at least one SKU")
    if not approver.strip():
        raise QuotingError("an approver is required")
    index = ctx.engine.index
    parsed = index.parser.parse(order)
    for sku in skus:
        item = index.get(sku)
        if item is None:
            raise QuotingError(f"unknown SKU {sku!r}")
        if is_named(parsed) and not carries_identity(parsed, item, index.ontology.normaliser):
            raise QuotingError(
                f"{sku} does not carry the brand, MPN or GTIN the line names: that is a "
                "substitution and needs a substitution approval, not a match approval")
    try:
        return ctx.engine.learn(tenant_id, order, skus, approver)
    except ValueError as exc:
        raise QuotingError(str(exc)) from exc
