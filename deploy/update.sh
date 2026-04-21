#!/usr/bin/env bash
# Pull latest code and redeploy — run as root on the droplet.
# Usage: bash update.sh YOUR_DOMAIN.com

set -euo pipefail

DOMAIN="${1:-usewise.live}"
APP_DIR="/opt/usewise"

# Pull latest
sudo -u usewise git -C "$APP_DIR" pull

# Reinstall backend deps (no-op if unchanged)
sudo -u usewise bash -c "
    cd $APP_DIR/api
    .venv/bin/pip install -e . --quiet
"
systemctl restart usewise-api

# Rebuild frontend
sudo -u usewise bash -c "
    cd $APP_DIR/web
    VITE_API_URL=https://$DOMAIN/api npm ci --silent
    VITE_API_URL=https://$DOMAIN/api npm run build
"
rsync -a --delete "$APP_DIR/web/dist/" /var/www/usewise/
chown -R www-data:www-data /var/www/usewise

echo "✓ Update complete"
