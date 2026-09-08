import pytest
import uuid
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient

from app.modules.iam.models import User, Department
from app.modules.fleet.models import Machine, MachineType, MachineRequisition
from app.modules.jobs.models import JobCard


@pytest.mark.asyncio
async def test_get_machine_details_and_filtered_tabs(
    async_client: AsyncClient,
    db,
    seed_user_a: User,
    token_user_a: str,
    seed_department_a: Department,
):
    # 1. Create a machine type and machine
    mtype = MachineType(
        id=uuid.uuid4(),
        name=f"Excavator Pro {uuid.uuid4().hex[:6]}",
        category="Excavation",
        hourly_rate=120.0,
    )
    db.add(mtype)
    await db.flush()

    machine = Machine(
        id=uuid.uuid4(),
        machine_type_id=mtype.id,
        identifier=f"EX-800-{uuid.uuid4().hex[:4]}",
        serial_number="SN-EX800-TEST-99",
        status="AVAILABLE",
        capacity_rating="45 Tonnes",
        location="Open Pit Bench 3",
        current_hour_meter=3450.5,
    )
    db.add(machine)
    await db.flush()

    # 2. Create a requisition linked to this machine
    now = datetime.now(timezone.utc)
    req = MachineRequisition(
        id=uuid.uuid4(),
        requisition_number=f"REQ-{uuid.uuid4().hex[:6].upper()}",
        department_id=seed_department_a.id,
        requester_id=seed_user_a.id,
        purpose="Open pit waste stripping",
        machine_type_id=mtype.id,
        machine_id=machine.id,
        quantity=1,
        start_time=now,
        end_time=now + timedelta(hours=8),
        status="ALLOCATED",
    )
    db.add(req)

    # 3. Create a job card linked to this machine
    jc = JobCard(
        id=uuid.uuid4(),
        job_number=f"JC-{uuid.uuid4().hex[:6].upper()}",
        title=f"500h Periodic Service - {machine.identifier}",
        department_id=seed_department_a.id,
        creator_id=seed_user_a.id,
        machine_id=machine.id,
        priority=2,
        status="IN_PROGRESS",
    )
    db.add(jc)
    await db.commit()

    # 4. Verify GET /api/v1/fleet/machines/{id}
    res_m = await async_client.get(
        f"/api/v1/fleet/machines/{machine.id}",
        headers={"Authorization": f"Bearer {token_user_a}"},
    )
    assert res_m.status_code == 200, res_m.text
    data_m = res_m.json()
    assert data_m["identifier"] == machine.identifier
    assert data_m["serial_number"] == "SN-EX800-TEST-99"
    assert data_m["current_hour_meter"] == 3450.5
    assert data_m["capacity_rating"] == "45 Tonnes"
    assert data_m["machine_type"]["name"] == mtype.name

    # 5. Verify GET /api/v1/fleet/requisitions?machine_id={id}
    res_req = await async_client.get(
        f"/api/v1/fleet/requisitions?machine_id={machine.id}",
        headers={"Authorization": f"Bearer {token_user_a}"},
    )
    assert res_req.status_code == 200, res_req.text
    req_list = res_req.json()
    assert len(req_list) >= 1
    assert any(r["id"] == str(req.id) for r in req_list)

    # 6. Verify GET /api/v1/job-cards?machine_id={id}
    res_jc = await async_client.get(
        f"/api/v1/job-cards?machine_id={machine.id}",
        headers={"Authorization": f"Bearer {token_user_a}"},
    )
    assert res_jc.status_code == 200, res_jc.text
    jc_list = res_jc.json()
    assert len(jc_list) >= 1
    assert any(j["id"] == str(jc.id) for j in jc_list)
