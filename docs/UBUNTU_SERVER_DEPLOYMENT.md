# Ubuntu Server Production Deployment & Operations Guide (V1.9)

This manual provides authoritative procedures for deploying, configuring, monitoring, and operating the **Bikita Minerals Digital Work & Resource Management System (DWRMS)** on dedicated Ubuntu Server instances.

---

## 1. System Requirements & Architecture Stack

### Recommended Host Specifications

* **Operating System**: Ubuntu Server 22.04 LTS or 24.04 LTS (x86_64 / ARM64)
* **CPU**: 4+ Cores recommended for concurrent mining operations
* **RAM**: 8+ GB recommended for production with Redis & worker queues
* **Disk**: 50+ GB NVMe/SSD storage for database, document storage, and backups
* **Network**: Static IPv4 address or internal corporate DNS (e.g. `dwrms.bikita.com`)

### Service Topology

```text
Ubuntu Server (Host OS)
│
├── Nginx Reverse Proxy (:80, :443) ── TLS 1.2/1.3, Rate Limiting, Health & Static Cache
├── Next.js Web Application (:3000) ── Responsive Operations Portal & PWA
├── FastAPI Application Core (:8000) ── Authoritative Business Logic, Scoped RBAC, Storage
├── Celery Background Worker ────────── SMS dispatch, asynchronous actions
├── Celery Beat Scheduler ───────────── SLA escalation sweep (5m), storage purge (24h)
├── Relational Database (5432/3306) ─── PostgreSQL 16 / MySQL (Isolated internal network)
├── Redis 7 (6379) ──────────────────── Celery broker, caching, distributed locks
├── Storage Subsystem (/var/dwrms/storage) ── Attachment storage & validation
├── Logging Subsystem (/var/dwrms/logs) ───── Structured JSON logs with X-Request-ID
└── Disaster Recovery (/var/dwrms/backups) ── Daily snapshots (02:00 CAT)
```

---

## 2. Server Deployment Lifecycle (8-Stage Process)

The deployment orchestrator automates the complete operational lifecycle:

```text
[1. INSTALL] ➔ [2. CONFIGURE] ➔ [3. INITIALIZE DB] ➔ [4. RUN MIGRATIONS]
                                                                │
[8. VERIFY HEALTH] 🠤 [7. START SERVICES] 🠤 [6. CONFIGURE STORAGE] 🠤 [5. CREATE ADMIN]
```

### Automated Single-Command Deployment

```bash
# 1. Clone repository to server:
sudo git clone https://github.com/bikita-minerals/dwrms.git /opt/dwrms
cd /opt/dwrms

# 2. Execute production deployment script:
sudo chmod +x infrastructure/scripts/deploy_production.sh
sudo ./infrastructure/scripts/deploy_production.sh
```

---

## 3. Authoritative Platform Administration CLI (`ops`)

The **`ops`** command is installed globally at `/usr/local/bin/ops` (and available as `./ops` or `python manage.py`), providing a dedicated, structured administrative interface:

```bash
# View all available CLI commands:
ops --help

# 1. Interactive setup wizard:
ops setup

# 2. Real-time status of all containers and core subsystems:
ops status

# 3. Deep health and latency probe:
ops health

# 4. Filtered structured logs inspector:
ops logs -s app -n 50
ops logs -s error -n 100
ops logs -s backend -f

# 5. Non-sensitive system diagnostics report:
ops diagnostics
ops diagnostics --json

# 6. Disaster recovery snapshot creation and listing:
ops backup create --note "Pre-upgrade snapshot"
ops backup list
ops backup verify <archive_name>

# 7. Safe backup restoration with integrity check & confirmation:
ops restore <archive_name>

# 8. Emergency user management & role administration:
ops users list
ops users create-admin
ops users reset-password "user@bikita.com"
ops users deactivate "user@bikita.com"

# 9. Network topology and connectivity testing:
ops network

# 10. Server lifecycle management:
ops server start
ops server stop
ops server restart backend
ops server reload

# 11. Zero-downtime platform upgrade:
ops update
```

For the comprehensive command manual, see [docs/OPS_CLI_REFERENCE.md](file:///c:/Users/armut/404/job%20card/docs/OPS_CLI_REFERENCE.md).

---

## 4. Health, Readiness & Diagnostics Endpoints

### 1. Liveness Probe (`/health` or `/api/v1/health`)

Fast, non-blocking check verifying that the application process is running.

```bash
curl -k https://localhost/health
```

```json
{
  "status": "ok",
  "service": "Bikita Minerals DWRMS",
  "timestamp": "2026-08-28T14:00:00.000000Z"
}
```

### 2. Deep Readiness Probe (`/readiness` or `/api/v1/readiness`)

Evaluates all critical subsystem dependencies (Database latency, Redis ping, Storage write access). Returns HTTP `200 OK` when healthy, or HTTP `503 Service Unavailable` if degraded.

```bash
curl -k https://localhost/readiness
```

```json
{
  "status": "ready",
  "environment": "production",
  "version": "v1.9.0",
  "timestamp": "2026-08-28T14:00:00.000000Z",
  "services": {
    "database": {
      "status": "connected",
      "latency_ms": 1.42,
      "engine": "postgresql"
    },
    "redis": {
      "status": "connected",
      "latency_ms": 0.85
    },
    "storage": {
      "status": "healthy",
      "write_ok": true,
      "free_percentage": 34.2
    }
  }
}
```

### 3. Version Probe (`/version` or `/api/v1/version`)

Returns release version and operating environment.

```bash
curl -k https://localhost/version
```

### 4. Admin Diagnostics (`/api/v1/diagnostics`)

Protected diagnostic endpoint for authorized System Administrators providing CPU, memory metrics, database pool statistics, and storage health.

---

## 5. Logging, Correlation & Diagnostics

All logs are written to `/var/dwrms/logs` with structured JSON format and log rotation.

### Log Files

* `dwrms_app.log`: Application lifecycle, API requests, and audit logs.
* `dwrms_error.log`: Filtered error logs and uncaught exception tracebacks.
* `nginx/access.log`: Nginx access logs with request execution time and `req_id`.

### Request Correlation (`X-Request-ID`)

Every API request generates or accepts an `X-Request-ID` header. When an error occurs, clients receive:

```json
{
  "error": "INTERNAL_SERVER_ERROR",
  "detail": "An unexpected system error occurred. Please reference the request ID when reporting.",
  "request_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
}
```

Operators can immediately grep for the root cause in the server logs:

```bash
grep "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d" /var/dwrms/logs/dwrms_error.log
```

---

## 6. Restart Safety & Systemd Services

All containers and scheduled services are configured to survive unexpected server reboots:

* `dwrms.service`: Automatically starts the Docker multi-container stack on boot.
* `dwrms-backup.timer`: Executes automated daily snapshot backups at 02:00 CAT.
* `dwrms-healthcheck.timer`: Periodic watchdog that checks system readiness every 5 minutes.

### Service Management Commands

```bash
# Stack status:
systemctl status dwrms

# Restart stack:
systemctl restart dwrms

# View backup schedule:
systemctl list-timers | grep dwrms
```

---

## 7. Disaster Recovery & Backup Restoration

### Automated Daily Snapshots

Backups are archived in `/var/dwrms/backups/dwrms_backup_YYYYMMDD_HHMMSS.tar.gz` with a companion `.sha256` checksum file.

### Restoration Procedure

```bash
# 1. Stop active worker and API services:
sudo docker compose -f /opt/dwrms/docker-compose.prod.yml stop backend worker beat

# 2. Extract snapshot archive:
mkdir -p /tmp/restore
tar -xzf /var/dwrms/backups/dwrms_backup_YYYYMMDD_HHMMSS.tar.gz -C /tmp/restore

# 3. Restore PostgreSQL database:
docker compose -f /opt/dwrms/docker-compose.prod.yml exec -T db psql -U dwrms_prod -d dwrms < /tmp/restore/database.sql

# 4. Restore file storage:
cp -r /tmp/restore/storage/. /var/dwrms/storage/

# 5. Clean up temporary files and restart stack:
rm -rf /tmp/restore
sudo docker compose -f /opt/dwrms/docker-compose.prod.yml start backend worker beat

# 6. Verify system readiness:
curl -k https://localhost/readiness
```
