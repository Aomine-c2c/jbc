#!/usr/bin/env bash

# This script checks GitHub for new commits on the main branch.
# If new commits are found, it pulls them and restarts the application.

INSTALL_DIR="/opt/dwrms"
cd "${INSTALL_DIR}" || exit 1

# Automatically clear any stale git locks that might jam the updater
rm -f .git/index.lock

# Fetch latest from origin, prune dead branches, and force update refs
# If fetch fails (e.g. corrupted ref), delete the ref and try again
if ! git fetch origin main --prune >/dev/null 2>&1; then
    echo "[$(date)] Git fetch failed, attempting to repair refs..."
    git update-ref -d refs/remotes/origin/main
    git fetch origin main --prune >/dev/null 2>&1
fi

# Get local and remote commit hashes
LOCAL_HASH=$(git rev-parse HEAD 2>/dev/null || echo "NONE")
REMOTE_HASH=$(git rev-parse origin/main 2>/dev/null || echo "UNKNOWN")

if [ "$LOCAL_HASH" != "$REMOTE_HASH" ] && [ "$REMOTE_HASH" != "UNKNOWN" ]; then
    echo "[$(date)] New updates found ($LOCAL_HASH -> $REMOTE_HASH). Deploying..."
    
    # Force working directory to match the remote main branch exactly
    git reset --hard origin/main
    git clean -fd
    
    # Rebuild and restart the application containers
    docker compose -f docker-compose.prod.yml up -d --build backend frontend worker beat nginx
    
    echo "[$(date)] Auto-update complete."
fi
