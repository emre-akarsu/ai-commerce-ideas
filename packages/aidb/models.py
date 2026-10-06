"""SQLAlchemy Core table definitions (the Postgres schema of record is the alembic migration).

Every tenant table has ``tenant_id text not null`` and row level security (see ``rls.py``).
Primary keys are ``(tenant_id, id)`` rather than ``id`` alone so that an id that already exists in
another tenant is not an existence oracle (a colliding insert simply succeeds in its own tenant).
The pydantic domain object lives in ``data jsonb`` (``model_dump(mode="json")``); the typed columns
are copies used for keys, filtering and constraints.
"""

from __future__ import annotations

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    MetaData,
    PrimaryKeyConstraint,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()

ENTITY_TABLES = (
    "requests",
    "vendors",
    "rfqs",
    "quotes",
    "approvals",
    "standing_rules",
    "po_drafts",
    "corrections",
    "consent_records",
    "supplier_profiles",
    "assumptions",
)
# Every table below carries tenant_id and has FORCE ROW LEVEL SECURITY (tenants: id is the tenant).
TENANT_TABLES = ("tenants", *ENTITY_TABLES, "rule_uses", "events", "event_heads")

tenants = Table(
    "tenants",
    metadata,
    Column("id", Text, primary_key=True),
    Column("name", Text, nullable=False, server_default=""),
    Column("created_at", TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
    CheckConstraint("id <> ''", name="tenants_id_nonempty"),
)


def _entity(name: str, *, versioned: bool = False) -> Table:
    pk = ("tenant_id", "id", "version") if versioned else ("tenant_id", "id")
    return Table(
        name,
        metadata,
        Column("id", Text, nullable=False),
        Column("tenant_id", Text, ForeignKey("tenants.id"), nullable=False),
        Column("request_id", Text),
        Column("vendor_id", Text),
        Column("state", Text),
        Column("version", Integer, nullable=False, server_default="1"),
        Column("created_at", TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
        Column("data", JSONB, nullable=False),
        PrimaryKeyConstraint(*pk),
        CheckConstraint("tenant_id <> ''", name=f"{name}_tenant_nonempty"),
    )


requests = _entity("requests")
vendors = _entity("vendors")
rfqs = _entity("rfqs")
quotes = _entity("quotes", versioned=True)
approvals = _entity("approvals")
standing_rules = _entity("standing_rules")
po_drafts = _entity("po_drafts")
corrections = _entity("corrections")
consent_records = _entity("consent_records")
supplier_profiles = _entity("supplier_profiles")
assumptions = _entity("assumptions")

rule_uses = Table(
    "rule_uses",
    metadata,
    Column("tenant_id", Text, ForeignKey("tenants.id"), nullable=False),
    Column("rule_id", Text, nullable=False),
    Column("used", Integer, nullable=False, server_default="0"),
    PrimaryKeyConstraint("tenant_id", "rule_id"),
)

events = Table(
    "events",
    metadata,
    Column("id", Text, nullable=False),
    Column("tenant_id", Text, ForeignKey("tenants.id"), nullable=False),
    Column("request_id", Text),
    Column("seq", BigInteger, nullable=False),
    Column("ts", TIMESTAMP(timezone=True), nullable=False),
    Column("actor", Text, nullable=False),
    Column("type", Text, nullable=False),
    Column("prev_hash", Text, nullable=False),
    Column("hash", Text, nullable=False),
    Column("data", JSONB, nullable=False),  # full Event.model_dump(mode="json")
    PrimaryKeyConstraint("tenant_id", "id"),
    UniqueConstraint("tenant_id", "seq", name="events_tenant_seq_key"),
    UniqueConstraint("tenant_id", "prev_hash", name="events_tenant_prev_hash_key"),
    CheckConstraint("tenant_id <> ''", name="events_tenant_nonempty"),
)

event_heads = Table(  # maintained by a trigger on events; app_user can only read it
    "event_heads",
    metadata,
    Column("tenant_id", Text, ForeignKey("tenants.id"), primary_key=True),
    Column("count", BigInteger, nullable=False),
    Column("last_hash", Text, nullable=False),
)

TABLES_BY_NAME: dict[str, Table] = dict(metadata.tables)
