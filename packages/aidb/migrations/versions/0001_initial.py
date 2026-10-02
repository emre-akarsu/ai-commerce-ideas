"""Initial schema: tenant tables, RLS, app_user role, append-only events.

Events are append-only. UPDATE and DELETE are rejected by triggers (and app_user is not even
granted them), TRUNCATE is rejected too. The single exception is PII redaction (ADR-002): the
SECURITY DEFINER function ``aidb_redact_event(event_id, fields[])`` replaces raw values under
``data.payload._pii`` with the tombstone "[REDACTED]". The guard trigger only accepts an UPDATE that
(a) happens while that function has set ``aidb.redacting``, (b) changes nothing outside
``data.payload._pii`` and (c) only turns existing pii values into the tombstone. The chain hash
covers the committed pii digests, not the raw values, so the chain still verifies afterwards.
Hash/prev_hash/seq columns can never change.

The app_user role is created if missing (cluster-wide, so downgrade does not drop it) with no
password; set one out of band (or use peer/IAM auth) before using it outside local development.
"""

from alembic import op

from aidb.rls import APP_ROLE, enable_rls_sql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

PLAIN = [
    "requests",
    "vendors",
    "rfqs",
    "approvals",
    "standing_rules",
    "po_drafts",
    "corrections",
    "consent_records",
]
GRANTS = {
    "tenants": "SELECT",
    "requests": "SELECT, INSERT, UPDATE, DELETE",
    "vendors": "SELECT, INSERT, UPDATE, DELETE",
    "rfqs": "SELECT, INSERT, UPDATE, DELETE",
    "quotes": "SELECT, INSERT",
    "approvals": "SELECT, INSERT",
    "po_drafts": "SELECT, INSERT",
    "corrections": "SELECT, INSERT",
    "consent_records": "SELECT, INSERT",
    "standing_rules": "SELECT, INSERT, DELETE",
    "rule_uses": "SELECT, INSERT, UPDATE",
    "events": "SELECT, INSERT",
    "event_heads": "SELECT",
}


def _entity_table(name: str, pk: str) -> str:
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
        PRIMARY KEY ({pk}),
        CONSTRAINT {name}_tenant_nonempty CHECK (tenant_id <> '')
    )"""


def upgrade() -> None:
    op.execute(f"""
    DO $$ BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
            CREATE ROLE {APP_ROLE} LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
        END IF;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END $$""")

    op.execute("""
    CREATE TABLE tenants (
        id text PRIMARY KEY,
        name text NOT NULL DEFAULT '',
        created_at timestamptz NOT NULL DEFAULT now(),
        CONSTRAINT tenants_id_nonempty CHECK (id <> '')
    )""")
    for name in PLAIN:
        op.execute(_entity_table(name, "tenant_id, id"))
    op.execute(_entity_table("quotes", "tenant_id, id, version"))
    for name in (*PLAIN, "quotes"):
        op.execute(f"CREATE INDEX {name}_request_idx ON {name} (tenant_id, request_id)")

    op.execute("""
    CREATE TABLE rule_uses (
        tenant_id text NOT NULL REFERENCES tenants(id),
        rule_id text NOT NULL,
        used integer NOT NULL DEFAULT 0,
        PRIMARY KEY (tenant_id, rule_id),
        CONSTRAINT rule_uses_tenant_nonempty CHECK (tenant_id <> '')
    )""")
    op.execute("""
    CREATE TABLE events (
        id text NOT NULL,
        tenant_id text NOT NULL REFERENCES tenants(id),
        request_id text,
        seq bigint NOT NULL,
        ts timestamptz NOT NULL,
        actor text NOT NULL,
        type text NOT NULL,
        prev_hash text NOT NULL,
        hash text NOT NULL,
        data jsonb NOT NULL,
        PRIMARY KEY (tenant_id, id),
        CONSTRAINT events_tenant_seq_key UNIQUE (tenant_id, seq),
        CONSTRAINT events_tenant_prev_hash_key UNIQUE (tenant_id, prev_hash),
        CONSTRAINT events_tenant_nonempty CHECK (tenant_id <> '')
    )""")
    op.execute("CREATE INDEX events_request_idx ON events (tenant_id, request_id, seq)")
    op.execute("""
    CREATE TABLE event_heads (
        tenant_id text PRIMARY KEY REFERENCES tenants(id),
        count bigint NOT NULL,
        last_hash text NOT NULL
    )""")

    _events_triggers()

    for table in GRANTS:
        key = "id" if table == "tenants" else "tenant_id"
        for stmt in enable_rls_sql(table, key=key):
            op.execute(stmt)
    op.execute(f"GRANT USAGE ON SCHEMA public TO {APP_ROLE}")
    for table, privs in GRANTS.items():
        op.execute(f"GRANT {privs} ON {table} TO {APP_ROLE}")


def _events_triggers() -> None:
    op.execute("""
    CREATE FUNCTION aidb_events_guard() RETURNS trigger LANGUAGE plpgsql AS $f$
    BEGIN
        IF current_setting('aidb.redacting', true) = 'on'
           AND (to_jsonb(NEW) - 'data') = (to_jsonb(OLD) - 'data')
           AND (NEW.data #- '{payload,_pii}') = (OLD.data #- '{payload,_pii}')
           AND jsonb_typeof(OLD.data #> '{payload,_pii}') = 'object'
           AND jsonb_typeof(NEW.data #> '{payload,_pii}') = 'object'
           AND (SELECT array_agg(k ORDER BY k)
                  FROM jsonb_object_keys(NEW.data #> '{payload,_pii}') k)
               IS NOT DISTINCT FROM
               (SELECT array_agg(k ORDER BY k)
                  FROM jsonb_object_keys(OLD.data #> '{payload,_pii}') k)
           AND NOT EXISTS (
                SELECT 1 FROM jsonb_each(NEW.data #> '{payload,_pii}') n
                JOIN jsonb_each(OLD.data #> '{payload,_pii}') o USING (key)
                WHERE n.value <> o.value AND n.value <> '"[REDACTED]"'::jsonb)
        THEN
            RETURN NEW;
        END IF;
        RAISE EXCEPTION 'events is append-only: UPDATE rejected (only PII redaction is allowed)'
            USING ERRCODE = 'restrict_violation';
    END $f$""")
    op.execute("""
    CREATE FUNCTION aidb_events_reject() RETURNS trigger LANGUAGE plpgsql AS $f$
    BEGIN
        RAISE EXCEPTION 'events is append-only: % rejected', TG_OP
            USING ERRCODE = 'restrict_violation';
    END $f$""")
    op.execute(
        "CREATE TRIGGER events_no_update BEFORE UPDATE ON events "
        "FOR EACH ROW EXECUTE FUNCTION aidb_events_guard()"
    )
    op.execute(
        "CREATE TRIGGER events_no_delete BEFORE DELETE ON events "
        "FOR EACH ROW EXECUTE FUNCTION aidb_events_reject()"
    )
    op.execute(
        "CREATE TRIGGER events_no_truncate BEFORE TRUNCATE ON events "
        "FOR EACH STATEMENT EXECUTE FUNCTION aidb_events_reject()"
    )
    op.execute("""
    CREATE FUNCTION aidb_events_head() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
    SET search_path = public, pg_temp AS $f$
    BEGIN
        INSERT INTO event_heads (tenant_id, count, last_hash)
        VALUES (NEW.tenant_id, NEW.seq, NEW.hash)
        ON CONFLICT (tenant_id) DO UPDATE
          SET count = EXCLUDED.count, last_hash = EXCLUDED.last_hash;
        RETURN NULL;
    END $f$""")
    op.execute(
        "CREATE TRIGGER events_head AFTER INSERT ON events "
        "FOR EACH ROW EXECUTE FUNCTION aidb_events_head()"
    )
    op.execute("""
    CREATE FUNCTION aidb_redact_event(p_event_id text, p_fields text[]) RETURNS jsonb
    LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $f$
    DECLARE
        t text := current_setting('app.tenant_id', true);
        d jsonb;
        pii jsonb;
        f text;
    BEGIN
        IF t IS NULL OR t = '' THEN
            RAISE EXCEPTION 'no tenant context' USING ERRCODE = 'insufficient_privilege';
        END IF;
        SELECT data INTO d FROM events WHERE tenant_id = t AND id = p_event_id FOR UPDATE;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'event not found' USING ERRCODE = 'no_data_found';
        END IF;
        pii := d #> '{payload,_pii}';
        IF pii IS NULL OR jsonb_typeof(pii) <> 'object' OR pii = '{}'::jsonb THEN
            RAISE EXCEPTION 'event has no personal-data fields'
                USING ERRCODE = 'invalid_parameter_value';
        END IF;
        FOREACH f IN ARRAY p_fields LOOP
            IF NOT pii ? f THEN
                RAISE EXCEPTION 'not a personal-data field: %', f
                    USING ERRCODE = 'invalid_parameter_value';
            END IF;
            pii := jsonb_set(pii, ARRAY[f], '"[REDACTED]"'::jsonb);
        END LOOP;
        d := jsonb_set(d, '{payload,_pii}', pii);
        PERFORM set_config('aidb.redacting', 'on', true);
        UPDATE events SET data = d WHERE tenant_id = t AND id = p_event_id;
        PERFORM set_config('aidb.redacting', 'off', true);
        RETURN d;
    END $f$""")
    op.execute("REVOKE ALL ON FUNCTION aidb_redact_event(text, text[]) FROM PUBLIC")
    op.execute(f"GRANT EXECUTE ON FUNCTION aidb_redact_event(text, text[]) TO {APP_ROLE}")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS aidb_redact_event(text, text[])")
    for name in ("events_no_update", "events_no_delete", "events_no_truncate", "events_head"):
        op.execute(f"DROP TRIGGER IF EXISTS {name} ON events")
    for table in ("event_heads", "events", "rule_uses", "quotes", *reversed(PLAIN), "tenants"):
        op.execute(f"DROP TABLE IF EXISTS {table}")
    for fn in ("aidb_events_guard", "aidb_events_reject", "aidb_events_head"):
        op.execute(f"DROP FUNCTION IF EXISTS {fn}()")
