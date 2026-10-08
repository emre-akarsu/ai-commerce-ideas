"""Price history repository on real Postgres (migration 0007).

``PgPriceHistory`` keeps each tenant's observations apart, returns them newest first within the
documented limit, refuses a bad batch before any write, and writes a batch all or nothing. Nothing
here updates or deletes a point: a later load only adds to the history (spec F28 clause 5). Runs
through the fixtures in ``conftest.py``; skips with a reason when Postgres is unreachable.
"""

from __future__ import annotations

import inspect
import uuid
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest
from sqlalchemy import Engine, event, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from aidb.price_history import PgPriceHistory, TenantPriceHistory
from aidb.session import PrivilegedRoleError, make_engine
from components.verify.history import PriceHistory, PriceObservation

ITEM = "ITEM-1"
JAN_1 = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
BAD_TENANT_IDS = ["", "   ", None, 7, "t\x00x"]
RAW_INSERT = text(
    "INSERT INTO price_observations (tenant_id, id, item_key, merchant_id, unit_price, unit, "
    "currency, quantity, observed_at, source) VALUES (:t, :id, :item_key, 'M-1', :price, 'each', "
    "'EUR', NULL, :observed_at, 'po_import')"
)
ADMIN_INSERT = text(
    "INSERT INTO price_observations (tenant_id, id, item_key, merchant_id, unit_price, unit, "
    "currency, quantity, observed_at, source, recorded_at) VALUES (:t, :id, :item_key, 'M-1', "
    ":price, 'each', 'EUR', NULL, :observed_at, 'po_import', :recorded_at)"
)


def _obs(day: int = 1, **over: Any) -> PriceObservation:
    fields: dict[str, Any] = {
        "item_key": ITEM,
        "merchant_id": "M-1",
        "unit_price": Decimal("10.00"),
        "unit": "each",
        "currency": "EUR",
        "quantity": None,
        "observed_at": JAN_1 + timedelta(days=day - 1),
        "source": "po_import",
    }
    return PriceObservation(**{**fields, **over})


def _history(engine: Engine, tenant: str) -> TenantPriceHistory:
    return PgPriceHistory(engine).for_tenant(tenant)


# ---------------------------------------------------------------- construction and reads


@pytest.mark.parametrize("bad", BAD_TENANT_IDS)
def test_for_tenant_refuses_a_bad_tenant_id(app_engine, bad) -> None:
    with pytest.raises(ValueError):
        PgPriceHistory(app_engine).for_tenant(bad)


def test_every_field_round_trips_and_decimals_stay_exact(app_engine, tenants) -> None:
    a, _ = tenants
    zone = timezone(timedelta(hours=2))
    row = _obs(
        1,
        unit_price=Decimal("12.345678"),
        quantity=Decimal("3"),
        observed_at=datetime(2026, 1, 2, 8, 0, tzinfo=zone),
        source="accepted_quote",
    )
    assert _history(app_engine, a).add_many([row]) == 1
    (got,) = _history(app_engine, a).observations(ITEM)
    assert got == row
    assert got.unit_price == Decimal("12.345678")
    assert isinstance(got.unit_price, Decimal) and isinstance(got.quantity, Decimal)


@pytest.mark.parametrize(
    ("price", "quantity"),
    [
        pytest.param(Decimal("0"), None, id="zero-price-no-quantity"),
        pytest.param(
            Decimal("99999999999999.999999"), Decimal("0.000001"), id="largest-and-smallest"
        ),
        pytest.param(Decimal("1.2000000"), Decimal("1E+2"), id="trailing-zeros-are-exact"),
    ],
)
def test_values_that_numeric_20_6_keeps_exactly_are_accepted(
    app_engine, tenants, price, quantity
) -> None:
    a, _ = tenants
    row = _obs(1, unit_price=price, quantity=quantity)
    assert _history(app_engine, a).add_many([row]) == 1
    (got,) = _history(app_engine, a).observations(ITEM)
    assert got == row


def test_observations_come_back_newest_first(app_engine, tenants) -> None:
    a, _ = tenants
    repo = _history(app_engine, a)
    repo.add_many([_obs(d, unit_price=Decimal(d)) for d in (2, 5, 1, 4)])
    assert [o.unit_price for o in repo.observations(ITEM)] == [
        Decimal(5),
        Decimal(4),
        Decimal(2),
        Decimal(1),
    ]


def test_ties_on_observed_at_break_by_recorded_at_then_id(admin_engine, app_engine, tenants) -> None:
    a, _ = tenants
    t0 = datetime(2026, 2, 1, tzinfo=UTC)
    rows = [  # (id, unit price, observed_at, recorded_at); the database fills recorded_at normally
        ("aa", "1", JAN_1, t0 + timedelta(seconds=1)),
        ("ab", "2", JAN_1, t0 + timedelta(seconds=2)),
        ("zz", "3", JAN_1, t0 + timedelta(seconds=2)),
        ("late", "4", JAN_1 + timedelta(days=1), t0),
    ]
    with admin_engine.begin() as c:
        for row_id, price, observed, recorded in rows:
            c.execute(
                ADMIN_INSERT,
                {
                    "t": a,
                    "id": row_id,
                    "item_key": ITEM,
                    "price": Decimal(price),
                    "observed_at": observed,
                    "recorded_at": recorded,
                },
            )
    got = _history(app_engine, a).observations(ITEM)
    assert [o.unit_price for o in got] == [Decimal(4), Decimal(3), Decimal(2), Decimal(1)]


def test_default_limit_is_twenty_and_the_cap_is_200(app_engine, tenants) -> None:
    a, _ = tenants
    repo = _history(app_engine, a)
    repo.add_many([_obs(d) for d in range(1, 26)])
    assert len(repo.observations(ITEM)) == 20
    assert len(repo.observations(ITEM, limit=200)) == 25
    assert len(repo.observations(ITEM, limit=1)) == 1


@pytest.mark.parametrize("limit", [0, -1, 201, True])
def test_limit_outside_1_to_200_is_refused(app_engine, tenants, limit) -> None:
    a, _ = tenants
    with pytest.raises(ValueError):
        _history(app_engine, a).observations(ITEM, limit=limit)


def test_the_limit_error_does_not_echo_the_value(app_engine, tenants) -> None:
    a, _ = tenants
    with pytest.raises(ValueError) as err:
        _history(app_engine, a).observations(ITEM, limit=4321)
    assert "4321" not in str(err.value)


def test_item_and_merchant_filters(app_engine, tenants) -> None:
    a, _ = tenants
    repo = _history(app_engine, a)
    repo.add_many(
        [_obs(1, merchant_id="M-1"), _obs(2, merchant_id="M-2"), _obs(3, item_key="ITEM-2")]
    )
    assert [o.merchant_id for o in repo.observations(ITEM, merchant_id="M-2")] == ["M-2"]
    assert [o.merchant_id for o in repo.observations(ITEM)] == ["M-2", "M-1"]
    assert [o.item_key for o in repo.observations("ITEM-2")] == ["ITEM-2"]
    assert repo.observations("NO-SUCH-ITEM") == []


def test_the_tenant_history_matches_the_price_history_protocol(app_engine, tenants) -> None:
    proto = inspect.signature(PriceHistory.observations)
    impl = inspect.signature(TenantPriceHistory.observations)
    assert list(impl.parameters) == list(proto.parameters)
    assert {k: p.default for k, p in impl.parameters.items()} == {
        k: p.default for k, p in proto.parameters.items()
    }
    a, _ = tenants
    history: PriceHistory = _history(app_engine, a)
    assert history.observations(ITEM) == []


# ---------------------------------------------------------------- writes


def test_add_many_counts_rows_and_accepts_any_iterable(app_engine, tenants) -> None:
    a, _ = tenants
    repo = _history(app_engine, a)
    assert repo.add_many(_obs(d) for d in (1, 2)) == 2
    assert repo.add_many([]) == 0
    assert len(repo.observations(ITEM)) == 2


def test_a_later_load_adds_to_the_history_and_replaces_nothing(app_engine, tenants) -> None:
    a, _ = tenants
    repo = _history(app_engine, a)
    repo.add_many([_obs(1, unit_price=Decimal("10.00"))])
    repo.add_many([_obs(1, unit_price=Decimal("11.00"))])  # same item, merchant and day
    got = sorted(o.unit_price for o in repo.observations(ITEM))
    assert got == [Decimal("10.00"), Decimal("11.00")]


def test_ids_are_uuid4_hex(admin_engine, app_engine, tenants) -> None:
    a, _ = tenants
    _history(app_engine, a).add_many([_obs(1), _obs(2)])
    with admin_engine.connect() as c:
        ids = (
            c.execute(text("SELECT id FROM price_observations WHERE tenant_id = :t"), {"t": a})
            .scalars()
            .all()
        )
    assert len(ids) == 2
    for value in ids:
        parsed = uuid.UUID(hex=value)
        assert parsed.version == 4 and parsed.hex == value


# A value that Python must refuse, paired with text that must never appear in the error message.
BAD_OBSERVATIONS = [
    pytest.param({"unit_price": 10.5}, "10.5", id="price-float"),
    pytest.param({"unit_price": 7}, "7", id="price-int"),
    pytest.param({"unit_price": Decimal("-0.01")}, "-0.01", id="price-negative"),
    pytest.param({"unit_price": Decimal("NaN")}, "NaN", id="price-nan"),
    pytest.param({"unit_price": Decimal("Infinity")}, "Infinity", id="price-infinite"),
    pytest.param({"unit_price": Decimal("1.2345675")}, "1.2345675", id="price-7-decimals"),
    pytest.param({"unit_price": Decimal("100000000000000")}, "100000000000000", id="price-big"),
    pytest.param({"quantity": 2.5}, "2.5", id="quantity-float"),
    pytest.param({"quantity": Decimal("0")}, "0", id="quantity-zero"),
    pytest.param({"quantity": Decimal("-4")}, "-4", id="quantity-negative"),
    pytest.param({"quantity": Decimal("NaN")}, "NaN", id="quantity-nan"),
    pytest.param({"currency": "eur"}, "eur", id="currency-lower"),
    pytest.param({"currency": "EURO"}, "EURO", id="currency-four"),
    pytest.param({"currency": None}, "None", id="currency-none"),
    pytest.param({"observed_at": datetime(2026, 1, 1)}, "2026", id="observed-naive"),
    pytest.param({"observed_at": date(2026, 1, 1)}, "2026-01-01", id="observed-date"),
    pytest.param({"source": "manual"}, "manual", id="source-unknown"),
    pytest.param({"source": "PO_IMPORT"}, "PO_IMPORT", id="source-case"),
]


@pytest.mark.parametrize(("over", "sentinel"), BAD_OBSERVATIONS)
def test_a_batch_with_one_bad_observation_writes_nothing(
    app_engine, tenants, over, sentinel
) -> None:
    a, _ = tenants
    repo = _history(app_engine, a)
    with pytest.raises(ValueError) as err:
        repo.add_many([_obs(1), _obs(2, **over)])
    assert sentinel not in str(err.value)
    assert repo.observations(ITEM) == []


def test_a_row_the_database_refuses_rolls_back_the_whole_batch(app_engine, tenants) -> None:
    a, _ = tenants
    repo = _history(app_engine, a)
    # A space passes the Python checks but not the merchant_id CHECK, so the database refuses it.
    with pytest.raises(IntegrityError) as err:
        repo.add_many([_obs(1), _obs(2, merchant_id="bad merchant")])
    assert err.value.orig.diag.constraint_name == "price_observations_merchant_id_check"
    assert repo.observations(ITEM) == []


# ---------------------------------------------------------------- tenant isolation


def test_a_repository_never_returns_another_tenants_observations(app_engine, tenants) -> None:
    a, b = tenants
    ra, rb = _history(app_engine, a), _history(app_engine, b)
    ra.add_many([_obs(1, unit_price=Decimal("1.00")), _obs(2, unit_price=Decimal("2.00"))])
    rb.add_many([_obs(3, unit_price=Decimal("99.00")), _obs(4, item_key="ITEM-2")])
    assert [o.unit_price for o in ra.observations(ITEM)] == [Decimal("2.00"), Decimal("1.00")]
    assert [o.unit_price for o in rb.observations(ITEM)] == [Decimal("99.00")]
    assert rb.observations(ITEM, merchant_id="M-9") == []
    assert ra.observations("ITEM-2") == []


def test_a_raw_app_connection_that_binds_no_tenant_sees_no_rows(app_engine, tenants) -> None:
    a, _ = tenants
    _history(app_engine, a).add_many([_obs(1)])
    with app_engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM price_observations")).scalar() == 0
        with pytest.raises(DBAPIError):  # WITH CHECK: with no tenant bound, no row can be written
            with conn.begin_nested():
                conn.execute(
                    RAW_INSERT,
                    {"t": a, "id": "raw-1", "item_key": ITEM, "price": Decimal("1"),
                     "observed_at": JAN_1},
                )
    assert len(_history(app_engine, a).observations(ITEM)) == 1


def test_the_owner_engine_cannot_act_as_a_tenant(admin_engine, tenants) -> None:
    a, _ = tenants
    with pytest.raises(PrivilegedRoleError):
        _history(admin_engine, a).observations(ITEM)


def test_every_read_filters_by_the_tenant_in_its_own_query(app_engine, app_url, tenants) -> None:
    a, _ = tenants
    _history(app_engine, a).add_many([_obs(1)])
    eng = make_engine(app_url)
    statements: list[str] = []

    def capture(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(eng, "before_cursor_execute", capture)
    try:
        _history(eng, a).observations(ITEM)
    finally:
        event.remove(eng, "before_cursor_execute", capture)
        eng.dispose()
    reads = [s for s in statements if "FROM price_observations" in s]
    assert reads, "the read never reached the database"
    assert all("price_observations.tenant_id = " in s for s in reads)
