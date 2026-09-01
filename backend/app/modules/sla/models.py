import uuid
from datetime import datetime, timezone
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
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.db.mixins import TimestampMixin


class SLAPriority(str, enum.Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SLAStatus(str, enum.Enum):
    CREATED = "CREATED"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class SLAHealth(str, enum.Enum):
    ON_TRACK = "ON_TRACK"
    AT_RISK = "AT_RISK"
    BREACHED_RESPONSE = "BREACHED_RESPONSE"
    BREACHED_COMPLETION = "BREACHED_COMPLETION"
    MET = "MET"
    BREACHED_MET = "BREACHED_MET"


class SLAPolicy(Base, TimestampMixin):
    """
    Configurable SLA Policy matrix.
    Defines response & completion targets, warning thresholds, and escalation rules.
    """
    __tablename__ = "sla_policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Matching Criteria (NULL = Wildcard match)
    priority: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)  # LOW, NORMAL, HIGH, CRITICAL
    work_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)  # MAINTENANCE, INSPECTION, JOB_CARD, etc.
    department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True, index=True)
    asset_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Target Milestones (in Minutes)
    response_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    completion_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=480)
    warning_threshold_percentage: Mapped[int] = mapped_column(Integer, nullable=False, default=80)
    
    # Multilevel Escalation Rules
    escalation_rules: Mapped[list | None] = mapped_column(JSON, default=list)
    # Example: [
    #   {"level": 1, "trigger": "RESPONSE_WARNING", "after_percentage": 80, "target_role": "Supervisor", "notify_channel": "PUSH"},
    #   {"level": 2, "trigger": "RESPONSE_BREACH", "after_percentage": 100, "target_role": "HOD", "notify_channel": "SMS_PUSH"},
    #   {"level": 3, "trigger": "COMPLETION_BREACH", "after_percentage": 100, "target_role": "Plant_Manager", "notify_channel": "ALL"}
    # ]

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    department = relationship("Department", lazy="selectin")
    trackers = relationship("SLATracker", back_populates="policy", lazy="selectin")


class SLATracker(Base, TimestampMixin):
    """
    Live operational tracker recording SLA milestones, paused periods,
    breach statuses, and escalation levels for individual work units.
    """
    __tablename__ = "sla_trackers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sla_policies.id"), nullable=True, index=True)
    
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # WORK_ITEM, JOB_CARD, OPERATIONAL_REQUEST
    resource_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    resource_reference: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[str] = mapped_column(String(50), nullable=False, default=SLAPriority.NORMAL.value, index=True)
    department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True, index=True)
    
    # State & Health
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=SLAStatus.CREATED.value, index=True)
    health: Mapped[str] = mapped_column(String(50), nullable=False, default=SLAHealth.ON_TRACK.value, index=True)
    
    # Time Targets (Stored in UTC)
    target_response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    target_completion_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_completion_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Pause Handling
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_paused_minutes: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Escalation & Breach Info
    current_escalation_level: Mapped[int] = mapped_column(Integer, default=0)
    breach_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    history_logs: Mapped[list | None] = mapped_column(JSON, default=list)

    policy = relationship("SLAPolicy", back_populates="trackers")
    department = relationship("Department", lazy="selectin")
    escalation_logs = relationship(
        "SLAEscalationLog", back_populates="tracker", lazy="selectin", cascade="all, delete-orphan", order_by="SLAEscalationLog.created_at.desc()"
    )


class SLAEscalationLog(Base, TimestampMixin):
    """
    Immutable record of SLA escalation dispatches to prevent duplicate alerts.
    """
    __tablename__ = "sla_escalation_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tracker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sla_trackers.id"), nullable=False, index=True)
    
    escalation_level: Mapped[int] = mapped_column(Integer, nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # RESPONSE_WARNING, RESPONSE_BREACH, COMPLETION_WARNING, COMPLETION_BREACH
    notified_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notified_user_ids: Mapped[list | None] = mapped_column(JSON, default=list)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    tracker = relationship("SLATracker", back_populates="escalation_logs")
