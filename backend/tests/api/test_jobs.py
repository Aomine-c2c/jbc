import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from datetime import datetime

from app.modules.iam.models import User, Role, Permission, UserRole, RolePermission, Department, Scope
from app.modules.jobs.models import JobCard
from app.core.security import create_access_token, get_password_hash


async def create_user_with_perms(db: AsyncSession, email: str, perms: list[str], dept_id: uuid.UUID) -> tuple[User, str]:
    user = User(
        id=uuid.uuid4(),
        email=email,
        first_name="Test",
        last_name="User",
        hashed_password=get_password_hash("password123"),
        department_id=dept_id,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    role = Role(id=uuid.uuid4(), name=f"Role_{uuid.uuid4().hex[:8]}", description="Test Role")
    db.add(role)
    await db.commit()
    await db.refresh(role)

    db.add(UserRole(user_id=user.id, role_id=role.id))

    for p_name in perms:
        res = await db.execute(select(Permission).where(Permission.name == p_name))
        perm = res.scalar_one_or_none()
        if not perm:
            perm = Permission(id=uuid.uuid4(), name=p_name, description=p_name)
            db.add(perm)
            await db.commit()
            await db.refresh(perm)
        db.add(RolePermission(role_id=role.id, permission_id=perm.id, scope=Scope.GLOBAL))

    await db.commit()
    user_id = str(user.id)
    db.expunge(user)
    token = create_access_token(subject=user_id)
    return user, token


@pytest.mark.asyncio
async def test_job_card_happy_path(async_client: AsyncClient, db: AsyncSession, seed_department_a: Department):
    """Verifies a full valid lifecycle DRAFT -> SUBMITTED -> APPROVED -> ASSIGNED -> IN_PROGRESS -> COMPLETED -> VERIFIED -> CLOSED"""
    creator, creator_token = await create_user_with_perms(db, "creator@test.com", ["job_card:create", "job_card:read", "job_card:update"], seed_department_a.id)
    approver, approver_token = await create_user_with_perms(db, "approver@test.com", ["job_card:approve", "job_card:read"], seed_department_a.id)
    supervisor, supervisor_token = await create_user_with_perms(db, "supervisor@test.com", ["job_card:update", "job_card:verify", "job_card:read"], seed_department_a.id)
    tech, tech_token = await create_user_with_perms(db, "tech@test.com", ["job_card:update", "job_card:read"], seed_department_a.id)

    creator_headers = {"Authorization": f"Bearer {creator_token}"}
    approver_headers = {"Authorization": f"Bearer {approver_token}"}
    supervisor_headers = {"Authorization": f"Bearer {supervisor_token}"}
    tech_headers = {"Authorization": f"Bearer {tech_token}"}

    # 1. Create (DRAFT)
    res = await async_client.post("/api/v1/job-cards", headers=creator_headers, json={
        "title": "Fix Crusher Jaw",
        "description": "Crusher jaw plate worn out",
        "department_id": str(seed_department_a.id),
        "job_type": "Corrective Maintenance",
        "workshop_code": "WS-MECH-01",
        "location": "Shaft 01 Level 4",
        "plant_area": "Crushing Section",
        "estimated_hours": 4.0,
        "estimated_cost": 1250.0,
    })
    assert res.status_code == 201
    job_id = res.json()["id"]
    assert res.json()["status"] == "DRAFT"
    assert res.json()["job_number"].startswith("JC-")

    # 2. Submit (DRAFT -> SUBMITTED)
    res = await async_client.post(f"/api/v1/job-cards/{job_id}/submit", headers=creator_headers, json={"comments": "Ready for approval"})
    assert res.status_code == 200
    assert res.json()["status"] in ["SUBMITTED", "PENDING_APPROVAL"]

    # 3. Separation of Duties Check: Creator cannot approve own job card
    res_bad = await async_client.post(f"/api/v1/job-cards/{job_id}/approve", headers=creator_headers, json={"comments": "Self approval"})
    assert res_bad.status_code in [403, 409]

    # Approver approves (SUBMITTED -> APPROVED)
    res = await async_client.post(f"/api/v1/job-cards/{job_id}/approve", headers=approver_headers, json={"comments": "Approved for execution"})
    assert res.status_code == 200
    assert res.json()["status"] == "APPROVED"

    # 4. Plan (APPROVED -> PLANNING)
    res = await async_client.post(f"/api/v1/job-cards/{job_id}/plan", headers=supervisor_headers, json={
        "estimated_hours": 5.0,
        "estimated_cost": 1500.0,
        "job_instruction": "Lockout CB-01 before work",
        "comments": "Planned for shift 2"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "PLANNING"

    # 5. Assign (PLANNING -> ASSIGNED)
    res = await async_client.post(f"/api/v1/job-cards/{job_id}/assign", headers=supervisor_headers, json={
        "supervisor_id": str(supervisor.id),
        "assigned_personnel": "John Doe (Fitter), Jane Smith (Boilermaker)",
        "comments": "Assigned to mechanical team"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "ASSIGNED"

    # 6. Start (ASSIGNED -> IN_PROGRESS)
    res = await async_client.post(f"/api/v1/job-cards/{job_id}/start", headers=tech_headers, json={
        "actual_start_time": datetime.utcnow().isoformat(),
        "comments": "Started work on crusher jaw plate"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "IN_PROGRESS"

    # 7. Pause (IN_PROGRESS -> ON_HOLD)
    res = await async_client.post(f"/api/v1/job-cards/{job_id}/hold", headers=tech_headers, json={
        "reason": "Waiting for crane availability",
        "comments": "Crane currently allocated to Shaft 2"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "ON_HOLD"

    # 8. Resume (ON_HOLD -> IN_PROGRESS)
    res = await async_client.post(f"/api/v1/job-cards/{job_id}/start", headers=tech_headers, json={
        "comments": "Crane arrived, resuming replacement"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "IN_PROGRESS"

    # 9. Complete (IN_PROGRESS -> COMPLETED) with structured labor and spares
    res = await async_client.post(f"/api/v1/job-cards/{job_id}/complete", headers=tech_headers, json={
        "action_taken": "Replaced worn jaw plate, torqued wedge bolts to 450Nm, test ran empty.",
        "downtime_hours": 4.5,
        "labour_entries": [
            {"technician_name": "John Doe", "trade": "Mechanical Fitter", "hours_spent": 4.5, "hourly_rate": 30.0},
            {"technician_name": "Jane Smith", "trade": "Rigger", "hours_spent": 2.0, "hourly_rate": 25.0}
        ],
        "parts_used": [
            {"part_name": "Crusher Fixed Jaw Plate", "part_number": "CJ-500-01", "quantity": 1, "unit_cost": 850.0, "is_material": False},
            {"part_name": "Anti-Seize Grease & Shims", "part_number": "CHEM-09", "quantity": 2, "unit_cost": 45.0, "is_material": True}
        ],
        "completion_notes": "Equipment ready for trial run.",
        "comments": "Work complete"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "COMPLETED"
    
    # Verify auto-calculated metrics
    calc = res.json()["calculations"]
    assert calc["total_labour_hours"] == 6.5
    assert calc["total_labour_cost"] == (4.5 * 30.0) + (2.0 * 25.0)  # 135 + 50 = 185
    assert calc["total_spares_cost"] == 850.0
    assert calc["total_materials_cost"] == 90.0
    assert calc["total_material_cost"] == 940.0
    assert calc["total_actual_cost"] == 185.0 + 940.0  # 1125.0

    # 10. QA Verify (COMPLETED -> VERIFIED)
    res = await async_client.post(f"/api/v1/job-cards/{job_id}/verify", headers=supervisor_headers, json={
        "comments": "QA verified: Torque check passed, alignment within 0.05mm tolerance"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "VERIFIED"

    # 11. Requester Handover Confirmation
    res = await async_client.post(f"/api/v1/job-cards/{job_id}/confirm", headers=creator_headers, json={
        "requester_confirmed": True,
        "requester_notes": "Trial run completed under load. Throughput normal.",
        "comments": "Signed off by production supervisor"
    })
    assert res.status_code == 200

    # 12. Close & Archive (VERIFIED -> CLOSED)
    res = await async_client.post(f"/api/v1/job-cards/{job_id}/close", headers=supervisor_headers, json={
        "comments": "Job closed and archived into maintenance history."
    })
    assert res.status_code == 200
    assert res.json()["status"] == "CLOSED"

    # 13. Verify Execution Events were tracked
    res_get = await async_client.get(f"/api/v1/job-cards/{job_id}", headers=supervisor_headers)
    events = [e["event_type"] for e in res_get.json()["execution_events"]]
    assert "REQUESTED" in events
    assert "APPROVED" in events
    assert "ASSIGNED" in events
    assert "STARTED" in events
    assert "PAUSED" in events
    assert "RESUMED" in events
    assert "COMPLETED" in events
    assert "SUPERVISOR_APPROVED" in events
    assert "CLOSED" in events


@pytest.mark.asyncio
async def test_controlled_amendment_with_audit(async_client: AsyncClient, db: AsyncSession, seed_department_a: Department):
    """Verifies that controlled amendments update target field and create immutable audit logs."""
    supervisor, supervisor_token = await create_user_with_perms(db, "sup_amend@test.com", ["job_card:create", "job_card:update", "job_card:read"], seed_department_a.id)
    headers = {"Authorization": f"Bearer {supervisor_token}"}

    # Create job
    res = await async_client.post("/api/v1/job-cards", headers=headers, json={
        "title": "Conveyor Belt Lacing",
        "description": "Splice belt",
        "department_id": str(seed_department_a.id),
        "estimated_cost": 500.0,
    })
    job_id = res.json()["id"]

    # Submit controlled amendment
    res_amend = await async_client.post(f"/api/v1/job-cards/{job_id}/amend", headers=headers, json={
        "field_name": "estimated_cost",
        "new_value": "750.0",
        "amendment_reason": "Price adjustment due to upgraded vulcanized splice kit requirement"
    })
    assert res_amend.status_code == 200
    assert res_amend.json()["estimated_cost"] == 750.0
    assert len(res_amend.json()["amendments"]) == 1
    assert res_amend.json()["amendments"][0]["amendment_reason"] == "Price adjustment due to upgraded vulcanized splice kit requirement"


@pytest.mark.asyncio
async def test_invalid_state_transition(async_client: AsyncClient, db: AsyncSession, seed_department_a: Department):
    """Verifies that invalid state transitions throw 409 Conflict"""
    supervisor, supervisor_token = await create_user_with_perms(db, "sup_invalid@test.com", ["job_card:create", "job_card:verify", "job_card:read", "job_card:update"], seed_department_a.id)
    headers = {"Authorization": f"Bearer {supervisor_token}"}

    # Create job in DRAFT
    res = await async_client.post("/api/v1/job-cards", headers=headers, json={
        "title": "Invalid Transition Test",
        "description": "Testing invalid transition",
        "department_id": str(seed_department_a.id)
    })
    assert res.status_code == 201
    job_id = res.json()["id"]

    # Try to verify a DRAFT job card directly (Invalid transition)
    res_invalid = await async_client.post(f"/api/v1/job-cards/{job_id}/verify", headers=headers, json={
        "comments": "Invalid direct jump to verify"
    })
    assert res_invalid.status_code == 409


@pytest.mark.asyncio
async def test_rework_transition(async_client: AsyncClient, db: AsyncSession, seed_department_a: Department):
    """Verifies that COMPLETED can go back to IN_PROGRESS via start (rework)"""
    tech, tech_token = await create_user_with_perms(db, "tech_rework@test.com", ["job_card:create", "job_card:update", "job_card:read", "job_card:approve"], seed_department_a.id)
    headers = {"Authorization": f"Bearer {tech_token}"}

    # Create & advance to COMPLETED
    job = JobCard(
        job_number=f"JC-TEST-{uuid.uuid4().hex[:4].upper()}",
        title="Rework Test Job",
        description="Testing rework",
        department_id=seed_department_a.id,
        creator_id=tech.id,
        status="COMPLETED"
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Transition COMPLETED -> IN_PROGRESS via start
    res = await async_client.post(f"/api/v1/job-cards/{job.id}/start", headers=headers, json={
        "actual_start_time": datetime.utcnow().isoformat(),
        "comments": "Reworking the seal after inspection"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "IN_PROGRESS"
