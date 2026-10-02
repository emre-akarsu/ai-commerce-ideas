"""Row level security helpers (R10, ADR-007, stack-map S2).

Policy: every tenant table has ``ENABLE`` + ``FORCE ROW LEVEL SECURITY`` and a policy
``tenant_isolation`` with ``tenant_id = current_setting('app.tenant_id', true)`` for USING and
WITH CHECK. Missing setting -> NULL -> no rows visible, inserts rejected.

Superusers and roles with BYPASSRLS ignore RLS entirely (``FORCE`` only covers the table owner when
it is an ordinary role). The application therefore must connect as ``app_user`` (NOSUPERUSER,
NOBYPASSRLS, minimal grants); ``tenant_session`` refuses to run on a privileged connection.
The migration/admin role is only for migrations and tenant provisioning.
"""

from __future__ import annotations

APP_ROLE = "app_user"
TENANT_SETTING = "app.tenant_id"
POLICY_NAME = "tenant_isolation"
_PRED = "tenant_id = current_setting('app.tenant_id', true)"


def enable_rls_sql(table: str, *, key: str = "tenant_id") -> list[str]:
    pred = _PRED.replace("tenant_id", key, 1)
    return [
        f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY",
        f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY",
        f"CREATE POLICY {POLICY_NAME} ON {table} USING ({pred}) WITH CHECK ({pred})",
    ]
