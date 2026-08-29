import socket
import urllib.request
import click
from urllib.parse import urlparse

from app.cli.utils import (
    print_header,
    print_table,
    print_success,
    print_warning,
    print_error,
)
from app.core.config import settings
from app.core.remote_connectivity import remote_connectivity_manager

try:
    import psutil
except ImportError:
    psutil = None


@click.command("network")
def network_command():
    """Display application network configuration, remote transport layer, and connectivity."""
    print_header("DWRMS NETWORK TOPOLOGY & TRANSPORT CONNECTIVITY")

    # 1. Authoritative URLs & CORS Policy
    print_table(
        ["Configuration Property", "Configured Value"],
        [
            ["Authoritative Portal URL", settings.FRONTEND_URL],
            ["Backend API Gateway URL", f"{settings.FRONTEND_URL.rstrip('/')}/api/v1"],
            ["Allowed CORS Origins", settings.CORS_ORIGINS],
        ],
        title="Web & API Endpoints",
    )

    # 2. Remote Connectivity & Transport Layer
    remote_status = remote_connectivity_manager.get_remote_network_status()
    print_table(
        ["Transport Property", "Runtime State"],
        [
            ["Deployment Mode", remote_status["deployment_mode"]],
            ["Remote Transport Status", remote_status["status"]],
            ["Configured Provider", remote_status["provider"].upper()],
            ["Active Interface", remote_status["interface_name"] or "None"],
            ["Virtual Mesh IP", remote_status["virtual_ip"] or "None (LAN/Domain Direct)"],
            ["Security Model", "Transport Layer Only (JWT + RBAC + Approvals Enforced)"],
        ],
        title="Secure Remote Transport Layer (Optional / Provider-Agnostic)",
    )

    # 3. Host Network Interfaces & IP Addresses
    if psutil:
        if_rows = []
        for iface_name, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    if_rows.append([iface_name, "IPv4", addr.address, addr.netmask or "-"])
        print_table(["Interface", "Family", "IP Address", "Subnet Mask"], if_rows, title="Host Network Interfaces")
    else:
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            print_table(["Host Property", "Value"], [["Hostname", hostname], ["Primary IP", local_ip]], title="Host IP")
        except Exception:
            pass

    # 4. Port Listening & Connectivity Checks
    click.secho("\nPort & Service Reachability", fg="cyan", bold=True)
    parsed = urlparse(settings.FRONTEND_URL)
    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    # Test DNS resolution
    try:
        ip = socket.gethostbyname(host)
        print_success(f"DNS Resolution: '{host}' resolves to {ip}")
    except socket.gaierror as e:
        print_warning(f"DNS Resolution: Failed to resolve '{host}': {e}")

    # Test TCP Port Connect
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        res = sock.connect_ex((host, port))
        sock.close()
        if res == 0:
            print_success(f"TCP Gateway: Successfully connected to {host}:{port}")
        else:
            print_warning(f"TCP Gateway: Port {port} on {host} did not respond (code {res}).")
    except Exception as e:
        print_warning(f"TCP Connection Test: {e}")

    click.echo("")
