#!/usr/bin/env bash
# Fix nginx so www.usewise.live is the canonical URL.
# Run on the droplet as root: bash /opt/usewise/deploy/fix-nginx.sh [DOMAIN]
# (default DOMAIN: usewise.live)

set -euo pipefail

DOMAIN="${1:-usewise.live}"

echo "=== Expanding SSL cert to cover www.$DOMAIN (if not already) ==="
certbot certonly --nginx -d "$DOMAIN" -d "www.$DOMAIN" \
    --non-interactive --agree-tos \
    --email "simon.barras@epfl.ch" \
    --expand

echo "=== Writing final nginx config (www.$DOMAIN canonical) ==="
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

ln -sf /etc/nginx/sites-available/usewise /etc/nginx/sites-enabled/usewise
nginx -t && systemctl reload nginx

echo ""
echo "Done. www.$DOMAIN is now the canonical URL."
echo "Health check: curl https://www.$DOMAIN/api/health/"
