import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_platform_status_and_health_check(async_client: AsyncClient, admin_headers: dict):
    # 1. Test platform status
    res = await async_client.get("/api/v1/platform/status", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "subsystems" in data
    assert data["subsystems"]["application"]["status"] == "HEALTHY"
    assert data["subsystems"]["database"]["status"] == "HEALTHY"
    assert data["subsystems"]["storage"]["status"] == "HEALTHY"
    assert data["subsystems"]["worker"]["status"] == "RUNNING"
    assert data["subsystems"]["network"]["status"] == "ONLINE"

    # 2. Test live health check
    hc_res = await async_client.post("/api/v1/platform/health-check", headers=admin_headers)
    assert hc_res.status_code == 200
    hc_data = hc_res.json()
    assert hc_data["status"] == "HEALTHY"
    assert hc_data["database"]["ok"] is True


@pytest.mark.asyncio
async def test_platform_diagnostics_and_updates(async_client: AsyncClient, admin_headers: dict):
    # Diagnostics
    diag_res = await async_client.get("/api/v1/platform/diagnostics", headers=admin_headers)
    assert diag_res.status_code == 200
    diag_data = diag_res.json()
    assert "memory" in diag_data
    assert "database_pool" in diag_data

    # Update status
    up_res = await async_client.get("/api/v1/platform/update-status", headers=admin_headers)
    assert up_res.status_code == 200
    up_data = up_res.json()
    assert up_data["status"] == "UP_TO_DATE"
    assert "installed_version" in up_data


@pytest.mark.asyncio
async def test_platform_backups_and_logs(async_client: AsyncClient, admin_headers: dict):
    # 1. Create a backup
    create_res = await async_client.post(
        "/api/v1/platform/backups/create",
        headers=admin_headers,
        json={"note": "Test Backup from pytest", "include_storage": True},
    )
    assert create_res.status_code == 200
    create_data = create_res.json()
    assert create_data["status"] == "created"
    assert "sha256" in create_data
    assert "filename" in create_data

    # 2. List backups
    list_res = await async_client.get("/api/v1/platform/backups", headers=admin_headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total_archives"] >= 1
    assert any(b["filename"] == create_data["filename"] for b in list_data["archives"])

    # 3. Read logs
    logs_res = await async_client.get("/api/v1/platform/logs?lines=50&level=ALL", headers=admin_headers)
    assert logs_res.status_code == 200
    logs_data = logs_res.json()
    assert "logs" in logs_data
    assert len(logs_data["logs"]) > 0
