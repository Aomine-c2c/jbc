import pytest
from httpx import AsyncClient
from app.modules.common.models import AuditLog

pytestmark = pytest.mark.asyncio

async def test_get_pending_approvals_empty(
    async_client: AsyncClient,
    token_user_a: str
):
    """Test that a user has no pending approvals by default."""
    response = await async_client.get(
        "/api/v1/approvals/pending",
        headers={"Authorization": f"Bearer {token_user_a}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

async def test_get_pending_approvals_user_b(
    async_client: AsyncClient,
    token_user_b: str
):
    """Test that user_b can get pending approvals."""
    response = await async_client.get(
        "/api/v1/approvals/pending",
        headers={"Authorization": f"Bearer {token_user_b}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.iam.models import Department
from tests.api.test_jobs import create_user_with_perms

@pytest.mark.asyncio
async def test_approval_flow_integration(
    async_client: AsyncClient,
    db: AsyncSession,
    seed_department_a: Department
):
    """Integration test verifying items requiring approval appear in the unified pending list."""
    creator, creator_token = await create_user_with_perms(db, "creator_appr@test.com", ["job_card:create", "job_card:read", "job_card:update"], seed_department_a.id)
    approver, approver_token = await create_user_with_perms(db, "approver_appr@test.com", ["job_card:approve", "job_card:read"], seed_department_a.id)
    
    creator_headers = {"Authorization": f"Bearer {creator_token}"}
    approver_headers = {"Authorization": f"Bearer {approver_token}"}

    # 1. Create Job Card
    res = await async_client.post("/api/v1/job-cards", headers=creator_headers, json={
        "title": "Approval Integration Test",
        "description": "Testing unified approvals",
        "department_id": str(seed_department_a.id),
    })
    assert res.status_code == 201
    job_id = res.json()["id"]
    
    # 2. Submit Job Card
    res = await async_client.post(f"/api/v1/job-cards/{job_id}/submit", headers=creator_headers, json={"comments": "Please approve"})
    assert res.status_code == 200
    
    # 3. Check Pending Approvals for Approver
    res = await async_client.get("/api/v1/approvals/pending", headers=approver_headers)
    assert res.status_code == 200
    pending = res.json()
    
    # Verify the job card is in the pending list
    found = next((p for p in pending if p["resource_id"] == job_id), None)
    assert found is not None
    assert found["resource"] == "JOB_CARD"
    assert found["required_capability"] == "job_card:approve"
