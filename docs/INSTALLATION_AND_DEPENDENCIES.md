# Installation & Dependency Management Guide

**Bikita Minerals DWRMS — Digital Work Request & Resource Management System**
*Version 2.10.0*

---

## 1. Overview

This guide provides step-by-step procedures for installing the DWRMS platform, managing dependencies, and configuring the system across all supported environments. Two installation paths are available:

| Path | Target | Description |
|:---|:---|:---|
| **Automated Server Install** | Ubuntu Server 22.04 / 24.04 LTS | One-command installation via `install.sh` — provisions Docker, firewall, TLS, database, and systemd services |
| **Manual Development Install** | Linux, Windows (WSL2), macOS | Per-component setup for local development and testing |

---

## 2. System Requirements

### 2.1 Minimum Hardware (Development)

| Component | Requirement |
|:---|:---|
| CPU | 2+ cores |
| RAM | 4 GB |
| Disk | 10 GB free |
| Network | Internet access for package downloads |

### 2.2 Recommended Hardware (Production)

| Component | Requirement |
|:---|:---|
| CPU | 4+ cores |
| RAM | 8+ GB |
| Disk | 50+ GB NVMe SSD |
| Network | Static IPv4 or internal DNS |

### 2.3 Software Dependencies (Server)

| Dependency | Minimum Version | Purpose |
|:---|:---|:---|
| Ubuntu Server | 22.04 / 24.04 LTS | Host operating system |
| Docker CE | 24.0+ | Container runtime |
| Docker Compose plugin | v2.20+ | Multi-container orchestration |
| OpenSSL | 3.0+ | TLS certificate generation |
| Python | 3.12+ | Backend & CLI runtime |
| curl | Any | One-liner download |
| jq | 1.6+ | JSON parsing in scripts |
| git | 2.30+ | Repository cloning |
| ufw | Any | Firewall management |
| cron / logrotate | Any | Scheduled backups & log rotation |

For optional remote connectivity:

| Dependency | Purpose |
|:---|:---|
| Tailscale | Mesh VPN transport (optional) |
| WireGuard | Alternative VPN transport (optional) |
| OpenSSH server | Secure administrative access (Tier 3) |
| Fail2ban | SSH intrusion prevention (optional) |

---

## 3. Automated Server Installation (Ubuntu)

### 3.1 One-Liner Installation (Remote Server)

```bash
curl -fsSL https://raw.githubusercontent.com/Aomine-c2c/jbc/main/install.sh | sudo bash
```

### 3.2 Local Repository Installation

```bash
# 1. Clone the repository
cd /tmp
git clone https://github.com/Aomine-c2c/jbc.git
cd jbc

# 2. Make the installer executable and run
sudo chmod +x install.sh
sudo ./install.sh
```

### 3.3 What `install.sh` Provisions

The installer executes a **7-stage provisioning pipeline**:

| Stage | Action | Details |
|:---|:---|:---|
| **1. Source Verification** | Repository clone or sync to `/opt/dwrms` | Creates symlinks for compose files, backend, and frontend |
| **2. System Prerequisites** | `apt-get install` | ca-certificates, curl, gnupg, lsb-release, git, ufw, openssl, jq, cron, logrotate, tar, rsync, python3-venv, python3-pip |
| **3. Docker & Compose** | Docker CE installation | Installs `docker-ce`, `docker-ce-cli`, `containerd.io`, `docker-compose-plugin`; enables Docker service; adds executing user to `docker` group |
| **4. Directories & Storage** | Filesystem layout | Creates `/var/dwrms/storage/{job_cards,reports,fleet,signatures,temp}`, `/var/dwrms/backups`, `/var/dwrms/logs` with permissions (`0750` storage, `0700` backups, `0755` logs). Sets up host Python venv for `ops` CLI. Installs global `/usr/local/bin/ops` symlink. |
| **5. Environment & TLS** | `.env` + certificates | Generates cryptographically secure `SECRET_KEY` (32-byte hex), database passwords. Auto-detects LAN IP and Tailscale IP for CORS. Creates self-signed TLS certificates via OpenSSL. |
| **6. Database & Services** | Docker stack startup | Starts DB + Redis containers; waits for health checks; runs `init_db_all.py`, `seed.py`, `seed_rbac.py`, `seed_faker.py`; launches full stack (backend, frontend, worker, beat, nginx) with `docker compose up -d --build` |
| **7. Systemd Services** | Service registration | Copies systemd unit/timer files: `dwrms.service` (auto-restart), `dwrms-backup.timer` (daily 02:00), `dwrms-healthcheck.timer` (every 5 min), `dwrms-autoupdate.timer` (60s auto-pull) |

### 3.4 Environment Variable Configuration

The installer generates `.env` at `/opt/dwrms/.env`. Key environment variables:

```ini
# Environment
ENVIRONMENT=production
DEBUG=false
APP_NAME="Bikita Minerals DWRMS"

# URLs
FRONTEND_URL=https://<HOST_LAN_IP>
NEXT_PUBLIC_API_URL=https://<HOST_LAN_IP>/api/v1
CORS_ORIGINS=https://localhost,http://localhost:3000,http://localhost:1420,tauri://localhost

# Database (PostgreSQL by default)
DB_ENGINE=postgresql
DB_HOST=db
DB_PORT=5432
DB_NAME=dwrms
DB_USER=postgres
DB_PASSWORD=<generated>

# Security
SECRET_KEY=<64-char hex>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Storage & Logs
STORAGE_PATH=/var/dwrms/storage
BACKUP_DIR=/var/dwrms/backups
LOG_DIR=/var/dwrms/logs
LOG_LEVEL=INFO
LOG_FORMAT=json

# Redis
REDIS_URL=redis://redis:6379/0

# Optional Remote Connectivity
DEPLOYMENT_MODE=LOCAL_ONLY
REMOTE_CONNECTIVITY_ENABLED=false
```

Templates for staging and production are provided:
- [`deploy/.env.example`](deploy/.env.example) — Full reference with all variables documented
- [`deploy/.env.production.example`](deploy/.env.production.example) — Production template
- [`deploy/.env.staging.example`](deploy/.env.staging.example) — Staging template

---

## 4. Dependency Management

### 4.1 Backend Dependencies (Python)

Dependencies are declared in [`backend/requirements.txt`](../backend/requirements.txt):

```
fastapi>=0.115.0
uvicorn[standard]==0.34.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.30.0
aiosqlite
pydantic>=2.9.0
pydantic-settings>=2.7.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart
celery>=5.4.0
redis>=5.0.0
alembic>=1.13.0
bcrypt>=4.0.0
aiomysql
cryptography
ldap3>=2.9.1
click>=8.1.0
psutil>=5.9.0
faker>=30.0.0
pytest>=8.0.0
pytest-asyncio>=0.24.0
httpx>=0.27.0
```

**Managing backend dependencies**:

```bash
# Activate virtual environment
cd backend
source .venv/bin/activate              # Linux/WSL
# .venv\Scripts\activate             # Windows

# Install all dependencies
pip install -r requirements.txt

# Upgrade all packages
pip install --upgrade -r requirements.txt

# Add a new dependency
pip install <package-name>
pip freeze > requirements.txt

# Verify installed packages
pip list
```

### 4.2 Frontend Dependencies (Node.js)

Dependencies are declared in [`frontend/package.json`](../frontend/package.json):

```bash
cd frontend

# Install dependencies (clean install from lockfile)
npm ci

# Add a new dependency
npm install <package-name>

# Add a dev dependency
npm install -D <package-name>

# Update all dependencies
npm update

# Check for outdated packages
npm outdated

# View dependency tree
npm ls
```

### 4.3 Version Pinning Strategy

| Environment | Strategy |
|:---|:---|
| Production | Exact pinned versions in `requirements.txt` and `package-lock.json` |
| Staging | Matches production pin set |
| Development | Allows `>=` ranges for flexibility; lockfile for reproducible installs |

### 4.4 Dependency Security

- Run `pip-audit` regularly on backend dependencies: `pip-audit -r requirements.txt`
- Run `npm audit` on frontend dependencies: `npm audit`
- Update lockfiles before every production deploy: `npm ci` + `pip install -r requirements.txt`

---

## 5. Manual Installation (Development)

### 5.1 Backend Manual Setup

```bash
# 1. Clone the repository
git clone https://github.com/Aomine-c2c/jbc.git
cd jbc/backend

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Copy environment template
cp ../deploy/.env.example .env
# Edit .env as needed (use SQLite for dev)

# 5. Initialize database
python init_db_all.py

# 6. Seed baseline data
python seed.py
python seed_rbac.py
python seed_faker.py

# 7. Start the backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5.2 Frontend Manual Setup

```bash
# 1. From project root
cd frontend

# 2. Install npm dependencies
npm ci

# 3. Copy environment (if needed)
# Next.js reads from .env.local, .env.development, etc.
# The API URL is configured via NEXT_PUBLIC_API_URL

# 4. Start development server
npm run dev
# Or for full Tauri dev loop:
npm run tauri:dev
```

### 5.3 Database Container (for local dev)

```bash
# Spin up PostgreSQL + Redis only
docker compose -f infrastructure/docker-compose.yml up -d db redis

# Then run backend locally with --reload
# (DATABASE_URL in .env should point to localhost or docker network)
```

---

## 6. Post-Installation Verification

### 6.1 Verify Docker Services

```bash
# Check running containers
docker compose -f infrastructure/docker-compose.prod.yml ps

# Check service health
docker compose -f infrastructure/docker-compose.prod.yml ps --services | while read svc; do
    echo -n "$svc: "
    docker compose -f infrastructure/docker-compose.prod.yml exec $svc curl -sf http://localhost:8000/api/v1/health || echo "unhealthy"
done
```

### 6.2 Verify Health Endpoints

```bash
# Liveness probe
curl -k https://localhost/health

# Readiness probe (deep subsystem check)
curl -k https://localhost/readiness

# Version endpoint
curl -k https://localhost/version

# Platform status
curl -k https://localhost/api/v1/platform/status
```

### 6.3 Verify Platform CLI

```bash
ops status
ops health
ops version
```

### 6.4 Default Credentials

| Role | Email | Password |
|:---|:---|:---|
| Administrator | `admin@bikita.com` | `password123` |
| Operator | `operator@bikita.com` | `password123` |
| Technician | `tech@bikita.com` | `password123` |
| Supervisor | `supervisor@bikita.com` | `password123` |
| Dept Manager | `mechmgr@bikita.com` | `password123` |
| Safety Officer | `safety@bikita.com` | `password123` |

> **Security note**: Change these credentials immediately after first login.

---

## 7. Uninstallation

### 7.1 Remove Production Installation

```bash
# 1. Stop all services
sudo systemctl stop dwrms
sudo systemctl disable dwrms
sudo systemctl disable dwrms-backup.timer
sudo systemctl disable dwrms-healthcheck.timer
sudo systemctl disable dwrms-autoupdate.timer

# 2. Stop and remove Docker containers
sudo docker compose -f /opt/dwrms/infrastructure/docker-compose.prod.yml down -v

# 3. Remove installation directory
sudo rm -rf /opt/dwrms

# 4. Remove data directories (WARNING: destroys all data)
sudo rm -rf /var/dwrms

# 5. Remove CLI
sudo rm -f /usr/local/bin/ops

# 6. Remove firewall rules (optional)
sudo ufw delete allow 80/tcp
sudo ufw delete allow 443/tcp
sudo ufw delete allow 22/tcp
```

### 7.2 Remove Docker & System Packages (optional)

```bash
sudo apt-get purge docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo apt-get autoremove -y
```

---

## 8. Troubleshooting Installation

### 8.1 Docker Not Found

```bash
# Verify Docker installation
docker --version
docker compose version

# If permission denied, add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Then re-login or restart session
```

### 8.2 Database Health Check Fails

```bash
# Check database container logs
docker compose -f infrastructure/docker-compose.prod.yml logs db

# Verify database connection
docker compose -f infrastructure/docker-compose.prod.yml exec db psql -U postgres -d dwrms -c "SELECT 1;"
```

### 8.3 Port Conflicts

```bash
# Check what's using port 80/443
sudo fuser 80/tcp
sudo lsof -i :80
sudo ss -tlnp | grep ':80'
```

### 8.4 Permission Denied on Storage

```bash
# Fix storage directory permissions
sudo chown -R 999:999 /var/dwrms/storage
sudo chmod -R 750 /var/dwrms/storage
```

---

## 9. Offline Installation

For air-gapped or offline environments:

1. Download all required packages on a connected machine:
   ```bash
   # Docker packages
   apt-get download docker-ce docker-ce-cli containerd.io docker-compose-plugin
   
   # Python wheels
   pip wheel -r requirements.txt -w ./wheels/
   
   # npm dependencies
   npm ci --prefer-offline --no-audit --no-fund
   ```

2. Transfer archives to the offline server.

3. Install Docker from downloaded `.deb` packages:
   ```bash
   sudo dpkg -i *.deb
   ```

4. Install Python dependencies from wheels:
   ```bash
   pip install --no-index --find-links ./wheels/ -r requirements.txt
   ```

5. Run `install.sh` — it will detect existing Docker and Python installations.

---

## 10. Environment Configuration Reference

### 10.1 Production `.env` Template

```ini
# BIKITA MINERALS DWRMS — PRODUCTION ENVIRONMENT
ENVIRONMENT=production
DEBUG=false
APP_NAME="Bikita Minerals DWRMS"
APP_VERSION=v2.10.0

# Authoritative URLs
FRONTEND_URL=https://dwrms.bikita.com
NEXT_PUBLIC_API_URL=https://dwrms.bikita.com/api/v1
CORS_ORIGINS=https://dwrms.bikita.com,tauri://localhost,http://tauri.localhost

# Database (PostgreSQL)
DB_ENGINE=postgresql
DB_HOST=db
DB_PORT=5432
DB_NAME=dwrms
DB_USER=dwrms_user
DB_PASSWORD=<strong_password>
DATABASE_URL=postgresql+asyncpg://dwrms_user:<strong_password>@db:5432/dwrms

# Security — Generate with: openssl rand -hex 32
SECRET_KEY=<64_char_hex_string>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis & Celery
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Storage & Logs
STORAGE_PATH=/var/dwrms/storage
BACKUP_DIR=/var/dwrms/backups
LOG_DIR=/var/dwrms/logs
LOG_LEVEL=INFO
LOG_FORMAT=json
MAX_UPLOAD_SIZE_MB=50

# Optional Remote Connectivity
DEPLOYMENT_MODE=HYBRID_REMOTE
REMOTE_CONNECTIVITY_ENABLED=true
REMOTE_NETWORK_PROVIDER=tailscale
REMOTE_NETWORK_INTERFACE=tailscale0
REMOTE_NETWORK_HOSTNAME=dwrms-server.bikita.ts.net
REMOTE_NETWORK_IP=100.x.y.z

# Versioning
MIN_SUPPORTED_CLIENT_VERSION=v2.0.0
UPDATE_CHANNEL=enterprise_lts
```
