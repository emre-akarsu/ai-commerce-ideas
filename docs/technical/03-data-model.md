# Data model

Status: the schema after migrations 0001 to 0007, read from a live PostgreSQL 16 database that the migrations were applied to (32 relations). Everything the app stores for a tenant in its own tables lives behind row-level security. Three things are outside that: the platform-wide `shared_offers` table; the `procrastinate_*` queue tables, which the worker reaches through its own `PROCRASTINATE_DATABASE_URL` and which a one-off Procrastinate schema command creates (see `apps/worker/README.md`), not Alembic; and two per-process caches that are not in the database at all, the prepared-message cache and the approval-link notifier (listed in `REMAINING_H2` in `apps/api/asgi.py`).

## Design

- **One generic shape for the purchasing entities.** `requests`, `vendors`, `rfqs`, `quotes`, `approvals`, `standing_rules`, `po_drafts`, `corrections`, `consent_records`, `supplier_profiles` and `assumptions` share the columns `id`, `tenant_id`, `request_id`, `vendor_id`, `state`, `version`, `created_at` and `data jsonb`. For most of them the Pydantic model lives in `data` (`corrections` and `consent_records` store a plain dict). The other columns are copies kept for indexing and queries.
- **The only foreign key is to `tenants`.** Relationships between entities (a request has RFQs, an RFQ has quotes) are by id inside the rows. The database does not enforce them. The generic repository checks only that the object is the right type and belongs to the repository's tenant; whether the thing a row points at exists is checked by the service code, not by the storage layer.
- **Composite primary keys start with `tenant_id`.** Two tenants can use the same id without clashing, and one tenant can never address another's row by id.
- **Row-level security on 30 tables, forced.** Every tenant table has `ENABLE` and `FORCE ROW LEVEL SECURITY` and a policy `tenant_isolation`, `tenant_id = current_setting('app.tenant_id', true)` for both `USING` and `WITH CHECK`. `tenants` has no `tenant_id` column, so its policy compares `id` instead, and it has a second policy, `tenants_directory_owner` (migration 0002, `SELECT` only). With no tenant set the setting is `NULL` on a new connection and an empty string on a pooled connection that has been used before; either way no row is visible and no insert is accepted, and a `CHECK (tenant_id <> '')` on every tenant table except `event_heads` backs the empty-string case (`event_heads` is written only by a trigger, and its `tenant_id` references `tenants.id`, which has `CHECK (id <> '')`). `shared_offers` and `alembic_version` have no policy.
- **The app never connects as the owner.** It uses the `app_user` role (`NOSUPERUSER`, `NOBYPASSRLS`, least-privilege grants). `tenant_session` refuses to run if the connected role is a superuser or has `BYPASSRLS` (`PrivilegedRoleError`), so a mistake in the connection string fails loudly.
- **Append-only where history matters.** Grants are narrowed so that rows that are history can be read and inserted but not changed (see the last column of each table below). The audit log is also protected by triggers.
- **Money and decimal quantities in `data` are strings** parsed to `Decimal` in code (rule R9 of the product spec, rule 5 in `CLAUDE.md`). Whole-number fields (`Request.quantity`, the PO draft quantity, `Quote.moq`) are JSON numbers. A few typed columns use `numeric`: `price_observations` (`unit_price`, `quantity`), `cap_spend.spent`, `spend_holds.amount` and `follow_up_plans.sched_interval_seconds`. The newer typed tables (`price_observations`, `review_events`, `review_drills`) also use CHECK constraints for value sets, id shapes and size limits.
- **Retention deletes are an owner-role job** and no deployment runs one. Two pieces exist: `aidb.telemetry.purge_review_events(admin_engine, before)` deletes every tenant's review events older than a cutoff (it refuses a role that is not a superuser and has no `BYPASSRLS`), and the worker has a scheduled `purge_expired_raw_email` task. Nothing calls the first, and `worker_main.py` does not configure the raw-email store the second needs, so that task fails with "no raw email store configured".

## Relationships

The first diagram is the purchasing side. The lines from `tenants` are real foreign keys (`tenant_id` references `tenants.id`). All the other lines are logical (by id inside the rows), not database foreign keys.

```mermaid
erDiagram
  tenants ||--o{ requests : "tenant_id"
  tenants ||--o{ vendors : "tenant_id"
  tenants ||--o{ events : "tenant_id"
  requests ||--o{ assumptions : "request_id"
  requests ||--o{ rfqs : "request_id"
  requests ||--o{ events : "request_id"
  requests ||--o{ approvals : "no request_id on the row"
  requests ||--o| po_drafts : "request_id"
  requests ||--o{ spend_holds : "request_id"
  vendors ||--o| supplier_profiles : "vendor_id"
  vendors ||--o{ rfqs : "vendor_id"
  rfqs ||--o{ quotes : "rfq_id in data (versions)"
  quotes ||--o{ po_drafts : "quote_id, quote_version in data"
  approvals ||--o{ spent_approvals : "two rows: approval id and nonce"
  event_heads ||--o{ events : "one head row per tenant"
  requests {
    text tenant_id PK
    text id PK
    text state
    jsonb data
  }
  rfqs {
    text tenant_id PK
    text id PK
    text request_id
    text vendor_id
    jsonb data
  }
  quotes {
    text tenant_id PK
    text id PK
    int version PK
    jsonb data
  }
  events {
    text tenant_id PK
    text id PK
    bigint seq
    text prev_hash
    text hash
    jsonb data
  }
```

The second diagram is the quote engine and the review telemetry. None of these tables has a link to a purchasing request.

```mermaid
erDiagram
  tenants ||--o{ offers : "tenant_id"
  tenants ||--o{ price_imports : "tenant_id"
  tenants ||--o{ price_observations : "tenant_id"
  tenants ||--o{ approved_matches : "tenant_id"
  tenants ||--o{ kit_templates : "tenant_id"
  tenants ||--o{ quote_snapshots : "tenant_id"
  tenants ||--o{ review_events : "tenant_id"
  tenants ||--o{ review_drills : "tenant_id"
  shared_offers {
    text id PK
    text sku_id
    text merchant_id
    text source_kind
    jsonb data
  }
  offers {
    text tenant_id PK
    text id PK
    text sku_id
    text merchant_id
    text source_kind
    timestamptz observed_at
    jsonb data
  }
  quote_snapshots {
    text tenant_id PK
    text id PK
    int version PK
    jsonb data
  }
  price_observations {
    text tenant_id PK
    text id PK
    text item_key
    text merchant_id
    numeric unit_price
    text unit
    text currency
  }
  review_events {
    text tenant_id PK
    text id PK
    text user_ref
    text surface
    text event
    jsonb meta
  }
```

## Tables

### Platform

| Table | Holds | Primary key | The app role may |
|---|---|---|---|
| `alembic_version` | The migration head. | `version_num` | nothing |
| `tenants` | The tenant directory (id, name). Read-only for the app. | `id` | SELECT |

### Purchasing

| Table | Holds | Primary key | The app role may |
|---|---|---|---|
| `approvals` | Approvals of four kinds: per message, standing, purchase order and substitution. Append-only. The row has no `request_id`. | `tenant_id, id` | SELECT, INSERT |
| `assumptions` | The assumption ledger: one row per entry of a request. Rows are history, never deleted. | `tenant_id, id` | SELECT, INSERT, UPDATE |
| `consent_records` | Defined, with a repository. No application code writes it yet. | `tenant_id, id` | SELECT, INSERT |
| `corrections` | Defined, with a repository. No application code writes it yet. | `tenant_id, id` | SELECT, INSERT |
| `po_drafts` | Purchase order drafts. Append-only. | `tenant_id, id` | SELECT, INSERT |
| `quotes` | One row per version of a quote read from a reply. Append-only, so a re-read is a new version. | `tenant_id, id, version` | SELECT, INSERT |
| `requests` | One row per purchase request. The `Request` model is in `data`; `state` is a copy of the workflow state for queries. | `tenant_id, id` | SELECT, INSERT, UPDATE, DELETE |
| `rfqs` | One row per message to a supplier: subject, body, reply token and `sent_message_id`. | `tenant_id, id` | SELECT, INSERT, UPDATE, DELETE |
| `rule_uses` | How many times each standing rule has been used. | `tenant_id, rule_id` | SELECT, INSERT, UPDATE |
| `standing_rules` | Standing pre-authorisation rules (R1). Rows can be created and revoked, not edited. | `tenant_id, id` | SELECT, INSERT, DELETE |
| `supplier_profiles` | One row per supplier: the buyer's profile, the admin's verification (who, when, note) and the suppression flag. | `tenant_id, id` | SELECT, INSERT, UPDATE |
| `vendors` | Suppliers: name, domain, contact email, preferred, opted out. | `tenant_id, id` | SELECT, INSERT, UPDATE, DELETE |

### Audit

| Table | Holds | Primary key | The app role may |
|---|---|---|---|
| `event_heads` | Per-tenant chain head: event count and last hash. Written by the append, never by the app role directly. | `tenant_id` | SELECT |
| `events` | The hash-chained audit log. Append-only, enforced by triggers as well as by grants. | `tenant_id, id` | SELECT, INSERT |

### Shared security state

The seven tables the API and worker processes must agree on (`SHARED_STATE_TABLES` in `aidb.models`, migration 0005).

| Table | Holds | Primary key | The app role may |
|---|---|---|---|
| `approval_tokens` | Issued approval links: signed claims, `consumed`, `po_issued`. The claims do not name a request. Consuming one is a single conditional UPDATE, so exactly one caller wins. | `tenant_id, jti` | SELECT, INSERT, UPDATE |
| `cap_spend` | Daily aggregate spend per tenant and UTC day. A reservation is one conditional UPDATE (`spent + amount <= cap`). | `tenant_id, day` | SELECT, INSERT, UPDATE |
| `follow_up_plans` | A follow-up plan: the bytes of the message that was sent plus a schedule (count and interval). A row exists only if a message was prepared with a schedule. The purchasing service passes none (the default is no follow-ups), so the application as built writes no rows. | `tenant_id, id` | SELECT, INSERT, UPDATE |
| `idempotency_keys` | Stored responses to idempotent writes (2xx only). The `key` column holds a JSON array of user, role, method, path and the client's `Idempotency-Key`, so a stored response is only replayed to the same user and role. `body_hash` covers the method, the query string and the body. Entries expire after 24 hours, and expired rows of the tenant are deleted on the next write. | `tenant_id, key` | SELECT, INSERT, DELETE |
| `kill_switches` | The per-tenant kill-switch state. | `tenant_id` | SELECT, INSERT, UPDATE |
| `spend_holds` | Approved-but-undrafted spend (`committed`) and reserved cap spend (`reserved`) per request. Deleted when the spend is released. | `tenant_id, request_id, kind` | SELECT, INSERT, UPDATE, DELETE |
| `spent_approvals` | One row per approval id and per nonce handed to the transport. The primary key is the single-use guarantee. | `tenant_id, key` | SELECT, INSERT |

### Quote engine

| Table | Holds | Primary key | The app role may |
|---|---|---|---|
| `approved_matches` | A customer's approved line-to-product matches, keyed by a signature. Upserted. | `tenant_id, signature` | SELECT, INSERT, UPDATE |
| `kit_templates` | Saved job templates: answers, sizes, option picks. No prices. | `tenant_id, id` | SELECT, INSERT, UPDATE, DELETE |
| `offers` | A tenant's price offers, loaded from price files. | `tenant_id, id` | SELECT, INSERT, DELETE |
| `price_imports` | One append-only report per price-file load. | `tenant_id, seq` | SELECT, INSERT |
| `price_observations` | The customer's own price points over time. Typed columns with CHECK constraints. | `tenant_id, id` | SELECT, INSERT |
| `quote_snapshots` | Saved quote documents, one row per version. Append-only. | `tenant_id, id, version` | SELECT, INSERT |
| `shared_offers` | Public platform price data. No tenant column and no row-level security: the app role can only read it. | `id` | SELECT |

### Telemetry

| Table | Holds | Primary key | The app role may |
|---|---|---|---|
| `review_drills` | Seeded drill cases and the decision a reviewer should make. Append-only. | `tenant_id, id` | SELECT, INSERT |
| `review_events` | Content-free review events. Typed columns with CHECK constraints. Append-only. | `tenant_id, id` | SELECT, INSERT |

Every table that has `tenant_id` also has the `tenant_isolation` policy. `corrections` and `consent_records` have repositories (`PgTenantStore.corrections`, `.consents`) but nothing in the application writes or reads them yet.

## The audit log in the database

`events` is the hash-chained audit log, one chain per tenant.

- `seq` is unique per tenant, and so is `prev_hash`, so a chain cannot fork.
- `events_no_update` (guard), `events_no_delete` and `events_no_truncate` reject changes. The one allowed change is personal-data redaction: `aidb_redact_event(event_id, fields[])` is a `SECURITY DEFINER` function that replaces named values under `data.payload._pii` with `"[REDACTED]"`, takes the tenant from the session setting, and sets a transaction-local flag that the guard trigger checks. The chain hash covers keyed digests of the personal data, not the raw values, so the chain still verifies after a redaction.
- `events_head` is an `AFTER INSERT` trigger (also `SECURITY DEFINER`) that keeps `event_heads` (count and last hash) up to date, so the app role needs only `SELECT` on it.
- The hash is an HMAC under `AUDIT_CHAIN_KEY`, so rewriting a row and its successors requires the key. The export tail can still be truncated with a rewritten head (see [known gaps](../architecture/known-gaps.md)).

## Migrations

Each revision id is the four-digit number; the file is `packages/aidb/migrations/versions/<id>_<name>.py`.

| Revision | What it adds |
|---|---|
| `0001` (`_initial`) | The `app_user` role, `tenants`, the generic entity tables, `rule_uses`, `events`, `event_heads`, the append-only triggers, the redaction function, RLS and grants. |
| `0002` (`_tenant_directory`) | `aidb_list_tenant_ids()`, a `SECURITY DEFINER` function that returns tenant ids only, for the worker's per-tenant fan-out (the app role cannot read `tenants` without a tenant context). |
| `0003` (`_suppliers_assumptions`) | `supplier_profiles` and `assumptions`. |
| `0004` (`_stage2_tables`) | `offers`, `shared_offers`, `approved_matches`, `price_imports`, `kit_templates`, `quote_snapshots`. |
| `0005` (`_shared_state`) | `spent_approvals`, `approval_tokens`, `cap_spend`, `spend_holds`, `kill_switches`, `idempotency_keys`, `follow_up_plans`: what the API and worker processes must agree on. |
| `0006` (`_review_events`) | `review_events` and `review_drills`. |
| `0007` (`_price_observations`) | `price_observations`. |

Run them with `python -c "from aidb.migrate import upgrade; upgrade('<owner url>')"` (what the compose `migrate` service does). Migrations run as the owner role. A chain written before the keyed hash was introduced fails verification, and no data migration was provided (the project is pre-release).

## How the code reaches the tables

`aidb.session.tenant_session(engine, tenant_id)` is how application code gets a tenant's connection. The exceptions are deliberate and listed: the worker's `PgTenantDirectory.tenant_ids()` opens a plain connection to call `aidb_list_tenant_ids()` (it needs no tenant, and the function returns ids only), and the owner-role code (migrations, `create_tenant`, the shared price writer, `purge_review_events`) never goes through it. `tenant_session` opens a transaction, sets `app.tenant_id` with `set_config(..., true)` (a bound parameter, transaction-local, so nothing leaks into the next use of a pooled connection), and checks in the same round trip that the role cannot bypass RLS.

| In memory (tests, `demo_api.py`) | PostgreSQL |
|---|---|
| `components.core.store` tenant stores | `aidb.repositories.PgStore`, `PgTenantStore`, `PgRepo` (generic `data jsonb` rows) |
| `EventLog` | `PgEventStore` |
| In-memory approval, cap, kill-switch, follow-up and idempotency stores | `aidb.state.PgSharedState`: `PgSpentApprovals`, `PgTokenStore`, `PgCapLedger`, `PgSpendBook`, `PgFollowUpPlans`, `PgKillSwitch`, `PgIdempotencyStore` |
| Quote-engine stores | `aidb.stage2`: `PgOfferStore`, `PgApprovedMatchStore`, `PgImportStore`, `PgTemplateStore`, `PgQuoteSnapshotStore` (wired by `apps/api/quote_pg.py`), and `PgSharedOfferWriter`, the owner-engine writer for the shared price table (used by `apps/api/quote_provision.py`) |
| `InMemoryPriceHistory` | `PgPriceHistory` |
| `InMemoryTelemetryStore` | `PgReviewEvents` |
| The purchasing service's stores | `employees/purchasing/pg_wiring.py`: `PgServiceStore` and `PgTenantFacade`, used by `build_pg_service` |

The Postgres stores satisfy the same `Protocol`s as the in-memory ones, so the services do not know which they have.

## Inspecting a database

`scripts/pg_dev.sh start` starts a throwaway local PostgreSQL 16 for tests and development (trust authentication, no Docker). By default it uses the binaries in `/usr/lib/postgresql/16/bin`, the data directory `/tmp/pg_dev_data` and port 54329; override them with `PG_BIN`, `PG_DATA` and `PG_PORT`, and `scripts/pg_dev.sh url` prints the URL. After migrations:

```sql
-- rows are invisible without a tenant
SELECT count(*) FROM requests;                                 -- 0 as app_user
SELECT set_config('app.tenant_id', 'demo-tenant-a', false);
SELECT id, state FROM requests ORDER BY created_at;

-- the chain as stored (SQL cannot tell you it is intact: GET /v1/audit and scripts/verify_audit_export.py recompute the keyed hashes)
SELECT seq, type, left(hash, 12) FROM events WHERE tenant_id = 'demo-tenant-a' ORDER BY seq;

-- which tables force RLS?
SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class
WHERE relkind = 'r' AND relnamespace = 'public'::regnamespace ORDER BY 1;
```

Connect as `app_user` to see what the application sees, and as the owner to administer. Recomputing a chain hash needs `AUDIT_CHAIN_KEY`, so use `scripts/verify_audit_export.py` on an export rather than SQL.
