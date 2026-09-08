# Bikita Minerals DWRMS - Digital Work Request & Resource Management System

**Authoritative Industrial Operations, Heavy Fleet Management & Cross-Departmental Governance Core**  
*Enterprise Platform Architecture for Bikita Minerals Lithium Operations (Version 2.9.0)*

---

## 1. Multi-Device & Cross-Platform Support Matrix

Bikita Minerals DWRMS is architected for seamless multi-device deployment across the full spectrum of mining and engineering workflows—from open-pit heavy equipment operators to executive superintendents:

| Device Category | Target Persona / Hardware | Form Factor & Ingress | Key Capabilities | Deployment Method |
| :--- | :--- | :--- | :--- | :--- |
| **Desktop Workstations** | Control Room Engineers, Plant Superintendents, Planners, IT Admins | 1920x1080+ Monitors, Dual-Screen Control Consoles | Multi-panel telemetry, live fleet radar, complex shift gantt charts, and administrative system configuration. | Native Windows App (`.exe` / `.msi`) or Modern Desktop Browsers (Chrome / Edge / Firefox) |
| **Field Laptops** | Mobile Maintenance Supervisors, Field Inspectors, Electrical Techs | 13"–16" Rugged Laptops (Panasonic Toughbook, Dell Rugged) | Full offline draft preservation, batch job card sign-offs, and remote mesh connectivity via Tailscale. | Native Windows App (`.exe` installer) or Desktop Web App |
| **Rugged Tablets** | Machine Operators, Heavy Haulage Drivers, Field Artisans | 8"–11" Touch Displays (Samsung Galaxy Active, Zebra ET5x) | Glove-friendly high-contrast UI, Pre-Start Inspection modals, capacitive touch digital signatures, and offline PWA storage. | Progressive Web App (PWA) with Standalone Homescreen Launch |
| **Mobile Handhelds** | Roving Safety Officers (HSE), Shift Bosses, Requisition Requesters | 5.5"–6.7" iOS & Android Mobile Devices | Mobile Bottom Navigation drawer, instant photo/hazard report uploads, push notifications, and quick approvals. | Mobile Responsive Web (Next.js responsive layout) / PWA |

---

## 2. Desktop Packaging & Distribution Artifacts

The native Windows desktop packages are pre-compiled and verified in [`frontend/src-tauri/target/release/bundle/`](frontend/src-tauri/target/release/bundle/):

| Package Format | Output Location | Size | SHA-256 Checksum | Target Deployment |
| :--- | :--- | :---: | :--- | :--- |
| **NSIS Setup (.exe)** | [`frontend/src-tauri/target/release/bundle/nsis/DWRMS_2.9.0_x64-setup.exe`](frontend/src-tauri/target/release/bundle/nsis/DWRMS_2.9.0_x64-setup.exe) | **2.64 MB** | `a49529a10d8ff8bda74f05d2c1ea7f93062677454cd58af4d4c585e410916dd8` | Self-contained Windows installer for workstations and field laptops |
| **Windows Installer (.msi)** | [`frontend/src-tauri/target/release/bundle/msi/DWRMS_2.9.0_x64_en-US.msi`](frontend/src-tauri/target/release/bundle/msi/DWRMS_2.9.0_x64_en-US.msi) | **3.62 MB** | `78954c114608250af5d62f76d37e2ed40d74f6b2b0d0a762e1461fb0d4703a6a` | Enterprise Active Directory / Group Policy (GPO) silent domain rollout |

To compile fresh desktop binaries from source:
```powershell
.\deploy\build-desktop-apps.ps1
```

---

## 3. System Documentation & Operational Manuals

| Document | File Path | Focus & Target Audience |
| :--- | :--- | :--- |
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

#### What `install.sh` provisions automatically:
1. **Host Dependencies**: Docker CE, Docker Compose plugin, UFW firewall, OpenSSL, curl, and jq.
2. **Storage Structure**: Provisions and permissions `/var/dwrms/storage`, `/var/dwrms/backups`, and `/var/dwrms/logs` (`0750`).
3. **Network Security**: UFW lockdown allowing HTTP (`80`), HTTPS (`443`), and SSH (`22`) while isolating internal database ports.
4. **Environment & TLS**: Generates production `.env` with cryptographically secure secret keys and self-signed TLS certificates for Nginx.
5. **Database & RBAC**: Boots PostgreSQL 16, runs Alembic migrations, and seeds baseline roles and admin accounts.
6. **Full Stack Startup**: Launches Backend, Frontend, Celery Worker, Celery Beat, and Nginx.
7. **Systemd Recovery & Watchdogs**: Enables `dwrms.service` (auto-restart on crash/power recovery), healthcheck timers, and daily backups at 02:00 CAT (`dwrms-backup.timer`).

---

## 6. Development & Local Run

### Prerequisites
- **Node.js**: v20+
- **Python**: v3.12+ (or `.venv` in `/backend`)

### Launch All Services Concurrently
```powershell
cd frontend
npm run tauri:dev
```
*Starts the FastAPI backend daemon (`http://localhost:8000`), Next.js App Router (`http://localhost:3000`), and native Tauri Desktop window.*

### Run Production Build & Lint Verification
```powershell
cd frontend
npm run build
npm run lint
```
