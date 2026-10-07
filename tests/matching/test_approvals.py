"""Approvals store: tenant-scoped on every method, injected clock, normalised signatures."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from components.core.fakes import FakeClock
from components.matching.approvals import ApprovedMatchStore, InMemoryApprovedMatchStore, signature

from .conftest import parse_line


def test_the_in_memory_store_satisfies_the_protocol() -> None:
    store = InMemoryApprovedMatchStore(FakeClock())
    assert all(hasattr(store, m) for m in ("approve", "lookup", "nearest", "count"))
    typed: ApprovedMatchStore = store
    assert typed.count("t1") == 0


def test_every_method_is_tenant_scoped() -> None:
    store = InMemoryApprovedMatchStore(FakeClock())
    store.approve("t1", "sigA", "12.5mm board", "12.5mm board", ["S1"], "alice")
    assert store.lookup("t1", "sigA") is not None
    assert store.lookup("t2", "sigA") is None
    assert store.nearest("t2", "12.5mm board", 3) == []
    assert store.count("t1") == 1 and store.count("t2") == 0
    store.approve("t2", "sigA", "other", "other", ["S2"], "bob")
    assert store.lookup("t1", "sigA").sku_ids == ("S1",)  # type: ignore[union-attr]
    assert store.lookup("t2", "sigA").sku_ids == ("S2",)  # type: ignore[union-attr]


def test_the_timestamp_comes_from_the_injected_clock() -> None:
    clock = FakeClock(datetime(2026, 10, 6, 12, 0, tzinfo=UTC))
    store = InMemoryApprovedMatchStore(clock)
    first = store.approve("t1", "s", "l", "l", ["S1"], "alice")
    clock.advance(hours=2)
    second = store.approve("t1", "s2", "l", "l", ["S1"], "alice")
    assert first.approved_at == datetime(2026, 10, 6, 12, 0, tzinfo=UTC)
    assert second.approved_at == datetime(2026, 10, 6, 14, 0, tzinfo=UTC)
    assert first.approver == "alice"


@pytest.mark.parametrize(("tenant", "approver", "skus"),
                         [("", "a", ["S"]), ("t", "", ["S"]), ("t", "a", [])])
def test_an_approval_needs_tenant_approver_and_a_sku(tenant: str, approver: str, skus: list[str]) -> None:
    with pytest.raises(ValueError):
        InMemoryApprovedMatchStore(FakeClock()).approve(tenant, "s", "l", "l", skus, approver)


def test_nearest_returns_the_closest_approved_lines_first() -> None:
    store = InMemoryApprovedMatchStore(FakeClock())
    store.approve("t1", "a", "MR board 12.5mm", "12.5mm moisture plasterboard resistant", ["S1"], "x")
    store.approve("t1", "b", "copper elbow", "15mm compression elbow", ["S2"], "x")
    store.approve("t1", "c", "MR board 15mm", "15mm moisture plasterboard resistant", ["S3"], "x")
    got = store.nearest("t1", "12.5mm moisture plasterboard resistant tapered", 2)
    assert [r.signature for r in got][0] == "a" and "b" not in [r.signature for r in got]


def test_signatures_ignore_quantity_wording_and_unit_format(seed_parser) -> None:  # noqa: ANN001
    a = signature(parse_line(seed_parser, "20 sheets 12.5mm tapered p/board 2.4x1.2"))
    b = signature(parse_line(seed_parser, "5 x plasterboard 2400 x 1200mm 12.5 mm tapered"))
    c = signature(parse_line(seed_parser, "20 sheets 15mm tapered p/board 2.4x1.2"))
    assert a is not None and a == b and a != c


def test_an_ambiguous_line_has_no_signature(seed_parser) -> None:  # noqa: ANN001
    assert signature(parse_line(seed_parser, "20 x 12.5mm p/board")) is None
