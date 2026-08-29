import pytest
import uuid

from app.modules.iam.models import (
    Organization,
    Site,
    Department,
    Section,
    Team,
    Position,
    User,
    UserRole,
    Role,
)
from app.modules.iam.org_service import OrgService
from app.modules.iam.org_schemas import (
    OrganizationCreate,
    SiteCreate,
    SectionCreate,
    TeamCreate,
    PositionCreate,
    UserPlacementUpdate,
)


@pytest.mark.asyncio
async def test_org_service_default_seeding(db):
    org, site = await OrgService.ensure_default_org_and_site(db)
    assert org is not None
    assert org.code == "BIKITA_MINERALS"
    assert site is not None
    assert site.code == "BIKITA_MINE_SITE"
    assert site.organization_id == org.id


@pytest.mark.asyncio
async def test_create_and_list_org_entities(db):
    org, site = await OrgService.ensure_default_org_and_site(db)
    
    # 1. Create Department
    dept = Department(id=uuid.uuid4(), name="Electrical Department", code="ELEC", site_id=site.id)
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    
    # 2. Create Section
    sec = await OrgService.create_section(
        db,
        SectionCreate(department_id=dept.id, code="HIGH_VOLTAGE", name="High Voltage Distribution"),
    )
    assert sec.code == "HIGH_VOLTAGE"
    assert sec.department_id == dept.id
    
    # 3. Create Team
    team = await OrgService.create_team(
        db,
        TeamCreate(section_id=sec.id, code="HV_CREW_1", name="Substation A Maintenance Crew", shift_pattern="DAY_SHIFT"),
    )
    assert team.code == "HV_CREW_1"
    assert team.section_id == sec.id
    
    # 4. Create Position
    pos = await OrgService.create_position(
        db,
        PositionCreate(code="HV_ELECTRICIAN_SR", title="Senior HV Electrician", department_id=dept.id, skill_level="SPECIALIST"),
    )
    assert pos.code == "HV_ELECTRICIAN_SR"


@pytest.mark.asyncio
async def test_chain_of_command_hierarchy(db, seed_user_a, seed_user_b):
    # Setup 3-tier supervisor chain: Tech (seed_user_a) -> Supervisor (seed_user_b) -> HOD (hod_user)
    from app.core.security import get_password_hash
    hod_user = User(
        id=uuid.uuid4(),
        email="hod.electrical@bikita.com",
        first_name="Farai",
        last_name="Moyo",
        hashed_password=get_password_hash("password123"),
        is_active=True,
    )
    db.add(hod_user)
    await db.commit()
    await db.refresh(hod_user)
    
    # Assign Position
    pos_hod = await OrgService.create_position(
        db, PositionCreate(code="ELEC_ENG_HOD", title="Engineering HOD", skill_level="SUPERINTENDENT")
    )
    pos_sup = await OrgService.create_position(
        db, PositionCreate(code="ELEC_SUP_I", title="Electrical Shift Supervisor", skill_level="SUPERVISOR")
    )
    pos_tech = await OrgService.create_position(
        db, PositionCreate(code="AUTO_ELEC_II", title="Auto Electrician II", skill_level="JOURNEYMAN")
    )
    
    # Update placements
    await OrgService.update_user_placement(
        db, hod_user.id, UserPlacementUpdate(position_id=pos_hod.id)
    )
    await OrgService.update_user_placement(
        db, seed_user_b.id, UserPlacementUpdate(position_id=pos_sup.id, supervisor_id=hod_user.id)
    )
    await OrgService.update_user_placement(
        db, seed_user_a.id, UserPlacementUpdate(position_id=pos_tech.id, supervisor_id=seed_user_b.id)
    )
    
    # Query Chain of Command for Tech
    res = await OrgService.get_user_chain_of_command(db, seed_user_a.id)
    assert res.target_user_id == seed_user_a.id
    assert len(res.chain) == 2
    
    # Level 1: Direct Supervisor (User B)
    assert res.chain[0].level == 1
    assert res.chain[0].user_id == seed_user_b.id
    assert res.chain[0].position_title == "Electrical Shift Supervisor"
    
    # Level 2: HOD (Farai Moyo)
    assert res.chain[1].level == 2
    assert res.chain[1].user_id == hod_user.id
    assert res.chain[1].position_title == "Engineering HOD"


@pytest.mark.asyncio
async def test_prevent_self_supervision(db, seed_user_a):
    with pytest.raises(Exception) as excinfo:
        await OrgService.update_user_placement(
            db, seed_user_a.id, UserPlacementUpdate(supervisor_id=seed_user_a.id)
        )
    assert "cannot be their own supervisor" in str(excinfo.value)


@pytest.mark.asyncio
async def test_org_api_endpoints(async_client, admin_headers):
    # 1. Get Hierarchy Tree
    tree_res = await async_client.get("/api/v1/org/hierarchy", headers=admin_headers)
    assert tree_res.status_code == 200
    tree_data = tree_res.json()
    assert "sites" in tree_data
    assert tree_data["code"] == "BIKITA_MINERALS"
    
    # 2. Create Site
    site_payload = {
        "code": "HARARE_REGIONAL_OFFICE",
        "name": "Harare Corporate Headquarters",
        "site_type": "ADMIN_OFFICE",
    }
    site_res = await async_client.post("/api/v1/org/sites", json=site_payload, headers=admin_headers)
    assert site_res.status_code == 201
    assert site_res.json()["code"] == "HARARE_REGIONAL_OFFICE"
    
    # 3. Create Position
    pos_payload = {
        "code": "COMM_TECH_SR",
        "title": "Senior Telecommunications Technician",
        "skill_level": "SPECIALIST",
    }
    pos_res = await async_client.post("/api/v1/org/positions", json=pos_payload, headers=admin_headers)
    assert pos_res.status_code == 201
    assert pos_res.json()["title"] == "Senior Telecommunications Technician"
