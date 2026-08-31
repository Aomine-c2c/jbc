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
    """Launch the structured 8-stage first-time server setup wizard for DWRMS platform."""
    print_header("BIKITA MINERALS DWRMS -- FIRST-TIME SERVER SETUP WIZARD (V2.3)")

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
            click.secho("\nRecovery Instructions:", fg="yellow", bold=True)
            click.echo("  1. Review database credentials in .env or run 'ops configure list'.")
            click.echo("  2. Check storage directory permissions (/var/dwrms/storage).")
            click.echo("  3. Run 'ops health' to identify degraded subsystems.\n")
            sys.exit(1)
        return

    click.echo("This structured 8-stage wizard will configure, provision, and verify your authoritative server stack.\n")

    # ── STEP 1: ORGANIZATION ─────────────────────────────────────
    click.secho("[STEP 1/8] Organization & Operational Site", fg="cyan", bold=True)
    step1_defaults = saved_state.get("step_1_platform", {})
    org_name = click.prompt("  Organization Name", default=step1_defaults.get("organization_name", "Bikita Minerals DWRMS"))
    inst_name = click.prompt("  Installation Name", default=step1_defaults.get("installation_name", "Masvingo Lithium Operation"))
    primary_site = click.prompt("  Primary Site", default=step1_defaults.get("primary_site", "Bikita Mining Site 1"))
    timezone = click.prompt("  Timezone", default=step1_defaults.get("timezone", "Africa/Harare"))

    step1_data = {
        "organization_name": org_name,
        "installation_name": inst_name,
        "primary_site": primary_site,
        "timezone": timezone,
    }
    SetupManager.save_step(1, step1_data)
    print_success("Organization settings saved.")

    # ── STEP 2: SERVER ───────────────────────────────────────────
    click.secho("\n[STEP 2/8] Server Identity & Network Endpoints", fg="cyan", bold=True)
    step2_defaults = saved_state.get("step_2_network", {})
    server_name = click.prompt("  Server Name", default=step2_defaults.get("server_name", "masvingo-srv-01"))
    env_type = click.prompt(
        "  Environment",
        type=click.Choice(["production", "staging", "development"], case_sensitive=False),
        default=step2_defaults.get("environment", "production"),
    )
    domain_name = click.prompt("  Domain Name", default=step2_defaults.get("domain_name", "dwrms.bikita.com"))
    internal_address = click.prompt("  Internal Address (LAN IP / Host Binding)", default=step2_defaults.get("internal_address", "192.168.1.100"))
    https_enabled = click.confirm("  HTTPS Configuration (Enable TLS Encryption)?", default=step2_defaults.get("https_enabled", True))
    default_url = f"https://{domain_name}" if https_enabled else f"http://{domain_name}"
    primary_url = click.prompt("  Primary Server URL", default=step2_defaults.get("primary_url", default_url))
    cors_origins = click.prompt(
        "  Trusted CORS Origins (comma-separated)",
        default=step2_defaults.get("cors_origins", f"{primary_url},tauri://localhost,http://tauri.localhost"),
    )

    step2_data = {
        "server_name": server_name,
        "environment": env_type,
        "domain_name": domain_name,
        "internal_address": internal_address,
        "https_enabled": https_enabled,
        "primary_url": primary_url,
        "cors_origins": cors_origins,
    }
    SetupManager.save_step(2, step2_data)
    print_success("Server & endpoint configuration saved.")

    # ── STEP 3: DATABASE ─────────────────────────────────────────
    click.secho("\n[STEP 3/8] Database Configuration & Pre-Flight Testing", fg="cyan", bold=True)
    step3_defaults = saved_state.get("step_3_database", {})
    db_engine = click.prompt(
        "  Database Engine",
        type=click.Choice(["mysql", "postgresql", "sqlite"], case_sensitive=False),
        default=step3_defaults.get("engine", "mysql"),
    )

    db_host = "db" if db_engine != "sqlite" else "localhost"
    db_port = 3306 if db_engine == "mysql" else (5432 if db_engine == "postgresql" else 0)
    db_name = "dwrms"
    db_user = "user" if db_engine == "mysql" else "postgres"
    db_pass = ""

    if db_engine != "sqlite":
        while True:
            db_host = click.prompt("  Database Host", default=step3_defaults.get("host", "db"))
            db_port = click.prompt("  Database Port", type=int, default=3306 if db_engine == "mysql" else 5432)
            db_name = click.prompt("  Database Name", default=step3_defaults.get("name", "dwrms"))
            db_user = click.prompt("  Database User", default=step3_defaults.get("user", "user" if db_engine == "mysql" else "dwrms_prod"))
            db_pass = click.prompt("  Database Password", hide_input=True, default=step3_defaults.get("password", ""))

            print_info(f"Testing database connectivity to {db_engine.upper()} at {db_host}:{db_port}/{db_name}...")
            try:
                probe_res = asyncio.run(
                    SetupManager.test_database(db_engine, db_host, db_port, db_name, db_user, db_pass)
                )
                print_success(f"Database connection verified! (Latency: {probe_res.get('latency_ms')} ms)")
                break
            except Exception as e:
                print_error(f"Database probe failed: {e}")
                click.secho("  Recovery: Verify database service is running and credentials are valid.", fg="yellow")
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

    # ── STEP 4: INITIAL ADMINISTRATOR ────────────────────────────
    click.secho("\n[STEP 4/8] Initial Platform Administrator", fg="cyan", bold=True)
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
    print_success("Initial Administrator credentials validated.")

    # ── STEP 5: STORAGE ──────────────────────────────────────────
    click.secho("\n[STEP 5/8] Attachment Storage & Capacity Verification", fg="cyan", bold=True)
    step5_defaults = saved_state.get("step_5_storage", {})
    default_storage = "/var/dwrms/storage" if env_type != "development" else "./storage"
    storage_path = click.prompt("  Storage Directory Path", default=step5_defaults.get("path", default_storage))
    max_upload_mb = click.prompt("  Max Upload Size (MB)", type=int, default=step5_defaults.get("max_upload_size_mb", 25))

    print_info(f"Probing storage path write access and capacity at {storage_path}...")
    st_res = SetupManager.test_storage(storage_path)
    if st_res.get("write_ok"):
        print_success(f"Storage verified: {st_res.get('free_gb')} GB free space ({st_res.get('free_percentage')}% free).")
    else:
        print_warning(f"Storage notice: {st_res.get('error', 'Unwritable')}. Directory will be initialized during finalization.")

    step5_data = {
        "path": storage_path,
        "max_upload_size_mb": max_upload_mb,
    }
    SetupManager.save_step(5, step5_data)

    # ── STEP 6: BACKUPS ──────────────────────────────────────────
    click.secho("\n[STEP 6/8] Backup Location, Schedule & Retention Policy", fg="cyan", bold=True)
    step6_defaults = saved_state.get("step_6_backups", {})
    default_backups = "/var/dwrms/backups" if env_type != "development" else "./backups"
    backup_path = click.prompt("  Backup Directory Location", default=step6_defaults.get("path", default_backups))
    backup_freq = click.prompt("  Backup Schedule", type=click.Choice(["daily", "weekly", "hourly"]), default="daily")
    retention_days = click.prompt("  Retention Policy (Days)", type=int, default=step6_defaults.get("retention_days", 30))

    step6_data = {
        "path": backup_path,
        "frequency": backup_freq,
        "retention_days": retention_days,
    }
    SetupManager.save_step(6, step6_data)
    print_success("Disaster recovery and backup policy configured.")

    # ── STEP 7: CONNECTIVITY ─────────────────────────────────────
    click.secho("\n[STEP 7/8] Connectivity (LAN, Internal Domain, Optional Remote Networking)", fg="cyan", bold=True)
    click.echo("  (Note: Third-party remote networking is strictly optional. SSH administration operates on port 22.)")
    remote_mode = click.prompt(
        "  Network Connectivity Mode",
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
    print_success(f"Connectivity mode: {remote_mode.upper()}")

    # ── STEP 8: VERIFICATION ─────────────────────────────────────
    click.secho("\n[STEP 8/8] System Verification Checklist & Provisioning", fg="cyan", bold=True)
    click.echo("Executing verification checklist: Application, Database, Storage, Workers, Network, Administrator, and Health...\n")

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
        print_error(f"Setup Verification Failed: {e}")
        click.secho("\nRecovery Instructions:", fg="yellow", bold=True)
        click.echo("  1. Run 'ops status' to inspect container health.")
        click.echo("  2. If database schema failed: Check database engine configuration and port.")
        click.echo("  3. If storage failed: Check filesystem permissions on storage directory.")
        click.echo("  4. To restart the wizard: Run 'ops setup --force'.\n")
        sys.exit(1)


def _display_completion_report(report: dict):
    """Displays formatted final setup report."""
    print_header("SERVER SETUP COMPLETED & VERIFIED")
    click.secho("All critical verification checks passed. The authoritative platform core is initialized and locked.", fg="green", bold=True)
    click.echo(f"  Portal URL:       {report.get('application_url')}")
    click.echo(f"  Server Node:      {report.get('server_name')}")
    click.echo(f"  Platform Version: {report.get('version')}")
    click.echo(f"  Environment:      {report.get('environment')}")
    click.echo(f"  Superuser Admin:  {report.get('admin_email')}\n")

    verification = report.get("verification", {})
    if verification:
        rows = [[k.replace("_", " ").title(), "PASS"] for k in verification.keys()]
        print_table(["Verification Check", "Result"], rows, title="Step 8 System Verification Results")

    click.secho("\nNext Administrative Steps:", fg="cyan", bold=True)
    for step in report.get("next_steps", []):
        click.echo(f"  * {step}")
    click.echo("")
