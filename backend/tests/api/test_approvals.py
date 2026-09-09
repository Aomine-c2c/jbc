import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.approvals.models import ApprovalRequest, ApprovalStep
from app.modules.fleet.models import MachineRequisition, MachineType
from app.modules.iam.models import Department
from tests.api.test_jobs import create_user_with_perms

pytestmark = pytest.mark.asyncio


async def test_get_pending_approvals_empty(
    async_client: AsyncClient,
    token_user_a: str,
):
    """Test that a user has no pending approvals by default."""
    response = await async_client.get(
        "/api/v1/approvals/pending",
        headers={"Authorization": f"Bearer {token_user_a}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_get_pending_approvals_user_b(
    async_client: AsyncClient,
    token_user_b: str,
):
    """Test that user_b can get pending approvals."""
    response = await async_client.get(
        "/api/v1/approvals/pending",
        headers={"Authorization": f"Bearer {token_user_b}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_approval_flow_integration(
    async_client: AsyncClient,
    db: AsyncSession,
    seed_department_a: Department,
):
    """Integration test verifying items requiring approval appear in the unified pending list."""
    creator, creator_token = await create_user_with_perms(
        db,
        "creator_appr@test.com",
        ["job_card:create", "job_card:read", "job_card:update"],
        seed_department_a.id,
    )
    approver, approver_token = await create_user_with_perms(
        db,
        "approver_appr@test.com",
        ["job_card:approve", "job_card:read"],
        seed_department_a.id,
    )

    creator_headers = {"Authorization": f"Bearer {creator_token}"}
    approver_headers = {"Authorization": f"Bearer {approver_token}"}

    # 1. Create Job Card
    res = await async_client.post(
        "/api/v1/job-cards",
        headers=creator_headers,
        json={
            "title": "Approval Integration Test",
            "description": "Testing unified approvals",
            "department_id": str(seed_department_a.id),
        },
    )
    assert res.status_code == 201
    job_id = res.json()["id"]

    # 2. Submit Job Card
    res = await async_client.post(
        f"/api/v1/job-cards/{job_id}/submit",
        headers=creator_headers,
        json={"comments": "Please approve"},
    )
    assert res.status_code == 200

    # 3. Check Pending Approvals for Approver
    res = await async_client.get("/api/v1/approvals/pending", headers=approver_headers)
    assert res.status_code == 200
    pending = res.json()

    # Verify the job card is in the pending list
    found = next((p for p in pending if p["approval_request"]["resource_id"] == job_id), None)
    assert found is not None
    assert found["approval_request"]["resource_type"] == "JOB_CARD"
    assert found["pending_step"]["required_permission"] == "job_card:approve"


async def test_machine_requisition_pending_approval_display(
    async_client: AsyncClient,
    db: AsyncSession,
    seed_department_a: Department,
):
    """Test that MachineRequisition pending approvals query requester and department without error."""
    user_a, _ = await create_user_with_perms(db, "mr_creator@test.com", ["requisition:create"], seed_department_a.id)
    approver, approver_token = await create_user_with_perms(
        db, "mr_approver@test.com", ["requisition:approve"], seed_department_a.id
    )

    mtype = MachineType(
        id=uuid.uuid4(),
        name=f"Excavator {uuid.uuid4().hex[:6]}",
        description="Heavy earth moving machine",
    )
    db.add(mtype)
    await db.flush()

    mr = MachineRequisition(
        id=uuid.uuid4(),
        requisition_number="REQ-2026-001",
        department_id=seed_department_a.id,
        requester_id=user_a.id,
        machine_type_id=mtype.id,
        purpose="Open pit bench excavation",
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc) + timedelta(hours=8),
        status="DEPARTMENT_APPROVAL",
    )
    db.add(mr)
    await db.flush()

    app_req = ApprovalRequest(
        id=uuid.uuid4(),
        resource_type="machine_requisition",
        resource_id=mr.id,
        status="OPEN",
        priority=1,
        created_by_id=user_a.id,
    )
    db.add(app_req)
    await db.flush()

    app_step = ApprovalStep(
        id=uuid.uuid4(),
        approval_request_id=app_req.id,
        step_number=1,
        authority_role="Supervisor",
        required_permission="requisition:approve",
        status="PENDING",
    )
    db.add(app_step)
    await db.commit()

    res = await async_client.get(
        "/api/v1/approvals/pending",
        headers={"Authorization": f"Bearer {approver_token}"},
    )
    assert res.status_code == 200
    pending = res.json()
    found = next((item for item in pending if item["approval_request"]["resource_id"] == str(mr.id)), None)
    assert found is not None
    assert found["resource_title"] == "Machine Requisition REQ-2026-001"
    assert found["resource_description"] == "Open pit bench excavation"
    assert found["department_name"] == seed_department_a.name
    assert user_a.first_name in found["requester_name"]
