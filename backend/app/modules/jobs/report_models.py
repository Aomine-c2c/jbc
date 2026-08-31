import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, DateTime, Float, Integer, func, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


# ── Progress Update Types ──────────────────────────────────────
PROGRESS_UPDATE_TYPES = [
    "WORK_START",   # Technician logs start of physical work
    "PROGRESS",     # Mid-job progress note
    "PAUSE",        # Work paused (hold reason required)
    "RESUME",       # Work resumed after a pause
    "COMPLETION",   # Technician marks work done
]

# ── Material / Resource Categories ────────────────────────────
MATERIAL_CATEGORIES = [
    "SPARE_PART",
    "CONSUMABLE",
    "MATERIAL",
    "TOOL",
    "EQUIPMENT",
    "OTHER",
]

# ── Attachment Categories ──────────────────────────────────────
ATTACHMENT_CATEGORIES = [
    "PHOTO",
    "DOCUMENT",
    "SKETCH",
    "CERTIFICATE",
    "MEASUREMENT_SHEET",
    "OTHER",
]

# ── Department Schema Types (must match dept_schemas.py) ──────
DEPT_SCHEMA_TYPES = [
    "MECHANICAL",
    "INSTRUMENTATION",
    "IT_SYSTEMS",
    "ELECTRICAL",
    "CIVIL",
    "HSE",
    "STORES",
    "GENERIC",
]


class JobReport(Base):
    """
    First-class execution report associated 1:1 with a JobCard.
    Auto-created when the Job Card transitions to IN_PROGRESS.
    Locked (is_locked=True) permanently when the Job Card is CLOSED.
    Post-closure corrections must go through JobReportAmendment.
    """
    __tablename__ = "job_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_cards.id"), nullable=False, unique=True, index=True
    )

    # ── Immutability ───────────────────────────────────────────
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # ── Core Execution Data ────────────────────────────────────
    # Fault diagnosis
    fault_found: Mapped[str | None] = mapped_column(Text, nullable=True)
    fault_code: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # What was done
    corrective_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    technical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Outcome & forward planning
    observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    follow_up_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Labour Summary ─────────────────────────────────────────
    actual_labour_hours: Mapped[float] = mapped_column(Float, default=0.0)
    actual_cost: Mapped[float] = mapped_column(Float, default=0.0)

    # ── Department-Specific Configurable Fields ────────────────
    # One of DEPT_SCHEMA_TYPES above — determines how dept_specific_data is interpreted
    dept_schema_type: Mapped[str] = mapped_column(String(50), nullable=False, default="GENERIC")
    # Free-form JSON validated by dept_schemas.py discriminated union at service layer
    dept_specific_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # ── Timestamps ────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ──────────────────────────────────────────
    job_card = relationship("JobCard", back_populates="job_report", uselist=False)
    progress_updates = relationship(
        "JobReportProgressUpdate",
        back_populates="report",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="JobReportProgressUpdate.timestamp.asc()",
    )
    materials = relationship(
        "JobReportMaterial",
        back_populates="report",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    attachments = relationship(
        "JobReportAttachment",
        back_populates="report",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    amendments = relationship(
        "JobReportAmendment",
        back_populates="report",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="JobReportAmendment.created_at.desc()",
    )


class JobReportProgressUpdate(Base):
    """
    Timestamped progress event during job execution.
    Forms a full execution timeline (start → pauses → completion).
    """
    __tablename__ = "job_report_progress_updates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_reports.id"), nullable=False, index=True)
    reported_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # WORK_START | PROGRESS | PAUSE | RESUME | COMPLETION
    update_type: Mapped[str] = mapped_column(String(50), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # 0–100 completion estimate at time of this update
    percentage_complete: Mapped[int] = mapped_column(Integer, default=0)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Required when update_type == PAUSE
    hold_reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    report = relationship("JobReport", back_populates="progress_updates")


class JobReportMaterial(Base):
    """
    Structured record of materials, spares, tools, or equipment used during the job.
    Replaces the free-text `equipment_used` field with individual line items.
    """
    __tablename__ = "job_report_materials"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_reports.id"), nullable=False, index=True)

    # SPARE_PART | CONSUMABLE | MATERIAL | TOOL | EQUIPMENT | OTHER
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="SPARE_PART")
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    item_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    quantity: Mapped[float] = mapped_column(Float, default=1.0)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g. kg, m, pcs, L
    unit_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    report = relationship("JobReport", back_populates="materials")


class JobReportAttachment(Base):
    """
    File attachment categorised by type (photo, document, certificate, etc.).
    More structured than the existing JobCardAttachment.
    """
    __tablename__ = "job_report_attachments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_reports.id"), nullable=False, index=True)
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # PHOTO | DOCUMENT | SKETCH | CERTIFICATE | MEASUREMENT_SHEET | OTHER
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="PHOTO")
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size_kb: Mapped[float] = mapped_column(Float, default=0.0)
    caption: Mapped[str | None] = mapped_column(String(500), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    report = relationship("JobReport", back_populates="attachments")


class JobReportAmendment(Base):
    """
    Immutable post-closure correction record.
    When a JobReport is locked (is_locked=True), direct edits are blocked.
    All corrections must create one of these records, which captures the
    old value, new value, reason, and optional second-level approval.
    """
    __tablename__ = "job_report_amendments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_reports.id"), nullable=False, index=True)
    amended_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    amendment_reason: Mapped[str] = mapped_column(Text, nullable=False)

    # PENDING | APPROVED | REJECTED
    approval_status: Mapped[str] = mapped_column(String(20), nullable=False, default="APPROVED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    report = relationship("JobReport", back_populates="amendments")
