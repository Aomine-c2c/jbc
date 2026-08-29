import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_readiness_check(async_client: AsyncClient):
    response = await async_client.get("/api/v1/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "services" in data
    assert "database" in data["services"]
    assert data["services"]["database"]["status"] == "connected"
    assert "storage" in data["services"]


@pytest.mark.asyncio
async def test_version(async_client: AsyncClient):
    response = await async_client.get("/api/v1/version")
    assert response.status_code == 200
    data = response.json()
    assert data["version"].startswith("v2.")
    assert "environment" in data


@pytest.mark.asyncio
async def test_info(async_client: AsyncClient):
    response = await async_client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert data["architecture"] == "Server-First Multi-Client"
    assert data["version"].startswith("v2.")
    assert data["database"]["connected"] is True


@pytest.mark.asyncio
async def test_diagnostics(async_client: AsyncClient):
    response = await async_client.get("/api/v1/diagnostics")
    assert response.status_code == 200
    data = response.json()
    assert "system" in data
    assert "database" in data
    assert "storage" in data
