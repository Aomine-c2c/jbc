import os
import sys
import json
import time
import platform
import shutil
import asyncio
import click
from sqlalchemy import text

from app.cli.utils import (
    print_header,
    print_table,
    print_success,
    print_info,
)
from app.core.config import settings
from app.core.storage import storage_manager

try:
    import psutil
except ImportError:
    psutil = None


@click.command("diagnostics")
@click.option("--json-output", "--json", is_flag=True, help="Output diagnostics in raw JSON format")
def diagnostics_command(json_output):
    """Collect non-sensitive system and application metrics for troubleshooting."""
    data = {}

    # 1. Host & Platform Telemetry
    data["platform"] = {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "hostname": platform.node(),
        "os_type": platform.system(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "python_version": sys.version.split()[0],
    }

    # 2. Host Compute Resources
    if psutil:
        mem = psutil.virtual_memory()
        cpu_pct = psutil.cpu_percent(interval=0.2)
        data["compute"] = {
            "cpu_cores_logical": psutil.cpu_count(logical=True),
            "cpu_cores_physical": psutil.cpu_count(logical=False),
            "cpu_utilization_pct": cpu_pct,
            "memory_total_mb": round(mem.total / (1024 * 1024), 2),
            "memory_available_mb": round(mem.available / (1024 * 1024), 2),
            "memory_used_pct": mem.percent,
        }
    else:
        data["compute"] = {
            "cpu_cores": os.cpu_count(),
            "note": "Install psutil for detailed memory and CPU utilization metrics.",
        }

    # 3. Database Core Metrics
    async def _get_db_metrics():
        from app.db.session import engine
        t0 = time.perf_counter()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        lat = (time.perf_counter() - t0) * 1000
        pool = engine.pool
        pool_stats = {
            "size": pool.size() if hasattr(pool, "size") else 0,
            "checkedin": pool.checkedin() if hasattr(pool, "checkedin") else 0,
            "checkedout": pool.checkedout() if hasattr(pool, "checkedout") else 0,
            "overflow": pool.overflow() if hasattr(pool, "overflow") else 0,
        }
        await engine.dispose()
        return lat, pool_stats

    try:
        lat, pool_stats = asyncio.run(_get_db_metrics())
        data["database"] = {
            "engine": settings.DB_ENGINE,
            "latency_ms": round(lat, 2),
            "status": "connected",
            "connection_pool": pool_stats,
        }
    except Exception as e:
        data["database"] = {
            "engine": settings.DB_ENGINE,
            "status": f"error: {str(e)}",
        }

    # 4. Storage Metrics
    st_health = storage_manager.get_storage_health()
    data["storage"] = {
        "path": st_health.get("path"),
        "writable": st_health.get("write_ok"),
        "total_gb": round(st_health.get("total_bytes", 0) / (1024 ** 3), 2),
        "free_gb": round(st_health.get("free_bytes", 0) / (1024 ** 3), 2),
        "free_percentage": st_health.get("free_percentage", 0),
    }

    if json_output:
        click.echo(json.dumps(data, indent=2))
        return

    # Formatted Terminal Report
    print_header("DWRMS NON-SENSITIVE DIAGNOSTIC REPORT")

    p = data["platform"]
    print_table(
        ["Property", "Value"],
        [
            ["Application Version", p["version"]],
            ["Environment", p["environment"]],
            ["Node Hostname", p["hostname"]],
            ["Operating System", f"{p['os_type']} {p['os_release']} ({p['architecture']})"],
            ["Python Runtime", p["python_version"]],
        ],
        title="Host & Runtime",
    )

    c = data["compute"]
    c_rows = [["CPU Logical Cores", c.get("cpu_cores_logical", c.get("cpu_cores"))]]
    if "cpu_utilization_pct" in c:
        c_rows.append(["CPU Utilization", f"{c['cpu_utilization_pct']}%"])
        c_rows.append(["Total RAM", f"{c['memory_total_mb']} MB"])
        c_rows.append(["Available RAM", f"{c['memory_available_mb']} MB ({100 - c['memory_used_pct']:.1f}% free)"])
    print_table(["Metric", "Measurement"], c_rows, title="Compute Resources")

    db = data["database"]
    db_rows = [["Engine", db["engine"]], ["Status", db["status"]]]
    if "latency_ms" in db:
        db_rows.append(["Round-Trip Latency", f"{db['latency_ms']} ms"])
        if "connection_pool" in db:
            db_rows.append(["Pool Checked Out", db["connection_pool"].get("checkedout", 0)])
            db_rows.append(["Pool Total Size", db["connection_pool"].get("size", 0)])
    print_table(["Parameter", "Value"], db_rows, title="Database Subsystem")

    st = data["storage"]
    print_table(
        ["Storage Attribute", "Value"],
        [
            ["Directory Path", st["path"]],
            ["Writable Status", "Yes" if st["writable"] else "NO"],
            ["Capacity", f"{st['free_gb']} GB Free / {st['total_gb']} GB Total ({st['free_percentage']}% free)"],
        ],
        title="Attachment Storage",
    )

    click.echo("\n[INFO] To export raw JSON diagnostics for support tickets: ops diagnostics --json\n")
