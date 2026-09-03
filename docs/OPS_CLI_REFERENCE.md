# Bikita Minerals DWRMS — Platform Administration CLI (`ops`) Reference Manual (V2.2)

The **`ops`** command is the unified technical administration and operations interface for the **Bikita Minerals Digital Work & Resource Management System (DWRMS)**.

Installed globally on Ubuntu Server at `/usr/local/bin/ops` (or accessible via `./ops` / `python manage.py`), it replaces disparate scripts with a structured, hardened, and SSH-friendly command-line suite.

---

## 1. Global Usage & Flags

```bash
ops [OPTIONS] COMMAND [ARGS]...

Options:
  --version     Show platform version (v2.2.0)
  -h, --help    Show help message and exit
```

---

## 2. Command Index

| Command | Summary | Key Options / Arguments |
| :--- | :--- | :--- |
| **`ops setup`** | Interactive first-time server setup wizard | `--non-interactive`, `--force` |
| **`ops install`** | Installs system packages, firewall rules, directories & systemd | `--skip-docker`, `--skip-firewall` |
| **`ops configure`** | Inspect, get, set, and validate environment settings | `list`, `get <key>`, `set <k> <v>`, `validate` |
| **`ops status`** | Consolidated real-time status (App, API, DB, Worker, Storage, Backup) | — |
| **`ops health`** | Deep latency & readiness probe (Database, Redis, Storage, Gateway) | `--timeout <sec>` |
| **`ops logs`** | Tail, search, and filter structured logs with correlation IDs | `-s <service>`, `-n <lines>`, `-f`, `-l <level>`, `-q <search>`, `--request-id <id>` |
| **`ops diagnostics`** | Safe non-sensitive system telemetry report (Text or JSON) | `--json` |
| **`ops backup`** | Create, list, and verify SHA-256 disaster recovery snapshots | `create`, `list`, `verify <archive>`, `prune` |
| **`ops restore`** | Restore database & storage with integrity check and confirmation | `<archive>`, `-y`, `--skip-storage` |
| **`ops users`** | Emergency user administration, role assignment & password reset | `list`, `create-admin`, `reset-password`, `activate`, `deactivate` |
| **`ops network`** | Inspect network interfaces, ports, CORS, and DNS reachability | — |
| **`ops server`** | Stack lifecycle orchestrator (Docker & background workers) | `start`, `stop`, `restart [svc]`, `reload`, `ps` |
| **`ops update`** | Upgrade platform, run schema migrations, and reload containers | `matrix`, `check`, `apply`, `rollback` |
| **`ops version`** | Display platform version, database engine, schema, and environment | — |

---

## 3. Command Reference & Examples

### 3.1 `ops setup`

Launches the structured 8-stage server setup and configuration process:

1. **STEP 1 — Platform Configuration**: Organization name, installation/mine site name, server node identifier, environment (`production`/`staging`/`development`), timezone.
2. **STEP 2 — Network Configuration**: Primary server URL, domain name, local LAN IP, HTTPS/TLS encryption mode, trusted CORS origins (no fixed public IP required).
3. **STEP 3 — Database Pre-Flight & Credentials**: Engine (`postgresql`/`mysql`/`sqlite`), Host, Port, Name, Username, Password with **live async connection testing before proceeding**.
4. **STEP 4 — Initial Administrator Account**: Email, Name, Department, and Password with complexity validation.
5. **STEP 5 — File Storage Subsystem**: Attachment storage path, permissions probe, and disk capacity verification.
6. **STEP 6 — Backups & Disaster Recovery**: Backup location, frequency (daily/weekly/hourly), retention policy (days).
7. **STEP 7 — Optional Remote Connectivity**: Network access mode (Local LAN only, Corporate VPN/Proxy, Optional Tailscale Mesh Network). Independent SSH server administration on port 22.
8. **STEP 8 — System Verification & Finalization**: Executes migrations, seeds mining roles, provisions administrator, locks setup (`SETUP_COMPLETED=true`), and displays completion report.

```bash
# Interactive 8-stage wizard:
ops setup

# Non-interactive automated deployment:
ops setup --non-interactive

# Force re-configuration:
ops setup --force
```

---

### 3.2 `ops status`

Displays real-time operational status for all containers and services:

```bash
ops status
```

```text
======================================================================
  BIKITA MINERALS DWRMS -- PLATFORM STATUS
======================================================================
Platform Identity
  Platform:        Bikita Minerals DWRMS
  Version:         v2.0.0
  Environment:     production
  Host Node:       masvingo-srv-01 (Linux 5.15.0-105-generic)
  Authoritative:   https://dwrms.bikita.com

Container Stack Status (Docker Compose)
Service      Status              Ports
---------    ------------------  -----------------------
nginx        Up (healthy)        0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
frontend     Up (healthy)        3000/tcp
backend      Up (healthy)        8000/tcp
worker       Up                  
beat         Up                  
db           Up (healthy)        5432/tcp
redis        Up (healthy)        6379/tcp

--- Authoritative Core Subsystems ---
Component            Target / Engine       Operational State                   
-------------------  --------------------  ------------------------------------
Relational Database  POSTGRESQL            ONLINE (Connected)                  
Redis Broker         In-Memory Broker      ONLINE (Responding)                 
Storage Subsystem    /var/dwrms/storage    HEALTHY (140.5 GB free, 29.6% free)
```

---

### 3.3 `ops health`

Runs a deep readiness probe testing millisecond round-trip latencies:

```bash
ops health
```

```text
======================================================================
  DWRMS DEEP HEALTH & READINESS PROBE
======================================================================
Subsystem          Target            Latency / Metric      Health State            
-----------------  ----------------  --------------------  ------------------------

  [OK] ALL CRITICAL SUBSYSTEMS ARE OPERATIONAL (Exit Code 0)
```

---

### 3.4 `ops configure`

Inspect and update configuration safely with automatic credential masking:

```bash
# List all configuration settings (passwords and secret keys masked as ******):
ops configure list

# Show plaintext secrets (authorized administrator only):
ops configure list --show-secrets

# Retrieve a single setting:
ops configure get ENVIRONMENT

# Update a setting in .env:
ops configure set MAX_UPLOAD_SIZE_MB 50

# Audit configuration integrity:
ops configure validate
```

---

### 3.5 `ops logs`

Inspects, searches, and streams structured logs:

```bash
# View last 50 application logs:
ops logs -s app -n 50

# View only error logs:
ops logs -s error -n 100

# Stream logs in real time:
ops logs -s backend -f

# Filter by log level:
ops logs -s app -l ERROR

# Search for a specific request ID or error term:
ops logs -s app --request-id 9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d
ops logs -s app -q "database connection"
```

---

### 3.6 `ops backup` & `ops restore`

#### Backup Creation & Verification

```bash
# Create an on-demand full snapshot (Database + Attachments + Metadata + SHA-256):
ops backup create --note "Pre-upgrade snapshot"

# List all available snapshots:
ops backup list

# Verify archive integrity and SHA-256 checksum:
ops backup verify dwrms_backup_20260828_121912.tar.gz
```

#### Safe Restoration Runbook

Restoring overwrites active data and requires explicit confirmation:

```bash
# Interactive restore:
ops restore dwrms_backup_20260828_121912.tar.gz

# Automated restore with pre-confirmation:
ops restore dwrms_backup_20260828_121912.tar.gz -y
```

---

### 3.7 `ops users`

Emergency user administration and role management:

```bash
# List all registered users, departments, and active statuses:
ops users list

# Filter users by department:
ops users list --department "Mining Operations"

# Create a new System Administrator:
ops users create-admin --email "supervisor@bikita.com" --first-name "Tendai" --last-name "Moyo"

# Emergency password reset:
ops users reset-password "operator@bikita.com"

# Deactivate a compromised or departed account:
ops users deactivate "compromised_user@bikita.com"

# Re-activate an account:
ops users activate "operator@bikita.com"
```

---

### 3.8 `ops network`

Examines network interfaces, CORS policies, DNS resolution, and port reachability:

```bash
ops network
```

---

### 3.9 `ops diagnostics`

Collects non-sensitive telemetry useful for troubleshooting tickets and support:

```bash
# Formatted text table:
ops diagnostics

# Export raw JSON for attachments or automated monitoring:
ops diagnostics --json > /tmp/dwrms_diag_$(date +%s).json
```

---

### 3.10 `ops server` & `ops update`

Stack lifecycle management:

```bash
# Start all containers:
ops server start

# Stop all containers (with confirmation):
ops server stop

# Restart a specific service:
ops server restart backend
ops server restart worker

# Reload containers after .env edits:
ops server reload

# Check running container processes:
ops server ps

# Upgrade platform: pull repo, build containers, run migrations, and reload:
ops update
```

---

### 3.11 `ops version`

Displays full authoritative platform build metadata, database engine, schema version, release channel, and environment:

```bash
ops version
```

```text
======================================================================
  BIKITA MINERALS DWRMS -- PLATFORM VERSION
======================================================================
  Application:       Bikita Minerals DWRMS
  Platform Version:  v2.2.0
  API Version:       v1
  Database Engine:   MYSQL
  Database Schema:   2026.08.28.01
  Environment:       PRODUCTION
  Release Channel:   enterprise_lts
  Min Client:        v2.0.0
```

---

## 4. Security & Remote Administration Guidelines

1. **Least Privilege**: `ops install`, `ops server start/stop`, and `ops restore` require appropriate host permissions (`sudo`).
2. **Credential Redaction**: `ops configure list` and `ops diagnostics` redact sensitive secrets (`SECRET_KEY`, `DB_PASSWORD`, `POSTGRES_PASSWORD`, `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD`, `JWT_SECRET`).
3. **SSH Remote Administration**: All commands format output using clean ASCII tables that render across PuTTY, OpenSSH, and Windows Terminal.
