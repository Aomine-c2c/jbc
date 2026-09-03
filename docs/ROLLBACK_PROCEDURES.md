# Emergency Platform Update Rollback Procedures

## Overview

If a software update causes breaking operational issues or fails post-update health checks, follow these procedures to restore the platform to its verified pre-upgrade state.

---

## 1. Automated 1-Command Rollback (Recommended)

Run:

```bash
ops update rollback
```

The CLI automatically:

1. Locates the most recent `dwrms_backup_pre_upgrade_*.tar.gz` snapshot.
2. Validates the snapshot's SHA-256 integrity hash.
3. Automatically creates a safety snapshot of current data before reverting.
4. Restores the database schema and application storage.
5. Gracefully restarts platform services.

---

## 2. Manual Snapshot Restoration

If the CLI rollback is unavailable:

1. List available snapshots:

   ```bash
   ops backup list
   ```

2. Verify integrity:

   ```bash
   ops backup verify dwrms_backup_pre_upgrade_YYYYMMDD_HHMMSS.tar.gz
   ```

3. Execute restore:

   ```bash
   ops restore dwrms_backup_pre_upgrade_YYYYMMDD_HHMMSS.tar.gz
   # Enter 'CONFIRM RESTORE'
   ```

4. Verify subsystem readiness:

   ```bash
   ops health
   ops status
   ```
