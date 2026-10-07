#!/usr/bin/env bash
# Idempotent first-boot setup for a 1 GB e2-micro (Debian 12): swap, Caddy, the app user, a nightly
# backup timer. It generates the access password itself and prints where it saved it; no secret is
# stored in the repo. Safe to run again.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

# 1. Swap: 1 GB of RAM is too little for apt, builds and Postgres together.
if ! swapon --show | grep -q /swapfile; then
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  grep -q /swapfile /etc/fstab || echo "/swapfile none swap sw 0 0" >> /etc/fstab
  sysctl -w vm.swappiness=20 >/dev/null; echo "vm.swappiness=20" > /etc/sysctl.d/99-swap.conf
fi

# 2. Packages (Caddy from its Debian repo; Python for the optional API).
apt-get update -y
apt-get install -y --no-install-recommends debian-keyring debian-archive-keyring apt-transport-https curl gpg ca-certificates python3 python3-venv git sqlite3
if ! command -v caddy >/dev/null; then
  curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/gpg.key | gpg --dearmor -o /usr/share/keyrings/caddy.gpg
  echo "deb [signed-by=/usr/share/keyrings/caddy.gpg] https://dl.cloudsmith.io/public/caddy/stable/deb/debian any-version main" > /etc/apt/sources.list.d/caddy.list
  apt-get update -y && apt-get install -y caddy
fi

# 3. App user and directories. The web demo is one static file served by Caddy.
id rfq >/dev/null 2>&1 || useradd --system --create-home --shell /usr/sbin/nologin rfq
install -d -o rfq -g rfq /srv/rfq/www /srv/rfq/backup
install -d -m 750 -o root -g caddy /etc/rfq

# 4. Access password for the whole site (the demo has test logins, so it must never be open).
if [ ! -f /etc/rfq/access.env ]; then
  PASS="$(head -c 18 /dev/urandom | base64 | tr -d '/+=' | head -c 20)"
  HASH="$(caddy hash-password --plaintext "$PASS")"
  printf 'ACCESS_USER=rfq\nACCESS_PASSWORD_HASH=%s\n' "$HASH" > /etc/rfq/access.env
  printf 'rfq / %s\n' "$PASS" > /root/rfq-access-password.txt && chmod 600 /root/rfq-access-password.txt
  chgrp caddy /etc/rfq/access.env && chmod 640 /etc/rfq/access.env
  echo "Access password saved to /root/rfq-access-password.txt (user: rfq). Read it over SSH, then delete the file."
fi

# 5. Caddy config and service environment (see README for SITE_ADDRESS).
[ -s /etc/rfq/site.env ] || { echo 'SITE_ADDRESS=:80' > /etc/rfq/site.env; chgrp caddy /etc/rfq/site.env; chmod 640 /etc/rfq/site.env; }
mkdir -p /etc/systemd/system/caddy.service.d
printf '[Service]\nEnvironmentFile=/etc/rfq/access.env\nEnvironmentFile=/etc/rfq/site.env\n' > /etc/systemd/system/caddy.service.d/rfq.conf
echo "Copy Caddyfile to /etc/caddy/Caddyfile and page.html to /srv/rfq/www/index.html (see README), then: systemctl daemon-reload && systemctl restart caddy"

# 6. Nightly backup timer (the script is copied by deploy.sh or by hand to /usr/local/bin/rfq-backup).
cat > /etc/systemd/system/rfq-backup.service <<'U'
[Unit]
Description=RFQ nightly backup
[Service]
Type=oneshot
ExecStart=/usr/local/bin/rfq-backup
U
cat > /etc/systemd/system/rfq-backup.timer <<'U'
[Unit]
Description=RFQ nightly backup
[Timer]
OnCalendar=*-*-* 03:17:00
Persistent=true
[Install]
WantedBy=timers.target
U
systemctl daemon-reload && systemctl enable --now rfq-backup.timer
