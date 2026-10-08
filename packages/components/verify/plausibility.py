"""Plausibility of a price and quantity against the customer's own history. Flags only: nothing here
approves, picks a reading or changes a value.

`InMemoryPriceHistory` is a `PriceHistory` held in memory. ONE instance holds ONE tenant's history:
the caller builds one per tenant and never shares it (tenant isolation, hard rule 7).

`check_plausibility` compares one checked line with that history. Arithmetic is exact Decimal and
floats are refused. Thresholds come from `VerifyConfig` (the resolved deployment profile); the unit
factors 10, 12, 100 and 1000 are fixed unit arithmetic, not configuration.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from decimal import MAX_EMAX, MIN_EMIN, ROUND_HALF_UP, Context, Decimal, localcontext

from components.verify.config import VerifyConfig
from components.verify.findings import Finding
from components.verify.history import PriceHistory, PriceObservation

UNIT_FACTORS: tuple[Decimal, ...] = (Decimal(10), Decimal(12), Decimal(100), Decimal(1000))
_TWO_DP = Decimal("0.01")
_MAX_PLAIN_EXPONENT = 15  # display only: a ratio of 10**16 or more is shown in scientific notation
# Fixed arithmetic for every check, whatever the caller's decimal context. The exponent range is
# widened: at the default one, multiplying a price near 10**999999 raises Overflow.
_CONTEXT = Context(prec=28, Emax=MAX_EMAX, Emin=MIN_EMIN)


class InMemoryPriceHistory:
    """Price history held in memory, for tests and offline use.

    ONE instance is ONE tenant's history. The caller builds one per tenant and never shares it
    (hard rule 7). Rows carry no tenant field, so this separation is the caller's to keep: the
    store does not check it.

    Rows keep insertion order. `observations` returns the newest first: by `observed_at`, and on a
    tie the later insertion comes first. It filters by item key and, when given, by merchant.
    """

    def __init__(self, observations: Iterable[PriceObservation] = ()) -> None:
        self._rows: list[PriceObservation] = []
        for obs in observations:
            self.add(obs)

    def add(self, obs: PriceObservation) -> None:
        self._rows.append(obs)

    def add_many(self, observations: Iterable[PriceObservation]) -> int:
        batch = list(observations)
        self._rows.extend(batch)
        return len(batch)

    def observations(
        self, item_key: str, merchant_id: str | None = None, limit: int = 20
    ) -> Sequence[PriceObservation]:
        if limit < 1:
            raise ValueError("limit must be >= 1")
        hits = [
            (seq, row)
            for seq, row in enumerate(self._rows)
            if row.item_key == item_key and (merchant_id is None or row.merchant_id == merchant_id)
        ]
        hits.sort(key=lambda hit: (hit[1].observed_at, hit[0]), reverse=True)
        return [row for _, row in hits[:limit]]


def _finite(name: str, value: object) -> Decimal:
    """The value as a finite Decimal. Floats and ints are refused: prices are Decimal."""
    if not isinstance(value, Decimal):
        raise TypeError(f"{name} must be a Decimal, not {type(value).__name__}")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _positive(value: Decimal) -> bool:
    """True for a finite Decimal above zero. History rows that fail this are ignored."""
    return value.is_finite() and value > 0


def _comparable(rows: Iterable[PriceObservation], currency: str) -> list[PriceObservation]:
    """Rows in the checked currency with a positive price. Other currencies and zero prices are
    ignored everywhere: in the minimum count, for last paid, the usual unit and the quantities."""
    return [row for row in rows if row.currency == currency and _positive(row.unit_price)]


def _norm_unit(unit: str) -> str:
    """Units compare case-insensitively and ignoring surrounding spaces."""
    return unit.strip().casefold()


def _usual_unit(rows: Sequence[PriceObservation]) -> str:
    """The most common unit in `rows`; a tie goes to the alphabetically first unit."""
    counts = Counter(_norm_unit(row.unit) for row in rows)
    return min(counts, key=lambda unit: (-counts[unit], unit))


def _near_unit_factor(hi: Decimal, lo: Decimal, tolerance: Decimal) -> bool:
    """True when hi / lo is within `tolerance` (relative to the factor) of a unit factor.

    Exact and division-free: with lo > 0 and hi >= lo, hi / lo must lie in
    [f * (1 - t), f * (1 + t)] for some factor f.
    """
    return any(lo * f * (1 - tolerance) <= hi <= lo * f * (1 + tolerance) for f in UNIT_FACTORS)


def _two_dp(ratio: Decimal) -> str:
    """A ratio (at least 1) to two decimals, half up, as text. Ratios of 10**16 or more are shown in
    scientific notation, so the text stays short whatever the size."""
    if ratio.adjusted() > _MAX_PLAIN_EXPONENT:
        return format(ratio, ".2e")
    return str(ratio.quantize(_TWO_DP, rounding=ROUND_HALF_UP))


def _median(values: Sequence[Decimal]) -> Decimal:
    """Exact median: the middle value, or the mean of the two middle values for an even count."""
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def _last_paid(
    history: PriceHistory,
    item_key: str,
    merchant_id: str,
    currency: str,
    same: Sequence[PriceObservation],
) -> PriceObservation | None:
    """The newest comparable row from this merchant, else the newest comparable row overall.

    The merchant rows come from their own query, so a merchant whose last purchase is older than
    the overall window is still found.
    """
    mine = _comparable(history.observations(item_key, merchant_id=merchant_id), currency)
    if mine:
        return mine[0]
    return same[0] if same else None


def _price_finding(
    price: Decimal, unit: str, last: PriceObservation, usual: str, cfg: VerifyConfig
) -> Finding | None:
    """At most one price finding.

    `price_jump_vs_last_paid` needs the same unit as last paid, a ratio above the threshold and no
    unit-factor match. Otherwise `unit_basis_shift` fires when the ratio is near a unit factor, or
    when the unit is not the usual one and the ratio is above the threshold.
    """
    hi, lo = max(price, last.unit_price), min(price, last.unit_price)
    jump = hi > lo * cfg.price_jump_ratio
    basis = _near_unit_factor(hi, lo, cfg.unit_basis_tolerance)
    if jump and not basis and _norm_unit(unit) == _norm_unit(last.unit):
        return Finding.of(
            "price_jump_vs_last_paid",
            "unit_price",
            price=price,
            last_paid=last.unit_price,
            ratio=_two_dp(hi / lo),
        )
    if basis or (jump and _norm_unit(unit) != _norm_unit(usual)):
        return Finding.of("unit_basis_shift", "unit_price", price=price, usual_unit=usual)
    return None


def _quantity_finding(
    qty: Decimal, same: Sequence[PriceObservation], cfg: VerifyConfig
) -> Finding | None:
    """Flags a quantity far from the median of the comparable rows that carry a positive one."""
    usable = [row.quantity for row in same if row.quantity is not None and _positive(row.quantity)]
    if len(usable) < cfg.min_history_points:
        return None
    usual = _median(usable)
    hi, lo = max(qty, usual), min(qty, usual)
    if hi <= lo * cfg.quantity_ratio:
        return None
    return Finding.of(
        "quantity_unusual", "quantity", quantity=qty, ratio=_two_dp(hi / lo), usual=usual
    )


def check_plausibility(
    item_key: str,
    merchant_id: str,
    unit_price: Decimal,
    unit: str,
    currency: str,
    quantity: Decimal | None,
    history: PriceHistory | None,
    cfg: VerifyConfig,
) -> tuple[Finding, ...]:
    """Flags for one checked line against the customer's own history. Findings only.

    `unit_price` and `quantity` must be finite Decimals: other types raise TypeError and NaN or
    infinity raise ValueError, before anything else is looked at.

    No findings when `history` is None, or when it holds fewer than `cfg.min_history_points` rows
    for the item in this currency with a positive price (the history's window, newest first). Then:
    - last paid is the newest row from `merchant_id`, else the newest row overall. A zero or
      negative checked price is not compared;
    - at most one price finding, see `_price_finding`;
    - `quantity_unusual` when the checked quantity is positive, at least `cfg.min_history_points`
      rows carry a positive quantity, and the larger of quantity / usual and usual / quantity is
      above `cfg.quantity_ratio`. `usual` is the exact median of those quantities.

    Units compare case-insensitively. Ratios in the findings have two decimals, half up, or
    scientific notation from 10**16. Findings are sorted by (field, code).
    """
    with localcontext(_CONTEXT):
        price = _finite("unit_price", unit_price)
        qty = None if quantity is None else _finite("quantity", quantity)
        if history is None:
            return ()
        same = _comparable(history.observations(item_key), currency)
        if len(same) < cfg.min_history_points:
            return ()
        last = _last_paid(history, item_key, merchant_id, currency, same)
        found: list[Finding | None] = []
        if last is not None and price > 0:
            found.append(_price_finding(price, unit, last, _usual_unit(same), cfg))
        if qty is not None and qty > 0:
            found.append(_quantity_finding(qty, same, cfg))
        kept = [finding for finding in found if finding is not None]
        return tuple(sorted(kept, key=lambda f: (f.field, f.code)))
