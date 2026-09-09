# Bikita Minerals DWRMS — Changelog

All notable changes to this platform are documented in this file in adherence to [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v2.10.0] — 2026-09-09

### Added

- **Multi-Client Gateway & Server Connection Profiles**: Enhanced server profile management modal (`ServerProfileManagerDialog`) with dynamic connection switching, live ping telemetry, and pre-flight health validation.
- **Unified Multi-Device Distribution Pipeline**: Automated packaging workflow via `deploy/build-all-device-setups.ps1` with native Tauri release bundles (`.exe` NSIS setup and `.msi`), field PWA assets (`manifest.json`, `sw.js`, device profile), and Android Enterprise packaging specs.
- **Fleet Machine Requisition ORM Relationships**: Explicit `requester`, `department`, and `collaborating_department` relationships on `MachineRequisition` with robust approval workflow routing.
- **Dynamic Next.js Static Export Embedding**: Configured conditional export mode for Tauri client bundling (`npm run build:export`) with automated `generateStaticParams` across all dynamic routes (`[id]`).

### Changed

- **Standardized Light Mode Design Tokens**: Comprehensive refactoring of Server Profile Manager inputs, Connection Status badges, and Platform Administration diagnostic matrices from hardcoded dark backgrounds to accessible, high-contrast semantic theme tokens.
- **Upgraded Platform Versioning**: Bumped authoritative version to `v2.10.0` across Backend Core, Ops CLI, Tauri configuration, and Client Profiles.

---

## [v2.9.0] — 2026-08-28

### Added

- **Multi-Tier Version Matrix Tracking**: Explicit version tracking across Server Platform Core, Authoritative REST API, Database Schema, Web Client (Next.js/PWA), Desktop Native Client (Tauri), and Minimum Compatible Client.
- **8-Step Controlled Update Lifecycle**: Non-destructive pipeline encompassing health pre-validation, compatibility checks, pre-upgrade safety snapshotting, code staging, transactional schema migrations, service restarts, post-update health checks, and critical workflow smoke tests.
- **CLI Update Management**: `ops update matrix`, `ops update check`, `ops update apply`, and `ops update rollback`.
- **GUI Update Console**: Integrated version matrix cards, release channel telemetry, and update triggers in `/admin/platform` (Tab 5).
- **Client Compatibility Header Validation**: Server validation of client semver vs `MIN_SUPPORTED_CLIENT_VERSION` (`v2.0.0`).

### Changed

- Standardized `APP_VERSION` across backend and client profiles to `v2.9.0`.
- Hardened database migration execution in update pipelines with fail-fast rollbacks.

---

## [v2.8.0] — 2026-08-28

### Added

- **Standardized Archive Manifest (`manifest.json`)**: Every backup archive includes standardized metadata with UUID `backup_id`, `timestamp`, `platform_version`, `database_engine`, `backup_type`, and `integrity_status`.
- **Companion SHA-256 Checksum Files**: Generated on all snapshots for cryptographic integrity verification.
- **Pre-Restore Safety Snapshots**: Automatically creates `dwrms_prerestore_safety_*.tar.gz` before any restore is applied.
- **Retention Policy & Pruning**: Automated pruning of archives older than 30 days while permanently preserving baseline recovery targets.
- **Disaster Recovery Runbooks**: Detailed operational SOPs in `docs/DISASTER_RECOVERY.md`.

---

## [v2.7.0] — 2026-08-28

### Added

- **Five-State Network Connection Monitor**: `ONLINE`, `CONNECTING`, `RECONNECTING`, `OFFLINE`, and `SERVER UNAVAILABLE`.
- **Backend Idempotency Middleware (`X-Idempotency-Key`)**: 15-minute TTL cache preventing duplicate Job Cards or requisitions on retransmissions.
- **Controlled GET Retries**: Up to 2 retries with exponential backoff on read operations.
- **Form Draft Preservation (`useDraftPreserver`)**: Browser `localStorage` auto-saving for Job Cards and Requisitions with restore alerts.
- **Non-Blocking `NetworkStatusBar`**: Top alert banner with "Reconnect Now" action.

---

## [v2.6.0] — 2026-08-28

- Added optional provider-agnostic secure remote transport layer (Tailscale/WireGuard) operating strictly below application authentication.

---

## [v2.5.0] — 2026-08-28

- Hardened SSH technical administration with Ed25519 keys, Fail2ban, and 3-tier administrative boundary.

---

## [v2.4.0] — 2026-08-28

- Platform Administration GUI with 7-matrix system status dashboard and live diagnostics.

---

## [v2.3.0] — 2026-08-28

- First-class Next.js web application and responsive mobile PWA client.

---

## [v2.2.0] — 2026-08-28

- Configurable server connection profiles with pre-flight health validation.

---

## [v2.1.0] — 2026-08-28

- Interactive first-time server setup wizard via CLI and Web GUI.

---

## [v2.0.0] — 2026-08-28

- Authoritative Platform Administration CLI (`ops`).
