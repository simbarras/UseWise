#!/usr/bin/env bash
# Bootstrap a fresh Ubuntu 24.04 droplet for UseWise (Docker-based).
# Usage: bash setup.sh [DOMAIN] [BRANCH]   (default: usewise.live, main)
# Run as root.

set -euo pipefail

DOMAIN="${1:-usewise.live}"
REPO="https://github.com/simbarras/usewise.git"
BRANCH="${2:-main}"
APP_DIR="/opt/usewise"
DEPLOY_DIR="$APP_DIR/deploy"

echo "=== System packages ==="
apt-get update -y
apt-get install -y git nginx certbot python3-certbot-nginx curl

echo "=== Docker ==="
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
fi
# Ensure docker compose plugin is available
docker compose version

echo "=== Clone / update repo ==="
if [ -d "$APP_DIR/.git" ]; then
    echo "Repo already cloned — pulling latest"
    git -C "$APP_DIR" fetch origin
    git -C "$APP_DIR" checkout "$BRANCH"
    git -C "$APP_DIR" pull origin "$BRANCH"
else
    git clone -b "$BRANCH" "$REPO" "$APP_DIR"
fi

echo "=== Prepare data dir for SQLite DB ==="
mkdir -p "$DEPLOY_DIR/data"

echo ""
echo "STEP: Create $DEPLOY_DIR/.env with your GROQ_API_KEY before continuing."
echo "      cp $DEPLOY_DIR/.env.example $DEPLOY_DIR/.env && nano $DEPLOY_DIR/.env"
echo ""
read -rp "Press Enter once .env is ready..."

echo "=== Pull Docker images ==="
cd "$DEPLOY_DIR"
docker compose pull

echo "=== Start containers ==="
docker compose up -d

echo "=== Nginx config (HTTP only — for certbot ACME challenge) ==="
cat > /etc/nginx/sites-available/usewise <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        client_max_body_size 5M;
    }
}
EOF
ln -sf /etc/nginx/sites-available/usewise /etc/nginx/sites-enabled/usewise
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo "=== SSL (Let's Encrypt — certonly so we control the final nginx config) ==="
certbot certonly --nginx -d "$DOMAIN" -d "www.$DOMAIN" \
    --non-interactive --agree-tos \
    --email "simon.barras@epfl.ch"

echo "=== Nginx config (final — www.$DOMAIN is canonical) ==="
# www.$DOMAIN is the real app; bare $DOMAIN redirects to www.
cat > /etc/nginx/sites-available/usewise <<EOF
# HTTP: redirect everything to https://www.$DOMAIN
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    return 301 https://www.$DOMAIN\$request_uri;
}

# HTTPS: bare domain → redirect to www
server {
    listen 443 ssl;
    server_name $DOMAIN;
    ssl_certificate     /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    return 301 https://www.$DOMAIN\$request_uri;
}

# HTTPS: www.$DOMAIN — the real app
server {
    listen 443 ssl;
    server_name www.$DOMAIN;
    ssl_certificate     /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host              \$host;
        proxy_set_header X-Real-IP         \$remote_addr;
        proxy_set_header X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        client_max_body_size 5M;
    }
}
EOF
nginx -t && systemctl reload nginx

echo ""
echo "UseWise deployed at https://www.$DOMAIN"
echo "NOTE: Ensure your DNS has an A record for www.$DOMAIN pointing to this server's IP."
echo "Health check: curl https://www.$DOMAIN/api/health/"
