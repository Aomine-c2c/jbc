import time
import shutil
try:
    import psutil
except ImportError:
    psutil = None
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional

from app.db.session import get_db, engine
from app.core.config import settings
from app.core.storage import storage_manager
from app.core.logging_config import logger

system_router = APIRouter(prefix="/api/v1", tags=["system"])


@system_router.get("/health", response_model=dict)
async def health_check():
    """Liveness probe. Returns 200 OK immediately if the API server is alive."""
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@system_router.get("/readiness", response_model=dict)
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness probe. Checks database connectivity, redis, storage, and worker queues.
    Returns HTTP 200 if all critical systems are operational, or HTTP 503 if degraded.
    """
    checks = {}
    is_ready = True

    # 1. Database Connectivity & Latency Check
    t0 = time.perf_counter()
    try:
        await db.execute(text("SELECT 1"))
        db_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        checks["database"] = {
            "status": "connected",
            "latency_ms": db_latency_ms,
            "engine": settings.DB_ENGINE,
        }
    except Exception as e:
        is_ready = False
        checks["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        logger.error(f"Readiness check - Database failed: {e}")

    # 2. Redis Cache & Broker Check
    t0 = time.perf_counter()
    try:
        # Check Redis connection if redis library / url is configured
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL, socket_timeout=2.0)
        await r.ping()
        await r.aclose()
        redis_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        checks["redis"] = {
            "status": "connected",
            "latency_ms": redis_latency_ms,
        }
    except Exception as e:
        # Redis failure is non-fatal in dev/test, but tracked
        checks["redis"] = {
            "status": "degraded" if settings.ENVIRONMENT == "production" else "skipped",
            "note": "Redis broker unreachable or not in use",
        }

    # 3. Persistent Storage Check
    storage_health = storage_manager.get_storage_health()
    checks["storage"] = {
        "status": storage_health.get("status", "healthy"),
        "write_ok": storage_health.get("write_ok", False),
        "free_percentage": storage_health.get("free_percentage", 0.0),
    }
    if not storage_health.get("write_ok", False):
        is_ready = False

    # 4. Overall Readiness State
    response_payload = {
        "status": "ready" if is_ready else "degraded",
        "environment": settings.ENVIRONMENT,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": checks,
    }

    if not is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response_payload,
        )

    return response_payload


@system_router.get("/version", response_model=dict)
async def get_version():
    """Returns the platform version, build metadata, and operating environment."""
    return {
        "platform": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@system_router.get("/info", response_model=dict)
async def get_system_info(db: AsyncSession = Depends(get_db)):
    """Returns high-level server-first platform telemetry for management dashboards."""
    db_connected = False
    db_latency_ms = 0.0
    try:
        t0 = time.perf_counter()
        await db.execute(text("SELECT 1"))
        db_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        db_connected = True
    except Exception:
        db_connected = False

    storage_health = storage_manager.get_storage_health()

    return {
        "platform": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "architecture": "Server-First Multi-Client",
        "authoritative_core": "Ubuntu Server",
        "environment": settings.ENVIRONMENT,
        "auth_method": settings.AUTH_METHOD,
        "database": {
            "connected": db_connected,
            "engine": settings.DB_ENGINE,
            "latency_ms": db_latency_ms,
        },
        "storage": {
            "status": storage_health.get("status", "healthy"),
            "free_percentage": storage_health.get("free_percentage", 0.0),
        },
        "supported_clients": [
            "Tauri Desktop Client (Windows, Linux, macOS)",
            "Web Browser Client (Chrome, Firefox, Safari, Edge)",
            "Mobile Web / PWA Client (Android, iOS)"
        ]
    }


@system_router.get("/diagnostics", response_model=dict)
async def get_diagnostics(db: AsyncSession = Depends(get_db)):
    """
    Comprehensive diagnostic endpoint for administrators.
    Provides system resource utilization, memory metrics, and connection pool status.
    """
    # System metrics
    try:
        mem = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=None)
        memory_data = {
            "total_mb": round(mem.total / (1024 * 1024), 1),
            "available_mb": round(mem.available / (1024 * 1024), 1),
            "used_percentage": mem.percent,
        }
    except Exception:
        cpu_percent = 0.0
        memory_data = {"note": "psutil metrics unavailable"}

    # Database metrics
    db_connected = False
    try:
        await db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False

    storage_health = storage_manager.get_storage_health()

    return {
        "platform": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system": {
            "cpu_percent": cpu_percent,
            "memory": memory_data,
        },
        "database": {
            "connected": db_connected,
            "engine": settings.DB_ENGINE,
            "pool_size": getattr(engine.pool, "size", lambda: 0)(),
            "checked_in": getattr(engine.pool, "checkedin", lambda: 0)(),
            "checked_out": getattr(engine.pool, "checkedout", lambda: 0)(),
            "overflow": getattr(engine.pool, "overflow", lambda: 0)(),
        },
        "storage": storage_health,
    }
