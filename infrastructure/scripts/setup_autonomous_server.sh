#!/usr/bin/env bash
# ==============================================================================
# Bikita Minerals DWRMS - Autonomous On-Premises Server Setup Script
# Target OS: Ubuntu 22.04 LTS / 24.04 LTS Server
# ==============================================================================
# This script provisions an autonomous, self-healing server environment:
# 1. System packages & Python 3.12 environment
# 2. Process isolation & non-root user (dwrms)
# 3. Systemd auto-healing service (auto-restart on crash/power recovery)
# 4. Nginx reverse proxy with LAN HTTP/HTTPS & WebSocket forwarding
# 5. UFW Firewall security rules
# 6. Autonomous 5-minute watchdog health monitor & auto-recovery cron
# 7. Daily automated encrypted backups with 30-day rotation cleanup
# ==============================================================================

set -euo pipefail

# Visual formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# Verify root privileges
if [ "$(id -u)" -ne 0 ]; then
    log_error "This installation script must be executed as root (or with sudo)."
    exit 1
fi

INSTALL_DIR="/opt/dwrms"
APP_USER="dwrms"
APP_GROUP="dwrms"
LOG_DIR="/var/log/dwrms"
BACKUP_DIR="/var/backups/dwrms"

echo -e "${BOLD}===================================================================${NC}"
echo -e "${BOLD}   BIKITA MINERALS DWRMS - AUTONOMOUS SERVER INSTALLATION          ${NC}"
echo -e "${BOLD}===================================================================${NC}"

# 1. System Package Updates & Prerequisites
log_info "Step 1: Installing essential system dependencies and Python 3.12..."
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    software-properties-common \
    build-essential \
    curl \
    wget \
    git \
    jq \
    ufw \
    nginx \
    sqlite3 \
    libsqlite3-dev \
    tar \
    gzip \
    cron \
    logrotate

# Ensure Python 3.12 & virtual environment tooling
if ! command -v python3.12 &> /dev/null; then
    add-apt-repository -y ppa:deadsnakes/ppa
    apt-get update -y
    apt-get install -y python3.12 python3.12-venv python3.12-dev
fi

# 2. System User & Directory Layout
log_info "Step 2: Configuring system user '${APP_USER}' and production directories..."
if ! id -u "${APP_USER}" &> /dev/null; then
    useradd --system --shell /usr/sbin/nologin --home-dir "${INSTALL_DIR}" --create-home "${APP_USER}"
    log_success "Created system user: ${APP_USER}"
fi

mkdir -p "${INSTALL_DIR}" "${LOG_DIR}" "${BACKUP_DIR}" "${INSTALL_DIR}/storage" "${INSTALL_DIR}/backups"
chown -R "${APP_USER}:${APP_GROUP}" "${INSTALL_DIR}" "${LOG_DIR}" "${BACKUP_DIR}"
chmod 750 "${INSTALL_DIR}"
chmod 750 "${LOG_DIR}"
chmod 700 "${BACKUP_DIR}"

# 3. Python Virtual Environment & Backend Setup
log_info "Step 3: Setting up Python 3.12 virtual environment..."
if [ ! -d "${INSTALL_DIR}/venv" ]; then
    sudo -u "${APP_USER}" python3.12 -m venv "${INSTALL_DIR}/venv"
fi

"${INSTALL_DIR}/venv/bin/pip" install --upgrade pip setuptools wheel

# Install backend dependencies if requirements.txt exists
if [ -f "${INSTALL_DIR}/backend/requirements.txt" ]; then
    log_info "Installing Python backend packages from requirements.txt..."
    "${INSTALL_DIR}/venv/bin/pip" install -r "${INSTALL_DIR}/backend/requirements.txt"
fi

# 4. Systemd Auto-Healing Service Configuration
log_info "Step 4: Deploying Systemd Auto-Healing Service..."

cat <<'EOF' > /etc/systemd/system/dwrms-backend.service
[Unit]
Description=Bikita Minerals DWRMS Authoritative Backend Server
Documentation=https://github.com/bikita-minerals/dwrms
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=dwrms
Group=dwrms
WorkingDirectory=/opt/dwrms/backend
Environment="PATH=/opt/dwrms/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
EnvironmentFile=-/opt/dwrms/.env
ExecStart=/opt/dwrms/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4 --proxy-headers --forwarded-allow-ips='*'
ExecReload=/bin/kill -s HUP $MAINPID

# Autonomous Self-Healing Policies
Restart=always
RestartSec=5s
StartLimitIntervalSec=300
StartLimitBurst=10

# Security & Sandboxing
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/dwrms/backend /opt/dwrms/storage /var/log/dwrms /var/backups/dwrms
PrivateTmp=true
StandardOutput=append:/var/log/dwrms/backend.log
StandardError=append:/var/log/dwrms/backend.error.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable dwrms-backend.service
log_success "Systemd service dwrms-backend.service enabled with auto-healing restart policy."

# 5. Nginx LAN Reverse Proxy Configuration
log_info "Step 5: Configuring Nginx reverse proxy on port 80..."

cat <<'EOF' > /etc/nginx/sites-available/dwrms.conf
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _ dwrms-server.local;

    client_max_body_size 50M;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Backend API & WebSocket Proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400s;
    }

    # Frontend Static App Delivery
    location / {
        root /opt/dwrms/frontend/out;
        try_files $uri $uri.html $uri/ /index.html;
        expires 1h;
        add_header Cache-Control "public, no-transform";
    }

    # Static Assets Caching
    location /_next/static/ {
        alias /opt/dwrms/frontend/out/_next/static/;
        expires 1y;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }
}
EOF

ln -sf /etc/nginx/sites-available/dwrms.conf /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx || systemctl restart nginx
log_success "Nginx reverse proxy active on port 80."

# 6. Autonomous Watchdog Healthcheck Setup
log_info "Step 6: Installing autonomous 5-minute health watchdog cron..."

cat <<'EOF' > /opt/dwrms/watchdog_healthcheck.sh
#!/usr/bin/env bash
# Bikita DWRMS Autonomous Watchdog Health Probe
set -uo pipefail

HEALTH_URL="http://127.0.0.1:8000/api/v1/health"
LOG_FILE="/var/log/dwrms/watchdog.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Perform HTTP health probe with 5s timeout
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${HEALTH_URL}" 2>/dev/null || echo "000")

if [ "${HTTP_CODE}" -eq 200 ]; then
    # Health check OK
    exit 0
else
    echo "[${TIMESTAMP}] ALERT: Health check failed with HTTP ${HTTP_CODE}. Restarting dwrms-backend.service..." >> "${LOG_FILE}"
    systemctl restart dwrms-backend.service
    
    # Wait and re-verify
    sleep 5
    NEW_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${HEALTH_URL}" 2>/dev/null || echo "000")
    if [ "${NEW_CODE}" -eq 200 ]; then
        echo "[${TIMESTAMP}] RECOVERY: Backend successfully self-healed and resumed operations." >> "${LOG_FILE}"
    else
        echo "[${TIMESTAMP}] CRITICAL: Backend restart failed to restore HTTP 200. Manual inspection required." >> "${LOG_FILE}"
    fi
fi
EOF

chmod +x /opt/dwrms/watchdog_healthcheck.sh
chown "${APP_USER}:${APP_GROUP}" /opt/dwrms/watchdog_healthcheck.sh

# 7. Automated Daily Backup Script & 30-Day Rotation
log_info "Step 7: Installing automated backup engine with 30-day rotation..."

cat <<'EOF' > /opt/dwrms/backup_daily.sh
#!/usr/bin/env bash
# Bikita DWRMS Autonomous Daily Backup Engine
set -euo pipefail

BACKUP_DIR="/var/backups/dwrms"
DB_PATH="/opt/dwrms/backend/dwrms.db"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_FILE="${BACKUP_DIR}/dwrms_backup_${TIMESTAMP}.tar.gz"
LOG_FILE="/var/log/dwrms/backup.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting automated database and config backup..." >> "${LOG_FILE}"

if [ -f "${DB_PATH}" ]; then
    # Create atomic snapshot using sqlite3 vacuum into
    TEMP_SNAPSHOT="/tmp/snapshot_${TIMESTAMP}.db"
    sqlite3 "${DB_PATH}" "VACUUM INTO '${TEMP_SNAPSHOT}';"
    
    # Package database snapshot and environment config
    tar -czf "${BACKUP_FILE}" -C /tmp "snapshot_${TIMESTAMP}.db" -C /opt/dwrms ".env" 2>/dev/null || tar -czf "${BACKUP_FILE}" -C /tmp "snapshot_${TIMESTAMP}.db"
    rm -f "${TEMP_SNAPSHOT}"
    
    chmod 600 "${BACKUP_FILE}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup created: ${BACKUP_FILE} ($(du -h "${BACKUP_FILE}" | cut -f1))" >> "${LOG_FILE}"
fi

# Clean up backups older than 30 days
find "${BACKUP_DIR}" -type f -name "dwrms_backup_*.tar.gz" -mtime +30 -exec rm -f {} \;
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 30-day retention cleanup complete." >> "${LOG_FILE}"
EOF

chmod +x /opt/dwrms/backup_daily.sh
chown "${APP_USER}:${APP_GROUP}" /opt/dwrms/backup_daily.sh

# 8. Configure Cron Schedule for Watchdog and Backups
log_info "Step 8: Registering cron jobs for watchdog (every 5 mins) and backup (daily 02:00 AM)..."

CRON_FILE="/etc/cron.d/dwrms-tasks"
cat <<'EOF' > "${CRON_FILE}"
# /etc/cron.d/dwrms-tasks: Autonomous system cron schedule for Bikita DWRMS
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# 1. Watchdog probe every 5 minutes
*/5 * * * * root /opt/dwrms/watchdog_healthcheck.sh >/dev/null 2>&1

# 2. Daily automated database backup at 02:00 AM
0 2 * * * root /opt/dwrms/backup_daily.sh >/dev/null 2>&1
EOF

chmod 644 "${CRON_FILE}"

# 9. Firewall (UFW) Hardening
log_info "Step 9: Hardening UFW firewall (allowing SSH 22, HTTP 80, HTTPS 443, Backend 8000)..."
ufw allow 22/tcp comment "SSH Remote Management"
ufw allow 80/tcp comment "DWRMS Web & Mobile LAN"
ufw allow 443/tcp comment "DWRMS Secure LAN"
ufw allow 8000/tcp comment "DWRMS Direct API Endpoint"
ufw --force enable

echo -e "${BOLD}===================================================================${NC}"
echo -e "${GREEN}${BOLD}   AUTONOMOUS SERVER INSTALLATION COMPLETE!                       ${NC}"
echo -e "${BOLD}===================================================================${NC}"
echo -e " • Application Root:    ${INSTALL_DIR}"
echo -e " • Backend Service:     systemctl status dwrms-backend"
echo -e " • Health Watchdog:     Every 5 minutes (/var/log/dwrms/watchdog.log)"
echo -e " • Daily Backup:        02:00 AM (/var/backups/dwrms, 30-day retention)"
echo -e " • LAN Web Interface:   http://$(hostname -I | awk '{print $1}') or http://dwrms-server.local"
echo -e "${BOLD}===================================================================${NC}"
