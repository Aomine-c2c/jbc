import logging
from typing import Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
import uuid

from app.db.session import async_session_factory
from app.modules.audit.models import BusinessAuditLog
from app.modules.iam.models import User

logger = logging.getLogger("DWRMS.Audit")

class AuditService:
    @staticmethod
    async def log_event(
        db: AsyncSession,
        action: str,
        resource: str,
        resource_id: Optional[str] = None,
        user: Optional[User] = None,
        previous_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """
        Records an immutable business audit log. 
        Values are denormalized from the user object to prevent data loss if the user is deleted.
        """
        try:
            audit = BusinessAuditLog(
                action=action,
                resource=resource,
                resource_id=resource_id,
                previous_value=previous_value,
                new_value=new_value,
                reason=reason,
                ip_address=ip_address,
                user_agent=user_agent
            )

            if user:
                audit.user_id = user.id
                audit.user_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email
                
                # Fetch department and role if loaded, otherwise safely try
                if "department" in user.__dict__ and user.department:
                    audit.department_name = user.department.name
                
                if "roles" in user.__dict__ and user.roles:
                    audit.role_names = ", ".join([r.role.name for r in user.roles if r.role])

            db.add(audit)
            # We don't commit here in case it's part of a larger transaction, 
            # unless the caller requires it.
            # Usually the router `Depends(get_db)` commits at the end, but if this is 
            # called in a background task, the session will commit it.
        except Exception as e:
            logger.error(f"Failed to create audit log event: {e}")

    @staticmethod
    async def list_events(
        db: AsyncSession,
        page: int = 1,
        size: int = 50,
        user_id: Optional[uuid.UUID] = None,
        department_name: Optional[str] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ):
        query = select(BusinessAuditLog)

        if user_id:
            query = query.where(BusinessAuditLog.user_id == user_id)
        if department_name:
            query = query.where(BusinessAuditLog.department_name == department_name)
        if action:
            query = query.where(BusinessAuditLog.action == action)
        if resource:
            query = query.where(BusinessAuditLog.resource == resource)
        if resource_id:
            query = query.where(BusinessAuditLog.resource_id == resource_id)
        if start_date:
            query = query.where(BusinessAuditLog.timestamp >= start_date)
        if end_date:
            query = query.where(BusinessAuditLog.timestamp <= end_date)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one_or_none() or 0

        # Pagination and order
        query = query.order_by(desc(BusinessAuditLog.timestamp))
        query = query.offset((page - 1) * size).limit(size)

        result = await db.execute(query)
        items = result.scalars().all()

        return items, total
