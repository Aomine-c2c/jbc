# Secure Remote Connectivity Guide (Optional Transport Layer)

> **Bikita Minerals Industrial Operations Platform (DWRMS)**  
> **Version 2.6 — Server-First Platform Architecture**  
> **Authoritative Node**: Ubuntu Server 22.04 LTS / 24.04 LTS (`masvingo-srv-01`)

---

## 1. Architectural Philosophy: Transport Layer Agnosticism

The Bikita Minerals DWRMS platform treats secure remote networks (such as Tailscale, WireGuard, Cloudflare Tunnels, or Corporate VPNs) **strictly as an optional transport layer**.

### 1.1 Invariant Security Model

Remote network connectivity establishes encrypted network reachability; it **never** replaces or bypasses the application security hierarchy:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                APPLICATION SECURITY CHAIN                              │
└────────────────────────────────────────────────────────────────────────────────────────┘

  1. TRANSPORT LAYER        → Local LAN / Internal DNS / Tailscale / WireGuard / Mesh VPN
         ↓
  2. APPLICATION AUTH       → Cryptographic JWT & Password Credentials (No anonymous access)
         ↓
  3. RBAC ENFORCEMENT       → Role Capabilities (job_card:create, settings:manage, etc.)
         ↓
  4. OBJECT-LEVEL AUTH      → AuthzGuard (Department, Equipment & Work Order Scope)
         ↓
  5. WORKFLOW AUTHORITY     → Approval Thresholds (HOD Limits & Emergency Sign-offs)
```

> [!IMPORTANT]
> **No Vendor Dependency**: The platform is 100% provider-agnostic. The core application logic has zero direct dependencies on Tailscale or any specific third-party networking vendor. Any secure overlay network or standard LAN/DNS configuration can be used.

---

## 2. Supported Deployment Modes

### MODE 1 — Local Network Only (Default)

Ideal for self-contained mine site installations where all client devices reside within the on-premises mining LAN or dedicated operational Wi-Fi.

* **Client Reachability**: Internal domain (`https://dwrms.bikita.local`), internal DNS, or server LAN IP (`http://192.168.10.50:8000`).
* **Remote Networking**: Disabled (`REMOTE_CONNECTIVITY_ENABLED=false`).
* **Security Surface**: Zero external or public network ingress; isolated by local network boundaries.

```text
  [ Mining Plant LAN / Wi-Fi ]
  ├── Rugged Tablets (PWA) ──────┐
  ├── Maintenance Workstations ──┼──► [ Ubuntu Server: masvingo-srv-01 ]
  └── Tauri Desktop Clients ─────┘    (192.168.10.50 / dwrms.bikita.local)
```

---

### MODE 2 — Local Network + Optional Secure Remote Access (Hybrid)

Ideal for active mining operations where on-site personnel connect directly via high-speed LAN/Wi-Fi, while traveling engineers, executive managers, and off-site supervisors connect securely over an encrypted mesh overlay (e.g. Tailscale or WireGuard).

* **On-Site Access**: High-speed direct LAN / internal DNS.
* **Remote Access**: Encrypted point-to-point tunnel via Tailscale (`100.x.y.z` or MagicDNS) or WireGuard.
* **Failover Capability**: Client desktop and mobile applications automatically probe LAN addresses with fallback to the secure remote URL.

```text
  [ Local Plant LAN ]                      [ Remote / Off-Site Users ]
  ├── On-site Tablets (LAN) ─────┐          ├── Mobile Field App (Remote Mesh) ──┐
  └── Local Workstations (LAN) ──┤          └── Laptop Client (Tailscale / VPN) ─┤
                                 ▼                                               ▼
                     [ Ubuntu Server Gateway ] ◄─────────────────────────────────┘
                     • LAN IP: 192.168.10.50
                     • Mesh IP: 100.64.12.34 (Tailscale / WireGuard)
```

---

### MODE 3 — Private Distributed Deployment

Ideal for multi-site mining enterprises operating across several geographical pits, processing facilities, and regional offices (e.g. Bikita Pit, Masvingo Regional Office, Harare HQ).

* **Primary Transport**: Dedicated private overlay network / Zero Trust mesh connecting all operational nodes.
* **Decentralized Clients**: Clients across all facilities connect over the encrypted overlay directly to the authoritative central Ubuntu Server core.

---

## 3. Server Configuration & Environment Variables

Remote connectivity is configured declaratively in `/opt/dwrms/.env` without exposing any secrets:

```ini
# /opt/dwrms/.env — Transport Layer Configuration

# Deployment Mode: LOCAL_ONLY | HYBRID_REMOTE | PRIVATE_DISTRIBUTED
DEPLOYMENT_MODE=HYBRID_REMOTE

# Enable Remote Transport Layer Telemetry
REMOTE_CONNECTIVITY_ENABLED=true

# Remote Network Provider: none | tailscale | wireguard | custom_vpn | zero_trust
REMOTE_NETWORK_PROVIDER=tailscale

# Virtual Interface Name to Monitor (e.g. tailscale0, wg0, tun0)
REMOTE_NETWORK_INTERFACE=tailscale0

# Optional Hostname or Assigned Mesh IP
REMOTE_NETWORK_HOSTNAME=masvingo-srv-01.bikita.ts.net
REMOTE_NETWORK_IP=100.64.12.34
```

> [!TIP]
> **Zero Secret Leakage**: The platform API and UI **never** display or return private auth keys, pre-shared WireGuard keys, or authentication tokens. Only runtime status (`CONNECTED`, `STANDBY`, `DISABLED`), active interface, and virtual IP are displayed to authorized administrators.

---

## 4. Setting Up Tailscale on Ubuntu Server (Optional)

To enable optional Tailscale connectivity on the Ubuntu Server:

```bash
# 1. Run the automated remote mesh setup helper
sudo /opt/dwrms/infrastructure/scripts/setup-remote-mesh.sh tailscale

# 2. Authenticate the node to your Tailscale tailnet
sudo tailscale up --hostname=dwrms-server-masvingo --ssh

# 3. Verify Tailscale IP
tailscale ip -4
```

---

## 5. Setting Up WireGuard on Ubuntu Server (Optional)

To enable optional WireGuard point-to-point connectivity:

```bash
# 1. Run the setup helper for WireGuard
sudo /opt/dwrms/infrastructure/scripts/setup-remote-mesh.sh wireguard

# 2. Place server configuration in /etc/wireguard/wg0.conf
# 3. Enable and start WireGuard systemd service
sudo systemctl enable --now wg-quick@wg0
```

---

## 6. Remote Connectivity Telemetry & Verification

### 6.1 Inspecting via Web Platform Administration GUI

Authorized administrators can inspect transport status at [`/admin/platform`](file:///c:/Users/armut/404/job%20card/frontend/src/app/admin/platform/page.tsx):

* **Deployment Mode Badge**: `LOCAL_ONLY` | `HYBRID_REMOTE` | `PRIVATE_DISTRIBUTED`
* **Transport Status**: `CONNECTED` (Green) | `STANDBY` (Slate) | `DISABLED`
* **Virtual Mesh IP**: e.g. `100.64.12.34` or `None (LAN Direct)`

### 6.2 Inspecting via the `ops` CLI

Run over local or SSH terminal:

```bash
ops network
```

Output includes:

```text
======================================================================
  DWRMS NETWORK TOPOLOGY & TRANSPORT CONNECTIVITY
======================================================================

  Secure Remote Transport Layer (Optional / Provider-Agnostic)
  +--------------------------+-------------------------------------------------------------+
  | Transport Property       | Runtime State                                               |
  +--------------------------+-------------------------------------------------------------+
  | Deployment Mode          | HYBRID_REMOTE                                               |
  | Remote Transport Status  | CONNECTED                                                   |
  | Configured Provider      | TAILSCALE                                                   |
  | Active Interface         | tailscale0                                                  |
  | Virtual Mesh IP          | 100.64.12.34                                                |
  | Security Model           | Transport Layer Only (JWT + RBAC + Approvals Enforced)      |
  +--------------------------+-------------------------------------------------------------+
```
