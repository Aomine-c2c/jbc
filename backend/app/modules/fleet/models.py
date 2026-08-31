import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, DateTime, Float, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from app.db.mixins import TimestampMixin


# ── Machine State Machine ─────────────────────────────────────
MACHINE_STATES = [
    "AVAILABLE", "RESERVED", "ALLOCATED", "IN_USE", 
    "UNDER_MAINTENANCE", "OUT_OF_SERVICE", "RETIRED"
]
MACHINE_TRANSITIONS = {
    "AVAILABLE": {"reserve": "RESERVED", "allocate": "ALLOCATED", "start_use": "IN_USE", "maintenance": "UNDER_MAINTENANCE", "out_of_service": "OUT_OF_SERVICE", "retire": "RETIRED"},
    "RESERVED": {"allocate": "ALLOCATED", "start_use": "IN_USE", "cancel": "AVAILABLE", "maintenance": "UNDER_MAINTENANCE"},
    "ALLOCATED": {"start_use": "IN_USE", "cancel": "AVAILABLE", "maintenance": "UNDER_MAINTENANCE"},
    "IN_USE": {"return": "AVAILABLE", "maintenance": "UNDER_MAINTENANCE", "out_of_service": "OUT_OF_SERVICE"},
    "UNDER_MAINTENANCE": {"available": "AVAILABLE", "out_of_service": "OUT_OF_SERVICE", "retire": "RETIRED"},
    "OUT_OF_SERVICE": {"available": "AVAILABLE", "maintenance": "UNDER_MAINTENANCE", "retire": "RETIRED"},
    "RETIRED": {}
}


def validate_machine_transition(from_state: str, action: str) -> str:
    if from_state not in MACHINE_TRANSITIONS:
        raise ValueError(f"Unknown machine state: {from_state}")
    if action not in MACHINE_TRANSITIONS[from_state]:
        raise ValueError(f"Cannot {action} machine from state {from_state}")
    return MACHINE_TRANSITIONS[from_state][action]


# ── Full Requisition State Machine ───────────────────────────
REQUISITION_STATES = [
    "DRAFT",
    "SUBMITTED",
    "REVIEWED",
    "APPROVED",
    "AWAITING_ALLOCATION",
    "ALLOCATED",
    "IN_USE",
    "RETURNED",
    "CLOSED",
    "REJECTED",
    "CANCELLED",
    "RETURNED_FOR_CORRECTION",
    "UNAVAILABLE",
    "PARTIALLY_ALLOCATED",
]

REQUISITION_TRANSITIONS = {
    "DRAFT": {
        "submit": "SUBMITTED",
        "cancel": "CANCELLED",
    },
    "SUBMITTED": {
        "review": "REVIEWED",
        "dept_approve": "DEPARTMENT_APPROVAL",
        "dept-approve": "DEPARTMENT_APPROVAL",
        "return_for_correction": "RETURNED_FOR_CORRECTION",
        "reject": "REJECTED",
        "cancel": "CANCELLED",
    },
    "DEPARTMENT_APPROVAL": {
        "equipment_check": "EQUIPMENT_CHECK",
        "equipment-check": "EQUIPMENT_CHECK",
        "approve": "APPROVED",
        "reject": "REJECTED",
        "cancel": "CANCELLED",
    },
    "EQUIPMENT_CHECK": {
        "approve": "APPROVED",
        "allocate": "ALLOCATED",
        "schedule": "SCHEDULED",
        "reject": "REJECTED",
        "cancel": "CANCELLED",
    },
    "REVIEWED": {
        "approve": "APPROVED",
        "return_for_correction": "RETURNED_FOR_CORRECTION",
        "reject": "REJECTED",
        "cancel": "CANCELLED",
    },
    "APPROVED": {
        "await_allocation": "AWAITING_ALLOCATION",
        "allocate": "ALLOCATED",
        "schedule": "SCHEDULED",
        "dispatch": "DISPATCHED",
        "cancel": "CANCELLED",
    },
    "SCHEDULED": {
        "dispatch": "DISPATCHED",
        "allocate": "ALLOCATED",
        "start_use": "IN_USE",
        "cancel": "CANCELLED",
    },
    "DISPATCHED": {
        "start_use": "IN_USE",
        "cancel": "CANCELLED",
    },
    "AWAITING_ALLOCATION": {
        "allocate": "ALLOCATED",
        "allocate_partial": "PARTIALLY_ALLOCATED",
        "mark_unavailable": "UNAVAILABLE",
        "cancel": "CANCELLED",
    },
    "PARTIALLY_ALLOCATED": {
        "allocate": "ALLOCATED",
        "mark_unavailable": "UNAVAILABLE",
        "cancel": "CANCELLED",
        "start_use": "IN_USE",
    },
    "ALLOCATED": {
        "start_use": "IN_USE",
        "cancel": "CANCELLED",
        "return": "RETURNED",
    },
    "IN_USE": {
        "return": "RETURNED",
        "return_equipment": "RETURNED",
        "request_return": "RETURN_REQUESTED",
        "request-return": "RETURN_REQUESTED",
    },
    "RETURN_REQUESTED": {
        "return": "RETURNED",
        "return_equipment": "RETURNED",
        "inspect": "INSPECTED",
    },
    "RETURNED": {
        "inspect": "INSPECTED",
        "close": "CLOSED",
    },
    "INSPECTED": {
        "close": "CLOSED",
    },
    "CLOSED": {},
    "REJECTED": {
        "submit": "SUBMITTED",
    },
    "CANCELLED": {},
    "RETURNED_FOR_CORRECTION": {
        "submit": "SUBMITTED",
        "cancel": "CANCELLED",
    },
    "UNAVAILABLE": {
        "await_allocation": "AWAITING_ALLOCATION",
        "cancel": "CANCELLED",
    },
}


def validate_requisition_transition(from_state: str, action: str) -> str:
    if from_state not in REQUISITION_TRANSITIONS:
        raise ValueError(f"Unknown requisition state: {from_state}")
    transitions = REQUISITION_TRANSITIONS.get(from_state, {})
    if action not in transitions:
        raise ValueError(f"Cannot {action} requisition from state {from_state}")
    return transitions[action]


# ── Models ─────────────────────────────────────────────────────

class MachineType(Base):
    __tablename__ = "machine_types"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), default="Lifting & Transport")
    hourly_rate: Mapped[float] = mapped_column(Float, default=50.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    machines = relationship("Machine", back_populates="machine_type", lazy="selectin")


class Machine(Base):
    __tablename__ = "machines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    machine_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("machine_types.id"), nullable=False)
    identifier: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="AVAILABLE")
    location: Mapped[str | None] = mapped_column(String(255), nullable=True, default="Central Equipment Yard")
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True, index=True
    )
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", use_alter=True), nullable=True, index=True
    )
    capacity_rating: Mapped[str | None] = mapped_column(String(100), nullable=True)
    current_hour_meter: Mapped[float] = mapped_column(Float, default=0.0)
    last_maintenance_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    machine_type = relationship("MachineType", back_populates="machines", lazy="selectin")
    reservations = relationship("MachineReservation", back_populates="machine", lazy="selectin")
    requisitions = relationship("MachineRequisition", back_populates="allocated_machine", lazy="selectin")
    location_ref = relationship("Location", foreign_keys=[location_id], lazy="selectin")
    asset = relationship("Asset", foreign_keys=[asset_id], lazy="selectin")


class MachineRequisition(Base, TimestampMixin):
    __tablename__ = "machine_requisitions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requisition_number: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)
    
    # Department & Requester
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False)
    collaborating_department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    requester_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Scope & Purpose
    purpose: Mapped[str] = mapped_column(String(2000), nullable=False)
    job_card_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("job_cards.id"), nullable=True)
    
    # Equipment Specs
    machine_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("machine_types.id"), nullable=False)
    machine_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("machines.id"), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    location: Mapped[str] = mapped_column(String(255), nullable=False, default="On-site Works")
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True, index=True
    )
    
    location_ref = relationship("Location", foreign_keys=[location_id], lazy="selectin")

    # Time Schedule
    required_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    estimated_duration_hours: Mapped[float] = mapped_column(Float, default=1.0)
    priority: Mapped[int] = mapped_column(Integer, default=1)  # 0: Low, 1: Medium, 2: High, 3: Urgent

    # Operational Requirements
    operator_required: Mapped[bool] = mapped_column(Boolean, default=False)
    operator_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    special_requirements: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    safety_requirements: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    
    # Financial Costing
    cost_centre: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    actual_cost: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Workflow Status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT")
    
    # Approvals & Audits
    dept_approver_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    dept_approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    equipment_checker_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    equipment_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    approver_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    scheduler_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    dispatcher_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    inspector_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    inspected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    inspection_notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    
    start_hour_meter: Mapped[float | None] = mapped_column(Float, nullable=True)
    end_hour_meter: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    comments: Mapped[str | None] = mapped_column(String(4000), nullable=True)

    # Relationships
    machine_type = relationship("MachineType", lazy="selectin")
    allocated_machine = relationship("Machine", foreign_keys=[machine_id], back_populates="requisitions", lazy="selectin")
    reservations = relationship("MachineReservation", back_populates="requisition", lazy="selectin", cascade="all, delete-orphan")
    action_logs = relationship("RequisitionActionLog", back_populates="requisition", lazy="selectin", cascade="all, delete-orphan", order_by="RequisitionActionLog.created_at.desc()")


class MachineReservation(Base):
    __tablename__ = "machine_reservations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requisition_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("machine_requisitions.id"), nullable=True)
    machine_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("machines.id"), nullable=False)
    reservation_type: Mapped[str] = mapped_column(String(50), nullable=False, default="REQUISITION")  # REQUISITION, MAINTENANCE
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reservation_status: Mapped[str] = mapped_column(String(50), nullable=False, default="SCHEDULED")  # SCHEDULED, ALLOCATED, IN_USE, COMPLETED, CANCELLED
    start_hours: Mapped[float] = mapped_column(Float, default=0.0)
    end_hours: Mapped[float | None] = mapped_column(Float, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    requisition = relationship("MachineRequisition", back_populates="reservations")
    machine = relationship("Machine", back_populates="reservations")


class RequisitionActionLog(Base):
    __tablename__ = "requisition_action_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requisition_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("machine_requisitions.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    state_from: Mapped[str | None] = mapped_column(String(50), nullable=True)
    state_to: Mapped[str | None] = mapped_column(String(50), nullable=True)
    details: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    requisition = relationship("MachineRequisition", back_populates="action_logs")
