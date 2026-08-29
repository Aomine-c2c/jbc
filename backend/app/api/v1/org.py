import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.iam.models import User
from app.modules.iam.org_service import OrgService
from app.modules.iam.org_schemas import (
    OrganizationCreate,
    OrganizationResponse,
    SiteCreate,
    SiteResponse,
    SectionCreate,
    SectionResponse,
    TeamCreate,
    TeamResponse,
    PositionCreate,
    PositionResponse,
    UserPlacementUpdate,
    ChainOfCommandResponse,
    OrganizationHierarchyTree,
)

org_router = APIRouter(prefix="/api/v1/org", tags=["Organizational Structure"])


def _get_current_user():
    from app.main import get_current_user as _gcu
    return _gcu


# ── Hierarchy Tree & Chain of Command ────────────────────────

@org_router.get("/hierarchy", response_model=OrganizationHierarchyTree)
async def get_organization_hierarchy(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    """
    Returns the complete multi-tier organizational tree:
    Organization -> Sites -> Departments -> Sections -> Teams -> Members.
    """
    return await OrgService.get_organization_hierarchy_tree(db)


@org_router.get("/users/{user_id}/chain-of-command", response_model=ChainOfCommandResponse)
async def get_user_chain_of_command(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    """
    Returns the upward supervisory chain of command and escalation steps for an employee.
    """
    return await OrgService.get_user_chain_of_command(db, user_id)


@org_router.patch("/users/{user_id}/placement")
async def update_user_placement(
    user_id: uuid.UUID,
    payload: UserPlacementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    """
    Updates an employee's departmental, section, team, position, and supervisor assignments.
    """
    if not current_user.is_superuser:
        from app.modules.iam.api import _get_user_permissions
        perms = _get_user_permissions(current_user)
        if "iam:admin" not in perms and "global_override" not in perms:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required.")

    user = await OrgService.update_user_placement(db, user_id, payload)
    return {
        "status": "updated",
        "user_id": str(user.id),
        "department_id": str(user.department_id) if user.department_id else None,
        "section_id": str(user.section_id) if user.section_id else None,
        "team_id": str(user.team_id) if user.team_id else None,
        "position_id": str(user.position_id) if user.position_id else None,
        "supervisor_id": str(user.supervisor_id) if user.supervisor_id else None,
    }


# ── Organizations ────────────────────────────────────────────

@org_router.get("/organizations", response_model=List[OrganizationResponse])
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await OrgService.list_organizations(db)


@org_router.post("/organizations", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required.")
    return await OrgService.create_organization(db, payload)


# ── Sites ────────────────────────────────────────────────────

@org_router.get("/sites", response_model=List[SiteResponse])
async def list_sites(
    organization_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await OrgService.list_sites(db, organization_id)


@org_router.post("/sites", response_model=SiteResponse, status_code=status.HTTP_201_CREATED)
async def create_site(
    payload: SiteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required.")
    return await OrgService.create_site(db, payload)


# ── Sections ─────────────────────────────────────────────────

@org_router.get("/sections", response_model=List[SectionResponse])
async def list_sections(
    department_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await OrgService.list_sections(db, department_id)


@org_router.post("/sections", response_model=SectionResponse, status_code=status.HTTP_201_CREATED)
async def create_section(
    payload: SectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required.")
    return await OrgService.create_section(db, payload)


# ── Teams ────────────────────────────────────────────────────

@org_router.get("/teams", response_model=List[TeamResponse])
async def list_teams(
    section_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await OrgService.list_teams(db, section_id)


@org_router.post("/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    payload: TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required.")
    return await OrgService.create_team(db, payload)


# ── Positions (Job Titles / Trades) ──────────────────────────

@org_router.get("/positions", response_model=List[PositionResponse])
async def list_positions(
    department_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await OrgService.list_positions(db, department_id)


@org_router.post("/positions", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
async def create_position(
    payload: PositionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required.")
    return await OrgService.create_position(db, payload)
