#!/usr/bin/env bash
# ==============================================================================
# Bikita Minerals DWRMS - Standalone Autonomous Watchdog Health Probe
# ==============================================================================
# Performs periodic health probe against local FastAPI backend, verifies container
# status, and initiates automatic self-healing restart if unresponsive.
# ==============================================================================

set -uo pipefail

HEALTH_URL="http://127.0.0.1:8000/api/v1/info"
FRONTEND_URL="http://127.0.0.1:3000/login"
LOG_DIR="/var/dwrms/logs"
LOG_FILE="${LOG_DIR}/watchdog.log"
TIMESTAMP=$(date -u '+%Y-%m-%d %H:%M:%S')

mkdir -p "${LOG_DIR}"

# 1. Execute probe with 5-second connection & read timeout
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${HEALTH_URL}" 2>/dev/null || echo "000")
FRONT_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${FRONTEND_URL}" 2>/dev/null || echo "000")

if [ "${HTTP_CODE}" -eq 200 ] && [ "${FRONT_CODE}" -eq 200 ]; then
    # Silent success for cron execution
    exit 0
fi

# 2. On non-200 or connection failure, trigger autonomous self-healing recovery
echo "[${TIMESTAMP} UTC] [ALERT] Health check failure (Backend: HTTP ${HTTP_CODE}, Frontend: HTTP ${FRONT_CODE}). Attempting autonomous recovery..." >> "${LOG_FILE}"

if [ -f "/opt/dwrms/docker-compose.yml" ]; then
    docker compose -f /opt/dwrms/docker-compose.yml up -d >> "${LOG_FILE}" 2>&1
    sleep 5
    systemctl reload nginx 2>/dev/null || systemctl restart nginx 2>/dev/null || true
    
    # Re-probe to verify recovery
    RETRY_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${HEALTH_URL}" 2>/dev/null || echo "000")
    if [ "${RETRY_CODE}" -eq 200 ]; then
        echo "[${TIMESTAMP} UTC] [RECOVERY] Containers successfully self-healed and returned HTTP 200." >> "${LOG_FILE}"
    else
        echo "[${TIMESTAMP} UTC] [CRITICAL] Self-healing attempted; health check returned HTTP ${RETRY_CODE}." >> "${LOG_FILE}"
    fi
fi
