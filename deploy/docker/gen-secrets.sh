#!/usr/bin/env bash
# Writes .env with generated secrets (never committed; .gitignore covers it). Prints the access
# password once. Run it on the VPS, in this directory. Needs docker.
set -euo pipefail
cd "$(dirname "$0")"
[ -f .env ] && { echo ".env exists; delete it to regenerate (this would NOT change an existing database password)"; exit 1; }
rnd() { head -c 24 /dev/urandom | base64 | tr -d '/+=' | head -c 24; }
ACCESS="$(rnd)"
HASH="$(docker run --rm caddy:2-alpine caddy hash-password --plaintext "$ACCESS")"
umask 077
cat > .env <<EOF
OWNER_DB_PASSWORD=$(rnd)
APP_DB_PASSWORD=$(rnd)
ACCESS_USER=rfq
ACCESS_PASSWORD_HASH='$HASH'
# A domain name here gets an automatic certificate; ":80" is plain HTTP (use an SSH tunnel).
SITE_ADDRESS=:80
EOF
mkdir -p www backup
echo "Access: user rfq, password $ACCESS  (shown once; store it in a password manager)"
