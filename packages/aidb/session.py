"""Tenant-scoped database sessions (stack-map S2: workers have no user JWT).

``tenant_session(engine, tenant_id)`` is the only way application code gets a connection. It opens
a transaction and sets ``app.tenant_id`` with ``set_config(..., true)`` (transaction-local, bound
parameter, so no injection and no leakage to the next pooled use). RLS then applies to every query
on that connection. The engine must connect as a role that does not bypass RLS; this is verified on
every session in the same round trip.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Connection, Engine, create_engine, text

from .rls import TENANT_SETTING

INFO_KEY = "aidb_tenant"


class PrivilegedRoleError(RuntimeError):
    """The connection role is a superuser or has BYPASSRLS, so RLS would not protect anything."""


def to_sa_url(url: str) -> str:
    """postgresql://... -> postgresql+psycopg://... (psycopg 3)."""
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def make_engine(url: str) -> Engine:
    # client_encoding: psycopg returns bytes for text on SQL_ASCII databases (e.g. initdb in a C
    # locale); forcing utf8 keeps behaviour identical everywhere.
    return create_engine(
        to_sa_url(url), pool_pre_ping=True, connect_args={"client_encoding": "utf8"}
    )


def _valid_tenant(tenant_id: str) -> str:
    if not isinstance(tenant_id, str) or not tenant_id.strip() or "\x00" in tenant_id:
        raise ValueError("tenant_id must be a non-empty string")
    return tenant_id


_BIND = text(
    "SELECT set_config('app.tenant_id', :t, true), "
    "(SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname = current_user) AS privileged"
)


@contextmanager
def tenant_session(engine: Engine, tenant_id: str) -> Iterator[Connection]:
    """Transaction bound to one tenant. Commits on success, rolls back on error."""
    tenant = _valid_tenant(tenant_id)
    with engine.begin() as conn:
        row = conn.execute(_BIND, {"t": tenant}).one()
        if row.privileged:
            raise PrivilegedRoleError(
                "connected role bypasses row level security; use the app_user role"
            )
        conn.info[INFO_KEY] = tenant
        try:
            yield conn
        finally:
            conn.info.pop(INFO_KEY, None)


def bound_tenant(conn: Connection) -> str | None:
    """The tenant a connection was bound to by ``tenant_session`` (None if unbound)."""
    value = conn.info.get(INFO_KEY)
    return value if isinstance(value, str) else None


__all__ = [
    "TENANT_SETTING",
    "PrivilegedRoleError",
    "bound_tenant",
    "make_engine",
    "tenant_session",
    "to_sa_url",
]
