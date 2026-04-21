#!/usr/bin/env bash
# Pull latest Docker images and restart containers.
# Run on the droplet: bash /opt/usewise/deploy/update.sh [BRANCH] (default: main)

set -euo pipefail

BRANCH="${1:-main}"
APP_DIR="/opt/usewise"
DEPLOY_DIR="$APP_DIR/deploy"

cd "$APP_DIR"
echo "=== Fetching latest code from branch $BRANCH ==="
git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH"

cd "$DEPLOY_DIR"
echo "=== Pulling latest images ==="
docker compose pull

echo "=== Restarting containers ==="
docker compose up -d --remove-orphans

echo "✓ Update complete"
