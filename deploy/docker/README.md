# One VPS with Docker (Hetzner, Google, any Linux host)

Caddy (HTTPS and a password), the API, PostgreSQL and a nightly backup in one `compose.yaml`. Only Caddy publishes ports (80 and 443); the API and database are on an internal network. This is provider-neutral: the Google Always Free notes are in `../gcp-free-tier/` (no Docker there, because 1 GB of RAM is too little for it).

**Status, honestly.** I validated `compose.yaml` with `docker compose config` and the shell with `bash -n`. This sandbox has the Docker client but no running Docker daemon, so I have **not built the image, started the stack or run the migrations**. Treat the first run as a test on a throwaway server. The API service runs `uvicorn apps.api.asgi:app` on Postgres as `app_user` (quotes, templates, approved matches, events and the shared security state are in the database); a one-shot `provision` step loads the **synthetic** demo tenants and price files (`QUOTE_DEMO_DATA=1`; fictional merchants, invented prices). Nothing is sent and the entrypoint still refuses `ENV=production` (known-gaps H2). `.env` also needs `AUDIT_CHAIN_KEY` and `APPROVAL_SECRET` (`gen-secrets.sh` writes them) and a token key (`SUPABASE_JWT_SECRET` or `SUPABASE_JWKS_URL`). Not yet run on a real server.

## Sizing and price (from web search; check the provider's page, Hetzner raised prices twice in 2026)
Per [recent pricing roundups](https://www.vpsbenchmarks.com/hosters/hetzner/plans/cax11), Hetzner's small shared plans are about 2 vCPU, 4 GB RAM, 40 GB disk for roughly 4 to 6 euro a month (CX23 x86, CAX11 ARM), plus about 0.50 euro a month for an IPv4 address, with 20 TB of traffic included in the EU (US locations include much less). The stack here needs about 1 GB, so the smallest plan with 2 GB or more is plenty; you can run `PG_SHARED_BUFFERS=256MB PG_CACHE=1GB` on 4 GB. All images are multi-architecture, so ARM plans work. Choose an EU location for UK or EU customer data. Compare Hetzner's current price list before ordering.

## Steps (run on the server)
1. Create the server (Debian 12 or Ubuntu 24.04), add your SSH key, disable password login, and install Docker (`curl -fsSL https://get.docker.com | sh`). Enable the firewall: allow 22, 80, 443 only (`ufw allow 22,80,443/tcp && ufw enable`), plus `unattended-upgrades`. Never open 5432 or 8000 (the compose file does not publish them).
2. `git clone` the repo, then `cd deploy/docker`.
3. Build the demo page on your own machine (`cd apps/web && npx vite build -c demo/vite.config.mjs && node demo/inline.mjs`) and copy `apps/web/demo-dist/page.html` to `deploy/docker/www/index.html` on the server.
4. `./gen-secrets.sh` writes `.env` (generated database and access passwords; never committed) and prints the access password once. Set `SITE_ADDRESS=your.domain` in `.env` once a DNS record points at the server, so Caddy gets a certificate; the default `:80` is plain HTTP, use it only through an SSH tunnel (`ssh -L 8080:localhost:80`).
5. `docker compose up -d --build`. Order is enforced: database healthy, migrations run as `rfq_owner` (which create the restricted `app_user`), `dbinit` sets `app_user`'s password, then the API starts as `app_user`. Check `docker compose ps` and `docker compose logs migrate`.
6. Backups land in `./backup` (a dump at start, then every 24 hours, 7 days kept). Copy them off the server regularly and test a restore (`pg_restore`) before any real data.

## Rules
- The app connects as `app_user` only; row-level security does not protect against the owner role. Run the repo's cross-tenant tests against this database before real data.
- The site is behind basic auth because the demo has test logins. Do not remove it.
- No customer or merchant data until Stage 1 closes known-gaps H2 and the restore test passes.
- Update: `git pull && docker compose up -d --build`; page updates are a file copy to `www/`.
