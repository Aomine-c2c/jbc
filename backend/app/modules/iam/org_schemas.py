import uuid
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


# ── Organization Schemas ─────────────────────────────────────

class OrganizationBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    industry_type: Optional[str] = "Mining & Mineral Processing"
    country: Optional[str] = "Zimbabwe"
    currency: Optional[str] = "USD"
    is_active: Optional[bool] = True


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    industry_type: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    is_active: Optional[bool] = None


class OrganizationResponse(OrganizationBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Site Schemas ─────────────────────────────────────────────

class SiteBase(BaseModel):
    organization_id: Optional[uuid.UUID] = None
    code: str
    name: str
    site_type: Optional[str] = "MINE_SITE"
    address: Optional[str] = None
    gps_coordinates: Optional[str] = None
    is_active: Optional[bool] = True


class SiteCreate(SiteBase):
    pass


class SiteUpdate(BaseModel):
    name: Optional[str] = None
    site_type: Optional[str] = None
    address: Optional[str] = None
    gps_coordinates: Optional[str] = None
    is_active: Optional[bool] = None


class SiteResponse(SiteBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Section Schemas ──────────────────────────────────────────

class SectionBase(BaseModel):
    department_id: uuid.UUID
    code: str
    name: str
    description: Optional[str] = None
    supervisor_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = True


class SectionCreate(SectionBase):
    pass


class SectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    supervisor_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class SectionResponse(SectionBase):
    id: uuid.UUID
    created_at: datetime
    supervisor_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ── Team Schemas ─────────────────────────────────────────────

class TeamBase(BaseModel):
    section_id: uuid.UUID
    code: str
    name: str
    shift_pattern: Optional[str] = "DAY_SHIFT"
    team_lead_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = True


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    shift_pattern: Optional[str] = None
    team_lead_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class TeamResponse(TeamBase):
    id: uuid.UUID
    created_at: datetime
    team_lead_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ── Position Schemas ─────────────────────────────────────────

class PositionBase(BaseModel):
    code: str
    title: str
    department_id: Optional[uuid.UUID] = None
    skill_level: Optional[str] = "JOURNEYMAN"
    description: Optional[str] = None
    is_active: Optional[bool] = True


class PositionCreate(PositionBase):
    pass


class PositionUpdate(BaseModel):
    title: Optional[str] = None
    department_id: Optional[uuid.UUID] = None
    skill_level: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PositionResponse(PositionBase):
    id: uuid.UUID
    created_at: datetime
    department_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ── Placement & Chain of Command ─────────────────────────────

class UserPlacementUpdate(BaseModel):
    department_id: Optional[uuid.UUID] = None
    section_id: Optional[uuid.UUID] = None
    team_id: Optional[uuid.UUID] = None
    position_id: Optional[uuid.UUID] = None
    supervisor_id: Optional[uuid.UUID] = None
    employee_number: Optional[str] = None
    phone_number: Optional[str] = None
    shift_pattern: Optional[str] = None


class ChainOfCommandStep(BaseModel):
    level: int
    user_id: uuid.UUID
    name: str
    email: str
    position_title: Optional[str] = None
    department_name: Optional[str] = None
    role: str


class ChainOfCommandResponse(BaseModel):
    target_user_id: uuid.UUID
    target_user_name: str
    chain: List[ChainOfCommandStep]


# ── Full Multi-Tier Hierarchy Tree ───────────────────────────

class MemberNode(BaseModel):
    id: str
    name: str
    email: str
    position_title: Optional[str] = None
    roles: List[str] = []
    shift_pattern: Optional[str] = None
    supervisor_id: Optional[str] = None


class TeamNode(BaseModel):
    id: str
    code: str
    name: str
    shift_pattern: str
    team_lead_id: Optional[str] = None
    members: List[MemberNode] = []


class SectionNode(BaseModel):
    id: str
    code: str
    name: str
    supervisor_id: Optional[str] = None
    teams: List[TeamNode] = []
    unassigned_members: List[MemberNode] = []


class DepartmentNode(BaseModel):
    id: str
    code: Optional[str] = None
    name: str
    hod_id: Optional[str] = None
    sla_hours_default: int
    sections: List[SectionNode] = []
    unassigned_members: List[MemberNode] = []


class SiteNode(BaseModel):
    id: str
    code: str
    name: str
    site_type: str
    departments: List[DepartmentNode] = []


class OrganizationHierarchyTree(BaseModel):
    id: str
    code: str
    name: str
    industry_type: str
    country: str
    sites: List[SiteNode] = []
    unassigned_departments: List[DepartmentNode] = []
