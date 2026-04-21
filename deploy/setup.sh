#!/usr/bin/env bash
# Run this once on a fresh Ubuntu 24.04 droplet as root.
# Usage: bash setup.sh YOUR_DOMAIN.com

set -euo pipefail

DOMAIN="${1:-usewise.live}"
BRANCH="${2:-main}"
REPO="https://github.com/simbarras/usewise.git"
APP_DIR="/opt/usewise"
VENV_DIR="/opt/usewise-venv"

echo "=== System packages ==="
apt-get update -y
apt-get install -y \
    git nginx certbot python3-certbot-nginx \
    python3.12 python3.12-venv python3-pip \
    curl

echo "=== Node.js 20 (via NodeSource) ==="
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

echo "=== Dedicated system user ==="
useradd --system --shell /usr/sbin/nologin usewise \
    || echo "User already exists, skipping"

echo "=== Clone repo ==="
if [ -d "$APP_DIR" ]; then
    echo "Repo already cloned, only pulling latest changes"
    sudo -u usewise git -C "$APP_DIR" fetch origin
    sudo -u usewise git -C "$APP_DIR" checkout "$BRANCH"
    sudo -u usewise git -C "$APP_DIR" pull origin "$BRANCH"
else
    git clone -b "$BRANCH" "$REPO" "$APP_DIR"
    chown -R usewise:usewise "$APP_DIR"
fi

echo "=== Backend: Python venv + install ==="
mkdir -p "$VENV_DIR"
chown usewise:usewise "$VENV_DIR"
sudo -u usewise bash -c "
    set -e
    cd $APP_DIR/api
    [ -f $VENV_DIR/bin/pip ] || python3.12 -m venv $VENV_DIR
    $VENV_DIR/bin/pip install --upgrade pip
    $VENV_DIR/bin/pip install -e .
"

echo ""
echo "STEP: Create $APP_DIR/api/.env with your GROQ_API_KEY before continuing."
echo "      cp $APP_DIR/api/.env.example $APP_DIR/api/.env && nano $APP_DIR/api/.env"
echo ""
read -rp "Press Enter once .env is ready..."

echo "=== Backend: systemd service ==="
cp "$APP_DIR/deploy/usewise-api.service" /etc/systemd/system/usewise-api.service
systemctl daemon-reload
systemctl enable --now usewise-api

echo "=== Frontend: build ==="
# VITE_API_URL points to the /api prefix Nginx exposes
sudo -u usewise bash -c "
    set -e
    cd $APP_DIR/web
    VITE_API_URL=https://$DOMAIN/api npm ci
    VITE_API_URL=https://$DOMAIN/api npm run build
"

mkdir -p /var/www/usewise
cp -r "$APP_DIR/web/dist/." /var/www/usewise/
chown -R www-data:www-data /var/www/usewise

echo "=== Nginx config ==="
sed "s/YOUR_DOMAIN.com/$DOMAIN/g" "$APP_DIR/deploy/nginx.conf" \
    > /etc/nginx/sites-available/usewise
ln -sf /etc/nginx/sites-available/usewise /etc/nginx/sites-enabled/usewise
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo "=== SSL (Let's Encrypt) ==="
certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos \
    --email "simon.barras@epfl.ch" --redirect

systemctl reload nginx

echo ""
echo "UseWise deployed at https://$DOMAIN"
echo "Backend health:  curl https://$DOMAIN/api/health/"
