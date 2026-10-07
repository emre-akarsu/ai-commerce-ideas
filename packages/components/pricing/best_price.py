"""Best price for one resolved line (spec stage 2).

For every offer of an SKU in the line's approved match group: normalise to the line unit and the
comparison basis, apply the freshness, stock, VAT-basis, currency and sanity gates, compute whole
packs (minimum order and multiples), goods, delivery and landed cost, then rank the eligible offers.

Ranking key, fixed and documented: (1) the cost the deployment compares on (landed, or goods when
`include_delivery_in_comparison` is false), (2) shorter lead time (unknown last), (3) higher
confidence, (4) more recent observation, (5) offer id. When the winner and the runner-up tie on
cost, the first key on which they differ is reported (`tie_break`). The result never depends on
the order the offers are supplied in.

Search snapshots are indicative only: ignored entirely unless the configuration enables them, and
then shown as a range, never selectable. Only SKUs in the approved match group are ever priced
(CLAUDE.md rule 2); the engine never widens the group.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from fractions import Fraction

from components.core.ports import Clock

from .assess import Assessed, assess_offer, ordered
from .config import PricingConfig
from .decimals import frac_to_decimal, fraction_to_exact_decimal, median, quantize_places
from .explain import Ctx, SanityNote, explain, surplus_reason
from .lines import ResolvedLine
from .models import Offer
from .reasons import Reason, make_reason
from .repository import OfferFilter, OfferRepository
from .results import ExcludedOffer, IndicativeRange, LineStatus, PricedLine, PricedOffer
from .sanity import find_outliers, index_band_flag

_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
_NO_LEAD_TIME = 10**9
_TIE_CRITERIA = ("lead_time", "confidence", "freshness", "offer_id")
_INDICATIVE = frozenset({"indicative_only"})


@dataclass(frozen=True)
class _Final:
    """An assessed offer after the relative sanity checks."""

    a: Assessed
    flags: frozenset[str]
    codes: frozenset[str]
    note: SanityNote | None


def _micros(moment: datetime) -> int:
    return (moment - _EPOCH) // timedelta(microseconds=1)


def rank_key(p: PricedOffer) -> tuple[Decimal, int, Decimal, int, str]:
    lead = p.lead_time_days if p.lead_time_days is not None else _NO_LEAD_TIME
    return (p.rank_cost, lead, -p.offer.confidence, -_micros(p.offer.observed_at),
            p.offer.offer_id)


# ---------------------------------------------------------------- sanity


def _exact(a: Assessed) -> Decimal:
    assert a.numbers is not None
    return fraction_to_exact_decimal(a.numbers.unit_price)


def _display(a: Assessed) -> Decimal:
    assert a.numbers is not None
    return frac_to_decimal(a.numbers.unit_price, 4)


def _usable_snapshot(a: Assessed) -> bool:
    return a.indicative and a.numbers is not None and a.codes == _INDICATIVE


def _outliers(
    group: dict[str, Decimal], cfg: PricingConfig
) -> tuple[dict[str, str], Decimal | None]:
    found = find_outliers(group, cfg)
    return found, (quantize_places(median(list(group.values())), 4) if found else None)


def _sanity(assessed: list[Assessed], line: ResolvedLine, cfg: PricingConfig) -> list[_Final]:
    firm = {a.offer.offer_id: _exact(a) for a in assessed if a.peer}
    snaps = {a.offer.offer_id: _exact(a) for a in assessed if _usable_snapshot(a)}
    firm_out, firm_median = _outliers(firm, cfg)
    snap_out, snap_median = _outliers(snaps, cfg)
    band = line.index_band
    out: list[_Final] = []
    for a in assessed:
        oid = a.offer.offer_id
        extra: set[str] = set()
        note: SanityNote | None = None
        if oid in firm_out or oid in snap_out:
            extra.add(firm_out.get(oid) or snap_out[oid])
            peers = len(firm) if oid in firm_out else len(snaps)
            note = SanityNote(_display(a), firm_median if oid in firm_out else snap_median, peers)
        if a.numbers is not None and not a.indicative:
            flag = index_band_flag(_exact(a), line.unit, band, cfg)
            if flag and band is not None:
                extra.add(flag)
                note = SanityNote(_display(a), note.median if note else None,
                                  note.peers if note else 0,
                                  quantize_places(band.low, 4), quantize_places(band.high, 4))
        codes = set(a.codes)
        if cfg.outlier_offers == "exclude_from_best":
            codes |= extra
        out.append(_Final(a, a.flags | frozenset(extra), frozenset(codes), note))
    return out


# ---------------------------------------------------------------- building results


def _priced(f: _Final, line: ResolvedLine, cfg: PricingConfig) -> PricedOffer:
    a = f.a
    n = a.numbers
    assert n is not None
    zero = Decimal(0)
    landed = n.goods + (n.delivery if n.delivery is not None else zero)
    purchased = n.packs * n.content
    surplus = purchased - Fraction(line.quantity)
    ctx = Ctx(a, line, cfg, f.note)
    surplus_dec = frac_to_decimal(surplus, 6)
    reasons = explain(f.flags | f.codes, ctx)
    if surplus_dec > 0:
        reasons += (surplus_reason(ctx, surplus_dec),)
    return PricedOffer(
        offer=a.offer, sku=a.sku, packs=n.packs, pack_content=frac_to_decimal(n.content, 6),
        purchased=frac_to_decimal(purchased, 6), surplus=surplus_dec,
        pack_price=frac_to_decimal(n.pack_price, 4), unit_price=frac_to_decimal(n.unit_price, 4),
        goods_cost=n.goods, delivery_cost=n.delivery, landed_total=landed,
        landed_unit_cost=frac_to_decimal(Fraction(landed) / Fraction(line.quantity), 4),
        rank_cost=landed if cfg.include_delivery_in_comparison else n.goods, basis=n.basis,
        schedule=n.schedule, flags=tuple(sorted(f.flags | f.codes)), reasons=reasons)


def _excluded(f: _Final, line: ResolvedLine, cfg: PricingConfig) -> ExcludedOffer:
    a = f.a
    ctx = Ctx(a, line, cfg, f.note)
    return ExcludedOffer(
        offer=a.offer, sku=a.sku, codes=ordered(f.codes),
        flags=tuple(sorted(f.flags | f.codes)), reasons=explain(f.codes, ctx),
        detail=_priced(f, line, cfg) if a.numbers is not None else None)


def _indicative_range(
    usable: list[PricedOffer], line: ResolvedLine, cfg: PricingConfig
) -> IndicativeRange | None:
    if not usable:
        return None
    prices = [p.unit_price for p in usable]
    seen = [p.offer.observed_at for p in usable]
    return IndicativeRange(
        low=min(prices), high=max(prices), unit=line.unit, currency=cfg.base_currency,
        basis=usable[0].basis, count=len(usable), oldest_observed_at=min(seen),
        newest_observed_at=max(seen), offers=tuple(usable))


def _tie_reason(first: PricedOffer, second: PricedOffer) -> Reason | None:
    k1, k2 = rank_key(first), rank_key(second)
    if k1[0] != k2[0]:
        return None
    differs = next(i for i in range(1, 5) if k1[i] != k2[i])
    return make_reason("tie_break", winner_id=first.offer.offer_id,
                       other_id=second.offer.offer_id, criterion=_TIE_CRITERIA[differs - 1])


def _selection_reasons(
    ranked: list[PricedOffer], line: ResolvedLine, cfg: PricingConfig
) -> tuple[Reason, ...]:
    best = ranked[0]
    if len(ranked) == 1:
        return (make_reason("selected_only_eligible", offer_id=best.offer.offer_id),)
    common = {
        "offer_id": best.offer.offer_id, "merchant_id": best.offer.merchant_id,
        "sku_id": best.offer.sku_id, "currency": cfg.base_currency, "quantity": line.quantity,
        "unit": line.unit, "packs": best.packs, "goods": best.goods_cost, "basis": best.basis,
    }
    if cfg.include_delivery_in_comparison:
        delivery = best.delivery_cost if best.delivery_cost is not None else "not_stated"
        head = make_reason("selected_lowest_landed_cost", landed=best.landed_total,
                           delivery=delivery, **common)
    else:
        head = make_reason("selected_lowest_goods_cost", **common)
    tie = _tie_reason(best, ranked[1])
    return (head, tie) if tie else (head,)


def _status_reasons(
    status: LineStatus, line: ResolvedLine, rng: IndicativeRange | None
) -> tuple[Reason, ...]:
    if status is LineStatus.NO_OFFERS:
        return (make_reason("no_offers", line_id=line.line_id),)
    if status is LineStatus.NO_ELIGIBLE_OFFER:
        return (make_reason("no_eligible_offer", line_id=line.line_id),)
    assert rng is not None
    return (make_reason("indicative_only_line", line_id=line.line_id),)


def _range_reason(rng: IndicativeRange) -> Reason:
    return make_reason("indicative_range", low=rng.low, high=rng.high, currency=rng.currency,
                       unit=rng.unit, basis=rng.basis, count=rng.count)


# ---------------------------------------------------------------- public API


def price_line_from_offers(
    line: ResolvedLine, offers: Iterable[Offer], cfg: PricingConfig, now: datetime
) -> PricedLine:
    """Price `line` from `offers` (pure and deterministic). Offers for SKUs outside the line's
    match group are ignored; search snapshots are ignored unless the configuration enables them."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be a timezone-aware datetime")
    group = {s.sku_id: s for s in line.skus}
    pool = sorted(
        (o for o in offers if o.sku_id in group
         and (cfg.allow_search_snapshot_sources or not o.is_indicative)),
        key=lambda o: o.offer_id)
    if len({o.offer_id for o in pool}) != len(pool):
        raise ValueError("duplicate offer ids in the offers to price")
    assessed = [assess_offer(o, group[o.sku_id], line, cfg, now) for o in pool]
    finals = _sanity(assessed, line, cfg)
    ranked = sorted((_priced(f, line, cfg) for f in finals if not f.codes), key=rank_key)
    usable = [_priced(f, line, cfg) for f in finals
              if f.a.indicative and f.a.numbers is not None and f.codes == _INDICATIVE]
    rng = _indicative_range(usable, line, cfg)
    excluded = tuple(
        _excluded(f, line, cfg) for f in finals
        if f.codes and not (f.a.indicative and f.a.numbers is not None and f.codes == _INDICATIVE))
    runner_ups = tuple(ranked[1:1 + cfg.runner_up_count])
    if ranked:
        status = LineStatus.PRICED
    elif rng is not None:
        status = LineStatus.INDICATIVE_ONLY
    else:
        status = LineStatus.NO_ELIGIBLE_OFFER if pool else LineStatus.NO_OFFERS
    reasons: tuple[Reason, ...] = ()
    if ranked:
        reasons += _selection_reasons(ranked, line, cfg)
    if rng is not None:
        reasons += (_range_reason(rng),)
    if status is not LineStatus.PRICED:
        reasons += _status_reasons(status, line, rng)
    flags = ranked[0].flags if ranked else (status.value,)
    return PricedLine(
        line=line, status=status, best=ranked[0] if ranked else None, ranked=tuple(ranked),
        runner_ups=runner_ups, excluded=excluded, indicative=rng, flags=flags, reasons=reasons,
        as_of=now)


def price_line(
    line: ResolvedLine, repo: OfferRepository, cfg: PricingConfig, clock: Clock
) -> PricedLine:
    """Price `line` from the offers `repo` can see (shared plus its own tenant's private ones),
    with the time read once from the injected clock."""
    now = clock.now()
    offers = repo.search(OfferFilter(sku_ids=frozenset(line.sku_ids)))
    return price_line_from_offers(line, offers, cfg, now)
