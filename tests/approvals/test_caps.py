"""R9: per-order and daily-aggregate caps, Decimal only."""

from __future__ import annotations

from decimal import Decimal

import pytest

from components.purchase_orders.approvals.service import (
    CapCurrencyMismatch,
    CapPolicy,
    DailyCapExceeded,
    InvalidAmount,
    PerOrderCapExceeded,
)
from components.core.fakes import FakeClock

D = Decimal


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def caps(clock: FakeClock) -> CapPolicy:
    return CapPolicy(per_order=D("1000"), daily_aggregate=D("2500"), clock=clock)


def test_within_caps_passes_and_boundary_is_inclusive(caps: CapPolicy) -> None:
    caps.check("t1", D("1000"))
    caps.reserve("t1", D("1000"))
    assert caps.spent_today("t1") == D("1000")


def test_per_order_cap(caps: CapPolicy) -> None:
    with pytest.raises(PerOrderCapExceeded):
        caps.check("t1", D("1000.01"))
    with pytest.raises(PerOrderCapExceeded):
        caps.reserve("t1", D("1000.01"))
    assert caps.spent_today("t1") == D("0")  # a refused reservation records nothing


def test_daily_aggregate_blocks_split_pos(caps: CapPolicy) -> None:
    """Three POs that each pass the per-order cap but together exceed the daily cap."""
    caps.reserve("t1", D("900"))
    caps.reserve("t1", D("900"))
    caps.reserve("t1", D("700"))  # 2500 exactly: allowed
    with pytest.raises(DailyCapExceeded):
        caps.reserve("t1", D("0.01"))
    assert caps.spent_today("t1") == D("2500")
    assert caps.remaining_today("t1") == D("0")


def test_check_does_not_record(caps: CapPolicy) -> None:
    for _ in range(10):
        caps.check("t1", D("1000"))
    assert caps.spent_today("t1") == D("0")


def test_daily_cap_resets_on_the_next_utc_day(caps: CapPolicy, clock: FakeClock) -> None:
    caps.reserve("t1", D("1000"))
    caps.reserve("t1", D("1000"))
    caps.reserve("t1", D("500"))
    with pytest.raises(DailyCapExceeded):
        caps.reserve("t1", D("1"))
    clock.advance(days=1)
    caps.reserve("t1", D("1000"))
    assert caps.spent_today("t1") == D("1000")


def test_tenants_have_independent_daily_totals(caps: CapPolicy) -> None:
    caps.reserve("t1", D("1000"))
    caps.reserve("t1", D("1000"))
    caps.reserve("t2", D("1000"))
    assert caps.spent_today("t1") == D("2000")
    assert caps.spent_today("t2") == D("1000")


def test_decimal_precision_is_exact(clock: FakeClock) -> None:
    caps = CapPolicy(D("0.3"), D("0.3"), clock)
    caps.reserve("t", D("0.1"))
    caps.reserve("t", D("0.1"))
    caps.reserve("t", D("0.1"))  # 0.1 * 3 == 0.3 exactly with Decimal (not with float)
    with pytest.raises(DailyCapExceeded):
        caps.reserve("t", D("0.0001"))


@pytest.mark.parametrize("bad", [0.1, 5, "5", None])
def test_floats_and_ints_are_rejected(caps: CapPolicy, bad: object) -> None:
    with pytest.raises(InvalidAmount):
        caps.check("t1", bad)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", [D("-0.01"), D("NaN"), D("Infinity")])
def test_negative_and_non_finite_amounts_rejected(caps: CapPolicy, bad: Decimal) -> None:
    with pytest.raises(InvalidAmount):
        caps.reserve("t1", bad)


def test_currency_must_match(caps: CapPolicy) -> None:
    caps.check("t1", D("10"), currency="USD")
    with pytest.raises(CapCurrencyMismatch):
        caps.check("t1", D("10"), currency="EUR")


def test_invalid_policy_rejected(clock: FakeClock) -> None:
    with pytest.raises(ValueError, match="per_order"):
        CapPolicy(D("0"), D("10"), clock)
    with pytest.raises(ValueError, match="daily"):
        CapPolicy(D("10"), D("5"), clock)  # daily must be >= per-order
    with pytest.raises(InvalidAmount):
        CapPolicy(1000, D("2000"), clock)  # type: ignore[arg-type]


def test_concurrent_reservations_cannot_overshoot(clock: FakeClock) -> None:
    import threading

    caps = CapPolicy(D("100"), D("1000"), clock)
    ok: list[int] = []

    def worker() -> None:
        try:
            caps.reserve("t", D("100"))
            ok.append(1)
        except DailyCapExceeded:
            pass

    threads = [threading.Thread(target=worker) for _ in range(40)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(ok) == 10
    assert caps.spent_today("t") == D("1000")
