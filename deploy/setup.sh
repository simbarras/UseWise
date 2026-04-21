#!/usr/bin/env bash
# Run this once on a fresh Ubuntu 24.04 droplet as root.
# Usage: bash setup.sh YOUR_DOMAIN.com

set -euo pipefail

DOMAIN="${1:-usewise.live}"
REPO="https://github.com/simbarras/usewise.git"
APP_DIR="/opt/usewise"

# ── System packages ─────────────────────────────────────────────────────────
apt-get update -y
apt-get install -y \
    git nginx certbot python3-certbot-nginx \
    python3.12 python3.12-venv python3-pip \
    nodejs npm

# ── Dedicated system user ────────────────────────────────────────────────────
useradd --system --shell /usr/sbin/nologin --create-home --home-dir "$APP_DIR" usewise

# ── Clone repo ───────────────────────────────────────────────────────────────
git clone "$REPO" "$APP_DIR"
chown -R usewise:usewise "$APP_DIR"

# ── Backend: Python venv + install ──────────────────────────────────────────
sudo -u usewise bash -c "
    cd $APP_DIR/api
    python3.12 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -e .
"

echo ""
echo "STEP: Create $APP_DIR/api/.env with your GROQ_API_KEY before continuing."
echo "      cp $APP_DIR/api/.env.example $APP_DIR/api/.env && nano $APP_DIR/api/.env"
echo ""
read -rp "Press Enter once .env is ready..."

# ── Backend: systemd service ─────────────────────────────────────────────────
cp "$APP_DIR/deploy/usewise-api.service" /etc/systemd/system/usewise-api.service
systemctl daemon-reload
systemctl enable --now usewise-api

# ── Frontend: build ──────────────────────────────────────────────────────────
# VITE_API_URL points to the /api prefix Nginx exposes
sudo -u usewise bash -c "
    cd $APP_DIR/web
    VITE_API_URL=https://$DOMAIN/api npm ci
    VITE_API_URL=https://$DOMAIN/api npm run build
"

mkdir -p /var/www/usewise
cp -r "$APP_DIR/web/dist/." /var/www/usewise/
chown -R www-data:www-data /var/www/usewise

# ── Nginx config ─────────────────────────────────────────────────────────────
sed "s/YOUR_DOMAIN.com/$DOMAIN/g" "$APP_DIR/deploy/nginx.conf" \
    > /etc/nginx/sites-available/usewise
ln -sf /etc/nginx/sites-available/usewise /etc/nginx/sites-enabled/usewise
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# ── SSL (Let's Encrypt) ──────────────────────────────────────────────────────
certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos \
    --email "simon.barras@epfl.ch" --redirect

systemctl reload nginx

echo ""
echo "UseWise deployed at https://$DOMAIN"
echo "Backend health:  curl https://$DOMAIN/api/health/"
