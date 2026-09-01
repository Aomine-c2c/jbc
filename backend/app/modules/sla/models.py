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


class SLAPriorityConfig(Base, TimestampMixin):
    """
    Configurable Priority Level definitions.
    Replaces hard-coded enum values with administrator-managed records
    that define default SLA response/completion targets per priority level.
    """
    __tablename__ = "sla_priority_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    # e.g. LOW, NORMAL, HIGH, CRITICAL — must match SLAPriority values
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    color_code: Mapped[str | None] = mapped_column(String(20), nullable=True)  # e.g. "#FF0000"

    # Default SLA targets in minutes (overridden by SLAPolicy if matched)
    default_response_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    default_completion_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=480)

    # Ordering for UI display (lower = higher urgency)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class SLAPolicy(Base, TimestampMixin):
    """
    Configurable SLA Policy matrix.
    Defines response & completion targets, warning thresholds, and escalation rules.
    NULL fields act as wildcards during policy matching (scored by specificity).
    """
    __tablename__ = "sla_policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Matching Criteria (NULL = Wildcard) ─────────────────────
    priority: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    work_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    request_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True, index=True)
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True, index=True)
    asset_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # ── Target Milestones (in Minutes) ──────────────────────────
    response_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    completion_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=480)

    # ── Warning Thresholds (percentage of time elapsed) ─────────
    # Response warning fires when this % of response window has elapsed
    warning_threshold_percentage: Mapped[int] = mapped_column(Integer, nullable=False, default=80)
    # Completion warning fires when this % of completion window has elapsed
    completion_warning_threshold_percentage: Mapped[int] = mapped_column(Integer, nullable=False, default=80)

    # ── Notification Spam Prevention ─────────────────────────────
    # Minimum gap between repeat notifications for the same tracker & trigger type
    notification_cooldown_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)

    # ── Multilevel Escalation Rules ──────────────────────────────
    escalation_rules: Mapped[list | None] = mapped_column(JSON, default=list)
    # Example:
    # [
    #   {"level": 1, "trigger": "RESPONSE_WARNING", "after_percentage": 80, "target_role": "Supervisor", "notify_channel": "PUSH"},
    #   {"level": 2, "trigger": "RESPONSE_BREACH", "after_percentage": 100, "target_role": "HOD", "notify_channel": "SMS_PUSH"},
    #   {"level": 3, "trigger": "COMPLETION_BREACH", "after_percentage": 100, "target_role": "Plant_Manager", "notify_channel": "ALL"}
    # ]

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    department = relationship("Department", lazy="selectin")
    location = relationship("Location", lazy="selectin", foreign_keys=[location_id])
    trackers = relationship("SLATracker", back_populates="policy", lazy="selectin")


class SLATracker(Base, TimestampMixin):
    """
    Live operational tracker recording SLA milestones, paused periods,
    breach statuses, and escalation levels for individual work units.
    """
    __tablename__ = "sla_trackers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sla_policies.id"), nullable=True, index=True)

    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    resource_reference: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[str] = mapped_column(String(50), nullable=False, default=SLAPriority.NORMAL.value, index=True)
    request_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Organizational Context
    department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True, index=True)
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True, index=True)

    # Timezone (IANA format, e.g. "Africa/Harare"). Deadlines are always stored in UTC.
    # This field is for display/reporting purposes only.
    timezone: Mapped[str] = mapped_column(String(100), nullable=False, default="UTC")

    # ── State & Health ───────────────────────────────────────────
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=SLAStatus.CREATED.value, index=True)
    health: Mapped[str] = mapped_column(String(50), nullable=False, default=SLAHealth.ON_TRACK.value, index=True)

    # ── Time Targets (UTC) ───────────────────────────────────────
    target_response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    target_completion_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_completion_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Pause Handling ───────────────────────────────────────────
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_paused_minutes: Mapped[float] = mapped_column(Float, default=0.0)

    # ── Escalation & Breach Info ─────────────────────────────────
    current_escalation_level: Mapped[int] = mapped_column(Integer, default=0)
    breach_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    history_logs: Mapped[list | None] = mapped_column(JSON, default=list)

    # ── Warning Cooldown Tracking ────────────────────────────────
    # Stores the UTC timestamp of the last time a response/completion WARNING was fired.
    # Used to prevent repeated warning notifications within the cooldown window.
    response_warning_fired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completion_warning_fired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    policy = relationship("SLAPolicy", back_populates="trackers")
    department = relationship("Department", lazy="selectin")
    location = relationship("Location", lazy="selectin", foreign_keys=[location_id])
    escalation_logs = relationship(
        "SLAEscalationLog", back_populates="tracker", lazy="selectin",
        cascade="all, delete-orphan", order_by="SLAEscalationLog.created_at.desc()"
    )


class SLAEscalationLog(Base, TimestampMixin):
    """
    Immutable record of SLA escalation dispatches to prevent duplicate alerts.
    Each (tracker_id, escalation_level, trigger_type) combination is recorded once.
    The fired_at timestamp supports cooldown window queries for warning-type triggers.
    """
    __tablename__ = "sla_escalation_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tracker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sla_trackers.id"), nullable=False, index=True)

    escalation_level: Mapped[int] = mapped_column(Integer, nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    notified_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notified_user_ids: Mapped[list | None] = mapped_column(JSON, default=list)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Explicit UTC timestamp of when this escalation was dispatched (for cooldown queries)
    fired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    tracker = relationship("SLATracker", back_populates="escalation_logs")
