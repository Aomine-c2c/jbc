import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from httpx import AsyncClient

from app.modules.iam.models import User, Department, Location
from app.modules.fleet.models import Machine, MachineType
from app.modules.work.models import WorkItem, WorkItemType
from app.modules.jobs.models import JobCard


@pytest.mark.asyncio
async def test_operator_clean_pre_start_inspection(
    async_client: AsyncClient,
    db,
    seed_user_a: User,
    token_user_a: str,
    seed_department_a: Department,
):
    # 1. Create a machine type and machine
    mtype = MachineType(
        id=uuid.uuid4(),
        name=f"Haul Truck Test {uuid.uuid4().hex[:6]}",
        category="Haulage",
    )
    db.add(mtype)
    await db.flush()

    machine = Machine(
        id=uuid.uuid4(),
        machine_type_id=mtype.id,
        identifier=f"CAT-777D-T-{uuid.uuid4().hex[:4]}",
        status="AVAILABLE",
        current_hour_meter=1200.0,
    )
    db.add(machine)
    await db.commit()
    await db.refresh(machine)

    # 2. Submit clean pre-start inspection
    payload = {
        "machine_id": str(machine.id),
        "hour_meter_reading": 1205.5,
        "operator_notes": "All green. Shift start walkaround completed.",
        "checklist_results": [
            {"category": "Fluids & Leaks", "item": "Engine Oil Level", "status": "PASS"},
            {"category": "Brakes & Steering", "item": "Service Brakes Response", "status": "PASS"},
            {"category": "Tires & Tracks", "item": "Tire Pressures & Cuts", "status": "PASS"},
            {"category": "Cab & Controls", "item": "Reversing Alarm & Horn", "status": "PASS"},
            {"category": "Emergency Systems", "item": "Fire Extinguisher & E-Stops", "status": "PASS"},
        ],
    }

    resp = await async_client.post(
        "/api/v1/work/pre-starts",
        json=payload,
        headers={"Authorization": f"Bearer {token_user_a}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["overall_status"] == "PASSED"
    assert data["is_grounded"] is False
    assert data["hour_meter_reading"] == 1205.5
    assert data["machine_status"] == "AVAILABLE"
    assert data["spawned_job_card_id"] is None

    # Verify machine record in DB
    await db.refresh(machine)
    assert machine.current_hour_meter == 1205.5
    assert machine.status == "AVAILABLE"


@pytest.mark.asyncio
async def test_operator_critical_defect_grounds_machine(
    async_client: AsyncClient,
    db,
    seed_user_a: User,
    token_user_a: str,
):
    mtype = MachineType(
        id=uuid.uuid4(),
        name=f"Excavator Test {uuid.uuid4().hex[:6]}",
        category="Excavation",
    )
    db.add(mtype)
    await db.flush()

    machine = Machine(
        id=uuid.uuid4(),
        machine_type_id=mtype.id,
        identifier=f"EXC-1250-T-{uuid.uuid4().hex[:4]}",
        status="AVAILABLE",
        current_hour_meter=3400.0,
    )
    db.add(machine)
    await db.commit()

    # Submit inspection with Critical Brakes failure
    payload = {
        "machine_id": str(machine.id),
        "hour_meter_reading": 3402.0,
        "operator_notes": "Brake pedal hits floor! Accumulator pressure low.",
        "checklist_results": [
            {"category": "Fluids & Leaks", "item": "Hydraulic Oil Level", "status": "PASS"},
            {"category": "Brakes & Steering", "item": "Service Brakes Response", "status": "CRITICAL_RED_TAG", "notes": "No pressure"},
            {"category": "Emergency Systems", "item": "E-Stop Operational", "status": "PASS"},
        ],
    }

    resp = await async_client.post(
        "/api/v1/work/pre-starts",
        json=payload,
        headers={"Authorization": f"Bearer {token_user_a}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["overall_status"] == "CRITICAL_RED_TAG"
    assert data["is_grounded"] is True
    assert data["machine_status"] == "OUT_OF_SERVICE"
    assert data["spawned_job_card_id"] is not None
    assert data["spawned_job_card_number"] is not None

    # Verify machine grounded in database
    await db.refresh(machine)
    assert machine.status == "OUT_OF_SERVICE"
    assert machine.current_hour_meter == 3402.0

    # Verify spawned job card
    jc = await db.execute(select(JobCard).where(JobCard.id == uuid.UUID(data["spawned_job_card_id"])))
    job = jc.scalar_one()
    assert job.priority == 4
    assert "CRITICAL RED-TAG DEFECT" in job.title
    assert "Service Brakes Response" in job.reported_issue


@pytest.mark.asyncio
async def test_operator_hour_meter_rollback_prevention(
    async_client: AsyncClient,
    db,
    seed_user_a: User,
    token_user_a: str,
):
    mtype = MachineType(
        id=uuid.uuid4(),
        name=f"Dozer Test {uuid.uuid4().hex[:6]}",
    )
    db.add(mtype)
    await db.flush()

    machine = Machine(
        id=uuid.uuid4(),
        machine_type_id=mtype.id,
        identifier=f"DZR-09-T-{uuid.uuid4().hex[:4]}",
        status="AVAILABLE",
        current_hour_meter=5000.0,
    )
    db.add(machine)
    await db.commit()

    # Attempt to submit with lower hour meter (e.g. 4800.0)
    payload = {
        "machine_id": str(machine.id),
        "hour_meter_reading": 4800.0,
        "checklist_results": [
            {"category": "Fluids & Leaks", "item": "Engine Oil", "status": "PASS"},
        ],
    }

    resp = await async_client.post(
        "/api/v1/work/pre-starts",
        json=payload,
        headers={"Authorization": f"Bearer {token_user_a}"},
    )
    assert resp.status_code == 400
    assert "cannot be less than current recorded hours" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_operator_minor_defect_and_listing(
    async_client: AsyncClient,
    db,
    seed_user_a: User,
    token_user_a: str,
):
    mtype = MachineType(
        id=uuid.uuid4(),
        name=f"FEL Test {uuid.uuid4().hex[:6]}",
    )
    db.add(mtype)
    await db.flush()

    machine = Machine(
        id=uuid.uuid4(),
        machine_type_id=mtype.id,
        identifier=f"CAT-988K-T-{uuid.uuid4().hex[:4]}",
        status="AVAILABLE",
        current_hour_meter=800.0,
    )
    db.add(machine)
    await db.commit()

    # Minor defect: Right wiper blade split
    payload = {
        "machine_id": str(machine.id),
        "hour_meter_reading": 805.0,
        "operator_notes": "Right wiper blade rubber torn. Does not impair primary visibility.",
        "checklist_results": [
            {"category": "Cab & Controls", "item": "Wipers & Washer", "status": "MINOR_DEFECT", "notes": "Rubber split"},
            {"category": "Brakes & Steering", "item": "Service Brakes", "status": "PASS"},
        ],
    }

    resp = await async_client.post(
        "/api/v1/work/pre-starts",
        json=payload,
        headers={"Authorization": f"Bearer {token_user_a}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["overall_status"] == "DEFECTS_NOTED"
    assert data["is_grounded"] is False
    assert data["machine_status"] == "AVAILABLE"

    # Test listing endpoint
    list_resp = await async_client.get(
        f"/api/v1/work/pre-starts?machine_id={machine.id}",
        headers={"Authorization": f"Bearer {token_user_a}"},
    )
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) >= 1
    assert items[0]["machine_name"] == machine.identifier
    assert items[0]["overall_status"] == "DEFECTS_NOTED"

