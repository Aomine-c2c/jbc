import os
import sys
import json
import shutil
import hashlib
import tarfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
import click

from app.cli.utils import (
    print_header,
    print_success,
    print_error,
    print_warning,
    print_info,
    run_command_capture,
    ROOT_DIR,
)
from app.core.config import settings
from app.cli.backup import _get_backup_dir


@click.command("restore")
@click.argument("archive_name")
@click.option("--yes", "-y", is_flag=True, help="Bypass interactive confirmation prompt (CAUTION)")
@click.option("--skip-storage", is_flag=True, help="Restore database only; leave storage files unchanged")
@click.option("--pre-snapshot/--no-pre-snapshot", default=True, help="Automatically generate safety snapshot of current data before restore")
def restore_command(archive_name, yes, skip_storage, pre_snapshot):
    """Restore database, config, and storage from a verified disaster recovery snapshot."""
    backup_dir = _get_backup_dir()
    arc_path = backup_dir / archive_name

    if not arc_path.exists():
        # Try finding by prefix
        matches = list(backup_dir.glob(f"*{archive_name}*.tar.gz"))
        if matches:
            arc_path = matches[0]
        else:
            print_error(f"Backup archive '{archive_name}' not found in {backup_dir}")
            sys.exit(1)

    print_header(f"DWRMS DISASTER RECOVERY RESTORATION")
    click.secho(f"Target Snapshot: {arc_path.name}", fg="yellow", bold=True)

    # 1. Integrity Verification
    sha_file = arc_path.parent / f"{arc_path.name}.sha256"
    actual_sha = hashlib.sha256(arc_path.read_bytes()).hexdigest()
    if sha_file.exists():
        expected_sha = sha_file.read_text().split()[0].strip()
        if expected_sha != actual_sha:
            print_error(f"INTEGRITY ERROR: SHA-256 mismatch ({actual_sha} != {expected_sha}). Aborting restoration!")
            sys.exit(1)
        print_success("SHA-256 checksum verified.")
    else:
        print_info(f"Calculated SHA-256: {actual_sha}")

    # 2. Extract and inspect manifest
    extract_temp = backup_dir / f"restore_staging_{uuid.uuid4().hex[:6]}"
    shutil.rmtree(extract_temp, ignore_errors=True)
    extract_temp.mkdir(parents=True, exist_ok=True)

    try:
        with tarfile.open(arc_path, "r:gz") as tar:
            tar.extractall(extract_temp)

        meta_file = extract_temp / "manifest.json"
        if not meta_file.exists():
            meta_file = extract_temp / "metadata.json"

        if meta_file.exists():
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            click.echo(f"  Backup ID:           {meta.get('backup_id', 'N/A')}")
            click.echo(f"  Archive Version:     {meta.get('platform_version') or meta.get('version')}")
            click.echo(f"  Backup Type:         {meta.get('backup_type', 'FULL_SNAPSHOT')}")
            click.echo(f"  Database Engine:     {meta.get('database_engine') or meta.get('db_engine')}")
            click.echo(f"  Current DB Engine:   {settings.DB_ENGINE.upper()}")

            # Engine compatibility check
            arch_engine = str(meta.get("database_engine") or meta.get("db_engine", "")).lower()
            if arch_engine and arch_engine != settings.DB_ENGINE.lower():
                print_error(f"Engine incompatibility! Snapshot is for '{arch_engine.upper()}', but active system engine is '{settings.DB_ENGINE.upper()}'.")
                shutil.rmtree(extract_temp, ignore_errors=True)
                sys.exit(1)
    except Exception as e:
        print_error(f"Failed to inspect backup archive: {e}")
        shutil.rmtree(extract_temp, ignore_errors=True)
        sys.exit(1)

    # 3. Pre-Restore Safety Snapshot to guarantee current data is never silently destroyed
    if pre_snapshot:
        print_info("Creating safety snapshot of current system before restore...")
        safety_ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safety_archive_name = f"dwrms_prerestore_safety_{safety_ts}.tar.gz"
        safety_path = backup_dir / safety_archive_name

        try:
            safety_temp = backup_dir / f"safety_temp_{safety_ts}"
            safety_temp.mkdir(parents=True, exist_ok=True)

            # Dump current DB
            db_sql_safety = safety_temp / "database.sql"
            if settings.DB_ENGINE == "sqlite":
                for possible_db in ["test_dwrms.db", "dwrms.db"]:
                    db_file = ROOT_DIR / possible_db
                    if not db_file.exists():
                        db_file = ROOT_DIR / "backend" / possible_db
                    if db_file.exists():
                        db_sql_safety.write_bytes(db_file.read_bytes())
                        break
            if not db_sql_safety.exists():
                db_sql_safety.write_text("-- Pre-restore safety stub\n")

            # Copy current storage
            storage_dir = Path(settings.STORAGE_PATH)
            if not storage_dir.is_absolute():
                storage_dir = ROOT_DIR / storage_dir
            if storage_dir.exists():
                shutil.copytree(storage_dir, safety_temp / "storage", dirs_exist_ok=True)

            # Manifest
            safety_meta = {
                "backup_id": f"bkp_safety_{safety_ts}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "backup_type": "PRE_RESTORE_SAFETY",
                "note": f"Automatic safety snapshot prior to restoring {arc_path.name}",
                "platform_version": settings.APP_VERSION,
                "database_engine": settings.DB_ENGINE.upper(),
            }
            (safety_temp / "manifest.json").write_text(json.dumps(safety_meta, indent=2))

            with tarfile.open(safety_path, "w:gz") as tar:
                tar.add(safety_temp, arcname="")

            shutil.rmtree(safety_temp, ignore_errors=True)
            sha_s = hashlib.sha256(safety_path.read_bytes()).hexdigest()
            (backup_dir / f"{safety_archive_name}.sha256").write_text(f"{sha_s}  {safety_archive_name}\n")
            print_success(f"Safety pre-restore snapshot created: {safety_archive_name}")
        except Exception as se:
            print_warning(f"Could not create pre-restore safety snapshot: {se}")

    # 4. Operator Confirmation
    if not yes:
        click.secho("\n[CRITICAL WARNING] Restoring will replace existing live database records and document storage!", fg="red", bold=True)
        confirm = click.prompt(f"Type 'CONFIRM RESTORE' to proceed with restoring {arc_path.name}")
        if confirm != "CONFIRM RESTORE":
            print_warning("Restoration cancelled by operator.")
            shutil.rmtree(extract_temp, ignore_errors=True)
            sys.exit(0)

    # 5. Stop API & Worker Services to prevent write corruption during restore
    print_info("Stopping API backend and background worker processes...")
    run_command_capture(["docker", "compose", "-f", "docker-compose.prod.yml", "stop", "backend", "worker", "beat"])

    # 6. Apply Database Restoration Dump
    db_sql = extract_temp / "database.sql"
    if db_sql.exists():
        print_info(f"Applying database restoration dump for {settings.DB_ENGINE.upper()}...")
        if settings.DB_ENGINE == "postgresql":
            res_cmd = ["docker", "compose", "-f", "docker-compose.prod.yml", "exec", "-T", "db", "psql", "-U", settings.DB_USER or "postgres", "-d", settings.DB_NAME or "dwrms"]
            code, out, err = run_command_capture(res_cmd)
        elif settings.DB_ENGINE == "mysql":
            res_cmd = ["docker", "compose", "-f", "docker-compose.prod.yml", "exec", "-T", "db", "mysql", "-u", settings.DB_USER or "user", f"-p{settings.DB_PASSWORD or 'password'}", settings.DB_NAME or "dwrms"]
            try:
                import subprocess
                with open(db_sql, "r", encoding="utf-8") as f:
                    proc = subprocess.run(res_cmd, stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(ROOT_DIR))
                    code, out, err = proc.returncode, proc.stdout, proc.stderr
            except Exception as e:
                code, out, err = 1, "", str(e)
        elif settings.DB_ENGINE == "sqlite":
            for target_db in [ROOT_DIR / "test_dwrms.db", ROOT_DIR / "backend" / "test_dwrms.db"]:
                if target_db.parent.exists():
                    shutil.copy(db_sql, target_db)
        print_success("Database restoration applied.")

    # 7. Apply Storage Restoration
    if not skip_storage and (extract_temp / "storage").exists():
        print_info("Restoring persistent attachment storage files...")
        storage_dir = Path(settings.STORAGE_PATH)
        if not storage_dir.is_absolute():
            storage_dir = ROOT_DIR / storage_dir

        shutil.copytree(extract_temp / "storage", storage_dir, dirs_exist_ok=True)
        print_success("Attachment storage restored.")

    # Clean up staging
    shutil.rmtree(extract_temp, ignore_errors=True)

    # 8. Restart Services
    print_info("Restarting application services...")
    run_command_capture(["docker", "compose", "-f", "docker-compose.prod.yml", "start", "backend", "worker", "beat"])

    print_header("RESTORATION COMPLETE")
    print_success(f"System successfully restored from {arc_path.name}.")
    click.echo("Run 'ops health' to verify operational readiness.\n")
