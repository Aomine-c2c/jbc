from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class RequestMaterialItemCreate(BaseModel):
    material_name: str = Field(..., min_length=1, max_length=255)
    part_number: Optional[str] = None
    quantity_requested: float = Field(1.0, gt=0)
    unit: str = Field("units", max_length=50)
    store_location: Optional[str] = None
    unit_cost: Optional[float] = 0.0


class RequestMaterialItemResponse(BaseModel):
    id: UUID
    request_id: UUID
    material_name: str
    part_number: Optional[str] = None
    quantity_requested: float
    unit: str
    store_location: Optional[str] = None
    quantity_issued: float = 0.0
    quantity_returned: float = 0.0
    unit_cost: float = 0.0
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class MaterialIssueRequest(BaseModel):
    item_id: UUID
    quantity: float = Field(..., gt=0)
    notes: Optional[str] = None


class MaterialReturnRequest(BaseModel):
    item_id: UUID
    quantity: float = Field(..., gt=0)
    notes: Optional[str] = None


class RequestCreate(BaseModel):
    request_type: str = Field("MACHINE_REQUEST", description="MACHINE_REQUEST, EQUIPMENT_REQUEST, VEHICLE_REQUEST, MATERIAL_REQUEST, PERSONNEL_REQUEST, CONTRACTOR_REQUEST, OTHER")
    title: str = Field(..., min_length=1, max_length=255)
    purpose: str = Field(..., min_length=1, max_length=2000)
    description: Optional[str] = None
    priority: int = Field(1, ge=0, le=4)
    department_id: UUID
    collaborating_department_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    location: Optional[str] = None
    required_from: Optional[datetime] = None
    required_to: Optional[datetime] = None
    estimated_duration_hours: Optional[float] = 0.0
    cost_centre: Optional[str] = None
    estimated_cost: Optional[float] = 0.0
    work_item_id: Optional[UUID] = None
    job_card_id: Optional[UUID] = None
    machine_requisition_id: Optional[UUID] = None
    type_specific_data: Optional[Dict[str, Any]] = None
    material_items: Optional[List[RequestMaterialItemCreate]] = None


class RequestUpdate(BaseModel):
    title: Optional[str] = None
    purpose: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    department_id: Optional[UUID] = None
    collaborating_department_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    location: Optional[str] = None
    required_from: Optional[datetime] = None
    required_to: Optional[datetime] = None
    estimated_duration_hours: Optional[float] = None
    cost_centre: Optional[str] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    type_specific_data: Optional[Dict[str, Any]] = None


class RequestTransition(BaseModel):
    action: str = Field(..., description="SUBMIT, REVIEW, APPROVE, REJECT, RETURN_FOR_CORRECTION, CANCEL")
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class RequestFulfill(BaseModel):
    fulfillment_status: str = Field("FULFILLED", description="AWAITING_FULFILLMENT, PARTIALLY_FULFILLED, FULFILLED, CLOSED")
    notes: Optional[str] = None
    actual_cost: Optional[float] = None


class RequestCommentCreate(BaseModel):
    comment: str = Field(..., min_length=1, max_length=2000)


class RequestCommentResponse(BaseModel):
    id: UUID
    request_id: UUID
    user_id: UUID
    comment: str
    created_at: Optional[datetime] = None
    user_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class RequestActionLogResponse(BaseModel):
    id: UUID
    request_id: UUID
    user_id: UUID
    action: str
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    user_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class RequestAttachmentResponse(BaseModel):
    id: UUID
    request_id: UUID
    filename: str
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    file_size_kb: float = 0.0
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class RequestResponse(BaseModel):
    id: UUID
    request_number: str
    request_type: str
    title: str
    purpose: str
    description: Optional[str] = None
    priority: int
    status: str
    fulfillment_status: str
    requester_id: UUID
    department_id: UUID
    collaborating_department_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    location: Optional[str] = None
    required_from: Optional[datetime] = None
    required_to: Optional[datetime] = None
    estimated_duration_hours: float = 0.0
    cost_centre: Optional[str] = None
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    work_item_id: Optional[UUID] = None
    job_card_id: Optional[UUID] = None
    machine_requisition_id: Optional[UUID] = None
    approver_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    fulfillment_user_id: Optional[UUID] = None
    fulfilled_at: Optional[datetime] = None
    type_specific_data: Optional[Dict[str, Any]] = None
    
    requester_name: Optional[str] = None
    department_name: Optional[str] = None
    collaborating_department_name: Optional[str] = None
    location_breadcrumb: Optional[str] = None
    approver_name: Optional[str] = None
    fulfillment_user_name: Optional[str] = None
    work_item_reference: Optional[str] = None
    
    material_items: List[RequestMaterialItemResponse] = []
    action_logs: List[RequestActionLogResponse] = []
    comments: List[RequestCommentResponse] = []
    attachments: List[RequestAttachmentResponse] = []
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class RequestListResponse(BaseModel):
    id: UUID
    request_number: str
    request_type: str
    title: str
    purpose: str
    priority: int
    status: str
    fulfillment_status: str
    requester_name: Optional[str] = None
    department_id: UUID
    department_name: Optional[str] = None
    collaborating_department_name: Optional[str] = None
    location_breadcrumb: Optional[str] = None
    required_from: Optional[datetime] = None
    required_to: Optional[datetime] = None
    work_item_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
