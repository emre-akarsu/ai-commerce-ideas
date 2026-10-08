# ruff: noqa: E501
"""Price history: ``price_observations`` (migration 0007).

The customer's own price points (spec F28 clause 5): a later price-file load or a superseded offer
does not erase the point this table holds. It is a tenant table with FORCE ROW LEVEL SECURITY and
the usual ``tenant_isolation`` policy. ``app_user`` may SELECT and INSERT only: rows are history, so
there is no UPDATE or DELETE grant. Retention deletion is an owner-role job and is not built here.
Value sets, id shapes and size limits are CHECK constraints, enforced by the database itself.
"""

from alembic import op

from aidb.rls import APP_ROLE, enable_rls_sql

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

TABLES = ("price_observations",)

PRICE_OBSERVATIONS_DDL = """
    CREATE TABLE price_observations (
        tenant_id text NOT NULL REFERENCES tenants(id),
        id text NOT NULL,
        item_key text NOT NULL,
        merchant_id text NOT NULL,
        unit_price numeric(20,6) NOT NULL,
        unit text NOT NULL,
        currency text NOT NULL,
        quantity numeric(20,6),
        observed_at timestamptz NOT NULL,
        source text NOT NULL,
        recorded_at timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (tenant_id, id),
        CONSTRAINT price_observations_tenant_nonempty CHECK (tenant_id <> ''),
        CONSTRAINT price_observations_item_key_check CHECK (item_key ~ '^[A-Za-z0-9._:/ -]{1,80}$'),
        CONSTRAINT price_observations_merchant_id_check CHECK (merchant_id ~ '^[A-Za-z0-9._:-]{1,64}$'),
        CONSTRAINT price_observations_unit_price_check CHECK (unit_price >= 0),
        CONSTRAINT price_observations_unit_check CHECK (char_length(unit) BETWEEN 1 AND 24),
        CONSTRAINT price_observations_currency_check CHECK (currency ~ '^[A-Z]{3}$'),
        CONSTRAINT price_observations_quantity_check CHECK (quantity IS NULL OR quantity > 0),
        CONSTRAINT price_observations_source_check CHECK (source IN ('po_import', 'accepted_quote', 'price_file'))
    )"""

PRICE_OBSERVATIONS_INDEXES = (
    "CREATE INDEX price_observations_item_idx ON price_observations (tenant_id, item_key, observed_at DESC)",
    "CREATE INDEX price_observations_item_merchant_idx ON price_observations (tenant_id, item_key, merchant_id, observed_at DESC)",
)


def upgrade() -> None:
    op.execute(PRICE_OBSERVATIONS_DDL)
    for stmt in PRICE_OBSERVATIONS_INDEXES:
        op.execute(stmt)
    for name in TABLES:
        for stmt in enable_rls_sql(name):
            op.execute(stmt)
        op.execute(f"GRANT SELECT, INSERT ON {name} TO {APP_ROLE}")


def downgrade() -> None:
    for name in reversed(TABLES):
        op.execute(f"DROP TABLE IF EXISTS {name}")
