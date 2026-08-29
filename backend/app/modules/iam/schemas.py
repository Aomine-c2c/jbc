from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class DepartmentCreate(BaseModel):
    name: str
    description: Optional[str] = None


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class DepartmentResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: str
    first_name: str
    last_name: str
    password: str
    department_id: Optional[UUID] = None


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    department_id: Optional[UUID] = None
    is_active: bool
    is_superuser: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    department_id: Optional[UUID] = None
    department_name: Optional[str] = None
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
