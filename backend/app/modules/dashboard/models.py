import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, ForeignKey, DateTime, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class DashboardSavedView(Base):
    __tablename__ = "dashboard_saved_views"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    dashboard_key: Mapped[str] = mapped_column(String(50), nullable=False, default="employee")
    scope: Mapped[str] = mapped_column(String(30), nullable=False, default="personal")
    filters: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    sorting: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    columns: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    search_query: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date_range: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", backref="dashboard_saved_views")
    department = relationship("Department", backref="dashboard_saved_views")
