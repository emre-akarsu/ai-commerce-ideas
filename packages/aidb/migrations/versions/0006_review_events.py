# ruff: noqa: E501
"""Review telemetry: ``review_events`` and ``review_drills`` (migration 0006).

``review_events`` records how a reviewer engaged with a review surface (shown, expanded, approved,
edited, rejected, deferred, dismissed) and for how long. ``review_drills`` holds seeded drill cases,
each with the decision the reviewer is expected to make, at most one per subject and tenant. Both
are tenant tables with FORCE ROW LEVEL SECURITY and the usual ``tenant_isolation`` policy.
``app_user`` may SELECT and INSERT only: rows are history, so there is no UPDATE or DELETE grant.
Value sets, id shapes and size limits are CHECK constraints, enforced by the database itself.
"""

from alembic import op

from aidb.rls import APP_ROLE, enable_rls_sql

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

TABLES = ("review_events", "review_drills")

REVIEW_EVENTS_DDL = """
    CREATE TABLE review_events (
        tenant_id text NOT NULL REFERENCES tenants(id),
        id text NOT NULL,
        user_ref text NOT NULL,
        surface text NOT NULL,
        subject_id text NOT NULL,
        event text NOT NULL,
        occurred_at timestamptz NOT NULL,
        duration_ms integer,
        meta jsonb NOT NULL DEFAULT '{}',
        PRIMARY KEY (tenant_id, id),
        CONSTRAINT review_events_tenant_nonempty CHECK (tenant_id <> ''),
        CONSTRAINT review_events_user_ref_check CHECK (user_ref ~ '^[0-9a-f]{64}$'),
        CONSTRAINT review_events_surface_check CHECK (surface IN ('approval_card', 'exception', 'clarification', 'review_line', 'comparison')),
        CONSTRAINT review_events_subject_id_check CHECK (subject_id ~ '^[A-Za-z0-9._:-]{1,64}$'),
        CONSTRAINT review_events_event_check CHECK (event IN ('shown', 'expanded', 'approved', 'edited', 'rejected', 'deferred', 'dismissed')),
        CONSTRAINT review_events_duration_ms_check CHECK (duration_ms >= 0),
        CONSTRAINT review_events_meta_check CHECK (jsonb_typeof(meta) = 'object' AND length(meta::text) <= 400)
    )"""

REVIEW_EVENTS_INDEXES = (
    "CREATE INDEX review_events_occurred_idx ON review_events (tenant_id, occurred_at)",
    "CREATE INDEX review_events_subject_idx ON review_events (tenant_id, subject_id)",
)

REVIEW_DRILLS_DDL = """
    CREATE TABLE review_drills (
        tenant_id text NOT NULL REFERENCES tenants(id),
        id text NOT NULL,
        kind text NOT NULL,
        subject_id text NOT NULL,
        expected text NOT NULL,
        created_by text NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now(),
        PRIMARY KEY (tenant_id, id),
        CONSTRAINT review_drills_tenant_nonempty CHECK (tenant_id <> ''),
        CONSTRAINT review_drills_kind_check CHECK (kind ~ '^[a-z_]{1,32}$'),
        CONSTRAINT review_drills_subject_id_check CHECK (subject_id ~ '^[A-Za-z0-9._:-]{1,64}$'),
        CONSTRAINT review_drills_expected_check CHECK (expected IN ('reject', 'edit', 'flag')),
        CONSTRAINT review_drills_created_by_check CHECK (created_by ~ '^[0-9a-f]{64}$'),
        CONSTRAINT review_drills_tenant_subject_key UNIQUE (tenant_id, subject_id)
    )"""


def upgrade() -> None:
    op.execute(REVIEW_EVENTS_DDL)
    for stmt in REVIEW_EVENTS_INDEXES:
        op.execute(stmt)
    op.execute(REVIEW_DRILLS_DDL)
    for name in TABLES:
        for stmt in enable_rls_sql(name):
            op.execute(stmt)
        op.execute(f"GRANT SELECT, INSERT ON {name} TO {APP_ROLE}")


def downgrade() -> None:
    for name in reversed(TABLES):
        op.execute(f"DROP TABLE IF EXISTS {name}")
