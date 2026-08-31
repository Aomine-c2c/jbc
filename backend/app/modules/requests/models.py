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


class RequestType(str, enum.Enum):
    MACHINE_REQUEST = "MACHINE_REQUEST"
    EQUIPMENT_REQUEST = "EQUIPMENT_REQUEST"
    VEHICLE_REQUEST = "VEHICLE_REQUEST"
    MATERIAL_REQUEST = "MATERIAL_REQUEST"
    PERSONNEL_REQUEST = "PERSONNEL_REQUEST"
    CONTRACTOR_REQUEST = "CONTRACTOR_REQUEST"
    OTHER = "OTHER"


class RequestStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    AWAITING_FULFILLMENT = "AWAITING_FULFILLMENT"
    PARTIALLY_FULFILLED = "PARTIALLY_FULFILLED"
    FULFILLED = "FULFILLED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    RETURNED_FOR_CORRECTION = "RETURNED_FOR_CORRECTION"


class FulfillmentStatus(str, enum.Enum):
    UNALLOCATED = "UNALLOCATED"
    AWAITING_FULFILLMENT = "AWAITING_FULFILLMENT"
    PARTIALLY_FULFILLED = "PARTIALLY_FULFILLED"
    FULFILLED = "FULFILLED"
    CLOSED = "CLOSED"


class OperationalRequest(Base, TimestampMixin):
    """
    Authoritative Universal Operational Request entity.
    Represents requisitions for machinery, equipment, vehicles, warehouse materials, personnel, and contractors.
    """
    __tablename__ = "operational_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    request_type: Mapped[str] = mapped_column(String(50), nullable=False, default=RequestType.OTHER.value, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(2000), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=1, index=True)  # 0: Low, 1: Medium, 2: High, 3: Urgent, 4: Critical
    
    # Workflow & Fulfillment Lifecycle
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=RequestStatus.DRAFT.value, index=True)
    fulfillment_status: Mapped[str] = mapped_column(String(50), nullable=False, default=FulfillmentStatus.UNALLOCATED.value, index=True)
    
    # Ownership & Organizational Context
    requester_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True)
    collaborating_department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    
    # Spatial Location (Hierarchical link + text fallback)
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True, index=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Schedule & Timeline
    required_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    required_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_duration_hours: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Financial Costing
    cost_centre: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    actual_cost: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Cross-Domain Links
    work_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("work_items.id"), nullable=True, index=True)
    job_card_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("job_cards.id"), nullable=True, index=True)
    machine_requisition_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("machine_requisitions.id"), nullable=True, index=True)
    
    # Approval State (Explicitly separated from fulfillment)
    approver_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Fulfillment State (Stores, Dispatcher, HR or Supervisor execution)
    fulfillment_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    fulfilled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Flexible Type-Specific Payloads (Machine type/hours, operator required, safety gear, skills, scopes)
    type_specific_data: Mapped[dict | None] = mapped_column(JSON, default=dict)

    # Relationships
    requester = relationship("User", foreign_keys=[requester_id], lazy="selectin")
    department = relationship("Department", foreign_keys=[department_id], lazy="selectin")
    collaborating_department = relationship("Department", foreign_keys=[collaborating_department_id], lazy="selectin")
    location_ref = relationship("Location", foreign_keys=[location_id], lazy="selectin")
    work_item = relationship("WorkItem", foreign_keys=[work_item_id], lazy="selectin")
    job_card = relationship("JobCard", foreign_keys=[job_card_id], lazy="selectin")
    approver = relationship("User", foreign_keys=[approver_id], lazy="selectin")
    fulfillment_user = relationship("User", foreign_keys=[fulfillment_user_id], lazy="selectin")

    material_items = relationship(
        "RequestMaterialItem", back_populates="request", lazy="selectin", cascade="all, delete-orphan"
    )
    action_logs = relationship(
        "RequestActionLog", back_populates="request", lazy="selectin", cascade="all, delete-orphan", order_by="RequestActionLog.created_at.desc()"
    )
    comments = relationship(
        "RequestComment", back_populates="request", lazy="selectin", cascade="all, delete-orphan", order_by="RequestComment.created_at.desc()"
    )
    attachments = relationship(
        "RequestAttachment", back_populates="request", lazy="selectin", cascade="all, delete-orphan"
    )


class RequestMaterialItem(Base, TimestampMixin):
    """
    Line items for Material and Spare Part requisitions.
    Tracks quantities requested, warehouse store issuance, and returns.
    """
    __tablename__ = "request_material_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("operational_requests.id"), nullable=False, index=True)
    material_name: Mapped[str] = mapped_column(String(255), nullable=False)
    part_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    quantity_requested: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    unit: Mapped[str] = mapped_column(String(50), default="units")
    store_location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    quantity_issued: Mapped[float] = mapped_column(Float, default=0.0)
    quantity_returned: Mapped[float] = mapped_column(Float, default=0.0)
    unit_cost: Mapped[float] = mapped_column(Float, default=0.0)

    request = relationship("OperationalRequest", back_populates="material_items")


class RequestActionLog(Base, TimestampMixin):
    """
    Immutable audit trail for Request lifecycle state transitions and fulfillment actions.
    """
    __tablename__ = "request_action_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("operational_requests.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    request = relationship("OperationalRequest", back_populates="action_logs")
    user = relationship("User", lazy="selectin")


class RequestComment(Base, TimestampMixin):
    """
    Operational discussions and clarification notes on requests.
    """
    __tablename__ = "request_comments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("operational_requests.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    comment: Mapped[str] = mapped_column(String(2000), nullable=False)

    request = relationship("OperationalRequest", back_populates="comments")
    user = relationship("User", lazy="selectin")


class RequestAttachment(Base, TimestampMixin):
    """
    Specifications, safety certificates, quotes, and delivery notes.
    """
    __tablename__ = "request_attachments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("operational_requests.id"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(100), default="application/octet-stream")
    file_size_kb: Mapped[float] = mapped_column(Float, default=0.0)

    request = relationship("OperationalRequest", back_populates="attachments")
