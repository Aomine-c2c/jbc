import pytest
import uuid
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.iam.models import User, Department
from app.modules.jobs.models import JobCard
from app.modules.jobs.service import JobCardService
from app.modules.jobs.schemas import JobCardApprove, JobCardStart, JobCardComplete, JobCardVerify, JobCardClose, JobCardSubmit
from app.modules.fleet.service import FleetService
from app.modules.fleet.schemas import (
    RequisitionCreate, RequisitionSubmit, RequisitionApprove, RequisitionReject,
    RequisitionReturn
)
from app.modules.fleet.models import MachineRequisition, MachineReservation, Machine
from app.modules.common.sms_provider import MockSMSProvider, get_sms_provider
from app.modules.common.models import SMSMessage
from app.modules.common.notifications import NotificationService
from app.worker import _send_sms_async
from app.core.security import create_access_token, get_password_hash
from fastapi import HTTPException
import random


@pytest.mark.asyncio
async def test_role_escalation_blocked(async_client: AsyncClient, token_user_a):
    response = await async_client.post("/api/v1/iam/users", headers={"Authorization": f"Bearer {token_user_a}"}, json={
        "email": "hacker@test.com",
        "first_name": "Hacker",
        "last_name": "Man",
        "password": "Password123!",
        "department_id": None
    })
    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough privileges"


@pytest.mark.asyncio
async def test_cross_department_isolation(async_client: AsyncClient, token_user_a, seed_department_b, db: AsyncSession):
    from app.core.authz import AuthzGuard
    fake_user = User(id=uuid.uuid4(), department_id=uuid.uuid4())
    with pytest.raises(HTTPException) as exc:
        result = AuthzGuard.check_permission(fake_user, "jobs:read", {"jobs:read": ["DEPARTMENT"]}, resource_dept_id=seed_department_b.id)
        if not result:
            raise HTTPException(status_code=403, detail="Forbidden")
    assert exc.value.status_code == 403
    assert AuthzGuard.check_permission(fake_user, "jobs:read", {"jobs:read": ["GLOBAL"]}, resource_dept_id=seed_department_b.id) == True


@pytest.mark.asyncio
async def test_resource_id_manipulation(async_client: AsyncClient, token_user_a, db: AsyncSession):
    job = JobCard(
        id=uuid.uuid4(),
        title="Test",
        creator_id=uuid.uuid4(),
        department_id=uuid.uuid4(),
        status="DRAFT",
    )
    db.add(job)
    await db.commit()
    from app.core.authz import AuthzGuard
    fake_user = User(id=uuid.uuid4())
    with pytest.raises(HTTPException) as exc:
        result = AuthzGuard.check_permission(fake_user, "jobs:update", {"jobs:update": ["OWN"]}, resource_owner_id=job.creator_id)
        if not result:
            raise HTTPException(status_code=403, detail="Forbidden")
    assert exc.value.status_code == 403
    assert AuthzGuard.check_permission(fake_user, "jobs:update", {"global_override": []}, resource_owner_id=job.creator_id) == True


@pytest.mark.asyncio
async def test_separation_of_duties(async_client: AsyncClient, seed_user_a, token_user_a, db: AsyncSession):
    job = JobCard(
        id=uuid.uuid4(),
        title="Test Job",
        creator_id=seed_user_a.id,
        department_id=seed_user_a.department_id,
        status="PENDING_APPROVAL",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    with pytest.raises(HTTPException) as exc:
        await JobCardService.approve(db, job.id, JobCardApprove(comments="Approving my own work"), seed_user_a)
    assert exc.value.status_code == 409
    assert "Separation of Duties" in exc.value.detail


@pytest.mark.asyncio
async def test_unauthorized_machine_dispatch(async_client: AsyncClient, seed_user_a, db: AsyncSession):
    # Create a machine type and machine first
    from app.modules.fleet.models import MachineType
    mt = MachineType(id=uuid.uuid4(), name="Test Machine")
    db.add(mt)
    await db.commit()

    m = Machine(id=uuid.uuid4(), machine_type_id=mt.id, identifier="M-001")
    db.add(m)
    await db.commit()

    # Create a requisition in RESERVED state
    req = MachineRequisition(
        id=uuid.uuid4(),
        machine_type_id=mt.id,
        requester_id=uuid.uuid4(),
        department_id=uuid.uuid4(),
        purpose="Test Purpose",
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=2),
        status="RESERVED",
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)

    # Create reservation
    res = MachineReservation(
        id=uuid.uuid4(),
        requisition_id=req.id,
        machine_id=m.id,
        reservation_status="RESERVED",
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=2),
    )
    db.add(res)
    await db.commit()
    await db.refresh(res)

    # User without dispatch permission tries to dispatch
    token = create_access_token(subject=str(seed_user_a.id))
    response = await async_client.post(f"/api/v1/fleet/requisitions/{req.id}/dispatch", headers={"Authorization": f"Bearer {token}"}, json={
        "start_hours": 1000,
    })
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_invalid_workflow_transition(async_client: AsyncClient, seed_user_a, db: AsyncSession):
    job = JobCard(
        id=uuid.uuid4(),
        title="Test Job",
        creator_id=seed_user_a.id,
        department_id=seed_user_a.department_id,
        status="DRAFT",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    with pytest.raises(HTTPException) as exc:
        await JobCardService.start(db, job.id, JobCardStart(comments=""), seed_user_a)
    assert exc.value.status_code == 409
    assert "Cannot start job card from state DRAFT" in exc.value.detail


@pytest.mark.asyncio
async def test_refresh_token_rejected_as_access_token(async_client: AsyncClient, seed_user_a):
    from app.core.security import create_refresh_token
    refresh_token = create_refresh_token(subject=str(seed_user_a.id))
    response = await async_client.get(
        "/api/v1/iam/users/me",
        headers={"Authorization": f"Bearer {refresh_token}"}
    )
    assert response.status_code == 401
    assert "Refresh tokens cannot be used as access tokens" in response.json()["detail"]


@pytest.mark.asyncio
async def test_csrf_protection_for_cookie_auth(async_client: AsyncClient, seed_user_a):
    access_token = create_access_token(subject=str(seed_user_a.id))
    # 1. Missing both cookie and header for cookie-authenticated mutation
    res_no_csrf = await async_client.post(
        "/api/v1/jobs",
        cookies={"dwrms_access_token": access_token},
        json={"title": "Unauthorized CSRF Job", "department_id": str(seed_user_a.department_id)}
    )
    assert res_no_csrf.status_code == 403

    # 2. Header present, but cookie missing (spoof attempt)
    res_spoof = await async_client.post(
        "/api/v1/jobs",
        cookies={"dwrms_access_token": access_token},
        headers={"X-CSRF-Token": "attacker_supplied_token"},
        json={"title": "Unauthorized CSRF Job", "department_id": str(seed_user_a.department_id)}
    )
    assert res_spoof.status_code == 403

    # 3. Both cookie and header present but mismatched
    res_mismatch = await async_client.post(
        "/api/v1/jobs",
        cookies={"dwrms_access_token": access_token, "dwrms_csrf_token": "valid_cookie_token"},
        headers={"X-CSRF-Token": "different_header_token"},
        json={"title": "Unauthorized CSRF Job", "department_id": str(seed_user_a.department_id)}
    )
    assert res_mismatch.status_code == 403


@pytest.mark.asyncio
async def test_security_headers_present(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

