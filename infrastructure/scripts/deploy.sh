#!/bin/bash
set -e

ENVIRONMENT=${1:-staging}
PROJECT_DIR="/opt/dwrms"
COMPOSE_FILE="docker-compose.${ENVIRONMENT}.yml"

echo "Deploying DWRMS to ${ENVIRONMENT} environment..."

cd "${PROJECT_DIR}"

# 1. Pull the latest Docker images from the registry
echo "Pulling latest images..."
docker compose -f "${COMPOSE_FILE}" pull

# 2. Run Database Migrations before starting the new app version
# We use a temporary container to run Alembic safely.
echo "Running database migrations..."
docker compose -f "${COMPOSE_FILE}" run --rm backend alembic upgrade head

# 3. Bring up the services (recreates containers if image changed)
echo "Starting services..."
docker compose -f "${COMPOSE_FILE}" up -d --remove-orphans

# 4. Verification/Healthcheck
echo "Verifying deployment..."
sleep 10 # Wait for services to fully initialize

HEALTH_URL="http://localhost:8080/api/health"
if [ "$ENVIRONMENT" = "prod" ]; then
    HEALTH_URL="http://localhost:80/api/health"
fi

HTTP_STATUS=$(curl -o /dev/null -s -w "%{http_code}\n" "${HEALTH_URL}" || true)

if [ "${HTTP_STATUS}" == "200" ]; then
    echo "Deployment verified successfully!"
else
    echo "ERROR: Health check failed with status ${HTTP_STATUS}."
    echo "Initiating rollback procedures..."
    
    # Ideally trigger rollback script here or alert
    exit 1
fi
