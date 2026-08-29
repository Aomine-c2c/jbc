import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from datetime import datetime, timedelta

from app.modules.iam.models import User, Role, Permission, UserRole, RolePermission, Department, Scope
from app.modules.fleet.models import MachineType, Machine, MachineRequisition
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
        is_superuser=True,  # Test helper user
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
    token = create_access_token(subject=str(user.id))
    return user, token


@pytest.mark.asyncio
async def test_multi_department_requisition_happy_path(async_client: AsyncClient, db: AsyncSession, seed_department_a: Department, seed_department_b: Department):
    """Verifies complete generic 12-stage requisition lifecycle with Job Card linking and multi-department support."""
    # Departments: Engineering (seed_department_a) and IT (seed_department_b)
    it_requester, it_token = await create_user_with_perms(db, "it_tech@bikita.com", ["requisition:create", "requisition:read"], seed_department_b.id)
    hod, hod_token = await create_user_with_perms(db, "hod@bikita.com", ["requisition:approve", "requisition:read"], seed_department_b.id)
    controller, controller_token = await create_user_with_perms(db, "fleet_controller@bikita.com", ["machines:manage", "requisition:approve", "requisition:read"], seed_department_a.id)

    it_headers = {"Authorization": f"Bearer {it_token}"}
    hod_headers = {"Authorization": f"Bearer {hod_token}"}
    ctrl_headers = {"Authorization": f"Bearer {controller_token}"}

    # Setup Machine Type & Specific Machine
    m_type = MachineType(
        id=uuid.uuid4(),
        name="Mobile Crane 50T",
        description="Heavy rough terrain telescopic mobile crane",
        category="Lifting Equipment",
        hourly_rate=120.0
    )
    db.add(m_type)
    await db.commit()

    crane = Machine(
        id=uuid.uuid4(),
        machine_type_id=m_type.id,
        identifier="CRANE-50T-01",
        serial_number="TEREX-2022-88",
        status="AVAILABLE",
        location="Shaft 01 Yard",
        capacity_rating="50 Tonne",
        current_hour_meter=1250.0
    )
    db.add(crane)

    # Setup Job Card to link to
    jc = JobCard(
        id=uuid.uuid4(),
        job_number="JC-2026-IT01",
        title="Install CCTV at High Mast Tower 4",
        department_id=seed_department_b.id,
        creator_id=it_requester.id,
        status="IN_PROGRESS"
    )
    db.add(jc)
    await db.commit()

    start_t = datetime.utcnow() + timedelta(hours=2)
    end_t = start_t + timedelta(hours=4)

    # 1. Create Requisition (DRAFT) - IT requesting Crane for high mast CCTV installation
    res = await async_client.post("/api/v1/fleet/requisitions", headers=it_headers, json={
        "machine_type_id": str(m_type.id),
        "department_id": str(seed_department_b.id),
        "collaborating_department_id": str(seed_department_a.id),
        "purpose": "Install high-resolution CCTV camera on 30m tower mast 4",
        "job_card_id": str(jc.id),
        "quantity": 1,
        "location": "Shaft 01 High Mast 4",
        "start_time": start_t.isoformat(),
        "end_time": end_t.isoformat(),
        "priority": 2,
        "operator_required": True,
        "special_requirements": "Man-basket attachment required",
        "safety_requirements": "Working at heights permit, Wind speed < 20 knots, Outrigger mats",
        "cost_centre": "CC-IT-901"
    })
    assert res.status_code == 201
    req_id = res.json()["id"]
    assert res.json()["status"] == "DRAFT"
    assert res.json()["requisition_number"].startswith("REQ-")
    assert res.json()["estimated_cost"] == 4.0 * 120.0  # 480.0

    # 2. Submit (DRAFT -> SUBMITTED)
    res = await async_client.post(f"/api/v1/fleet/requisitions/{req_id}/submit", headers=it_headers, json={
        "comments": "Submitting for departmental sign-off"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "SUBMITTED"

    # 3. Department Approval (SUBMITTED -> DEPARTMENT_APPROVAL)
    res = await async_client.post(f"/api/v1/fleet/requisitions/{req_id}/dept-approve", headers=hod_headers, json={
        "comments": "IT Department HOD approved necessity"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "DEPARTMENT_APPROVAL"

    # 4. Equipment Check (DEPARTMENT_APPROVAL -> EQUIPMENT_CHECK)
    res = await async_client.post(f"/api/v1/fleet/requisitions/{req_id}/equipment-check", headers=ctrl_headers, json={
        "machine_id": str(crane.id),
        "comments": "Crane 50T-01 inspected and available for window"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "EQUIPMENT_CHECK"

    # 5. Final Approval (EQUIPMENT_CHECK -> APPROVED)
    res = await async_client.post(f"/api/v1/fleet/requisitions/{req_id}/approve", headers=ctrl_headers, json={
        "comments": "Approved for dispatch scheduling"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "APPROVED"

    # 6. Schedule (APPROVED -> SCHEDULED)
    res = await async_client.post(f"/api/v1/fleet/requisitions/{req_id}/schedule", headers=ctrl_headers, json={
        "machine_id": str(crane.id),
        "operator_name": "Tendai Moyo (Certified Crane Operator)",
        "comments": "Scheduled on board for shift 1"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "SCHEDULED"

    # 7. Dispatch (SCHEDULED -> DISPATCHED)
    res = await async_client.post(f"/api/v1/fleet/requisitions/{req_id}/dispatch", headers=ctrl_headers, json={
        "start_hour_meter": 1250.0,
        "operator_name": "Tendai Moyo",
        "comments": "Dispatched to Shaft 01 High Mast 4"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "DISPATCHED"

    # 8. Start Use (DISPATCHED -> IN_USE)
    res = await async_client.post(f"/api/v1/fleet/requisitions/{req_id}/start-use", headers=it_headers, json={
        "comments": "Equipment arrived at site, rigging man-basket"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "IN_USE"

    # 9. Request Return (IN_USE -> RETURN_REQUESTED)
    res = await async_client.post(f"/api/v1/fleet/requisitions/{req_id}/request-return", headers=it_headers, json={
        "comments": "CCTV camera installed and tested. Ready for de-rigging"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "RETURN_REQUESTED"

    # 10. Return (RETURN_REQUESTED -> RETURNED)
    res = await async_client.post(f"/api/v1/fleet/requisitions/{req_id}/return", headers=ctrl_headers, json={
        "end_hour_meter": 1254.5,
        "comments": "Returned to central equipment yard"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "RETURNED"
    assert res.json()["actual_cost"] == 4.5 * 120.0  # 540.0

    # 11. Inspect (RETURNED -> INSPECTED)
    res = await async_client.post(f"/api/v1/fleet/requisitions/{req_id}/inspect", headers=ctrl_headers, json={
        "inspection_notes": "Outriggers and wire ropes inspected. No damage. Hour meter verified."
    })
    assert res.status_code == 200
    assert res.json()["status"] == "INSPECTED"

    # 12. Close (INSPECTED -> CLOSED)
    res = await async_client.post(f"/api/v1/fleet/requisitions/{req_id}/close", headers=ctrl_headers, json={
        "comments": "Requisition closed and billed to CC-IT-901"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "CLOSED"


@pytest.mark.asyncio
async def test_double_booking_prevention(async_client: AsyncClient, db: AsyncSession, seed_department_a: Department):
    """Verifies that scheduling the same machine for overlapping time windows strictly throws 409 Conflict."""
    controller, ctrl_token = await create_user_with_perms(db, "controller2@bikita.com", ["machines:manage", "requisition:create", "requisition:approve", "requisition:read"], seed_department_a.id)
    headers = {"Authorization": f"Bearer {ctrl_token}"}

    # Setup Machine Type & Machine
    m_type = MachineType(id=uuid.uuid4(), name="Excavator CAT 330", category="Earthmoving", hourly_rate=150.0)
    db.add(m_type)
    await db.commit()

    excavator = Machine(id=uuid.uuid4(), machine_type_id=m_type.id, identifier="EXCAV-01", status="AVAILABLE")
    db.add(excavator)
    await db.commit()

    base_time = datetime.utcnow() + timedelta(days=1)
    
    # 1. Create and schedule First Requisition from 08:00 to 12:00
    res1 = await async_client.post("/api/v1/fleet/requisitions", headers=headers, json={
        "machine_type_id": str(m_type.id),
        "department_id": str(seed_department_a.id),
        "purpose": "Trenching for Electrical Cable",
        "location": "South Waste Dump",
        "start_time": base_time.replace(hour=8, minute=0, second=0).isoformat(),
        "end_time": base_time.replace(hour=12, minute=0, second=0).isoformat(),
    })
    assert res1.status_code == 201
    req1_id = res1.json()["id"]
    
    await async_client.post(f"/api/v1/fleet/requisitions/{req1_id}/submit", headers=headers)
    await async_client.post(f"/api/v1/fleet/requisitions/{req1_id}/dept-approve", headers=headers)
    await async_client.post(f"/api/v1/fleet/requisitions/{req1_id}/equipment-check", headers=headers, json={"machine_id": str(excavator.id)})
    await async_client.post(f"/api/v1/fleet/requisitions/{req1_id}/approve", headers=headers, json={"comments": "Approved"})
    
    res_sched1 = await async_client.post(f"/api/v1/fleet/requisitions/{req1_id}/schedule", headers=headers, json={
        "machine_id": str(excavator.id),
        "operator_name": "Peter Dube"
    })
    assert res_sched1.status_code == 200
    assert res_sched1.json()["status"] == "SCHEDULED"

    # 2. Create Second Requisition attempting to book from 10:00 to 14:00 (Overlapping!)
    res2 = await async_client.post("/api/v1/fleet/requisitions", headers=headers, json={
        "machine_type_id": str(m_type.id),
        "department_id": str(seed_department_a.id),
        "purpose": "Civil Earthworks for Substation",
        "location": "North Substation",
        "start_time": base_time.replace(hour=10, minute=0, second=0).isoformat(),
        "end_time": base_time.replace(hour=14, minute=0, second=0).isoformat(),
    })
    assert res2.status_code == 201
    req2_id = res2.json()["id"]
    await async_client.post(f"/api/v1/fleet/requisitions/{req2_id}/submit", headers=headers)
    await async_client.post(f"/api/v1/fleet/requisitions/{req2_id}/dept-approve", headers=headers)
    await async_client.post(f"/api/v1/fleet/requisitions/{req2_id}/equipment-check", headers=headers)
    await async_client.post(f"/api/v1/fleet/requisitions/{req2_id}/approve", headers=headers, json={"comments": "Approved"})

    # 3. Attempting to schedule the conflicting slot must fail with 409 Conflict
    res_conflict = await async_client.post(f"/api/v1/fleet/requisitions/{req2_id}/schedule", headers=headers, json={
        "machine_id": str(excavator.id),
        "operator_name": "Simba Moyo"
    })
    assert res_conflict.status_code == 409
    assert "Double booking conflict" in res_conflict.json()["detail"]


@pytest.mark.asyncio
async def test_equipment_availability_telemetry(async_client: AsyncClient, db: AsyncSession, seed_department_a: Department):
    """Verifies that the visual availability endpoint returns live machine status and scheduled slots."""
    m_type = MachineType(id=uuid.uuid4(), name="Forklift 5T", category="Warehouse & Spares", hourly_rate=40.0)
    db.add(m_type)
    await db.commit()

    forklift = Machine(id=uuid.uuid4(), machine_type_id=m_type.id, identifier="FORK-05", status="AVAILABLE")
    db.add(forklift)
    await db.commit()

    res = await async_client.get(f"/api/v1/fleet/availability?machine_type_id={m_type.id}")
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 1
    assert items[0]["identifier"] == "FORK-05"
    assert items[0]["is_available_for_window"] is True
