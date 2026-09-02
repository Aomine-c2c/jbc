#!/usr/bin/env bash
# ==============================================================================
# Bikita Minerals DWRMS - Standalone Autonomous Watchdog Health Probe
# ==============================================================================
# Performs periodic health probe against local FastAPI backend, verifies DB lock
# status, and initiates automatic self-healing restart if unresponsive.
# ==============================================================================

set -uo pipefail

HEALTH_URL="http://127.0.0.1:8000/api/v1/health"
SERVICE_NAME="dwrms-backend.service"
LOG_DIR="/var/log/dwrms"
LOG_FILE="${LOG_DIR}/watchdog.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

mkdir -p "${LOG_DIR}"

# 1. Execute probe with 5-second connection & read timeout
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${HEALTH_URL}" 2>/dev/null || echo "000")

if [ "${HTTP_CODE}" -eq 200 ]; then
    # Silent success for cron execution
    exit 0
fi

# 2. On non-200 or connection failure, trigger autonomous self-healing recovery
echo "[${TIMESTAMP}] [ALERT] Health check failed with HTTP ${HTTP_CODE}. Attempting autonomous recovery..." >> "${LOG_FILE}"

if command -v systemctl &>/dev/null; then
    systemctl restart "${SERVICE_NAME}"
    sleep 5
    
    # Re-probe to verify recovery
    RETRY_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${HEALTH_URL}" 2>/dev/null || echo "000")
    if [ "${RETRY_CODE}" -eq 200 ]; then
        echo "[${TIMESTAMP}] [RECOVERY] Service ${SERVICE_NAME} successfully self-healed and returned HTTP 200." >> "${LOG_FILE}"
    else
        echo "[${TIMESTAMP}] [CRITICAL] Self-healing restart completed but health check still returned HTTP ${RETRY_CODE}." >> "${LOG_FILE}"
    fi
else
    echo "[${TIMESTAMP}] [ERROR] systemctl command unavailable on host." >> "${LOG_FILE}"
fi
