import os
import pytest
from httpx import AsyncClient
from app.core.setup_manager import SetupManager, SETUP_STATE_FILE


@pytest.mark.asyncio
async def test_setup_status_and_preflight(async_client: AsyncClient):
    # Ensure fresh setup state for test
    if SETUP_STATE_FILE.exists():
        SETUP_STATE_FILE.unlink()
    os.environ.pop("SETUP_COMPLETED", None)

    # 1. Check status
    res = await async_client.get("/api/v1/setup/status")
    assert res.status_code == 200
    data = res.json()
    assert "is_completed" in data

    # 2. Test Storage Probe
    st_res = await async_client.post("/api/v1/setup/test-storage", json={"path": "./storage"})
    assert st_res.status_code == 200
    st_data = st_res.json()
    assert st_data["write_ok"] is True
    assert "free_gb" in st_data

    # 3. Test Database Probe (SQLite mode in tests)
    db_res = await async_client.post(
        "/api/v1/setup/test-db",
        json={
            "engine": "sqlite",
            "host": "localhost",
            "port": 5432,
            "name": "test.db",
            "user": "",
            "password": "",
        },
    )
    assert db_res.status_code == 200
    db_data = db_res.json()
    assert db_data["status"] == "connected"

    # 4. Save Step 1
    step_res = await async_client.post(
        "/api/v1/setup/step/1",
        json={
            "organization_name": "Test Mining Corp",
            "installation_name": "Site Alpha",
            "server_name": "srv-alpha-01",
            "environment": "testing",
            "timezone": "UTC",
        },
    )
    assert step_res.status_code == 200
    assert step_res.json()["status"] == "saved"


@pytest.mark.asyncio
async def test_setup_finalize_and_locking(async_client: AsyncClient):
    # Ensure fresh setup state
    if SETUP_STATE_FILE.exists():
        SETUP_STATE_FILE.unlink()
    os.environ.pop("SETUP_COMPLETED", None)

    payload = {
        "step_1_platform": {
            "organization_name": "Test Mining Corp",
            "installation_name": "Site Alpha",
            "server_name": "srv-alpha-01",
            "environment": "testing",
            "timezone": "UTC",
        },
        "step_2_network": {
            "primary_url": "http://localhost:3000",
            "domain_name": "localhost",
            "local_ip": "127.0.0.1",
            "https_enabled": False,
            "cors_origins": "http://localhost:3000",
        },
        "step_3_database": {
            "engine": "sqlite",
            "host": "localhost",
            "port": 5432,
            "name": "test.db",
            "user": "",
            "password": "",
        },
        "step_4_admin": {
            "email": "test_admin@bikita.com",
            "first_name": "Test",
            "last_name": "Admin",
            "department": "Maintenance",
            "password": "SecurePassword123!",
        },
        "step_5_storage": {
            "path": "./storage",
            "max_upload_size_mb": 25,
        },
        "step_6_backups": {
            "path": "./backups",
            "frequency": "daily",
            "retention_days": 30,
        },
        "step_7_remote": {
            "mode": "local_only",
        },
    }

    # Finalize setup
    finalize_res = await async_client.post("/api/v1/setup/finalize", json={"config": payload})
    assert finalize_res.status_code == 200
    report = finalize_res.json()
    assert report["status"] == "success"
    assert report["admin_email"] == "test_admin@bikita.com"
    assert SetupManager.is_setup_completed() is True

    # Attempting to call finalize again should fail with 403 Forbidden
    dup_res = await async_client.post("/api/v1/setup/finalize", json={"config": payload})
    assert dup_res.status_code == 403

    # Clean up test state
    if SETUP_STATE_FILE.exists():
        SETUP_STATE_FILE.unlink()
    os.environ.pop("SETUP_COMPLETED", None)
