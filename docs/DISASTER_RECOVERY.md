# Bikita Minerals DWRMS — Backup, Recovery and Disaster Readiness Guide

## Version 2.8 Standard Operating Procedures (SOP)

This document establishes the authoritative backup, recovery, and disaster readiness procedures for the self-hosted **Digital Work Request and Maintenance Management System (DWRMS)** deployed on central Ubuntu Servers.

---

## 1. Backup Strategy Overview

The platform uses a layered disaster readiness strategy protecting four core pillars:

1. **Authoritative Database State**: Complete schema, tables, foreign keys, RBAC capabilities, and audit logs.
2. **Uploaded Document & Attachment Storage**: Equipment manuals, breakdown photos, job attachments, and calibration reports located in `/var/dwrms/storage/uploads`.
3. **Platform Configuration & State**: Sanitized environment variables, domain binding, and encryption configuration.
4. **Cryptographic Manifest & Integrity Hashes**: Standardized `manifest.json` embedded inside every `.tar.gz` archive paired with an external `.sha256` digest.

```text
Standardized Backup Archive Layout (dwrms_backup_YYYYMMDD_HHMMSS.tar.gz)
│
├── manifest.json         # Authoritative metadata (ID, version, engine, checksum, type)
├── metadata.json         # Backward-compatible metadata alias
├── config.json           # Sanitized environment configuration
├── database.sql          # Full SQL dump or SQLite file snapshot
└── storage/              # Persistent attachments and uploaded files
    └── uploads/
```

### Manifest Schema Specification (`manifest.json`)

```json
{
  "backup_id": "bkp_20260828_153000_a1b2c3d4",
  "timestamp": "2026-08-28T15:30:00.000Z",
  "platform_version": "v2.8.0",
  "database_engine": "POSTGRESQL",
  "database_version": "POSTGRESQL standard",
  "backup_type": "FULL_SNAPSHOT",
  "status": "VERIFIED",
  "storage_location": "/var/dwrms/backups/dwrms_backup_20260828_153000.tar.gz",
  "integrity_status": "VERIFIED_SHA256",
  "files_included": ["manifest.json", "database.sql", "config.json", "storage"],
  "retention_days": 30,
  "note": "Pre-maintenance baseline snapshot"
}
```

---

## 2. Retention Policy & Automated Pruning

The platform enforces a configurable retention policy (`RETENTION_DAYS=30` by default):

* Snapshots older than 30 days are automatically pruned during daily scheduled backup runs.
* **Baseline Preservation Rule**: The 2 most recent baseline snapshots are permanently protected against automatic pruning regardless of age to guarantee a valid recovery target.
* Operators can manually enforce or preview retention cleanup using:

```bash
ops backup prune --retention-days 30
```

---

## 3. Disaster Recovery Runbooks

### Runbook 1: Database Corruption

**Symptom**: Database fails health check, reports IO errors, or query execution crashes with corruption logs.

1. **Assess System Status via CLI**:

   ```bash
   ops status
   ops health
   ```

2. **List and Verify Available Snapshots**:

   ```bash
   ops backup list
   ops backup verify dwrms_backup_YYYYMMDD_HHMMSS.tar.gz
   ```

3. **Execute Controlled Restoration**:

   ```bash
   ops restore dwrms_backup_YYYYMMDD_HHMMSS.tar.gz
   # Confirm with 'CONFIRM RESTORE' when prompted
   ```

   *Note: A pre-restore safety snapshot (`dwrms_prerestore_safety_*.tar.gz`) is automatically generated before any existing files are modified.*

4. **Verify Health Post-Restoration**:

   ```bash
   ops health
   ```

---

### Runbook 2: Accidental Data Deletion

**Symptom**: Critical Job Cards, fleet requisitions, or user permissions accidentally removed.

1. **Locate Most Recent Verified Snapshot Prior to Incident**:

   ```bash
   ops backup list
   ```

2. **Execute Restoration with Pre-Restore Snapshot Protection**:

   ```bash
   ops restore <snapshot_name>
   ```

3. **Inspect Application Logs**:

   ```bash
   ops logs --lines 100 --follow
   ```

---

### Runbook 3: Server Hardware / VM Failure (Bare-Metal Re-Provisioning)

**Symptom**: Physical host or virtual machine completely destroyed or unbootable.

1. **Provision Fresh Ubuntu Server 24.04 LTS Instance**.
2. **Transfer Off-Site Backup Archive** to `/var/dwrms/backups/`.
3. **Execute First-Time Platform Setup**:

   ```bash
   ops setup
   ```

4. **Restore Authoritative Snapshot**:

   ```bash
   ops restore dwrms_backup_YYYYMMDD_HHMMSS.tar.gz -y
   ```

5. **Verify Subsystem Readiness**:

   ```bash
   ops health
   ops diagnostics
   ```

---

### Runbook 4: Application Service Failure

**Symptom**: Reverse proxy reports 502/504 Bad Gateway or background Celery workers stop processing.

1. **Inspect Subsystem Diagnostics**:

   ```bash
   ops status
   ops diagnostics
   ```

2. **Restart Application Services**:

   ```bash
   ops server restart
   ```

3. **Check Real-Time Logs**:

   ```bash
   ops logs --level ERROR
   ```

---

### Runbook 5: Failed Platform Update / Rollback

**Symptom**: An applied software update introduces breaking schema incompatibilities or operational faults.

1. **Locate Pre-Upgrade Snapshot** (automatically tagged `PRE_UPGRADE` or `PRE_RESTORE_SAFETY`):

   ```bash
   ops backup list
   ```

2. **Verify Integrity**:

   ```bash
   ops backup verify dwrms_backup_pre_upgrade.tar.gz
   ```

3. **Restore Baseline State**:

   ```bash
   ops restore dwrms_backup_pre_upgrade.tar.gz
   ```

4. **Confirm Status**:

   ```bash
   ops status
   ```

---

### Runbook 6: Persistent Storage Failure / Disk Loss

**Symptom**: Persistent attachment storage (`/var/dwrms/storage` or `./storage`) is lost, unmounted, or corrupted.

1. **Inspect Storage Health via CLI**:

   ```bash
   ops status
   ops diagnostics
   ```

2. **Re-create / Remount Storage Volume**:

   ```bash
   sudo mkdir -p /var/dwrms/storage/uploads
   sudo chown -R 1000:1000 /var/dwrms/storage
   ```

3. **Restore Storage from Latest Verified Snapshot**:

   ```bash
   ops restore <snapshot_name>
   ```

4. **Verify Storage Permissions & Capacity**:

   ```bash
   ops health
   ```

---

## 4. Disaster Recovery Readiness Checklist

| Phase | Action Item | Frequency / Trigger | Verification Method |
| :--- | :--- | :--- | :--- |
| **Prevention** | Daily Automated Scheduled Backup | Every 24 hours (02:00 UTC) | Check `ops backup list` |
| **Integrity** | Cryptographic SHA-256 Digest Match | On every backup creation | `ops backup verify <archive>` |
| **Safety** | Pre-Restore Safety Snapshot Generation | Prior to every restore | Verify `dwrms_prerestore_safety_*.tar.gz` created |
| **Pruning** | Retention Policy Cleanup (30 Days) | Automated daily | `ops backup prune` |
| **Testing** | Disaster Recovery Restoration Drill | Quarterly | Execute restore on staging environment |
| **Off-Site** | Cold Storage Archive Replication | Weekly | Sync `/var/dwrms/backups/` to remote offsite vault |

---

## 5. Security & Authorization Safeguards

1. **Authorization Guard**: Backup creation and restore endpoints strictly require the `settings:manage` capability (Super Administrator role).
2. **Secret Masking**: Database passwords, JWT keys, and API tokens are never exposed in plaintext in backup metadata or console logs.
3. **Explicit Confirmation**: Restores cannot be triggered accidentally — operators must provide explicit confirmation phrase `CONFIRM RESTORE`.
