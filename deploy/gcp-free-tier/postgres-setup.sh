#!/usr/bin/env bash
# One VPS for everything: installs PostgreSQL on the same e2-micro, tuned for 1 GB of RAM, listening
# on localhost only. Run as root on the VM after bootstrap.sh. Idempotent. No secret is stored in
# the repo: passwords are generated here and saved under /etc/rfq (root:rfq, mode 640).
#   1. creates the owner role (runs migrations) and the database;
#   2. you run the migrations (README), which create the restricted app_user role;
#   3. `./postgres-setup.sh app-password` then sets app_user's password and writes the app's URL.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
DB=rfq; OWNER=rfq_owner; ENVF=/etc/rfq/db.env

if [ "${1:-}" = "app-password" ]; then
  # Row-level security is only enforced for a role that is not the owner and cannot bypass it: the
  # app must connect as app_user, never as the owner. This sets its password once migrations ran.
  . "$ENVF"
  APP_PASS="$(head -c 24 /dev/urandom | base64 | tr -d '/+=' | head -c 24)"
  sudo -u postgres psql -v ON_ERROR_STOP=1 -d "$DB" -c "ALTER ROLE app_user PASSWORD '$APP_PASS'"
  grep -v '^DATABASE_URL=' "$ENVF" > "$ENVF.new" || true
  echo "DATABASE_URL=postgresql://app_user:$APP_PASS@127.0.0.1:5432/$DB" >> "$ENVF.new"
  mv "$ENVF.new" "$ENVF"; chgrp rfq "$ENVF"; chmod 640 "$ENVF"
  echo "app_user password set; DATABASE_URL written to $ENVF"; exit 0
fi

apt-get install -y --no-install-recommends postgresql postgresql-contrib
PGVER="$(ls /etc/postgresql | head -1)"
cat > "/etc/postgresql/$PGVER/main/conf.d/rfq-small.conf" <<'C'
# Sized for a 1 GB VM that also runs Caddy and the API. Measure with `free -m` and pg_stat_activity.
listen_addresses = 'localhost'
max_connections = 20
shared_buffers = 64MB
effective_cache_size = 256MB
work_mem = 2MB
maintenance_work_mem = 32MB
wal_buffers = 4MB
checkpoint_completion_target = 0.9
max_wal_size = 256MB
random_page_cost = 1.1
log_min_duration_statement = 500
# Durability stays on: approvals and the event chain must not be lost on a crash.
synchronous_commit = on
fsync = on
C
systemctl restart postgresql

if [ ! -f "$ENVF" ]; then
  OWNER_PASS="$(head -c 24 /dev/urandom | base64 | tr -d '/+=' | head -c 24)"
  sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
DO \$\$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='$OWNER') THEN
  CREATE ROLE $OWNER LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD '$OWNER_PASS'; END IF; END \$\$;
SELECT 'CREATE DATABASE $DB OWNER $OWNER' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname='$DB')\gexec
SQL
  printf 'OWNER_DATABASE_URL=postgresql://%s:%s@127.0.0.1:5432/%s\n' "$OWNER" "$OWNER_PASS" "$DB" > "$ENVF"
  chgrp rfq "$ENVF"; chmod 640 "$ENVF"
fi
echo "PostgreSQL ready on localhost. Next: run the migrations as the owner (README), then: ./postgres-setup.sh app-password"
