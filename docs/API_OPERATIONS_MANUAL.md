# Bikita Minerals DWRMS - API & Operations Manual

**Authoritative REST API Reference & System Operations Manual**  
*Base URL: `http://<server-host>:8000` or `/api/v1` via Nginx Reverse Proxy*

---

## 1. Authentication & Identity Management (`/api/v1/iam`)

| Method | Endpoint | Description | Clearance Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/iam/auth/login` | Authenticate user credentials, set HTTP-only cookie, and issue JWT bearer token | Public |
| `POST` | `/api/v1/iam/auth/logout` | Revoke active session token and CSRF cookie | Authenticated |
| `GET` | `/api/v1/iam/users` | List all system personnel, positions, and assigned RBAC roles | `users:manage` / Admin |
| `POST` | `/api/v1/iam/users` | Create new staff account with department mapping and initial role | `users:manage` / Admin |
| `PATCH` | `/api/v1/iam/users/{id}` | Update user attributes, active status, or supervisory chain | `users:manage` / Admin |
| `GET` | `/api/v1/iam/departments` | List all 10 operational departments with SLA hours defaults | Authenticated |

---

## 2. Job Cards & Work Order Lifecycle (`/api/v1/job-cards`)

| Method | Endpoint | Description | Clearance Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/job-cards` | Query job cards registry with filters (`status`, `priority`, `department_id`, `search`) | `jobs:view` |
| `POST` | `/api/v1/job-cards` | Create new breakdown fault or planned maintenance work order | `job_card:create` |
| `GET` | `/api/v1/job-cards/{id}` | Fetch full specification, report materials, LOTO tags, and activity history | `jobs:view` |
| `POST` | `/api/v1/job-cards/{id}/submit` | Submit draft work order for supervisor / superintendent approval | `job_card:create` |
| `POST` | `/api/v1/job-cards/{id}/approve` | Authorize work order execution and dispatch artisans | `job_card:approve` |
| `POST` | `/api/v1/job-cards/{id}/start` | Apply LOTO tag and begin live labor tracking timer | `job_card:update` |
| `POST` | `/api/v1/job-cards/{id}/hold` | Place work order on pause (e.g. awaiting warehouse spares) | `job_card:update` |
| `POST` | `/api/v1/job-cards/{id}/resume` | Resume work order execution after hold | `job_card:update` |
| `POST` | `/api/v1/job-cards/{id}/complete` | Record meter hours, submit Lead Artisan digital signature | `job_card:update` |
| `POST` | `/api/v1/job-cards/{id}/verify` | Perform QA inspection and record Workshop Supervisor signature | `job_card:verify` |
| `POST` | `/api/v1/job-cards/{id}/close` | Apply formal Superintendent Closure Seal and archive work order | `job_card:verify` |
| `POST` | `/api/v1/job-cards/{id}/cancel` | Permanently cancel work order with logged audit reason | `job_card:create` |

---

## 3. Universal Requests & Requisitions (`/api/v1/requests`)

| Method | Endpoint | Description | Clearance Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/requests` | List cross-departmental requisitions (machinery, spares, labor, transport) | `requisition:create` |
| `POST` | `/api/v1/requests` | Submit new universal requisition request with required dates and items | `requisition:create` |
| `GET` | `/api/v1/requests/{id}` | Fetch requisition detail, approval steps, and fulfillment logs | `requisition:create` |
| `POST` | `/api/v1/requests/{id}/approve` | Authorize requisition for warehouse dispatch | `requisition:approve` |
| `POST` | `/api/v1/requests/{id}/fulfill` | Record warehouse item issue or machine allocation | `requisition:allocate` |

---

## 4. Multi-Tier Approvals Inbox (`/api/v1/approvals`)

| Method | Endpoint | Description | Clearance Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/approvals/pending` | Query actionable approval requests for the current user's authority role | `approvals:view` |
| `POST` | `/api/v1/approvals/{id}/decision` | Record digital approval or return with comments and signature hash | `job_card:approve` |
| `GET` | `/api/v1/approvals/{id}/certificate` | Retrieve cryptographic approval verification certificate | `approvals:view` |

---

## 5. Assets & Machine Fleet Registry (`/api/v1/assets`, `/api/v1/fleet`)

| Method | Endpoint | Description | Clearance Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/assets` | Query equipment registry with health scores, meter hours, and criticalities | `assets:view` |
| `POST` | `/api/v1/assets` | Register new heavy machine, processing unit, or electrical asset | `assets:create` |
| `GET` | `/api/v1/fleet/machines` | List heavy mobile fleet units with real-time operational statuses | `fleet:view` |
| `POST` | `/api/v1/fleet/allocations` | Allocate machine to open pit cut or haulage shift | `fleet:allocate` |

---

## 6. Materials & Stores Warehouse (`/api/v1/materials`)

| Method | Endpoint | Description | Clearance Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/materials/stock` | Query inventory stock levels, reorder thresholds, and bin locations | `materials:view` |
| `POST` | `/api/v1/materials/issue` | Issue spare parts against an approved Job Card number | `materials:issue` |
| `POST` | `/api/v1/materials/receive` | Record incoming purchase order delivery into warehouse | `materials:manage` |

---

## 7. Platform Telemetry & System Diagnostics (`/api/v1/info`, `/api/v1/platform`)

| Method | Endpoint | Description | Clearance Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/info` | Public host diagnostics, database version, and server environment | Public |
| `GET` | `/api/v1/health` | Fast watchdog health probe (< 10 ms response) | Public |
| `GET` | `/api/v1/platform/status` | Real-time 7-subsystem status matrix and resource telemetry | `platform:manage` |
| `POST` | `/api/v1/platform/backups` | Trigger immediate on-demand atomic backup snapshot | `platform:manage` |
| `GET` | `/api/v1/audit/logs` | Query immutable cryptographic system audit log stream | `audit:view` |
