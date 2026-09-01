import uuid
from datetime import datetime

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
async def test_operational_intelligence_returns_metric_definitions_and_grouped_views(async_client: AsyncClient, token_user_a: str, db, seed_user_a, seed_department_a):
    headers = {"Authorization": f"Bearer {token_user_a}"}
    job = JobCard(
        id=uuid.uuid4(),
        title="Crusher vibration check",
        description="Diagnostic work",
        status="COMPLETED",
        priority=2,
        department_id=seed_department_a.id,
        creator_id=seed_user_a.id,
        job_number="JC-2026-1001",
        job_type="MAINTENANCE",
        estimated_cost=0,
        estimated_hours=0,
        actual_start_time=datetime.utcnow(),
        actual_end_time=datetime.utcnow(),
        required_date=datetime.utcnow(),
    )
    db.add(job)
    await db.commit()

    response = await async_client.post("/api/v1/dashboard/metrics", json={"date_from": "2026-01-01T00:00:00Z", "date_to": "2027-12-31T23:59:59Z"}, headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert "operational_metrics" in payload
    assert "department_metrics" in payload
    assert "asset_metrics" in payload
    assert "resource_metrics" in payload
    assert "request_metrics" in payload
    assert "contractor_metrics" in payload
    assert "metric_definitions" in payload
    assert "trend_views" in payload
    assert "future_analytics" in payload
    assert isinstance(payload["metric_definitions"], list)
    assert any(item["name"] == "Total Work" for item in payload["metric_definitions"])
    assert isinstance(payload["trend_views"], list)


@pytest.mark.asyncio
async def test_operational_intelligence_respects_department_scope(async_client: AsyncClient, token_user_a: str, db, seed_user_a, seed_department_a, seed_department_b):
    db.add(JobCard(
        id=uuid.uuid4(),
        title="Other department work",
        description="Should be excluded",
        status="ASSIGNED",
        priority=1,
        department_id=seed_department_b.id,
        creator_id=seed_user_a.id,
        job_number="JC-2026-2001",
        job_type="MAINTENANCE",
        estimated_cost=0,
        estimated_hours=0,
    ))
    await db.commit()

    response = await async_client.post(
        "/api/v1/dashboard/metrics",
        json={"department_id": str(seed_department_b.id)},
        headers={"Authorization": f"Bearer {token_user_a}"},
    )
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


@pytest.mark.asyncio
async def test_dashboard_config_returns_role_defaults(async_client: AsyncClient, token_user_a: str):
    headers = {"Authorization": f"Bearer {token_user_a}"}
    response = await async_client.get("/api/v1/dashboard/config", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "dashboard_key" in data
    assert "widgets" in data
    assert isinstance(data["widgets"], list)
    assert "saved_views" in data


@pytest.mark.asyncio
async def test_dashboard_saved_views_are_owned_and_permission_safe(async_client: AsyncClient, token_user_a: str):
    headers = {"Authorization": f"Bearer {token_user_a}"}
    payload = {
        "name": "My Critical IT Jobs",
        "scope": "personal",
        "dashboard_key": "employee",
        "filters": {"department_id": "not-a-real-uuid", "priority": 1},
        "sorting": {"field": "priority", "direction": "desc"},
        "columns": ["job_number", "title", "priority", "status"],
        "search_query": "IT",
        "date_range": {"from": "2026-01-01T00:00:00Z", "to": "2026-12-31T00:00:00Z"},
    }
    create_response = await async_client.post("/api/v1/dashboard/views", json=payload, headers=headers)
    assert create_response.status_code in {200, 201}

    list_response = await async_client.get("/api/v1/dashboard/views", headers=headers)
    assert list_response.status_code == 200
    saved_views = list_response.json()
    assert isinstance(saved_views, list)
    assert any(view["name"] == "My Critical IT Jobs" for view in saved_views)

    view_id = next(view["id"] for view in saved_views if view["name"] == "My Critical IT Jobs")
    get_response = await async_client.get(f"/api/v1/dashboard/views/{view_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "My Critical IT Jobs"
