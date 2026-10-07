"""Search for candidate baskets. The pricing engine's `optimise_basket` does ALL the optimisation.

Option (a) is `optimise_basket` itself. Every other option is the same optimiser run on a
RESTRICTED copy of the lines (only some offers kept): a subset of merchants, offers up to a lead
time, preferred merchants first. The optimiser is exact below its line limit, so each restricted
run is the exact minimum of that restricted problem. Candidates are then re-evaluated here with
the full delivery schedules (`Instance.evaluate`), which reproduces the optimiser's own totals
(checked for option (a): a mismatch raises). Only a greedy coverage step for the preferred option
and the single-supplier cost are computed here; they are cheap evaluations, not optimisation.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable, Hashable, Sequence
from dataclasses import dataclass, replace
from decimal import Decimal

from components.pricing import PricedLine, PricedOffer, PricingConfig, Visibility, optimise_basket
from components.pricing.basket import BasketResult
from components.pricing.delivery import FeeSchedule, combine

from .options_config import OptionsConfig, OptionsError
from .options_score import Lead, lead_of

Pairs = tuple[tuple[str, str], ...]  # (line id, offer id), sorted by line id
Keep = Callable[[str, PricedOffer], bool]


@dataclass(frozen=True)
class Order:
    merchant_id: str
    line_ids: tuple[str, ...]
    spend: Decimal
    fee: Decimal | None


@dataclass(frozen=True)
class Evaluated:
    pairs: Pairs
    orders: tuple[Order, ...]
    goods: Decimal
    delivery: Decimal
    total: Decimal
    delivery_incomplete: bool
    lead: Lead
    unknown_lead_lines: tuple[str, ...]
    preferred_lines: tuple[str, ...]
    preferred_rank_sum: int

    @property
    def merchants(self) -> int:
        return len(self.orders)


class Instance:
    """The firm lines with every eligible offer, plus cheapest-per-merchant and fee schedules."""

    def __init__(self, lines: Sequence[PricedLine], preferred: tuple[str, ...]) -> None:
        self.lines = tuple(sorted(lines, key=lambda pl: pl.line.line_id))
        self.preferred = preferred
        self.rank = {m: i for i, m in enumerate(preferred)}
        self.by_key: dict[tuple[str, str], PricedOffer] = {}
        self.cheapest: dict[tuple[str, str], PricedOffer] = {}
        for pl in self.lines:
            lid = pl.line.line_id
            for p in pl.ranked:  # best first: the first of a merchant wins ties (as the optimiser)
                self.by_key.setdefault((lid, p.offer.offer_id), p)
                cur = self.cheapest.get((lid, p.offer.merchant_id))
                if cur is None or p.goods_cost < cur.goods_cost:
                    self.cheapest[(lid, p.offer.merchant_id)] = p
        self.merchants = sorted({m for _, m in self.cheapest})
        self.schedules = {m: self._schedule(m) for m in self.merchants}
        self.line_merchants = {pl.line.line_id: {p.offer.merchant_id for p in pl.ranked}
                               for pl in self.lines}
        self.present_preferred = tuple(m for m in preferred if m in self.merchants)

    def _schedule(self, merchant: str) -> FeeSchedule | None:
        """The same rule as the optimiser: tenant-private terms first, the larger fee wins."""
        offers = [p for pl in self.lines for p in pl.ranked
                  if p.offer.merchant_id == merchant and p.schedule is not None]
        private = [p for p in offers if p.offer.visibility is Visibility.TENANT_PRIVATE]
        chosen = private or offers
        if not chosen:
            return None
        unique = {p.schedule for p in chosen if p.schedule is not None}
        return combine(sorted(unique, key=lambda s: s.bands))

    def order_fee(self, merchant: str, spend: Decimal) -> Decimal | None:
        sched = self.schedules[merchant]
        if sched is None:
            return None
        return sched.fee(spend) if spend > 0 else Decimal(0)

    def evaluate(self, pairs: Pairs) -> Evaluated:
        by_merchant: dict[str, list[tuple[str, PricedOffer]]] = {}
        for lid, oid in pairs:
            p = self.by_key[(lid, oid)]
            by_merchant.setdefault(p.offer.merchant_id, []).append((lid, p))
        orders: list[Order] = []
        for m in sorted(by_merchant):
            spend = sum((p.goods_cost for _, p in by_merchant[m]), Decimal(0))
            orders.append(Order(m, tuple(lid for lid, _ in by_merchant[m]), spend,
                                self.order_fee(m, spend)))
        goods = sum((o.spend for o in orders), Decimal(0))
        delivery = sum((o.fee or Decimal(0) for o in orders), Decimal(0))
        chosen = {lid: self.by_key[(lid, oid)] for lid, oid in pairs}
        leads = [p.lead_time_days for p in chosen.values()]
        pref = tuple(lid for lid, p in chosen.items() if p.offer.merchant_id in self.rank)
        return Evaluated(
            pairs=pairs, orders=tuple(orders), goods=goods, delivery=delivery,
            total=goods + delivery, delivery_incomplete=any(o.fee is None for o in orders),
            lead=lead_of(leads),
            unknown_lead_lines=tuple(sorted(lid for lid, p in chosen.items()
                                            if p.lead_time_days is None)),
            preferred_lines=tuple(sorted(pref)),
            preferred_rank_sum=sum(self.rank[chosen[lid].offer.merchant_id] for lid in pref))


def pairs_of(choices: Sequence[tuple[str, str]]) -> Pairs:
    return tuple(sorted(choices))


class Searcher:
    """Candidate generation. `pool` collects every distinct basket evaluated (for the balanced
    pick); `calls` counts optimiser runs; each search may use at most `max_solver_calls`."""

    def __init__(self, inst: Instance, pcfg: PricingConfig, cfg: OptionsConfig) -> None:
        self.inst, self.pcfg, self.cfg = inst, pcfg, cfg
        self.cache: dict[Hashable, Evaluated | None] = {}
        self.pool: dict[Pairs, Evaluated] = {}
        self.calls = 0
        self.used = 0
        self.incomplete = False
        self.basket: BasketResult | None = None

    def begin(self) -> None:
        self.used = 0

    def consider(self, ev: Evaluated) -> Evaluated:
        self.pool.setdefault(ev.pairs, ev)
        return ev

    # -------------------------------------------------------------- optimiser runs

    def _run(self, lines: Sequence[PricedLine]) -> tuple[Pairs, BasketResult]:
        basket = optimise_basket(lines, self.pcfg)
        self.calls += 1
        return pairs_of([(c.line_id, c.offer.offer.offer_id) for c in basket.choices]), basket

    def cheapest(self) -> Evaluated:
        """Option (a): the pricing engine's own optimum over every firm offer."""
        if ("all",) in self.cache and self.cache[("all",)] is not None:
            return self.cache[("all",)]  # type: ignore[return-value]
        pairs, basket = self._run(self.inst.lines)
        self.basket = basket
        ev = self.consider(self.inst.evaluate(pairs))
        if ev.goods != basket.goods_total or ev.delivery != basket.delivery_total:
            raise OptionsError("internal: option totals differ from the basket optimiser")
        self.cache[("all",)] = ev
        return ev

    def solve(self, key: Hashable, keep: Keep) -> Evaluated | None:
        """The optimiser's optimum when only offers with keep(line_id, offer) are allowed."""
        if key in self.cache:
            return self.cache[key]
        if self.used >= self.cfg.max_solver_calls:
            self.incomplete = True
            return None
        restricted: list[PricedLine] = []
        for pl in self.inst.lines:
            ranked = tuple(p for p in pl.ranked if keep(pl.line.line_id, p))
            if not ranked:
                self.cache[key] = None
                return None
            restricted.append(replace(pl, ranked=ranked, best=ranked[0], runner_ups=ranked[1:]))
        self.used += 1
        pairs, _ = self._run(restricted)
        ev = self.consider(self.inst.evaluate(pairs))
        self.cache[key] = ev
        return ev

    # -------------------------------------------------------------- the options

    def within(self, ev: Evaluated, ref: Decimal, pct: Decimal) -> bool:
        return ev.total * 100 <= ref * (100 + pct)

    def fewest_deliveries(self, ref: Evaluated) -> Evaluated:
        """Smallest number of merchants whose restricted optimum is within the tolerance."""
        self.begin()
        pct = self.cfg.tolerance_pct
        ms = self.search_merchants()
        for k in range(1, len(ms) + 1):
            found: list[Evaluated] = []
            for subset in itertools.combinations(ms, k):
                if not all(self.inst.line_merchants[lid] & set(subset)
                           for lid in self.inst.line_merchants):
                    continue
                chosen = frozenset(subset)
                ev = self.solve(("S", chosen), lambda _l, p, s=chosen: p.offer.merchant_id in s)
                if ev is not None and self.within(ev, ref.total, pct):
                    found.append(ev)
            if found:
                return min(found, key=lambda e: (e.merchants, e.total, e.pairs))
        return ref

    def search_merchants(self) -> list[str]:
        ms = self.inst.merchants
        if len(ms) <= self.cfg.max_search_merchants:
            return list(ms)
        self.incomplete = True
        count = {m: sum(1 for lid in self.inst.line_merchants if m in self.inst.line_merchants[lid])
                 for m in ms}
        return sorted(sorted(ms, key=lambda m: (-count[m], m))[:self.cfg.max_search_merchants])

    def fastest(self, ref: Evaluated) -> Evaluated:
        """Lowest latest lead time whose restricted optimum is within the tolerance. An offer with
        no stated lead time is allowed only at the last level, so it counts as slower than any."""
        self.begin()
        pct = self.cfg.fast_tolerance
        days = sorted({p.lead_time_days for pl in self.inst.lines for p in pl.ranked
                       if p.lead_time_days is not None})
        for level in (*days, None):
            if level is None:
                return ref
            ev = self.solve(("L", level), lambda _l, p, lv=level: (
                p.lead_time_days is not None and p.lead_time_days <= lv))
            if ev is not None and self.within(ev, ref.total, pct):
                return ev
        return ref

    def preferred(self, ref: Evaluated) -> Evaluated:
        """Most lines from preferred merchants within the tolerance (ties: more-preferred
        merchants, then lower total, then fewer merchants)."""
        self.begin()
        pct = self.cfg.tolerance_pct
        present = self.inst.present_preferred[:self.cfg.max_search_merchants]
        cands = [self.improve(ref, ref.total, pct)]
        for k in range(len(present), 0, -1):
            for subset in itertools.combinations(present, k):
                chosen = frozenset(subset)
                ev = self.solve(("P", chosen), lambda lid, p, s=chosen: (
                    p.offer.merchant_id in s
                    or not (self.inst.line_merchants[lid] & s)))
                if ev is not None and self.within(ev, ref.total, pct):
                    cands.append(self.improve(ev, ref.total, pct))
        return min(cands, key=lambda e: (-len(e.preferred_lines), e.preferred_rank_sum, e.total,
                                         e.merchants, e.pairs))

    def improve(self, ev: Evaluated, ref_total: Decimal, pct: Decimal) -> Evaluated:
        """Greedy: move one line at a time to a preferred merchant (cheapest resulting total that
        stays within the tolerance) until no move is possible. Strictly raises coverage."""
        inst = self.inst
        while True:
            best: tuple[tuple[Decimal, int, str, str], Evaluated] | None = None
            chosen = dict(ev.pairs)
            for lid, oid in ev.pairs:
                if inst.by_key[(lid, oid)].offer.merchant_id in inst.rank:
                    continue
                for m in inst.present_preferred:
                    p = inst.cheapest.get((lid, m))
                    if p is None:
                        continue
                    trial = inst.evaluate(pairs_of({**chosen, lid: p.offer.offer_id}.items()))
                    if trial.total * 100 <= ref_total * (100 + pct):
                        key = (trial.total, inst.rank[m], lid, p.offer.offer_id)
                        if best is None or key < best[0]:
                            best = (key, trial)
            if best is None:
                return ev
            ev = self.consider(best[1])

    def single_supplier(self) -> tuple[Evaluated, str, tuple[str, ...]] | None:
        """The merchant that can supply the most lines (ties: cheaper for those lines, then id);
        lines it cannot supply are bought from the other merchants at their optimum."""
        inst = self.inst
        if not inst.merchants:
            return None
        self.begin()

        def rank(m: str) -> tuple[int, Decimal, str]:
            mine = [inst.cheapest[(lid, m)] for lid in inst.line_merchants
                    if (lid, m) in inst.cheapest]
            spend = sum((p.goods_cost for p in mine), Decimal(0))
            return (-len(mine), spend + (inst.order_fee(m, spend) or Decimal(0)), m)

        merchant = min(inst.merchants, key=rank)
        covered = tuple(lid for lid in inst.line_merchants if (lid, merchant) in inst.cheapest)
        ev = self.solve(("U", merchant), lambda lid, p, m=merchant, c=frozenset(covered): (
            (p.offer.merchant_id == m) if lid in c else (p.offer.merchant_id != m)))
        return None if ev is None else (ev, merchant, covered)
