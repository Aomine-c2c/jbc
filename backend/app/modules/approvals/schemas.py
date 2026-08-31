import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ApprovalStepOut(BaseModel):
    id: uuid.UUID
    step_number: int
    authority_role: str
    required_permission: str
    status: str
    approver_id: Optional[uuid.UUID] = None
    approver_name: Optional[str] = None
    approver_role_name: Optional[str] = None
    action: Optional[str] = None
    comment: Optional[str] = None
    state_from: Optional[str] = None
    state_to: Optional[str] = None
    signature_token: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: Optional[datetime] = None
    delegated_to_id: Optional[uuid.UUID] = None
    delegated_to_name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovalRequestOut(BaseModel):
    id: uuid.UUID
    resource_type: str
    resource_id: uuid.UUID
    workflow_type: str
    priority: int
    risk_level: str
    estimated_cost: float
    status: str
    created_by_id: uuid.UUID
    created_at: datetime
    resolved_at: Optional[datetime] = None
    steps: list[ApprovalStepOut] = []

    model_config = {"from_attributes": True}


class ApprovalDecideRequest(BaseModel):
    action: str = Field(..., description="approve | reject | return | delegate | escalate")
    comment: str = Field("", description="Mandatory for reject/return; recommended for approve")
    resource_owner_id: uuid.UUID = Field(..., description="ID of the resource creator for self-approval check")
    state_from: str = Field(..., description="Current resource status")
    state_to: str = Field(..., description="Target resource status after this decision")


class ApprovalDelegateRequest(BaseModel):
    delegate_to_id: uuid.UUID
    delegate_to_name: str
    comment: str = ""


class ApprovalEscalateRequest(BaseModel):
    comment: str = ""


class ApprovalOpenRequest(BaseModel):
    resource_owner_id: uuid.UUID
    department_id: uuid.UUID
    current_status: str
    priority: int = 0
    estimated_cost: float = 0.0
    risk_level: str = "LOW"
    workflow_type: str = "STANDARD"


class ApprovalDecisionOut(BaseModel):
    approval_request_id: uuid.UUID
    step_id: uuid.UUID
    action: str
    next_resource_status: str
    all_resolved: bool
    signature_token: str

class ApprovalInboxItem(BaseModel):
    approval_request: ApprovalRequestOut
    pending_step: ApprovalStepOut
    resource_title: str
    resource_description: str
    requester_name: str
    department_name: Optional[str] = None

class WorkflowStepDefCreate(BaseModel):
    step_number: int
    authority_role: str
    required_permission: str

class WorkflowStepDefOut(WorkflowStepDefCreate):
    id: uuid.UUID
    workflow_id: uuid.UUID
    model_config = {"from_attributes": True}

class WorkflowDefinitionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    resource_type: Optional[str] = None
    department_id: Optional[uuid.UUID] = None
    min_cost: Optional[float] = None
    min_priority: Optional[int] = None
    risk_level: Optional[str] = None
    workflow_type: Optional[str] = None
    is_active: bool = True
    priority: int = 0
    steps: list[WorkflowStepDefCreate]

class WorkflowDefinitionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    resource_type: Optional[str] = None
    department_id: Optional[uuid.UUID] = None
    min_cost: Optional[float] = None
    min_priority: Optional[int] = None
    risk_level: Optional[str] = None
    workflow_type: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    steps: Optional[list[WorkflowStepDefCreate]] = None

class WorkflowDefinitionOut(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    resource_type: Optional[str] = None
    department_id: Optional[uuid.UUID] = None
    min_cost: Optional[float] = None
    min_priority: Optional[int] = None
    risk_level: Optional[str] = None
    workflow_type: Optional[str] = None
    is_active: bool
    priority: int
    created_at: datetime
    steps: list[WorkflowStepDefOut] = []
    
    model_config = {"from_attributes": True}
