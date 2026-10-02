# apps/worker

Procrastinate (Postgres-backed) background worker. Documentation only for deployment: nothing here is deployed.

## Rules it enforces (stack-map S2)
- Every per-tenant task takes `tenant_id` (set by the platform when the job is deferred) and runs inside
  `aidb.session.tenant_session`: the `app_user` role (NOBYPASSRLS) plus transaction-local `app.tenant_id`.
  A superuser/BYPASSRLS connection is refused (`PrivilegedRoleError`); a missing or unknown tenant raises
  `TenantContextError` and the task does nothing. There is no service-role path.
- The worker never sends mail. `run_follow_ups` calls the send-service's pre-approved follow-up runner through
  an injected `send_service_factory(tenant_id)`; the service refuses anything without a registered approval.
  Caveat: `SendService.run_due_follow_ups()` takes no tenant argument, so the factory must return a runner
  scoped to that tenant (or the service must gain a tenant filter).
- Document content is parsed by `components.doc_parse` (inert text only); audit payloads carry hashes/flags/counts, never text.

## Tasks (`tasks.py`)
| task | schedule (UTC) |
|---|---|
| `worker.parse_inbound_message(tenant_id, message_ref)` | on demand (inbound webhook) |
| `worker.run_follow_ups(tenant_id)` | every 15 min via `fan_out_follow_ups` |
| `worker.verify_audit_chain(tenant_id)` | 02:30 daily via `fan_out_verify_audit_chain`; records `audit.chain_verified` / `audit.chain_invalid` |
| `worker.meter_usage_rollup(tenant_id)` | hourly via `fan_out_meter_usage_rollup` (stub) |

Periodic tasks are fan-outs: they list tenants from `WorkerContext.tenant_directory` and defer one per-tenant job
(with a queueing lock, so a slow run is not piled up).

## Run locally
```
export PYTHONPATH=packages:.
export PROCRASTINATE_DATABASE_URL=postgresql://...      # queue schema (procrastinate_* tables)
export DATABASE_URL=postgresql://app_user@.../db        # tenant data: MUST be app_user
export TENANT_DIRECTORY_URL=postgresql://...            # role that may SELECT tenants.id (fan-out only)
python -c "import procrastinate,psycopg; from procrastinate import schema; \
  psycopg.connect('$PROCRASTINATE_DATABASE_URL', autocommit=True, client_encoding='utf8')\
  .execute(schema.SchemaManager.get_schema())"          # once per database
python -m apps.worker.worker_main
```
`inbound_source` and `send_service_factory` are not wired in `worker_main.py` yet; tasks that need them fail loudly.
Tests: `make test` (real Postgres via `scripts/pg_dev.sh start`; skipped with a reason if unreachable).

## Render (`render.yaml` snippet, not deployed)
```yaml
services:
  - type: worker            # long-running Procrastinate worker (also runs the periodic fan-outs)
    name: purchasing-worker
    runtime: python
    buildCommand: pip install -e .
    startCommand: PYTHONPATH=packages:. python -m apps.worker.worker_main
    envVars:
      - key: PROCRASTINATE_DATABASE_URL
        sync: false
      - key: DATABASE_URL            # app_user role only
        sync: false
      - key: TENANT_DIRECTORY_URL
        sync: false
  # Alternative to Procrastinate periodic tasks: one Render cron per schedule that defers the fan-out job.
  - type: cron
    name: purchasing-followups-cron
    runtime: python
    schedule: "*/15 * * * *"
    buildCommand: pip install -e .
    startCommand: PYTHONPATH=packages:. python -m procrastinate --app=apps.worker.worker_main.app defer worker.fan_out_follow_ups
```
Use either the periodic tasks (worker service) or the cron services, not both. The cron variant needs a module-level
`app` in `worker_main` (not provided yet); the parsing sandbox (S4) is a separate isolated service and is not defined here.
