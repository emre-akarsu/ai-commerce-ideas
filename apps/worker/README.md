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

## Building the send-service for `send_service_factory`
`send_service_factory(tenant_id)` must return a `SendService` built **from the deployment profile**, not with the bare
constructor. (The send-service is the only holder of the transport, as everywhere else; the worker's own code never
touches it.)

```python
from components.send_service import SendService
from components.send_service.service import TenantIdentities

send = SendService.from_profile(
    profile, transport, clock, store, event_log,        # the deployment's own objects (same store and log as the API)
    caps=caps, kill_switch=kill_switch,
    identity_provider=TenantIdentities({...}),          # only when the profile lists business-identity fields
)
```

`SendService.from_profile` takes the R8 footer wording, the recipient limit (`comms.max_vendors`) and, when the profile
sets `legal.business_identity.required`, the required identity labels from the profile (`required_identity_labels` can
only add to them). The constructor's `required_identity_labels` defaults to `()`, which requires nothing: a service built
with `SendService(...)` has no send-time identity backstop and uses the generic footer, and nothing downstream notices.
Follow-ups copy the identity lines of the original message, so the worker never needs the tenants' values; the provider
is for `prepare`. The API process builds its service the same way (`build_in_memory_service`).

## Tasks (`tasks.py`)
| task | schedule (UTC) |
|---|---|
| `worker.parse_inbound_message(tenant_id, message_ref)` | on demand (inbound webhook) |
| `worker.run_follow_ups(tenant_id)` | every 15 min via `fan_out_follow_ups` |
| `worker.verify_audit_chain(tenant_id)` | 02:30 daily via `fan_out_verify_audit_chain`; records `audit.chain_verified` / `audit.chain_invalid` |
| `worker.meter_usage_rollup(tenant_id)` | hourly via `fan_out_meter_usage_rollup` (stub) |

Periodic tasks are fan-outs: they list tenants from `WorkerContext.tenant_directory`, which `worker_main` backs with the SECURITY DEFINER function `aidb_list_tenant_ids()` (migration 0002) over the same `app_user` connection (ids only; no RLS-bypassing credential) and defer one per-tenant job
(with a queueing lock, so a slow run is not piled up).

## Run locally
```
export PYTHONPATH=packages:.
export PROCRASTINATE_DATABASE_URL=postgresql://...      # queue schema (procrastinate_* tables)
export DATABASE_URL=postgresql://app_user@.../db        # tenant data: MUST be app_user
export AUDIT_PII_KEY=... AUDIT_CHAIN_KEY=...            # >=16 chars, same values as the API; required when ENV=production
python -c "import procrastinate,psycopg; from procrastinate import schema; \
  psycopg.connect('$PROCRASTINATE_DATABASE_URL', autocommit=True, client_encoding='utf8')\
  .execute(schema.SchemaManager.get_schema())"          # once per database
python -m apps.worker.worker_main
```
`inbound_source` and `send_service_factory` are NOT wired in `worker_main.py` (no inbound storage or send-service deployment exists in this repo): `parse_inbound_message` and `run_follow_ups` raise a clear error when they run under it. Wire both before relying on those tasks.
Without `AUDIT_PII_KEY`/`AUDIT_CHAIN_KEY` a non-production process uses ephemeral keys (warning logged) and its audit chains will not verify elsewhere; with `ENV=production` startup fails.
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
      - key: AUDIT_PII_KEY
        sync: false
      - key: AUDIT_CHAIN_KEY
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
