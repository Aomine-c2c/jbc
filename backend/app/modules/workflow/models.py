import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    String, Boolean, ForeignKey, DateTime, Integer, JSON, Text, func, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.db.mixins import TimestampMixin


class WorkflowEntityType(str, enum.Enum):
    WORK_ITEM = "WORK_ITEM"
    REQUEST = "REQUEST"
    JOB_CARD = "JOB_CARD"
    APPROVAL = "APPROVAL"
    RESOURCE_ALLOCATION = "RESOURCE_ALLOCATION"
    ASSET = "ASSET"
    ANY = "ANY"


class WorkflowTemplate(Base, TimestampMixin):
    """
    Versioned, configurable state-machine workflow template.
    Each activation creates a new version record.
    WorkflowInstance.metadata snapshots states+transitions at creation
    so historical instances are not affected by future template changes.
    """
    __tablename__ = "workflow_templates"
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_workflow_template_name_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Which entity type this template applies to
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=WorkflowEntityType.ANY.value, index=True
    )

    # Matching criteria (all nullable — null = match any)
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True
    )
    min_priority: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(30), nullable=True)
    request_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Version control
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    # Escalation policy & Actions config
    escalation_policy: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # State machine definition stored as JSON
    states: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    transitions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Author
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Relationships
    department = relationship("Department", foreign_keys=[department_id], lazy="selectin")
    created_by = relationship("User", foreign_keys=[created_by_id], lazy="selectin")
    instances = relationship("WorkflowInstance", back_populates="template", lazy="dynamic")

    def get_initial_states(self) -> list[str]:
        return [s["name"] for s in self.states if s.get("is_initial", False)]

    def get_terminal_states(self) -> list[str]:
        return [s["name"] for s in self.states if s.get("is_terminal", False)]

    def get_state_names(self) -> list[str]:
        return [s["name"] for s in self.states]

    def get_available_transitions(self, from_state: str) -> list[dict]:
        return [t for t in self.transitions if t.get("from_state") == from_state]


class WorkflowInstance(Base, TimestampMixin):
    """
    Per-entity live workflow runtime tracker.
    Stores a JSON snapshot of the template's states/transitions
    at the time of creation to preserve historical integrity.
    """
    __tablename__ = "workflow_instances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Template reference (soft version pin)
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_templates.id"), nullable=False, index=True
    )
    template_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Generic entity link (not a FK — supports any entity type)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Current state
    current_state: Mapped[str] = mapped_column(String(100), nullable=False)

    # Lifecycle timestamps
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Historical snapshot — states + transitions at creation time
    template_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Relationships
    template = relationship("WorkflowTemplate", back_populates="instances", lazy="selectin")
    transition_logs = relationship(
        "WorkflowTransitionLog",
        back_populates="instance",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="WorkflowTransitionLog.created_at.asc()",
    )

    def get_available_transitions(self) -> list[dict]:
        transitions = self.template_snapshot.get("transitions", [])
        return [t for t in transitions if t.get("from_state") == self.current_state]


class WorkflowTransitionLog(Base):
    """
    Immutable audit trail of every state transition performed on a WorkflowInstance.
    Records who acted, what action, from/to state, and optional notes.
    """
    __tablename__ = "workflow_transition_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_instances.id"), nullable=False, index=True
    )

    action: Mapped[str] = mapped_column(String(100), nullable=False)
    from_state: Mapped[str] = mapped_column(String(100), nullable=False)
    to_state: Mapped[str] = mapped_column(String(100), nullable=False)

    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    actor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(100), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    instance = relationship("WorkflowInstance", back_populates="transition_logs")
    actor = relationship("User", foreign_keys=[actor_id], lazy="selectin")
