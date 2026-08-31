import pytest
import uuid
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.modules.iam.models import Organization, Site, Location, User, Department, Scope
from app.modules.iam.location_schemas import LocationCreate, LocationUpdate, LocationArchive
from app.modules.iam.location_service import LocationService
from app.modules.jobs.models import JobCard
from app.modules.fleet.models import Machine, MachineType
from app.core.authz import AuthzGuard


@pytest.mark.asyncio
async def test_full_location_hierarchy_creation_and_breadcrumbs(db: AsyncSession):
    # 1. Organization & Site
    org = Organization(
        id=uuid.uuid4(),
        code="MINING_CORP",
        name="Global Mining Corp",
        industry_type="Mining",
        country="Zimbabwe",
    )
    db.add(org)
    await db.commit()

    site = Site(
        id=uuid.uuid4(),
        organization_id=org.id,
        code="OPERATION_SITE_A",
        name="Bikita Operations",
        site_type="MINE_SITE",
    )
    db.add(site)
    await db.commit()

    # 2. Facility / Plant (Level 1 under Site)
    plant = await LocationService.create_location(
        db=db,
        data=LocationCreate(
            site_id=site.id,
            organization_id=org.id,
            code="PROC_PLANT_01",
            name="Processing Plant",
            location_type="FACILITY",
        )
    )
    assert plant.hierarchy_level == 1
    assert plant.breadcrumb == "Bikita Operations / Processing Plant"

    # 3. Area (Level 2 under Facility)
    area = await LocationService.create_location(
        db=db,
        data=LocationCreate(
            parent_id=plant.id,
            code="CRUSH_AREA_01",
            name="Crushing Plant",
            location_type="AREA",
        )
    )
    assert area.hierarchy_level == 2
    assert area.breadcrumb == "Bikita Operations / Processing Plant / Crushing Plant"

    # 4. Section (Level 3 under Area)
    section = await LocationService.create_location(
        db=db,
        data=LocationCreate(
            parent_id=area.id,
            code="CONV_SEC_01",
            name="Conveyor Section",
            location_type="SECTION",
        )
    )
    assert section.hierarchy_level == 3
    assert section.breadcrumb == "Bikita Operations / Processing Plant / Crushing Plant / Conveyor Section"

    # 5. Specific Location (Level 4 under Section)
    spec_loc = await LocationService.create_location(
        db=db,
        data=LocationCreate(
            parent_id=section.id,
            code="CONV_C01",
            name="Conveyor C-01 Drive Head",
            location_type="SPECIFIC_LOCATION",
            barcode_or_nfc="TAG-CONV-C01-998",
        )
    )
    assert spec_loc.hierarchy_level == 4
    assert spec_loc.breadcrumb == "Bikita Operations / Processing Plant / Crushing Plant / Conveyor Section / Conveyor C-01 Drive Head"

    # 6. Verify Hierarchy Tree
    tree = await LocationService.get_hierarchy_tree(db=db, site_id=site.id)
    assert len(tree) == 1
    assert tree[0].code == "PROC_PLANT_01"
    assert len(tree[0].children) == 1
    assert tree[0].children[0].code == "CRUSH_AREA_01"
    assert len(tree[0].children[0].children) == 1
    assert tree[0].children[0].children[0].code == "CONV_SEC_01"
    assert len(tree[0].children[0].children[0].children) == 1
    assert tree[0].children[0].children[0].children[0].code == "CONV_C01"


@pytest.mark.asyncio
async def test_flexible_hierarchy_varying_depths(db: AsyncSession):
    """Verifies that hierarchy handles varying levels e.g. Site -> Head Office -> Server Room."""
    site = Site(
        id=uuid.uuid4(),
        code="HQ_SITE",
        name="Harare Head Office",
        site_type="COMMERCIAL_OFFICE",
    )
    db.add(site)
    await db.commit()

    # Short hierarchy: Site -> Area -> Specific Location (only 2 levels)
    it_area = await LocationService.create_location(
        db=db,
        data=LocationCreate(
            site_id=site.id,
            code="IT_INFRA",
            name="IT Infrastructure",
            location_type="AREA",
        )
    )
    assert it_area.hierarchy_level == 1
    assert it_area.breadcrumb == "Harare Head Office / IT Infrastructure"

    server_room = await LocationService.create_location(
        db=db,
        data=LocationCreate(
            parent_id=it_area.id,
            code="SRV_ROOM_01",
            name="Primary Server Room Rack B",
            location_type="ROOM",
        )
    )
    assert server_room.hierarchy_level == 2
    assert server_room.breadcrumb == "Harare Head Office / IT Infrastructure / Primary Server Room Rack B"


@pytest.mark.asyncio
async def test_hierarchy_cycle_prevention(db: AsyncSession):
    """Ensures node cannot be set as its own parent or as child of a descendant."""
    node_a = await LocationService.create_location(
        db=db,
        data=LocationCreate(code="NODE_A", name="Node A", location_type="AREA")
    )
    node_b = await LocationService.create_location(
        db=db,
        data=LocationCreate(parent_id=node_a.id, code="NODE_B", name="Node B", location_type="SECTION")
    )
    node_c = await LocationService.create_location(
        db=db,
        data=LocationCreate(parent_id=node_b.id, code="NODE_C", name="Node C", location_type="SPECIFIC_LOCATION")
    )

    # 1. Attempt self-parenting
    with pytest.raises(HTTPException) as exc_self:
        await LocationService.update_location(
            db=db,
            location_id=node_a.id,
            data=LocationUpdate(parent_id=node_a.id),
        )
    assert exc_self.value.status_code == 400
    assert "own parent" in exc_self.value.detail

    # 2. Attempt cycle: set Node A's parent to Node C (which is descendant of A)
    with pytest.raises(HTTPException) as exc_cycle:
        await LocationService.update_location(
            db=db,
            location_id=node_a.id,
            data=LocationUpdate(parent_id=node_c.id),
        )
    assert exc_cycle.value.status_code == 400
    assert "Hierarchy cycle detected" in exc_cycle.value.detail


@pytest.mark.asyncio
async def test_location_rename_updates_descendant_breadcrumbs(db: AsyncSession):
    parent = await LocationService.create_location(
        db=db,
        data=LocationCreate(code="WORKSHOP_MAIN", name="Old Mechanical Workshop", location_type="FACILITY")
    )
    child = await LocationService.create_location(
        db=db,
        data=LocationCreate(parent_id=parent.id, code="BAY_01", name="Heavy Bay 1", location_type="WORK_CENTER")
    )
    assert child.breadcrumb == "Old Mechanical Workshop / Heavy Bay 1"

    # Rename parent
    await LocationService.update_location(
        db=db,
        location_id=parent.id,
        data=LocationUpdate(name="Central Heavy Workshop"),
    )

    # Verify child breadcrumb updated automatically
    child_fetched = await LocationService.get_location(db=db, location_id=child.id)
    assert child_fetched.breadcrumb == "Central Heavy Workshop / Heavy Bay 1"


@pytest.mark.asyncio
async def test_location_search(db: AsyncSession):
    loc = await LocationService.create_location(
        db=db,
        data=LocationCreate(
            code="HYDRAULIC_SHOP",
            name="Hydraulic Maintenance Workshop",
            location_type="WORK_CENTER",
            barcode_or_nfc="NFC-HYDR-092",
        )
    )

    # Search by name substring
    res_name = await LocationService.search_locations(db=db, query_str="Hydraulic")
    assert any(r.id == loc.id for r in res_name)

    # Search by code
    res_code = await LocationService.search_locations(db=db, query_str="HYDRAULIC_SHOP")
    assert any(r.id == loc.id for r in res_code)

    # Search by barcode/NFC
    res_nfc = await LocationService.search_locations(db=db, query_str="NFC-HYDR")
    assert any(r.id == loc.id for r in res_nfc)


@pytest.mark.asyncio
async def test_location_archiving_and_deletion_safety(db: AsyncSession):
    loc_parent = await LocationService.create_location(
        db=db,
        data=LocationCreate(code="SAFE_AREA", name="Safety Area", location_type="AREA")
    )
    loc_child = await LocationService.create_location(
        db=db,
        data=LocationCreate(parent_id=loc_parent.id, code="SAFE_SUB", name="Sub Station", location_type="SPECIFIC_LOCATION")
    )

    # 1. Attempt to delete parent with child should be rejected (409)
    with pytest.raises(HTTPException) as exc_del_child:
        await LocationService.delete_location(db=db, location_id=loc_parent.id)
    assert exc_del_child.value.status_code == 409
    assert "child location" in exc_del_child.value.detail

    # 2. Archive parent
    archived = await LocationService.archive_location(
        db=db, location_id=loc_parent.id, reason="Area decommissioned for overhaul"
    )
    assert archived.is_archived is True
    assert archived.is_active is False
    assert archived.archived_reason == "Area decommissioned for overhaul"

    # 3. Restore parent
    restored = await LocationService.restore_location(db=db, location_id=loc_parent.id)
    assert restored.is_archived is False
    assert restored.is_active is True


@pytest.mark.asyncio
async def test_legacy_text_location_migration(db: AsyncSession):
    """Tests automatic scanning and non-destructive mapping of historical string locations."""
    # Setup test department and user
    dept = Department(id=uuid.uuid4(), name="Processing Dept", is_active=True)
    db.add(dept)
    user = User(id=uuid.uuid4(), email="worker@example.com", first_name="John", last_name="Doe", hashed_password="pw", is_active=True)
    db.add(user)
    m_type = MachineType(id=uuid.uuid4(), name="CAT Excavator 320D", category="Earthmoving")
    db.add(m_type)
    await db.commit()

    # Create legacy Job Cards with text location strings but null location_id
    jc1 = JobCard(
        id=uuid.uuid4(),
        job_number="JC-LEGACY-001",
        title="Repair vibrating screen bearing",
        department_id=dept.id,
        creator_id=user.id,
        location="Screening Plant Deck 2",
        plant_area="Processing Plant Area",
        location_id=None,
    )
    db.add(jc1)

    m1 = Machine(
        id=uuid.uuid4(),
        machine_type_id=m_type.id,
        identifier="EXC-LEGACY-01",
        location="North Open Pit Bench 4",
        location_id=None,
    )
    db.add(m1)
    await db.commit()

    # Run migration
    summary = await LocationService.migrate_text_locations(db=db)
    assert summary.scanned_job_cards >= 1
    assert summary.scanned_machines >= 1
    assert summary.created_locations >= 2

    # Verify Job Card now has location_id linked while preserving original location text string
    await db.refresh(jc1)
    assert jc1.location_id is not None
    assert jc1.location == "Screening Plant Deck 2"

    # Verify Machine now has location_id linked while preserving original location text string
    await db.refresh(m1)
    assert m1.location_id is not None
    assert m1.location == "North Open Pit Bench 4"

    # Verify created locations exist
    loc_res = await db.execute(select(Location).where(Location.id == jc1.location_id))
    loc = loc_res.scalar_one_or_none()
    assert loc is not None
    assert loc.name == "Screening Plant Deck 2"


@pytest.mark.asyncio
async def test_location_aware_authorization():
    """Verifies location and site scoped permission enforcement in AuthzGuard."""
    site_a = uuid.uuid4()
    site_b = uuid.uuid4()
    loc_a = uuid.uuid4()
    loc_b = uuid.uuid4()

    user_site_a = User(
        id=uuid.uuid4(),
        email="site_a_mgr@example.com",
        first_name="Site",
        last_name="Manager",
        hashed_password="pw",
        site_id=site_a,
        location_id=loc_a,
        is_active=True,
    )

    # User has SITE scoped permission
    perms_site = {"job_card:read": [Scope.SITE]}
    assert AuthzGuard.check_permission(user_site_a, "job_card:read", perms_site, resource_site_id=site_a) is True
    assert AuthzGuard.check_permission(user_site_a, "job_card:read", perms_site, resource_site_id=site_b) is False

    # User has LOCATION scoped permission
    perms_loc = {"job_card:update": [Scope.LOCATION]}
    assert AuthzGuard.check_permission(user_site_a, "job_card:update", perms_loc, resource_location_id=loc_a) is True
    assert AuthzGuard.check_permission(user_site_a, "job_card:update", perms_loc, resource_location_id=loc_b) is False
