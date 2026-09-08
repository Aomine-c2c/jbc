# Bikita Minerals DWRMS - Digital Work Request & Resource Management System

**Authoritative Industrial Operations, Heavy Fleet Management & Cross-Departmental Governance Core**  
*Enterprise Platform Architecture for Bikita Minerals Lithium Operations (Version 2.9.0)*

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
| **Workstations & Laptops** | [`dist/desktop/DWRMS_2.9.0_x64-setup.exe`](dist/desktop/DWRMS_2.9.0_x64-setup.exe) | **2.64 MB** | `a49529a10d8ff8bda74f05d2c1ea7f93062677454cd58af4d4c585e410916dd8` | Self-contained Windows installer for workshop PCs & rugged field laptops |
| **Active Directory Rollout** | [`dist/desktop/DWRMS_2.9.0_x64_en-US.msi`](dist/desktop/DWRMS_2.9.0_x64_en-US.msi) | **3.62 MB** | `78954c114608250af5d62f76d37e2ed40d74f6b2b0d0a762e1461fb0d4703a6a` | Silent GPO / SCCM domain-wide installation across mine office PCs |
| **Rugged Tablets & Mobile** | [`dist/tablet-mobile-pwa/`](dist/tablet-mobile-pwa/) | **~102 KB** | *Verified Service Worker + Manifest + Icons* | Offline PWA app shell for Samsung Galaxy Tab Active, Zebra & iOS/Android devices |
| **Android Enterprise (MDM)** | [`dist/android/BUILD_INSTRUCTIONS.txt`](dist/android/BUILD_INSTRUCTIONS.txt) | **~1 KB** | *Tauri Android APK generation pipeline* | Standalone APK build configuration for corporate mobile device managers |

### Build Setups for All Devices in One Command:
```powershell
.\deploy\build-all-device-setups.ps1
```

### Build Specific Device Profiles:
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
