# ruff: noqa: E501
"""Supplier profiles and the assumption ledger (api-contract-mvp.md sections 1 and 2).

``supplier_profiles`` holds one row per (tenant, vendor): the buyer's profile of the supplier, the admin
attestation and the suppression flag. ``assumptions`` holds one row per ledger entry of a request. Both
are tenant tables with FORCE ROW LEVEL SECURITY and the usual ``tenant_isolation`` policy; ``app_user``
may SELECT, INSERT and UPDATE but not DELETE (rows are history). Neither table touches the event
tables: every change is also appended as an event by the service.
"""

from alembic import op

from aidb.rls import APP_ROLE, enable_rls_sql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

TABLES = ("supplier_profiles", "assumptions")


def _table(name: str) -> str:
    return f"""
    CREATE TABLE {name} (
        id text NOT NULL,
        tenant_id text NOT NULL REFERENCES tenants(id),
        request_id text,
        vendor_id text,
        state text,
        version integer NOT NULL DEFAULT 1,
        created_at timestamptz NOT NULL DEFAULT now(),
        data jsonb NOT NULL,
        PRIMARY KEY (tenant_id, id),
        CONSTRAINT {name}_tenant_nonempty CHECK (tenant_id <> '')
    )"""


def upgrade() -> None:
    for name in TABLES:
        op.execute(_table(name))
        op.execute(f"CREATE INDEX {name}_request_idx ON {name} (tenant_id, request_id)")
        for stmt in enable_rls_sql(name):
            op.execute(stmt)
        op.execute(f"GRANT SELECT, INSERT, UPDATE ON {name} TO {APP_ROLE}")


def downgrade() -> None:
    for name in reversed(TABLES):
        op.execute(f"DROP TABLE IF EXISTS {name}")
