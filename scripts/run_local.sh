#!/usr/bin/env bash
# Runs the whole app on your machine: PostgreSQL (Docker), migrations, synthetic demo data, the API
# on :8000 and the web app on :3000 against it. SYNTHETIC DATA ONLY; nothing is sent or ordered.
# Needs: docker, python 3.11+, node 20+.   Usage: scripts/run_local.sh   (Ctrl+C stops the API and web;
# the database container keeps running, stop it with: docker rm -f rfq-local-pg)
set -euo pipefail
cd "$(dirname "$0")/.."
PGPORT="${PGPORT:-55432}"; DB=rfq_local
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -e ".[dev]"
if ! docker ps --format '{{.Names}}' | grep -qx rfq-local-pg; then
  docker rm -f rfq-local-pg >/dev/null 2>&1 || true
  docker run -d --name rfq-local-pg -e POSTGRES_PASSWORD=localowner -e POSTGRES_DB="$DB" \
    -p "127.0.0.1:$PGPORT:5432" postgres:16-alpine >/dev/null
fi
until docker exec rfq-local-pg pg_isready -U postgres -d "$DB" >/dev/null 2>&1; do sleep 1; done
export PYTHONPATH=packages:.
OWNER="postgresql://postgres:localowner@127.0.0.1:$PGPORT/$DB"
.venv/bin/python -c "from aidb.migrate import upgrade; upgrade('$OWNER'); print('migrated')"
docker exec rfq-local-pg psql -U postgres -d "$DB" -qc "ALTER ROLE app_user PASSWORD 'localapp'"
SECRET="local-test-secret-local-test-secret-123456"
export ENV=dev AUTH_MODE=test TEST_AUTH_SECRET="$SECRET" DEPLOYMENT_PROFILE=uk QUOTE_DEMO_DATA=1
export DATABASE_URL="postgresql://app_user:localapp@127.0.0.1:$PGPORT/$DB" OWNER_DATABASE_URL="$OWNER"
export AUDIT_CHAIN_KEY=local-audit-chain-key-0123456789 APPROVAL_SECRET=local-approval-secret-0123456789
export CORS_ORIGINS=http://localhost:3000
.venv/bin/python scripts/provision_demo_tenant.py
TOKEN="$(.venv/bin/python -c "
from apps.api.auth import make_test_token
print(make_test_token('$SECRET', sub='buyer-1', tenant_id='demo-tenant-a', role='buyer', ttl=86400))")"
(cd apps/web && [ -d node_modules ] || npm ci)
.venv/bin/python -m uvicorn apps.api.asgi:app --host 127.0.0.1 --port 8000 --log-level warning &
API=$!; trap 'kill $API 2>/dev/null || true' EXIT
echo "API http://localhost:8000   web http://localhost:3000 (signed in as buyer of demo-tenant-a)"
cd apps/web
APP_ENV=dev NEXT_PUBLIC_API_URL=http://localhost:8000 NEXT_PUBLIC_DEV_TOKEN="$TOKEN" npx next dev -p 3000
