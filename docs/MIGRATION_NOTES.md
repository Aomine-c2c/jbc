# Database & Platform Migration Notes

## Migration: 2026.08.28.01 (v2.9.0 Upgrade)

### Summary
This migration standardizes version matrix tracking, sets up transactional safety constraints, and applies configuration fields for client compatibility thresholds.

### Pre-Migration Checklist
1. Verify database health: `ops health`
2. Create snapshot backup: `ops backup create --note "Pre-v2.9.0 baseline"`
3. Verify snapshot integrity: `ops backup verify <archive>`

### Schema Changes Applied
* Added `platform_version` and `schema_version` tracking in application settings.
* Ensured idempotency store table/in-memory cache compatibility.
* Preserved all foreign keys across `job_cards`, `requisitions`, `approvals`, and `users`.

### Post-Migration Verification
Run:
```bash
ops update matrix
ops health
```
All components should report `ACTIVE` or `APPLIED`.
