# Version Upgrade Procedures Guide

**Bikita Minerals DWRMS — Seamless Platform Upgrades & Database Migrations**
*Version 2.10.0*

This document describes the structured procedures for upgrading the DWRMS platform from one release to another, managing database schema migrations, and rolling back in case of issues.

---

## 1. Version Matrix

The DWRMS platform tracks versions across multiple independent components. Use `ops update matrix` at any time to inspect the current state:

| Component | Current Version | Description |
|:---|:---|:---|
| Server Platform Core | v2.10.0 | Host OS + Docker stack + systemd services |
| Authoritative API | v1 (v2.10.0) | FastAPI REST API version |
| Database Schema | 2026.08.28.01 | Alembic migration revision |
| Web Client | v2.10.0 | Next.js / PWA browser application |
| Desktop Client (Tauri) | v2.10.0 | Native Windows/Linux/macOS app |
| Minimum Compatible Client | v2.0.0 | Oldest accepted client version |
| Release Channel | enterprise_lts | Update channel for production |

### Client Compatibility Policy

- **Minimum Supported Client Version**: `v2.0.0`
- Any client older than `v2.0.0` will receive a compatibility warning or be rejected during authentication.
- The server validates the `X-Client-Version` header on each request against `MIN_SUPPORTED_CLIENT_VERSION`.

---

## 2. Pre-Upgrade Checklist

Before applying any upgrade, run the following checks:

```bash
# 1. Review current version matrix
ops update matrix

# 2. Run deep health probe
ops health

# 3. Check for available updates
ops update check

# 4. Verify storage capacity (minimum 10 GB free for staging)
ops status

# 5. Create a pre-upgrade snapshot backup
ops backup create --note "Pre-upgrade snapshot v2.10.0 -> v2.11.0"

# 6. Verify backup integrity
ops backup list
ops backup verify <archive_name>
```

> **Warning**: The upgrade pipeline automatically creates a pre-upgrade safety snapshot. However, creating one manually provides an explicit recovery point with your own notes.

---

## 3. Automated Upgrade Procedure (8-Step Pipeline)

The `ops update apply` command executes a controlled, non-destructive upgrade pipeline:

```bash
ops update apply
```

### Step-by-Step Pipeline

| Step | Action | Command Equivalent | Safety |
|:---|:---|:---|:---|
| **1. Health Pre-Validation** | Verifies all containers are running and healthy | `ops health` | Blocks if any service is down |
| **2. Version Compatibility Check** | Checks target version against current; warns on downgrade | `ops update matrix` | Fails on incompatible versions |
| **3. Pre-Upgrade Safety Snapshot** | Creates `dwrms_backup_pre_upgrade_YYYYMMDD_HHMMSS.tar.gz` | `ops backup create --type PRE_UPGRADE` | Mandatory unless `--skip-backup` |
| **4. Staged Code Deployment** | `git pull --ff-only` + Docker image rebuild | `docker compose build` | Rollback snapshot exists |
| **5. Transactional Schema Migrations** | Alembic migrations applied in order | `alembic upgrade head` | Rollback via `downgrade` if failed |
| **6. Zero-Downtime Service Restart** | Rolling container restart with health checks | `docker compose up -d --remove-orphans` | Health probe before traffic |
| **7. Post-Update Health Check** | Full subsystem verification | `ops health` | Fails → rollback triggered |
| **8. Smoke Test Verification** | Auth login, job card lifecycle, fleet requisition | API smoke tests | Fails → rollback triggered |

### Upgrade Command Options

```bash
# Standard upgrade (interactive confirmation)
ops update apply

# Fully non-interactive (for automation / CI)
ops update apply -y

# Target specific version
ops update apply --target-version v2.11.0

# Skip git pull (for offline / local installs)
ops update apply --skip-git

# Skip pre-upgrade snapshot (NOT RECOMMENDED)
ops update apply --skip-backup
```

---

## 4. Database Schema Migration Management

### 4.1 Migration Overview

Database schema changes are managed by **Alembic** and live in [`backend/alembic/versions/`](../backend/alembic/versions). The platform follows an **additive-only migration** policy — migrations never delete columns or tables, ensuring reversibility.

Current migration chain (9 revisions):

```
48bcca2bf4fe_init
    → 7a8b9c0d1e2f_add_industrial_operations_core
        → a1b2c3d4e5f6_v1_3_job_report_engine
            → 3416e09ebcc3_add_industrial_operations_core_schemas
                → 415d1feb1cc1_migrate_requisition_statuses
                    → 415d1feb1cc2_v1_5_scheduling
                        → 74bd076d72cc_add_jobcard_extended_completion_fields
                                → debd9a6a4bcd_add_work_packages_and_collaborators
                                → ea5c866570ed_add_businessauditlog_table
                                    → (latest) 2026.08.28.01
```

### 4.2 Manual Migration Commands

```bash
# 1. Check current revision
alembic current

# 2. Review pending migrations
alembic heads
alembic history

# 3. Apply all pending migrations
alembic upgrade head

# 4. Apply to specific revision
alembic upgrade 3416e09ebcc3

# 5. Downgrade (rollback) one revision
alembic downgrade -1

# 6. Generate a new migration
alembic revision -m "add_new_field_to_job_cards" --depends-on 3416e09ebcc3

# 7. View migration diff
alembic upgrade head --sql   # Generates SQL without applying
```

### 4.3 Migration Safety Rules

1. **Never delete columns or tables** — mark as deprecated instead.
2. **Always test migrations locally first** — use the SQLite dev DB.
3. **Run migrations inside the container** — `docker compose run --rm backend alembic upgrade head`.
4. **Create a backup before every migration** — `ops backup create --note "Pre-migration"`.
5. **Verify migrations in staging** — deploy to staging environment before production.

### 4.4 Migration Testing

```bash
# Run inside the backend container or dev venv
cd backend

# Test migration up
alembic upgrade head

# Test migration down (if reversible)
alembic downgrade base

# Re-apply
alembic upgrade head
```

---

## 5. Rollback Procedures

### 5.1 Automated Rollback (1-Command)

If a post-upgrade issue is detected:

```bash
ops update rollback
```

This command:
1. Locates the most recent `dwrms_backup_pre_upgrade_*.tar.gz` snapshot.
2. Validates the snapshot's SHA-256 integrity hash.
3. Automatically creates a safety snapshot of current data before reverting.
4. Restores the database schema and application storage.
5. Gracefully restarts platform services.

### 5.2 Manual Rollback via Backup Restore

```bash
# 1. List available snapshots
ops backup list

# 2. Verify integrity
ops backup verify dwrms_backup_pre_upgrade_YYYYMMDD_HHMMSS.tar.gz

# 3. Execute restore
ops restore dwrms_backup_pre_upgrade_YYYYMMDD_HHMMSS.tar.gz
# Confirm with 'CONFIRM RESTORE' when prompted

# 4. Verify health
ops health
ops status
```

### 5.3 Docker-Level Rollback (if CLI unavailable)

```bash
# 1. Stop services
docker compose -f infrastructure/docker-compose.prod.yml stop backend worker beat

# 2. Restore database from dump
docker compose -f infrastructure/docker-compose.prod.yml exec -T db \
  psql -U postgres -d dwrms < /tmp/restore/database.sql

# 3. Restore file storage
cp -r /tmp/restore/storage/. /var/dwrms/storage/

# 4. Restart
docker compose -f infrastructure/docker-compose.prod.yml up -d
```

---

## 6. Client-Side Upgrade

### 6.1 Desktop Client (Tauri)

The desktop client checks for updates on launch against the server's version matrix:

```bash
# Manual check
ops update check

# The web UI at /admin/platform (Tab 5) also shows update status
```

When an update is available:
1. The server returns `has_update: true` with the latest approved version.
2. The desktop client downloads the new version bundle.
3. The user is prompted to restart the application.

### 6.2 Web / PWA Client

The web client is served directly from the server. No client-side update is needed — users simply refresh their browsers. For PWA clients, the service worker automatically detects and applies updates.

### 6.3 Forced Client Update

To force all clients to update (e.g., security patch):

```bash
# Update the minimum supported client version in .env
# Then restart the backend
ops server restart backend
```

Clients below the minimum version will be rejected at login with a redirect to the update page.

---

## 7. Staged Deployment (Production)

For production environments, use a staged upgrade strategy:

### Stage 1: Staging Environment

```bash
# 1. Deploy to staging
docker compose -f infrastructure/docker-compose.staging.yml up -d --build

# 2. Run migrations in staging
docker compose -f infrastructure/docker-compose.staging.yml run --rm backend alembic upgrade head

# 3. Verify staging
curl -k https://staging-dwrms.bikita.com/readiness
ops health  # (pointed at staging)
```

### Stage 2: Production Cutover

```bash
# 1. Create production backup
ops backup create --note "Pre-production upgrade v2.10.0 -> v2.11.0"

# 2. Apply update
ops update apply -y

# 3. Monitor
ops status
ops health
```

### Stage 3: Post-Upgrade Verification

```bash
# Verify version matrix
ops update matrix

# Run workflow smoke tests
# (Authentication, Job Cards, Fleet Requisitions)
curl -k https://dwrms.bikita.com/api/v1/health
curl -k https://dwrms.bikita.com/api/v1/version
```

---

## 8. Breaking Changes Handling

### 8.1 Pre-Upgrade Breaking Change Audit

Before upgrading, check for breaking changes:

```bash
# Review the breaking changes document
cat docs/BREAKING_CHANGES.md
```

Current breaking changes (v2.9.0+):

| Change | Impact | Mitigation |
|:---|:---|:---|
| Idempotency header requirement | Mutating endpoints recommend `X-Idempotency-Key` | Add idempotency key to all POST/PUT/PATCH requests |
| Client compatibility threshold (v2.0.0) | Clients older than v2.0.0 rejected | Upgrade all clients before server upgrade |
| Standardized backup archives | Old untagged archives deprecated | Re-verify old backups have `manifest.json` |

### 8.2 Post-Upgrade Schema Verification

```bash
# Check that all migrations applied
alembic current

# Verify database connectivity
docker compose -f infrastructure/docker-compose.prod.yml exec db pg_isready -U postgres

# Check for migration conflicts
alembic heads  # Should return no output (no divergent branches)
```

---

## 9. Upgrade Troubleshooting

### 9.1 Migration Fails

```bash
# 1. Check Alembic error
alembic upgrade head 2>&1 | tail -50

# 2. Rollback to last known good
alembic downgrade <previous_revision>

# 3. Restore from pre-upgrade snapshot
ops restore dwrms_backup_pre_upgrade_YYYYMMDD_HHMMSS.tar.gz
```

### 9.2 Docker Image Build Fails

```bash
# 1. Check build logs
docker compose -f infrastructure/docker-compose.prod.yml build backend 2>&1

# 2. Verify backend Dockerfile
# See: backend/Dockerfile

# 3. Rebuild with no cache
docker compose -f infrastructure/docker-compose.prod.yml build --no-cache backend
```

### 9.3 Health Check Fails After Upgrade

```bash
# 1. Check specific component
ops status
ops health

# 2. Inspect logs
ops logs -s backend -n 100
ops logs -s error -n 50

# 3. Check container status
docker compose -f infrastructure/docker-compose.prod.yml ps

# 4. Restart specific service
ops server restart backend
```

### 9.4 Rollback Recovery

If automated rollback fails:

```bash
# 1. Stop all services
sudo systemctl stop dwrms

# 2. Restore database from backup
ops restore <snapshot_archive> -y

# 3. Rebuild and restart
docker compose -f /opt/dwrms/infrastructure/docker-compose.prod.yml up -d --build

# 4. Verify
ops health
ops status
```

---

## 10. Continuous Updates (Auto-Pull)

The platform includes a 1-minute auto-pull timer for development/staging environments:

```bash
# Check timer status
systemctl is-active dwrms-autoupdate.timer

# View timer configuration
cat infrastructure/systemd/dwrms-autoupdate.timer

# Disable auto-update (production)
sudo systemctl disable dwrms-autoupdate.timer

# Enable auto-update (staging/development)
sudo systemctl enable --now dwrms-autoupdate.timer
```

The auto-update script (`scripts/ops/autoupdate.sh`) performs:
1. `git fetch origin`
2. `git pull --ff-only` (if ahead)
3. `docker compose pull` (if using remote images)
4. `docker compose up -d --build`
5. Health check verification
