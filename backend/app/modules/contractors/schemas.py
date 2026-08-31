from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class CertificationRecord(BaseModel):
    certification: str = Field(..., min_length=1)
    number: Optional[str] = None
    expiry: Optional[str] = None
    issued_by: Optional[str] = None


class ContractorCompanyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    registration_number: Optional[str] = None
    primary_contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    service_categories: List[str] = Field(default_factory=list)
    status: str = Field("ACTIVE", max_length=50)
    safety_induction_valid_until: Optional[datetime] = None
    notes: Optional[str] = None


class ContractorCompanyCreate(ContractorCompanyBase):
    company_code: Optional[str] = None


class ContractorCompanyUpdate(BaseModel):
    name: Optional[str] = None
    registration_number: Optional[str] = None
    primary_contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    service_categories: Optional[List[str]] = None
    status: Optional[str] = None
    safety_induction_valid_until: Optional[datetime] = None
    notes: Optional[str] = None


class ContractorCompanyResponse(ContractorCompanyBase):
    id: UUID
    company_code: str
    is_archived: bool = False
    archived_at: Optional[datetime] = None
    archived_reason: Optional[str] = None
    worker_count: int = 0
    assignment_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ContractorCompanyListResponse(BaseModel):
    id: UUID
    company_code: str
    name: str
    primary_contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    service_categories: List[str] = Field(default_factory=list)
    status: str
    safety_induction_valid_until: Optional[datetime] = None
    worker_count: int = 0
    is_archived: bool = False
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ContractorWorkerBase(BaseModel):
    contractor_company_id: UUID
    full_name: str = Field(..., min_length=1, max_length=255)
    skill_or_role: str = Field(..., min_length=1, max_length=100)
    certification_records: List[Dict[str, Any]] = Field(default_factory=list)
    certification_expiry: Optional[datetime] = None
    status: str = Field("ACTIVE", max_length=50)
    phone_number: Optional[str] = None
    badge_number: Optional[str] = None
    notes: Optional[str] = None


class ContractorWorkerCreate(ContractorWorkerBase):
    worker_code: Optional[str] = None


class ContractorWorkerUpdate(BaseModel):
    full_name: Optional[str] = None
    skill_or_role: Optional[str] = None
    certification_records: Optional[List[Dict[str, Any]]] = None
    certification_expiry: Optional[datetime] = None
    status: Optional[str] = None
    phone_number: Optional[str] = None
    badge_number: Optional[str] = None
    notes: Optional[str] = None


class ContractorWorkerResponse(ContractorWorkerBase):
    id: UUID
    worker_code: str
    company_name: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ContractorWorkerListResponse(BaseModel):
    id: UUID
    worker_code: str
    full_name: str
    skill_or_role: str
    company_name: Optional[str] = None
    status: str
    certification_expiry: Optional[datetime] = None
    phone_number: Optional[str] = None
    badge_number: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ContractorAssignmentCreate(BaseModel):
    contractor_company_id: UUID
    worker_ids: Optional[List[UUID]] = Field(default_factory=list)
    work_item_id: Optional[UUID] = None
    job_card_id: Optional[UUID] = None
    work_scope: str = Field(..., min_length=1, max_length=2000)
    start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    cost_agreed: Optional[float] = 0.0


class ContractorAssignmentVerify(BaseModel):
    verification_status: str = Field("VERIFIED_ACCEPTED", max_length=50)
    performance_rating: Optional[int] = Field(None, ge=1, le=5)
    performance_notes: Optional[str] = None
    actual_cost: Optional[float] = None


class ContractorAssignmentResponse(BaseModel):
    id: UUID
    assignment_number: str
    contractor_company_id: UUID
    company_name: Optional[str] = None
    work_item_id: Optional[UUID] = None
    work_item_reference: Optional[str] = None
    job_card_id: Optional[UUID] = None
    work_scope: str
    assignment_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    supervisor_id: UUID
    supervisor_name: Optional[str] = None
    verified_by_id: Optional[UUID] = None
    verified_by_name: Optional[str] = None
    verified_at: Optional[datetime] = None
    verification_status: str = "PENDING"
    performance_rating: Optional[int] = None
    performance_notes: Optional[str] = None
    cost_agreed: float = 0.0
    actual_cost: float = 0.0
    assigned_workers: List[ContractorWorkerListResponse] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ContractorAssignmentListResponse(BaseModel):
    id: UUID
    assignment_number: str
    company_name: str = "Unknown Company"
    work_scope: str
    verification_status: str = "PENDING"
    supervisor_name: Optional[str] = None
    performance_rating: Optional[int] = None
    assignment_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    work_item_reference: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ContractorDocumentCreate(BaseModel):
    contractor_company_id: Optional[UUID] = None
    contractor_worker_id: Optional[UUID] = None
    document_type: str = Field(..., max_length=50)
    title: str = Field(..., min_length=1, max_length=255)
    file_url: Optional[str] = None
    expiry_date: Optional[datetime] = None


class ContractorDocumentResponse(BaseModel):
    id: UUID
    contractor_company_id: Optional[UUID] = None
    contractor_worker_id: Optional[UUID] = None
    document_type: str
    title: str
    file_url: Optional[str] = None
    expiry_date: Optional[datetime] = None
    is_verified: bool
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
