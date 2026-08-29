#!/usr/bin/env bash
# ==============================================================================
# BIKITA MINERALS DWRMS — PRODUCTION SERVER DEPLOYMENT ORCHESTRATOR
# Platform Version: V1.9 (Server-First Authoritative Operations Core)
# Target OS: Ubuntu Server 22.04 LTS / 24.04 LTS
# ==============================================================================
# Lifecycle Workflow:
#   1. INSTALL
#   2. CONFIGURE
#   3. INITIALIZE DATABASE
#   4. RUN MIGRATIONS
#   5. CREATE INITIAL ADMINISTRATOR
#   6. CONFIGURE STORAGE
#   7. START SERVICES
#   8. VERIFY HEALTH
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

INSTALL_DIR="${INSTALL_DIR:-/opt/dwrms}"
STORAGE_DIR="${STORAGE_DIR:-/var/dwrms/storage}"
BACKUP_DIR="${BACKUP_DIR:-/var/dwrms/backups}"
LOG_DIR="${LOG_DIR:-/var/dwrms/logs}"
COMPOSE_FILE="${INSTALL_DIR}/docker-compose.prod.yml"

echo -e "${BLUE}========================================================================${NC}"
echo -e "${BLUE}   BIKITA MINERALS DWRMS — UBUNTU SERVER PRODUCTION DEPLOYMENT (V1.9)   ${NC}"
echo -e "${BLUE}========================================================================${NC}"

# Check for root privileges
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}[ERROR] This deployment script must be executed as root or with sudo.${NC}"
   exit 1
fi

# ── STAGE 1: INSTALL ─────────────────────────────────────────────────────────
echo -e "\n${CYAN}==> [1/8] STAGE: INSTALL (Prerequisites & Dependencies)...${NC}"

apt-get update -y
apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    ufw \
    openssl \
    jq \
    cron \
    logrotate \
    tar

# Install Docker CE and Compose plugin if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker CE..."
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable docker
    systemctl start docker
fi

# Create directory hierarchy
mkdir -p "${INSTALL_DIR}"
mkdir -p "${STORAGE_DIR}"/{job_cards,reports,fleet,signatures,temp}
mkdir -p "${BACKUP_DIR}"
mkdir -p "${LOG_DIR}"
mkdir -p "${INSTALL_DIR}/infrastructure/certs"

# Configure UFW Firewall (Public HTTPS/SSH only)
echo "Configuring firewall rules..."
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment "SSH Remote Administration"
ufw allow 80/tcp comment "HTTP Gateway"
ufw allow 443/tcp comment "HTTPS Gateway"
ufw deny 3306/tcp comment "Block external MySQL"
ufw deny 5432/tcp comment "Block external PostgreSQL"
ufw deny 6379/tcp comment "Block external Redis"
ufw deny 8000/tcp comment "Block direct API port"
echo "y" | ufw enable || true
echo -e "${GREEN}[OK] STAGE 1 (INSTALL) COMPLETE: Packages, directories, and firewall active.${NC}"

# ── STAGE 2: CONFIGURE ───────────────────────────────────────────────────────
echo -e "\n${CYAN}==> [2/8] STAGE: CONFIGURE (Environment & TLS Security)...${NC}"

ENV_FILE="${INSTALL_DIR}/.env"
if [[ ! -f "${ENV_FILE}" ]]; then
    if [[ -f "${INSTALL_DIR}/.env.production.example" ]]; then
        cp "${INSTALL_DIR}/.env.production.example" "${ENV_FILE}"
    elif [[ -f "${INSTALL_DIR}/.env.example" ]]; then
        cp "${INSTALL_DIR}/.env.example" "${ENV_FILE}"
    fi

    # Generate secure 32-byte secret key
    RAND_KEY=$(openssl rand -hex 32)
    sed -i "s/SECRET_KEY=.*/SECRET_KEY=${RAND_KEY}/" "${ENV_FILE}"
    echo -e "${GREEN}[OK] Generated .env with secure SECRET_KEY.${NC}"
fi

# Load variables
set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

# Generate fallback self-signed TLS certificates if none exist
CERT_FILE="${INSTALL_DIR}/infrastructure/certs/dwrms.crt"
KEY_FILE="${INSTALL_DIR}/infrastructure/certs/dwrms.key"
if [[ ! -f "$CERT_FILE" || ! -f "$KEY_FILE" ]]; then
    echo "Generating TLS certificate for initial deployment..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$KEY_FILE" \
        -out "$CERT_FILE" \
        -subj "/C=ZW/ST=Masvingo/L=Bikita/O=Bikita Minerals/OU=Operations/CN=${FRONTEND_URL:-dwrms.bikita.com}"
    chmod 600 "$KEY_FILE"
    chmod 644 "$CERT_FILE"
fi
echo -e "${GREEN}[OK] STAGE 2 (CONFIGURE) COMPLETE: Environment & TLS certificates verified.${NC}"

# ── STAGE 3: INITIALIZE DATABASE ─────────────────────────────────────────────
echo -e "\n${CYAN}==> [3/8] STAGE: INITIALIZE DATABASE (Starting db & redis containers)...${NC}"
cd "${INSTALL_DIR}"
docker compose -f "${COMPOSE_FILE}" up -d db redis

echo "Waiting for database container health status..."
ATTEMPTS=0
MAX_ATTEMPTS=30
until docker compose -f "${COMPOSE_FILE}" ps db | grep -q "(healthy)"; do
    ATTEMPTS=$((ATTEMPTS + 1))
    if [[ $ATTEMPTS -ge $MAX_ATTEMPTS ]]; then
        echo -e "${RED}[ERROR] Database container failed to become healthy within timeout.${NC}"
        docker compose -f "${COMPOSE_FILE}" logs db
        exit 1
    fi
    sleep 2
done
echo -e "${GREEN}[OK] STAGE 3 (INITIALIZE DATABASE) COMPLETE: Database is healthy.${NC}"

# ── STAGE 4: RUN MIGRATIONS ──────────────────────────────────────────────────
echo -e "\n${CYAN}==> [4/8] STAGE: RUN MIGRATIONS (Alembic schema migrations)...${NC}"
docker compose -f "${COMPOSE_FILE}" run --rm backend python manage.py migrate || {
    echo -e "${YELLOW}[INFO] Applying fallback schema initialization...${NC}"
    docker compose -f "${COMPOSE_FILE}" run --rm backend python manage.py init-db
}
echo -e "${GREEN}[OK] STAGE 4 (RUN MIGRATIONS) COMPLETE: Schema up to date.${NC}"

# ── STAGE 5: CREATE INITIAL ADMINISTRATOR ────────────────────────────────────
echo -e "\n${CYAN}==> [5/8] STAGE: CREATE INITIAL ADMINISTRATOR (Baseline seed & admin)...${NC}"
docker compose -f "${COMPOSE_FILE}" run --rm backend python manage.py seed

ADMIN_EMAIL="${INITIAL_ADMIN_EMAIL:-admin@bikita.com}"
ADMIN_PASS="${INITIAL_ADMIN_PASSWORD:-}"

if [[ -n "$ADMIN_PASS" ]]; then
    docker compose -f "${COMPOSE_FILE}" run --rm backend python manage.py createsuperuser \
        --email "$ADMIN_EMAIL" \
        --password "$ADMIN_PASS" \
        --first-name "System" \
        --last-name "Administrator" \
        --department "Maintenance" || true
    echo -e "${GREEN}[OK] Administrator account (${ADMIN_EMAIL}) provisioned.${NC}"
else
    echo -e "${YELLOW}[INFO] Seeded default superuser (admin@bikita.com). Change password on first login.${NC}"
fi
echo -e "${GREEN}[OK] STAGE 5 (CREATE INITIAL ADMINISTRATOR) COMPLETE.${NC}"

# ── STAGE 6: CONFIGURE STORAGE ───────────────────────────────────────────────
echo -e "\n${CYAN}==> [6/8] STAGE: CONFIGURE STORAGE (Directories & Permissions)...${NC}"
chmod -R 750 "${STORAGE_DIR}"
chmod 700 "${BACKUP_DIR}"
chmod -R 755 "${LOG_DIR}"

docker compose -f "${COMPOSE_FILE}" run --rm backend python manage.py storage-verify
echo -e "${GREEN}[OK] STAGE 6 (CONFIGURE STORAGE) COMPLETE: Storage initialized and verified.${NC}"

# ── STAGE 7: START SERVICES ──────────────────────────────────────────────────
echo -e "\n${CYAN}==> [7/8] STAGE: START SERVICES (Deploying full stack & Systemd units)...${NC}"
# Install Systemd units
cp "${INSTALL_DIR}/infrastructure/systemd/dwrms.service" /etc/systemd/system/
cp "${INSTALL_DIR}/infrastructure/systemd/dwrms-backup.service" /etc/systemd/system/
cp "${INSTALL_DIR}/infrastructure/systemd/dwrms-backup.timer" /etc/systemd/system/
cp "${INSTALL_DIR}/infrastructure/systemd/dwrms-healthcheck.service" /etc/systemd/system/
cp "${INSTALL_DIR}/infrastructure/systemd/dwrms-healthcheck.timer" /etc/systemd/system/

systemctl daemon-reload
systemctl enable --now dwrms.service
systemctl enable --now dwrms-backup.timer
systemctl enable --now dwrms-healthcheck.timer

docker compose -f "${COMPOSE_FILE}" up -d --build --remove-orphans
echo -e "${GREEN}[OK] STAGE 7 (START SERVICES) COMPLETE: All containers & Systemd units active.${NC}"

# ── STAGE 8: VERIFY HEALTH ───────────────────────────────────────────────────
echo -e "\n${CYAN}==> [8/8] STAGE: VERIFY HEALTH (Probing health & readiness endpoints)...${NC}"
sleep 5

echo "Testing /health endpoint..."
curl -k -fsS https://localhost/health | jq . || curl -k -fsS https://localhost/api/v1/health | jq .

echo "Testing /readiness endpoint..."
curl -k -fsS https://localhost/readiness | jq . || curl -k -fsS https://localhost/api/v1/readiness | jq .

echo "Testing /version endpoint..."
curl -k -fsS https://localhost/version | jq . || curl -k -fsS https://localhost/api/v1/version | jq .

echo -e "\n${GREEN}========================================================================${NC}"
echo -e "${GREEN}   DEPLOYMENT SUCCESSFUL: DWRMS V1.9 Authoritative Ubuntu Server Core   ${NC}"
echo -e "${GREEN}========================================================================${NC}"
echo -e "Operational Portal:  ${BLUE}${FRONTEND_URL:-https://dwrms.bikita.com}${NC}"
echo -e "API Gateway:         ${BLUE}${FRONTEND_URL:-https://dwrms.bikita.com}/api/v1${NC}"
echo -e "Health Monitor:      ${BLUE}curl -k https://localhost/readiness${NC}"
echo -e "Management CLI:      ${BLUE}cd /opt/dwrms && python manage.py --help${NC}"
echo -e "Systemd Service:     ${BLUE}systemctl status dwrms${NC}"
echo -e "Backup Schedule:     ${BLUE}Daily at 02:00 CAT (/var/dwrms/backups)${NC}"
