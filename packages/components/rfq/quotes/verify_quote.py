"""Verification of one ingested quote (docs/product/12-next-version-improvement-triage.md, item 9).

Runs the verification layer over a normalised `Quote`: the shadow diff between the primary
reading and an independent second reading, the number checks on the normalised price, and, when a
history is supplied, plausibility against the customer's own price history. It returns findings
only. It never approves a quote, never picks between two readings, never fills a blank field and
never changes a recipient, amount or rule (spec R1, R3, R6, R9).
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from components.core.domain import ExtractedQuote, Quote
from components.verify.checks import QuoteLineFacts, check_line
from components.verify.config import VerifyConfig
from components.verify.findings import Finding, Severity, explain
from components.verify.history import PriceHistory
from components.verify.plausibility import check_plausibility
from components.verify.shadow import diff_readings

__all__ = ["REVIEW_FLAG", "ATTENTION_FLAG", "finding_payload", "flags_for", "verify_quote"]

REVIEW_FLAG = "verification_review"    # a finding that keeps the quote out of "clean"
ATTENTION_FLAG = "verification_flag"   # a finding worth a look, shown on the approval page


def verify_quote(
    quote: Quote,
    primary: ExtractedQuote,
    shadow: ExtractedQuote | None,
    *,
    cfg: VerifyConfig,
    history: PriceHistory | None = None,
    merchant_id: str = "",
    quantity: Decimal | None = None,
    item_key: str | None = None,
) -> tuple[Finding, ...]:
    """`primary` is the reading the quote was built from; `shadow` an independent second reading
    of the same text (None when no second reader is configured). `history` is bound to the
    quote's tenant. `item_key` is the key the history is filed under (the caller's normalised part
    number); it defaults to the offered part number as stated."""
    found: list[Finding] = []
    if shadow is not None:
        found.extend(diff_readings(shadow, primary))
    price = quote.unit_price_each
    if price is not None:
        found.extend(check_line(
            QuoteLineFacts(line_id=quote.id, unit_price=price, currency=quote.currency), cfg))
        key = item_key or quote.offered_mpn
        if history is not None and key and quote.currency:
            found.extend(check_plausibility(
                key, merchant_id, price, "each", quote.currency, quantity, history, cfg))
    return tuple(sorted(found, key=lambda f: (f.field, f.code, f.values)))


def flags_for(findings: Iterable[Finding]) -> tuple[str, ...]:
    """Quote flags for a set of findings: one review flag if any finding needs a review, one
    attention flag if any needs a look. Notes (info) add nothing."""
    severities = {f.severity for f in findings}
    out: list[str] = []
    if Severity.REVIEW in severities:
        out.append(REVIEW_FLAG)
    if Severity.FLAG in severities:
        out.append(ATTENTION_FLAG)
    return tuple(out)


def finding_payload(findings: Iterable[Finding]) -> list[dict[str, str]]:
    """Audit-event form of the findings: code, severity, field and the templated explanation."""
    return [{"code": f.code, "severity": f.severity.value, "field": f.field,
             "text": explain(f)} for f in findings]
