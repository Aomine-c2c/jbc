# Bikita Minerals DWRMS - Digital Work Request & Maintenance System

**Industrial Operations, Heavy Fleet Management & Cross-Departmental Governance Core**  
*Enterprise Solution for Bikita Minerals Lithium Operations*

---

## 1. System Documentation & Operational Guides

| Document | File Path | Focus & Target Audience |
| :--- | :--- | :--- |
| **Master System Documentation** | [`docs/SYSTEM_DOCUMENTATION.md`](docs/SYSTEM_DOCUMENTATION.md) | Enterprise architecture, 10 mining departments, state machine lifecycle, 6-role RBAC matrix, and offline sync. |
| **6-Role Interactive Demo Walkthrough** | [`docs/ROLE_DEMO_WALKTHROUGH.md`](docs/ROLE_DEMO_WALKTHROUGH.md) | Step-by-step interactive demonstration script centered on CAT 777D Haul Truck breakdown and repair scenario. |
| **API & Operations Manual** | [`docs/API_OPERATIONS_MANUAL.md`](docs/API_OPERATIONS_MANUAL.md) | Authoritative REST API endpoint specifications, parameters, response formats, and security clearances. |
| **Autonomous Server Setup Guide** | [`infrastructure/scripts/setup_autonomous_server.sh`](infrastructure/scripts/setup_autonomous_server.sh) | 1-click master provisioning script for Ubuntu Linux host (Systemd auto-restart, Watchdogs, Nginx, Backups). |
| **Client Applications Setup Guide** | [`deploy/CLIENT_SETUP_GUIDE.md`](deploy/CLIENT_SETUP_GUIDE.md) | IT deployment manual for Windows Desktop Apps (.msi / Tauri) and Rugged Tablet PWAs. |

---

## 2. Quick Demonstration Credentials

The application login screen at `http://localhost:3000/login` includes one-click role selector buttons for instant testing across all six operational personas:

| Persona | Test Email | Password | Default Landing Hub | Primary Clearance |
| :--- | :--- | :--- | :--- | :--- |
| **Operator / Driver** | `operator@bikita.com` | `password123` | `/my-work` | Basic fault logging, safety hazard alerts |
| **Technician / Artisan** | `tech@bikita.com` | `password123` | `/my-work` | LOTO isolation, live labor timer, spares requisitions, Lead Artisan signature |
| **Supervisor / Shift Boss** | `supervisor@bikita.com` | `password123` | `/dashboard` | Shift Kanban, dispatch artisans, QA verification endorsement |
| **Dept Manager / Superintendent** | `mechmgr@bikita.com` | `password123` | `/dashboard` | Multi-tier cost approvals, SLA governance, formal Superintendent closure seal |
| **Safety Officer (HSE)** | `safety@bikita.com` | `password123` | `/dashboard` | Immutable audit stream, LOTO compliance verification |
| **Administrator** | `admin@bikita.com` | `password123` | `/dashboard` | Host telemetry, organizational tree, automated 30-day backups |

---

## 3. Quick Start (Development & Local Run)

### Prerequisites

- **Node.js**: v20+
- **Python**: v3.12+ (or `.venv` in `/backend`)

### Launch All Services

```powershell
# In frontend directory
cd frontend
npm run tauri:dev
```

*Starts the FastAPI backend daemon (`http://localhost:8000`), Next.js Turbo dev server (`http://localhost:3000`), and Tauri Desktop runtime concurrently.*

### Production Build Verification

```powershell
cd frontend
npm run build
```

*Compiles all 28 application routes with strict TypeScript and RBAC route guard validation.*
