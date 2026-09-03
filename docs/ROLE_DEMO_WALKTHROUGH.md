# Bikita Minerals DWRMS - 6-Role Interactive Demonstration Walkthrough

**Interactive Step-by-Step Live Demo Script**  
*Featured Scenario: CAT 777D Haul Truck #04 Hydraulic Steering Failure in Open Pit Cut 3*

---

## 1. Demonstration Credentials & Persona Switcher

The DWRMS login screen includes one-click role selector buttons for instant persona switching during demonstrations.

| Persona / Role | Email | Password | Default Landing Hub | Primary Demo Responsibilities |
| :--- | :--- | :--- | :--- | :--- |
| **Operator / Driver** | `operator@bikita.com` | `password123` | `/my-work` | Log breakdown faults, report safety hazards |
| **Technician / Artisan** | `tech@bikita.com` | `password123` | `/my-work` | Lockout/Tagout (LOTO), live timer, request spares, lead artisan sign-off |
| **Supervisor / Shift Boss** | `supervisor@bikita.com` | `password123` | `/dashboard` | Shift Kanban, dispatch artisans, QA verification endorsement |
| **Dept Manager / Superintendent** | `mechmgr@bikita.com` | `password123` | `/dashboard` | High-risk approvals, SLA governance, formal closure seal |
| **Safety Officer (HSE)** | `safety@bikita.com` | `password123` | `/dashboard` | Audit immutable log streams, verify LOTO isolation compliance |
| **Administrator** | `admin@bikita.com` | `password123` | `/dashboard` | Platform telemetry, organization structure, automated backups |

---

## 2. End-to-End Operational Lifecycle Demo

### Phase 1: Operator / Driver (Open Pit Cut 3)

*Goal: Log an urgent breakdown fault directly from a rugged tablet in the field.*

1. **Sign In**:
   - Navigate to `/login`.
   - Click the **"Operator"** quick credential card (`operator@bikita.com`).
   - Notice the system automatically routes the Operator to the **My Work Hub** (`/my-work`).
2. **Log the Breakdown Fault**:
   - Click **"+ Log Breakdown / Fault"** (routes to `/jobs/new`).
   - Fill in the fault details:
     - **Title**: `CAT 777D Haul Truck #04 - Hydraulic Steering Pressure Loss`
     - **Department**: `Mechanical Maintenance` (or `Mining Operations`)
     - **Priority**: `CRITICAL (P1)`
     - **Asset / Machine**: `CAT-777D-04 (Heavy Haul Truck)`
     - **Plant Area / Location**: `Open Pit - Cut 3 Haul Road Ramp`
     - **Description**: `Steering booster pump pressure dropped below 1,200 PSI during uphill haul. Machine safely parked in emergency bay.`
   - Click **"Create Job Card"**.
   - Notice the job is created with state `DRAFT / SUBMITTED` and appears in the work queue.

---

### Phase 2: Technician / Artisan (Workshop & Field Bay)

*Goal: Enforce Lockout/Tagout (LOTO), start repair timer, requisition spare parts, and sign lead artisan endorsement.*

1. **Sign In**:
   - Navigate to `/login` and select **"Technician"** (`tech@bikita.com`).
   - Notice the Technician lands on **My Work Hub** (`/my-work`) with assigned tasks.
2. **Accept Job & Apply Safety Lockout (LOTO)**:
   - Click on the new CAT 777D job card to open the **Interactive Job Card Detail Console** (`/jobs/[id]`).
   - Click **"Acknowledge & Start Work"**.
   - Enter LOTO Isolation Tag: `LOTO-2026-881` and check **"Isolation Points Confirmed"**.
   - Click **"Start Live Timer"**. Notice the live stopwatch timer begins tracking billable labor hours.
3. **Requisition Spares from Warehouse**:
   - Scroll to **Required Materials & Spares**.
   - Add spare part:
     - **Part Name**: `Hydraulic Steering Cylinder Seal Kit`
     - **Part #**: `CAT-HYD-9920`
     - **Quantity**: `2`
     - **Unit Cost**: `$345.00`
   - Click **"Add Spare Part"**.
4. **Complete Work & Sign Endorsement**:
   - Record Final Meter Hours: `12,454 hrs` (Start: `12,450 hrs`).
   - Click **"Complete Job"**.
   - In the Signature Pad modal, draw/enter the digital signature for **Lead Artisan: Farai Moyo**.
   - Click **"Submit for QA Supervisor Verification"**. State advances to `COMPLETED / PENDING_REVIEW`.

---

### Phase 3: Shift Supervisor / Shift Boss (Workshop Office)

*Goal: Review technician's execution report, perform QA inspection, and sign supervisor endorsement.*

1. **Sign In**:
   - Navigate to `/login` and select **"Supervisor"** (`supervisor@bikita.com`).
   - Lands on **Operations Dashboard** (`/dashboard`) showing Shift View KPIs.
2. **Review Shift Kanban**:
   - Navigate to **Work Hub** (`/work`). Notice the Kanban board with columns: *Backlog, In Progress, Under QA Review, Completed*.
3. **QA Inspection & Endorsement**:
   - Open the CAT 777D job card.
   - Review the recorded labor duration, meter hours, and materials breakdown.
   - Click **"QA Supervisor Verify"**.
   - Sign the digital signature pad for **Shift Supervisor: Tendai Shumba**.
   - State advances to `VERIFIED`.

---

### Phase 4: Department Manager / Superintendent (Engineering Directorate)

*Goal: Authorize multi-tier high-risk approvals, review departmental SLA governance, and apply formal closure seal.*

1. **Sign In**:
   - Navigate to `/login` and select **"Dept Manager"** (`mechmgr@bikita.com`).
   - Lands on **Operations Dashboard** (`/dashboard`) showing Departmental Cost & SLA compliance.
2. **Approvals Inbox**:
   - Navigate to **Approvals Inbox** (`/approvals`).
   - Notice high-risk and material cost threshold approval requests awaiting Superintendent authorization.
   - Click **"Approve Requisition"** to authorize warehouse spares release.
3. **Formal Digital Handover & Closure**:
   - Navigate to the job card detail page.
   - Click **"Handover Certificate"** to open the **Official Digital Job Handover Certificate**.
   - Notice the 3 signature slots:
     - ✅ **Lead Technician**: Signed & Cryptographically Stamped
     - ✅ **Workshop Supervisor**: Approved & Verified
     - ✍️ **Superintendent / HSE Seal**: Ready for Archive
   - Click **"Formal Sign-off & Close"** to archive the record into permanent compliance storage.

---

### Phase 5: Safety Officer (HSE Directorate)

*Goal: Conduct safety audit, verify LOTO isolation compliance, and inspect immutable system audit stream.*

1. **Sign In**:
   - Navigate to `/login` and select **"Safety Officer"** (`safety@bikita.com`).
   - Notice navigation is restricted to Compliance, Assets, Fleet Safety, and Audit Logs.
2. **Audit Immutable System Trail**:
   - Navigate to **Audit Logs & Compliance** (`/admin/audit`).
   - Inspect the real-time immutable audit stream showing every state transition, LOTO tag application, and user signature with cryptographic hashes.
3. **Verify Fleet Health & Incidents**:
   - Navigate to **Fleet & Machines** (`/fleet`).
   - Verify the CAT 777D status has transitioned from *Under Maintenance* back to *Available / Operating*.

---

### Phase 6: System Administrator (Platform & Infrastructure)

*Goal: Inspect server telemetry, monitor self-healing watchdogs, and manage organizational hierarchy.*

1. **Sign In**:
   - Navigate to `/login` and select **"Admin"** (`admin@bikita.com`).
   - Full access across all 28 modules and administrative tools.
2. **Server Diagnostics & Telemetry**:
   - Navigate to **Platform System Telemetry** (`/admin/system`).
   - Verify client type (*Modern Web / Tauri Desktop*), backend latency (< 5 ms), and database integrity.
   - Click **"Configure Server Node"** to display the LAN Quick-Connect QR Code.
3. **Subsystem Matrix & Backups**:
   - Navigate to **Platform Infrastructure** (`/admin/platform`).
   - Review the 7-subsystem matrix (Application, Database, Storage, Worker, Tasks, Security, Network).
   - Inspect automated backup history and verify 30-day retention policies.
