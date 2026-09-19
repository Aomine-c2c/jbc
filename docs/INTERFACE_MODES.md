# Interface Modes Guide

**Bikita Minerals DWRMS — GUI, CLI, TUI, and Text-Based Interface Usage**
*Version 2.10.0*

This document covers all interface modes available for interacting with the DWRMS platform, including the web GUI, the `ops` CLI, the interactive TUI monitor, Docker commands, and non-interactive automation.

---

## 1. Interface Mode Overview

The DWRMS platform provides multiple interface modes for different operational needs:

| Interface Mode | Command Entry Point | Target Users | Description |
|:---|:---|:---|:---|
| **Web GUI** | Browser (`https://<host>`) | End-users (all roles) | Full graphical web application via Nginx → Next.js |
| **Tauri Desktop** | Native application (`.exe` / `.msi`) | Desktop users | Native Tauri wrapper embedding the web UI |
| **CLI (`ops`)** | `ops <command>` | Server admins, DevOps | Text-based administrative interface (Click/Python) |
| **TUI Monitor** | `ops monitor` | Server admins, DevOps | Interactive terminal dashboard with real-time telemetry |
| **Docker Compose** | `docker compose ...` | Server admins | Direct container lifecycle management |
| **HTTP API** | `curl` / `http` / Postman | Developers, integrators | Direct REST API interaction via HTTP |
| **SSH** | `ssh bikita-server` | Server admins | Secure shell access to the host OS |

---

## 2. Web Graphical Interface (GUI)

### 2.1 Access

The web application is served via Nginx reverse proxy:

```
https://<server-lan-ip>          (HTTPS via Nginx)
http://<server-lan-ip>:80         (HTTP, redirects to HTTPS)
https://<server-lan-ip>:8000      (direct FastAPI, dev only)
```

### 2.2 Role-Based Navigation

Each of the 6 roles has a designated landing hub:

| Role | Landing Route | Key Features |
|:---|:---|:---|
| **Operator / Driver** | `/my-work` | Fault logging, pre-start inspections, hazard alerts |
| **Technician / Artisan** | `/my-work` | LOTO isolation, live labor timer, spares requisitions |
| **Supervisor / Shift Boss** | `/dashboard` | Shift Kanban, dispatch artisans, QA verification |
| **Dept Manager / Superintendent** | `/dashboard` | Multi-tier approvals, SLA governance, formal closure |
| **Safety Officer (HSE)** | `/dashboard` | Immutable audit stream, LOTO compliance, safety dashboards |
| **Administrator** | `/dashboard` | Full system access, telemetry, backups, org structure |

### 2.3 Desktop Client (Tauri)

The native Windows desktop client is installed via:

```powershell
# Silent install (Active Directory / SCCM)
msiexec /i dist\desktop\DWRMS_2.10.0_x64_en-US.msi /quiet /qn

# Or interactive install
dist\desktop\DWRMS_2.10.0_x64-setup.exe
```

Upon first launch, configure the server connection profile:
1. Click the **Connection Status Badge** in the top navigation header.
2. Select or create a **Connection Profile**:
   - **Central Server**: `https://dwrms.bikita.com`
   - **Plant LAN**: `http://192.168.10.50:8000`
   - **Tailscale Field Mesh**: `http://100.x.y.z:8000`
3. Click **"Test Connection"** to verify latency and health.

### 2.4 Mobile / PWA Client

On a mobile device or tablet:
1. Navigate to the app URL in Chrome/Safari.
2. **iOS**: Tap Share → "Add to Home Screen".
3. **Android**: Tap Menu (⋮) → "Add to Home Screen" or "Install App".
4. The PWA launches in standalone fullscreen mode with touch-optimized bottom navigation.

---

## 3. Command-Line Interface (`ops`)

The `ops` command is the unified administrative interface, installed globally at `/usr/local/bin/ops` on production servers.

### 3.1 Installation

```bash
# On production server (installed by install.sh)
sudo ln -sf /opt/dwrms/scripts/ops/ops /usr/local/bin/ops
sudo chmod +x /usr/local/bin/ops

# On Windows
# ops.ps1 is available in scripts/ops/ops.ps1
# Or use ops.bat for batch execution
```

### 3.2 Global Flags

```bash
ops --version
ops --help
ops -h
```

### 3.3 Command Reference

#### `ops setup` — First-Time Server Setup Wizard

```bash
# Interactive 8-stage wizard
ops setup

# Non-interactive (uses existing .env)
ops setup --non-interactive

# Force re-configuration
ops setup --force
```

**Wizard stages**:
1. Organization & site configuration
2. Server identity & network endpoints
3. Database pre-flight & credentials (with live async connection test)
4. Initial administrator account
5. File storage subsystem
6. Backups & disaster recovery
7. Optional remote connectivity (Tailscale/WireGuard)
8. System verification & finalization

#### `ops status` — Real-Time Platform Status

```bash
ops status
```

Displays: platform identity, container stack status, database connectivity, Redis broker, storage subsystem, and backup status.

#### `ops health` — Deep Health & Readiness Probe

```bash
ops health
ops health --timeout 30
```

Tests millisecond round-trip latencies for:
- Database connection (PostgreSQL 16)
- Redis broker ping
- Storage write access
- API gateway responsiveness

#### `ops logs` — Structured Log Browser

```bash
# View last 50 application logs
ops logs -s app -n 50

# View only errors
ops logs -s error -n 100

# Stream logs in real time
ops logs -s backend -f

# Filter by log level
ops logs -s app -l ERROR

# Search by request ID or keyword
ops logs -s app --request-id 9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d
ops logs -s app -q "database connection"
```

**Options**:
| Flag | Description |
|:---|:---|
| `-s, --service` | Filter by service: `app`, `error`, `backend`, `nginx`, `worker`, `db` |
| `-n, --lines` | Number of log lines (default: 50) |
| `-f, --follow` | Stream logs in real-time |
| `-l, --level` | Filter by level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `-q, --query` | Search for keyword in log messages |
| `--request-id` | Filter by X-Request-ID for correlation tracing |
| `--json` | Output raw JSON log entries |

#### `ops diagnostics` — System Telemetry Report

```bash
# Formatted text table
ops diagnostics

# Raw JSON for monitoring systems
ops diagnostics --json > /tmp/dwrms_diag.json
```

Collects non-sensitive telemetry: CPU, memory, disk, Docker container status, database pool stats, network interfaces, and CORS configuration. All secrets are redacted.

#### `ops configure` — Environment Configuration

```bash
# List all configuration (secrets masked)
ops configure list

# Show secrets (authorized admin only)
ops configure list --show-secrets

# Get a single setting
ops configure get ENVIRONMENT

# Update a setting in .env
ops configure set MAX_UPLOAD_SIZE_MB 50

# Validate configuration integrity
ops configure validate

# Validate with fix mode
ops configure validate --fix
```

#### `ops backup` — Disaster Recovery Snapshots

```bash
# Create on-demand snapshot
ops backup create --note "Pre-maintenance snapshot"

# List all archives
ops backup list

# Verify archive integrity (SHA-256)
ops backup verify dwrms_backup_20260828_121912.tar.gz

# Prune old archives
ops backup prune --retention-days 30

# Create encrypted backup
ops backup create --encrypted
```

#### `ops restore` — Safe Backup Restoration

```bash
# Interactive restore
ops restore dwrms_backup_20260828_121912.tar.gz

# Automated with pre-confirmation
ops restore dwrms_backup_20260828_121912.tar.gz -y

# Restore database only (skip storage files)
ops restore dwrms_backup_20260828_121912.tar.gz --skip-storage

# Restore as safety snapshot before restore
ops restore dwrms_backup_20260828_121912.tar.gz --pre-snapshot
```

> **Safety**: Restores create a `dwrms_prerestore_safety_*.tar.gz` snapshot before modifying any existing data.

#### `ops users` — Emergency User Management

```bash
# List all users
ops users list

# Filter by department
ops users list --department "Mining Operations"

# Create system administrator
ops users create-admin --email "supervisor@bikita.com" --first-name "Tendai" --last-name "Moyo"

# Reset password
ops users reset-password "operator@bikita.com"

# Deactivate account
ops users deactivate "compromised_user@bikita.com"

# Re-activate
ops users activate "operator@bikita.com"
```

#### `ops network` — Network & Connectivity Inspection

```bash
ops network
ops network --json
```

Displays: LAN IP, Tailscale IP, MagicDNS, CORS origins, DNS resolution, port reachability, and deployment mode.

#### `ops server` — Stack Lifecycle Management

```bash
# Start all containers
ops server start

# Start with image rebuild
ops server start --build

# Stop all containers (with confirmation)
ops server stop
ops server stop -y

# Restart all or specific service
ops server restart            # restart all
ops server restart backend    # restart one service
ops server restart worker

# Reload configuration (zero-downtime)
ops server reload

# List running containers
ops server ps
```

#### `ops update` — Platform Update Management

```bash
# Show version matrix
ops update matrix

# Check for available updates
ops update check

# Apply update (8-step controlled pipeline)
ops update apply

# Non-interactive apply
ops update apply -y

# Rollback to pre-upgrade snapshot
ops update rollback
ops update rollback -y
```

#### `ops monitor` — Interactive Real-Time TUI

```bash
ops monitor
```

Launches a full-screen terminal dashboard showing:
- Dual IP access endpoints (LAN + Tailscale)
- Host hardware telemetry (CPU, RAM, disk with bar graphs)
- Docker Compose container stack status
- Automated update system (1-min cadence)
- Recent operations log telemetry

**TUI keyboard controls**:
| Key | Action |
|:---|:---|
| `q` | Quit monitor |
| `r` | Force refresh |
| `u` | Check for upstream updates (git fetch) |
| `l` | View full logs (docker compose logs) |

### 3.4 CLI Command Index

| Command | Summary |
|:---|:---|
| `ops --version` | Show platform version |
| `ops setup` | First-time server setup wizard |
| `ops install` | Install system packages & firewall |
| `ops configure list/get/set/validate` | Environment configuration |
| `ops status` | Real-time platform status |
| `ops health` | Deep subsystem health probe |
| `ops logs` | Structured log browser |
| `ops diagnostics` | System telemetry report |
| `ops backup create/list/verify/prune` | Backup management |
| `ops restore` | Safe backup restoration |
| `ops users list/create-admin/reset-password` | User management |
| `ops network` | Network & CORS inspection |
| `ops server start/stop/restart/reload/ps` | Container lifecycle |
| `ops update matrix/check/apply/rollback` | Version management |
| `ops monitor` | Interactive TUI dashboard |
| `ops version` | Platform version details |

---

## 4. Docker Compose Interface

The container stack is managed via Docker Compose. The `ops` CLI delegates to these commands internally.

### 4.1 Production Compose

```bash
# Project directory
cd /opt/dwrms

# Compose file
COMPOSE_FILE=infrastructure/docker-compose.prod.yml
ENV_FILE=.env

# Start
docker compose -f $COMPOSE_FILE --env-file $ENV_FILE up -d --build

# Stop
docker compose -f $COMPOSE_FILE --env-file $ENV_FILE down

# Restart specific service
docker compose -f $COMPOSE_FILE restart backend

# View logs
docker compose -f $COMPOSE_FILE logs -f backend

# Rebuild without cache
docker compose -f $COMPOSE_FILE build --no-cache

# Scale workers
docker compose -f $COMPOSE_FILE up -d --scale worker=4
```

### 4.2 Development Compose

```bash
cd /project-root

# Development stack (PostgreSQL, Redis, backend with reload, frontend)
docker compose -f infrastructure/docker-compose.yml up --build

# Backend auto-initializes DB and seeds demo data
```

### 4.3 Compose File Variants

| File | Environment | Description |
|:---|:---|:---|
| `infrastructure/docker-compose.yml` | Development | Mounts source code, auto-init DB, live reload |
| `infrastructure/docker-compose.prod.yml` | Production | Hardened, health-checked, persistent volumes |
| `infrastructure/docker-compose.staging.yml` | Staging | Mirrors production with staging ports (8080/8443) |
| `deploy/docker-compose.server.yml` | Production (deploy tool) | Parameterized for remote deployment |

---

## 5. HTTP API Interface

### 5.1 Direct API Access

The REST API is available at `/api/v1/`. For production, access via Nginx (HTTPS):

```
https://<server>/api/v1/...
```

For development, direct access:

```
http://localhost:8000/api/v1/...
```

### 5.2 Health & Diagnostics Endpoints

```bash
# Liveness probe (fast, < 10ms)
curl -k https://localhost/health
curl -k https://localhost/api/v1/health

# Readiness probe (deep subsystem check)
curl -k https://localhost/readiness
curl -k https://localhost/api/v1/readiness

# Version endpoint
curl -k https://localhost/version
curl -k https://localhost/api/v1/version

# Platform info (public)
curl -k https://localhost/api/v1/info

# Admin diagnostics (requires admin auth)
curl -k -H "Authorization: Bearer <token>" \
  https://localhost/api/v1/diagnostics
```

### 5.3 Authentication

```bash
# Login
curl -k -X POST https://localhost/api/v1/iam/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@bikita.com","password":"password123"}' \
  -c cookies.txt

# Use session cookie for subsequent requests
curl -k -b cookies.txt https://localhost/api/v1/iam/users
```

### 5.4 API Documentation

- **Swagger UI**: `http://localhost:8000/api/docs` (development only — disabled in production)
- **ReDoc**: `http://localhost:8000/api/redoc` (development only — disabled in production)

The authoritative API reference is in [`docs/API_OPERATIONS_MANUAL.md`](API_OPERATIONS_MANUAL.md).

---

## 6. SSH Administration Interface

### 6.1 Connecting via SSH

```bash
# With SSH config (~/.ssh/config)
ssh bikita-server

# Direct connection
ssh administrator@masvingo-srv-01.bikita.local
```

### 6.2 SSH-Based Remote Commands (Non-Interactive)

```bash
# Remote health check
ssh administrator@masvingo-srv-01.bikita.local "ops health"

# Remote snapshot creation
ssh administrator@masvingo-srv-01.bikita.local "ops backup create --note 'Automated Nightly' --json"

# Remote log inspection
ssh administrator@masvingo-srv-01.bikita.local "ops logs -s app -n 100 --level ERROR"

# Remote container status
ssh administrator@masvingo-srv-01.bikita.local "ops server ps"
```

### 6.3 systemd Service Management via SSH

```bash
# Check dwrms service status
ssh administrator@masvingo-srv-01.bikita.local "systemctl status dwrms"

# Restart platform
ssh administrator@masvingo-srv-01.bikita.local "sudo systemctl restart dwrms"

# View backup schedule
ssh administrator@masvingo-srv-01.bikita.local "systemctl list-timers | grep dwrms"

# Check auto-update timer
ssh administrator@masvingo-srv-01.bikita.local "systemctl status dwrms-autoupdate.timer"
```

---

## 7. Non-Interactive / Automation Usage

### 7.1 Using `manage.py`

The repository root contains a `manage.py` entrypoint that delegates to the same CLI:

```bash
# Equivalent to 'ops' commands
python manage.py status
python manage.py health
python manage.py backup list
python manage.py version
```

### 7.2 Windows PowerShell CLI

On Windows, use the PowerShell wrapper:

```powershell
# scripts/ops/ops.ps1
.\scripts\ops\ops.ps1 status
.\scripts\ops\ops.ps1 health
.\scripts\ops\ops.ps1 logs -Service app -Lines 50
```

### 7.3 CI/CD Integration

The GitHub Actions workflows use non-interactive patterns:

```yaml
# Backend CI (.github/workflows/backend.yml)
- run: pip install -r requirements.txt
- run: pytest

# Frontend CI (.github/workflows/main.yml)
- run: npm ci
- run: npm run lint
- run: npm run test

# CD (.github/workflows/deploy.yml)
- run: docker compose up -d --build
- run: docker exec dwrms-backend-1 python init_db_all.py
```

---

## 8. Interface Accessibility

### 8.1 TUI Monitor Key Bindings

| Key | Action | Notes |
|:---|:---|:---|
| `q` / `Q` | Quit the monitor | Exits cleanly, restores terminal |
| `r` | Force refresh | Re-renders the dashboard immediately |
| `u` | Check for upstream updates | Runs `git fetch` and shows status |
| `l` | View full container logs | Opens `docker compose logs` in current terminal |

### 8.2 Terminal Encoding

The CLI is designed for cross-terminal compatibility:
- **PuTTY**: Works with default UTF-8 settings
- **OpenSSH**: Full Unicode support (box-drawing characters)
- **Windows Terminal**: Native UTF-8 support
- **tmux/screen**: Compatible with 256-color terminals

### 8.3 Output Formats

Most `ops` subcommands support structured output:

```bash
ops status --json        # JSON output
ops health --json        # JSON format
ops diagnostics --json   # Machine-readable telemetry
ops backup list --json   # JSON backup inventory
```

---

## 9. Interface Mode Comparison

| Mode | Best For | Authentication | Offline Support |
|:---|:---|:---|:---|
| **Web GUI** | Daily operations, all user roles | JWT bearer token + HttpOnly cookie | Limited (PWA offline via IndexedDB) |
| **Tauri Desktop** | Offline field work, shop floor | Local token storage | Full offline draft + sync |
| **`ops` CLI** | Server administration, automation | SSH key + sudo | N/A (server-side) |
| **TUI Monitor** | Live monitoring, incident response | SSH session | Real-time only |
| **Docker Compose** | Container management | Docker socket | N/A |
| **HTTP API** | Integrations, scripts | JWT bearer token | Via API client retry logic |
| **SSH** | OS-level administration | Public key auth | N/A |
