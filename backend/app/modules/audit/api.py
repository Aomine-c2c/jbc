import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.iam.models import User
from app.core.authz import AuthzGuard
from app.modules.audit.schemas import AuditListResponse
from app.modules.audit.service import AuditService

def _get_current_user():
    """Lazy import to avoid circular imports."""
    from app.main import get_current_user as gcu
    return gcu

audit_router = APIRouter(prefix="/api/v1/audit", tags=["audit"])

@audit_router.get("", response_model=AuditListResponse)
async def list_audit_events(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    user_id: Optional[uuid.UUID] = None,
    department_name: Optional[str] = None,
    action: Optional[str] = None,
    resource: Optional[str] = None,
    resource_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    from app.modules.iam.api import _get_user_permissions
    user_perms = _get_user_permissions(current_user)
    
    # Must have explicit audit read permissions
    if not AuthzGuard.check_permission(current_user, "audit:read", user_perms):
        raise HTTPException(status_code=403, detail="Not authorized to view audit logs")

    items, total = await AuditService.list_events(
        db=db,
        page=page,
        size=size,
        user_id=user_id,
        department_name=department_name,
        action=action,
        resource=resource,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date
    )

    return AuditListResponse(
        items=items,
        total=total,
        page=page,
        size=size
    )
