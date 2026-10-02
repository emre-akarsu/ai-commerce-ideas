#!/usr/bin/env bash
# Starts a throwaway local Postgres 16 for tests (sandbox/dev). Usage: scripts/pg_dev.sh start|stop|url
set -euo pipefail
BIN=${PG_BIN:-/usr/lib/postgresql/16/bin}
DATA=${PG_DATA:-/tmp/pg_dev_data}
PORT=${PG_PORT:-54329}
RUN="runuser -u postgres --"
if [ "$(id -u)" != "0" ]; then RUN=""; fi
case "${1:-url}" in
  start)
    if [ ! -d "$DATA" ]; then
      mkdir -p "$DATA"; [ -n "$RUN" ] && chown postgres "$DATA"
      $RUN "$BIN/initdb" -D "$DATA" -A trust -U postgres >/dev/null
    fi
    $RUN "$BIN/pg_ctl" -D "$DATA" -o "-p $PORT -k /tmp -c listen_addresses=127.0.0.1" -l "$DATA/log" -w start >/dev/null
    ;;
  stop) $RUN "$BIN/pg_ctl" -D "$DATA" -m fast stop >/dev/null ;;
  url) ;;
esac
echo "postgresql://postgres@127.0.0.1:$PORT/postgres"
