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
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.db.mixins import TimestampMixin


class MaterialRequirementStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    PARTIALLY_ISSUED = "PARTIALLY_ISSUED"
    ISSUED = "ISSUED"
    IN_USE = "IN_USE"
    CONSUMED = "CONSUMED"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"


class MaterialTransactionType(str, enum.Enum):
    ISSUE = "ISSUE"
    USAGE = "USAGE"
    RETURN = "RETURN"
    ADJUSTMENT = "ADJUSTMENT"
    ERP_SYNC = "ERP_SYNC"


class MaterialCatalogItem(Base, TimestampMixin):
    """
    Shared operational catalog of spare parts, consumables, and raw materials.
    Can be synchronized with or linked to external ERP/Inventory master items.
    """
    __tablename__ = "material_catalog"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    part_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    unit_of_measure: Mapped[str] = mapped_column(String(50), default="units")
    default_unit_cost: Mapped[float] = mapped_column(Float, default=0.0)
    primary_store: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    external_erp_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    requirements = relationship("MaterialRequirement", back_populates="catalog_item", lazy="selectin")
    transactions = relationship("MaterialTransaction", back_populates="catalog_item", lazy="selectin")


class MaterialRequirement(Base, TimestampMixin):
    """
    Authoritative operational record of materials planned, requested, approved,
    issued, used on site, and returned to warehouse stores.
    """
    __tablename__ = "material_requirements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    
    catalog_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("material_catalog.id"), nullable=True, index=True)
    material_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    part_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit: Mapped[str] = mapped_column(String(50), default="units")
    unit_cost: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Quantities Tracking Lifecycle
    quantity_required: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    quantity_approved: Mapped[float] = mapped_column(Float, default=0.0)
    quantity_issued: Mapped[float] = mapped_column(Float, default=0.0)
    quantity_used: Mapped[float] = mapped_column(Float, default=0.0)
    quantity_returned: Mapped[float] = mapped_column(Float, default=0.0)
    
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=MaterialRequirementStatus.REQUESTED.value, index=True)
    store_location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    purpose: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    
    # Cross-Domain Links
    work_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("work_items.id"), nullable=True, index=True)
    job_card_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("job_cards.id"), nullable=True, index=True)
    asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True, index=True)
    request_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("operational_requests.id"), nullable=True, index=True)
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True)
    
    # User Accountability & Sign-offs
    requester_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    approver_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_reservation_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    catalog_item = relationship("MaterialCatalogItem", back_populates="requirements", lazy="selectin")
    work_item = relationship("WorkItem", foreign_keys=[work_item_id], lazy="selectin")
    job_card = relationship("JobCard", foreign_keys=[job_card_id], lazy="selectin")
    asset = relationship("Asset", foreign_keys=[asset_id], lazy="selectin")
    request = relationship("OperationalRequest", foreign_keys=[request_id], lazy="selectin")
    department = relationship("Department", foreign_keys=[department_id], lazy="selectin")
    requester = relationship("User", foreign_keys=[requester_id], lazy="selectin")
    approver = relationship("User", foreign_keys=[approver_id], lazy="selectin")

    transactions = relationship(
        "MaterialTransaction", back_populates="requirement", lazy="selectin", cascade="all, delete-orphan", order_by="MaterialTransaction.created_at.desc()"
    )


class MaterialTransaction(Base, TimestampMixin):
    """
    Immutable movement ledger of material transactions:
    Stores Issue, Site Consumption/Usage, Warehouse Returns, and ERP sync receipts.
    """
    __tablename__ = "material_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("material_requirements.id"), nullable=True, index=True)
    catalog_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("material_catalog.id"), nullable=True, index=True)
    
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # ISSUE, USAGE, RETURN, ADJUSTMENT, ERP_SYNC
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), default="units")
    unit_cost: Mapped[float] = mapped_column(Float, default=0.0)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)
    
    store_location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    batch_or_serial: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Storekeeper & Recipient Tracking
    issued_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    received_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    external_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    requirement = relationship("MaterialRequirement", back_populates="transactions")
    catalog_item = relationship("MaterialCatalogItem", back_populates="transactions")
    issued_by = relationship("User", foreign_keys=[issued_by_id], lazy="selectin")
    received_by = relationship("User", foreign_keys=[received_by_id], lazy="selectin")
