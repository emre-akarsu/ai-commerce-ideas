"""Tenant directory function for the worker cron fan-out (review finding M8).

``tenants`` has FORCE ROW LEVEL SECURITY, so ``app_user`` with no tenant context sees no rows and
the worker's per-tenant fan-out would silently do nothing (or need an RLS-bypassing credential).
``aidb_list_tenant_ids()`` is SECURITY DEFINER (runs as the migration role that owns it) with a
pinned ``search_path``; EXECUTE is revoked from PUBLIC and granted only to ``app_user``. It returns
tenant ids only (no names, no tenant data). A narrow SELECT policy for the owner role lets the
function read ``tenants`` despite FORCE RLS; ``app_user`` is not covered by that policy.

Compatibility note (pre-release): the event hash chain is now an HMAC keyed by ``AUDIT_CHAIN_KEY``
(see components.evidence.log). Chains written before this change used an unkeyed SHA-256 and will
fail verification; no data migration is provided.
"""

from alembic import op

from aidb.rls import APP_ROLE

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE POLICY tenants_directory_owner ON tenants FOR SELECT TO CURRENT_USER USING (true)""")
    op.execute("""
    CREATE FUNCTION aidb_list_tenant_ids() RETURNS SETOF text
    LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public, pg_temp AS $f$
        SELECT id FROM public.tenants ORDER BY id
    $f$""")
    op.execute("REVOKE ALL ON FUNCTION aidb_list_tenant_ids() FROM PUBLIC")
    op.execute(f"GRANT EXECUTE ON FUNCTION aidb_list_tenant_ids() TO {APP_ROLE}")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS aidb_list_tenant_ids()")
    op.execute("DROP POLICY IF EXISTS tenants_directory_owner ON tenants")
