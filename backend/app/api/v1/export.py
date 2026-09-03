import io
import csv
import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.modules.iam.models import User, Department
from app.modules.jobs.models import JobCard
from app.modules.fleet.models import Machine, MachineType, MachineRequisition
from app.modules.audit.models import BusinessAuditLog


export_router = APIRouter(prefix="/api/v1/export", tags=["Operational Export"])


def _get_current_user():
    from app.main import get_current_user as _gcu
    return _gcu


@export_router.get("/job-cards")
async def export_job_cards_csv(
    department_id: Optional[uuid.UUID] = Query(None),
    status_filter: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    """Streams a formatted CSV export of Job Cards with financial variances and workflow dates."""
    query = select(JobCard)
    if department_id:
        query = query.where(JobCard.department_id == department_id)
    elif current_user.department_id and not current_user.is_superuser:
        query = query.where(JobCard.department_id == current_user.department_id)

    if status_filter and status_filter != "ALL":
        query = query.where(JobCard.status == status_filter)

    query = query.order_by(JobCard.created_at.desc())
    result = await db.execute(query)
    jobs = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    # Header row
    writer.writerow([
        "Job Card ID",
        "Job Number",
        "Title",
        "Department ID",
        "Priority",
        "Status",
        "Estimated Hours",
        "Actual Hours",
        "Estimated Cost (USD)",
        "Actual Cost (USD)",
        "Cost Variance (USD)",
        "Created At",
        "Actual Start Time",
        "Completed At",
    ])

    for job in jobs:
        est_cost = getattr(job, "estimated_cost", 0.0) or 0.0
        act_cost = getattr(job, "actual_cost", 0.0) or 0.0
        variance = act_cost - est_cost
        writer.writerow([
            str(job.id),
            getattr(job, "job_number", "") or "",
            job.title,
            str(job.department_id),
            str(job.priority),
            job.status,
            str(getattr(job, "estimated_duration_hours", "") or ""),
            str(getattr(job, "actual_duration_hours", "") or ""),
            f"{est_cost:.2f}",
            f"{act_cost:.2f}",
            f"{variance:.2f}",
            job.created_at.isoformat() if job.created_at else "",
            job.actual_start_time.isoformat() if job.actual_start_time else "",
            getattr(job, "completed_at", "") or "",
        ])

    output.seek(0)
    filename = f"dwrms_job_cards_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@export_router.get("/audit-logs")
async def export_audit_logs_csv(
    resource: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    """Streams a formatted CSV export of immutable audit trail records."""
    if not current_user.is_superuser:
        from app.core.authz import get_user_permissions
        perms = get_user_permissions(current_user)
        if "audit:read" not in perms and "global_override" not in perms:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Audit export permissions required.")

    query = select(BusinessAuditLog)
    if resource and resource != "ALL":
        query = query.where(BusinessAuditLog.resource == resource)

    query = query.order_by(BusinessAuditLog.timestamp.desc()).limit(1000)
    result = await db.execute(query)
    logs = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Log ID",
        "Timestamp",
        "Actor Name",
        "Actor ID",
        "Action",
        "Resource",
        "Resource ID",
        "IP Address",
        "Reason / Details",
    ])

    for log in logs:
        writer.writerow([
            str(log.id),
            log.timestamp.isoformat() if log.timestamp else "",
            log.user_name or "",
            str(log.user_id) if log.user_id else "",
            log.action,
            log.resource,
            str(log.resource_id) if log.resource_id else "",
            log.ip_address or "",
            log.reason or "",
        ])

    output.seek(0)
    filename = f"dwrms_audit_trail_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
