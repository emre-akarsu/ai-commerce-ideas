#!/usr/bin/env bash
# Run on YOUR machine after `make` builds the demo: pushes the single-file demo to the VM.
# Usage: PROJECT=... ZONE=... NAME=rfq-free ./deploy.sh path/to/apps/web/demo-dist/page.html
set -euo pipefail
: "${PROJECT:?}"; ZONE="${ZONE:-us-central1-a}"; NAME="${NAME:-rfq-free}"
PAGE="${1:?path to page.html}"; HERE="$(dirname "$0")"
gcloud compute scp --project "$PROJECT" --zone "$ZONE" "$PAGE" "$HERE/Caddyfile" "$HERE/backup.sh" "$NAME:/tmp/"
gcloud compute ssh --project "$PROJECT" --zone "$ZONE" "$NAME" --command \
 'sudo install -o rfq -g rfq -m 644 /tmp/page.html /srv/rfq/www/index.html && sudo install -m 644 /tmp/Caddyfile /etc/caddy/Caddyfile && sudo install -m 755 /tmp/backup.sh /usr/local/bin/rfq-backup && sudo systemctl daemon-reload && sudo systemctl restart caddy && systemctl is-active caddy'
