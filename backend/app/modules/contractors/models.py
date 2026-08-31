import uuid
from datetime import datetime
import enum
from sqlalchemy import (
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Integer,
    Float,
    JSON,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.db.mixins import TimestampMixin


class ContractorCompanyStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    INACTIVE = "INACTIVE"
    BLACKLISTED = "BLACKLISTED"


class ContractorWorkerStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    EXPIRED_CERTIFICATION = "EXPIRED_CERTIFICATION"
    SUSPENDED = "SUSPENDED"


class ContractorVerificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    VERIFIED_ACCEPTED = "VERIFIED_ACCEPTED"
    REWORK_REQUIRED = "REWORK_REQUIRED"


class ContractorCompany(Base, TimestampMixin):
    """
    Authoritative entity for external service providers, vendors, and contractor firms.
    """
    __tablename__ = "contractor_companies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    registration_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    primary_contact_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    service_categories: Mapped[list | None] = mapped_column(JSON, default=list)  # ["Electrical", "Rigging", "Civil", "Instrumentation"]
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=ContractorCompanyStatus.ACTIVE.value, index=True)
    
    safety_induction_valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    workers = relationship("ContractorWorker", back_populates="company", lazy="selectin", cascade="all, delete-orphan")
    assignments = relationship("ContractorAssignment", back_populates="company", lazy="selectin")
    documents = relationship("ContractorDocument", back_populates="company", lazy="selectin", cascade="all, delete-orphan")


class ContractorWorker(Base, TimestampMixin):
    """
    External contractor individual worker / technician.
    Maintains skill profile, trade qualifications, certifications, and compliance validity.
    """
    __tablename__ = "contractor_workers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contractor_company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contractor_companies.id"), nullable=False, index=True)
    worker_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    skill_or_role: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    certification_records: Mapped[list | None] = mapped_column(JSON, default=list)  # [{"certification": "33kV Lineman", "number": "HV-123", "expiry": "2027-01-01"}]
    certification_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=ContractorWorkerStatus.ACTIVE.value, index=True)
    phone_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    badge_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    company = relationship("ContractorCompany", back_populates="workers")
    assignments = relationship("ContractorWorkerAssignment", back_populates="worker", lazy="selectin")
    documents = relationship("ContractorDocument", back_populates="worker", lazy="selectin", cascade="all, delete-orphan")


class ContractorAssignment(Base, TimestampMixin):
    """
    Engagement of a contractor company (and individual workers) for a specific Work Item or Job Card.
    Tracks scope, timeline, internal supervision, and quality sign-off verification.
    """
    __tablename__ = "contractor_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    
    contractor_company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contractor_companies.id"), nullable=False, index=True)
    work_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("work_items.id"), nullable=True, index=True)
    job_card_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("job_cards.id"), nullable=True, index=True)
    
    work_scope: Mapped[str] = mapped_column(String(2000), nullable=False)
    assignment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completion_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Internal Staff Accountability
    supervisor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    verified_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(50), default=ContractorVerificationStatus.PENDING.value, index=True)
    
    # Performance & Financials
    performance_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1 to 5 stars
    performance_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost_agreed: Mapped[float] = mapped_column(Float, default=0.0)
    actual_cost: Mapped[float] = mapped_column(Float, default=0.0)

    company = relationship("ContractorCompany", back_populates="assignments")
    work_item = relationship("WorkItem", foreign_keys=[work_item_id], lazy="selectin")
    job_card = relationship("JobCard", foreign_keys=[job_card_id], lazy="selectin")
    supervisor = relationship("User", foreign_keys=[supervisor_id], lazy="selectin")
    verified_by = relationship("User", foreign_keys=[verified_by_id], lazy="selectin")
    
    assigned_workers = relationship("ContractorWorkerAssignment", back_populates="assignment", lazy="selectin", cascade="all, delete-orphan")


class ContractorWorkerAssignment(Base, TimestampMixin):
    """
    Many-to-many junction linking specific external workers to a contractor assignment.
    """
    __tablename__ = "contractor_worker_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contractor_assignments.id"), nullable=False, index=True)
    contractor_worker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contractor_workers.id"), nullable=False, index=True)
    role_on_site: Mapped[str | None] = mapped_column(String(100), nullable=True)

    assignment = relationship("ContractorAssignment", back_populates="assigned_workers")
    worker = relationship("ContractorWorker", back_populates="assignments")


class ContractorDocument(Base, TimestampMixin):
    """
    Compliance documentation, safety inductions, liability insurance certificates, trade licenses.
    """
    __tablename__ = "contractor_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contractor_company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("contractor_companies.id"), nullable=True, index=True)
    contractor_worker_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("contractor_workers.id"), nullable=True, index=True)
    
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)  # INSURANCE, SAFETY_INDUCTION, CERTIFICATE, CONTRACT, ID_PROOF
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    company = relationship("ContractorCompany", back_populates="documents")
    worker = relationship("ContractorWorker", back_populates="documents")
