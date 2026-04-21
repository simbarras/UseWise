#!/usr/bin/env bash
# Pull latest Docker images and restart containers.
# Run on the droplet: bash /opt/usewise/deploy/update.sh

set -euo pipefail

DEPLOY_DIR="/opt/usewise/deploy"

cd "$DEPLOY_DIR"

echo "=== Pulling latest images ==="
docker compose pull

echo "=== Restarting containers ==="
docker compose up -d --remove-orphans

echo "✓ Update complete"
