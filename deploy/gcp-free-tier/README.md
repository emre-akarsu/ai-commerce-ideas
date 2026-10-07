# Run the demo on Google Cloud's Always Free VM

What this is: a **password-protected staging copy of the demo** (synthetic data, nothing is sent) on one `e2-micro` VM. What it is not: a production deployment. The shipped API keeps approvals, caps and the kill switch in process memory and refuses `ENV=production` (`docs/architecture/known-gaps.md` H2), so real customer data and real sending must wait for Stage 1 of `docs/product/10-roadmap-to-functional-app.md`. These scripts were checked with `bash -n` only; I could not create or test a VM, so run them on a throwaway VM first.

## Free tier facts and what still costs money
Source: [Google Cloud Free Tier, compute](https://cloud.google.com/free/docs/free-cloud-features#compute); the figures below come from a web search, so confirm them on that page before you rely on them.

- One non-preemptible `e2-micro` per month, only in `us-west1`, `us-central1` or `us-east1`; 30 GB-months of standard persistent disk; 1 GB per month of egress from North America (excluding China and Australia).
- Not free: an external IPv4 address (expect a few dollars a month; check your billing page), a bigger or SSD disk, snapshots beyond the allowance, egress beyond 1 GB. A billing account is required. Set a budget alert at a low amount before creating anything.
- 1 GB RAM and a shared 0.25 vCPU: no Docker, no Next.js server, no builds on the VM. Build the demo elsewhere and copy the single file. The scripts add 2 GB of swap.

## Memory budget (approximate, measure it)
Caddy about 30 MB; optional demo API about 150 to 250 MB (capped at 300 MB by the unit); Postgres (installed by `postgres-setup.sh`, tuned to `shared_buffers=64MB`, `max_connections=20`) about 150 MB. That fits in 1 GB with swap for a single user. Decision (owner, 2026-10-07): one VPS runs everything; no serverless or managed database. It will not serve many users; it is a staging box.

## Steps
1. Build the demo locally: `cd apps/web && npx vite build -c demo/vite.config.mjs && node demo/inline.mjs` (writes `demo-dist/page.html`).
2. In your own project: `PROJECT=<id> ./create-vm.sh` (refuses zones outside the three free regions). The startup script installs Caddy, adds swap, generates the access password and saves it to `/root/rfq-access-password.txt` on the VM (user `rfq`). Read it over SSH, then delete it.
3. `PROJECT=<id> ./deploy.sh ../../apps/web/demo-dist/page.html` copies the page and Caddyfile and restarts Caddy.
4. Reach it without exposing it: `gcloud compute ssh rfq-free -- -L 8080:localhost:80`, then open `http://localhost:8080` and sign in. This needs no firewall rule and no domain.
5. To serve it on the internet instead: point a domain at the VM, open only 80 and 443, set `SITE_ADDRESS=your.domain` in `/etc/rfq/site.env`, restart Caddy (it gets a certificate itself). The password prompt stays on for every path.

## Rules this setup follows
- Never open ports 8000 or 5432; the API and database listen on 127.0.0.1 only.
- The demo has test logins, so the whole site sits behind Caddy basic auth. Do not remove it.
- No secret is in the repo; the password is generated on the VM. No customer or merchant data goes on this box.
- Optional API: copy the repo to `/srv/rfq/app`, create `/srv/rfq/venv`, `pip install -e .`, install `rfq-api.service`. It is the in-memory demo and loses state on restart.

## Database on the same VM
1. As root on the VM: `./postgres-setup.sh` (installs PostgreSQL, tuned for 1 GB, localhost only, creates the owner role and the `rfq` database, saves credentials to `/etc/rfq/db.env`).
2. Run the migrations as the owner: `set -a; . /etc/rfq/db.env; set +a; cd /srv/rfq/app && /srv/rfq/venv/bin/python -c "from aidb.migrate import upgrade; import os; upgrade(os.environ['OWNER_DATABASE_URL'])"`. This also creates the restricted `app_user` role.
3. `./postgres-setup.sh app-password` gives `app_user` a password and writes `DATABASE_URL` for the app. The app must use `DATABASE_URL` (app_user), never the owner URL: row-level security does not protect against the owner.
4. Port 5432 stays closed to the internet (it listens on localhost only). The nightly backup now includes a `pg_dump` of `rfq`.
5. Before any real data: run the repo's cross-tenant tests against this database, test a restore from the dump, and keep an off-VM copy (mind the 1 GB monthly egress).

Still true: the shipped API entrypoint is the in-memory demo and refuses `ENV=production` until Stage 1 of the roadmap (database-backed service, known-gaps H2) is done. Move to a paid VM when a second user needs it or memory pressure shows in `free -m`.
