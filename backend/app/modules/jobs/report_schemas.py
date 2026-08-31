import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field


# ── Progress Update ────────────────────────────────────────────

class JobReportProgressUpdateCreate(BaseModel):
    update_type: str = Field(..., description="WORK_START | PROGRESS | PAUSE | RESUME | COMPLETION")
    notes: Optional[str] = None
    hold_reason: Optional[str] = Field(None, description="Required when update_type is PAUSE")
    percentage_complete: int = Field(0, ge=0, le=100, description="Completion estimate 0–100%")


class JobReportProgressUpdateResponse(BaseModel):
    id: uuid.UUID
    update_type: str
    timestamp: datetime
    percentage_complete: int
    notes: Optional[str] = None
    hold_reason: Optional[str] = None
    reported_by_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


# ── Materials & Resources ──────────────────────────────────────

class JobReportMaterialCreate(BaseModel):
    category: str = Field("SPARE_PART", description="SPARE_PART | CONSUMABLE | MATERIAL | TOOL | EQUIPMENT | OTHER")
    item_name: str = Field(..., min_length=1, max_length=255)
    item_code: Optional[str] = None
    quantity: float = Field(1.0, gt=0)
    unit: Optional[str] = Field(None, description="e.g. kg, m, pcs, L")
    unit_cost: Optional[float] = None
    notes: Optional[str] = None


class JobReportMaterialResponse(BaseModel):
    id: uuid.UUID
    category: str
    item_name: str
    item_code: Optional[str] = None
    quantity: float
    unit: Optional[str] = None
    unit_cost: Optional[float] = None
    notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


# ── Attachments ────────────────────────────────────────────────

class JobReportAttachmentCreate(BaseModel):
    category: str = Field("PHOTO", description="PHOTO | DOCUMENT | SKETCH | CERTIFICATE | MEASUREMENT_SHEET | OTHER")
    filename: str = Field(..., min_length=1)
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    file_size_kb: float = 0.0
    caption: Optional[str] = None


class JobReportAttachmentResponse(BaseModel):
    id: uuid.UUID
    category: str
    filename: str
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    file_size_kb: float
    caption: Optional[str] = None
    uploaded_by_id: uuid.UUID
    uploaded_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ── Amendments ─────────────────────────────────────────────────

class JobReportAmendmentCreate(BaseModel):
    field_name: str = Field(..., description="The report field being corrected")
    new_value: str = Field(..., description="The corrected value")
    amendment_reason: str = Field(..., min_length=5, description="Auditable justification for the correction")


class JobReportAmendmentResponse(BaseModel):
    id: uuid.UUID
    field_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    amendment_reason: str
    approval_status: str
    amended_by_id: uuid.UUID
    approved_by_id: Optional[uuid.UUID] = None
    created_at: datetime
    approved_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ── Main Report ────────────────────────────────────────────────

class JobReportUpdate(BaseModel):
    """Fields that can be updated on the report during execution."""
    fault_found: Optional[str] = None
    fault_code: Optional[str] = None
    corrective_action: Optional[str] = None
    technical_notes: Optional[str] = None
    observations: Optional[str] = None
    recommendations: Optional[str] = None
    follow_up_required: Optional[bool] = None
    follow_up_notes: Optional[str] = None
    actual_labour_hours: Optional[float] = None
    actual_cost: Optional[float] = None
    dept_schema_type: Optional[str] = None
    dept_specific_data: Optional[dict[str, Any]] = None


class JobReportResponse(BaseModel):
    id: uuid.UUID
    job_card_id: uuid.UUID

    # Immutability state
    is_locked: bool
    locked_at: Optional[datetime] = None
    locked_by_id: Optional[uuid.UUID] = None

    # Core report data
    fault_found: Optional[str] = None
    fault_code: Optional[str] = None
    corrective_action: Optional[str] = None
    technical_notes: Optional[str] = None
    observations: Optional[str] = None
    recommendations: Optional[str] = None
    follow_up_required: bool
    follow_up_notes: Optional[str] = None
    actual_labour_hours: float
    actual_cost: float

    # Department-specific
    dept_schema_type: str
    dept_specific_data: Optional[dict[str, Any]] = None

    # Nested children
    progress_updates: list[JobReportProgressUpdateResponse] = []
    materials: list[JobReportMaterialResponse] = []
    attachments: list[JobReportAttachmentResponse] = []
    amendments: list[JobReportAmendmentResponse] = []

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Schema field metadata for frontend dynamic rendering ──────

class DeptFieldMeta(BaseModel):
    name: str
    label: str
    description: str
    type: str


class DeptSchemaMetaResponse(BaseModel):
    dept_schema_type: str
    fields: list[DeptFieldMeta]
