"""Basket optimisation across merchants with delivery thresholds.

Model: every priced line is bought from exactly one merchant, at that merchant's cheapest eligible
offer for the line (cost c_ij, minor units). A merchant order costs its goods spend plus a delivery
fee that is a step function of that spend (flat fee, free strictly over a threshold, or tiers).
Minimise the sum over merchant orders. The problem is NP-hard (NP-complete even with two shops),
so:

* Lines that share no merchant form independent groups (connected components) solved separately.
* Within a group, lines with a single possible merchant are forced and only add to that merchant's
  base spend. The remaining ("free") lines are solved EXACTLY by a dynamic programme over subsets
  of lines (merchant by merchant, O(m * 3^n)), pruned by a bound from a heuristic incumbent. It is
  used while a group has at most `basket_exact_max_lines` free lines and the work estimate fits
  `basket_work_budget`.
* Otherwise a deterministic greedy start (line-by-line cheapest, best single merchant) with local
  search (move one line, merge one merchant into another) is used, and the result says
  `exact=False` with an optimality-gap note (objective minus the sum of per-line minimum costs).

Production should use a MILP (assignment x_ij, merchant used y_j, threshold met z_j; minimise
sum c_ij x_ij + sum f_j (y_j - z_j)) with this DP as the test oracle (docs/architecture/
pricing-engine.md). Ties prefer fewer merchants, then the lowest merchant ids, so results are a pure
function of the input set. All amounts are integers of the minor unit inside the search.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from .config import PricingConfig
from .decimals import CTX
from .delivery import FeeSchedule, combine
from .models import Visibility
from .reasons import Reason, make_reason
from .results import LineStatus, PricedLine, PricedOffer

_USED = 1024  # key = total * 1024 + merchants used (lexicographic: cost, then fewer merchants)


@dataclass(frozen=True, slots=True)
class BasketChoice:
    line_id: str
    offer: PricedOffer


@dataclass(frozen=True, slots=True)
class MerchantOrder:
    merchant_id: str
    line_ids: tuple[str, ...]
    goods: Decimal
    delivery: Decimal | None  # None when the merchant's terms are not stated or usable
    total: Decimal


@dataclass(frozen=True, slots=True)
class BasketResult:
    choices: tuple[BasketChoice, ...]
    orders: tuple[MerchantOrder, ...]
    unpriced_line_ids: tuple[str, ...]
    goods_total: Decimal
    delivery_total: Decimal
    grand_total: Decimal  # goods + delivery, always
    comparison_total: Decimal  # what the optimiser minimised (goods only if delivery is excluded)
    line_by_line_total: Decimal  # baseline, same units as comparison_total
    single_merchant_total: Decimal | None  # best merchant covering every line, else None
    savings_vs_line_by_line: Decimal
    savings_vs_single_merchant: Decimal | None
    exact: bool
    method: str  # "exact_dp" or "heuristic"
    components: int
    optimality_gap: Decimal  # 0 when exact; else the true optimum is at most this much lower
    delivery_incomplete: bool
    notes: tuple[Reason, ...]


class _Problem:
    """The reduced instance: costs and fees in minor units, merchants and lines indexed."""

    def __init__(self, lines: list[PricedLine], cfg: PricingConfig) -> None:
        self.cfg = cfg
        self.places = cfg.minor_unit_places
        self.lines = lines
        self.merchants = sorted({p.offer.merchant_id for pl in lines for p in pl.ranked})
        self.mi = {m: j for j, m in enumerate(self.merchants)}
        n, m = len(lines), len(self.merchants)
        self.cost: list[list[int | None]] = [[None] * m for _ in range(n)]
        self.pick: list[dict[int, PricedOffer]] = [{} for _ in range(n)]
        for i, pl in enumerate(lines):
            for p in pl.ranked:  # ranked is best first, so the first of a merchant wins ties
                j = self.mi[p.offer.merchant_id]
                c = self.minor(p.goods_cost)
                cur = self.cost[i][j]
                if cur is None or c < cur:
                    self.cost[i][j] = c
                    self.pick[i][j] = p
        self.schedule = [self._merchant_schedule(mid) for mid in self.merchants]

    def minor(self, amount: Decimal) -> int:
        return int(amount.scaleb(self.places, context=CTX))

    def money(self, minor: int) -> Decimal:
        return Decimal(minor).scaleb(-self.places, context=CTX)

    def _merchant_schedule(self, merchant_id: str) -> FeeSchedule | None:
        offers = [p for pl in self.lines for p in pl.ranked
                  if p.offer.merchant_id == merchant_id and p.schedule is not None]
        private = [p for p in offers if p.offer.visibility is Visibility.TENANT_PRIVATE]
        chosen = private or offers
        if not chosen:
            return None
        unique = {p.schedule for p in chosen if p.schedule is not None}
        return combine(sorted(unique, key=lambda s: s.bands))

    def real_fee(self, j: int, spend: int) -> int:
        sched = self.schedule[j]
        return sched.fee_minor(spend) if sched is not None and spend > 0 else 0

    def fee(self, j: int, spend: int) -> int:
        return self.real_fee(j, spend) if self.cfg.include_delivery_in_comparison else 0

    def options(self, i: int) -> list[int]:
        return [j for j, c in enumerate(self.cost[i]) if c is not None]

    def key(self, assign: dict[int, int]) -> int:
        spend: dict[int, int] = {}
        for i, j in assign.items():
            c = self.cost[i][j]
            assert c is not None
            spend[j] = spend.get(j, 0) + c
        total = sum(s + self.fee(j, s) for j, s in spend.items())
        return total * _USED + len(spend)


# ---------------------------------------------------------------- heuristic


def _cheapest(p: _Problem, lines: list[int]) -> dict[int, int]:
    out: dict[int, int] = {}
    for i in lines:
        out[i] = min(p.options(i), key=lambda j: (p.cost[i][j], j))  # type: ignore[type-var,return-value]
    return out


def _single_merchant_seeds(p: _Problem, lines: list[int]) -> list[dict[int, int]]:
    common = set(p.options(lines[0]))
    for i in lines[1:]:
        common &= set(p.options(i))
    return [{i: j for i in lines} for j in sorted(common)]


def _neighbours(p: _Problem, assign: dict[int, int]) -> list[dict[int, int]]:
    out: list[dict[int, int]] = []
    for i in sorted(assign):
        for j in p.options(i):
            if j != assign[i]:
                out.append({**assign, i: j})
    used = sorted(set(assign.values()))
    for a in used:
        for b in used:
            moved = [i for i, j in assign.items() if j == a]
            if a != b and all(p.cost[i][b] is not None for i in moved):
                out.append({i: (b if j == a else j) for i, j in assign.items()})
    return out


def _local_search(p: _Problem, assign: dict[int, int]) -> dict[int, int]:
    best, best_key = assign, p.key(assign)
    while True:
        step: dict[int, int] | None = None
        for cand in _neighbours(p, best):
            k = p.key(cand)
            if k < best_key:
                step, best_key = cand, k
        if step is None:
            return best
        best = step


def _heuristic(p: _Problem, lines: list[int]) -> dict[int, int]:
    seeds = [_cheapest(p, lines), *_single_merchant_seeds(p, lines)]
    results = [_local_search(p, s) for s in seeds]
    return min(results, key=lambda a: (p.key(a), sorted(a.items())))


# ---------------------------------------------------------------- exact DP


def _dp(p: _Problem, lines: list[int], upper: int, budget: int, cap: int) -> dict[int, int] | None:
    opts = {i: p.options(i) for i in lines}
    forced = [i for i in lines if len(opts[i]) == 1]
    free = [i for i in lines if len(opts[i]) > 1]
    n = len(free)
    if n > cap:
        return None
    merchants = sorted({j for i in lines for j in opts[i]})
    avail = {j: [i for i in free if p.cost[i][j] is not None] for j in merchants}
    if sum(3 ** len(avail[j]) * 2 ** (n - len(avail[j])) for j in merchants) > budget:
        return None
    base = {j: 0 for j in merchants}
    for i in forced:
        base[opts[i][0]] += p.cost[i][opts[i][0]]  # type: ignore[operator]
    bit = {i: 1 << k for k, i in enumerate(free)}
    minc = {i: min(p.cost[i][j] for j in opts[i]) for i in free}  # type: ignore[type-var,misc]
    rest = [0] * (1 << n)  # cheapest cost of the free lines NOT in the mask
    for mask in range(1 << n):
        rest[mask] = sum(minc[i] for i in free if not mask & bit[i])  # type: ignore[misc]
    order = [j for j in merchants if avail[j] or base[j] > 0]
    after = [sum(base[j] for j in order[k + 1:]) for k in range(len(order))]
    states: dict[int, int] = {0: 0}
    layers: list[dict[int, tuple[int, int]]] = []
    work = 0
    for k, j in enumerate(order):
        table = _merchant_table(p, j, avail[j], bit, base[j])
        amask = sum(bit[i] for i in avail[j])
        nxt: dict[int, tuple[int, int]] = {}
        for mask in sorted(states, reverse=True):  # carrying over an earlier merchant first
            key, free_bits = states[mask], amask & ~mask
            sub = free_bits
            while True:
                work += 1
                nk, nm = key + table[sub], mask | sub
                if (nk >> 10) + rest[nm] + after[k] <= upper and (
                    nm not in nxt or nk < nxt[nm][0]
                ):
                    nxt[nm] = (nk, mask)
                if sub == 0:
                    break
                sub = (sub - 1) & free_bits
        if work > budget:
            return None
        layers.append(nxt)
        states = {m: v[0] for m, v in nxt.items()}
    full = (1 << n) - 1
    if full not in states:
        return None
    assign = {i: opts[i][0] for i in forced}
    mask = full
    for k in range(len(order) - 1, -1, -1):
        _, prev = layers[k][mask]
        for i in free:
            if (mask ^ prev) & bit[i]:
                assign[i] = order[k]
        mask = prev
    return assign


def _merchant_table(
    p: _Problem, j: int, lines: list[int], bit: dict[int, int], base: int
) -> dict[int, int]:
    """key increment for merchant j taking each subset of `lines` (on top of its forced base)."""
    subs = [(0, 0)]
    for i in lines:
        c = p.cost[i][j]
        assert c is not None
        subs += [(m | bit[i], s + c) for m, s in subs]
    table: dict[int, int] = {}
    for mask, spend in subs:
        total = base + spend
        table[mask] = 0 if total == 0 else (total + p.fee(j, total)) * _USED + 1
    return table


# ---------------------------------------------------------------- components


def _components(p: _Problem) -> list[list[int]]:
    parent = list(range(len(p.merchants)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(len(p.lines)):
        opts = p.options(i)
        for j in opts[1:]:
            parent[find(j)] = find(opts[0])
    groups: dict[int, list[int]] = {}
    for i in range(len(p.lines)):
        groups.setdefault(find(p.options(i)[0]), []).append(i)
    return [groups[r] for r in sorted(groups, key=lambda r: groups[r][0])]


def _solve_component(
    p: _Problem, lines: list[int], cfg: PricingConfig
) -> tuple[dict[int, int], bool, int]:
    """(assignment, exact?, lower bound on the objective) for one group of lines."""
    incumbent = _heuristic(p, lines)
    lower = sum(min(c for c in p.cost[i] if c is not None) for i in lines)
    exact = _dp(p, lines, p.key(incumbent) >> 10, cfg.basket_work_budget,
                cfg.basket_exact_max_lines)
    if exact is not None:
        return exact, True, lower
    return incumbent, False, lower


# ---------------------------------------------------------------- result


def _orders(p: _Problem, assign: dict[int, int]) -> tuple[MerchantOrder, ...]:
    out: list[MerchantOrder] = []
    for j in sorted(set(assign.values())):
        mine = sorted(i for i, m in assign.items() if m == j)
        spend = sum(p.cost[i][j] for i in mine)  # type: ignore[misc]
        sched = p.schedule[j]
        fee = p.real_fee(j, spend) if sched is not None else None
        out.append(MerchantOrder(
            merchant_id=p.merchants[j], line_ids=tuple(p.lines[i].line.line_id for i in mine),
            goods=p.money(spend), delivery=None if fee is None else p.money(fee),
            total=p.money(spend + (fee or 0))))
    return tuple(out)


def _baselines(p: _Problem) -> tuple[int, int | None]:
    every = list(range(len(p.lines)))
    by_line = p.key(_cheapest(p, every)) >> 10
    seeds = _single_merchant_seeds(p, every)
    single = min((p.key(s) >> 10 for s in seeds), default=None)
    return by_line, single


def optimise_basket(lines: Sequence[PricedLine], cfg: PricingConfig) -> BasketResult:
    """Choose one offer per priced line to minimise the comparison total over merchant orders."""
    priced = sorted((pl for pl in lines if pl.status is LineStatus.PRICED and pl.ranked),
                    key=lambda pl: pl.line.line_id)
    unpriced = tuple(sorted(pl.line.line_id for pl in lines if pl not in priced))
    p = _Problem(priced, cfg)
    assign: dict[int, int] = {}
    exact_all, gap, heuristic_lines, comps = True, 0, 0, 0
    if priced:
        for comp in _components(p):
            comps += 1
            part, exact, lower = _solve_component(p, comp, cfg)
            assign.update(part)
            if not exact:
                exact_all = False
                heuristic_lines += len(comp)
                gap += (p.key(part) >> 10) - lower
    orders = _orders(p, assign)
    choices = tuple(BasketChoice(priced[i].line.line_id, p.pick[i][assign[i]])
                    for i in sorted(assign))
    goods = sum((o.goods for o in orders), p.money(0))
    delivery = sum((o.delivery or p.money(0) for o in orders), p.money(0))
    objective = (p.key(assign) >> 10) if assign else 0
    by_line, single = _baselines(p) if priced else (0, None)
    note = (make_reason("basket_exact", components=comps) if exact_all else
            make_reason("basket_heuristic", lines=heuristic_lines,
                        limit=cfg.basket_exact_max_lines, gap=p.money(gap),
                        currency=cfg.base_currency))
    return BasketResult(
        choices=choices, orders=orders, unpriced_line_ids=unpriced, goods_total=goods,
        delivery_total=delivery, grand_total=goods + delivery, comparison_total=p.money(objective),
        line_by_line_total=p.money(by_line),
        single_merchant_total=None if single is None else p.money(single),
        savings_vs_line_by_line=p.money(by_line - objective),
        savings_vs_single_merchant=None if single is None else p.money(single - objective),
        exact=exact_all, method="exact_dp" if exact_all else "heuristic", components=comps,
        optimality_gap=p.money(gap), delivery_incomplete=any(o.delivery is None for o in orders),
        notes=(note,))
