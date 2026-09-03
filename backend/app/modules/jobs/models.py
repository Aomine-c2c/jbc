import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, DateTime, Float, func, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from app.db.mixins import TimestampMixin, SoftDeleteMixin

# Import report models to ensure they are registered with the Base metadata
# (avoids circular imports; models are not directly referenced here)
import app.modules.jobs.report_models  # noqa: F401


# ── Work Package State Machine ─────────────────────────────────
WORK_PACKAGE_STATES = [
    "DRAFT", "SUBMITTED", "APPROVED", "IN_PROGRESS", "ON_HOLD",
    "COMPLETED", "VERIFIED", "REJECTED", "CANCELLED",
]

WORK_PACKAGE_TRANSITIONS = {
    "DRAFT": {"submit": "SUBMITTED", "cancel": "CANCELLED"},
    "SUBMITTED": {"approve": "APPROVED", "reject": "REJECTED", "cancel": "CANCELLED"},
    "APPROVED": {"start": "IN_PROGRESS", "reject": "REJECTED", "cancel": "CANCELLED"},
    "IN_PROGRESS": {"hold": "ON_HOLD", "complete": "COMPLETED", "cancel": "CANCELLED"},
    "ON_HOLD": {"start": "IN_PROGRESS", "resume": "IN_PROGRESS", "cancel": "CANCELLED"},
    "COMPLETED": {"verify": "VERIFIED", "start": "IN_PROGRESS"},  # rework
    "VERIFIED": {},
    "REJECTED": {"submit": "SUBMITTED"},
    "CANCELLED": {},
}


def validate_wp_transition(from_state: str, action: str) -> str:
    """Return the target state for a valid WP transition, or raise ValueError."""
    transitions = WORK_PACKAGE_TRANSITIONS.get(from_state, {})
    if action not in transitions:
        raise ValueError(f"Cannot {action} work package from state {from_state}")
    return transitions[action]


# Work Package terminal states — parent JC cannot close unless all WPs are in one of these
WP_TERMINAL_STATES = {"COMPLETED", "VERIFIED", "CANCELLED", "REJECTED"}

# Collaboration roles
COLLABORATION_ROLES = ["REQUESTING", "RESPONSIBLE", "SUPPORTING", "ASSIGNED", "EXTERNAL_CONTRACTOR"]

# Package types
WORK_PACKAGE_TYPES = [
    "ELECTRICAL", "MECHANICAL", "INSTRUMENTATION", "IT_SYSTEMS", "CIVIL",
    "HSE", "STORES", "PROCUREMENT", "PRODUCTION", "WORKSHOP", "FINANCE", "OTHER",
]


# ── Job Card State Machine ─────────────────────────────────────
JOB_CARD_STATES = [
    "DRAFT", "SUBMITTED", "PENDING_APPROVAL", "RETURNED", "REJECTED",
    "APPROVED", "PLANNING", "ASSIGNED", "IN_PROGRESS", "ON_HOLD",
    "COMPLETED", "PENDING_REVIEW", "VERIFIED", "CLOSED", "CANCELLED",
]

# Full Lifecycle Transitions
VALID_TRANSITIONS = {
    "DRAFT": {
        "submit": "SUBMITTED",
        "cancel": "CANCELLED",
    },
    "SUBMITTED": {
        "submit": "PENDING_APPROVAL",
        "approve": "APPROVED",
        "reject": "REJECTED",
        "return": "RETURNED",
        "cancel": "CANCELLED",
    },
    "PENDING_APPROVAL": {
        "approve": "APPROVED",
        "reject": "REJECTED",
        "return": "RETURNED",
        "cancel": "CANCELLED",
    },
    "RETURNED": {
        "submit": "SUBMITTED",
        "cancel": "CANCELLED",
    },
    "REJECTED": {
        "submit": "SUBMITTED",
        "cancel": "CANCELLED",
    },
    "APPROVED": {
        "plan": "PLANNING",
        "assign": "ASSIGNED",
        "reject": "REJECTED",
        "cancel": "CANCELLED",
    },
    "PLANNING": {
        "assign": "ASSIGNED",
        "hold": "ON_HOLD",
        "cancel": "CANCELLED",
    },
    "ASSIGNED": {
        "start": "IN_PROGRESS",
        "hold": "ON_HOLD",
        "reject": "REJECTED",
        "cancel": "CANCELLED",
    },
    "IN_PROGRESS": {
        "complete": "COMPLETED",
        "start": "IN_PROGRESS",  # idempotent start/heartbeat
        "hold": "ON_HOLD",
        "cancel": "CANCELLED",
    },
    "ON_HOLD": {
        "start": "IN_PROGRESS",
        "resume": "IN_PROGRESS",
        "cancel": "CANCELLED",
    },
    "COMPLETED": {
        "verify": "VERIFIED",
        "review": "PENDING_REVIEW",
        "start": "IN_PROGRESS",  # rework transition
        "return": "RETURNED",
        "close": "CLOSED",
    },
    "PENDING_REVIEW": {
        "verify": "VERIFIED",
        "start": "IN_PROGRESS",  # rework transition
        "close": "CLOSED",
    },
    "VERIFIED": {
        "close": "CLOSED",
        "reject": "REJECTED",
    },
    "CLOSED": {},
    "CANCELLED": {},
}


def validate_transition(from_state: str, action: str) -> str:
    """Return the target state for a valid transition, or raise ValueError."""
    transitions = VALID_TRANSITIONS.get(from_state, {})
    if action not in transitions:
        raise ValueError(f"Cannot {action} job card from state {from_state}")
    return transitions[action]


class JobCard(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "job_cards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT")
    priority: Mapped[int] = mapped_column(default=0)
    
    # Department & Workshop Identification
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False)
    # Cross-department collaboration: the department that originally requested the work
    requesting_department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    # The department primarily responsible for executing / delivering the work
    responsible_department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    # Optional external contractor info
    external_contractor: Mapped[str | None] = mapped_column(String(500), nullable=True)
    workshop_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True, index=True
    )
    plant_area: Mapped[str | None] = mapped_column(String(255), nullable=True)
    machine_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("machines.id"), nullable=True)

    # Requester Specifications
    creator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    required_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    job_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    maintenance_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reported_issue: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    job_instruction: Mapped[str | None] = mapped_column(String(4000), nullable=True)

    # Approvals
    approver_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Planning & Assignment
    supervisor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_personnel: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    estimated_hours: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)

    # Execution Telemetry
    actual_start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    downtime_hours: Mapped[float] = mapped_column(Float, default=0.0)

    # Technical Report & Labor Costing
    action_taken: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    labour_details: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    completion_notes: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    
    # Extended Completion Data (v1.2)
    equipment_used: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    observations: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    problems_encountered: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    recommendations: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    
    # Requester Confirmation & Sign-off
    requester_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    requester_notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    requester_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Supervisor QA Verification
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Formal Closure
    closure_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Safety Clearance & HSE Gate
    safety_cleared: Mapped[bool] = mapped_column(Boolean, default=False)
    safety_cleared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    safety_cleared_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    safety_clearance_notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    loto_tag_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # User Relationships
    creator = relationship("User", foreign_keys=[creator_id], lazy="selectin")
    approver = relationship("User", foreign_keys=[approver_id], lazy="selectin")
    supervisor = relationship("User", foreign_keys=[supervisor_id], lazy="selectin")
    closed_by = relationship("User", foreign_keys=[closed_by_id], lazy="selectin")

    # Relationships
    attachments = relationship("JobCardAttachment", back_populates="job_card", lazy="selectin", cascade="all, delete-orphan")
    comments = relationship("JobCardComment", back_populates="job_card", lazy="selectin", cascade="all, delete-orphan")
    action_logs = relationship("JobCardActionLog", back_populates="job_card", lazy="selectin", cascade="all, delete-orphan", order_by="JobCardActionLog.created_at.desc()")
    parts = relationship("JobCardPart", back_populates="job_card", lazy="selectin", cascade="all, delete-orphan")
    labour_entries = relationship("JobCardLabour", back_populates="job_card", lazy="selectin", cascade="all, delete-orphan")
    execution_events = relationship("JobCardExecutionEvent", back_populates="job_card", lazy="selectin", cascade="all, delete-orphan", order_by="JobCardExecutionEvent.timestamp.asc()")
    amendments = relationship("JobCardAmendment", back_populates="job_card", lazy="selectin", cascade="all, delete-orphan", order_by="JobCardAmendment.created_at.desc()")
    # Cross-department collaboration
    collaborators = relationship("JobCardCollaborator", back_populates="job_card", lazy="selectin", cascade="all, delete-orphan")
    work_packages = relationship("WorkPackage", back_populates="job_card", lazy="selectin", cascade="all, delete-orphan", foreign_keys="WorkPackage.job_card_id", order_by="WorkPackage.package_number.asc()")
    # V1.3: 1:1 Job Execution Report
    job_report = relationship("JobReport", back_populates="job_card", uselist=False, lazy="selectin", cascade="all, delete-orphan")
    location_ref = relationship("Location", foreign_keys=[location_id], lazy="selectin")


class JobCardPart(Base, TimestampMixin):
    __tablename__ = "job_card_parts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_card_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_cards.id"), nullable=False)
    part_name: Mapped[str] = mapped_column(String(255), nullable=False)
    part_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    quantity: Mapped[float] = mapped_column(Float, default=1.0)
    unit_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_material: Mapped[bool] = mapped_column(Boolean, default=False)  # True for consumable materials, False for Spares

    job_card = relationship("JobCard", back_populates="parts")


class JobCardLabour(Base, TimestampMixin):
    __tablename__ = "job_card_labour"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_card_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_cards.id"), nullable=False)
    technician_name: Mapped[str] = mapped_column(String(255), nullable=False)
    trade: Mapped[str] = mapped_column(String(100), nullable=False, default="Mechanical Fitter")
    hours_spent: Mapped[float] = mapped_column(Float, default=0.0)
    hourly_rate: Mapped[float] = mapped_column(Float, default=25.0)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    job_card = relationship("JobCard", back_populates="labour_entries")


class JobCardExecutionEvent(Base):
    __tablename__ = "job_card_execution_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_card_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_cards.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # REQUESTED, APPROVED, ASSIGNED, STARTED, PAUSED, RESUMED, COMPLETED, SUPERVISOR_APPROVED, CLOSED
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    duration_minutes: Mapped[float] = mapped_column(Float, default=0.0)
    operator_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    job_card = relationship("JobCard", back_populates="execution_events")


class JobCardAmendment(Base):
    __tablename__ = "job_card_amendments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_card_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_cards.id"), nullable=False)
    amended_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    new_value: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    amendment_reason: Mapped[str] = mapped_column(String(2000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job_card = relationship("JobCard", back_populates="amendments")


class JobCardAttachment(Base):
    __tablename__ = "job_card_attachments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_card_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_cards.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size_kb: Mapped[float | None] = mapped_column(Float, default=0.0)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job_card = relationship("JobCard", back_populates="attachments")


class JobCardComment(Base):
    __tablename__ = "job_card_comments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_card_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_cards.id"), nullable=False)
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    comment: Mapped[str] = mapped_column(String(4000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job_card = relationship("JobCard", back_populates="comments")


class JobCardActionLog(Base):
    __tablename__ = "job_card_action_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_card_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_cards.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    state_from: Mapped[str | None] = mapped_column(String(50), nullable=True)
    state_to: Mapped[str | None] = mapped_column(String(50), nullable=True)
    details: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job_card = relationship("JobCard", back_populates="action_logs")


# ── Cross-Department Collaboration ────────────────────────────

class JobCardCollaborator(Base, TimestampMixin):
    """Links an additional department to a Job Card with a defined collaboration role."""
    __tablename__ = "job_card_collaborators"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_card_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_cards.id"), nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False)
    # REQUESTING | RESPONSIBLE | SUPPORTING | ASSIGNED | EXTERNAL_CONTRACTOR
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="SUPPORTING")
    added_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    job_card = relationship("JobCard", back_populates="collaborators")


# ── Work Packages ─────────────────────────────────────────────

class WorkPackage(Base, TimestampMixin):
    """
    A child execution unit under a parent Job Card.
    Each WP is owned by a specific department and tracks its own state machine.
    Departments can only mutate their own WPs; parent visibility is read-only for others.
    """
    __tablename__ = "work_packages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_card_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_cards.id"), nullable=False)
    # Auto-numbered per job card e.g. WP-001, WP-002
    package_number: Mapped[str] = mapped_column(String(20), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(4000), nullable=True)

    # ELECTRICAL | MECHANICAL | INSTRUMENTATION | IT_SYSTEMS | CIVIL | HSE | STORES | PROCUREMENT | PRODUCTION | WORKSHOP | FINANCE | OTHER
    package_type: Mapped[str] = mapped_column(String(50), nullable=False, default="OTHER")

    # The department responsible for executing this work package
    owning_department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False)
    responsible_supervisor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_personnel: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Scheduling
    planned_start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    planned_end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_hours: Mapped[float] = mapped_column(Float, default=0.0)
    actual_hours: Mapped[float] = mapped_column(Float, default=0.0)

    # Status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Work Content
    work_performed: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    special_requirements: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    safety_notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    # Dependency: this WP cannot start until prerequisite_wp_id is COMPLETED or VERIFIED
    prerequisite_wp_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("work_packages.id"), nullable=True
    )

    # Relationships
    job_card = relationship("JobCard", back_populates="work_packages", foreign_keys=[job_card_id])
    prerequisite = relationship("WorkPackage", remote_side="WorkPackage.id", foreign_keys=[prerequisite_wp_id])
    action_logs = relationship("WorkPackageActionLog", back_populates="work_package", lazy="selectin", cascade="all, delete-orphan", order_by="WorkPackageActionLog.created_at.asc()")


class WorkPackageActionLog(Base):
    """Immutable per-WP audit log — one entry per state transition or field update."""
    __tablename__ = "work_package_action_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_package_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("work_packages.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    state_from: Mapped[str | None] = mapped_column(String(50), nullable=True)
    state_to: Mapped[str | None] = mapped_column(String(50), nullable=True)
    details: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    work_package = relationship("WorkPackage", back_populates="action_logs")
