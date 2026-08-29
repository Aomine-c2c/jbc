#!/usr/bin/env bash

# This script checks GitHub for new commits on the main branch.
# If new commits are found, it pulls them and restarts the application.

INSTALL_DIR="/opt/dwrms"
cd "${INSTALL_DIR}" || exit 1

# Fetch latest from origin
git fetch origin main >/dev/null 2>&1

# Get local and remote commit hashes
LOCAL_HASH=$(git rev-parse HEAD)
REMOTE_HASH=$(git rev-parse origin/main)

if [ "$LOCAL_HASH" != "$REMOTE_HASH" ]; then
    echo "[$(date)] New updates found ($LOCAL_HASH -> $REMOTE_HASH). Deploying..."
    
    # Pull the latest code
    git reset --hard origin/main
    
    # Rebuild and restart the application containers
    docker compose -f docker-compose.prod.yml up -d --build backend frontend worker beat
    
    echo "[$(date)] Auto-update complete."
fi
