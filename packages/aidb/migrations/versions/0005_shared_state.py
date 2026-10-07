# ruff: noqa: E501
"""Shared security state (known-gaps H2): what API and worker processes must agree on.

Seven tenant tables, each with ``tenant_id``, FORCE ROW LEVEL SECURITY and the usual
``tenant_isolation`` policy; ``app_user`` only, with the least privilege each needs:

* ``spent_approvals``: one row per approval id and per approval nonce that was handed to the transport.
  The primary key is the single-use guarantee. INSERT/SELECT only: a spent approval cannot be un-spent.
* ``approval_tokens``: issued approval links (claims, ``consumed``, ``po_issued``). Consumption is one
  conditional UPDATE, so exactly one caller wins.
* ``cap_spend``: the daily aggregate spend per (tenant, UTC day). A reservation is one conditional
  UPDATE (``spent + amount <= cap``), atomic under concurrency.
* ``spend_holds``: approved-but-undrafted spend (``committed``) and reserved cap spend (``reserved``)
  per (tenant, request). Rows are deleted when the spend is released.
* ``follow_up_plans``: scheduled follow-ups; ``done`` moves with one conditional UPDATE per slot.
* ``kill_switches``: the per-tenant stop for outbound mail.
* ``idempotency_keys``: stored responses for ``Idempotency-Key`` replay.
Money is ``numeric`` (read back as Decimal, rule 5). Nothing here touches the event tables: every change
that matters is also appended as a hash-chained event by the service (rule 6).
"""

from alembic import op

from aidb.rls import APP_ROLE, enable_rls_sql

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

# table -> (privileges for app_user, create statement)
_TABLES: dict[str, tuple[str, str]] = {
    "spent_approvals": ("SELECT, INSERT", """
        CREATE TABLE spent_approvals (
            tenant_id text NOT NULL REFERENCES tenants(id),
            key text NOT NULL,
            approval_id text NOT NULL,
            spent_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (tenant_id, key),
            CONSTRAINT spent_approvals_tenant_nonempty CHECK (tenant_id <> '')
        )"""),
    "approval_tokens": ("SELECT, INSERT, UPDATE", """
        CREATE TABLE approval_tokens (
            tenant_id text NOT NULL REFERENCES tenants(id),
            jti text NOT NULL,
            claims jsonb NOT NULL,
            consumed boolean NOT NULL DEFAULT false,
            po_issued boolean NOT NULL DEFAULT false,
            created_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (tenant_id, jti),
            CONSTRAINT approval_tokens_tenant_nonempty CHECK (tenant_id <> '')
        )"""),
    "cap_spend": ("SELECT, INSERT, UPDATE", """
        CREATE TABLE cap_spend (
            tenant_id text NOT NULL REFERENCES tenants(id),
            day date NOT NULL,
            spent numeric NOT NULL DEFAULT 0 CHECK (spent >= 0),
            PRIMARY KEY (tenant_id, day),
            CONSTRAINT cap_spend_tenant_nonempty CHECK (tenant_id <> '')
        )"""),
    "spend_holds": ("SELECT, INSERT, UPDATE, DELETE", """
        CREATE TABLE spend_holds (
            tenant_id text NOT NULL REFERENCES tenants(id),
            request_id text NOT NULL,
            kind text NOT NULL CHECK (kind IN ('committed', 'reserved')),
            day date NOT NULL,
            amount numeric NOT NULL CHECK (amount >= 0),
            currency text,
            PRIMARY KEY (tenant_id, request_id, kind),
            CONSTRAINT spend_holds_tenant_nonempty CHECK (tenant_id <> '')
        )"""),
    "follow_up_plans": ("SELECT, INSERT, UPDATE", """
        CREATE TABLE follow_up_plans (
            tenant_id text NOT NULL REFERENCES tenants(id),
            id text NOT NULL,
            request_id text NOT NULL,
            rfq_id text NOT NULL,
            vendor_id text NOT NULL,
            approval_id text NOT NULL,
            sched_count integer NOT NULL,
            sched_interval_seconds numeric NOT NULL,
            sent_at timestamptz NOT NULL,
            raw_mime bytea NOT NULL,
            done integer NOT NULL DEFAULT 0,
            active boolean NOT NULL DEFAULT true,
            PRIMARY KEY (tenant_id, id),
            CONSTRAINT follow_up_plans_tenant_nonempty CHECK (tenant_id <> '')
        )"""),
    "kill_switches": ("SELECT, INSERT, UPDATE", """
        CREATE TABLE kill_switches (
            tenant_id text NOT NULL REFERENCES tenants(id),
            engaged boolean NOT NULL,
            changed_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (tenant_id),
            CONSTRAINT kill_switches_tenant_nonempty CHECK (tenant_id <> '')
        )"""),
    "idempotency_keys": ("SELECT, INSERT, DELETE", """
        CREATE TABLE idempotency_keys (
            tenant_id text NOT NULL REFERENCES tenants(id),
            key text NOT NULL,
            body_hash text NOT NULL,
            status integer NOT NULL,
            content_type text NOT NULL,
            body bytea NOT NULL,
            stored_at timestamptz NOT NULL,
            PRIMARY KEY (tenant_id, key),
            CONSTRAINT idempotency_keys_tenant_nonempty CHECK (tenant_id <> '')
        )"""),
}


def upgrade() -> None:
    for name, (privileges, create) in _TABLES.items():
        op.execute(create)
        for stmt in enable_rls_sql(name):
            op.execute(stmt)
        op.execute(f"GRANT {privileges} ON {name} TO {APP_ROLE}")
    op.execute("CREATE INDEX follow_up_plans_active_idx ON follow_up_plans (tenant_id, active)")


def downgrade() -> None:
    for name in reversed(list(_TABLES)):
        op.execute(f"DROP TABLE IF EXISTS {name}")
