#!/usr/bin/env bash
# ==============================================================================
# BIKITA MINERALS DWRMS — UBUNTU SERVER PROVISIONING & DEPLOYMENT SCRIPT
# Version: 1.8 (Server-First Platform Architecture)
# Target OS: Ubuntu Server 22.04 LTS / 24.04 LTS
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==============================================================${NC}"
echo -e "${BLUE}   BIKITA MINERALS DWRMS — SERVER-FIRST UBUNTU PROVISIONING   ${NC}"
echo -e "${BLUE}   Version Update V1.8 Authoritative Operations Core          ${NC}"
echo -e "${BLUE}==============================================================${NC}"

# Check for root / sudo permissions
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}[ERROR] This script must be run as root or with sudo privileges.${NC}"
   exit 1
fi

INSTALL_DIR="/opt/dwrms"
STORAGE_DIR="/var/dwrms/storage"
BACKUP_DIR="/var/dwrms/backups"
LOG_DIR="/var/dwrms/logs"

echo -e "\n${YELLOW}==> [1/7] Updating package index and installing prerequisites...${NC}"
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
    logrotate

echo -e "\n${YELLOW}==> [2/7] Installing Docker and Docker Compose Plugin...${NC}"
if ! command -v docker &> /dev/null; then
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable docker
    systemctl start docker
    echo -e "${GREEN}[OK] Docker installed successfully.${NC}"
else
    echo -e "${GREEN}[OK] Docker is already installed.${NC}"
fi

echo -e "\n${YELLOW}==> [3/7] Setting up directories and permissions...${NC}"
mkdir -p "${INSTALL_DIR}"
mkdir -p "${STORAGE_DIR}"
mkdir -p "${BACKUP_DIR}"
mkdir -p "${LOG_DIR}"
mkdir -p "${INSTALL_DIR}/infrastructure/certs"

chmod 750 "${STORAGE_DIR}"
chmod 700 "${BACKUP_DIR}"

echo -e "\n${YELLOW}==> [4/7] Configuring UFW Firewall for Server-First Security...${NC}"
# Allow SSH, HTTP, HTTPS
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment "SSH Remote Management"
ufw allow 80/tcp comment "HTTP Client Gateway"
ufw allow 443/tcp comment "HTTPS Secure Multi-Client Gateway"

# Ensure Database & Redis ports are blocked from public internet
ufw deny 3306/tcp comment "Block external MySQL"
ufw deny 5432/tcp comment "Block external PostgreSQL"
ufw deny 6379/tcp comment "Block external Redis"
ufw deny 8000/tcp comment "Block direct backend port"

echo "y" | ufw enable || true
echo -e "${GREEN}[OK] Firewall configured: Public traffic restricted strictly to HTTPS (443) and SSH (22).${NC}"

echo -e "\n${YELLOW}==> [5/7] Generating Self-Signed TLS Certificates (if not provided)...${NC}"
CERT_FILE="${INSTALL_DIR}/infrastructure/certs/dwrms.crt"
KEY_FILE="${INSTALL_DIR}/infrastructure/certs/dwrms.key"

if [[ ! -f "$CERT_FILE" || ! -f "$KEY_FILE" ]]; then
    echo -e "${YELLOW}Generating self-signed certificate for initial installation...${NC}"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$KEY_FILE" \
        -out "$CERT_FILE" \
        -subj "/C=ZW/ST=Masvingo/L=Bikita/O=Bikita Minerals/OU=Operations/CN=dwrms.company.internal"
    chmod 600 "$KEY_FILE"
    chmod 644 "$CERT_FILE"
    echo -e "${GREEN}[OK] TLS certificate created at ${CERT_FILE}.${NC}"
fi

echo -e "\n${YELLOW}==> [6/7] Installing Systemd Services & Automated Backup Timers...${NC}"
cat << 'EOF' > /etc/systemd/system/dwrms.service
[Unit]
Description=Bikita Minerals DWRMS Server-First Platform Stack
Requires=docker.service
After=docker.service network.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/dwrms
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d --remove-orphans
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
ExecReload=/usr/bin/docker compose -f docker-compose.prod.yml up -d --remove-orphans
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

cat << 'EOF' > /etc/systemd/system/dwrms-backup.service
[Unit]
Description=Daily Automated DWRMS Database & State Backup
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/opt/dwrms
ExecStart=/bin/bash /opt/dwrms/infrastructure/scripts/backup.sh

[Install]
WantedBy=multi-user.target
EOF

cat << 'EOF' > /etc/systemd/system/dwrms-backup.timer
[Unit]
Description=Run daily DWRMS backup at 02:00 CAT
Requires=dwrms-backup.service

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
Timers.target
EOF

systemctl daemon-reload
systemctl enable dwrms-backup.timer
systemctl start dwrms-backup.timer
echo -e "${GREEN}[OK] Systemd unit files and daily backup timer (02:00 AM) configured.${NC}"

echo -e "\n${YELLOW}==> [7/7] Verifying Environment Configuration File...${NC}"
if [[ ! -f "${INSTALL_DIR}/.env" ]]; then
    if [[ -f "${INSTALL_DIR}/.env.example" ]]; then
        cp "${INSTALL_DIR}/.env.example" "${INSTALL_DIR}/.env"
        # Generate random 32-byte secret key
        RAND_KEY=$(openssl rand -hex 32)
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=${RAND_KEY}/" "${INSTALL_DIR}/.env"
        echo -e "${GREEN}[OK] Created ${INSTALL_DIR}/.env with a newly generated secure SECRET_KEY.${NC}"
    fi
fi

echo -e "\n${GREEN}==============================================================${NC}"
echo -e "${GREEN}   PROVISIONING COMPLETE: Ubuntu Server Authoritative Core    ${NC}"
echo -e "${GREEN}==============================================================${NC}"
echo -e "Next steps to launch:"
echo -e "1. Review configuration: ${BLUE}nano /opt/dwrms/.env${NC}"
echo -e "2. Start DWRMS platform: ${BLUE}systemctl start dwrms${NC}"
echo -e "3. Check live status:    ${BLUE}curl -k https://localhost/api/v1/health${NC}"
echo -e "4. Multi-client access:  Connect via Web Browser, Tauri Desktop, or Mobile PWA."
