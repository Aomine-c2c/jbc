from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from datetime import datetime
import uuid

class BusinessAuditLogBase(BaseModel):
    user_id: Optional[uuid.UUID] = None
    user_name: Optional[str] = None
    department_name: Optional[str] = None
    role_names: Optional[str] = None
    action: str
    resource: str
    resource_id: Optional[str] = None
    previous_value: Optional[Any] = None
    new_value: Optional[Any] = None
    reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class BusinessAuditLogResponse(BusinessAuditLogBase):
    id: uuid.UUID
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class AuditListResponse(BaseModel):
    items: list[BusinessAuditLogResponse]
    total: int
    page: int
    size: int
