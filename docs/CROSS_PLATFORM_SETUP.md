# Cross-Platform Setup Guide

**Bikita Minerals DWRMS — Linux & Windows Environment Setup**
*Version 2.10.0*

This document provides separate, detailed setup instructions for Linux (Ubuntu Server) and Windows environments. Choose the section matching your target platform.

---

## Part A: Linux Setup Guide (Ubuntu Server 22.04 / 24.04 LTS)

### A.1 Automated Server Installation (Production)

#### Prerequisites

- A clean Ubuntu Server 22.04 or 24.04 LTS installation (x86_64 or ARM64)
- Root or sudo access
- Network connectivity (for package downloads on first install)
- At least 4 CPU cores, 8 GB RAM, 50 GB disk

#### Step 1: Boot the Server and Log In

SSH into the server as the primary administrator:

```bash
ssh administrator@masvingo-srv-01.bikita.local
```

#### Step 2: Run the Master Installer

Two methods are available:

**Method A — Remote one-liner (fresh server with no repo clone):**

```bash
curl -fsSL https://raw.githubusercontent.com/Aomine-c2c/jbc/main/install.sh | sudo bash
```

**Method B — From a cloned repository:**

```bash
# Clone the repository
sudo git clone https://github.com/Aomine-c2c/jbc.git /opt/dwrms
cd /opt/dwrms

# Execute the installer
sudo chmod +x install.sh
sudo ./install.sh
```

#### Step 3: Installation Pipeline (7 Stages)

The `install.sh` script performs the following automatically:

1. **Source Verification** — Clones or syncs the repository to `/opt/dwrms`, creates symlinks.
2. **System Prerequisites** — Installs `ca-certificates`, `curl`, `gnupg`, `git`, `ufw`, `openssl`, `jq`, `cron`, `logrotate`, `python3-venv`, `python3-pip`, and more.
3. **Docker Installation** — Installs Docker CE, Docker Compose plugin, enables the Docker daemon, and adds the executing user to the `docker` group.
4. **Directory Structure** — Creates `/var/dwrms/storage/{job_cards,reports,fleet,signatures,temp}`, `/var/dwrms/backups`, `/var/dwrms/logs` with secure permissions. Sets up the host Python venv and global `ops` CLI symlink.
5. **Environment & TLS** — Generates a production `.env` with a cryptographically secure `SECRET_KEY`, database credentials, and CORS origins (auto-detecting LAN and Tailscale IPs). Creates self-signed TLS certificates.
6. **Database Initialization** — Starts PostgreSQL and Redis containers, runs `init_db_all.py`, `seed.py`, `seed_rbac.py`, and `seed_faker.py` for baseline data.
7. **Full Stack Launch** — Builds and starts all containers (backend, frontend, worker, beat, nginx) via `docker compose up -d --build`.
8. **Systemd Registration** — Installs systemd units: `dwrms.service` (auto-restart on boot), `dwrms-backup.timer` (daily 02:00), `dwrms-healthcheck.timer` (every 5 min), `dwrms-autoupdate.timer` (60s auto-pull).

#### Step 4: Verify Installation

```bash
# Check service status
systemctl status dwrms

# View container health
docker compose -f /opt/dwrms/infrastructure/docker-compose.prod.yml ps

# Run the health probe
ops health

# Check the version matrix
ops version
```

Expected output from `ops status`:

```text
  Platform:        Bikita Minerals DWRMS
  Version:         v2.10.0
  Environment:     PRODUCTION
  Host Node:       masvingo-srv-01 (Linux 6.x.x)
  Authoritative:   https://192.168.1.100

  Container Stack Status
  Service      Status              Ports
  nginx        Up (healthy)        0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
  frontend     Up (healthy)        3000/tcp
  backend      Up (healthy)        8000/tcp
  worker       Up                 
  beat         Up                 
  db           Up (healthy)         5432/tcp
  redis        Up (healthy)         6379/tcp
```

### A.2 SSH Hardening (Server Administration)

This project supports secure SSH-based administration. See [docs/SSH_SERVER_ADMINISTRATION.md](SSH_SERVER_ADMINISTRATION.md) for full details:

```bash
# 1. Generate Ed25519 key pair on your workstation
ssh-keygen -t ed25519 -C "admin@bikita.local" -f ~/.ssh/id_ed25519_dwrms

# 2. Add to workstation SSH config (~/.ssh/config)
cat >> ~/.ssh/config <<EOF
Host bikita-server
    HostName masvingo-srv-01.bikita.local
    User administrator
    IdentityFile ~/.ssh/id_ed5519_dwrms
    Port 22
    ServerAliveInterval 60
EOF

# 3. Connect
ssh bikita-server
```

### A.3 Optional Remote Mesh (Tailscale)

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Authenticate
sudo tailscale up --hostname=dwrms-server-masvingo --ssh

# Verify
tailscale ip -4
```

### A.4 Firewall Configuration

```bash
# UFW rules (auto-configured by install.sh)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    comment 'SSH Remote Management'
sudo ufw allow 80/tcp    comment 'HTTP Web Gateway'
sudo ufw allow 443/tcp   comment 'HTTPS Secure Gateway'
sudo ufw deny 3306/tcp   comment 'Block external MySQL'
sudo ufw deny 5432/tcp   comment 'Block external Postgres'
sudo ufw deny 6379/tcp   comment 'Block external Redis'
sudo ufw enable
```

---

## Part B: Windows Setup Guide

### B.1 Server Installation (WSL2 — Recommended for Windows)

Windows servers should run DWRMS inside **WSL2** (Windows Subsystem for Linux) with an Ubuntu distribution, mirroring the Linux setup above. This gives full compatibility with the `install.sh` script.

#### Step 1: Enable WSL2 and Install Ubuntu

```powershell
# Run in PowerShell as Administrator
wsl --install -d Ubuntu-24.04
```

Reboot when prompted. Launch Ubuntu from the Start Menu and create your UNIX username/password.

#### Step 2: Run the Linux Installer Inside WSL2

```bash
# Update packages
sudo apt update && sudo apt upgrade -y

# Install prerequisites
sudo apt install -y curl git

# Run the master installer
curl -fsSL https://raw.githubusercontent.com/Aomine-c2c/jbc/main/install.sh | sudo bash
```

Follow the same 7-stage pipeline as the Linux installation. Docker runs inside WSL2 (Docker Desktop must be installed separately on the Windows host).

#### Step 3: Port Forwarding (if needed)

WSL2 auto-forwards localhost ports. To access from the Windows host:
- Web: `http://localhost:3000`
- API: `http://localhost:8000`
- HTTPS: `https://localhost` (port 443)

### B.2 Desktop Client (Windows x64 — Development & Field Use)

The DWRMS desktop client is built with **Tauri** and produces native Windows installers.

#### Step 1: Install Development Prerequisites

| Tool | Download Link |
|:--|:--|
| **Node.js v20+** | https://nodejs.org/ |
| **Rust (stable)** | https://rustup.rs (install with default options) |
| **Visual C++ Build Tools** | https://visualstudio.microsoft.com/visual-cpp-build-tools/ (select "Desktop development with C++") |

Verify installations:

```powershell
node --version
npm --version
rustc --version
```

#### Step 2: Clone and Install Frontend

```powershell
git clone https://github.com/Aomine-c2c/jbc.git
cd jbc\frontend

# Install npm dependencies
npm ci
```

#### Step 3: Run Development Mode

```powershell
# Start backend + Next.js + Tauri desktop window concurrently
npm run tauri:dev
```

This launches:
- FastAPI backend on `http://localhost:8000`
- Next.js dev server on `http://localhost:3000`
- Tauri desktop window (native Windows app)

#### Step 4: Production Build (Packaging)

To create distributable Windows installers (`.exe` and `.msi`):

```powershell
# From the repository root
.\deploy\build-all-device-setups.ps1 -DevicePlatform desktop

# Or build only desktop packages
.\deploy\build-desktop-apps.ps1
```

This produces:
- `dist/desktop/DWRMS_2.10.0_x64-setup.exe` — NSIS installer (end-user install)
- `dist/desktop/DWRMS_2.10.0_x64_en-US.msi` — MSI installer (Active Directory/GPO rollout)

Verify package integrity:

```powershell
Get-FileHash -Path dist\desktop\* -Algorithm SHA256 | Format-Table -AutoSize
```

#### Step 5: Silent Installation (Enterprise/GPO)

```powershell
# Silent MSI install (Active Directory deploy)
msiexec /i dist\desktop\DWRMS_2.10.0_x64_en-US.msi /quiet /qn

# With logging
msiexec /i dist\desktop\DWRMS_2.10.0_x64_en-US.msi /quiet /qn /l*v dwrms_install.log
```

### B.3 Windows Service Installation (Backend)

For running the backend API as a Windows Service (without Docker):

#### Step 1: Install NSSM (Windows Service Manager)

Download `nssm.exe` from https://nssm.cc/download and place it in the `deploy/` directory.

#### Step 2: Run the Service Installer

```powershell
cd deploy
.\install_service.ps1
```

This installs:
- Service name: `DWRMS_API`
- Command: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
- Auto-start on boot
- Log files at `backend\logs\service.log` and `backend\logs\service-error.log`

#### Step 3: Manage the Service

```powershell
# Check status
Get-Service DWRMS_API

# Start / stop
Start-Service DWRMS_API
Stop-Service DWRMS_API

# Restart
Restart-Service DWRMS_API
```

### B.4 Windows Development — Docker Desktop

If you prefer running the full stack via Docker on Windows:

```powershell
# Install Docker Desktop for Windows: https://www.docker.com/products/docker-desktop

# Start Docker Desktop
# Then from the repository root:
docker compose -f infrastructure\docker-compose.yml up --build
```

The services will be accessible at:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

### B.5 Windows PowerShell Deployment Script

The `deploy/backup_db.ps1`, `deploy/restore_db.ps1`, and `deploy/startup_check.ps1` scripts provide Windows-compatible operational tooling:

```powershell
# Backup database
.\deploy\backup_db.ps1

# Restore database
.\deploy\restore_db.ps1

# Run startup verification
.\deploy\startup_check.ps1
```

---

## Part C: Environment Comparison

### C.1 Production Deployment Targets

| Aspect | Linux (Ubuntu Server) | Windows (WSL2 + Docker) | Windows (Native Tauri) |
|:---|:---|:---|:---|
| Host OS | Ubuntu 22.04/24.04 | Windows + WSL2 | Windows 10/11 x64 |
| Container Runtime | Docker CE | Docker Desktop | Docker Desktop (optional) |
| Database | PostgreSQL 16 | PostgreSQL 16 | SQLite / MySQL |
| Reverse Proxy | Nginx (port 80/443) | Nginx in container | N/A (dev) |
| Service Management | systemd | WSL2 systemd | Windows Service (NSSM) |
| Firewall | UFW | WSL2 network | Windows Firewall |
| Access Method | SSH (Ed25519) | SSH inside WSL2 | RDP / Desktop |

### C.2 Cross-Platform Access Matrix

All client platforms connect to the same backend API:

| Client | Platform | Connection Method | Notes |
|:---|:---|:---|:---|
| Tauri Desktop | Windows / Linux / macOS | Native `.exe` / `.msi` / `.deb` / `.AppImage` | Offline support, local storage |
| Web Browser | Any (Chrome, Edge, Firefox, Safari) | HTTPS via Nginx | Zero-install, full feature set |
| PWA | Android / iOS / Tablet | "Add to Home Screen" | Offline-first, IndexedDB sync |
| Mobile Web | Smartphone | Responsive mobile layout | Touch-optimized bottom navigation |

---

## Part D: Headless / Containerized Installation (Any OS)

For environments where you only need to run the platform without a desktop:

```bash
# 1. Clone and enter directory
git clone https://github.com/Aomine-c2c/jbc.git
cd jbc

# 2. Copy and configure environment
cp deploy/.env.production.example .env
# Edit .env with your production values

# 3. Start the full stack
docker compose -f infrastructure/docker-compose.prod.yml up -d --build

# 4. Initialize database (if first run)
docker compose -f infrastructure/docker-compose.prod.yml run --rm backend python init_db_all.py

# 5. Seed baseline data
docker compose -f infrastructure/docker-compose.prod.yml run --rm backend python seed.py
docker compose -f infrastructure/docker-compose.prod.yml run --rm backend python seed_rbac.py
docker compose -f infrastructure/docker-compose.prod.yml run --rm backend python seed_faker.py
```

Health endpoints are available at:
- `http://localhost/health` (HTTP)
- `http://localhost:8000/api/v1/health` (direct API)
- `http://localhost/readiness` (deep subsystem probe)
