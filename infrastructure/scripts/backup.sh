#!/usr/bin/env bash
# ==============================================================================
# BIKITA MINERALS DWRMS — AUTOMATED SNAPSHOT BACKUP SCRIPT
# Version: 1.9 (Database & Storage Disaster Recovery)
# ==============================================================================
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/dwrms/backups}"
COMPOSE_FILE="${COMPOSE_FILE:-/opt/dwrms/docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-/opt/dwrms/.env}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# Load environment variables if available
if [[ -f "${ENV_FILE}" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "${ENV_FILE}"
    set +a
fi

DB_USER="${POSTGRES_USER:-${DB_USER:-postgres}}"
DB_NAME="${POSTGRES_DB:-${DB_NAME:-dwrms}}"
STORAGE_DIR="${STORAGE_PATH:-/var/dwrms/storage}"

TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
SNAPSHOT_DIR="${BACKUP_DIR}/snapshot_${TIMESTAMP}"
ARCHIVE_FILE="${BACKUP_DIR}/dwrms_backup_${TIMESTAMP}.tar.gz"

echo "==> [1/4] Starting DWRMS backup snapshot at ${TIMESTAMP} (UTC)..."
mkdir -p "${SNAPSHOT_DIR}"
mkdir -p "${BACKUP_DIR}"

# ── 1. Database Dump ─────────────────────────────────────────────────────────
echo "==> [2/4] Dumping database (${DB_NAME})..."
if docker compose -f "${COMPOSE_FILE}" ps db | grep -q "Up"; then
    if [[ "${DB_ENGINE:-postgresql}" == "mysql" ]]; then
        docker compose -f "${COMPOSE_FILE}" exec -T db mysqldump -u "${DB_USER}" -p"${DB_PASSWORD}" "${DB_NAME}" > "${SNAPSHOT_DIR}/database.sql"
    else
        docker compose -f "${COMPOSE_FILE}" exec -T db pg_dump -U "${DB_USER}" -d "${DB_NAME}" -F p > "${SNAPSHOT_DIR}/database.sql"
    fi
    echo "[OK] Database dumped successfully."
else
    echo "[WARN] Database container not running; skipping database dump."
fi

# ── 2. Storage Directory Copy ────────────────────────────────────────────────
echo "==> [3/4] Archiving persistent file storage (${STORAGE_DIR})..."
if [[ -d "${STORAGE_DIR}" ]]; then
    mkdir -p "${SNAPSHOT_DIR}/storage"
    cp -r "${STORAGE_DIR}/." "${SNAPSHOT_DIR}/storage/"
    echo "[OK] Storage copied."
else
    echo "[WARN] Storage directory not found; skipping storage copy."
fi

# ── 3. Compress & Generate Checksum ──────────────────────────────────────────
echo "==> [4/4] Creating compressed archive & SHA-256 integrity digest..."
tar -czf "${ARCHIVE_FILE}" -C "${SNAPSHOT_DIR}" .
rm -rf "${SNAPSHOT_DIR}"

sha256sum "${ARCHIVE_FILE}" > "${ARCHIVE_FILE}.sha256"
chmod 600 "${ARCHIVE_FILE}"

echo "[SUCCESS] Backup completed: ${ARCHIVE_FILE} ($(du -h "${ARCHIVE_FILE}" | cut -f1))"

# ── 4. Apply Retention Policy ────────────────────────────────────────────────
echo "Applying retention policy: pruning archives older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -type f -name "dwrms_backup_*.tar.gz*" -mtime +"${RETENTION_DAYS}" -delete
echo "Retention pruning complete."
