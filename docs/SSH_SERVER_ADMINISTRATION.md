# SSH Server Administration and Operations Guide

> **Bikita Minerals Industrial Operations and Work Management Platform (DWRMS)**  
> **Version 2.5 — Server-First Platform Operations**  
> **Authoritative Node**: Ubuntu Server 22.04 LTS / 24.04 LTS (`masvingo-srv-01`)

---

## 1. Architectural Separation: The Three Administrative Layers

To guarantee platform security, organizational integrity, and clear operational boundaries, the Bikita Minerals DWRMS platform enforces **three strictly isolated administrative tiers**.

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              ADMINISTRATIVE ACCESS TIERS                               │
└────────────────────────────────────────────────────────────────────────────────────────┘

  TIER 1: APPLICATION USER (Mining Technicians, Supervisors, HODs, Requesters)
  ├── Interface     : Tauri Desktop Client / Web Browser / Mobile PWA
  ├── Authentication: Application JWT / User Credentials
  ├── Scope         : Work orders, job cards, breakdowns, fleet requisitions, approvals
  └── Access Policy : 🚫 NO SSH ACCESS. Application authentication only.

  TIER 2: PLATFORM ADMINISTRATOR (Operations Managers, IAM Administrators)
  ├── Interface     : Platform Web & Desktop GUI (/admin/users, /admin/platform, /admin/audit)
  ├── Authentication: Application Admin JWT with RBAC capabilities ('settings:manage', 'users:manage')
  ├── Scope         : User directory, roles & permissions, approval thresholds, fleet assets
  └── Access Policy : 🚫 NO SSH ACCESS REQUIRED. Manages operations via application UI.

  TIER 3: SERVER ADMINISTRATOR (DevOps, Infrastructure Engineers, Systems Administrators)
  ├── Interface     : Secure Shell (SSH) → Ubuntu Server Host
  ├── Authentication: Cryptographic Public Key Authentication (Ed25519) + Sudo Group
  ├── Scope         : Host operating system, Docker containers, systemd services, UFW firewall,
  │                   the authoritative 'ops' CLI, persistent storage volumes, log rotation,
  │                   disaster recovery archives, OS kernel patches, and TLS certificates
  └── Access Policy : ✅ Dedicated 'administrator' system account with restricted SSH ingress.
```

> [!IMPORTANT]
> **Core Security Invariant**: SSH is reserved strictly for operating system and infrastructure management. Normal application users and platform managers do not require SSH access. The web application does **not** expose unrestricted OS terminal or shell execution through the browser.

---

## 2. Server Infrastructure & SSH Hardening

### 2.1 SSH Key Generation

Server administrators must authenticate using **Ed25519 elliptic-curve public keys**. Password authentication over SSH is disabled.

Generate an administrative keypair on your local administrative workstation:

```bash
# Generate high-security Ed25519 keypair
ssh-keygen -t ed25519 -C "admin@bikita.local" -f ~/.ssh/id_ed25519_dwrms
```

### 2.2 OpenSSH Daemon Configuration (`/etc/ssh/sshd_config.d/dwrms-security.conf`)

The authoritative server deployment enforces hardened SSH policies via drop-in configuration:

```ini
# /etc/ssh/sshd_config.d/dwrms-security.conf

# 1. Disable root login over SSH
PermitRootLogin no

# 2. Enforce Public Key Authentication only
PubkeyAuthentication yes
PasswordAuthentication no
PermitEmptyPasswords no
AuthenticationMethods publickey

# 3. Connection Rate & Session Limits
MaxAuthTries 3
MaxSessions 5

# 4. Modern Cryptographic Primitives
HostKey /etc/ssh/ssh_host_ed25519_key
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group16-sha512
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com

# 5. Access Isolation & Inactivity Timeouts
AllowGroups sudo dwrms-admins
ClientAliveInterval 300
ClientAliveCountMax 2
X11Forwarding no
```

### 2.3 Network Firewall (UFW) Configuration

Port `22` (SSH) is restricted to the administrative management network or secure VPN:

```bash
# Allow administrative SSH from trusted subnet only
sudo ufw allow proto tcp from 192.168.10.0/24 to any port 22 comment 'Administrative SSH Subnet'

# Allow HTTP and HTTPS for client applications
sudo ufw allow 80/tcp comment 'HTTP Web & ACME'
sudo ufw allow 443/tcp comment 'HTTPS Reverse Proxy'

# Enable UFW
sudo ufw enable
```

### 2.4 Fail2ban Intrusion Prevention (`/etc/fail2ban/jail.d/dwrms-sshd.local`)

Automated rate-limiting and IP banning upon repeated failed SSH authentication attempts:

```ini
[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 4
findtime = 600
bantime = 3600
```

---

## 3. Server Administrator Onboarding Workflow

To provision a new server administrator and set up the interactive environment, run the automated provisioning script as root on the server:

```bash
# Run the automated SSH admin setup utility
sudo /opt/dwrms/infrastructure/scripts/setup-ssh-admin.sh administrator
```

The script performs:

1. Creates the `dwrms-admins` system group.
2. Provisions the `administrator` user with membership in `sudo`, `docker`, and `dwrms-admins`.
3. Creates `~/.ssh/authorized_keys` with `700`/`600` permissions.
4. Applies OpenSSH drop-in hardening rules and verifies syntax before reloading `sshd`.
5. Installs the global `/usr/local/bin/ops` executable wrapper.
6. Configures `/etc/profile.d/dwrms_ops.sh` to present an interactive server status banner upon login.

---

## 4. SSH-Based Operations Workflows

### 4.1 Workstation SSH Client Configuration (`~/.ssh/config`)

For seamless connectivity, add the server configuration to your workstation's `~/.ssh/config`:

```ini
Host bikita-server
    HostName masvingo-srv-01.bikita.local
    User administrator
    IdentityFile ~/.ssh/id_ed25519_dwrms
    Port 22
    ServerAliveInterval 60
```

### 4.2 Interactive SSH Session

Connect to the server:

```bash
ssh bikita-server
```

Upon logging in, the interactive MOTD banner displays available authoritative commands.

#### Example Interactive Command Sequence

```bash
# 1. Check overall platform status and 7-subsystem matrix
ops status

# 2. Execute a live end-to-end health and latency probe
ops health

# 3. Stream recent application logs with real-time level filtering
ops logs -s app -n 50

# 4. View hardware and process resource diagnostics
ops diagnostics

# 5. Initiate an immediate disaster recovery snapshot
ops backup create --note "Pre-maintenance snapshot"

# 6. Verify backup history and cryptographic checksums
ops backup list

# 7. Check platform updates and migration state
ops update
```

### 4.3 Non-Interactive Remote Automation

Server administrators can execute remote commands over SSH without opening an interactive shell (e.g. from CI/CD pipelines, remote cron jobs, or monitoring systems):

```bash
# Remote health check
ssh administrator@masvingo-srv-01.bikita.local "ops health"

# Remote automated snapshot creation with JSON output
ssh administrator@masvingo-srv-01.bikita.local "ops backup create --note 'Automated Nightly Snapshot' --json"

# Remote log inspection
ssh administrator@masvingo-srv-01.bikita.local "ops logs -s app -n 100"
```

---

## 5. Summary of Administrative Commands

| Command | Purpose | Access Tier |
| :--- | :--- | :--- |
| `ops status` | Displays aggregate status across Application, Database, Storage, Worker, Backups, Network | Server Admin (SSH) |
| `ops health` | Probes live DB ping, API latency, and filesystem write access | Server Admin (SSH) |
| `ops logs` | Streams sanitized application logs with level filtering and secret masking | Server Admin (SSH) |
| `ops diagnostics` | Displays CPU, RAM, disk breakdown, and DB connection pool statistics | Server Admin (SSH) |
| `ops backup create` | Generates a compressed tar.gz disaster recovery archive with SHA-256 hash | Server Admin (SSH) |
| `ops backup list` | Lists all historical backup archives with timestamps and integrity hashes | Server Admin (SSH) |
| `ops restore` | Restores database tables and storage volumes from a verified archive | Server Admin (SSH) |
| `ops server restart` | Restarts systemd units or Docker Compose services | Server Admin (SSH) |
| `ops update` | Inspects schema versions, applied migrations, and release channel | Server Admin (SSH) |
| `/admin/platform` | Web GUI for viewing telemetry, triggering health checks, and creating backups | Platform Admin (Web/Tauri) |
| `/admin/users` | Web GUI for user accounts, password resets, and role assignments | Platform Admin (Web/Tauri) |

---

## 6. Security Audit & Incident Response

1. **Review SSH Access Logs**:

   ```bash
   # Inspect authenticated SSH sessions
   sudo grep 'Accepted publickey' /var/log/auth.log
   
   # Inspect failed connection attempts
   sudo grep 'Failed publickey' /var/log/auth.log
   ```

2. **Inspect Fail2ban Ban Status**:

   ```bash
   sudo fail2ban-client status sshd
   ```

3. **Verify OpenSSH Daemon Status**:

   ```bash
   sudo systemctl status ssh
   ```
