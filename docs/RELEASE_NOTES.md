# Release Notes: Bikita Minerals DWRMS

## Release v2.9.0 — Platform Update and Version Management

### Overview
Release **v2.9.0** introduces a standardized, non-destructive platform update and version management system designed for enterprise-grade reliability in harsh or intermittent industrial mining environments.

---

### Key Capabilities in v2.9.0

1. **Multi-Tier Authoritative Version Matrix**:
   - Server Platform Core: `v2.9.0`
   - Authoritative API: `v1 (v2.9.0)`
   - Database Schema: `2026.08.28.01`
   - Web Client: `v2.9.0` (Next.js / PWA)
   - Native Desktop Client: `v2.9.0` (Tauri)
   - Minimum Compatible Client Version: `v2.0.0`

2. **Strict 8-Step Controlled Update Pipeline**:
   - Pre-update health and storage write checks.
   - Target version compatibility analysis.
   - Automated pre-upgrade disaster recovery snapshot (`dwrms_backup_pre_upgrade_*.tar.gz`).
   - Staged code deployment.
   - Transactional schema migrations.
   - Zero-downtime service reload.
   - Post-update health & latency verification.
   - Smoke testing of authentication, job card lifecycles, and fleet requisition workflows.

3. **1-Command Emergency Rollback**:
   - In case of post-update operational faults, operators can instantly execute `ops update rollback` to restore pre-upgrade state.

4. **Web Administration Console**:
   - Full version matrix visualization in `/admin/platform` (Tab 5).
   - Real-time release channel query (`enterprise_lts`).
