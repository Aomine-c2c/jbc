import os
import socket
from typing import Dict, Any, Optional
from datetime import datetime, timezone

try:
    import psutil
except ImportError:
    psutil = None

from app.core.config import settings
from app.core.logging_config import logger


class RemoteConnectivityManager:
    """
    Provider-agnostic Remote Connectivity & Transport Layer Manager.
    
    Treats remote networks (Tailscale, WireGuard, Cloudflare Tunnel, custom VPN)
    strictly as a transport layer.
    
    Security Invariant:
    Remote transport never bypasses or replaces Application Authentication (JWT),
    RBAC capabilities, Object-level authorization, or Workflow Approval thresholds.
    """

    KNOWN_REMOTE_INTERFACES = ["tailscale0", "wg0", "wg1", "tun0", "tun1", "utun0", "utun1", "utun2", "cloudflare"]

    def __init__(self):
        self._provider = settings.REMOTE_NETWORK_PROVIDER.lower()
        self._mode = settings.DEPLOYMENT_MODE.upper()
        self._configured_interface = settings.REMOTE_NETWORK_INTERFACE

    def scan_network_interfaces(self) -> Dict[str, Any]:
        """Scans host network interfaces to detect active remote mesh/VPN adapters."""
        detected_interfaces = {}
        if psutil:
            try:
                for iface_name, addrs in psutil.net_if_addrs().items():
                    for addr in addrs:
                        if addr.family == socket.AF_INET:
                            detected_interfaces[iface_name] = {
                                "ip": addr.address,
                                "netmask": addr.netmask,
                                "is_remote_mesh": iface_name.lower() in self.KNOWN_REMOTE_INTERFACES or "tailscale" in iface_name.lower() or "wg" in iface_name.lower(),
                            }
            except Exception as e:
                logger.warning(f"Error scanning network interfaces: {e}")
        return detected_interfaces

    def get_remote_network_status(self) -> Dict[str, Any]:
        """
        Returns structured, sanitized remote connectivity telemetry for authorized administrators.
        Guarantees zero raw secret keys or tokens are ever exposed.
        """
        interfaces = self.scan_network_interfaces()
        
        # Check if configured remote interface or any mesh interface is active
        matched_iface = None
        virtual_ip = settings.REMOTE_NETWORK_IP

        for iface_name, info in interfaces.items():
            if iface_name == self._configured_interface or info.get("is_remote_mesh"):
                matched_iface = iface_name
                if not virtual_ip:
                    virtual_ip = info.get("ip")
                break

        is_detected = matched_iface is not None or (settings.REMOTE_NETWORK_IP is not None)
        is_enabled = settings.REMOTE_CONNECTIVITY_ENABLED or (self._mode != "LOCAL_ONLY")

        # Determine overall transport state
        if not is_enabled:
            status_label = "DISABLED"
        elif is_detected:
            status_label = "CONNECTED"
        else:
            status_label = "STANDBY"

        return {
            "deployment_mode": self._mode,
            "enabled": is_enabled,
            "provider": self._provider if self._provider != "none" else ("tailscale" if is_detected else "none"),
            "status": status_label,
            "interface_name": matched_iface or self._configured_interface,
            "detected_on_host": is_detected,
            "virtual_ip": virtual_ip,
            "hostname": settings.REMOTE_NETWORK_HOSTNAME or getattr(settings, "SERVER_NAME", "masvingo-srv-01"),
            "security_model": {
                "layer_type": "Transport Layer Only",
                "application_auth": "JWT Enforced",
                "rbac": "Capabilities Enforced",
                "object_level_auth": "AuthzGuard Enforced",
                "approvals": "HOD Thresholds Enforced",
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Global singleton instance
remote_connectivity_manager = RemoteConnectivityManager()
