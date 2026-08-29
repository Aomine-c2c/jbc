import pytest
from httpx import AsyncClient
from app.modules.jobs.models import JobCard
from app.modules.iam.models import User, Department

@pytest.mark.asyncio
async def test_dashboard_metrics_unauthorized(async_client: AsyncClient):
    response = await async_client.post("/api/v1/dashboard/metrics", json={})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_dashboard_metrics_basic_load(async_client: AsyncClient, token_user_a: str):
    # Test basic payload
    headers = {"Authorization": f"Bearer {token_user_a}"}
    response = await async_client.post("/api/v1/dashboard/metrics", json={}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "job_metrics" in data
    assert "fleet_metrics" in data
    assert "department_workload" in data
    assert "timeseries_data" in data

@pytest.mark.asyncio
async def test_dashboard_metrics_filtering(async_client: AsyncClient, token_user_a: str):
    # Filter by specific priority
    headers = {"Authorization": f"Bearer {token_user_a}"}
    payload = {"priority": 1}
    response = await async_client.post("/api/v1/dashboard/metrics", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["job_metrics"]["total_jobs"], int)

@pytest.mark.asyncio
async def test_dashboard_metrics_cross_dept_denied(async_client: AsyncClient, token_user_a: str, seed_user_a: User):
    import uuid
    headers = {"Authorization": f"Bearer {token_user_a}"}
    other_dept = str(uuid.uuid4())
    payload = {"department_id": other_dept}
    response = await async_client.post("/api/v1/dashboard/metrics", json=payload, headers=headers)
    
    if not any(r.name in ["ADMIN", "MANAGER"] for r in seed_user_a.roles):
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_dashboard_analytics_summary(async_client: AsyncClient, admin_headers: dict):
    """
    Test the analytics summary endpoint for the dashboard.
    """
    response = await async_client.get("/api/v1/dashboard/analytics", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    
    assert "active_job_cards" in data
    assert "pending_approvals" in data
    assert "fleet_utilization" in data
    assert "recent_activity" in data
    assert isinstance(data["recent_activity"], list)
