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
| `caddy` | `caddy:2-alpine` | TLS (automatic when `SITE_ADDRESS` is a domain), **basic auth on the whole site** (the demo has test logins; never remove it), security headers, `/api/*` proxied to `api:8000`, everything else served from `www/` with a fallback to `index.html`. |
| `backup` | `postgres:16-alpine` | A `pg_dump` at start and every 24 hours into `./backup`, keeping seven days. |

Start order is enforced: database healthy, then `migrate`, `dbinit`, `provision`, `api`, `caddy`.

```text
cd deploy/docker
./gen-secrets.sh            # writes .env (uncommitted): DB passwords, AUDIT_CHAIN_KEY, APPROVAL_SECRET, the access password hash
cp ../../apps/web/demo-dist/page.html www/index.html
docker compose up -d --build
```

Set `SITE_ADDRESS=your.domain` in `.env` once DNS points at the server and Caddy gets a certificate on its own. Token verification needs `SUPABASE_JWT_SECRET` or `SUPABASE_JWKS_URL` in `.env` (the default `AUTH_MODE` is `supabase`). Update with `git pull && docker compose up -d --build`; a page update is a file copy into `www/`.

**Status, as the file itself says:** it was validated with `docker compose config` and the shell scripts with `bash -n`. The sandbox it was written in has the Docker client but no daemon, so the image was never built and the stack was never started there. Expect first-run problems and fix them. Also note:

- The page it serves is the **demo build** (mock data in the browser). It does not call the API. The compose stack therefore demonstrates the API's health, the database and the proxy, not the web app against real data.
- A comment at the top of the file still says the purchasing service's request store is in memory. That is out of date: with `DATABASE_URL` the purchasing stores are Postgres rows (`build_pg_service`).
- The worker is not in the compose file.

## Google Cloud free-tier VM

`deploy/gcp-free-tier`: scripts for a single `e2-micro` in one of the three free regions, **password-protected, synthetic data only**. No Docker and no Next.js server on the VM (1 GB of memory and a shared quarter vCPU).

1. `PROJECT=<id> ./create-vm.sh` creates the VM (it refuses zones outside the free regions). Its startup script installs Caddy, adds 2 GB of swap and generates the access password into `/root/rfq-access-password.txt`.
2. `PROJECT=<id> ./deploy.sh <page.html>` copies the demo page, the Caddyfile and the backup script.
3. Reach it with `gcloud compute ssh rfq-free -- -L 8080:localhost:80`, which needs no firewall rule and no domain. To serve it publicly, point a domain at the VM, open only 80 and 443 and set `SITE_ADDRESS` in `/etc/rfq/site.env`.
4. Optional API: copy the repository to `/srv/rfq/app`, make a virtualenv in `/srv/rfq/venv`, `pip install -e .`, and install `rfq-api.service`. The unit runs **`scripts/demo_api.py`**, the in-memory demo, with `MemoryMax=300M`, `ProtectSystem=strict`, `NoNewPrivileges` and `PrivateTmp`. State is lost on restart.
5. Optional database: `./postgres-setup.sh` installs PostgreSQL tuned for 1 GB and listening on localhost only, creates the owner role and `rfq`, and saves credentials to `/etc/rfq/db.env`. Run the migrations as the owner, then `./postgres-setup.sh app-password` for the `app_user` password.

Rules it follows: never open ports 8000 or 5432, keep basic auth on, and put no secret in the repository. The README lists the free-tier limits (one `e2-micro` per month in `us-west1`, `us-central1` or `us-east1`, 30 GB standard disk, 1 GB egress). Those figures came from a web search and should be confirmed on Google's page.

## Database operations

- **Roles.** Migrations and provisioning run as the owner. The application and the worker run as `app_user`, which has `NOSUPERUSER NOBYPASSRLS`. A connection as the owner would bypass row-level security, and `tenant_session` refuses it.
- **Migrate:** `python -c "from aidb.migrate import upgrade; upgrade('<owner url>')"`.
- **Backups:** the compose `backup` service dumps `rfq` in custom format (`pg_dump -Fc`) daily. Copy the dumps off the server and **test a restore** (`pg_restore`) before any real data. This has not been tested.
- **Tenants:** `scripts/provision_demo_tenant.py` is the only provisioning path, and it is for the demo. There is no tenant-creation endpoint or screen.
- **Retention:** `retention.*` is in the profile, and the worker has `purge_expired_raw_email`, but no retention job runs in any deployment here. `review_events` have an owner-role purge function (`purge_review_events`).

## Keys and rotation

| Key | If it changes |
|---|---|
| `AUDIT_CHAIN_KEY` | There is no key version in the chain, so every existing chain fails verification. Treat it as fixed for the life of the data. |
| `APPROVAL_SECRET` | Outstanding approval links and reply tokens stop verifying. A reply to a message that is already out can no longer be matched. |
| `INBOUND_WEBHOOK_SECRET` | Change it together with the provider's configuration. |
| `app_user` password | `ALTER ROLE app_user PASSWORD ...` and update `DATABASE_URL` for the API and worker. |
| `SUPABASE_JWT_SECRET` | Existing tokens stop verifying. |

The API and the worker must share `AUDIT_CHAIN_KEY` and `APPROVAL_SECRET`.

## Health and logs

- `GET /healthz` answers `{"status": "ok"}` without authentication. It does not check the database.
- Logging is Python's standard `logging`. An unhandled error logs only the exception type, never a trace or a body, and the client gets a generic `500`. There is no structured logging, tracing, metrics or error-reporting service in the code.
- Start-up warns when `AUDIT_CHAIN_KEY` or `AUDIT_PII_KEY` is unset and an ephemeral key is used.
- `scripts/check_production_readiness.py` prints each `REMAINING_H2` item as PASS or FAIL by reading the source (no network, no database). It exits 1 while anything fails. A PASS means the code has the property, not that the system is production ready.
- The worker task `worker.verify_audit_chain` re-verifies each tenant's chain. The worker is not deployed here.

## What operating this would need

These are not built, and each is listed in [known gaps](../architecture/known-gaps.md):

- A real mail transport and an inbound mail provider, with SPF, DKIM and DMARC reported for each reply.
- Delivery of approval links to the approvers.
- A web sign-in, and a way to set the approver list, company details and buyer names without code.
- The worker deployed, with its inbound source and send-service factory wired.
- The six `REMAINING_H2` items closed, a restore test, and a continuous-integration pipeline (none is configured in the repository).
