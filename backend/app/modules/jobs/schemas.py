import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class JobCardCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    department_id: uuid.UUID
    # Cross-department collaboration fields
    requesting_department_id: Optional[uuid.UUID] = None
    responsible_department_id: Optional[uuid.UUID] = None
    external_contractor: Optional[str] = None
    priority: int = 0
    machine_id: Optional[uuid.UUID] = None
    job_type: Optional[str] = None
    maintenance_type: Optional[str] = None
    workshop_code: Optional[str] = None
    location: Optional[str] = None
    plant_area: Optional[str] = None
    required_date: Optional[datetime] = None
    reported_issue: Optional[str] = None
    job_instruction: Optional[str] = None
    estimated_hours: Optional[float] = 0.0
    estimated_cost: Optional[float] = 0.0


class JobCardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    machine_id: Optional[uuid.UUID] = None
    job_type: Optional[str] = None
    maintenance_type: Optional[str] = None
    workshop_code: Optional[str] = None
    location: Optional[str] = None
    plant_area: Optional[str] = None
    required_date: Optional[datetime] = None
    reported_issue: Optional[str] = None
    job_instruction: Optional[str] = None
    estimated_hours: Optional[float] = None
    estimated_cost: Optional[float] = None
    assigned_personnel: Optional[str] = None
    labour_details: Optional[str] = None
    requesting_department_id: Optional[uuid.UUID] = None
    responsible_department_id: Optional[uuid.UUID] = None
    external_contractor: Optional[str] = None


class JobCardSubmit(BaseModel):
    comments: Optional[str] = None


class JobCardApprove(BaseModel):
    comments: str


# Alias used by security tests
JobCardAction = JobCardApprove


class JobCardReject(BaseModel):
    comments: str


class JobCardReturn(BaseModel):
    comments: str = Field(..., description="Reason for returning job card for correction")


class JobCardPlan(BaseModel):
    estimated_hours: Optional[float] = None
    estimated_cost: Optional[float] = None
    job_instruction: Optional[str] = None
    comments: Optional[str] = None


class JobCardAssign(BaseModel):
    supervisor_id: uuid.UUID
    assigned_tech_ids: Optional[list[str]] = None
    assigned_personnel: Optional[str] = None
    comments: Optional[str] = None


class JobCardStart(BaseModel):
    comments: Optional[str] = None
    actual_start_time: Optional[datetime] = None


class JobCardHold(BaseModel):
    reason: str = Field(..., description="Operational hold justification")
    comments: Optional[str] = None


class JobCardPartCreate(BaseModel):
    part_name: str = Field(..., min_length=1, max_length=255)
    part_number: Optional[str] = None
    quantity: float = 1.0
    unit_cost: Optional[float] = None
    is_material: bool = False


class JobCardLabourCreate(BaseModel):
    technician_name: str = Field(..., min_length=1)
    trade: str = Field("Mechanical Fitter", min_length=1)
    hours_spent: float = Field(..., ge=0.0)
    hourly_rate: float = Field(25.0, ge=0.0)
    notes: Optional[str] = None


class JobCardComplete(BaseModel):
    comments: Optional[str] = None
    actual_end_time: Optional[datetime] = None
    completion_notes: Optional[str] = None
    action_taken: str = Field(..., description="Details of the work performed")
    downtime_hours: float = Field(0.0, description="Total downtime of equipment in hours")
    parts_used: Optional[list[JobCardPartCreate]] = None
    labour_entries: Optional[list[JobCardLabourCreate]] = None
    labour_details: Optional[str] = None


class JobCardReview(BaseModel):
    comments: Optional[str] = None


class JobCardVerify(BaseModel):
    comments: str


class JobCardConfirm(BaseModel):
    requester_confirmed: bool = True
    requester_notes: Optional[str] = None
    comments: Optional[str] = None


class JobCardClose(BaseModel):
    comments: Optional[str] = None


class JobCardCancel(BaseModel):
    reason: str = Field(..., description="Reason for cancellation")
    comments: Optional[str] = None


class JobCardAmendmentCreate(BaseModel):
    field_name: str = Field(..., description="Field name being corrected")
    new_value: str = Field(..., description="New corrected value")
    amendment_reason: str = Field(..., min_length=5, description="Auditable justification for the amendment")


class JobCardAttachmentCreate(BaseModel):
    filename: str = Field(..., min_length=1)
    file_url: Optional[str] = None
    file_type: Optional[str] = "image/png"
    file_size_kb: Optional[float] = 0.0


# ── Work Package Schemas ─────────────────────────────────────────

class WorkPackageCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    package_type: str = "OTHER"
    owning_department_id: uuid.UUID
    responsible_supervisor_id: Optional[uuid.UUID] = None
    assigned_personnel: Optional[str] = None
    planned_start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None
    estimated_hours: float = 0.0
    special_requirements: Optional[str] = None
    safety_notes: Optional[str] = None
    prerequisite_wp_id: Optional[uuid.UUID] = None


class WorkPackageUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    package_type: Optional[str] = None
    responsible_supervisor_id: Optional[uuid.UUID] = None
    assigned_personnel: Optional[str] = None
    planned_start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    work_performed: Optional[str] = None
    special_requirements: Optional[str] = None
    safety_notes: Optional[str] = None
    prerequisite_wp_id: Optional[uuid.UUID] = None


class WorkPackageTransition(BaseModel):
    comments: Optional[str] = None
    work_performed: Optional[str] = None
    actual_hours: Optional[float] = None
    rejection_reason: Optional[str] = None


class WorkPackageActionLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    action: str
    state_from: Optional[str] = None
    state_to: Optional[str] = None
    details: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class WorkPackageResponse(BaseModel):
    id: uuid.UUID
    job_card_id: uuid.UUID
    package_number: str
    title: str
    description: Optional[str] = None
    package_type: str
    owning_department_id: uuid.UUID
    responsible_supervisor_id: Optional[uuid.UUID] = None
    assigned_personnel: Optional[str] = None
    planned_start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None
    estimated_hours: float = 0.0
    actual_hours: float = 0.0
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    verified_by_id: Optional[uuid.UUID] = None
    work_performed: Optional[str] = None
    special_requirements: Optional[str] = None
    safety_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    prerequisite_wp_id: Optional[uuid.UUID] = None
    action_logs: list[WorkPackageActionLogResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ── Collaborator Schemas ─────────────────────────────────────────

class JobCardCollaboratorCreate(BaseModel):
    department_id: uuid.UUID
    # REQUESTING | RESPONSIBLE | SUPPORTING | ASSIGNED | EXTERNAL_CONTRACTOR
    role: str = "SUPPORTING"
    notes: Optional[str] = None


class JobCardCollaboratorResponse(BaseModel):
    id: uuid.UUID
    job_card_id: uuid.UUID
    department_id: uuid.UUID
    role: str
    added_by_id: uuid.UUID
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ── Response DTOs ─────────────────────────────────────────────

class JobCardPartResponse(BaseModel):
    id: uuid.UUID
    part_name: str
    part_number: Optional[str] = None
    quantity: float
    unit_cost: Optional[float] = None
    is_material: bool = False
    model_config = ConfigDict(from_attributes=True)


class JobCardLabourResponse(BaseModel):
    id: uuid.UUID
    technician_name: str
    trade: str
    hours_spent: float
    hourly_rate: float
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class JobCardExecutionEventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    timestamp: datetime
    duration_minutes: float = 0.0
    operator_name: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class JobCardAmendmentResponse(BaseModel):
    id: uuid.UUID
    amended_by_id: uuid.UUID
    field_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    amendment_reason: str
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class JobCardAttachmentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    file_size_kb: Optional[float] = 0.0
    uploaded_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class JobCardCommentResponse(BaseModel):
    id: uuid.UUID
    author_id: uuid.UUID
    comment: str
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class JobCardActionLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    action: str
    state_from: Optional[str] = None
    state_to: Optional[str] = None
    details: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class JobReportCalculations(BaseModel):
    actual_duration_hours: float = 0.0
    total_labour_hours: float = 0.0
    total_labour_cost: float = 0.0
    total_spares_cost: float = 0.0
    total_materials_cost: float = 0.0
    total_material_cost: float = 0.0
    total_actual_cost: float = 0.0
    duration_variance_hours: float = 0.0
    cost_variance: float = 0.0
    cost_variance_percentage: float = 0.0
    variance_status: str = "ON_BUDGET"


class JobCardResponse(BaseModel):
    id: uuid.UUID
    job_number: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: str
    priority: int
    
    department_id: uuid.UUID
    requesting_department_id: Optional[uuid.UUID] = None
    responsible_department_id: Optional[uuid.UUID] = None
    external_contractor: Optional[str] = None
    workshop_code: Optional[str] = None
    location: Optional[str] = None
    plant_area: Optional[str] = None
    machine_id: Optional[uuid.UUID] = None

    creator_id: uuid.UUID
    required_date: Optional[datetime] = None
    job_type: Optional[str] = None
    maintenance_type: Optional[str] = None
    reported_issue: Optional[str] = None
    job_instruction: Optional[str] = None

    approver_id: Optional[uuid.UUID] = None
    approved_at: Optional[datetime] = None

    supervisor_id: Optional[uuid.UUID] = None
    assigned_date: Optional[datetime] = None
    assigned_personnel: Optional[str] = None
    estimated_hours: float = 0.0
    estimated_cost: float = 0.0

    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    downtime_hours: float = 0.0

    action_taken: Optional[str] = None
    labour_details: Optional[str] = None
    completion_notes: Optional[str] = None

    requester_confirmed: bool = False
    requester_notes: Optional[str] = None
    requester_confirmed_at: Optional[datetime] = None

    verified_at: Optional[datetime] = None
    closure_date: Optional[datetime] = None
    closed_by_id: Optional[uuid.UUID] = None

    parts: list[JobCardPartResponse] = []
    labour_entries: list[JobCardLabourResponse] = []
    execution_events: list[JobCardExecutionEventResponse] = []
    amendments: list[JobCardAmendmentResponse] = []
    attachments: list[JobCardAttachmentResponse] = []
    comments: list[JobCardCommentResponse] = []
    action_logs: list[JobCardActionLogResponse] = []

    # Cross-department collaboration
    collaborators: list[JobCardCollaboratorResponse] = []
    work_packages: list[WorkPackageResponse] = []
    # 0.0 – 100.0 aggregate of WP completion
    overall_completion_pct: float = 0.0

    # Calculated metrics
    calculations: Optional[JobReportCalculations] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class JobCardListResponse(BaseModel):
    id: uuid.UUID
    job_number: Optional[str] = None
    title: str
    status: str
    priority: int
    department_id: uuid.UUID
    workshop_code: Optional[str] = None
    location: Optional[str] = None
    maintenance_type: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
