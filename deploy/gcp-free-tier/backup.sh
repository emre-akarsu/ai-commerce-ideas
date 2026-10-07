#!/usr/bin/env bash
# Nightly: copy the deployed demo page and any SQLite file to /srv/rfq/backup, keep 7 days. This
# stays on the 30 GB boot disk; for real data add an off-VM copy (egress is limited to 1 GB/month).
set -euo pipefail
d=/srv/rfq/backup/$(date +%F); mkdir -p "$d"
cp -a /srv/rfq/www "$d/www"
for f in /srv/rfq/data/*.db; do [ -e "$f" ] && sqlite3 "$f" ".backup '$d/$(basename "$f")'"; done
find /srv/rfq/backup -mindepth 1 -maxdepth 1 -type d -mtime +7 -exec rm -rf {} +
