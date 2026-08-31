import os
import sys
import platform
import asyncio
import time
from datetime import datetime, timezone
import click
from pathlib import Path
from sqlalchemy import text

from app.cli.utils import (
    print_header,
    print_table,
    run_command_capture,
    _safe_str,
    ROOT_DIR,
)
from app.core.config import settings
from app.core.storage import storage_manager


@click.command("status")
def status_command():
    """Display real-time status of all platform services, containers, and resources."""
    print_header("BIKITA MINERALS DWRMS -- PLATFORM STATUS")

    # 1. Identity & Environment Overview
    click.secho("Platform Identity & Environment", fg="cyan", bold=True)
    click.echo(f"  Platform:        {_safe_str(settings.APP_NAME)}")
    click.echo(f"  Version:         {_safe_str(settings.APP_VERSION)}")
    click.echo(f"  Environment:     {_safe_str(settings.ENVIRONMENT.upper())}")
    click.echo(f"  Host Node:       {_safe_str(platform.node())} ({_safe_str(platform.system())} {_safe_str(platform.release())})")
    click.echo(f"  Authoritative:   {_safe_str(settings.FRONTEND_URL)}")

    # 2. Container Stack Status (Docker Compose)
    click.secho("\nContainer Stack Status (Docker Compose)", fg="cyan", bold=True)
    code, out, _ = run_command_capture(["docker", "compose", "-f", "docker-compose.prod.yml", "ps", "--format", "table {{.Service}}\t{{.Status}}\t{{.Ports}}"])
    docker_services = {}
    if code == 0 and out.strip():
        lines = out.strip().splitlines()
        if len(lines) > 1:
            headers = [h.strip() for h in lines[0].split("\t") if h.strip()]
            rows = [[c.strip() for c in line.split("\t")] for line in lines[1:]]
            print_table(headers, rows)
            for r in rows:
                if len(r) >= 2:
                    docker_services[r[0]] = r[1]
        else:
            click.echo(_safe_str(out))
    else:
        code2, out2, _ = run_command_capture(["docker", "compose", "-f", "docker-compose.prod.yml", "ps"])
        if code2 == 0 and out2.strip():
            click.echo(_safe_str(out2))
        else:
            click.secho("  Containers not running or Docker daemon unreachable.", fg="bright_black")

    # 3. Component Deep Status (Application, API, Database, Worker, Storage, Backup)
    service_rows = []
    overall_healthy = True

    # 3.1 Application Status
    app_state = "ONLINE"
    service_rows.append(["Application Status", settings.APP_NAME, "OPERATIONAL (Server-First Core)"])

    # 3.2 API Status
    api_status_str = "OFFLINE"
    try:
        import urllib.request
        import ssl
        api_url = f"{settings.FRONTEND_URL.rstrip('/')}/api/v1/health"
        t0 = time.perf_counter()
        req = urllib.request.Request(api_url, headers={"User-Agent": "DWRMS-Ops-CLI"})
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, context=ctx, timeout=2.0) as resp:
            lat = round((time.perf_counter() - t0) * 1000, 1)
            if resp.status == 200:
                api_status_str = f"ONLINE ({lat} ms latency)"
            else:
                api_status_str = f"DEGRADED (HTTP {resp.status})"
    except Exception:
        # Fallback to local port probe
        if "backend" in docker_services and "Up" in docker_services["backend"]:
            api_status_str = f"ONLINE (Container: {docker_services['backend']})"
        else:
            api_status_str = "STANDBY / DIRECT LOCAL API"
    service_rows.append(["API Status", f"{settings.FRONTEND_URL.rstrip('/')}/api/v1", api_status_str])

    # 3.3 Database Status
    async def _test_db():
        from app.db.session import engine
        t0 = time.perf_counter()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        lat = (time.perf_counter() - t0) * 1000
        await engine.dispose()
        return lat

    try:
        db_lat = asyncio.run(_test_db())
        service_rows.append(["Database Status", settings.DB_ENGINE.upper(), f"ONLINE (Connected, {db_lat:.2f} ms)"])
    except Exception as e:
        overall_healthy = False
        service_rows.append(["Database Status", settings.DB_ENGINE.upper(), f"OFFLINE ({str(e)[:30]})"])

    # 3.4 Worker Status
    worker_info = "STANDBY (Dev)"
    if "worker" in docker_services:
        worker_info = f"ACTIVE ({docker_services['worker']})"
    else:
        try:
            import redis
            r = redis.from_url(settings.REDIS_URL, socket_timeout=1.0)
            r.ping()
            worker_info = "ONLINE (Broker Connected)"
        except Exception:
            if settings.ENVIRONMENT == "production":
                worker_info = "OFFLINE"
            else:
                worker_info = "STANDBY (In-Process Worker Loop)"
    service_rows.append(["Worker Status", "Celery / Background Tasks", worker_info])

    # 3.5 Storage Status
    st_health = storage_manager.get_storage_health()
    if st_health.get("write_ok"):
        free_gb = round(st_health.get("free_bytes", 0) / (1024 ** 3), 1)
        service_rows.append(["Storage Status", st_health["path"], f"HEALTHY ({free_gb} GB free, {st_health.get('free_percentage')}% free)"])
    else:
        service_rows.append(["Storage Status", st_health["path"], f"UNHEALTHY ({st_health.get('error', 'Error')})"])

    # 3.6 Backup Status
    backup_dir = Path(settings.BACKUP_DIR)
    if not backup_dir.is_absolute():
        backup_dir = ROOT_DIR / backup_dir
    
    backup_archives = sorted(backup_dir.glob("*.tar.gz"), key=lambda p: p.stat().st_mtime, reverse=True) if backup_dir.exists() else []
    if backup_archives:
        latest = backup_archives[0]
        mtime = datetime.fromtimestamp(latest.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        size_mb = f"{latest.stat().st_size / (1024 * 1024):.1f} MB"
        service_rows.append(["Backup Status", f"{len(backup_archives)} snapshot(s)", f"LATEST: {latest.name} ({mtime}, {size_mb})"])
    else:
        service_rows.append(["Backup Status", str(backup_dir), "NO SNAPSHOTS (Run 'ops backup create')"])

    # 3.7 Version & Environment
    service_rows.append(["Version", settings.APP_NAME, settings.APP_VERSION])
    service_rows.append(["Environment", "Target Deployment", settings.ENVIRONMENT.upper()])

    print_table(["Operational Item", "Target / Path", "State / Diagnostic"], service_rows, title="Authoritative System Subsystems")
    click.echo("")
