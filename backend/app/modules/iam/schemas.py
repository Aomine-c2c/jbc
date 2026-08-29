from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID

# ── Organization ─────────────────────────────
class OrganizationCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    industry_type: Optional[str] = "Mining & Mineral Processing"
    country: Optional[str] = "Zimbabwe"
    currency: Optional[str] = "USD"

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    industry_type: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    is_active: Optional[bool] = None

class OrganizationResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    industry_type: str
    country: str
    currency: str
    is_active: bool
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# ── Site ─────────────────────────────────────
class SiteCreate(BaseModel):
    organization_id: Optional[UUID] = None
    code: str
    name: str
    site_type: Optional[str] = "MINE_SITE"
    address: Optional[str] = None
    gps_coordinates: Optional[str] = None

class SiteUpdate(BaseModel):
    name: Optional[str] = None
    site_type: Optional[str] = None
    address: Optional[str] = None
    gps_coordinates: Optional[str] = None
    is_active: Optional[bool] = None

class SiteResponse(BaseModel):
    id: UUID
    organization_id: Optional[UUID] = None
    code: str
    name: str
    site_type: str
    address: Optional[str] = None
    gps_coordinates: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# ── Department ───────────────────────────────
class DepartmentCreate(BaseModel):
    site_id: Optional[UUID] = None
    code: Optional[str] = None
    name: str
    description: Optional[str] = None
    hod_id: Optional[UUID] = None
    sla_hours_default: Optional[int] = 24

class DepartmentUpdate(BaseModel):
    site_id: Optional[UUID] = None
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    hod_id: Optional[UUID] = None
    sla_hours_default: Optional[int] = None
    is_active: Optional[bool] = None

class DepartmentResponse(BaseModel):
    id: UUID
    site_id: Optional[UUID] = None
    code: Optional[str] = None
    name: str
    description: Optional[str] = None
    hod_id: Optional[UUID] = None
    sla_hours_default: int
    is_active: bool
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# ── Section ──────────────────────────────────
class SectionCreate(BaseModel):
    department_id: UUID
    code: str
    name: str
    description: Optional[str] = None
    supervisor_id: Optional[UUID] = None

class SectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    supervisor_id: Optional[UUID] = None
    is_active: Optional[bool] = None

class SectionResponse(BaseModel):
    id: UUID
    department_id: UUID
    code: str
    name: str
    description: Optional[str] = None
    supervisor_id: Optional[UUID] = None
    is_active: bool
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# ── Team ─────────────────────────────────────
class TeamCreate(BaseModel):
    section_id: UUID
    code: str
    name: str
    shift_pattern: Optional[str] = "DAY_SHIFT"
    team_lead_id: Optional[UUID] = None

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    shift_pattern: Optional[str] = None
    team_lead_id: Optional[UUID] = None
    is_active: Optional[bool] = None

class TeamResponse(BaseModel):
    id: UUID
    section_id: UUID
    code: str
    name: str
    shift_pattern: str
    team_lead_id: Optional[UUID] = None
    is_active: bool
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# ── Position ─────────────────────────────────
class PositionCreate(BaseModel):
    code: str
    title: str
    department_id: Optional[UUID] = None
    skill_level: Optional[str] = "JOURNEYMAN"
    description: Optional[str] = None

class PositionUpdate(BaseModel):
    title: Optional[str] = None
    skill_level: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class PositionResponse(BaseModel):
    id: UUID
    code: str
    title: str
    department_id: Optional[UUID] = None
    skill_level: str
    description: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# ── Employee Profile ─────────────────────────
class EmployeeProfileCreate(BaseModel):
    national_id: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    medical_clearance_date: Optional[datetime] = None
    mine_induction_expiry: Optional[datetime] = None
    skills_and_certifications: Optional[List[Dict[str, Any]]] = None
    notes: Optional[str] = None

class EmployeeProfileUpdate(BaseModel):
    national_id: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    medical_clearance_date: Optional[datetime] = None
    mine_induction_expiry: Optional[datetime] = None
    skills_and_certifications: Optional[List[Dict[str, Any]]] = None
    notes: Optional[str] = None

class EmployeeProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    national_id: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    medical_clearance_date: Optional[datetime] = None
    mine_induction_expiry: Optional[datetime] = None
    skills_and_certifications: Optional[List[Dict[str, Any]]] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# ── Users ────────────────────────────────────
class UserCreate(BaseModel):
    email: str
    first_name: str
    last_name: str
    password: str
    department_id: Optional[UUID] = None
    section_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    position_id: Optional[UUID] = None
    supervisor_id: Optional[UUID] = None
    employee_number: Optional[str] = None
    phone_number: Optional[str] = None
    shift_pattern: Optional[str] = "DAY_SHIFT"

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department_id: Optional[UUID] = None
    section_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    position_id: Optional[UUID] = None
    supervisor_id: Optional[UUID] = None
    employee_number: Optional[str] = None
    phone_number: Optional[str] = None
    shift_pattern: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    department_id: Optional[UUID] = None
    section_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    position_id: Optional[UUID] = None
    supervisor_id: Optional[UUID] = None
    employee_number: Optional[str] = None
    phone_number: Optional[str] = None
    shift_pattern: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    profile: Optional[EmployeeProfileResponse] = None
    model_config = ConfigDict(from_attributes=True)

class UserListResponse(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    department_id: Optional[UUID] = None
    department_name: Optional[str] = None
    position_id: Optional[UUID] = None
    employee_number: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    is_active: bool
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: Optional[str] = None

class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MeResponse(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    department_id: Optional[UUID] = None
    section_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    position_id: Optional[UUID] = None
    supervisor_id: Optional[UUID] = None
    is_active: bool
    is_superuser: bool
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class RoleResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class UserRolesUpdate(BaseModel):
    role_ids: List[UUID]
