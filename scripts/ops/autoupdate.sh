#!/usr/bin/env bash
# ==============================================================================
# BIKITA MINERALS DWRMS — AUTOMATED 1-MINUTE CONTINUOUS UPDATE ENGINE
# Runs on 60-second systemd timer cadence to auto-pull remote changes safely.
# ==============================================================================

set -eo pipefail

APP_DIR="${INSTALL_DIR:-/opt/dwrms}"
if [[ ! -d "${APP_DIR}" ]]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    APP_DIR="${SCRIPT_DIR}"
fi

LOG_FILE="/var/dwrms/logs/autoupdate.log"
LOCK_FILE="/tmp/dwrms-autoupdate.lock"

# Ensure log directory exists
mkdir -p "$(dirname "${LOG_FILE}")" 2>/dev/null || true

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "${msg}"
    if [[ -w "$(dirname "${LOG_FILE}")" || -w "${LOG_FILE}" ]]; then
        echo "${msg}" >> "${LOG_FILE}" 2>/dev/null || true
    fi
}

# Prevent concurrent runs
if [[ -f "${LOCK_FILE}" ]]; then
    PID=$(cat "${LOCK_FILE}" 2>/dev/null || echo "")
    if [[ -n "${PID}" ]] && kill -0 "${PID}" 2>/dev/null; then
        exit 0
    fi
fi
echo "$$" > "${LOCK_FILE}"
trap 'rm -f "${LOCK_FILE}"' EXIT

cd "${APP_DIR}" || exit 0

if [[ ! -d ".git" ]]; then
    # Not a git clone directory (e.g. static archive)
    exit 0
fi

# Fetch remote silently
BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
git fetch origin "${BRANCH}" --quiet 2>/dev/null || {
    # Network unreachable or offline mode
    exit 0
}

LOCAL_HASH=$(git rev-parse HEAD 2>/dev/null || echo "")
REMOTE_HASH=$(git rev-parse "origin/${BRANCH}" 2>/dev/null || echo "")

if [[ -n "${LOCAL_HASH}" && -n "${REMOTE_HASH}" && "${LOCAL_HASH}" != "${REMOTE_HASH}" ]]; then
    log "[AUTO-UPDATE] New revision detected on origin/${BRANCH} (${LOCAL_HASH:0:7} -> ${REMOTE_HASH:0:7}). Applying..."
    
    if command -v ops &>/dev/null; then
        ops update apply --yes >> "${LOG_FILE}" 2>&1 || {
            log "[WARN] 'ops update apply' failed. Attempting git fast-forward..."
            git pull --ff-only origin "${BRANCH}" >> "${LOG_FILE}" 2>&1 || true
        }
    elif [[ -f "${APP_DIR}/scripts/ops/ops" ]]; then
        bash "${APP_DIR}/scripts/ops/ops" update apply --yes >> "${LOG_FILE}" 2>&1 || {
            git pull --ff-only origin "${BRANCH}" >> "${LOG_FILE}" 2>&1 || true
        }
    else
        git pull --ff-only origin "${BRANCH}" >> "${LOG_FILE}" 2>&1 || true
        if [[ -f "${APP_DIR}/infrastructure/docker-compose.prod.yml" ]]; then
            docker compose -f "${APP_DIR}/infrastructure/docker-compose.prod.yml" up -d --build --remove-orphans >> "${LOG_FILE}" 2>&1 || true
        fi
    fi

    NEW_HASH=$(git rev-parse HEAD 2>/dev/null || echo "")
    log "[AUTO-UPDATE] System successfully updated to ${NEW_HASH:0:7}."
fi
