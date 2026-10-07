"""Quote options: several ranked, explained alternatives for the same job.

Inputs are the firm priced lines (the pricing engine's `PricedLine`s: every eligible firm offer per
merchant), the tenant's ordered preferred merchants and an `OptionsConfig`. Output is an
`OptionSet`: complete basket assignments (cheapest, single supplier, fewest deliveries, fastest,
preferred suppliers, balanced), each with totals on the configured VAT basis, savings and extra
cost, deliveries, lead times, flags, templated trade-off sentences and per-line provenance, plus a
Pareto summary. Indicative offers never enter an option (they are listed apart). Nothing is sent
or ordered; options are data for a person (rule 1 [R1]). See docs/architecture/quote-options.md.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from decimal import ROUND_FLOOR, Decimal
from fractions import Fraction
from typing import Any

from components.core.ports import Clock
from components.pricing import PricedLine, PricedOffer, PricingConfig, VatBasis, Visibility
from components.pricing.results import LineStatus
from components.pricing.text import check_id
from components.pricing.vat import split_total

from .models import Bucket, QuoteResult
from .options_config import KINDS, OptionsConfig, OptionsError, check_preferred
from .options_engine import Evaluated, Instance, Pairs, Searcher
from .options_models import (
    LABELS,
    Duplicate,
    ExcludedLine,
    IndicativeInfo,
    NotShown,
    OptimiserInfo,
    OptionDelivery,
    OptionLine,
    OptionSet,
    OptionTotals,
    QuoteOption,
    SingleSupplierInfo,
)
from .options_reasons import OptionReason, reason
from .options_score import balanced_score, display_score, dominators
from .views import offer_provenance

KEEP_ORDER = ("cheapest", "balanced", "fastest", "fewest_deliveries", "preferred",
              "single_supplier")  # which options survive `max_options`, best first
FLAG_MAP = {
    "stale": "stale", "price_outlier_low": "outlier", "price_outlier_high": "outlier",
    "vat_basis_assumed": "vat_unknown", "vat_basis_unknown": "vat_unknown",
    "vat_rate_mismatch": "vat_unknown", "below_moq": "below_moq",
    "lead_time_unknown": "lead_time_unknown", "delivery_unknown": "delivery_unknown",
    "delivery_basis_unknown": "delivery_unknown", "low_stock": "low_stock",
    "stock_unknown": "stock_unknown",
}


def line_flags(p: PricedOffer) -> tuple[str, ...]:
    out = {FLAG_MAP[f] for f in p.flags if f in FLAG_MAP}
    if p.offer.stock_status.value == "made_to_order":
        out.add("made_to_order")
    if p.lead_time_days is None:
        out.add("lead_time_unknown")
    return tuple(sorted(out))


def _prepare(lines: Sequence[PricedLine], tenant_id: str) -> tuple[
        list[PricedLine], list[ExcludedLine], list[IndicativeInfo], set[str]]:
    """Firm lines only; indicative offers dropped (never in an option); tenant check."""
    ids = [pl.line.line_id for pl in lines]
    if len(set(ids)) != len(ids):
        raise OptionsError("line ids must be unique")
    firm: list[PricedLine] = []
    excluded: list[ExcludedLine] = []
    indicative: list[IndicativeInfo] = []
    dropped: set[str] = set()
    for pl in sorted(lines, key=lambda x: x.line.line_id):
        lid = pl.line.line_id
        if pl.indicative is not None:
            r = pl.indicative
            indicative.append(IndicativeInfo(
                lid, pl.line.description, r.low, r.high, r.unit, r.currency, r.basis, r.count,
                r.oldest_observed_at, r.newest_observed_at))
        if pl.status is not LineStatus.PRICED:
            excluded.append(ExcludedLine(lid, pl.status.value))
            continue
        ranked = tuple(p for p in pl.ranked if not p.offer.is_indicative)
        if len(ranked) != len(pl.ranked):
            dropped.add(lid)
        for p in ranked:
            o = p.offer
            if o.visibility is Visibility.TENANT_PRIVATE and o.tenant_id != tenant_id:
                raise OptionsError(f"offer {o.offer_id} is private to another tenant")
        if not ranked:
            excluded.append(ExcludedLine(lid, "indicative_only"))
            continue
        firm.append(pl if len(ranked) == len(pl.ranked) else
                    replace(pl, ranked=ranked, best=ranked[0], runner_ups=ranked[1:]))
    return firm, excluded, indicative, dropped


def _totals(ev: Evaluated, pcfg: PricingConfig) -> OptionTotals:
    split = split_total(ev.total, VatBasis(pcfg.compare_basis), pcfg.vat_rate,
                        pcfg.minor_unit_places)
    return OptionTotals(
        currency=pcfg.base_currency, basis=pcfg.compare_basis, goods=ev.goods,
        delivery=ev.delivery, subtotal=ev.total, tax_rate=pcfg.vat_rate, tax=split.vat,
        total_ex_tax=split.net, total_inc_tax=split.gross,
        delivery_incomplete=ev.delivery_incomplete)


def _lines(ev: Evaluated, inst: Instance) -> tuple[OptionLine, ...]:
    desc = {pl.line.line_id: pl.line.description for pl in inst.lines}
    out = []
    for lid, oid in ev.pairs:
        p = inst.by_key[(lid, oid)]
        o = p.offer
        out.append(OptionLine(
            line_id=lid, description=desc[lid], sku_id=o.sku_id, offer_id=o.offer_id,
            merchant_id=o.merchant_id, packs=p.packs, unit_price=p.unit_price, goods=p.goods_cost,
            lead_time_days=p.lead_time_days, stock_status=o.stock_status.value,
            flags=line_flags(p), match_tier=p.sku.tier.value,
            match_basis=p.sku.basis.value if p.sku.basis is not None else None,
            provenance=offer_provenance(p)))
    return tuple(out)


def _group(produced: dict[str, Evaluated], kinds: tuple[str, ...]
           ) -> list[tuple[Evaluated, tuple[str, ...]]]:
    """Identical assignments are one option; the first kind (fixed order) names it."""
    groups: list[tuple[Evaluated, list[str]]] = []
    for kind in kinds:
        ev = produced.get(kind)
        if ev is None:
            continue
        for g_ev, g_kinds in groups:
            if g_ev.pairs == ev.pairs:
                g_kinds.append(kind)
                break
        else:
            groups.append((ev, [kind]))
    return [(ev, tuple(k)) for ev, k in groups]


def _truncate(groups: list[tuple[Evaluated, tuple[str, ...]]], limit: int
              ) -> tuple[list[tuple[Evaluated, tuple[str, ...]]], list[NotShown]]:
    if len(groups) <= limit:
        return groups, []
    prio = {id(g): min(KEEP_ORDER.index(k) for k in g[1]) for g in groups}
    keep = sorted(groups, key=lambda g: prio[id(g)])[:limit]
    kept = [g for g in groups if g in keep]
    lost = [NotShown(k, reason("max_options", limit=limit))
            for g in groups if g not in keep for k in g[1]]
    return kept, lost


def _limit(ref: Decimal, pct: Decimal) -> Decimal:
    return (ref * (100 + pct) / 100).quantize(Decimal("0.01"), rounding=ROUND_FLOOR)


def _reasons(kinds: tuple[str, ...], ev: Evaluated, ref: Evaluated, *, pcfg: PricingConfig,
             cfg: OptionsConfig, lines: int, preferred: bool, dearest_shown: Decimal, single: SingleSupplierInfo | None, score: Decimal,
             indicative: int, exact: bool, incomplete: bool) -> tuple[OptionReason, ...]:
    cur, basis = pcfg.base_currency, pcfg.compare_basis
    out: list[OptionReason] = []
    if ev.pairs == ref.pairs:
        out.append(reason("total_is_lowest", total=ev.total, currency=cur, basis=basis))
    else:
        out.append(reason("extra_vs_lowest", extra=ev.total - ref.total, currency=cur,
                          basis=basis))
        pcts = {"fewest_deliveries": cfg.tolerance_pct, "preferred": cfg.tolerance_pct,
                "fastest": cfg.fast_tolerance}
        pct = next((pcts[k] for k in kinds if k in pcts), None)
        if pct is not None:
            out.append(reason("total_within_tolerance", pct=pct, limit=_limit(ref.total, pct),
                              currency=cur, basis=basis))
    d, d0 = ev.merchants, ref.merchants
    if d < d0:
        out.append(reason("deliveries_fewer", count=d0 - d, deliveries=d, other=d0))
    elif d > d0:
        out.append(reason("deliveries_more", count=d - d0, deliveries=d, other=d0))
    else:
        out.append(reason("deliveries_same", deliveries=d))
    out.extend(_lead_reasons(ev, ref))
    fees = sum(1 for o in ev.orders if o.fee is None)
    if fees:
        out.append(reason("delivery_terms_unknown", count=fees))
    if preferred:
        n = len(ev.preferred_lines)
        out.append(reason("preferred_coverage", covered=n, lines=lines) if n
                   else reason("preferred_none"))
    if single is not None:
        out.extend(_single_reasons(single, lines, cur, basis))
    if "balanced" in kinds:
        out.append(reason("balanced_score", score=score))
    if dearest_shown > ev.total:
        out.append(reason("saves_vs_dearest", amount=dearest_shown - ev.total, currency=cur,
                          basis=basis))
    if indicative:
        out.append(reason("indicative_excluded", count=indicative))
    if not exact:
        out.append(reason("not_proven_optimal"))
    if incomplete:
        out.append(reason("search_incomplete"))
    return tuple(out)


def _lead_reasons(ev: Evaluated, ref: Evaluated) -> list[OptionReason]:
    if ev.lead[0]:
        return [reason("lead_unknown", count=len(ev.unknown_lead_lines))]
    days = ev.lead[1]
    if ref.lead[0]:
        return [reason("lead_known", days=days)]
    diff = ref.lead[1] - days
    if diff > 0:
        return [reason("lead_earlier", days=days, diff=diff)]
    if diff < 0:
        return [reason("lead_later", days=days, diff=-diff)]
    return [reason("lead_same", days=days)]


def _single_reasons(s: SingleSupplierInfo, lines: int, cur: str, basis: str
                    ) -> list[OptionReason]:
    if not s.outside_line_ids:
        return [reason("single_supplier_all", merchant_id=s.merchant_id)]
    return [reason("single_supplier_covers", merchant_id=s.merchant_id,
                   covered=len(s.supplied_line_ids), lines=lines),
            reason("single_supplier_outside", outside=len(s.outside_line_ids),
                   remainder=s.remainder_total, currency=cur, basis=basis)]


def build_options(
    lines: Sequence[PricedLine], pcfg: PricingConfig, tenant_id: str, clock: Clock, *,
    preferred: Sequence[str] = (), config: OptionsConfig | None = None,
    excluded: Sequence[ExcludedLine] = (),
) -> OptionSet:
    """Build the option set for `tenant_id` from priced lines (one clock reading)."""
    cfg = config or OptionsConfig()
    check_id(tenant_id, "tenant_id")
    pref = check_preferred(list(preferred))
    now = clock.now()
    firm, drop_lines, indicative, dropped = _prepare(lines, tenant_id)
    ind_count = len(dropped | {i.line_id for i in indicative})
    excl = tuple(sorted({*excluded, *drop_lines}, key=lambda e: (e.line_id, e.bucket)))
    base = dict(tenant_id=tenant_id, generated_at=now, currency=pcfg.base_currency,
                basis=pcfg.compare_basis, tax_rate=pcfg.vat_rate, config=cfg, preferred=pref,
                excluded_lines=excl, indicative=tuple(indicative))
    if not firm:
        return OptionSet(
            **base, firm_line_ids=(), options=(), duplicates=(), not_shown=(), pareto_front=(),
            optimiser=OptimiserInfo("none", True, Decimal(0), 0, False),
            notes=(reason("no_firm_lines"),))  # type: ignore[arg-type]
    inst = Instance(firm, pref)
    s = Searcher(inst, pcfg, cfg)
    ref = s.cheapest()
    assert s.basket is not None
    produced: dict[str, Evaluated] = {"cheapest": ref}
    not_shown: list[NotShown] = []
    s_info: dict[Pairs, SingleSupplierInfo] = {}
    produced["fewest_deliveries"] = s.fewest_deliveries(ref)
    produced["fastest"] = s.fastest(ref)
    if pref:
        produced["preferred"] = s.preferred(ref)
    elif "preferred" in cfg.kinds:
        not_shown.append(NotShown("preferred", reason("no_preferred_list")))
    single = s.single_supplier()
    if single is not None:
        ev, merchant, covered = single
        produced["single_supplier"] = ev
        mine = next((o for o in ev.orders if o.merchant_id == merchant), None)
        mine_total = (mine.spend + (mine.fee or Decimal(0))) if mine else Decimal(0)
        s_info[ev.pairs] = SingleSupplierInfo(
            merchant, tuple(sorted(covered)),
            tuple(sorted(set(inst.line_merchants) - set(covered))), mine_total,
            ev.total - mine_total)
    anchor = ref.total
    produced["balanced"] = min(
        s.pool.values(),
        key=lambda e: (_raw_score(e, anchor, inst, pref, cfg), e.total, e.merchants, e.pairs))
    groups, lost = _truncate(_group(produced, cfg.kinds), cfg.max_options)
    not_shown.extend(lost)
    return _assemble(base, groups, not_shown, ref, inst, s, pcfg, cfg, s_info, ind_count)


def _raw_score(ev: Evaluated, anchor: Decimal, inst: Instance, pref: tuple[str, ...],
               cfg: OptionsConfig) -> Fraction:
    return balanced_score(
        total=ev.total, anchor=anchor, lead=ev.lead, deliveries=ev.merchants,
        preferred_lines=len(ev.preferred_lines), lines=len(inst.lines), has_preferred=bool(pref),
        cfg=cfg)


def _assemble(base: dict[str, Any], groups: list[tuple[Evaluated, tuple[str, ...]]],
              not_shown: list[NotShown], ref: Evaluated, inst: Instance, s: Searcher,
              pcfg: PricingConfig, cfg: OptionsConfig, s_info: dict[Pairs, SingleSupplierInfo],
              indicative_count: int) -> OptionSet:
    anchor = ref.total

    def score_of(ev: Evaluated) -> Decimal:
        return display_score(_raw_score(ev, anchor, inst, base["preferred"], cfg))

    ids = {id(g): g[1][0] for g in groups}
    totals = [g[0].total for g in groups]
    dearest = max(totals)
    dom = dominators([(ids[id(g)], g[0].total, g[0].lead, g[0].merchants) for g in groups])
    order = sorted(groups, key=lambda g: (score_of(g[0]), g[0].total, g[0].merchants,
                                          ids[id(g)]))
    score_rank = {ids[id(g)]: i + 1 for i, g in enumerate(order)}
    basket = s.basket
    assert basket is not None
    options: list[QuoteOption] = []
    dups: list[Duplicate] = []
    for g in groups:
        ev, kinds = g
        oid = ids[id(g)]
        info = s_info.get(ev.pairs) if "single_supplier" in kinds else None
        score = score_of(ev)
        lines = _lines(ev, inst)
        flags = {f for ln in lines for f in ln.flags}
        if indicative_count:
            flags.add("indicative_excluded")
        if ev.delivery_incomplete:
            flags.add("delivery_incomplete")
        if not basket.exact:
            flags.add("not_proven_optimal")
        if s.incomplete:
            flags.add("search_incomplete")
        covered = {ln.line_id for ln in lines}
        uncovered = tuple(sorted(set(inst.line_merchants) - covered))
        if uncovered:
            flags.add("partial_cover")
        reasons = _reasons(
            kinds, ev, ref, pcfg=pcfg, cfg=cfg, lines=len(inst.lines), preferred=bool(base["preferred"]),
            dearest_shown=dearest, single=info, score=score,
            indicative=indicative_count, exact=basket.exact, incomplete=s.incomplete)
        if uncovered:
            reasons += (reason("uncovered_lines", count=len(uncovered)),)
        options.append(QuoteOption(
            option_id=oid, kinds=kinds, label=LABELS[kinds[0]], lines=lines,
            deliveries=tuple(OptionDelivery(o.merchant_id, o.line_ids, o.spend, o.fee)
                             for o in ev.orders),
            totals=_totals(ev, pcfg), extra_vs_cheapest=ev.total - ref.total,
            savings_vs_most_expensive=dearest - ev.total, merchant_count=ev.merchants,
            delivery_count=ev.merchants, latest_lead_time_days=(
                None if not any(ln.lead_time_days is not None for ln in lines)
                else max(ln.lead_time_days for ln in lines if ln.lead_time_days is not None)),
            lead_time_complete=not ev.lead[0],
            lead_times=tuple((ln.line_id, ln.lead_time_days) for ln in lines),
            lead_time_unknown_line_ids=ev.unknown_lead_lines, uncovered_line_ids=uncovered,
            preferred_line_ids=ev.preferred_lines, balanced_score=score,
            score_rank=score_rank[oid], dominated=bool(dom[oid]), dominated_by=dom[oid],
            flags=tuple(sorted(flags)), reasons=reasons, single_supplier=info))
        for extra in kinds[1:]:
            dups.append(Duplicate(extra, oid, reason("same_as", option=oid)))
    front = tuple(o.option_id for o in options if not o.dominated)
    return OptionSet(
        **base, firm_line_ids=tuple(sorted(inst.line_merchants)), options=tuple(options),
        duplicates=tuple(dups), not_shown=tuple(not_shown), pareto_front=front,
        optimiser=OptimiserInfo(basket.method, basket.exact, ref.total, s.calls, s.incomplete),
        notes=())


def quote_options(
    result: QuoteResult, pcfg: PricingConfig, clock: Clock, *,
    preferred: Sequence[str] = (), config: OptionsConfig | None = None,
) -> OptionSet:
    """Options for a built quote: its firm lines are the options' lines, and every other line
    (review, unmatched, indicative only, no offer, skipped) is listed as excluded, never dropped."""
    priced = [r.priced for r in result.results if r.priced is not None]
    excluded = [ExcludedLine(r.line_id, r.bucket.value) for r in result.results
                if r.priced is None and r.bucket is not Bucket.PRICED]
    excluded += [ExcludedLine(sk.kit_line_id, Bucket.SKIPPED.value) for sk in result.skipped]
    return build_options(priced, pcfg, result.tenant_id, clock, preferred=preferred,
                         config=config, excluded=excluded)


__all__ = ["KINDS", "build_options", "quote_options"]
