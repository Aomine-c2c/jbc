#!/usr/bin/env bash
# ==============================================================================
# BIKITA MINERALS DWRMS — SERVER ADMINISTRATOR SSH ONBOARDING & SETUP
# Version: 2.5 (SSH Server Administration and Operations)
# Target OS: Ubuntu Server 22.04 LTS / 24.04 LTS
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}====================================================================${NC}"
echo -e "${BLUE}   BIKITA MINERALS DWRMS — SSH SERVER ADMINISTRATOR SETUP (V2.5)   ${NC}"
echo -e "${BLUE}====================================================================${NC}"

# Check for root privileges
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}[ERROR] This setup script must be run as root or with sudo.${NC}"
   exit 1
fi

ADMIN_USER="${1:-administrator}"
INSTALL_DIR="/opt/dwrms"

echo -e "\n${YELLOW}==> [1/5] Configuring system user and administrative groups...${NC}"
# Create dwrms-admins group if not present
if ! getent group dwrms-admins >/dev/null; then
    groupadd dwrms-admins
    echo -e "${GREEN}[OK] Created system group 'dwrms-admins'${NC}"
fi

# Create or update administrator user
if ! id -u "$ADMIN_USER" >/dev/null 2>&1; then
    useradd -m -s /bin/bash -g dwrms-admins -G sudo,docker "$ADMIN_USER"
    echo -e "${GREEN}[OK] Created administrative user '$ADMIN_USER'${NC}"
else
    usermod -aG sudo,docker,dwrms-admins "$ADMIN_USER"
    echo -e "${GREEN}[OK] User '$ADMIN_USER' already exists. Added to sudo, docker, dwrms-admins.${NC}"
fi

echo -e "\n${YELLOW}==> [2/5] Configuring SSH directory and authorized keys for '$ADMIN_USER'...${NC}"
USER_SSH_DIR="/home/$ADMIN_USER/.ssh"
mkdir -p "$USER_SSH_DIR"
chmod 700 "$USER_SSH_DIR"
touch "$USER_SSH_DIR/authorized_keys"
chmod 600 "$USER_SSH_DIR/authorized_keys"
chown -R "$ADMIN_USER:dwrms-admins" "$USER_SSH_DIR"

echo -e "${CYAN}[INFO] Please paste the public key (Ed25519) into:${NC}"
echo -e "       $USER_SSH_DIR/authorized_keys"

echo -e "\n${YELLOW}==> [3/5] Installing OpenSSH hardening configuration...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSH_SRC_CONF="$SCRIPT_DIR/../ssh/sshd_config.d/dwrms-security.conf"

if [[ -f "$SSH_SRC_CONF" ]]; then
    mkdir -p /etc/ssh/sshd_config.d
    cp "$SSH_SRC_CONF" /etc/ssh/sshd_config.d/dwrms-security.conf
    chmod 644 /etc/ssh/sshd_config.d/dwrms-security.conf
    
    # Test sshd syntax before reloading
    if sshd -t; then
        systemctl reload ssh || systemctl reload sshd || true
        echo -e "${GREEN}[OK] OpenSSH configuration applied and reloaded.${NC}"
    else
        echo -e "${RED}[WARNING] sshd syntax test failed. Reverting drop-in config to prevent lockout.${NC}"
        rm -f /etc/ssh/sshd_config.d/dwrms-security.conf
    fi
fi

echo -e "\n${YELLOW}==> [4/5] Installing global 'ops' CLI launcher across all shell sessions...${NC}"
cat << 'EOF' > /usr/local/bin/ops
#!/usr/bin/env bash
# ==============================================================================
# Bikita Minerals DWRMS — Authoritative Platform Administration Global Wrapper
# ==============================================================================
set -e

INSTALL_DIR="/opt/dwrms"
BACKEND_DIR="$INSTALL_DIR/backend"

# Detect active virtual environment
if [[ -f "$BACKEND_DIR/.venv/bin/python3" ]]; then
    PYTHON_EXEC="$BACKEND_DIR/.venv/bin/python3"
elif [[ -f "$INSTALL_DIR/.venv/bin/python3" ]]; then
    PYTHON_EXEC="$INSTALL_DIR/.venv/bin/python3"
elif command -v python3 &>/dev/null; then
    PYTHON_EXEC="$(command -v python3)"
else
    echo "[ERROR] Python 3 runtime not found for 'ops' execution." >&2
    exit 1
fi

export PYTHONPATH="$BACKEND_DIR:${PYTHONPATH:-}"
export DWRMS_INSTALL_DIR="$INSTALL_DIR"

exec "$PYTHON_EXEC" "$INSTALL_DIR/ops" "$@"
EOF

chmod 755 /usr/local/bin/ops
echo -e "${GREEN}[OK] Global /usr/local/bin/ops command installed.${NC}"

echo -e "\n${YELLOW}==> [5/5] Installing interactive SSH login banner & shell profile...${NC}"
cat << 'EOF' > /etc/profile.d/dwrms_ops.sh
# Bikita Minerals DWRMS Server Administration Environment
if [ -n "$PS1" ]; then
    echo -e "\033[0;34m====================================================================\033[0m"
    echo -e "\033[1;33m  Bikita Minerals DWRMS — Authoritative Ubuntu Server Node\033[0m"
    echo -e "\033[0;36m  Server Administration & Maintenance Environment (V2.5)\033[0m"
    echo -e "\033[0;34m====================================================================\033[0m"
    echo -e "  Authoritative Commands:"
    echo -e "    \033[1;32mops status\033[0m        - Platform status & subsystem matrix"
    echo -e "    \033[1;32mops health\033[0m        - Live health & database ping probe"
    echo -e "    \033[1;32mops logs\033[0m          - View real-time service logs (-s app -n 50)"
    echo -e "    \033[1;32mops backup create\033[0m - Initiate instant database snapshot"
    echo -e "    \033[1;32mops diagnostics\033[0m   - Inspect CPU, memory, disk & pool stats"
    echo -e "    \033[1;32mops update\033[0m        - Platform versioning & migration verification"
    echo -e "\033[0;34m====================================================================\033[0m"
fi
EOF

chmod 644 /etc/profile.d/dwrms_ops.sh
echo -e "${GREEN}[OK] Interactive login banner configured in /etc/profile.d/dwrms_ops.sh${NC}"

echo -e "\n${GREEN}====================================================================${NC}"
echo -e "${GREEN}   SSH SERVER ADMINISTRATOR SETUP COMPLETE!                        ${NC}"
echo -e "${GREEN}====================================================================${NC}"
echo -e "Connect from your workstation using:"
echo -e "   ${CYAN}ssh -i ~/.ssh/id_ed25519 ${ADMIN_USER}@<server-ip-or-domain>${NC}\n"
