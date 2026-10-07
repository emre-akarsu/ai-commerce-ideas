"""Build one tenant's price book: a record per merchant with source, as-of date, validity, VAT
basis, coverage of the quoted lines and next refresh due (strategy phase 1, step 1.2).

Inputs are handed in (no files, no network, no global clock):

* `offers`: anything with `for_tenant(tenant_id)` returning the tenant-bound `OfferRepository`
  (the same object quoting uses). The repository holds shared offers and that tenant's own and
  nothing else, so a tenant's book cannot contain another tenant's private prices.
* `merchants`: the merchants the deployment knows (name and id), so a merchant with no offers
  still appears, as missing.
* `pricing`: `PricingConfig` (max ages per source kind, currency, comparison basis), built by the
  caller from the resolved profile.
* `clock`: injected; one reading is used for the whole book.
* `quote`: optional `QuoteResult` for the same tenant. Coverage and gaps are read from the quote's
  per-line results (which firm offers each line has); nothing is re-priced here.
* `imports`: optional import reports, for the quarantined count.

The data the status rests on ("primary offers") are the firm offers when there are any, else all
visible offers. As-of, validity, VAT basis, attestation, visibility, dominant source kind and next
refresh are computed over them; `source_kinds` and `offers_count` cover every visible offer.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timedelta
from typing import Protocol

from components.core.ports import Clock
from components.pricing import (
    Offer,
    OfferRepository,
    PricingConfig,
    SourceKind,
    VatBasis,
    Visibility,
)
from components.pricing.repository import MAX_LIMIT, OfferFilter
from components.quoting import QuoteResult

from .errors import PriceBookError
from .gaps import compute_gaps
from .ladder import ladder_level
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
    VatSummary,
)
from .status import (
    current_reason,
    expired_reason,
    indicative_reason,
    merchant_status,
    missing_reason,
    offer_state,
    stale_reason,
)


class TenantOffers(Protocol):
    def for_tenant(self, tenant_id: str) -> OfferRepository: ...


class LoadReportLike(Protocol):
    """What `components.quoting.loading.LoadReport` offers; a price file import's outcome."""

    source_id: str
    visibility: str
    tenant_id: str | None
    offers: int
    quarantined: Sequence[object]


def summaries_from_reports(reports: Iterable[LoadReportLike],
                           merchant_by_source: Mapping[str, str]) -> tuple[ImportSummary, ...]:
    """Import summaries from load reports; `merchant_by_source` maps a source id to its merchant
    (the declaration the loader was given, which the caller holds)."""
    out = []
    for r in reports:
        if r.source_id not in merchant_by_source:
            raise PriceBookError(f"no merchant is declared for source {r.source_id}")
        out.append(ImportSummary(merchant_by_source[r.source_id], r.tenant_id, r.visibility,
                                 r.offers, len(r.quarantined)))
    return tuple(out)


def vat_summary(offers: Sequence[Offer]) -> tuple[VatSummary, tuple[tuple[str, int], ...]]:
    counts = Counter(o.price.vat_basis for o in offers)
    pairs = tuple((b.value, counts.get(b, 0)) for b in (VatBasis.EX_TAX, VatBasis.INC_TAX,
                                                         VatBasis.UNKNOWN))
    kinds = [b for b, n in pairs if n]
    if not kinds:
        return VatSummary.UNKNOWN, pairs
    if len(kinds) > 1:
        return VatSummary.MIXED, pairs
    return VatSummary(kinds[0]), pairs


def dominant_kind(offers: Sequence[Offer]) -> SourceKind | None:
    """The source kind with most offers; a tie goes to the alphabetically first kind."""
    counts = Counter(o.source_kind for o in offers)
    if not counts:
        return None
    return sorted(counts, key=lambda k: (-counts[k], k.value))[0]


def _coverage_counts(quote: QuoteResult | None) -> tuple[Mapping[str, int], int]:
    """Lines with a firm offer per merchant, and the number of quoted lines."""
    if quote is None:
        return {}, 0
    firm: Counter[str] = Counter()
    for r in quote.results:
        for merchant in {p.offer.merchant_id for p in r.firm_offers}:
            firm[merchant] += 1
    return firm, len(quote.results)


def _quarantined(imports: Iterable[ImportSummary], tenant_id: str) -> Mapping[str, int]:
    counts: Counter[str] = Counter()
    for s in imports:
        if s.tenant_id is None or s.tenant_id == tenant_id:
            counts[s.merchant_id] += s.quarantined
    return counts


def _visibility(primary: Sequence[Offer]) -> str:
    shared = bool(primary) and all(o.visibility is Visibility.SHARED for o in primary)
    return (Visibility.SHARED if shared else Visibility.TENANT_PRIVATE).value


def _merchant_book(
    info: MerchantInfo, offers: Sequence[Offer], cfg: PricingConfig, now: datetime,
    quarantined: int, coverage: Coverage | None,
) -> MerchantBook:
    firm = [o for o in offers if not o.is_indicative]
    primary = firm or list(offers)
    states = [offer_state(o, cfg, now) for o in firm]
    status = merchant_status(states, bool(offers))
    as_of = max((o.observed_at for o in primary), default=None)
    usable = [o for o, st in zip(firm, states, strict=True) if st is not OfferState.EXPIRED]
    untils = [o.valid_until for o in (usable or primary) if o.valid_until is not None]
    kind = dominant_kind(primary)
    max_age = cfg.max_age_hours(kind) if kind is not None else None
    vat, vat_counts = vat_summary(primary)
    code, text = _reason(status, offers, firm, states, cfg, now)
    return MerchantBook(
        merchant_id=info.merchant_id, name=info.name, status=status, status_reason_code=code,
        status_reason=text, ladder_level=ladder_level(offers),
        source_kinds=tuple(sorted({o.source_kind.value for o in offers})),
        visibility=_visibility(primary),
        attested=bool(primary) and all(o.tenant_attested for o in primary),
        offers_count=len(offers), firm_offers_count=len(firm),
        indicative_offers_count=len(offers) - len(firm), quarantined_count=quarantined,
        as_of=as_of, valid_until_earliest=min(untils, default=None),
        valid_until_latest=max(untils, default=None), vat_basis=vat, vat_counts=vat_counts,
        offers_current=states.count(OfferState.CURRENT),
        offers_stale=states.count(OfferState.STALE),
        offers_expired=states.count(OfferState.EXPIRED),
        dominant_source_kind=kind.value if kind else None, max_age_hours=max_age,
        next_refresh_due=(as_of + timedelta(hours=max_age)
                          if as_of is not None and max_age is not None else None),
        coverage=coverage)


def _reason(status: MerchantStatus, offers: Sequence[Offer], firm: Sequence[Offer],
            states: Sequence[OfferState], cfg: PricingConfig, now: datetime
            ) -> tuple[str, str]:
    if not offers:
        return missing_reason()
    if status is MerchantStatus.INDICATIVE_ONLY:
        return indicative_reason(offers)
    pairs = list(zip(firm, states, strict=True))
    until = max((o.valid_until for o in firm if o.valid_until), default=None)
    if status is MerchantStatus.MISSING:
        return expired_reason(until)
    pool = [o for o, s in pairs if s is (
        OfferState.CURRENT if status is MerchantStatus.CURRENT else OfferState.STALE)]
    newest = max(pool, key=lambda o: o.observed_at)
    kind = newest.source_kind
    limit = cfg.max_age_hours(kind)
    if status is MerchantStatus.STALE:
        return stale_reason(newest.observed_at, limit, now, kind.value)
    stale = sum(1 for _, s in pairs if s is not OfferState.CURRENT)
    return current_reason(newest.observed_at, min(
        (o.valid_until for o in pool if o.valid_until), default=None), limit, now, stale,
        len(firm))


def _freshness(merchants: Sequence[MerchantBook], now: datetime) -> FreshnessSummary:
    counts = Counter(m.status for m in merchants)
    dues = [m.next_refresh_due for m in merchants if m.next_refresh_due is not None]
    as_ofs = [m.as_of for m in merchants if m.as_of is not None]
    return FreshnessSummary(
        current=counts[MerchantStatus.CURRENT], stale=counts[MerchantStatus.STALE],
        missing=counts[MerchantStatus.MISSING],
        indicative_only=counts[MerchantStatus.INDICATIVE_ONLY], merchants_total=len(merchants),
        oldest_as_of=min(as_ofs, default=None), next_refresh_due=min(dues, default=None),
        overdue=sum(1 for d in dues if d <= now))


def build_price_book(
    offers: TenantOffers, tenant_id: str, merchants: Sequence[MerchantInfo],
    pricing: PricingConfig, clock: Clock, *, quote: QuoteResult | None = None,
    imports: Iterable[ImportSummary] = (),
) -> PriceBook:
    """The tenant's price book at the clock's current time (see the module docstring)."""
    now = clock.now()
    if now.tzinfo is None or now.utcoffset() is None:
        raise PriceBookError("the clock must return a timezone-aware time")
    if quote is not None and quote.tenant_id != tenant_id:
        raise PriceBookError("the quote belongs to another tenant")
    repo = offers.for_tenant(tenant_id)
    visible = repo.search(OfferFilter(limit=MAX_LIMIT))
    for o in visible:  # defence in depth: the repository already guarantees this
        if o.visibility is Visibility.TENANT_PRIVATE and o.tenant_id != tenant_id:
            raise PriceBookError("an offer of another tenant reached this book")
    by_merchant: dict[str, list[Offer]] = {}
    for o in visible:
        by_merchant.setdefault(o.merchant_id, []).append(o)
    known = {m.merchant_id: m for m in merchants}
    for mid in by_merchant:
        known.setdefault(mid, MerchantInfo(mid, mid))
    firm_lines, lines_total = _coverage_counts(quote)
    quarantined = _quarantined(imports, tenant_id)
    books = tuple(
        _merchant_book(
            known[mid], by_merchant.get(mid, []), pricing, now, quarantined.get(mid, 0),
            Coverage(firm_lines.get(mid, 0), lines_total) if quote is not None else None)
        for mid in sorted(known))
    gaps: tuple[GapLine, ...] = (
        compute_gaps(quote, known, pricing) if quote is not None else ())
    return PriceBook(
        tenant_id=tenant_id, as_of=now, currency=pricing.base_currency,
        comparison_basis=pricing.compare_basis, merchants=books, gaps=gaps,
        freshness=_freshness(books, now),
        contains_synthetic_data=any(o.provenance.synthetic for o in visible),
        lines_total=lines_total if quote is not None else None)
