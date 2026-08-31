from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class WorkItemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    work_type: str = Field("JOB_CARD", description="JOB_CARD, MAINTENANCE, INSPECTION, FOLLOW_UP, OTHER")
    department_id: UUID
    location_id: Optional[UUID] = None
    location: Optional[str] = None
    plant_area: Optional[str] = None
    machine_id: Optional[UUID] = None
    priority: int = Field(1, ge=0, le=4, description="0: Low, 1: Medium, 2: High, 3: Urgent, 4: Critical")
    supervisor_id: Optional[UUID] = None
    assigned_personnel: Optional[str] = None
    external_contractor: Optional[str] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = 0.0
    estimated_cost: Optional[float] = 0.0
    type_specific_data: Optional[Dict[str, Any]] = None


class WorkItemCreate(WorkItemBase):
    parent_work_item_id: Optional[UUID] = None
    source_request_id: Optional[UUID] = None
    job_card_id: Optional[UUID] = None


class WorkItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    work_type: Optional[str] = None
    department_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    location: Optional[str] = None
    plant_area: Optional[str] = None
    machine_id: Optional[UUID] = None
    priority: Optional[int] = None
    supervisor_id: Optional[UUID] = None
    assigned_personnel: Optional[str] = None
    external_contractor: Optional[str] = None
    due_date: Optional[datetime] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    type_specific_data: Optional[Dict[str, Any]] = None


class WorkItemTransition(BaseModel):
    status: str = Field(..., description="Target status: SUBMITTED, APPROVED, ASSIGNED, IN_PROGRESS, ON_HOLD, COMPLETED, VERIFIED, CLOSED, REJECTED, CANCELLED, RETURNED")
    comments: Optional[str] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    actual_hours: Optional[float] = None
    actual_cost: Optional[float] = None


class WorkItemFollowUpCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    work_type: str = "FOLLOW_UP"
    priority: int = 2
    assigned_personnel: Optional[str] = None
    due_date: Optional[datetime] = None
    findings: Optional[str] = None
    corrective_actions: Optional[str] = None


class WorkItemPartCreate(BaseModel):
    part_name: str = Field(..., min_length=1)
    part_number: Optional[str] = None
    quantity: float = Field(1.0, gt=0)
    unit_cost: Optional[float] = 0.0
    is_material: bool = False


class WorkItemPartResponse(BaseModel):
    id: UUID
    work_item_id: UUID
    part_name: str
    part_number: Optional[str] = None
    quantity: float
    unit_cost: Optional[float] = None
    is_material: bool
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class WorkItemActionLogResponse(BaseModel):
    id: UUID
    work_item_id: UUID
    user_id: UUID
    action: str
    state_from: Optional[str] = None
    state_to: Optional[str] = None
    details: Optional[str] = None
    created_at: Optional[datetime] = None
    user_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class WorkItemCommentCreate(BaseModel):
    comment: str = Field(..., min_length=1)


class WorkItemCommentResponse(BaseModel):
    id: UUID
    work_item_id: UUID
    user_id: UUID
    comment: str
    created_at: Optional[datetime] = None
    user_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class WorkItemResponse(WorkItemBase):
    id: UUID
    reference_number: str
    status: str
    requester_id: UUID
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    actual_hours: float = 0.0
    actual_cost: float = 0.0
    parent_work_item_id: Optional[UUID] = None
    source_request_id: Optional[UUID] = None
    job_card_id: Optional[UUID] = None
    
    approver_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    approval_status: str = "NONE"
    
    sla_hours: float = 24.0
    sla_due_at: Optional[datetime] = None
    sla_status: str = "WITHIN_SLA"
    
    # Nested relations & display fields
    department_name: Optional[str] = None
    location_breadcrumb: Optional[str] = None
    machine_identifier: Optional[str] = None
    requester_name: Optional[str] = None
    supervisor_name: Optional[str] = None
    
    action_logs: List[WorkItemActionLogResponse] = []
    comments: List[WorkItemCommentResponse] = []
    parts: List[WorkItemPartResponse] = []
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class WorkItemListResponse(BaseModel):
    id: UUID
    reference_number: str
    work_type: str
    title: str
    status: str
    priority: int
    department_id: UUID
    department_name: Optional[str] = None
    location_breadcrumb: Optional[str] = None
    machine_identifier: Optional[str] = None
    supervisor_name: Optional[str] = None
    assigned_personnel: Optional[str] = None
    due_date: Optional[datetime] = None
    sla_status: str = "WITHIN_SLA"
    job_card_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class WorkItemMigrationSummary(BaseModel):
    scanned_job_cards: int = 0
    created_work_items: int = 0
    updated_work_items: int = 0
    skipped: int = 0
    details: List[str] = []
