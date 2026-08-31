import pytest
import uuid
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.modules.iam.models import User, Department, Organization, Site, Location, Role, Permission, RolePermission, UserRole
from app.modules.fleet.models import Machine, MachineType
from app.modules.jobs.models import JobCard
from app.modules.work.models import WorkItem, WorkItemActionLog, WorkItemType, WorkItemStatus
from app.modules.work.schemas import WorkItemCreate, WorkItemTransition, WorkItemFollowUpCreate
from app.modules.work.service import WorkItemService
from app.core.security import get_password_hash


@pytest.mark.asyncio
async def test_create_all_work_item_types(db: AsyncSession):
    # Setup test org, site & dept
    org = Organization(name=f"Mining Corp WorkTest {uuid.uuid4().hex[:4]}", code=f"MCW-{uuid.uuid4().hex[:4]}", is_active=True)
    db.add(org)
    await db.commit()

    site = Site(name=f"Site {uuid.uuid4().hex[:4]}", code=f"ST-{uuid.uuid4().hex[:4]}", organization_id=org.id)
    db.add(site)
    await db.commit()

    dept = Department(name=f"Plant Maintenance {uuid.uuid4().hex[:4]}", code=f"PLT-{uuid.uuid4().hex[:4]}", site_id=site.id, sla_hours_default=24)
    db.add(dept)
    await db.commit()

    user = User(
        email=f"work_admin_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Work",
        last_name="Admin",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(user)
    await db.commit()

    types = ["JOB_CARD", "MAINTENANCE", "INSPECTION", "FOLLOW_UP", "OTHER"]
    created_items = []

    for wt in types:
        dto = WorkItemCreate(
            title=f"Test {wt} Work Unit",
            description=f"Automated test for {wt}",
            work_type=wt,
            department_id=dept.id,
            priority=2,
            type_specific_data={"custom_tag": f"TAG-{wt}"}
        )
        item = await WorkItemService.create_work_item(db, dto, user)
        assert item.id is not None
        assert item.work_type == wt
        assert item.status == "DRAFT"
        assert item.sla_hours > 0
        assert item.sla_due_at is not None
        created_items.append(item)

    # Verify prefixes
    assert created_items[0].reference_number.startswith("JC-")
    assert created_items[1].reference_number.startswith("PM-")
    assert created_items[2].reference_number.startswith("INS-")
    assert created_items[3].reference_number.startswith("FLW-")
    assert created_items[4].reference_number.startswith("WI-")


@pytest.mark.asyncio
async def test_type_specific_data_and_details(db: AsyncSession):
    org = Organization(name=f"Electro Power {uuid.uuid4().hex[:4]}", code=f"ELEC-PWR-{uuid.uuid4().hex[:4]}", is_active=True)
    db.add(org)
    await db.commit()

    dept = Department(name=f"Electrical Dept {uuid.uuid4().hex[:4]}", code=f"ELEC-{uuid.uuid4().hex[:4]}", sla_hours_default=12)
    db.add(dept)
    await db.commit()

    user = User(
        email=f"elec_lead_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Elec",
        last_name="Lead",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(user)
    await db.commit()

    inspection_payload = {
        "checklist": [
            {"item": "Voltage check 400V panel", "passed": True},
            {"item": "Transformer oil temperature", "value": "62C", "passed": True},
            {"item": "Emergency stop trip test", "passed": True}
        ],
        "calibration_standard": "ISO-9001-EL-44",
        "instrument_serial": "FLUKE-8846A"
    }

    dto = WorkItemCreate(
        title="Substation Weekly Diagnostic Inspection",
        description="Weekly electrical inspection on MCC Substation 2",
        work_type="INSPECTION",
        department_id=dept.id,
        priority=3, # Urgent
        type_specific_data=inspection_payload,
    )
    item = await WorkItemService.create_work_item(db, dto, user)
    
    # Retrieve detail response
    detail = await WorkItemService.get_work_item(db, item.id, user)
    assert detail.title == "Substation Weekly Diagnostic Inspection"
    assert detail.type_specific_data["calibration_standard"] == "ISO-9001-EL-44"
    assert len(detail.type_specific_data["checklist"]) == 3
    assert detail.sla_hours == 3.0  # 12.0 * 0.25 for Urgent tier


@pytest.mark.asyncio
async def test_status_transition_lifecycle_and_action_logs(db: AsyncSession):
    dept = Department(name=f"Mechanical Overhauls {uuid.uuid4().hex[:4]}", code=f"MECH-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    requester_user = User(
        email=f"mech_req_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Mech",
        last_name="Requester",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    approver_user = User(
        email=f"mech_approver_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Mech",
        last_name="Approver",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(requester_user)
    db.add(approver_user)
    await db.commit()

    dto = WorkItemCreate(
        title="Ball Mill Bearing Replacement",
        description="Replace worn SKF 23152 spherical roller bearing on Ball Mill 1",
        work_type="MAINTENANCE",
        department_id=dept.id,
        priority=2,
    )
    item = await WorkItemService.create_work_item(db, dto, requester_user)
    assert item.status == "DRAFT"

    # Step 1: Submit
    item = await WorkItemService.transition_status(db, item.id, WorkItemTransition(status="SUBMITTED", comments="Submitted for approval"), requester_user)
    assert item.status == "SUBMITTED"

    # Step 2: Approve (using independent approver user to satisfy SoD)
    item = await WorkItemService.transition_status(db, item.id, WorkItemTransition(status="APPROVED", comments="Approved by Lead"), approver_user)
    assert item.status == "APPROVED"
    assert item.approval_status == "APPROVED"
    assert item.approver_id == approver_user.id

    # Step 3: Assign
    item = await WorkItemService.transition_status(db, item.id, WorkItemTransition(status="ASSIGNED", comments="Assigned to mechanical team A"), approver_user)
    assert item.status == "ASSIGNED"

    # Step 4: In Progress (sets actual_start_time)
    item = await WorkItemService.transition_status(db, item.id, WorkItemTransition(status="IN_PROGRESS", comments="Started dismantling"), requester_user)
    assert item.status == "IN_PROGRESS"
    assert item.actual_start_time is not None

    # Step 5: Complete (sets actual_end_time and computes SLA)
    item = await WorkItemService.transition_status(
        db, item.id, WorkItemTransition(status="COMPLETED", actual_hours=5.5, actual_cost=1200.0, comments="Bearing fitted and greased"), requester_user
    )
    assert item.status == "COMPLETED"
    assert item.actual_end_time is not None
    assert item.actual_hours == 5.5
    assert item.actual_cost == 1200.0

    # Step 6: Verified & Closed
    item = await WorkItemService.transition_status(db, item.id, WorkItemTransition(status="VERIFIED", comments="Vibration analysis normal"), approver_user)
    assert item.status == "VERIFIED"

    item = await WorkItemService.transition_status(db, item.id, WorkItemTransition(status="CLOSED", comments="Work signed off"), approver_user)
    assert item.status == "CLOSED"

    # Verify action log audit trail
    detail = await WorkItemService.get_work_item(db, item.id, requester_user)
    assert len(detail.action_logs) >= 7


@pytest.mark.asyncio
async def test_follow_up_action_spawning(db: AsyncSession):
    dept = Department(name=f"Crushing Dept {uuid.uuid4().hex[:4]}", code=f"CRUSH-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    user = User(
        email=f"crush_tech_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Crush",
        last_name="Tech",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(user)
    await db.commit()

    # Create primary inspection
    ins_dto = WorkItemCreate(
        title="Primary Jaw Crusher Monthly Inspection",
        work_type="INSPECTION",
        department_id=dept.id,
        priority=1,
    )
    parent = await WorkItemService.create_work_item(db, ins_dto, user)

    # Spawn corrective follow-up action
    follow_up_dto = WorkItemFollowUpCreate(
        title="Replace Cracked Toggle Plate on Jaw Crusher",
        description="Severe hairline fracture observed on toggle plate seat during monthly inspection",
        work_type="FOLLOW_UP",
        priority=3,
        findings="Fracture width approx 2mm across center rib",
        corrective_actions="Procure new cast steel toggle plate and replace during Sunday shift shutdown"
    )
    child = await WorkItemService.create_follow_up(db, parent.id, follow_up_dto, user)

    assert child.id is not None
    assert child.work_type == "FOLLOW_UP"
    assert child.parent_work_item_id == parent.id
    assert child.reference_number.startswith("FLW-")
    assert child.type_specific_data["parent_reference"] == parent.reference_number
    assert child.type_specific_data["findings"] == "Fracture width approx 2mm across center rib"


@pytest.mark.asyncio
async def test_asset_and_location_hierarchy_linking(db: AsyncSession):
    org = Organization(name=f"Bikita Minerals WorkTest {uuid.uuid4().hex[:4]}", code=f"BIK-{uuid.uuid4().hex[:4]}", is_active=True)
    db.add(org)
    await db.commit()

    site = Site(name=f"Bikita Operations {uuid.uuid4().hex[:4]}", code=f"BIK-S-{uuid.uuid4().hex[:4]}", organization_id=org.id)
    db.add(site)
    await db.commit()

    facility = Location(name="Processing Plant", code=f"PP-{uuid.uuid4().hex[:4]}", location_type="FACILITY", site_id=site.id, hierarchy_level=1, breadcrumb="Bikita Operations / Processing Plant")
    db.add(facility)
    await db.commit()

    area = Location(name="Crushing Area", code=f"CR-{uuid.uuid4().hex[:4]}", location_type="AREA", site_id=site.id, parent_id=facility.id, hierarchy_level=2, breadcrumb="Bikita Operations / Processing Plant / Crushing Area")
    db.add(area)
    await db.commit()

    machine_type = MachineType(name=f"Heavy Excavator {uuid.uuid4().hex[:4]}", category="EARTHMOVING")
    db.add(machine_type)
    await db.commit()

    machine = Machine(
        identifier=f"CAT-349-{uuid.uuid4().hex[:4].upper()}",
        machine_type_id=machine_type.id,
        location="Crushing Area",
        location_id=area.id,
    )
    db.add(machine)
    await db.commit()

    dept = Department(name=f"Mining Operations {uuid.uuid4().hex[:4]}", code=f"MINE-{uuid.uuid4().hex[:4]}", site_id=site.id)
    db.add(dept)
    await db.commit()

    user = User(
        email=f"fleet_foreman_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Fleet",
        last_name="Foreman",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(user)
    await db.commit()

    dto = WorkItemCreate(
        title="500hr Hydraulic Service & Filter Change",
        work_type="MAINTENANCE",
        department_id=dept.id,
        location_id=area.id,
        machine_id=machine.id,
        priority=2,
    )
    item = await WorkItemService.create_work_item(db, dto, user)

    detail = await WorkItemService.get_work_item(db, item.id, user)
    assert detail.machine_identifier == machine.identifier
    assert detail.location_breadcrumb == "Bikita Operations / Processing Plant / Crushing Area"
    assert detail.department_name == dept.name


@pytest.mark.asyncio
async def test_job_card_sync_and_historical_migration(db: AsyncSession):
    dept = Department(name=f"Civil Works {uuid.uuid4().hex[:4]}", code=f"CIVIL-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    user = User(
        email=f"civil_eng_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Civil",
        last_name="Eng",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(user)
    await db.commit()

    # 1. Create a raw legacy JobCard directly
    job = JobCard(
        id=uuid.uuid4(),
        job_number=f"JC-2026-{uuid.uuid4().hex[:6].upper()}",
        title="Foundation Wall Reinforcement",
        description="Concrete crack repair on tailings foundation",
        status="DRAFT",
        priority=2,
        department_id=dept.id,
        creator_id=user.id,
    )
    db.add(job)
    await db.commit()

    # 2. Run historical migration utility
    migration_summary = await WorkItemService.migrate_historical_job_cards(db)
    assert migration_summary.scanned_job_cards >= 1
    assert migration_summary.created_work_items >= 1

    # 3. Verify created WorkItem matches JobCard
    res = await db.execute(select(WorkItem).where(WorkItem.job_card_id == job.id))
    work_item = res.scalar_one_or_none()
    assert work_item is not None
    assert work_item.reference_number == job.job_number
    assert work_item.title == "Foundation Wall Reinforcement"
    assert work_item.work_type == "JOB_CARD"
    assert work_item.status == "DRAFT"

    # 4. Update JobCard and test sync hook
    job.title = "Foundation Wall Reinforcement - Phase 2"
    job.status = "IN_PROGRESS"
    await WorkItemService.sync_job_card_to_work_item(db, job)

    await db.refresh(work_item)
    assert work_item.title == "Foundation Wall Reinforcement - Phase 2"
    assert work_item.status == "IN_PROGRESS"
