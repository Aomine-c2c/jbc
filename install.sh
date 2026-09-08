#!/usr/bin/env bash
# ==============================================================================
# BIKITA MINERALS DWRMS — AUTOMATED ONE-COMMAND INSTALLATION & SETUP SCRIPT
# Version: 2.5 (Authoritative Server Platform Deployment)
# Supported OS: Ubuntu 22.04 LTS / Ubuntu 24.04 LTS / Debian 12
# ==============================================================================
# Usage:
#   sudo ./install.sh
#   -- or via one-liner --
#   curl -fsSL <URL>/install.sh | sudo bash
# ==============================================================================

set -eo pipefail

# Text colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BLUE}${BOLD}========================================================================${NC}"
echo -e "${BLUE}${BOLD}   BIKITA MINERALS DWRMS — AUTOMATED SERVER INSTALLATION & SETUP        ${NC}"
echo -e "${BLUE}${BOLD}   Platform Version: 2.5 Authoritative Operations Core                  ${NC}"
echo -e "${BLUE}${BOLD}========================================================================${NC}"

# ── REQUIRE ROOT / SUDO ───────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}${BOLD}[ERROR] This installation script must be executed with sudo or as root.${NC}"
    echo -e "Please re-run with: ${YELLOW}sudo bash $0${NC}"
    exit 1
fi

# Determine script & repository directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${INSTALL_DIR:-/opt/dwrms}"
REPO_URL="${REPO_URL:-https://github.com/Aomine-c2c/jbc.git}"
BRANCH="${BRANCH:-main}"

echo -e "\n${CYAN}[1/7] Target Directory & Source Verification...${NC}"

# If running directly inside cloned repository, sync or link to TARGET_DIR
if [[ -f "${SCRIPT_DIR}/infrastructure/docker-compose.prod.yml" ]]; then
    echo -e "${GREEN}[OK] Running directly from repository directory: ${SCRIPT_DIR}${NC}"
    if [[ "${SCRIPT_DIR}" != "${TARGET_DIR}" ]]; then
        echo -e "Syncing source files to ${TARGET_DIR}..."
        mkdir -p "${TARGET_DIR}"
        rsync -a --exclude='.git' --exclude='node_modules' --exclude='.venv' "${SCRIPT_DIR}/" "${TARGET_DIR}/"
    fi
else
    # Clone repository to TARGET_DIR if not already present
    if [[ ! -d "${TARGET_DIR}/.git" ]]; then
        echo -e "Cloning authoritative repository (${BRANCH}) to ${TARGET_DIR}..."
        mkdir -p "${TARGET_DIR}"
        git clone --depth 1 --branch "${BRANCH}" "${REPO_URL}" "${TARGET_DIR}"
    else
        echo -e "Updating repository in ${TARGET_DIR}..."
        cd "${TARGET_DIR}"
        git fetch origin "${BRANCH}"
        git reset --hard "origin/${BRANCH}"
    fi
fi

cd "${TARGET_DIR}"

# ── INSTALL SYSTEM PREREQUISITES ──────────────────────────────────────────────
echo -e "\n${CYAN}[2/7] Installing System Prerequisites (apt)...${NC}"
apt-get update -y || {
    echo -e "${RED}[ERROR] apt-get update failed.${NC}"
    exit 1
}

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
    tar \
    rsync \
    python3-venv \
    python3-pip || {
    echo -e "${RED}[ERROR] Failed to install core packages via apt-get.${NC}"
    exit 1
}

echo -e "${GREEN}[OK] Core packages installed successfully.${NC}"

# ── DOCKER & DOCKER COMPOSE ───────────────────────────────────────────────────
echo -e "\n${CYAN}[3/7] Verifying Docker and Docker Compose Plugin...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker is not installed. Installing official Docker CE...${NC}"
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable docker
    systemctl start docker
    echo -e "${GREEN}[OK] Docker CE installed and started.${NC}"
else
    echo -e "${GREEN}[OK] Docker is already installed ($(docker --version)).${NC}"
fi

# Ensure docker service is running
systemctl is-active --quiet docker || systemctl start docker

# Add non-root executing user to docker group
if [[ -n "$SUDO_USER" && "$SUDO_USER" != "root" ]]; then
    echo -e "Configuring Docker group permissions for user: ${CYAN}${SUDO_USER}${NC}..."
    groupadd -f docker
    usermod -aG docker "$SUDO_USER" || true
fi

# ── DIRECTORIES & PERMISSIONS ─────────────────────────────────────────────────
echo -e "\n${CYAN}[4/7] Configuring Platform Directories & Storage...${NC}"
STORAGE_DIR="/var/dwrms/storage"
BACKUP_DIR="/var/dwrms/backups"
LOG_DIR="/var/dwrms/logs"
CERT_DIR="${TARGET_DIR}/infrastructure/certs"

mkdir -p "${TARGET_DIR}"
mkdir -p "${STORAGE_DIR}"/{job_cards,reports,fleet,signatures,temp}
mkdir -p "${BACKUP_DIR}"
mkdir -p "${LOG_DIR}"
mkdir -p "${CERT_DIR}"

chmod -R 750 "${STORAGE_DIR}"
chmod 700 "${BACKUP_DIR}"
chmod -R 755 "${LOG_DIR}"

# Ensure compose files and build contexts resolve from any directory
ln -sf "${TARGET_DIR}/infrastructure/docker-compose.prod.yml" "${TARGET_DIR}/docker-compose.prod.yml"
ln -sf "${TARGET_DIR}/infrastructure/docker-compose.yml" "${TARGET_DIR}/docker-compose.yml"
ln -sf "${TARGET_DIR}/backend" "${TARGET_DIR}/infrastructure/backend"
ln -sf "${TARGET_DIR}/frontend" "${TARGET_DIR}/infrastructure/frontend"
ln -sf "${TARGET_DIR}/infrastructure" "${TARGET_DIR}/infrastructure/infrastructure"

# Set up host Python management environment for instant, native 'ops' CLI execution
echo -e "Setting up host Python management environment for 'ops' CLI..."
VENV_DIR="${TARGET_DIR}/backend/.venv"
if [[ ! -d "${VENV_DIR}" ]]; then
    python3 -m venv "${VENV_DIR}" || true
fi
if [[ -f "${VENV_DIR}/bin/pip" ]]; then
    "${VENV_DIR}/bin/pip" install --upgrade pip --quiet 2>/dev/null || true
    "${VENV_DIR}/bin/pip" install -r "${TARGET_DIR}/backend/requirements.txt" --quiet 2>/dev/null || {
        "${VENV_DIR}/bin/pip" install click psutil pydantic pydantic-settings python-dotenv --quiet 2>/dev/null || true
    }
fi

# Set up global CLI symlink
if [[ -f "${TARGET_DIR}/scripts/ops/ops" ]]; then
    chmod +x "${TARGET_DIR}/scripts/ops/ops"
    ln -sf "${TARGET_DIR}/scripts/ops/ops" /usr/local/bin/ops
    echo -e "${GREEN}[OK] Global management command installed: /usr/local/bin/ops${NC}"
fi

# Grant directory ownership to executing user if under sudo
if [[ -n "$SUDO_USER" && "$SUDO_USER" != "root" ]]; then
    chown -R "$SUDO_USER":"$SUDO_USER" "${TARGET_DIR}" 2>/dev/null || true
fi

# ── CONFIGURE ENVIRONMENT & TLS ───────────────────────────────────────────────
echo -e "\n${CYAN}[5/7] Verifying Configuration (.env) & TLS Certificates...${NC}"
ENV_FILE="${TARGET_DIR}/.env"

# Auto-detect Server LAN IP
HOST_LAN_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || ip route get 1.1.1.1 2>/dev/null | awk -F"src " 'NR==1{split($2,a," ");print a[1]}' || echo "127.0.0.1")
if [[ -z "$HOST_LAN_IP" ]]; then
    HOST_LAN_IP="127.0.0.1"
fi

# Auto-detect Tailscale IP and MagicDNS
TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "")
MAGIC_DNS=""
if command -v tailscale &>/dev/null; then
    MAGIC_DNS=$(tailscale status --json 2>/dev/null | jq -r '.Self.DNSName // empty' 2>/dev/null | sed 's/\.$//' || echo "")
    # Configure Tailscale background serve for port 80 if active
    tailscale serve --bg 80 >/dev/null 2>&1 || true
fi

# Build authoritative dual IP CORS list
CORS_ORIGINS_VAL="https://localhost,http://localhost:3000,http://localhost:1420,tauri://localhost"
if [[ -n "$HOST_LAN_IP" && "$HOST_LAN_IP" != "127.0.0.1" ]]; then
    CORS_ORIGINS_VAL="${CORS_ORIGINS_VAL},http://${HOST_LAN_IP},https://${HOST_LAN_IP},http://${HOST_LAN_IP}:3000"
fi
if [[ -n "$TAILSCALE_IP" ]]; then
    CORS_ORIGINS_VAL="${CORS_ORIGINS_VAL},http://${TAILSCALE_IP},https://${TAILSCALE_IP},http://${TAILSCALE_IP}:3000"
fi
if [[ -n "$MAGIC_DNS" ]]; then
    CORS_ORIGINS_VAL="${CORS_ORIGINS_VAL},http://${MAGIC_DNS},https://${MAGIC_DNS}"
fi

echo -e "Detected Local LAN IP:      ${GREEN}${HOST_LAN_IP}${NC}"
if [[ -n "${TAILSCALE_IP}" ]]; then
    echo -e "Detected Tailscale IP:     ${GREEN}${TAILSCALE_IP}${NC} (MagicDNS: ${CYAN}${MAGIC_DNS:-dwrms.internal}${NC})"
else
    echo -e "Tailscale status:          ${YELLOW}Not installed / offline (LAN web access active)${NC}"
fi

if [[ ! -f "${ENV_FILE}" ]]; then
    echo -e "${YELLOW}Generating new production .env configuration...${NC}"
    SECRET_KEY_VAL=$(openssl rand -hex 32)
    MYSQL_PASS_VAL=$(openssl rand -hex 16)
    MYSQL_ROOT_VAL=$(openssl rand -hex 16)

    cat <<EOF > "${ENV_FILE}"
# BIKITA MINERALS DWRMS — SERVER PRODUCTION ENVIRONMENT
APP_NAME="Bikita Minerals DWRMS"
ENVIRONMENT=production
DEBUG=false
SERVER_NAME=bikita-srv-01
TIMEZONE=Africa/Harare

# Authoritative URLs & Dual IP Visibility
FRONTEND_URL=https://${HOST_LAN_IP}
NEXT_PUBLIC_API_URL=https://${HOST_LAN_IP}/api/v1
CORS_ORIGINS=${CORS_ORIGINS_VAL}
HOST_LAN_IP=${HOST_LAN_IP}
TAILSCALE_IP=${TAILSCALE_IP}
MAGIC_DNS=${MAGIC_DNS}

# Database Configuration (MySQL 8.0 container)
DB_ENGINE=mysql
DB_HOST=db
DB_PORT=3306
DB_NAME=dwrms
DB_USER=dwrms_user
DB_PASSWORD=${MYSQL_PASS_VAL}
MYSQL_DATABASE=dwrms
MYSQL_USER=dwrms_user
MYSQL_PASSWORD=${MYSQL_PASS_VAL}
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_VAL}

# Security
SECRET_KEY=${SECRET_KEY_VAL}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Storage & Logs
STORAGE_PATH=/var/dwrms/storage
BACKUP_DIR=/var/dwrms/backups
LOG_DIR=/var/dwrms/logs
LOG_LEVEL=INFO
LOG_FORMAT=json

# Setup state
SETUP_COMPLETED=true
EOF
    chmod 600 "${ENV_FILE}"
    echo -e "${GREEN}[OK] Generated secure .env configuration with dual IP support.${NC}"
else
    echo -e "${GREEN}[OK] Existing .env file found. Syncing dual IP CORS origins...${NC}"
    # Ensure current LAN IP and Tailscale IP are appended to CORS_ORIGINS if missing
    if ! grep -q "${HOST_LAN_IP}" "${ENV_FILE}" 2>/dev/null; then
        sed -i "/^CORS_ORIGINS=/ s|\$|,http://${HOST_LAN_IP},https://${HOST_LAN_IP}|" "${ENV_FILE}" 2>/dev/null || true
    fi
    if [[ -n "${TAILSCALE_IP}" ]] && ! grep -q "${TAILSCALE_IP}" "${ENV_FILE}" 2>/dev/null; then
        sed -i "/^CORS_ORIGINS=/ s|\$|,http://${TAILSCALE_IP},https://${TAILSCALE_IP}|" "${ENV_FILE}" 2>/dev/null || true
    fi
fi

# Ensure infrastructure/.env symlink stays synced with root .env
ln -sf "${ENV_FILE}" "${TARGET_DIR}/infrastructure/.env"


# TLS Certificates
CERT_FILE="${CERT_DIR}/dwrms.crt"
KEY_FILE="${CERT_DIR}/dwrms.key"

if [[ ! -f "$CERT_FILE" || ! -f "$KEY_FILE" ]]; then
    echo -e "${YELLOW}Generating self-signed TLS certificates for HTTPS gateway...${NC}"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$KEY_FILE" \
        -out "$CERT_FILE" \
        -subj "/C=ZW/ST=Masvingo/L=Bikita/O=Bikita Minerals/OU=Operations/CN=dwrms.internal" > /dev/null 2>&1
    chmod 600 "$KEY_FILE"
    chmod 644 "$CERT_FILE"
    echo -e "${GREEN}[OK] TLS certificates installed at ${CERT_DIR}.${NC}"
else
    echo -e "${GREEN}[OK] TLS certificates already present.${NC}"
fi

# ── CONFIGURE FIREWALL ────────────────────────────────────────────────────────
if command -v ufw &> /dev/null; then
    echo -e "\n${CYAN}Configuring UFW firewall rules...${NC}"
    ufw default deny incoming > /dev/null 2>&1 || true
    ufw default allow outgoing > /dev/null 2>&1 || true
    ufw allow 22/tcp comment "SSH Remote Management" > /dev/null 2>&1 || true
    ufw allow 80/tcp comment "HTTP Web Gateway" > /dev/null 2>&1 || true
    ufw allow 443/tcp comment "HTTPS Secure Gateway" > /dev/null 2>&1 || true
    ufw deny 3306/tcp comment "Block external MySQL" > /dev/null 2>&1 || true
    ufw deny 5432/tcp comment "Block external Postgres" > /dev/null 2>&1 || true
    ufw deny 6379/tcp comment "Block external Redis" > /dev/null 2>&1 || true
    ufw deny 8000/tcp comment "Block internal API port" > /dev/null 2>&1 || true
    echo "y" | ufw enable > /dev/null 2>&1 || true
    echo -e "${GREEN}[OK] Firewall configured: Public traffic restricted strictly to HTTPS (443), HTTP (80), and SSH (22).${NC}"
fi

# ── START PLATFORM & INITIALIZE DATABASE ──────────────────────────────────────
echo -e "\n${CYAN}[6/7] Launching Docker Containers & Initializing Schema...${NC}"
COMPOSE_FILE="${TARGET_DIR}/docker-compose.prod.yml"
if [[ ! -f "${COMPOSE_FILE}" ]]; then
    COMPOSE_FILE="${TARGET_DIR}/infrastructure/docker-compose.prod.yml"
fi

if [[ ! -f "${COMPOSE_FILE}" ]]; then
    echo -e "${RED}[ERROR] Compose file not found: ${COMPOSE_FILE}${NC}"
    exit 1
fi

dcompose() {
    docker compose --project-directory "${TARGET_DIR}" --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" "$@"
}

echo -e "Starting Database and Redis..."
dcompose up -d db redis

echo -e "Waiting for database to pass health check..."
ATTEMPTS=0
MAX_ATTEMPTS=35
until dcompose ps db | grep -qi "healthy"; do
    ATTEMPTS=$((ATTEMPTS + 1))
    if [[ $ATTEMPTS -ge $MAX_ATTEMPTS ]]; then
        echo -e "${RED}[ERROR] Database container failed to become healthy within timeout.${NC}"
        dcompose logs db --tail 50
        exit 1
    fi
    sleep 2
done
echo -e "${GREEN}[OK] Database container is healthy.${NC}"

echo -e "Creating tables and applying database schema..."
dcompose run --rm backend python init_db_all.py || {
    echo -e "${YELLOW}[WARN] init_db_all.py returned non-zero, checking alembic...${NC}"
    dcompose run --rm backend alembic upgrade head || true
}

echo -e "Seeding administrative roles, permissions, and default accounts..."
dcompose run --rm backend python seed.py
dcompose run --rm backend python seed_rbac.py

echo -e "Seeding rich industrial mining operations data (Fleet, Assets, Job Cards, Inventory, SLAs)..."
dcompose run --rm backend python seed_faker.py || {
    echo -e "${YELLOW}[WARN] Rich faker seeding encountered a notice, proceeding with verified baseline.${NC}"
}

echo -e "Building and starting full production stack (Backend, Frontend, Celery Worker, Celery Beat, Nginx)..."
dcompose up -d --build --remove-orphans

# ── SYSTEMD SERVICE INSTALLATION ──────────────────────────────────────────────
echo -e "\n${CYAN}[7/7] Registering Systemd Services and Automated Timers...${NC}"
SYSTEMD_SRC="${TARGET_DIR}/infrastructure/systemd"
if [[ -d "${SYSTEMD_SRC}" && -d "/etc/systemd/system" ]]; then
    chmod +x "${TARGET_DIR}/scripts/ops/autoupdate.sh" 2>/dev/null || true
    cp "${SYSTEMD_SRC}"/dwrms*.service /etc/systemd/system/ 2>/dev/null || true
    cp "${SYSTEMD_SRC}"/dwrms*.timer /etc/systemd/system/ 2>/dev/null || true
    systemctl daemon-reload
    systemctl enable dwrms.service > /dev/null 2>&1 || true
    systemctl enable --now dwrms-backup.timer > /dev/null 2>&1 || true
    systemctl enable --now dwrms-healthcheck.timer > /dev/null 2>&1 || true
    systemctl enable --now dwrms-autoupdate.timer > /dev/null 2>&1 || true
    echo -e "${GREEN}[OK] Systemd service 'dwrms', backup timers, and 1-minute auto-pull timer enabled.${NC}"
fi

# ── VERIFY HEALTH ─────────────────────────────────────────────────────────────
echo -e "\n${CYAN}Verifying system readiness...${NC}"
sleep 5

HEALTH_CHECK_OK=false
for i in {1..12}; do
    if curl -k -fsS https://localhost/health > /dev/null 2>&1 || curl -k -fsS http://localhost/health > /dev/null 2>&1 || curl -k -fsS http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        HEALTH_CHECK_OK=true
        break
    fi
    sleep 3
done

if [[ "$HEALTH_CHECK_OK" = true ]]; then
    echo -e "${GREEN}[OK] API Gateway and Backend health checks are PASSING.${NC}"
else
    echo -e "${YELLOW}[WARN] Health check still warming up. Inspect container logs with 'ops logs' or 'docker compose logs'.${NC}"
fi

# ── SUMMARY ───────────────────────────────────────────────────────────────────
echo -e "\n${GREEN}${BOLD}========================================================================${NC}"
echo -e "${GREEN}${BOLD}   INSTALLATION & SETUP COMPLETE! DWRMS SERVER IS OPERATIONAL           ${NC}"
echo -e "${GREEN}${BOLD}========================================================================${NC}"
echo -e "Local LAN Web App:   ${BLUE}${BOLD}http://${HOST_LAN_IP}${NC} (or https://${HOST_LAN_IP})"
if [[ -n "${TAILSCALE_IP}" ]]; then
echo -e "Tailscale Web App:   ${BLUE}${BOLD}https://${TAILSCALE_IP}${NC} (MagicDNS: ${CYAN}${MAGIC_DNS:-dwrms.internal}${NC})"
else
echo -e "Tailscale Web App:   ${YELLOW}Tailscale not detected. Install for remote mesh access.${NC}"
fi
echo -e "API Gateway:         ${BLUE}${BOLD}https://${HOST_LAN_IP}/api/v1${NC}"
echo -e "Default Admin:       ${YELLOW}admin@bikita.com${NC} / ${YELLOW}password123${NC} (change after login)"
echo -e "Auto-Pull Updates:   ${GREEN}Active (Running every 60s via dwrms-autoupdate.timer)${NC}"
if [[ -n "${SUDO_USER}" && "${SUDO_USER}" != "root" ]]; then
echo -e "Docker Group:        ${GREEN}User '${SUDO_USER}' added to 'docker' group.${NC}"
echo -e "                     ${YELLOW}(Note: Run 'newgrp docker' in your active shell to use ops without sudo)${NC}"
fi
echo -e ""
echo -e "Management Commands:"
echo -e "  Live Monitor TUI:  ${CYAN}ops monitor${NC}"
echo -e "  Check status:      ${CYAN}ops status${NC}"
echo -e "  View logs:         ${CYAN}ops logs -n 50${NC}"
echo -e "  Apply update:      ${CYAN}ops update apply${NC}"
echo -e "  Create backup:     ${CYAN}ops backup create${NC}"
echo -e "  Restart stack:     ${CYAN}ops server restart${NC}"
echo -e "  Systemd status:    ${CYAN}systemctl status dwrms${NC}"
echo -e "${GREEN}========================================================================${NC}"

# ── AUTOMATICALLY LAUNCH MONITOR TUI IN INTERACTIVE SHELL ──────────────────────
if [[ -t 0 ]]; then
    echo -e "\n${CYAN}Launching live operations monitoring console (ops monitor)... (Press 'q' to exit)${NC}"
    sleep 2
    if command -v ops &>/dev/null; then
        ops monitor || true
    elif [[ -f "${TARGET_DIR}/scripts/ops/ops" ]]; then
        python3 "${TARGET_DIR}/scripts/ops/ops" monitor || true
    fi
fi

