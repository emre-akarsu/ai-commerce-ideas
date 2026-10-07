"""Saved quote to outbound quote requests, through the existing approval and send flow.

Reads the templated messages of the quote's price book (`components.pricebook.rfq_messages`,
no model text) and hands each to `PurchasingService.prepare_text_rfq`, which holds it for the
hash-bound approval of `approve_send` (R1). This module has no mail credentials and no import
path to the transport; it sends and approves nothing. Merchant to supplier mapping: a price-book
`merchant_id` is the id of the tenant's own verified `Vendor`; a merchant with no verified vendor
is refused (nothing is prepared for any merchant in that call). See
docs/architecture/quote-to-rfq.md.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from aiplat.ctx import Ctx

from .service_port import Conflict, PurchasingServicePort, TextRfqDraft

MODES = ("per_supplier", "per_item")


class QuoteReader(Protocol):
    def price_books(self, ctx: Ctx, quote_id: str | None) -> dict[str, Any]: ...


class QuoteRfqDrafter:
    def __init__(self, quotes: QuoteReader, purchasing: PurchasingServicePort) -> None:
        self._quotes = quotes
        self._purchasing = purchasing

    def _messages(self, ctx: Ctx, quote_id: str, mode: str,
                  merchant_ids: Sequence[str] | None) -> list[dict[str, Any]]:
        if mode not in MODES:
            raise Conflict("unknown mode")
        book = self._quotes.price_books(ctx, quote_id)  # NotFound for another tenant's quote
        found: list[dict[str, Any]] = list(book.get("rfq_messages", {}).get(mode, []))
        if merchant_ids is not None:
            wanted = set(merchant_ids)
            missing = sorted(wanted - {m["merchant_id"] for m in found})
            if missing:
                raise Conflict(f"no quote request lines for merchant {missing[0]!r}")
            found = [m for m in found if m["merchant_id"] in wanted]
        if not found:
            raise Conflict("this quote has no lines to request")
        return found

    def create(self, ctx: Ctx, quote_id: str, mode: str = "per_supplier",
               merchant_ids: Sequence[str] | None = None) -> list[TextRfqDraft]:
        """Prepare one message per supplier (or per line). All-or-nothing: every message passes the
        service's dry run before the first is stored. A repeat call returns the drafts that already
        wait, it does not add duplicates."""
        msgs = self._messages(ctx, quote_id, mode, merchant_ids)
        for m in msgs:
            self._purchasing.check_text_rfq(
                ctx, vendor_id=m["merchant_id"], subject=m["subject"], body=m["body"],
                line_refs=list(m["line_ids"]), quote_ref=quote_id, mode=mode)
        waiting = {(d.prepared.vendor.id, tuple(d.line_refs), d.mode)
                   for d in self._purchasing.list_text_rfqs(ctx, quote_id)}
        for m in msgs:
            if (m["merchant_id"], tuple(m["line_ids"]), mode) not in waiting:
                self._purchasing.prepare_text_rfq(
                    ctx, vendor_id=m["merchant_id"], subject=m["subject"], body=m["body"],
                    line_refs=list(m["line_ids"]), quote_ref=quote_id, mode=mode)
        keep = {m["merchant_id"] for m in msgs}
        return [d for d in self._purchasing.list_text_rfqs(ctx, quote_id)
                if d.mode == mode and d.prepared.vendor.id in keep]

    def list(self, ctx: Ctx, quote_id: str) -> list[TextRfqDraft]:
        """Read-only. A quote of another tenant is a NotFound."""
        self._quotes.price_books(ctx, quote_id)
        return self._purchasing.list_text_rfqs(ctx, quote_id)
