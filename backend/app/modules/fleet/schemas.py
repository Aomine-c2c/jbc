from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


# ── Fleet Schemas ──────────────────────────────────────────────

class MachineTypeCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    category: Optional[str] = "Lifting & Transport"
    hourly_rate: float = 50.0


class MachineTypeResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    hourly_rate: float
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class MachineCreate(BaseModel):
    machine_type_id: UUID
    identifier: str = Field(..., min_length=1)
    serial_number: Optional[str] = None
    location: Optional[str] = "Central Equipment Yard"
    location_id: Optional[UUID] = None
    capacity_rating: Optional[str] = None
    current_hour_meter: Optional[float] = 0.0


class MachineUpdate(BaseModel):
    status: Optional[str] = None
    location: Optional[str] = None
    location_id: Optional[UUID] = None
    current_hour_meter: Optional[float] = None
    last_maintenance_date: Optional[datetime] = None


class MachineResponse(BaseModel):
    id: UUID
    machine_type_id: UUID
    identifier: str
    serial_number: Optional[str] = None
    status: str
    location: Optional[str] = None
    location_id: Optional[UUID] = None
    location_breadcrumb: Optional[str] = None
    capacity_rating: Optional[str] = None
    current_hour_meter: float = 0.0
    last_maintenance_date: Optional[datetime] = None
    machine_type: Optional[MachineTypeResponse] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ── Requisition DTOs ───────────────────────────────────────────

class RequisitionCreate(BaseModel):
    machine_type_id: UUID
    department_id: UUID
    collaborating_department_id: Optional[UUID] = None
    purpose: str = Field(..., min_length=3, description="Operational purpose of equipment requisition")
    job_card_id: Optional[UUID] = None
    machine_id: Optional[UUID] = None
    quantity: int = Field(1, ge=1)
    location: str = Field(..., min_length=2, description="Location of work execution")
    location_id: Optional[UUID] = None
    required_date: Optional[datetime] = None
    start_time: datetime
    end_time: datetime
    priority: int = 1  # 0: Low, 1: Medium, 2: High, 3: Urgent
    operator_required: bool = False
    operator_name: Optional[str] = None
    special_requirements: Optional[str] = None
    safety_requirements: Optional[str] = None
    cost_centre: Optional[str] = None
    estimated_cost: Optional[float] = 0.0
    notes: Optional[str] = None


class RequisitionSubmit(BaseModel):
    comments: Optional[str] = None


class RequisitionReview(BaseModel):
    comments: Optional[str] = "Review complete"


class RequisitionReturnForCorrection(BaseModel):
    comments: str = Field(..., description="Reason for correction")


class RequisitionApprove(BaseModel):
    comments: str = Field(..., description="Approval justification")


class RequisitionAllocate(BaseModel):
    machine_id: UUID = Field(..., description="Allocated specific equipment unit")
    start_hour_meter: Optional[float] = 0.0
    start_hours: Optional[int] = 0  # backwards compatibility
    operator_name: Optional[str] = None
    comments: Optional[str] = None


class RequisitionAllocatePartial(BaseModel):
    machine_id: UUID = Field(..., description="Allocated specific equipment unit")
    start_hour_meter: Optional[float] = 0.0
    operator_name: Optional[str] = None
    comments: Optional[str] = None


class RequisitionMarkUnavailable(BaseModel):
    comments: str = Field(..., description="Reason for unavailability")


class RequisitionReserve(BaseModel):
    machine_id: UUID
    start_hours: Optional[float] = 0.0


# Alias used by tests
MachineDispatchStart = RequisitionAllocate


class RequisitionConfirm(BaseModel):
    comments: Optional[str] = "Requisition confirmed"


class RequisitionDispatch(BaseModel):
    machine_id: Optional[UUID] = None
    start_hour_meter: Optional[float] = None
    start_hours: Optional[float] = None
    operator_name: Optional[str] = None
    comments: Optional[str] = None


class RequisitionFinish(BaseModel):
    comments: Optional[str] = "Requisition usage finished"


class RequisitionStartUse(BaseModel):
    comments: Optional[str] = None


class RequisitionReturn(BaseModel):
    end_hour_meter: Optional[float] = None
    end_hours: Optional[int] = None  # backwards compatibility
    damage_or_issues: Optional[str] = None
    comments: Optional[str] = None


class RequisitionClose(BaseModel):
    comments: Optional[str] = None


class RequisitionReject(BaseModel):
    comments: str = Field(..., description="Rejection rationale")


class RequisitionCancel(BaseModel):
    reason: str = Field(..., description="Cancellation rationale")


# ── Response Schemas ───────────────────────────────────────────

class RequisitionActionLogResponse(BaseModel):
    id: UUID
    user_id: UUID
    action: str
    state_from: Optional[str] = None
    state_to: Optional[str] = None
    details: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ReservationResponse(BaseModel):
    id: UUID
    requisition_id: Optional[UUID] = None
    machine_id: UUID
    reservation_type: str
    start_time: datetime
    end_time: datetime
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    reservation_status: str
    start_hours: float
    end_hours: Optional[float] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class RequisitionResponse(BaseModel):
    id: UUID
    requisition_number: Optional[str] = None
    department_id: UUID
    collaborating_department_id: Optional[UUID] = None
    requester_id: UUID
    purpose: str
    job_card_id: Optional[UUID] = None
    
    machine_type_id: UUID
    machine_id: Optional[UUID] = None
    quantity: int = 1
    location: str
    location_id: Optional[UUID] = None
    location_breadcrumb: Optional[str] = None
    
    required_date: Optional[datetime] = None
    start_time: datetime
    end_time: datetime
    estimated_duration_hours: float = 1.0
    priority: int = 1
    
    operator_required: bool = False
    operator_name: Optional[str] = None
    special_requirements: Optional[str] = None
    safety_requirements: Optional[str] = None
    
    cost_centre: Optional[str] = None
    estimated_cost: float = 0.0
    actual_cost: Optional[float] = None
    
    status: str
    
    dept_approver_id: Optional[UUID] = None
    dept_approved_at: Optional[datetime] = None
    equipment_checker_id: Optional[UUID] = None
    equipment_checked_at: Optional[datetime] = None
    approver_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    scheduler_id: Optional[UUID] = None
    scheduled_at: Optional[datetime] = None
    dispatcher_id: Optional[UUID] = None
    dispatched_at: Optional[datetime] = None
    returned_at: Optional[datetime] = None
    inspector_id: Optional[UUID] = None
    inspected_at: Optional[datetime] = None
    inspection_notes: Optional[str] = None
    
    start_hour_meter: Optional[float] = None
    end_hour_meter: Optional[float] = None
    closed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None
    comments: Optional[str] = None

    machine_type: Optional[MachineTypeResponse] = None
    allocated_machine: Optional[MachineResponse] = None
    reservations: list[ReservationResponse] = []
    action_logs: list[RequisitionActionLogResponse] = []

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class RequisitionListResponse(BaseModel):
    id: UUID
    requisition_number: Optional[str] = None
    department_id: UUID
    collaborating_department_id: Optional[UUID] = None
    purpose: str
    job_card_id: Optional[UUID] = None
    machine_type_id: UUID
    machine_id: Optional[UUID] = None
    location: str
    start_time: datetime
    end_time: datetime
    priority: int
    status: str
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ScheduledSlot(BaseModel):
    requisition_id: Optional[UUID] = None
    requisition_number: Optional[str] = None
    purpose: str
    department_name: Optional[str] = None
    start_time: datetime
    end_time: datetime
    status: str
    reservation_type: str

class MaintenanceScheduleCreate(BaseModel):
    start_time: datetime
    end_time: datetime
    comments: Optional[str] = None


class MachineAvailabilityItem(BaseModel):
    machine_id: UUID
    identifier: str
    machine_type_id: UUID
    machine_type_name: str
    status: str
    location: Optional[str] = None
    capacity_rating: Optional[str] = None
    is_available_for_window: bool
    scheduled_slots: list[ScheduledSlot] = []
