import sys
import time
import asyncio
import click
from sqlalchemy import text

from app.cli.utils import (
    print_header,
    print_table,
    print_success,
    print_error,
    print_warning,
)
from app.core.config import settings
from app.core.storage import storage_manager


@click.command("health")
@click.option("--timeout", default=5.0, help="Per-subsystem timeout in seconds (default: 5.0s)")
def health_command(timeout):
    """Perform a deep health and latency check across all core subsystems."""
    print_header("DWRMS DEEP HEALTH & READINESS PROBE")

    all_healthy = True
    results = []

    # 1. Database Connectivity & Query Latency
    async def _probe_db():
        from app.db.session import engine
        t0 = time.perf_counter()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        latency = (time.perf_counter() - t0) * 1000
        await engine.dispose()
        return latency

    try:
        db_lat = asyncio.run(asyncio.wait_for(_probe_db(), timeout=timeout))
        results.append(["Database Core", settings.DB_ENGINE.upper(), f"{db_lat:.2f} ms", "PASS"])
    except Exception as e:
        all_healthy = False
        results.append(["Database Core", settings.DB_ENGINE.upper(), "-", f"FAIL: {str(e)[:30]}"])

    # 2. Redis In-Memory Broker & Cache
    try:
        import redis
        t0 = time.perf_counter()
        r = redis.from_url(settings.REDIS_URL, socket_timeout=timeout)
        r.ping()
        redis_lat = (time.perf_counter() - t0) * 1000
        results.append(["Redis Broker", "Broker/Cache", f"{redis_lat:.2f} ms", "PASS"])
    except Exception as e:
        if settings.ENVIRONMENT == "production":
            all_healthy = False
            results.append(["Redis Broker", "Broker/Cache", "-", f"FAIL: {str(e)[:30]}"])
        else:
            results.append(["Redis Broker", "Broker/Cache", "-", "STANDBY (Non-prod)"])

    # 3. Storage Subsystem Read/Write Probe
    st_health = storage_manager.get_storage_health()
    if st_health.get("write_ok"):
        free_pct = st_health.get("free_percentage", 0.0)
        free_gb = round(st_health.get("free_bytes", 0) / (1024 ** 3), 1)
        results.append(["Storage Subsystem", "Filesystem", f"{free_gb} GB ({free_pct}%)", "PASS"])
    else:
        all_healthy = False
        results.append(["Storage Subsystem", "Filesystem", "-", f"FAIL: {st_health.get('error', 'Unwritable')}"])

    # 4. Web API Gateway Probe
    try:
        import urllib.request
        import urllib.error
        api_url = f"{settings.FRONTEND_URL.rstrip('/')}/api/v1/health"
        t0 = time.perf_counter()
        req = urllib.request.Request(api_url, headers={"User-Agent": "DWRMS-Ops-CLI"})
        # Allow self-signed in local probe
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            api_lat = (time.perf_counter() - t0) * 1000
            if resp.status == 200:
                results.append(["API Gateway", "HTTP Gateway", f"{api_lat:.2f} ms", "PASS"])
            else:
                results.append(["API Gateway", "HTTP Gateway", f"HTTP {resp.status}", "WARN"])
    except Exception as e:
        results.append(["API Gateway", "HTTP Gateway", "-", f"SKIP/WARN: {str(e)[:25]}"])

    print_table(["Subsystem", "Target", "Latency / Metric", "Health State"], results)

    click.echo("")
    if all_healthy:
        print_success("ALL CRITICAL SUBSYSTEMS ARE OPERATIONAL (Exit Code 0)")
        sys.exit(0)
    else:
        print_error("DEGRADED SUBSYSTEM DETECTED (Exit Code 1)")
        sys.exit(1)
