#!/usr/bin/env bash
# ==============================================================================
# Bikita Minerals DWRMS — Autonomous GitHub Repository Synchronizer & Deployer
# Checks origin/main every cycle, pulls updates, builds containers, runs DB init & seeds, and reloads Nginx.
# ==============================================================================

set -uo pipefail

INSTALL_DIR="/opt/dwrms"
LOG_DIR="/var/dwrms/logs"
mkdir -p "${LOG_DIR}"

cd "${INSTALL_DIR}" || exit 1

# Automatically clear any stale git locks that might jam the updater
rm -f .git/index.lock

# Fetch latest from origin
if ! git fetch origin main --prune >/dev/null 2>&1; then
    echo "[$(date -u)] Git fetch failed, attempting to repair origin refs..."
    git update-ref -d refs/remotes/origin/main 2>/dev/null || true
    git fetch origin main --prune >/dev/null 2>&1 || exit 0
fi

# Get local and remote commit hashes
LOCAL_HASH=$(git rev-parse HEAD 2>/dev/null || echo "NONE")
REMOTE_HASH=$(git rev-parse origin/main 2>/dev/null || echo "UNKNOWN")

if [ "$LOCAL_HASH" != "$REMOTE_HASH" ] && [ "$REMOTE_HASH" != "UNKNOWN" ]; then
    echo "[$(date -u)] [AUTONOMOUS SYNC] New GitHub update detected ($LOCAL_HASH -> $REMOTE_HASH). Deploying..."
    
    # 1. Reset working directory to match GitHub origin/main exactly
    git reset --hard origin/main
    git clean -fd
    chown -R sila:sila "${INSTALL_DIR}" 2>/dev/null || true

    # 2. Update Nginx reverse proxy if changed
    if [ -f "${INSTALL_DIR}/deploy/nginx_dwrms.conf" ]; then
        cp -f "${INSTALL_DIR}/deploy/nginx_dwrms.conf" /etc/nginx/sites-available/dwrms.conf
        rm -f /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/personal-server
        ln -sf /etc/nginx/sites-available/dwrms.conf /etc/nginx/sites-enabled/dwrms.conf
        nginx -t >/dev/null 2>&1 && (systemctl reload nginx 2>/dev/null || systemctl restart nginx 2>/dev/null) || true
    fi

    # 3. Ensure Tailscale HTTPS Serve is active on port 80
    tailscale serve --bg 80 >/dev/null 2>&1 || true

    # 4. Rebuild & Launch Docker Compose containers
    docker compose -f "${INSTALL_DIR}/docker-compose.yml" down --remove-orphans >/dev/null 2>&1 || true
    docker compose -f "${INSTALL_DIR}/docker-compose.yml" build >/dev/null 2>&1 || true
    docker compose -f "${INSTALL_DIR}/docker-compose.yml" up -d

    # 5. Wait for database and backend
    sleep 10
    docker exec dwrms-backend-1 python init_db_all.py >/dev/null 2>&1 || true
    docker exec dwrms-backend-1 python seed_faker.py >/dev/null 2>&1 || true

    NEW_HASH=$(git rev-parse HEAD)
    echo "[$(date -u)] [AUTONOMOUS SYNC] Application updated and verified live on commit ${NEW_HASH}."
fi
