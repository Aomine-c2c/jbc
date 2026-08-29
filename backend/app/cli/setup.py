import os
import sys
import secrets
import asyncio
import click
from pathlib import Path

from app.cli.utils import (
    print_header,
    print_table,
    print_success,
    print_error,
    print_warning,
    print_info,
    load_env_dict,
    ROOT_DIR,
)
from app.core.setup_manager import SetupManager


@click.command("setup")
@click.option("--non-interactive", is_flag=True, help="Run non-interactively using existing .env or defaults")
@click.option("--force", is_flag=True, help="Force re-run setup even if already completed (CAUTION)")
def setup_command(non_interactive, force):
    """Launch the 8-stage first-time server setup process for DWRMS platform."""
    print_header("BIKITA MINERALS DWRMS -- FIRST-TIME SERVER SETUP WIZARD (V2.1)")

    if SetupManager.is_setup_completed() and not force:
        print_warning("Platform setup has already been completed and locked.")
        click.echo("Use 'ops configure list' to inspect settings or 'ops status' for health.\n")
        return

    saved_state = SetupManager.get_setup_state()
    current_env = load_env_dict()

    if non_interactive:
        print_info("Executing non-interactive setup with baseline configuration...")
        try:
            report = asyncio.run(SetupManager.finalize_setup())
            _display_completion_report(report)
        except Exception as e:
            print_error(f"Setup finalization error: {e}")
            sys.exit(1)
        return

    click.echo("This 8-stage wizard will configure and verify your authoritative server stack.\n")

    # ── STEP 1: PLATFORM CONFIGURATION ───────────────────────────
    click.secho("[STEP 1/8] Platform & Server Identity", fg="cyan", bold=True)
    step1_defaults = saved_state.get("step_1_platform", {})
    org_name = click.prompt("  Organization Name", default=step1_defaults.get("organization_name", "Bikita Minerals DWRMS"))
    inst_name = click.prompt("  Installation/Site Name", default=step1_defaults.get("installation_name", "Masvingo Lithium Operation"))
    server_name = click.prompt("  Server Node Identifier", default=step1_defaults.get("server_name", "bikita-srv-01"))
    env_type = click.prompt(
        "  Deployment Environment",
        type=click.Choice(["production", "staging", "development"], case_sensitive=False),
        default=step1_defaults.get("environment", "production"),
    )
    timezone = click.prompt("  Server Operational Timezone", default=step1_defaults.get("timezone", "Africa/Harare"))

    step1_data = {
        "organization_name": org_name,
        "installation_name": inst_name,
        "server_name": server_name,
        "environment": env_type,
        "timezone": timezone,
    }
    SetupManager.save_step(1, step1_data)
    print_success("Platform identity saved.")

    # ── STEP 2: NETWORK CONFIGURATION ────────────────────────────
    click.secho("\n[STEP 2/8] Network & Client Endpoint Configuration", fg="cyan", bold=True)
    click.echo("  (Note: Fixed public IP is NOT required. Dynamic or internal LAN addresses are supported.)")
    step2_defaults = saved_state.get("step_2_network", {})
    primary_url = click.prompt("  Primary Server URL", default=step2_defaults.get("primary_url", "https://dwrms.bikita.com"))
    domain_name = click.prompt("  Domain Name (where available)", default=step2_defaults.get("domain_name", "dwrms.bikita.com"))
    local_ip = click.prompt("  Local LAN IP / Binding Address", default=step2_defaults.get("local_ip", "192.168.1.100"))
    https_enabled = click.confirm("  Enable HTTPS / TLS Encryption?", default=step2_defaults.get("https_enabled", True))
    cors_origins = click.prompt(
        "  Trusted CORS Origins (comma-separated)",
        default=step2_defaults.get("cors_origins", f"{primary_url},tauri://localhost,http://tauri.localhost"),
    )

    step2_data = {
        "primary_url": primary_url,
        "domain_name": domain_name,
        "local_ip": local_ip,
        "https_enabled": https_enabled,
        "cors_origins": cors_origins,
    }
    SetupManager.save_step(2, step2_data)
    print_success("Network configuration saved.")

    # ── STEP 3: DATABASE CONFIGURATION & PRE-FLIGHT ──────────────
    click.secho("\n[STEP 3/8] Database Configuration & Connection Test", fg="cyan", bold=True)
    step3_defaults = saved_state.get("step_3_database", {})
    db_engine = click.prompt(
        "  Database Engine",
        type=click.Choice(["postgresql", "mysql", "sqlite"], case_sensitive=False),
        default=step3_defaults.get("engine", "postgresql"),
    )

    db_host = "localhost"
    db_port = 5432
    db_name = "dwrms"
    db_user = "postgres"
    db_pass = ""

    if db_engine != "sqlite":
        while True:
            db_host = click.prompt("  Database Host", default=step3_defaults.get("host", "db"))
            db_port = click.prompt("  Database Port", type=int, default=5432 if db_engine == "postgresql" else 3306)
            db_name = click.prompt("  Database Name", default=step3_defaults.get("name", "dwrms"))
            db_user = click.prompt("  Database Username", default=step3_defaults.get("user", "dwrms_prod"))
            db_pass = click.prompt("  Database Password", hide_input=True, default=step3_defaults.get("password", ""))

            print_info(f"Testing connectivity to {db_engine} at {db_host}:{db_port}/{db_name}...")
            try:
                probe_res = asyncio.run(
                    SetupManager.test_database(db_engine, db_host, db_port, db_name, db_user, db_pass)
                )
                print_success(f"Database connection verified! (Latency: {probe_res.get('latency_ms')} ms)")
                break
            except Exception as e:
                print_error(f"Database probe failed: {e}")
                if not click.confirm("  Would you like to re-enter database credentials?", default=True):
                    print_warning("Proceeding with unverified database configuration.")
                    break

    step3_data = {
        "engine": db_engine,
        "host": db_host,
        "port": db_port,
        "name": db_name,
        "user": db_user,
        "password": db_pass,
    }
    SetupManager.save_step(3, step3_data)

    # ── STEP 4: INITIAL ADMINISTRATOR ACCOUNT ────────────────────
    click.secho("\n[STEP 4/8] Initial System Administrator Account", fg="cyan", bold=True)
    step4_defaults = saved_state.get("step_4_admin", {})
    admin_email = click.prompt("  Administrator Email", default=step4_defaults.get("email", "admin@bikita.com"))
    admin_fname = click.prompt("  First Name", default=step4_defaults.get("first_name", "System"))
    admin_lname = click.prompt("  Last Name", default=step4_defaults.get("last_name", "Administrator"))
    admin_dept = click.prompt("  Department", default=step4_defaults.get("department", "Maintenance"))

    while True:
        admin_pass = click.prompt("  Administrator Password", hide_input=True, confirmation_prompt=True)
        if len(admin_pass) < 8:
            print_error("Password must be at least 8 characters long.")
            continue
        break

    step4_data = {
        "email": admin_email,
        "first_name": admin_fname,
        "last_name": admin_lname,
        "department": admin_dept,
        "password": admin_pass,
    }
    SetupManager.save_step(4, step4_data)
    print_success("Administrator account credentials validated.")

    # ── STEP 5: FILE STORAGE CONFIGURATION ───────────────────────
    click.secho("\n[STEP 5/8] Persistent File & Attachment Storage", fg="cyan", bold=True)
    step5_defaults = saved_state.get("step_5_storage", {})
    default_storage = "/var/dwrms/storage" if env_type != "development" else "./storage"
    storage_path = click.prompt("  Storage Directory Path", default=step5_defaults.get("path", default_storage))
    max_upload_mb = click.prompt("  Max Attachment Upload Size (MB)", type=int, default=step5_defaults.get("max_upload_size_mb", 25))

    print_info(f"Probing storage path write access at {storage_path}...")
    st_res = SetupManager.test_storage(storage_path)
    if st_res.get("write_ok"):
        print_success(f"Storage path verified writable ({st_res.get('free_gb')} GB free space, {st_res.get('free_percentage')}% free).")
    else:
        print_warning(f"Storage probe notice: {st_res.get('error', 'Unwritable')}. Directory will be created during initialization.")

    step5_data = {
        "path": storage_path,
        "max_upload_size_mb": max_upload_mb,
    }
    SetupManager.save_step(5, step5_data)

    # ── STEP 6: BACKUPS & RETENTION POLICY ───────────────────────
    click.secho("\n[STEP 6/8] Disaster Recovery & Backup Policy", fg="cyan", bold=True)
    step6_defaults = saved_state.get("step_6_backups", {})
    default_backups = "/var/dwrms/backups" if env_type != "development" else "./backups"
    backup_path = click.prompt("  Backup Directory Path", default=step6_defaults.get("path", default_backups))
    backup_freq = click.prompt("  Backup Frequency", type=click.Choice(["daily", "weekly", "hourly"]), default="daily")
    retention_days = click.prompt("  Backup Retention Window (Days)", type=int, default=step6_defaults.get("retention_days", 30))

    step6_data = {
        "path": backup_path,
        "frequency": backup_freq,
        "retention_days": retention_days,
    }
    SetupManager.save_step(6, step6_data)
    print_success("Disaster recovery policy configured.")

    # ── STEP 7: OPTIONAL REMOTE CONNECTIVITY ─────────────────────
    click.secho("\n[STEP 7/8] Optional Remote Connectivity", fg="cyan", bold=True)
    click.echo("  Configure how operators and remote desktop clients securely connect to this server.")
    click.echo("  (Note: SSH server administration remains independently active on port 22.)")
    remote_mode = click.prompt(
        "  Remote Connectivity Mode",
        type=click.Choice(["local_only", "org_managed", "tailscale"], case_sensitive=False),
        default="local_only",
    )

    tailscale_key = ""
    if remote_mode == "tailscale":
        tailscale_key = click.prompt("  Optional Tailscale Auth Key (leave blank to authenticate manually)", default="", hide_input=True)

    step7_data = {
        "mode": remote_mode,
        "tailscale_auth_key": tailscale_key,
    }
    SetupManager.save_step(7, step7_data)
    print_success(f"Remote connectivity mode: {remote_mode.upper()}")

    # ── STEP 8: SYSTEM VERIFICATION & SETUP FINALIZATION ─────────
    click.secho("\n[STEP 8/8] System Verification Checklist & Provisioning", fg="cyan", bold=True)
    click.echo("Executing schema migrations, seeding mining baseline data, provisioning administrator, and locking setup...\n")

    combined_config = {
        "step_1_platform": step1_data,
        "step_2_network": step2_data,
        "step_3_database": step3_data,
        "step_4_admin": step4_data,
        "step_5_storage": step5_data,
        "step_6_backups": step6_data,
        "step_7_remote": step7_data,
    }

    try:
        report = asyncio.run(SetupManager.finalize_setup(combined_config))
        _display_completion_report(report)
    except Exception as e:
        print_error(f"Setup Finalization Failed: {e}")
        sys.exit(1)


def _display_completion_report(report: dict):
    """Displays formatted final setup report."""
    print_header("SERVER SETUP COMPLETED & VERIFIED")
    click.secho("All system verification checks passed. The authoritative server is online.", fg="green", bold=True)
    click.echo(f"  Portal URL:       {report.get('application_url')}")
    click.echo(f"  Server Node:      {report.get('server_name')}")
    click.echo(f"  Platform Version: {report.get('version')}")
    click.echo(f"  Environment:      {report.get('environment')}")
    click.echo(f"  Superuser Admin:  {report.get('admin_email')}\n")

    click.secho("Next Administrative Steps:", fg="cyan", bold=True)
    for step in report.get("next_steps", []):
        click.echo(f"  * {step}")
    click.echo("")
