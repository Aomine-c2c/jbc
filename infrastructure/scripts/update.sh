#!/usr/bin/env bash

# This script is triggered by the webhook to perform a rapid auto-update.
# It assumes it is running from within the webhook container which has the docker socket mounted.

echo "[$(date)] Webhook triggered: starting auto-update process"

# Ensure we are in the root directory (mapped to /var/dwrms/repo)
cd /var/dwrms/repo

# Pull latest code
echo "Pulling latest code from origin/main..."
git fetch origin main
git reset --hard origin/main

# Restart the backend, frontend, and celery workers
# Using compose to ensure any new images are built if Dockerfiles changed
echo "Rebuilding and restarting application containers..."
docker compose -f docker-compose.prod.yml up -d --build backend frontend worker beat

echo "[$(date)] Auto-update complete."
