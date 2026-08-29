import os
import sys
import platform
import asyncio
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

    # 1. System Platform Overview
    click.secho("Platform Identity", fg="cyan", bold=True)
    click.echo(f"  Platform:        {_safe_str(settings.APP_NAME)}")
    click.echo(f"  Version:         {_safe_str(settings.APP_VERSION)}")
    click.echo(f"  Environment:     {_safe_str(settings.ENVIRONMENT)}")
    click.echo(f"  Host Node:       {_safe_str(platform.node())} ({_safe_str(platform.system())} {_safe_str(platform.release())})")
    click.echo(f"  Authoritative:   {_safe_str(settings.FRONTEND_URL)}")

    # 2. Container Services Table
    click.secho("\nContainer Stack Status (Docker Compose)", fg="cyan", bold=True)
    code, out, _ = run_command_capture(["docker", "compose", "-f", "docker-compose.prod.yml", "ps", "--format", "table {{.Service}}\t{{.Status}}\t{{.Ports}}"])
    if code == 0 and out.strip():
        lines = out.strip().splitlines()
        if len(lines) > 1:
            headers = [h.strip() for h in lines[0].split("\t") if h.strip()]
            rows = [[c.strip() for c in line.split("\t")] for line in lines[1:]]
            print_table(headers, rows)
        else:
            click.echo(_safe_str(out))
    else:
        # Fallback if docker compose ps table format isn't supported or containers stopped
        code2, out2, _ = run_command_capture(["docker", "compose", "-f", "docker-compose.prod.yml", "ps"])
        if code2 == 0 and out2.strip():
            click.echo(_safe_str(out2))
        else:
            click.secho("  Containers not running or Docker daemon unreachable.", fg="bright_black")

    # 3. Component Deep Status
    service_rows = []

    # Database
    async def _test_db():
        from app.db.session import engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()

    try:
        asyncio.run(_test_db())
        service_rows.append(["Relational Database", settings.DB_ENGINE.upper(), "ONLINE (Connected)"])
    except Exception as e:
        service_rows.append(["Relational Database", settings.DB_ENGINE.upper(), f"OFFLINE ({str(e)[:30]})"])

    # Redis Broker
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL, socket_timeout=1.5)
        r.ping()
        service_rows.append(["Redis Broker", "In-Memory Broker", "ONLINE (Responding)"])
    except Exception:
        status_note = "OFFLINE" if settings.ENVIRONMENT == "production" else "STANDBY (Dev)"
        service_rows.append(["Redis Broker", "In-Memory Broker", status_note])

    # Storage Subsystem
    st_health = storage_manager.get_storage_health()
    if st_health.get("write_ok"):
        free_gb = round(st_health.get("free_bytes", 0) / (1024 ** 3), 1)
        service_rows.append(["Storage Subsystem", st_health["path"], f"HEALTHY ({free_gb} GB free, {st_health.get('free_percentage')}% free)"])
    else:
        service_rows.append(["Storage Subsystem", st_health["path"], f"UNHEALTHY ({st_health.get('error', 'Error')})"])

    print_table(["Component", "Target / Engine", "Operational State"], service_rows, title="Authoritative Core Subsystems")
    click.echo("")
