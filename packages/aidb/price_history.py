"""Postgres price history (migration 0007): the ``price_observations`` record set (F28 clause 5).

``PgPriceHistory(engine).for_tenant(tenant_id)`` returns a ``TenantPriceHistory``, which satisfies
the ``PriceHistory`` Protocol in ``components/verify/history.py``. Every call is one
``tenant_session`` transaction, and the tenant filter is also explicit in each query. ``app_user``
may SELECT and INSERT only: a point is never updated or deleted here, so a later price-file load
cannot erase an earlier one. A batch is validated in Python before any write and is written in one
transaction, so it lands whole or not at all. Errors name the field and never echo the rejected
value.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Iterable
from datetime import datetime
from decimal import Context, Decimal, InvalidOperation
from typing import Any

from sqlalchemy import Engine, RowMapping, insert, select

from components.verify.history import PriceHistory, PriceObservation

from .models import price_observations
from .session import tenant_session

PRICE_SOURCES = frozenset({"po_import", "accepted_quote", "price_file"})
MAX_LIMIT = 200
DEFAULT_LIMIT = 20
_CURRENCY = re.compile(r"[A-Z]{3}")
_SIX_PLACES = Decimal("0.000001")
_MAX_STORED = Decimal("99999999999999.999999")  # numeric(20,6): 14 digits before the point
_WIDE = Context(prec=60)  # more digits than numeric(20,6) can hold, so quantize never overflows
_NEWEST_FIRST = (
    price_observations.c.observed_at.desc(),
    price_observations.c.recorded_at.desc(),
    price_observations.c.id.desc(),
)


def _stores_exactly(value: Decimal) -> bool:
    """True when numeric(20,6) keeps the value unchanged: at most 6 decimals, 14 integer digits."""
    try:
        same = value.quantize(_SIX_PLACES, context=_WIDE) == value
    except InvalidOperation:
        return False
    return same and abs(value) <= _MAX_STORED


def _decimal(name: str, value: object) -> Decimal:
    """A finite Decimal that the column stores without rounding. Floats and ints are refused."""
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError(f"{name} must be a finite Decimal")
    if not _stores_exactly(value):
        raise ValueError(f"{name} must have at most 6 decimal places and fit numeric(20,6)")
    return value


def _validate(obs: PriceObservation) -> None:
    """Refuse a value before any write. Item key, merchant and unit are checked by the database."""
    if _decimal("unit_price", obs.unit_price) < 0:
        raise ValueError("unit_price must not be negative")
    if obs.quantity is not None and _decimal("quantity", obs.quantity) <= 0:
        raise ValueError("quantity must be positive when given")
    if not isinstance(obs.currency, str) or not _CURRENCY.fullmatch(obs.currency):
        raise ValueError("currency must be three upper-case letters")
    if not isinstance(obs.observed_at, datetime) or obs.observed_at.utcoffset() is None:
        raise ValueError("observed_at must be a timezone-aware datetime")
    if not isinstance(obs.source, str) or obs.source not in PRICE_SOURCES:
        raise ValueError(f"source must be one of: {', '.join(sorted(PRICE_SOURCES))}")


def _check_limit(limit: int) -> None:
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_LIMIT:
        raise ValueError(f"limit must be an integer from 1 to {MAX_LIMIT}")


def _tenant(value: object) -> str:
    """The same rule as ``aidb.session``: a non-empty string without NUL bytes."""
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ValueError("tenant_id must be a non-empty string")
    return value


def _row(tenant: str, obs: PriceObservation) -> dict[str, Any]:
    return {
        "tenant_id": tenant,
        "id": uuid.uuid4().hex,
        "item_key": obs.item_key,
        "merchant_id": obs.merchant_id,
        "unit_price": obs.unit_price,
        "unit": obs.unit,
        "currency": obs.currency,
        "quantity": obs.quantity,
        "observed_at": obs.observed_at,
        "source": obs.source,
    }


def _observation(m: RowMapping) -> PriceObservation:
    return PriceObservation(
        item_key=m["item_key"],
        merchant_id=m["merchant_id"],
        unit_price=m["unit_price"],
        unit=m["unit"],
        currency=m["currency"],
        quantity=m["quantity"],
        observed_at=m["observed_at"],
        source=m["source"],
    )


class TenantPriceHistory:
    """One tenant's price history. Use the app_user engine; one instance per tenant."""

    def __init__(self, engine: Engine, tenant_id: str) -> None:
        self._engine = engine
        self._tenant = tenant_id

    def observations(
        self, item_key: str, merchant_id: str | None = None, limit: int = DEFAULT_LIMIT
    ) -> list[PriceObservation]:
        _check_limit(limit)
        p = price_observations
        stmt = select(
            p.c.item_key, p.c.merchant_id, p.c.unit_price, p.c.unit, p.c.currency,
            p.c.quantity, p.c.observed_at, p.c.source,
        ).where(p.c.tenant_id == self._tenant, p.c.item_key == item_key)
        if merchant_id is not None:
            stmt = stmt.where(p.c.merchant_id == merchant_id)
        stmt = stmt.order_by(*_NEWEST_FIRST).limit(limit)
        with tenant_session(self._engine, self._tenant) as conn:
            rows = conn.execute(stmt).mappings().all()
        return [_observation(m) for m in rows]

    def add_many(self, observations: Iterable[PriceObservation]) -> int:
        batch = list(observations)
        for obs in batch:
            _validate(obs)
        if not batch:
            return 0
        rows = [_row(self._tenant, obs) for obs in batch]
        with tenant_session(self._engine, self._tenant) as conn:
            conn.execute(insert(price_observations), rows)
        return len(rows)


class PgPriceHistory:
    """Postgres price history. Pass the app_user engine; ``for_tenant`` picks the tenant."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def for_tenant(self, tenant_id: str) -> TenantPriceHistory:
        return TenantPriceHistory(self._engine, _tenant(tenant_id))


def _as_price_history(history: TenantPriceHistory) -> PriceHistory:
    """Static check only: mypy fails here if TenantPriceHistory stops satisfying the Protocol."""
    return history
