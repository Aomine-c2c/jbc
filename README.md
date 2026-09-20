# Bikita Minerals DWRMS - Digital Work Request & Resource Management System

**Authoritative Industrial Operations, Heavy Fleet Management & Cross-Departmental Governance Core**  
*Enterprise Platform Architecture for Bikita Minerals Lithium Operations (Version 2.10.0)*

---

## 1. Multi-Device & Cross-Platform Support Matrix

Bikita Minerals DWRMS is purpose-built and field-validated for seamless multi-device deployment across the entire spectrum of open-pit mining and industrial plant workflows:

| Device Category | Target Personas & Hardware | Form Factor & Screen Resolution | Input Modalities | Key Capabilities & UX Adaptations | Deployment & Access |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Desktop Workstations** | Control Room Engineers, Plant Superintendents, Production Planners, System Admins | 1920x1080 to 4K Ultrawide, Multi-Monitor Consoles | Keyboard, High-precision Mouse, Barcode / RFID desk scanners | Multi-column telemetry panels, interactive fleet gantt schedulers, live GIS map radar, batch job card dispatching, and deep administrative configuration. | Native Windows App (`.exe` / `.msi`) or Desktop Browser (Chrome, Edge, Firefox) |
| **Field Laptops** | Maintenance Supervisors, Heavy Equipment Inspectors, Electrical Field Technicians | 13"–16" Semi-Rugged / Fully-Rugged Laptops (Panasonic Toughbook, Dell Rugged Extreme, ThinkPad) | Trackpad, Full QWERTY Keyboard, Stylus, Field USB Scanners | 100% offline draft work-order caching, batch job card sign-offs, full LOTO permit verification, remote diagnostic mesh access over Tailscale VPN. | Native Windows App (`.exe` installer) or Local Web App via Tailscale Serve |
| **Rugged Tablets** | Machine Operators, Heavy Haulage Drivers, Mechanical Artisans, Mill Technicians | 8"–11" Rugged Android / Windows Tablets (Samsung Galaxy Tab Active4 Pro, Zebra ET51/ET56) | High-contrast Touch (glove & wet-finger modes), Active Stylus (S-Pen), Integrated 2D Barcode Imager | Large 48px+ touch targets, Pre-Start Inspection checklists with instant photo capture, capacitive digital artisan signature pads, quick fault logging, and offline IndexedDB sync. | Progressive Web App (PWA) with Standalone Homescreen Launch or Web Browser |
| **Mobile Handhelds & Smart Devices** | Roving Safety Officers (HSE), Shift Bosses, Traveling Requesters, Executives | 5.5"–6.7" iOS & Android Smartphones, Zebra/Honeywell Enterprise Handhelds | Single-hand Touch, Haptic Virtual Keyboard, Hardware Scan Trigger, Device Camera | Sticky mobile bottom navigation bar, collapsible side drawers, single-tap requisition approvals, real-time safety incident logging with live geo-coordinates and photo attachments. | Mobile Responsive Web (Tailwind/CSS Grid flex layout) / Add to Home Screen (PWA) |

### Responsive Adaptive Architecture Highlights

- **Dynamic Viewport Breakpoints**: Built with fluid Tailwind CSS grid breakpoints (`sm:640px`, `md:768px`, `lg:1024px`, `xl:1280px`, `2xl:1536px`), providing fluid auto-reflow from compact 375px mobile screens up to 4K control room video walls.
- **Touch-First UI Controls**: Minimum 44x44px interactive tap targets across all form fields, date pickers, dropdown selects, and approval action buttons to prevent mis-clicks in vibrating equipment or with gloved hands.
- **Offline Resiliency**: Client-side state caching and background synchronization ensure pre-start inspections and fault entries are safely preserved even in low-signal open-pit quarry bottoms and underground processing tunnels.
- **Adaptive Data Presentation**: Dense tabular views automatically transform into card-based summary feeds on mobile and compact tablet screens for effortless vertical thumb scrolling.

---

## 2. Multi-Device Packaging Pipeline & Distribution Setups

All device setups are built, verified, and packaged in the unified distribution directory [`/dist`](dist/):

| Target Device | Package / Distribution Artifact | Size | SHA-256 Checksum | Operational Target |
| :--- | :--- | :---: | :--- | :--- |
| **Workstations & Laptops** | [`dist/desktop/DWRMS_2.10.0_x64-setup.exe`](dist/desktop/DWRMS_2.10.0_x64-setup.exe) | **3.06 MB** | `31208ee6b18e903efd5363dffac507848e2520e9840938bf4e7fbce1cff60aaa` | Self-contained Windows installer for workshop PCs & rugged field laptops |
| **Active Directory Rollout** | [`dist/desktop/DWRMS_2.10.0_x64_en-US.msi`](dist/desktop/DWRMS_2.10.0_x64_en-US.msi) | **4.09 MB** | `d3b4f843620dccde507c374d0fc85319eb135e9f24ae7144702ec49d0f14a44a` | Silent GPO / SCCM domain-wide installation across mine office PCs |
| **Rugged Tablets & Mobile** | [`dist/tablet-mobile-pwa/`](dist/tablet-mobile-pwa/) | **~102 KB** | `7f5e4ec96893c938006e2571b64df197348efbfc064dd3b681cb3b4eb22891e5` | Offline PWA app shell for Samsung Galaxy Tab Active, Zebra & iOS/Android devices |
| **Android Enterprise (MDM)** | [`dist/android/BUILD_INSTRUCTIONS.txt`](dist/android/BUILD_INSTRUCTIONS.txt) | **~1 KB** | *Tauri Android APK generation pipeline* | Standalone APK build configuration for corporate mobile device managers |

### Build Setups for All Devices in One Command

```powershell
.\deploy\build-all-device-setups.ps1
```

### Build Specific Device Profiles

```powershell
# Desktop Workstations & Rugged Laptops (.exe / .msi)
.\deploy\build-all-device-setups.ps1 -DevicePlatform desktop

# Rugged Tablets & Mobile Handhelds (Offline PWA shell & assets)
.\deploy\build-all-device-setups.ps1 -DevicePlatform pwa

# Android Enterprise APK environment
.\deploy\build-all-device-setups.ps1 -DevicePlatform android
```

*For step-by-step device deployment and silent installation commands, see [`deploy/CLIENT_SETUP_GUIDE.md`](deploy/CLIENT_SETUP_GUIDE.md).*

---

## 3. System Documentation & Operational Manuals

| Document | File Path | Focus & Target Audience |
| :--- | :--- | :--- |
| **Comprehensive Developer Guide** | [`docs/DEVELOPER_GUIDE.md`](docs/DEVELOPER_GUIDE.md) | Authoritative technical specs, backend/frontend architecture, RBAC, domain modules, state machine, testing, and contribution standards. |
| **Cross-Platform Setup & Dependency Guide** | [`docs/CROSS_PLATFORM_SETUP.md`](docs/CROSS_PLATFORM_SETUP.md) | Dedicated automated/manual setup guides for Linux (Ubuntu/Debian) & Windows (MSI/NSIS/PowerShell), dependency management, and local dev. |
| **Installation & Dependency Management** | [`docs/INSTALLATION_AND_DEPENDENCIES.md`](docs/INSTALLATION_AND_DEPENDENCIES.md) | Detailed 7-stage automated `install.sh` pipeline, runtime packages, storage layout, environment variables, and TLS. |
| **Version Upgrade & Migration Guide** | [`docs/UPGRADE_AND_MIGRATION_GUIDE.md`](docs/UPGRADE_AND_MIGRATION_GUIDE.md) | The 8-stage `ops update apply` pipeline, version compatibility matrix, Alembic schema migrations, and 1-click disaster recovery rollback. |
| **Interface Modes & Operations Manual** | [`docs/INTERFACE_MODES.md`](docs/INTERFACE_MODES.md) | Comprehensive operational manual for Desktop Workstation GUI, Rugged Tablet PWA (offline sync), Web Portal, and `ops` CLI suite. |
| **Platform Administration CLI (`ops`) Reference** | [`docs/OPS_CLI_REFERENCE.md`](docs/OPS_CLI_REFERENCE.md) | Command syntax, options, and operational examples for the unified `ops` command-line suite. |
| **Operational Readiness Audit** | [`docs/OPERATIONAL_READINESS_AUDIT.md`](docs/OPERATIONAL_READINESS_AUDIT.md) | File-by-file audit of all 419 source files (100% READY) and multi-role browser click results. |
| **Master System Documentation** | [`docs/SYSTEM_DOCUMENTATION.md`](docs/SYSTEM_DOCUMENTATION.md) | Enterprise architecture, 10 mining departments, state machine lifecycle, and 8-role RBAC matrix. |
| **6-Role Demo Walkthrough** | [`docs/ROLE_DEMO_WALKTHROUGH.md`](docs/ROLE_DEMO_WALKTHROUGH.md) | Step-by-step interactive scenario centered on CAT 777D Haul Truck breakdown and repair. |
| **API & Operations Manual** | [`docs/API_OPERATIONS_MANUAL.md`](docs/API_OPERATIONS_MANUAL.md) | Authoritative REST API endpoint specifications, parameters, response formats, and security scopes. |
| **Ubuntu Server Deployment Guide** | [`docs/UBUNTU_SERVER_DEPLOYMENT.md`](docs/UBUNTU_SERVER_DEPLOYMENT.md) | Authoritative production server deployment instructions for Ubuntu 22.04 / 24.04 LTS. |
| **Disaster Recovery & Backups** | [`docs/DISASTER_RECOVERY.md`](docs/DISASTER_RECOVERY.md) | Backup procedures, SHA-256 integrity verification, 30-day rotation, and database restore runbooks. |
| **Client Applications Guide** | [`deploy/CLIENT_SETUP_GUIDE.md`](deploy/CLIENT_SETUP_GUIDE.md) | Multi-device installation manual for Windows Desktop Apps (.msi / Tauri) and Rugged Tablet PWAs. |

---

## 4. Quick Demonstration Credentials

The application login screen at `http://localhost:3000/login` includes one-click role selector buttons for instant testing across all operational personas:

| Persona | Test Email | Password | Default Landing Hub | Primary Clearance |
| :--- | :--- | :--- | :--- | :--- |
| **Operator / Driver** | `operator@bikita.com` | `password123` | `/my-work` | Pre-start machinery inspection checklist, fault logging, hazard alerts |
| **Technician / Artisan** | `tech@bikita.com` | `password123` | `/my-work` | LOTO isolation, live labor timer, spares requisitions, Lead Artisan signature |
| **Supervisor / Shift Boss** | `supervisor@bikita.com` | `password123` | `/jobs` | Shift Kanban, dispatch artisans, QA verification endorsement |
| **Dept Manager / Superintendent** | `mechmgr@bikita.com` | `password123` | `/approvals` | Multi-tier cost approvals, SLA governance, formal Superintendent closure seal |
| **Resource Coordinator** | `coordinator@bikita.com` | `password123` | `/fleet` | Equipment fleet management, machinery dispatch, plant requisitions |
| **Safety Officer (HSE)** | `safety@bikita.com` | `password123` | `/dashboard` | Immutable audit stream, LOTO compliance verification, safety dashboards |
| **Administrator** | `admin@bikita.com` | `password123` | `/admin/system` | Host telemetry, organizational tree, platform maintenance, automated backups |

---

## 5. Server Deployment (Automated Master Installer)

For production deployment on dedicated Ubuntu Server instances (22.04 LTS / 24.04 LTS):

### Single-Command Quick Install (Remote Server)

```bash
curl -fsSL https://raw.githubusercontent.com/Aomine-c2c/jbc/main/install.sh | sudo bash
```

### Or Run Locally from Repository

```bash
sudo chmod +x install.sh
sudo ./install.sh
```

#### What `install.sh` provisions automatically

1. **Host Dependencies**: Docker CE, Docker Compose plugin, UFW firewall, OpenSSL, curl, and jq.
2. **Storage Structure**: Provisions and permissions `/var/dwrms/storage`, `/var/dwrms/backups`, and `/var/dwrms/logs` (`0750`).
3. **Network Security**: UFW lockdown allowing HTTP (`80`), HTTPS (`443`), and SSH (`22`) while isolating internal database ports.
4. **Environment & TLS**: Generates production `.env` with cryptographically secure secret keys and self-signed TLS certificates for Nginx.
5. **Database & RBAC**: Boots PostgreSQL 16, runs Alembic migrations, and seeds baseline roles and admin accounts.
6. **Full Stack Startup**: Launches Backend, Frontend, Celery Worker, Celery Beat, and Nginx.
7. **Systemd Recovery & Watchdogs**: Enables `dwrms.service` (auto-restart on crash/power recovery), healthcheck timers, and daily backups at 02:00 CAT (`dwrms-backup.timer`).

---

## 6. Development & Local Run

### One-Command Developer Mode Launcher (`run.sh` / `run.bat` / `run.ps1`)

The repository includes authoritative cross-platform developer launchers that automatically verify system prerequisites (Python 3.10+, Node.js 18+, npm), configure `.env`, create `.venv`, install pip/npm dependencies, initialize the database schema, resolve port conflicts (8000 / 3000), and run services with live hot-reloading:

#### Linux & macOS

```bash
# Interactive selection menu:
./run.sh
# or via shortcut:
./run

# Or launch directly with commands:
./run.sh all         # Launch full stack (FastAPI Backend + Next.js Frontend concurrently)
./run.sh backend     # Launch FastAPI backend with live reload (http://127.0.0.1:8000)
./run.sh frontend    # Launch Next.js web application (http://localhost:3000)
./run.sh tauri       # Launch Backend & Tauri Desktop development app
./run.sh deps        # Verify and install dependencies & initialize database
```

#### Windows (Command Prompt & PowerShell)

```cmd
:: Windows Command Prompt:
run.bat
run.bat all
run.bat backend
run.bat frontend
run.bat tauri
run.bat deps
```

```powershell
# Windows PowerShell:
.\run.ps1
.\run.ps1 all
```

### Prerequisites

- **Node.js**: v20+ (with npm)
- **Python**: v3.12+ (or `.venv` in `/backend`)
- **Docker** + Docker Compose plugin (for containerized dev)
- **Rust** (optional, for Tauri desktop builds)

### Manual Service Execution (Web Mode — No Rust Required)

```bash
# Terminal 1: FastAPI backend
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Next.js frontend
cd frontend
npm run dev
```

### Desktop Native App Execution (Optional — Requires Rust & Cargo)

```powershell
cd frontend
npm run tauri:dev
```

*Note: Running `npm run tauri:dev` launches Tauri's native desktop shell, which requires the [Rust toolchain](https://rustup.rs/) and C++ build tools. If you do not have Rust installed, use `run.bat all` or the Web Mode above.*

### Run Production Build & Lint Verification

```powershell
cd frontend
npm run build
```

```powershell
npm run lint
```

### Docker-Based Local Development

```bash
# Start PostgreSQL, Redis, backend, worker, and frontend (with live DB init & seeding)
docker compose -f infrastructure/docker-compose.yml up --build

# Services: Frontend at http://localhost:3000, API at http://localhost:8000
```

### Backend Development

```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate    # Linux/WSL
# .venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Initialize database & seed demo data
python init_db_all.py
python seed.py
python seed_rbac.py
python seed_faker.py

# Start backend with auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
pytest tests/ -v
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm ci

# Start dev server
npm run dev

# Run unit/component tests
npm run test

# Run E2E tests (Playwright)
npx playwright test
```

### API Documentation

- **Swagger UI**: `http://localhost:8000/api/docs` (auto-disabled in production)
- **ReDoc**: `http://localhost:8000/api/redoc` (auto-disabled in production)

For the complete developer guide, see [`docs/DEVELOPER_GUIDE.md`](docs/DEVELOPER_GUIDE.md).

---

## 7. Platform Administration CLI (`ops`)

The `ops` command is the unified administrative interface for installed servers. See [`docs/INTERFACE_MODES.md`](docs/INTERFACE_MODES.md) for the full reference.

### Key Commands

```bash
ops status              # Real-time platform status & container health
ops health              # Deep subsystem readiness probe
ops logs -s app -f      # Stream structured logs in real-time
ops backup create       # Create disaster recovery snapshot
ops restore <snapshot>  # Restore from backup
ops update apply        # 8-step controlled platform upgrade
ops update rollback     # Emergency rollback to pre-upgrade snapshot
ops monitor             # Interactive TUI dashboard (live telemetry)
ops version             # Display platform version matrix
```

### Interactive Operations TUI

```bash
ops monitor
```

Launches a full-screen terminal dashboard showing container status, host hardware telemetry (CPU/RAM/disk), dual IP endpoints (LAN + Tailscale), auto-update status, and recent log telemetry. Keyboard controls: `q` (quit), `r` (refresh), `u` (check updates), `l` (view logs).

---

## 8. Version Upgrades & Migrations

The platform uses a controlled 8-step upgrade pipeline with automatic safety snapshots:

```bash
# Check current version matrix
ops update matrix

# Check for available updates
ops update check

# Apply platform update (with pre-upgrade backup, migrations, and health verification)
ops update apply

# Emergency rollback (1-command)
ops update rollback
```

The upgrade pipeline:
1. Validates current system health
2. Checks version compatibility (minimum client: `v2.0.0`)
3. Creates pre-upgrade safety snapshot (`dwrms_backup_pre_upgrade_*.tar.gz`)
4. Applies staged code deployment
5. Runs transactional Alembic schema migrations
6. Restarts services with zero downtime
7. Runs post-update health checks
8. Verifies critical workflows (auth, job cards, requisitions)

For the complete upgrade and migration guide, see [`docs/UPGRADE_AND_MIGRATION_GUIDE.md`](docs/UPGRADE_AND_MIGRATION_GUIDE.md).

---

## 9. Cross-Platform Setup

| Platform | Guide |
|:---|:---|
| **Ubuntu Server** (Production) | [`docs/CROSS_PLATFORM_SETUP.md`](docs/CROSS_PLATFORM_SETUP.md) — Automated `install.sh` with Docker, firewall, TLS, systemd |
| **Windows Workstations** (Clients) | [`deploy/CLIENT_SETUP_GUIDE.md`](deploy/CLIENT_SETUP_GUIDE.md) — MSI/GPO rollout, Tauri desktop .exe |
| **Linux Development** | [`docs/CROSS_PLATFORM_SETUP.md`](docs/CROSS_PLATFORM_SETUP.md) — Docker compose, manual setup |
| **Windows Development** | [`docs/CROSS_PLATFORM_SETUP.md`](docs/CROSS_PLATFORM_SETUP.md) — WSL2 or native, PowerShell packaging scripts |
| **Rugged Tablets / Mobile** | [`deploy/CLIENT_SETUP_GUIDE.md`](deploy/CLIENT_SETUP_GUIDE.md) — PWA installation, offline sync, Android Enterprise APK |

For the comprehensive installation and dependency management guide, see [`docs/INSTALLATION_AND_DEPENDENCIES.md`](docs/INSTALLATION_AND_DEPENDENCIES.md).
