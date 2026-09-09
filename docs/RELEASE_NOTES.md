# Release Notes: Bikita Minerals DWRMS

## Release v2.10.0 — Unified Multi-Device Distribution, Server Profiles & Enterprise Platform Hardening

### Overview

Release **v2.10.0** introduces unified multi-device packaging (Windows native MSI/NSIS setup, Rugged Tablet PWA, and Android Enterprise guidelines), dynamic Multi-Client Gateway server connection profiles with real-time latency ping telemetry, Next.js static export compatibility for offline desktop embedding, and enhanced fleet requisition approval relationships.

---

### Key Capabilities in v2.10.0

1. **Unified Multi-Device Packaging Pipeline**:
   - Automated cross-platform packaging via `deploy/build-all-device-setups.ps1`.
   - Windows Desktop Workstations & Field Laptops: Self-contained NSIS installer (`DWRMS_2.10.0_x64-setup.exe`) and Active Directory silent GPO MSI (`DWRMS_2.10.0_x64_en-US.msi`).
   - Rugged Field Tablets & Mobile: Verified offline PWA bundle in `dist/tablet-mobile-pwa/` with Service Worker, Web Manifest, and responsive icon assets.
   - Android Enterprise: Standardized APK/AAB build instructions and environment blueprint in `dist/android/`.

2. **Multi-Client Gateway & Dynamic Server Connection Profiles**:
   - Integrated `ServerProfileManagerDialog` enabling field operators and administrators to switch between Central Mine Server, Plant LAN Gateway, and Offline Mesh nodes.
   - Live HTTP ping diagnostics measuring latency (ms) with visual status indicators.
   - Dynamic profile persistence in client storage with active server telemetry badge.

3. **Desktop Native & Static Export Architecture**:
   - Conditional Next.js static export pipeline (`npm run build:export`) tailored for Tauri desktop embedding.
   - Complete `generateStaticParams` coverage across dynamic routes (`/jobs/[id]`, `/fleet/machines/[id]`, `/fleet/requisitions/[id]`).

4. **Fleet Machine Requisition Governance**:
   - Full SQLAlchemy ORM relationship mapping for `requester`, `department`, and `collaborating_department` on machine requisitions.
   - Multi-tier approval routing enforcement with validation safeguards.

5. **Design System & Semantic Token Normalization**:
   - Elimination of hardcoded dark backgrounds in profile dialogs, status badges, and diagnostic matrices.
   - Accessible, high-contrast semantic theme tokens compatible with both Dark and Light modes.

---

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
