from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.iam.models import User, Organization, Site, Section, Team, Position
from app.modules.iam.schemas import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    SiteCreate, SiteUpdate, SiteResponse,
    SectionCreate, SectionUpdate, SectionResponse,
    TeamCreate, TeamUpdate, TeamResponse,
    PositionCreate, PositionUpdate, PositionResponse,
)
from app.core.authz import AuthzGuard
from app.modules.audit.service import AuditService

def _get_current_user():
    """Lazy import to avoid circular dependency."""
    from app.main import get_current_user as gcu
    return gcu

org_router = APIRouter(prefix="/api/v1/iam/org", tags=["iam-org"])

# ── Organizations ──────────────────────────────────────────

@org_router.post("/organizations", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(data: OrganizationCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(_get_current_user())):
    from app.modules.iam.api import _get_user_permissions
    user_perms = _get_user_permissions(current_user)
    if not AuthzGuard.check_permission(current_user, "settings:manage", user_perms):
        raise HTTPException(status_code=403, detail="Not enough privileges")
    
    existing = await db.execute(select(Organization).where(Organization.code == data.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Organization code already exists")
        
    org = Organization(**data.model_dump())
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org

@org_router.get("/organizations", response_model=list[OrganizationResponse])
async def list_organizations(db: AsyncSession = Depends(get_db), current_user: User = Depends(_get_current_user())):
    result = await db.execute(select(Organization).order_by(Organization.name))
    return result.scalars().all()

@org_router.get("/organizations/{org_id}", response_model=OrganizationResponse)
async def get_organization(org_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(_get_current_user())):
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

@org_router.patch("/organizations/{org_id}", response_model=OrganizationResponse)
async def update_organization(org_id: UUID, data: OrganizationUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(_get_current_user())):
    from app.modules.iam.api import _get_user_permissions
    user_perms = _get_user_permissions(current_user)
    if not AuthzGuard.check_permission(current_user, "settings:manage", user_perms):
        raise HTTPException(status_code=403, detail="Not enough privileges")
    
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(org, k, v)
    await db.commit()
    await db.refresh(org)
    return org

# ── Sites ──────────────────────────────────────────────────

@org_router.post("/sites", response_model=SiteResponse, status_code=status.HTTP_201_CREATED)
async def create_site(data: SiteCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(_get_current_user())):
    from app.modules.iam.api import _get_user_permissions
    user_perms = _get_user_permissions(current_user)
    if not AuthzGuard.check_permission(current_user, "settings:manage", user_perms):
        raise HTTPException(status_code=403, detail="Not enough privileges")
    
    existing = await db.execute(select(Site).where(Site.code == data.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Site code already exists")
        
    site = Site(**data.model_dump())
    db.add(site)
    await db.commit()
    await db.refresh(site)
    return site

@org_router.get("/sites", response_model=list[SiteResponse])
async def list_sites(db: AsyncSession = Depends(get_db), current_user: User = Depends(_get_current_user())):
    result = await db.execute(select(Site).order_by(Site.name))
    return result.scalars().all()

@org_router.get("/sites/{site_id}", response_model=SiteResponse)
async def get_site(site_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(_get_current_user())):
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site

@org_router.patch("/sites/{site_id}", response_model=SiteResponse)
async def update_site(site_id: UUID, data: SiteUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(_get_current_user())):
    from app.modules.iam.api import _get_user_permissions
    user_perms = _get_user_permissions(current_user)
    if not AuthzGuard.check_permission(current_user, "settings:manage", user_perms):
        raise HTTPException(status_code=403, detail="Not enough privileges")
    
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
        
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(site, k, v)
    await db.commit()
    await db.refresh(site)
    return site


# ── Sections ───────────────────────────────────────────────

@org_router.post("/sections", response_model=SectionResponse, status_code=status.HTTP_201_CREATED)
async def create_section(data: SectionCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(_get_current_user())):
    from app.modules.iam.api import _get_user_permissions
    user_perms = _get_user_permissions(current_user)
    if not AuthzGuard.check_permission(current_user, "departments:manage", user_perms, resource_dept_id=data.department_id):
        raise HTTPException(status_code=403, detail="Not enough privileges")
    
    existing = await db.execute(select(Section).where(Section.code == data.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Section code already exists")
        
    section = Section(**data.model_dump())
    db.add(section)
    await db.commit()
    await db.refresh(section)
    return section

@org_router.get("/sections", response_model=list[SectionResponse])
async def list_sections(db: AsyncSession = Depends(get_db), current_user: User = Depends(_get_current_user())):
    result = await db.execute(select(Section).order_by(Section.name))
    return result.scalars().all()

@org_router.get("/sections/{section_id}", response_model=SectionResponse)
async def get_section(section_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(_get_current_user())):
    result = await db.execute(select(Section).where(Section.id == section_id))
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    return section

@org_router.patch("/sections/{section_id}", response_model=SectionResponse)
async def update_section(section_id: UUID, data: SectionUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(_get_current_user())):
    result = await db.execute(select(Section).where(Section.id == section_id))
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
        
    from app.modules.iam.api import _get_user_permissions
    user_perms = _get_user_permissions(current_user)
    if not AuthzGuard.check_permission(current_user, "departments:manage", user_perms, resource_dept_id=section.department_id):
        raise HTTPException(status_code=403, detail="Not enough privileges")
        
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(section, k, v)
    await db.commit()
    await db.refresh(section)
    return section

# ── Teams ──────────────────────────────────────────────────

@org_router.post("/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(data: TeamCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(_get_current_user())):
    existing = await db.execute(select(Team).where(Team.code == data.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Team code already exists")
        
    # verify section exists
    result = await db.execute(select(Section).where(Section.id == data.section_id))
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
        
    from app.modules.iam.api import _get_user_permissions
    user_perms = _get_user_permissions(current_user)
    if not AuthzGuard.check_permission(current_user, "departments:manage", user_perms, resource_dept_id=section.department_id):
        raise HTTPException(status_code=403, detail="Not enough privileges")

    team = Team(**data.model_dump())
    db.add(team)
    await db.commit()
    await db.refresh(team)
    return team

@org_router.get("/teams", response_model=list[TeamResponse])
async def list_teams(db: AsyncSession = Depends(get_db), current_user: User = Depends(_get_current_user())):
    result = await db.execute(select(Team).order_by(Team.name))
    return result.scalars().all()

@org_router.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(team_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(_get_current_user())):
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@org_router.patch("/teams/{team_id}", response_model=TeamResponse)
async def update_team(team_id: UUID, data: TeamUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(_get_current_user())):
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    # check permission via section -> department
    result_sec = await db.execute(select(Section).where(Section.id == team.section_id))
    section = result_sec.scalar_one_or_none()
    
    from app.modules.iam.api import _get_user_permissions
    user_perms = _get_user_permissions(current_user)
    if section and not AuthzGuard.check_permission(current_user, "departments:manage", user_perms, resource_dept_id=section.department_id):
        raise HTTPException(status_code=403, detail="Not enough privileges")
        
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(team, k, v)
    await db.commit()
    await db.refresh(team)
    return team


# ── Positions ──────────────────────────────────────────────

@org_router.post("/positions", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
async def create_position(data: PositionCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(_get_current_user())):
    from app.modules.iam.api import _get_user_permissions
    user_perms = _get_user_permissions(current_user)
    if not AuthzGuard.check_permission(current_user, "departments:manage", user_perms, resource_dept_id=data.department_id):
        raise HTTPException(status_code=403, detail="Not enough privileges")
        
    existing = await db.execute(select(Position).where(Position.code == data.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Position code already exists")
        
    position = Position(**data.model_dump())
    db.add(position)
    await db.commit()
    await db.refresh(position)
    return position

@org_router.get("/positions", response_model=list[PositionResponse])
async def list_positions(db: AsyncSession = Depends(get_db), current_user: User = Depends(_get_current_user())):
    result = await db.execute(select(Position).order_by(Position.title))
    return result.scalars().all()

@org_router.get("/positions/{position_id}", response_model=PositionResponse)
async def get_position(position_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(_get_current_user())):
    result = await db.execute(select(Position).where(Position.id == position_id))
    position = result.scalar_one_or_none()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position

@org_router.patch("/positions/{position_id}", response_model=PositionResponse)
async def update_position(position_id: UUID, data: PositionUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(_get_current_user())):
    result = await db.execute(select(Position).where(Position.id == position_id))
    position = result.scalar_one_or_none()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
        
    from app.modules.iam.api import _get_user_permissions
    user_perms = _get_user_permissions(current_user)
    if not AuthzGuard.check_permission(current_user, "departments:manage", user_perms, resource_dept_id=position.department_id):
        raise HTTPException(status_code=403, detail="Not enough privileges")
        
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(position, k, v)
    await db.commit()
    await db.refresh(position)
    return position
