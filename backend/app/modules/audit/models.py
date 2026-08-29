import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

class BusinessAuditLog(Base):
    """
    Immutable audit log storing semantic business events.
    Values are denormalized so logs remain accurate if relations are deleted.
    """
    __tablename__ = "business_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Actor details (Denormalized)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    user_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    department_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role_names: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Action & Resource details
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True) # e.g. CREATE, UPDATE, APPROVE
    resource: Mapped[str] = mapped_column(String(100), nullable=False, index=True) # e.g. JOB_CARD
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    
    # Payload
    previous_value: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    new_value: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Environment
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(1024), nullable=True)
