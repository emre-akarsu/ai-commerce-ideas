# ruff: noqa: E501
"""Stage-2 tables: offers, approved matches, price imports, kit templates, quote snapshots.

Every tenant table has ``tenant_id``, FORCE ROW LEVEL SECURITY and the usual ``tenant_isolation``
policy. Grants for ``app_user`` are minimal: ``price_imports`` and ``quote_snapshots`` are append-only
(no UPDATE or DELETE), ``offers`` has no UPDATE, ``approved_matches`` is upserted, ``kit_templates``
is fully editable. ``shared_offers`` is public platform price data (synthetic/licensed list prices,
no tenant column, no vendor quotes); ``app_user`` can only SELECT it, the platform loader writes it
with the migration/admin role. Money and quantities live as strings inside ``data`` jsonb (rule 5).
"""

from alembic import op

from aidb.rls import APP_ROLE, enable_rls_sql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

TENANT_TABLES = (
    "offers",
    "approved_matches",
    "price_imports",
    "kit_templates",
    "quote_snapshots",
)

_OFFER_COLS = """
        sku_id text NOT NULL,
        merchant_id text NOT NULL,
        source_kind text NOT NULL,
        observed_at timestamptz NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now(),
        data jsonb NOT NULL"""

_DDL = {
    "offers": f"""
    CREATE TABLE offers (
        id text NOT NULL,
        tenant_id text NOT NULL REFERENCES tenants(id),{_OFFER_COLS},
        PRIMARY KEY (tenant_id, id),
        CONSTRAINT offers_tenant_nonempty CHECK (tenant_id <> '')
    )""",
    "approved_matches": """
    CREATE TABLE approved_matches (
        signature text NOT NULL,
        tenant_id text NOT NULL REFERENCES tenants(id),
        updated_at timestamptz NOT NULL DEFAULT now(),
        data jsonb NOT NULL,
        PRIMARY KEY (tenant_id, signature),
        CONSTRAINT approved_matches_tenant_nonempty CHECK (tenant_id <> '')
    )""",
    "price_imports": """
    CREATE TABLE price_imports (
        seq bigint GENERATED ALWAYS AS IDENTITY,
        tenant_id text NOT NULL REFERENCES tenants(id),
        merchant_id text NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now(),
        data jsonb NOT NULL,
        PRIMARY KEY (tenant_id, seq),
        CONSTRAINT price_imports_tenant_nonempty CHECK (tenant_id <> '')
    )""",
    "kit_templates": """
    CREATE TABLE kit_templates (
        id text NOT NULL,
        tenant_id text NOT NULL REFERENCES tenants(id),
        name text NOT NULL,
        scope_id text NOT NULL,
        saved_at text NOT NULL DEFAULT '',
        created_at timestamptz NOT NULL DEFAULT now(),
        data jsonb NOT NULL,
        PRIMARY KEY (tenant_id, id),
        CONSTRAINT kit_templates_scope_name_key UNIQUE (tenant_id, scope_id, name),
        CONSTRAINT kit_templates_tenant_nonempty CHECK (tenant_id <> '')
    )""",
    "quote_snapshots": """
    CREATE TABLE quote_snapshots (
        id text NOT NULL,
        tenant_id text NOT NULL REFERENCES tenants(id),
        version integer NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now(),
        data jsonb NOT NULL,
        PRIMARY KEY (tenant_id, id, version),
        CONSTRAINT quote_snapshots_version_positive CHECK (version >= 1),
        CONSTRAINT quote_snapshots_tenant_nonempty CHECK (tenant_id <> '')
    )""",
}

_GRANTS = {
    "offers": "SELECT, INSERT, DELETE",
    "approved_matches": "SELECT, INSERT, UPDATE",
    "price_imports": "SELECT, INSERT",
    "kit_templates": "SELECT, INSERT, UPDATE, DELETE",
    "quote_snapshots": "SELECT, INSERT",
}


def upgrade() -> None:
    for name in TENANT_TABLES:
        op.execute(_DDL[name])
        for stmt in enable_rls_sql(name):
            op.execute(stmt)
        op.execute(f"GRANT {_GRANTS[name]} ON {name} TO {APP_ROLE}")
    op.execute(f"""
    CREATE TABLE shared_offers (
        id text PRIMARY KEY,{_OFFER_COLS}
    )""")
    op.execute(f"GRANT SELECT ON shared_offers TO {APP_ROLE}")
    for name in ("offers", "shared_offers"):
        op.execute(f"CREATE INDEX {name}_sku_idx ON {name} (sku_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS shared_offers")
    for name in reversed(TENANT_TABLES):
        op.execute(f"DROP TABLE IF EXISTS {name}")
