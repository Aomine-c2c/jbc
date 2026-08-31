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


class WorkItemType(str, enum.Enum):
    JOB_CARD = "JOB_CARD"
    MAINTENANCE = "MAINTENANCE"
    INSPECTION = "INSPECTION"
    FOLLOW_UP = "FOLLOW_UP"
    OTHER = "OTHER"


class WorkItemStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    VERIFIED = "VERIFIED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    RETURNED = "RETURNED"


class WorkItem(Base, TimestampMixin):
    """
    Unified operational work management unit.
    Represents Job Cards, Scheduled Maintenance, Inspections, Follow-Ups, and Future Work Types.
    """
    __tablename__ = "work_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    work_type: Mapped[str] = mapped_column(String(50), nullable=False, default=WorkItemType.JOB_CARD.value, index=True)
    
    # Core Identifiers & Scope
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=WorkItemStatus.DRAFT.value, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=1, index=True)  # 0: Low, 1: Medium, 2: High, 3: Urgent, 4: Critical
    
    # Organizational & Spatial Placement
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True)
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True, index=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Legacy string fallback
    plant_area: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Asset Link (Physical Assets, Machines, Vehicles, Processing Plant Units)
    asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True, index=True)
    machine_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("machines.id"), nullable=True, index=True)
    
    # Personnel & Ownership
    requester_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    supervisor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    assigned_personnel: Mapped[str | None] = mapped_column(String(500), nullable=True)
    external_contractor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Scheduling & Execution Time
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Estimates & Actual Costs
    estimated_hours: Mapped[float] = mapped_column(Float, default=0.0)
    actual_hours: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    actual_cost: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Relationships to other Work Items & Source Requests
    parent_work_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("work_items.id"), nullable=True, index=True)
    source_request_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    job_card_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("job_cards.id"), nullable=True, index=True)
    
    # Approvals & SLA
    approver_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approval_status: Mapped[str] = mapped_column(String(50), default="NONE")  # NONE, PENDING, APPROVED, REJECTED
    
    sla_hours: Mapped[float] = mapped_column(Float, default=24.0)
    sla_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sla_status: Mapped[str] = mapped_column(String(50), default="WITHIN_SLA")  # WITHIN_SLA, AT_RISK, BREACHED, MET
    
    # Flexible Type-Specific Data (Inspection checklists, PM intervals, calibration readings, follow-up findings)
    type_specific_data: Mapped[dict | None] = mapped_column(JSON, default=dict)

    # Relationships
    department = relationship("Department", foreign_keys=[department_id], lazy="selectin")
    location_ref = relationship("Location", foreign_keys=[location_id], lazy="selectin")
    asset = relationship("Asset", foreign_keys=[asset_id], lazy="selectin")
    machine = relationship("Machine", foreign_keys=[machine_id], lazy="selectin")
    requester = relationship("User", foreign_keys=[requester_id], lazy="selectin")
    supervisor = relationship("User", foreign_keys=[supervisor_id], lazy="selectin")
    job_card = relationship("JobCard", foreign_keys=[job_card_id], lazy="selectin")
    
    parent_item = relationship("WorkItem", remote_side=[id], back_populates="child_items")
    child_items = relationship("WorkItem", back_populates="parent_item", lazy="selectin", cascade="all")
    
    action_logs = relationship("WorkItemActionLog", back_populates="work_item", lazy="selectin", cascade="all, delete-orphan", order_by="WorkItemActionLog.created_at.desc()")
    attachments = relationship("WorkItemAttachment", back_populates="work_item", lazy="selectin", cascade="all, delete-orphan")
    comments = relationship("WorkItemComment", back_populates="work_item", lazy="selectin", cascade="all, delete-orphan")
    parts = relationship("WorkItemPart", back_populates="work_item", lazy="selectin", cascade="all, delete-orphan")


class WorkItemActionLog(Base, TimestampMixin):
    __tablename__ = "work_item_action_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("work_items.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    state_from: Mapped[str | None] = mapped_column(String(50), nullable=True)
    state_to: Mapped[str | None] = mapped_column(String(50), nullable=True)
    details: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    work_item = relationship("WorkItem", back_populates="action_logs")
    user = relationship("User", lazy="selectin")


class WorkItemAttachment(Base, TimestampMixin):
    __tablename__ = "work_item_attachments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("work_items.id"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(100), default="application/octet-stream")
    file_size_kb: Mapped[float] = mapped_column(Float, default=0.0)

    work_item = relationship("WorkItem", back_populates="attachments")


class WorkItemComment(Base, TimestampMixin):
    __tablename__ = "work_item_comments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("work_items.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    comment: Mapped[str] = mapped_column(String(2000), nullable=False)

    work_item = relationship("WorkItem", back_populates="comments")
    user = relationship("User", lazy="selectin")


class WorkItemPart(Base, TimestampMixin):
    __tablename__ = "work_item_parts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("work_items.id"), nullable=False, index=True)
    part_name: Mapped[str] = mapped_column(String(255), nullable=False)
    part_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    quantity: Mapped[float] = mapped_column(Float, default=1.0)
    unit_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_material: Mapped[bool] = mapped_column(Boolean, default=False)

    work_item = relationship("WorkItem", back_populates="parts")
