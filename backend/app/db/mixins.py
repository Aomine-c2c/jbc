from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, Boolean, ForeignKey

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class TimestampMixin:
    """Provides created_at and updated_at timestamps."""
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

class SoftDeleteMixin:
    """Provides is_deleted and deleted_at for soft deletion."""
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

class UserTrackingMixin:
    """Provides created_by_id and updated_by_id."""
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
