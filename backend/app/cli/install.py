import os
import sys
import shutil
import click
from pathlib import Path

from app.cli.utils import (
    print_header,
    print_success,
    print_error,
    print_warning,
    print_info,
    run_command_capture,
    ROOT_DIR,
)


@click.command("install")
@click.option("--skip-docker", is_flag=True, help="Skip Docker installation if already configured")
@click.option("--skip-firewall", is_flag=True, help="Skip UFW firewall rules configuration")
def install_command(skip_docker, skip_firewall):
    """Install system dependencies, directories, firewall, and systemd units."""
    print_header("DWRMS HOST PREREQUISITES INSTALLATION")

    if os.name != "posix":
        print_warning("Running on non-Linux OS. Host systemd and apt operations will be simulated.")

    # 1. Package Installation (Linux only)
    if os.name == "posix" and not skip_docker:
        if os.geteuid() != 0:
            print_error("Host installation requires root privileges. Please re-run with sudo.")
            sys.exit(1)

        print_info("Installing system packages via apt...")
        code, out, err = run_command_capture([
            "apt-get", "update", "-y"
        ])
        code, out, err = run_command_capture([
            "apt-get", "install", "-y",
            "ca-certificates", "curl", "gnupg", "lsb-release",
            "git", "ufw", "openssl", "jq", "cron", "logrotate", "tar"
        ])
        if code == 0:
            print_success("System packages installed.")
        else:
            print_error(f"Package installation error: {err}")

        # Check / Install Docker
        if not shutil.which("docker"):
            print_info("Installing Docker CE...")
            run_command_capture([
                "apt-get", "install", "-y", "docker-ce", "docker-ce-cli", "containerd.io", "docker-compose-plugin"
            ])
            run_command_capture(["systemctl", "enable", "--now", "docker"])
            print_success("Docker CE installed and started.")
        else:
            print_success("Docker CE already installed.")

    # 2. Directory Hierarchy
    print_info("Creating standard production directories...")
    directories = [
        "/opt/dwrms",
        "/var/dwrms/storage",
        "/var/dwrms/storage/job_cards",
        "/var/dwrms/storage/reports",
        "/var/dwrms/storage/fleet",
        "/var/dwrms/storage/signatures",
        "/var/dwrms/storage/temp",
        "/var/dwrms/backups",
        "/var/dwrms/logs",
    ] if os.name == "posix" else [
        str(ROOT_DIR / "storage"),
        str(ROOT_DIR / "backups"),
        str(ROOT_DIR / "logs"),
    ]

    for d in directories:
        Path(d).mkdir(parents=True, exist_ok=True)
    print_success("System directories created.")

    # 3. UFW Firewall Configuration
    if os.name == "posix" and not skip_firewall and shutil.which("ufw"):
        print_info("Configuring UFW firewall rules...")
        run_command_capture(["ufw", "default", "deny", "incoming"])
        run_command_capture(["ufw", "default", "allow", "outgoing"])
        run_command_capture(["ufw", "allow", "22/tcp"])
        run_command_capture(["ufw", "allow", "80/tcp"])
        run_command_capture(["ufw", "allow", "443/tcp"])
        run_command_capture(["ufw", "deny", "3306/tcp"])
        run_command_capture(["ufw", "deny", "5432/tcp"])
        run_command_capture(["ufw", "deny", "6379/tcp"])
        run_command_capture(["ufw", "deny", "8000/tcp"])
        run_command_capture(["ufw", "--force", "enable"])
        print_success("UFW Firewall configured: Public access restricted to 80, 443, 22.")

    # 4. Systemd Units Installation
    if os.name == "posix" and Path("/etc/systemd/system").exists():
        print_info("Installing Systemd unit files...")
        systemd_src = ROOT_DIR / "infrastructure" / "systemd"
        if systemd_src.exists():
            for unit_file in systemd_src.glob("dwrms*"):
                shutil.copy(unit_file, Path("/etc/systemd/system") / unit_file.name)
            run_command_capture(["systemctl", "daemon-reload"])
            run_command_capture(["systemctl", "enable", "dwrms.service"])
            run_command_capture(["systemctl", "enable", "--now", "dwrms-backup.timer"])
            run_command_capture(["systemctl", "enable", "--now", "dwrms-healthcheck.timer"])
            print_success("Systemd services & automated timers registered.")

    # 5. Create /usr/local/bin/ops Global Symlink
    if os.name == "posix":
        ops_src = ROOT_DIR / "ops"
        ops_link = Path("/usr/local/bin/ops")
        try:
            if ops_link.exists() or ops_link.is_symlink():
                ops_link.unlink()
            ops_link.symlink_to(ops_src)
            ops_src.chmod(0o755)
            print_success("Global CLI symlink created at: /usr/local/bin/ops")
        except Exception as e:
            print_warning(f"Could not link /usr/local/bin/ops: {e}")

    print_header("INSTALLATION COMPLETED")
    click.secho("Host system is provisioned. Run 'ops setup' to configure the platform.", fg="green", bold=True)
