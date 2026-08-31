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


class AssetType(str, enum.Enum):
    MACHINE = "MACHINE"
    EQUIPMENT = "EQUIPMENT"
    VEHICLE = "VEHICLE"
    TOOL = "TOOL"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    IT_EQUIPMENT = "IT_EQUIPMENT"
    PRODUCTION_EQUIPMENT = "PRODUCTION_EQUIPMENT"
    OTHER = "OTHER"


class AssetStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    IN_USE = "IN_USE"
    RESERVED = "RESERVED"
    UNDER_MAINTENANCE = "UNDER_MAINTENANCE"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"
    INACTIVE = "INACTIVE"
    RETIRED = "RETIRED"


class AssetCriticality(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Asset(Base, TimestampMixin):
    """
    Authoritative registered physical asset entity.
    Maintains physical identity, lifecycle, location history, and custody.
    """
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_tag: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False, default=AssetType.EQUIPMENT.value, index=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    
    # Manufacturer & Model specifications
    manufacturer: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    
    # Ownership & Custody
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True)
    custodian_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # Spatial Location (Hierarchical link + text fallback)
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True, index=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Operational Status & Criticality
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=AssetStatus.AVAILABLE.value, index=True)
    criticality: Mapped[str] = mapped_column(String(50), default=AssetCriticality.MEDIUM.value)
    
    # Financial & Lifecycle Dates
    commissioned_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retired_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    purchase_cost: Mapped[float | None] = mapped_column(Float, default=0.0)
    current_value: Mapped[float | None] = mapped_column(Float, default=0.0)
    
    # Identification & Barcodes
    barcode_or_nfc: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    specifications: Mapped[dict | None] = mapped_column(JSON, default=dict)
    
    # Archival state
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Optional Link to Resource Machine
    machine_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("machines.id"), nullable=True, index=True)

    # Relationships
    department = relationship("Department", lazy="selectin")
    location_ref = relationship("Location", lazy="selectin")
    custodian = relationship("User", foreign_keys=[custodian_id], lazy="selectin")
    machine = relationship("Machine", foreign_keys=[machine_id], lazy="selectin")
    
    activity_logs = relationship(
        "AssetActivityLog", back_populates="asset", lazy="selectin", cascade="all, delete-orphan", order_by="AssetActivityLog.created_at.desc()"
    )
    maintenance_records = relationship(
        "AssetMaintenanceRecord", back_populates="asset", lazy="selectin", cascade="all, delete-orphan", order_by="AssetMaintenanceRecord.service_date.desc()"
    )
    attachments = relationship(
        "AssetAttachment", back_populates="asset", lazy="selectin", cascade="all, delete-orphan"
    )


class AssetActivityLog(Base, TimestampMixin):
    """
    Immutable audit history of asset movements, custody transfers, and status transitions.
    """
    __tablename__ = "asset_activity_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # STATUS_CHANGE, LOCATION_CHANGE, CUSTODIAN_CHANGE, MAINTENANCE, ARCHIVE, RESTORE
    previous_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    new_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    asset = relationship("Asset", back_populates="activity_logs")
    user = relationship("User", lazy="selectin")


class AssetMaintenanceRecord(Base, TimestampMixin):
    """
    Historical maintenance events, service logs, and meter readings.
    """
    __tablename__ = "asset_maintenance_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    work_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("work_items.id"), nullable=True, index=True)
    job_card_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("job_cards.id"), nullable=True, index=True)
    maintenance_type: Mapped[str] = mapped_column(String(50), default="PREVENTIVE")  # PREVENTIVE, CORRECTIVE, CALIBRATION, OVERHAUL, INSPECTION
    performed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    service_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    meter_reading: Mapped[float | None] = mapped_column(Float, default=0.0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    summary: Mapped[str] = mapped_column(String(2000), nullable=False)

    asset = relationship("Asset", back_populates="maintenance_records")


class AssetAttachment(Base, TimestampMixin):
    """
    Asset documentation, manuals, calibration sheets, and photos.
    """
    __tablename__ = "asset_attachments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(100), default="application/octet-stream")
    file_size_kb: Mapped[float] = mapped_column(Float, default=0.0)

    asset = relationship("Asset", back_populates="attachments")
