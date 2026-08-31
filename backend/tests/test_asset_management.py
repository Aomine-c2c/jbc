import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.modules.iam.models import User, Department, Organization, Site, Location
from app.modules.fleet.models import Machine, MachineType
from app.modules.work.models import WorkItem
from app.modules.assets.models import Asset, AssetActivityLog, AssetMaintenanceRecord, AssetType, AssetStatus
from app.modules.assets.schemas import (
    AssetCreate,
    AssetUpdate,
    AssetStatusTransition,
    AssetMaintenanceCreate,
    AssetArchiveRequest,
)
from app.modules.assets.service import AssetService
from app.core.security import get_password_hash


@pytest.mark.asyncio
async def test_create_all_asset_types_and_tags(db: AsyncSession):
    org = Organization(name=f"Asset Test Org {uuid.uuid4().hex[:4]}", code=f"AST-ORG-{uuid.uuid4().hex[:4]}", is_active=True)
    db.add(org)
    await db.commit()

    site = Site(name=f"Site Alpha {uuid.uuid4().hex[:4]}", code=f"ST-{uuid.uuid4().hex[:4]}", organization_id=org.id)
    db.add(site)
    await db.commit()

    dept = Department(name=f"Asset Management Dept {uuid.uuid4().hex[:4]}", code=f"AST-D-{uuid.uuid4().hex[:4]}", site_id=site.id)
    db.add(dept)
    await db.commit()

    user = User(
        email=f"asset_admin_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Asset",
        last_name="Manager",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(user)
    await db.commit()

    types = ["MACHINE", "VEHICLE", "TOOL", "INFRASTRUCTURE", "IT_EQUIPMENT", "PRODUCTION_EQUIPMENT", "EQUIPMENT"]
    created_assets = []

    for t in types:
        dto = AssetCreate(
            name=f"Test {t} Asset Unit",
            asset_type=t,
            category=f"Category {t}",
            manufacturer="ABB Corp",
            model_number="MD-200",
            serial_number=f"SN-{uuid.uuid4().hex[:8].upper()}",
            department_id=dept.id,
            status="AVAILABLE",
            criticality="HIGH",
            purchase_cost=15000.0,
        )
        asset = await AssetService.create_asset(db, dto, user)
        assert asset.id is not None
        assert asset.asset_type == t
        assert asset.status == "AVAILABLE"
        created_assets.append(asset)

    # Verify generated tag prefixes
    assert created_assets[0].asset_tag.startswith("MCH-")
    assert created_assets[1].asset_tag.startswith("VEH-")
    assert created_assets[2].asset_tag.startswith("TOL-")
    assert created_assets[3].asset_tag.startswith("INF-")
    assert created_assets[4].asset_tag.startswith("IT-")
    assert created_assets[5].asset_tag.startswith("PRD-")
    assert created_assets[6].asset_tag.startswith("AST-")


@pytest.mark.asyncio
async def test_asset_status_transitions_and_history(db: AsyncSession):
    dept = Department(name=f"Operations Dept {uuid.uuid4().hex[:4]}", code=f"OPS-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    user = User(
        email=f"ops_lead_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Ops",
        last_name="Lead",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(user)
    await db.commit()

    dto = AssetCreate(
        name="Atlas Copco Air Compressor",
        asset_type="EQUIPMENT",
        category="Pneumatics",
        manufacturer="Atlas Copco",
        model_number="GA 90 VSD",
        serial_number=f"SN-AC-{uuid.uuid4().hex[:6].upper()}",
        department_id=dept.id,
        status="AVAILABLE",
    )
    asset = await AssetService.create_asset(db, dto, user)

    # Transition 1: Put in use
    asset = await AssetService.transition_status(db, asset.id, AssetStatusTransition(status="IN_USE", notes="Assigned to Plant Shift A"), user)
    assert asset.status == "IN_USE"

    # Transition 2: Maintenance breakdown
    asset = await AssetService.transition_status(db, asset.id, AssetStatusTransition(status="UNDER_MAINTENANCE", notes="Pressure valve seal replacement"), user)
    assert asset.status == "UNDER_MAINTENANCE"

    # Transition 3: Back available
    asset = await AssetService.transition_status(db, asset.id, AssetStatusTransition(status="AVAILABLE", notes="Maintenance complete, pressure tested OK"), user)
    assert asset.status == "AVAILABLE"

    # Retrieve detail and verify activity logs
    detail = await AssetService.get_asset(db, asset.id, user)
    assert len(detail.activity_logs) >= 4  # 1 registration + 3 status changes
    status_changes = [l for l in detail.activity_logs if l.activity_type == "STATUS_CHANGE"]
    assert len(status_changes) == 3


@pytest.mark.asyncio
async def test_location_and_custodian_movement_tracking(db: AsyncSession):
    org = Organization(name=f"Mining Hierarchy {uuid.uuid4().hex[:4]}", code=f"MH-{uuid.uuid4().hex[:4]}", is_active=True)
    db.add(org)
    await db.commit()

    site = Site(name=f"Site Bravo {uuid.uuid4().hex[:4]}", code=f"SB-{uuid.uuid4().hex[:4]}", organization_id=org.id)
    db.add(site)
    await db.commit()

    loc1 = Location(name="Main Workshop", code=f"WS-{uuid.uuid4().hex[:4]}", location_type="FACILITY", site_id=site.id, hierarchy_level=1, breadcrumb="Site Bravo / Main Workshop")
    loc2 = Location(name="Crushing Bay 3", code=f"CB-{uuid.uuid4().hex[:4]}", location_type="AREA", site_id=site.id, hierarchy_level=2, breadcrumb="Site Bravo / Main Workshop / Crushing Bay 3")
    db.add(loc1)
    db.add(loc2)
    await db.commit()

    dept = Department(name=f"Electrical Division {uuid.uuid4().hex[:4]}", code=f"ED-{uuid.uuid4().hex[:4]}", site_id=site.id)
    db.add(dept)
    await db.commit()

    custodian1 = User(
        email=f"tech1_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Alice",
        last_name="Technician",
        is_active=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    custodian2 = User(
        email=f"tech2_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Bob",
        last_name="Foreman",
        is_active=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    admin_user = User(
        email=f"admin_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Admin",
        last_name="User",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(custodian1)
    db.add(custodian2)
    db.add(admin_user)
    await db.commit()

    dto = AssetCreate(
        name="Fluke 8846A Precision Multimeter",
        asset_type="TOOL",
        category="Diagnostic Instruments",
        department_id=dept.id,
        location_id=loc1.id,
        custodian_id=custodian1.id,
    )
    asset = await AssetService.create_asset(db, dto, admin_user)

    # 1. Transfer location to Crushing Bay 3
    asset = await AssetService.update_asset(db, asset.id, AssetUpdate(location_id=loc2.id), admin_user)
    assert asset.location_id == loc2.id

    # 2. Transfer custody to Bob Foreman
    asset = await AssetService.update_asset(db, asset.id, AssetUpdate(custodian_id=custodian2.id), admin_user)
    assert asset.custodian_id == custodian2.id

    # Verify activity logs
    detail = await AssetService.get_asset(db, asset.id, admin_user)
    assert detail.location_breadcrumb == "Site Bravo / Main Workshop / Crushing Bay 3"
    assert detail.custodian_name == "Bob Foreman"

    loc_logs = [l for l in detail.activity_logs if l.activity_type == "LOCATION_CHANGE"]
    cust_logs = [l for l in detail.activity_logs if l.activity_type == "CUSTODIAN_CHANGE"]
    assert len(loc_logs) == 1
    assert len(cust_logs) == 1


@pytest.mark.asyncio
async def test_asset_maintenance_and_work_item_linking(db: AsyncSession):
    dept = Department(name=f"Heavy Maintenance {uuid.uuid4().hex[:4]}", code=f"HM-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    user = User(
        email=f"heavy_maint_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Heavy",
        last_name="Tech",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(user)
    await db.commit()

    dto = AssetCreate(
        name="Siemens 250kW Slurry Pump Motor",
        asset_type="PRODUCTION_EQUIPMENT",
        category="Motors & Drives",
        department_id=dept.id,
        purchase_cost=45000.0,
    )
    asset = await AssetService.create_asset(db, dto, user)

    # Create a linked WorkItem
    work_item = WorkItem(
        id=uuid.uuid4(),
        reference_number=f"PM-2026-{uuid.uuid4().hex[:6].upper()}",
        work_type="MAINTENANCE",
        title="2000hr Stator Winding Insulation Test",
        department_id=dept.id,
        asset_id=asset.id,
        requester_id=user.id,
        status="IN_PROGRESS",
    )
    db.add(work_item)
    await db.commit()

    # Record maintenance event
    m_dto = AssetMaintenanceCreate(
        maintenance_type="PREVENTIVE",
        summary="Megger insulation resistance test passed at 500M Ohms. Greased drive bearings.",
        performed_by="Siemens Certified Field Tech",
        meter_reading=2040.5,
        cost=1850.0,
        work_item_id=work_item.id,
    )
    m_rec = await AssetService.record_maintenance(db, asset.id, m_dto, user)
    assert m_rec.id is not None
    assert m_rec.cost == 1850.0

    # Retrieve asset details and check open work count and maintenance history
    detail = await AssetService.get_asset(db, asset.id, user)
    assert detail.open_work_items_count >= 1
    assert len(detail.maintenance_records) == 1
    assert detail.maintenance_records[0].summary == "Megger insulation resistance test passed at 500M Ohms. Greased drive bearings."


@pytest.mark.asyncio
async def test_asset_archiving_and_restoration(db: AsyncSession):
    dept = Department(name=f"IT Systems {uuid.uuid4().hex[:4]}", code=f"IT-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    user = User(
        email=f"it_admin_{uuid.uuid4().hex[:4]}@example.com",
        first_name="IT",
        last_name="Admin",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(user)
    await db.commit()

    dto = AssetCreate(
        name="Dell PowerEdge R740 Server",
        asset_type="IT_EQUIPMENT",
        category="Servers",
        department_id=dept.id,
        status="AVAILABLE",
    )
    asset = await AssetService.create_asset(db, dto, user)

    # 1. Archive
    asset = await AssetService.archive_asset(db, asset.id, "End of Life replacement after 5 years service", user)
    assert asset.is_archived is True
    assert asset.status == "RETIRED"
    assert asset.archived_reason == "End of Life replacement after 5 years service"

    # Default list should exclude archived
    active_list = await AssetService.list_assets(db, user, include_archived=False)
    assert asset.id not in [a.id for a in active_list]

    # Include archived list should contain it
    all_list = await AssetService.list_assets(db, user, include_archived=True)
    assert asset.id in [a.id for a in all_list]

    # 2. Restore
    asset = await AssetService.restore_asset(db, asset.id, user)
    assert asset.is_archived is False
    assert asset.status == "AVAILABLE"


@pytest.mark.asyncio
async def test_machine_to_asset_migration_and_sync(db: AsyncSession):
    dept = Department(name=f"Fleet Mining {uuid.uuid4().hex[:4]}", code=f"FM-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    user = User(
        email=f"fleet_mgr_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Fleet",
        last_name="Manager",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(user)
    await db.commit()

    m_type = MachineType(name=f"Dump Truck 50T {uuid.uuid4().hex[:4]}", category="HAULAGE")
    db.add(m_type)
    await db.commit()

    machine = Machine(
        identifier=f"CAT-777-{uuid.uuid4().hex[:4].upper()}",
        machine_type_id=m_type.id,
        serial_number=f"SN-DT-{uuid.uuid4().hex[:6].upper()}",
        status="AVAILABLE",
        location="Open Pit Section",
    )
    db.add(machine)
    await db.commit()

    # Run machine migration utility
    summary = await AssetService.migrate_machines_to_assets(db)
    assert summary.scanned_machines >= 1
    assert summary.created_assets >= 1
    assert summary.linked_machines >= 1

    await db.refresh(machine)
    assert machine.asset_id is not None

    # Verify Asset record
    res = await db.execute(select(Asset).where(Asset.id == machine.asset_id))
    asset = res.scalar_one_or_none()
    assert asset is not None
    assert asset.asset_tag == machine.identifier
    assert asset.asset_type == "MACHINE"
    assert asset.machine_id == machine.id

    # Test status synchronization: putting asset into UNDER_MAINTENANCE syncs machine
    await AssetService.transition_status(db, asset.id, AssetStatusTransition(status="UNDER_MAINTENANCE", notes="Transmission fluid leak"), user)
    await db.refresh(machine)
    assert machine.status == "UNDER_MAINTENANCE"
