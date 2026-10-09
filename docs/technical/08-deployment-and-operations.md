# Deployment and operations

**Nothing in this repository is a production deployment.** The API refuses `ENV=production` on purpose (six items in `REMAINING_H2`, see [system overview](01-system-overview.md#runtime-modes)). The setups below are for development, demonstration and staging with synthetic data. No customer or supplier data should be put on them.

## Ways to run it

| Way | What you get | Needs |
|---|---|---|
| `make demo-api` (`scripts/demo_api.py`) | The **in-memory** API on `127.0.0.1:8000`: test authentication, the UK profile with a synthetic company identity, a recording transport, a fake model, CORS for `http://localhost:3000`, seeded tenant, suppliers and requests. It prints one development token per role. State is lost on exit. | Python 3.11 or later and `make setup` |
| The web app against it | `cd apps/web && APP_ENV=dev NEXT_PUBLIC_API_URL=http://localhost:8000 NEXT_PUBLIC_DEV_TOKEN=<token> npx next dev -p 3000`. | Node (22 was used here; `package.json` declares no `engines`) |
| The web demo build | A single `page.html` with synthetic data and no server: `cd apps/web && npx vite build -c demo/vite.config.mjs && node demo/inline.mjs` writes `demo-dist/page.html`. This is what the screenshots in the [user guide](../user-guide/README.md) show. | Node |
| `scripts/run_local.sh` | PostgreSQL 16 in Docker, migrations, the synthetic demo tenants and prices, the shipped `apps.api.asgi:app` on `:8000`, and the web app on `:3000` signed in as the buyer of `demo-tenant-a`. | Docker, Python, Node |
| `deploy/docker/compose.yaml` | The staging demo on one VPS, below. | Docker on a Linux host |
| `deploy/gcp-free-tier` | The same demo on one Google Cloud `e2-micro`, without Docker, below. | `gcloud` |
| `scripts/pg_dev.sh` | A throwaway local PostgreSQL 16 for the database tests, with no Docker. | PostgreSQL 16 binaries |

The shipped entrypoint `apps.api.asgi:app` builds its service with no deployment settings, so on the `uk` profile it **cannot prepare a message** (company details are missing) and its only approver is `user:approver-1`. `scripts/run_local.sh` is therefore good for the quote engine, suppliers and requests up to choosing suppliers, not for the full approve-and-send path. For that, use `make demo-api`, or write an entrypoint that passes `Settings` (see [configuration](07-configuration.md#deployment-settings)).

## Docker Compose on one VPS

`deploy/docker/compose.yaml`. Only Caddy publishes ports (80 and 443). The API and database are on an internal network.

| Service | Image | What it does |
|---|---|---|
| `db` | `postgres:16-alpine` | The database `rfq`, owner `rfq_owner`. Tuned for 1 GB (`max_connections=30`, `shared_buffers` 128 MB). Durability stays on. Memory cap 512 MB. |
| `migrate` | the API image | One-shot. Runs the migrations as `rfq_owner`. This also creates the restricted `app_user` role. |
| `dbinit` | `postgres:16-alpine` | One-shot. Gives `app_user` its password. |
| `provision` | the API image | One-shot, idempotent. Creates `demo-tenant-a` and `demo-tenant-b` and loads the synthetic price files (`scripts/provision_demo_tenant.py`). Remove it and `QUOTE_DEMO_DATA` for anything that is not a demo. |
| `api` | the API image | `uvicorn apps.api.asgi:app`, as `app_user`, `DEPLOYMENT_PROFILE=uk`, `ENV=staging`, `QUOTE_DEMO_DATA=1`. Read-only root filesystem, a `tmpfs` for `/tmp`, all capabilities dropped, `no-new-privileges`, memory cap 384 MB. |
| `caddy` | `caddy:2-alpine` | TLS (automatic only when `SITE_ADDRESS` is a domain; the default `:80` is plain HTTP, to be reached through an SSH tunnel), **basic auth on the whole site** (the demo has test logins; never remove it), security headers, `/api/*` proxied to `api:8000`, everything else served from `www/` with a fallback to `index.html`. |
| `backup` | `postgres:16-alpine` | A `pg_dump` at start and every 24 hours into `./backup`, then `find -mtime +7 -delete`, which removes dumps older than seven full days, so about eight daily dumps are kept. |

Start order is enforced: database healthy, then `migrate`, `dbinit`, `provision`, `api`, `caddy`.

```text
cd deploy/docker
./gen-secrets.sh            # writes .env (uncommitted): DB passwords, AUDIT_CHAIN_KEY, APPROVAL_SECRET, the access password hash
cp ../../apps/web/demo-dist/page.html www/index.html
docker compose up -d --build
```

Set `SITE_ADDRESS=your.domain` in `.env` once DNS points at the server and Caddy gets a certificate on its own. Token verification needs `SUPABASE_JWT_SECRET` or `SUPABASE_JWKS_URL` in `.env` (the default `AUTH_MODE` is `supabase`). Update with `git pull && docker compose up -d --build`; a page update is a file copy into `www/`.

**Status, as the file itself says:** it was validated with `docker compose config` and the shell scripts with `bash -n`. The sandbox it was written in has the Docker client but no daemon, so the image was never built and the stack was never started there. Expect first-run problems and fix them. Also note:

- **The image build needs a `src` directory.** `deploy/docker/Dockerfile` has `COPY src ./src`, but git tracks nothing under `src/` (it is an empty directory left by the first scaffold, and git does not store empty directories), so a build from a fresh clone has no `src` and that step should fail. Create an empty one first with `mkdir src`. This is read from the Dockerfile and `git ls-files src`; it was not run, because no Docker daemon was available (see [known gaps](../architecture/known-gaps.md#found-while-writing-the-documentation-2026-10-09), row 39).
- The page it serves is the **demo build** (mock data in the browser). It does not call the API. The compose stack therefore demonstrates the API's health, the database and the proxy, not the web app against real data.
- A comment at the top of the file still says the purchasing service's request store is in memory. That is out of date: with `DATABASE_URL` the purchasing stores are Postgres rows (`build_pg_service`).
- The worker is not in the compose file.

## Google Cloud free-tier VM

`deploy/gcp-free-tier`: scripts for a single `e2-micro` in one of the three free regions, **password-protected, synthetic data only**. No Docker and no Next.js server on the VM (1 GB of memory and a shared quarter vCPU).

1. `PROJECT=<id> ./create-vm.sh` creates the VM (it refuses zones outside the free regions). Its startup script installs Caddy, adds 2 GB of swap and generates the access password into `/root/rfq-access-password.txt`.
2. `PROJECT=<id> ./deploy.sh <page.html>` copies the demo page, the Caddyfile and the backup script.
3. Reach it with `gcloud compute ssh rfq-free -- -L 8080:localhost:80`, which needs no firewall rule and no domain. To serve it publicly, point a domain at the VM, open only 80 and 443, set `SITE_ADDRESS` in `/etc/rfq/site.env` and restart Caddy (it reads the file only when it starts).
4. Optional API: copy the repository to `/srv/rfq/app`, make a virtualenv in `/srv/rfq/venv`, `pip install -e .`, and install `rfq-api.service`. The unit runs **`scripts/demo_api.py`**, the in-memory demo, with `MemoryMax=300M`, `ProtectSystem=strict`, `NoNewPrivileges` and `PrivateTmp`. State is lost on restart.
5. Optional database: `./postgres-setup.sh` installs PostgreSQL tuned for 1 GB and listening on localhost only, creates the owner role (`rfq_owner`, `NOSUPERUSER NOBYPASSRLS`, and so unable to create roles) and `rfq`, and saves credentials to `/etc/rfq/db.env`. **As the repository stands, the migrations then fail.** The first migration creates the `app_user` role and the owner may not (`permission denied to create role`; reproduced on a fresh PostgreSQL 16). Create the role once as the superuser before migrating, for example `sudo -u postgres psql -c "CREATE ROLE app_user LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE"`; the migrations then pass (checked: all seven, as a role without `CREATEROLE`). Then run the migrations as the owner, and `./postgres-setup.sh app-password` for the `app_user` password. The GCP README says the migration creates `app_user`, which is true only when the migrating role can create roles, as in the compose stack. This is row 20 of [known gaps](../architecture/known-gaps.md#found-while-writing-the-documentation-2026-10-09).

Rules it follows: never open ports 8000 or 5432, keep basic auth on, and put no secret in the repository. The README lists the free-tier limits (one `e2-micro` per month in `us-west1`, `us-central1` or `us-east1`, 30 GB standard disk, 1 GB egress). Those figures came from a web search and should be confirmed on Google's page.

## Database operations

- **Roles.** Migrations and provisioning run as the owner. The application and the worker run as `app_user`, which has `NOSUPERUSER NOBYPASSRLS`. A superuser or a role with `BYPASSRLS` ignores row-level security, and `tenant_session` refuses to run on such a connection. The compose owner is a superuser (the official PostgreSQL image makes `POSTGRES_USER` one). The free-tier VM's `rfq_owner` is an ordinary role: every tenant table uses `FORCE ROW LEVEL SECURITY`, so the policies still apply to it, and `tenant_session` would not refuse it. The application must connect as `app_user` either way. Tenant creation (`aidb.migrate.create_tenant`, which `scripts/provision_demo_tenant.py` uses) works with the compose owner and fails on the free-tier VM with `new row violates row-level security policy for table "tenants"`, because the owner is an ordinary role there; create tenants as the `postgres` superuser on that VM.
- **Migrate:** `python -c "from aidb.migrate import upgrade; upgrade('<owner url>')"`.
- **Backups:** the compose `backup` service dumps `rfq` in custom format (`pg_dump -Fc`) daily. Copy the dumps off the server and **test a restore** (`pg_restore`) before any real data. This has not been tested.
- **Tenants:** `scripts/provision_demo_tenant.py` is the only provisioning path, and it is for the demo. There is no tenant-creation endpoint or screen.
- **Retention:** `retention.*` is in the profile, and the worker has `purge_expired_raw_email`, but no retention job runs in any deployment here. `purge_review_events` (`aidb.telemetry`) deletes review events older than a cutoff, but nothing calls it, and it refuses any role that is neither a superuser nor has `BYPASSRLS`, so it works with the compose owner and not with the free-tier VM's `rfq_owner`.

## Keys and rotation

| Key | If it changes |
|---|---|
| `AUDIT_CHAIN_KEY` | There is no key version in the chain, so every existing chain fails verification. Treat it as fixed for the life of the data. |
| `APPROVAL_SECRET` | Outstanding approval links and reply tokens stop verifying. A reply to a message that is already out can no longer be matched. |
| `INBOUND_WEBHOOK_SECRET` | Change it together with the provider's configuration. |
| `app_user` password | `ALTER ROLE app_user PASSWORD ...` and update `DATABASE_URL` for the API and worker. |
| `SUPABASE_JWT_SECRET` | Existing tokens stop verifying. |

The API and the worker must share `AUDIT_CHAIN_KEY` and `AUDIT_PII_KEY` (the worker's own start-up notes say so). Set `AUDIT_PII_KEY` explicitly in both: when it is unset the API derives it from the chain key, but the worker does not, so it would use a random key (and `ENV=production` makes it refuse to start), and the personal-data digests it writes would not match the API's. The worker does not read `APPROVAL_SECRET`.

## Health and logs

- `GET /healthz` answers `{"status": "ok"}` without authentication, from the API process. It does not check the database. In the compose stack Caddy proxies only `/api/*`, so the path is `/api/healthz`, behind the site's basic auth, and nothing in the stack calls it (the `api` service has no health check).
- Logging is Python's standard `logging`. An unhandled error is logged by the application as its exception type only, and the client gets a generic `500`, but that is not the whole log: Starlette re-raises after sending the `500`, and `uvicorn` (the compose command) then logs `Exception in ASGI application` with the **full traceback, including the exception message**, which can contain submitted values. The application's own comment says it logs no trace; under `uvicorn` that does not hold (row 21 of [known gaps](../architecture/known-gaps.md#found-while-writing-the-documentation-2026-10-09)). There is no structured logging, tracing, metrics or error-reporting service in the code.
- With `DATABASE_URL` set, start-up requires `AUDIT_CHAIN_KEY` and `APPROVAL_SECRET` (at least 16 characters each; otherwise it stops with a `RuntimeError`), and an unset `AUDIT_PII_KEY` is derived from the chain key. Without `DATABASE_URL` (the in-memory build) a keyless audit log logs a warning and uses an ephemeral key, which `ENV=production` refuses.
- `scripts/check_production_readiness.py` prints nine checks as PASS or FAIL by reading the source (no network, no database). Two pass today (purchasing stores in Postgres, the per-tenant kill switch) and seven fail, which cover the six `REMAINING_H2` items (the prepared-message cache and the approval-link notifier are checked separately). It exits 1 while anything fails. A PASS means the code has the property, not that the system is production ready.
- The worker task `worker.verify_audit_chain` re-verifies each tenant's chain. The worker is not deployed here.

## What operating this would need

These are not built. [Known gaps](../architecture/known-gaps.md) tracks most of them; a restore test and a continuous-integration pipeline are not tracked there:

- A real mail transport and an inbound mail provider, with SPF, DKIM and DMARC reported for each reply.
- Delivery of approval links to the approvers.
- A web sign-in, and a way to set the approver list, company details and buyer names without code.
- The worker deployed, with its inbound source and send-service factory wired (known gaps covers the factory; `apps/worker/worker_main.py` notes that the deployment must supply the inbound source).
- The six `REMAINING_H2` items closed, a restore test, and a continuous-integration pipeline (none is configured in the repository).
