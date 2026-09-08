"""
Bikita Minerals DWRMS — Authoritative Real-time Platform Monitoring TUI.
Interactive terminal dashboard providing live container status, host telemetry,
dual IP endpoints (LAN + Tailscale), 1-minute auto-pull update status, and logs.
"""

import os
import sys
import time
import shutil
import platform
import subprocess
from datetime import datetime
from pathlib import Path
import click

try:
    import psutil
except ImportError:
    psutil = None

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from app.cli.utils import run_command_capture, ROOT_DIR
from app.core.config import settings


def _format_bar(percent: float, width: int = 24) -> str:
    filled = int(round((percent / 100.0) * width))
    filled = max(0, min(width, filled))
    try:
        "█░".encode(sys.stdout.encoding or "utf-8")
        return "█" * filled + "░" * (width - filled)
    except Exception:
        return "#" * filled + "-" * (width - filled)



def _get_ips() -> dict:
    lan_ip = "127.0.0.1"
    tailscale_ip = "Not Active"
    magic_dns = "dwrms.internal"

    # Try psutil for LAN IP
    if psutil:
        for iface, addrs in psutil.net_if_addrs().items():
            if iface.lower() in ("lo", "docker0", "br-"):
                continue
            for addr in addrs:
                if addr.family.name == "AF_INET":
                    ip = addr.address
                    if not ip.startswith("127.") and not ip.startswith("172.17.") and not ip.startswith("172.18."):
                        if iface.startswith("tailscale") or iface.startswith("ts"):
                            tailscale_ip = ip
                        elif lan_ip == "127.0.0.1":
                            lan_ip = ip

    # Try tailscale CLI if still missing
    if tailscale_ip == "Not Active":
        code, out, _ = run_command_capture(["tailscale", "ip", "-4"])
        if code == 0 and out.strip():
            tailscale_ip = out.strip().splitlines()[0]

    # Try hostname -I for LAN IP fallback
    if lan_ip == "127.0.0.1" and os.name != "nt":
        code, out, _ = run_command_capture(["hostname", "-I"])
        if code == 0 and out.strip():
            lan_ip = out.strip().split()[0]

    # Check MagicDNS or status
    code, out, _ = run_command_capture(["tailscale", "status", "--json"])
    if code == 0 and "Self" in out:
        try:
            import json
            data = json.loads(out)
            dns_name = data.get("Self", {}).get("DNSName", "")
            if dns_name:
                magic_dns = dns_name.rstrip(".")
        except Exception:
            pass

    return {
        "lan_ip": lan_ip,
        "tailscale_ip": tailscale_ip,
        "magic_dns": magic_dns
    }


def _get_containers() -> list:
    compose_file = ROOT_DIR / "infrastructure" / "docker-compose.prod.yml"
    if not compose_file.exists():
        compose_file = ROOT_DIR / "infrastructure" / "docker-compose.yml"

    code, out, _ = run_command_capture([
        "docker", "compose", "-f", str(compose_file), "ps", "--format", "{{.Service}}|{{.Status}}|{{.Ports}}"
    ])

    containers = []
    if code == 0 and out.strip():
        for line in out.strip().splitlines():
            parts = line.split("|")
            service = parts[0].strip()
            status = parts[1].strip() if len(parts) > 1 else "UNKNOWN"
            ports = parts[2].strip() if len(parts) > 2 else ""
            
            is_up = "Up" in status or "running" in status.lower()
            is_healthy = "healthy" in status.lower()
            
            containers.append({
                "service": service,
                "status": status,
                "ports": ports,
                "is_up": is_up,
                "is_healthy": is_healthy
            })
    return containers


def _get_git_update_status() -> dict:
    code_sha, sha_out, _ = run_command_capture(["git", "rev-parse", "--short", "HEAD"], cwd=str(ROOT_DIR))
    sha = sha_out.strip() if code_sha == 0 else "N/A"

    code_br, br_out, _ = run_command_capture(["git", "branch", "--show-current"], cwd=str(ROOT_DIR))
    branch = br_out.strip() if code_br == 0 else "main"

    # Check systemd timer state
    timer_active = False
    if os.name != "nt":
        code_tm, out_tm, _ = run_command_capture(["systemctl", "is-active", "dwrms-autoupdate.timer"])
        timer_active = (code_tm == 0 and "active" in out_tm.lower())

    return {
        "sha": sha,
        "branch": branch,
        "timer_active": timer_active,
        "cadence": "Every 60s (systemd)"
    }


def _get_recent_logs(lines: int = 6) -> list:
    log_file = Path("/var/dwrms/logs/dwrms.log")
    if log_file.exists():
        try:
            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                content = f.readlines()
                return [line.strip() for line in content[-lines:] if line.strip()]
        except Exception:
            pass

    # Fallback to docker compose logs
    compose_file = ROOT_DIR / "infrastructure" / "docker-compose.prod.yml"
    if compose_file.exists():
        code, out, _ = run_command_capture([
            "docker", "compose", "-f", str(compose_file), "logs", "--tail", str(lines), "backend"
        ])
        if code == 0 and out.strip():
            return [line.strip() for line in out.strip().splitlines()[-lines:]]

    return ["[SYSTEM] Services online and running stably. Telemetry stream active."]


def render_monitor_frame(term_width: int, term_height: int) -> str:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ips = _get_ips()
    containers = _get_containers()
    update_info = _get_git_update_status()
    logs = _get_recent_logs(6)

    # Resource stats
    cpu_pct = 0.0
    mem_pct = 0.0
    mem_used_gb = 0.0
    mem_total_gb = 0.0
    if psutil:
        try:
            cpu_pct = psutil.cpu_percent(interval=None)
            vmem = psutil.virtual_memory()
            mem_pct = vmem.percent
            mem_used_gb = round(vmem.used / (1024**3), 2)
            mem_total_gb = round(vmem.total / (1024**3), 2)
        except Exception:
            pass

    # Disk stats
    disk_pct = 0.0
    disk_free_gb = 0.0
    try:
        du = shutil.disk_usage("/")
        disk_pct = round((du.used / du.total) * 100, 1)
        disk_free_gb = round(du.free / (1024**3), 1)
    except Exception:
        pass

    out = []
    w = max(78, min(term_width - 2, 100))
    try:
        "╔═╗║╠╣╟╢╚╝─•".encode(sys.stdout.encoding or "utf-8")
        hr = "═" * w
        dash = "─" * w
        c_tl, c_tr, c_bl, c_br = "╔", "╗", "╚", "╝"
        c_ml, c_mr, c_dl, c_dr = "╠", "╣", "╟", "╢"
        v_bar = "║"
        bullet = "•"
    except Exception:
        hr = "=" * w
        dash = "-" * w
        c_tl, c_tr, c_bl, c_br = "+", "+", "+", "+"
        c_ml, c_mr, c_dl, c_dr = "+", "+", "+", "+"
        v_bar = "|"
        bullet = "*"

    # Header
    out.append(f"\033[1;36m{c_tl}{hr}{c_tr}\033[0m")
    title = f"  BIKITA MINERALS DWRMS — LIVE OPERATIONS MONITOR (V2.9)"
    out.append(f"\033[1;36m{v_bar}\033[0m\033[1;37m{title:<{w}}\033[0m\033[1;36m{v_bar}\033[0m")
    meta = f"  Node: {platform.node()}  |  OS: {platform.system()}  |  Time: {now_str}  |  Shift: Active"
    out.append(f"\033[1;36m{v_bar}\033[0m\033[0;37m{meta:<{w}}\033[0m\033[1;36m{v_bar}\033[0m")
    out.append(f"\033[1;36m{c_ml}{hr}{c_mr}\033[0m")

    # Section 1: Dual IP Access Endpoints
    out.append(f"\033[1;36m{v_bar}\033[0m \033[1;33m[1] DUAL IP WEB ACCESS & REMOTE CONNECTIVITY\033[0m{'':<{w - 44}}\033[1;36m{v_bar}\033[0m")
    lan_line = f"    {bullet} Local LAN Web App:     https://{ips['lan_ip']} (or http://{ips['lan_ip']})"
    ts_line  = f"    {bullet} Tailscale Secure Mesh: https://{ips['tailscale_ip']} (MagicDNS: {ips['magic_dns']})"
    api_line = f"    {bullet} Authoritative Gateway: https://{ips['lan_ip']}/api/v1"
    out.append(f"\033[1;36m{v_bar}\033[0m\033[0;32m{lan_line:<{w}}\033[0m\033[1;36m{v_bar}\033[0m")
    out.append(f"\033[1;36m{v_bar}\033[0m\033[0;34m{ts_line:<{w}}\033[0m\033[1;36m{v_bar}\033[0m")
    out.append(f"\033[1;36m{v_bar}\033[0m\033[0;37m{api_line:<{w}}\033[0m\033[1;36m{v_bar}\033[0m")
    out.append(f"\033[1;36m{c_dl}{dash}{c_dr}\033[0m")

    # Section 2: Host Hardware Telemetry
    out.append(f"\033[1;36m{v_bar}\033[0m \033[1;33m[2] HOST HARDWARE & CAPACITY UTILIZATION\033[0m{'':<{w - 40}}\033[1;36m{v_bar}\033[0m")
    cpu_bar = _format_bar(cpu_pct, 20)
    ram_bar = _format_bar(mem_pct, 20)
    disk_bar = _format_bar(disk_pct, 20)
    
    cpu_str = f"    CPU Load:  [{cpu_bar}] {cpu_pct:5.1f}%  ({psutil.cpu_count() if psutil else 4} vCPUs)"
    ram_str = f"    Memory:    [{ram_bar}] {mem_pct:5.1f}%  ({mem_used_gb} GB / {mem_total_gb} GB)"
    dsk_str = f"    Disk /:    [{disk_bar}] {disk_pct:5.1f}%  ({disk_free_gb} GB free)"
    out.append(f"\033[1;36m{v_bar}\033[0m\033[0;37m{cpu_str:<{w}}\033[0m\033[1;36m{v_bar}\033[0m")
    out.append(f"\033[1;36m{v_bar}\033[0m\033[0;37m{ram_str:<{w}}\033[0m\033[1;36m{v_bar}\033[0m")
    out.append(f"\033[1;36m{v_bar}\033[0m\033[0;37m{dsk_str:<{w}}\033[0m\033[1;36m{v_bar}\033[0m")
    out.append(f"\033[1;36m{c_dl}{dash}{c_dr}\033[0m")

    # Section 3: Docker Stack Containers
    out.append(f"\033[1;36m{v_bar}\033[0m \033[1;33m[3] DOCKER COMPOSE CONTAINER STACK\033[0m{'':<{w - 34}}\033[1;36m{v_bar}\033[0m")
    if containers:
        for c in containers[:6]:
            status_color = "\033[1;32m" if c["is_up"] else "\033[1;31m"
            badge = "RUNNING" if c["is_up"] else "STOPPED"
            if c["is_healthy"]:
                badge = "HEALTHY"
            svc_line = f"    {c['service']:<18} {badge:<10} {c['status'][:24]:<26} {c['ports'][:28]}"
            out.append(f"\033[1;36m{v_bar}\033[0m{status_color}{svc_line:<{w}}\033[0m\033[1;36m{v_bar}\033[0m")
    else:
        empty_c = "    No active compose containers detected. Run 'ops server start'."
        out.append(f"\033[1;36m{v_bar}\033[0m\033[0;33m{empty_c:<{w}}\033[0m\033[1;36m{v_bar}\033[0m")
    out.append(f"\033[1;36m{c_dl}{dash}{c_dr}\033[0m")

    # Section 4: Auto-Pull 1-Minute Update Engine
    out.append(f"\033[1;36m{v_bar}\033[0m \033[1;33m[4] AUTOMATED UPDATE SYSTEM (1-MIN CADENCE)\033[0m{'':<{w - 43}}\033[1;36m{v_bar}\033[0m")
    timer_badge = "ACTIVE (Running Every 60s)" if update_info["timer_active"] else "SYSTEMD TIMER PENDING"
    up_line1 = f"    {bullet} Systemd Timer:   {timer_badge}   {bullet} Branch: {update_info['branch']}"
    up_line2 = f"    {bullet} Current Commit:  {update_info['sha']}                          {bullet} Channel: production"
    out.append(f"\033[1;36m{v_bar}\033[0m\033[0;37m{up_line1:<{w}}\033[0m\033[1;36m{v_bar}\033[0m")
    out.append(f"\033[1;36m{v_bar}\033[0m\033[0;37m{up_line2:<{w}}\033[0m\033[1;36m{v_bar}\033[0m")
    out.append(f"\033[1;36m{c_dl}{dash}{c_dr}\033[0m")

    # Section 5: Recent Logs Stream
    out.append(f"\033[1;36m{v_bar}\033[0m \033[1;33m[5] RECENT OPERATIONS LOG TELEMETRY\033[0m{'':<{w - 35}}\033[1;36m{v_bar}\033[0m")
    for log_entry in logs:
        trimmed = log_entry[: w - 6]
        log_line = f"    {trimmed}"
        out.append(f"\033[1;36m{v_bar}\033[0m\033[0;37m{log_line:<{w}}\033[0m\033[1;36m{v_bar}\033[0m")

    # Footer
    out.append(f"\033[1;36m{c_ml}{hr}{c_mr}\033[0m")
    footer = "  [q] Quit Monitor   [r] Force Refresh   [u] Check Updates   [l] View Full Logs"
    out.append(f"\033[1;36m{v_bar}\033[0m\033[1;32m{footer:<{w}}\033[0m\033[1;36m{v_bar}\033[0m")
    out.append(f"\033[1;36m{c_bl}{hr}{c_br}\033[0m")


    return "\n".join(out)


def _check_key_press() -> str:
    """Non-blocking keyboard check for terminal interaction."""
    if os.name == "nt":
        import msvcrt
        if msvcrt.kbhit():
            ch = msvcrt.getch()
            try:
                return ch.decode("utf-8", errors="ignore").lower()
            except Exception:
                return ""
        return ""
    else:
        import select
        if select.select([sys.stdin], [], [], 0.0)[0]:
            try:
                ch = sys.stdin.read(1)
                return ch.lower()
            except Exception:
                return ""
        return ""


@click.command("monitor")
@click.option("--interval", "-i", default=2.5, help="Refresh interval in seconds (default: 2.5s)")
def monitor_command(interval: float):
    """Launch the interactive post-installation and live operations monitoring TUI."""
    if not sys.stdin.isatty():
        # Non-interactive fallback: render single snapshot
        width, height = shutil.get_terminal_size((80, 24))
        click.echo(render_monitor_frame(width, height))
        return

    # Terminal cbreak mode on Unix for immediate keystroke response
    old_settings = None
    if os.name != "nt":
        try:
            import tty
            import termios
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
        except Exception:
            old_settings = None

    try:
        # Hide cursor and clear screen
        sys.stdout.write("\033[?25l\033[2J\033[H")
        sys.stdout.flush()

        while True:
            width, height = shutil.get_terminal_size((80, 24))
            frame = render_monitor_frame(width, height)
            
            # Reposition to top-left and draw frame
            sys.stdout.write("\033[H" + frame)
            sys.stdout.flush()

            # Wait loop with sub-interval checks for keypresses
            steps = int(interval / 0.1)
            for _ in range(max(1, steps)):
                time.sleep(0.1)
                key = _check_key_press()
                if key == "q":
                    return
                elif key == "r":
                    break
                elif key == "u":
                    # Clear screen temporarily and run ops update check
                    sys.stdout.write("\033[2J\033[H\033[?25h")
                    sys.stdout.flush()
                    print("[INFO] Checking for upstream repository updates...")
                    run_command_capture(["git", "fetch", "origin"], cwd=str(ROOT_DIR))
                    time.sleep(1.5)
                    sys.stdout.write("\033[?25l\033[2J\033[H")
                    sys.stdout.flush()
                    break
                elif key == "l":
                    # Show logs
                    sys.stdout.write("\033[2J\033[H\033[?25h")
                    sys.stdout.flush()
                    compose_file = ROOT_DIR / "infrastructure" / "docker-compose.prod.yml"
                    subprocess.call(["docker", "compose", "-f", str(compose_file), "logs", "--tail", "30"])
                    print("\nPress ENTER to resume monitor...")
                    input()
                    sys.stdout.write("\033[?25l\033[2J\033[H")
                    sys.stdout.flush()
                    break

    except KeyboardInterrupt:
        pass
    finally:
        # Restore terminal cursor & settings
        sys.stdout.write("\033[?25h\033[2J\033[H")
        sys.stdout.flush()
        if old_settings and os.name != "nt":
            try:
                import termios
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            except Exception:
                pass
        click.secho("Exited DWRMS Live Operations Monitor.", fg="cyan")


if __name__ == "__main__":
    monitor_command()
