#!/usr/bin/env bash
# ==============================================================================
# BIKITA MINERALS DWRMS — OPTIONAL SECURE REMOTE MESH PROVISIONING HELPER
# Version: 2.6 (Optional Secure Remote Connectivity)
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
echo -e "${BLUE}   BIKITA MINERALS DWRMS — OPTIONAL REMOTE CONNECTIVITY SETUP     ${NC}"
echo -e "${BLUE}   Provider-Agnostic Transport Layer Provisioner (V2.6)             ${NC}"
echo -e "${BLUE}====================================================================${NC}"

# Check for root / sudo permissions
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}[ERROR] This script must be run as root or with sudo privileges.${NC}"
   exit 1
fi

PROVIDER="${1:-tailscale}"

case "$PROVIDER" in
    tailscale)
        echo -e "\n${YELLOW}==> [1/2] Installing Tailscale package on Ubuntu Server...${NC}"
        if ! command -v tailscale &>/dev/null; then
            curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/jammy.noarmor.gpg | tee /usr/share/keyrings/tailscale-archive-keyring.gpg >/dev/null
            curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/jammy.tailscale-keyring.list | tee /etc/apt/sources.list.d/tailscale.list >/dev/null
            apt-get update -y
            apt-get install -y tailscale
            systemctl enable --now tailscaled
            echo -e "${GREEN}[OK] Tailscale daemon installed and active.${NC}"
        else
            echo -e "${GREEN}[OK] Tailscale is already installed.${NC}"
        fi

        echo -e "\n${YELLOW}==> [2/2] Updating DWRMS environment configuration...${NC}"
        ENV_FILE="/opt/dwrms/.env"
        if [[ -f "$ENV_FILE" ]]; then
            sed -i 's/^DEPLOYMENT_MODE=.*/DEPLOYMENT_MODE=HYBRID_REMOTE/' "$ENV_FILE" || true
            sed -i 's/^REMOTE_CONNECTIVITY_ENABLED=.*/REMOTE_CONNECTIVITY_ENABLED=true/' "$ENV_FILE" || true
            sed -i 's/^REMOTE_NETWORK_PROVIDER=.*/REMOTE_NETWORK_PROVIDER=tailscale/' "$ENV_FILE" || true
        fi

        echo -e "\n${GREEN}[SUCCESS] Tailscale transport installed.${NC}"
        echo -e "To authenticate node, execute:"
        echo -e "   ${CYAN}sudo tailscale up --hostname=dwrms-server-masvingo --ssh${NC}\n"
        ;;

    wireguard)
        echo -e "\n${YELLOW}==> [1/2] Installing WireGuard on Ubuntu Server...${NC}"
        apt-get update -y
        apt-get install -y wireguard wireguard-tools
        echo -e "${GREEN}[OK] WireGuard installed.${NC}"

        echo -e "\n${YELLOW}==> [2/2] Updating DWRMS environment configuration...${NC}"
        ENV_FILE="/opt/dwrms/.env"
        if [[ -f "$ENV_FILE" ]]; then
            sed -i 's/^DEPLOYMENT_MODE=.*/DEPLOYMENT_MODE=HYBRID_REMOTE/' "$ENV_FILE" || true
            sed -i 's/^REMOTE_CONNECTIVITY_ENABLED=.*/REMOTE_CONNECTIVITY_ENABLED=true/' "$ENV_FILE" || true
            sed -i 's/^REMOTE_NETWORK_PROVIDER=.*/REMOTE_NETWORK_PROVIDER=wireguard/' "$ENV_FILE" || true
            sed -i 's/^REMOTE_NETWORK_INTERFACE=.*/REMOTE_NETWORK_INTERFACE=wg0/' "$ENV_FILE" || true
        fi

        echo -e "\n${GREEN}[SUCCESS] WireGuard transport installed.${NC}"
        echo -e "Place your config at ${CYAN}/etc/wireguard/wg0.conf${NC} and run:"
        echo -e "   ${CYAN}sudo systemctl enable --now wg-quick@wg0${NC}\n"
        ;;

    *)
        echo -e "${RED}[ERROR] Unsupported provider '$PROVIDER'. Supported: 'tailscale', 'wireguard'${NC}"
        exit 1
        ;;
esac
