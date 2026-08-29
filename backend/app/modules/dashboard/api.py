from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.db.session import get_db
from app.main import get_current_user
from app.modules.iam.models import User
from app.modules.dashboard.schemas import DashboardFilterParams, DashboardDataResponse
from app.modules.dashboard.service import DashboardService

dashboard_router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@dashboard_router.post("/metrics", response_model=DashboardDataResponse)
async def get_dashboard_metrics(
    filters: DashboardFilterParams,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get operational dashboard metrics respecting user scope and applying filters.
    """
    return await DashboardService.get_dashboard_data(db, filters, current_user)


@dashboard_router.get("/analytics")
async def get_analytics_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Quick operational analytics summary for the home dashboard tiles.
    Returns active job count, pending approvals, and a placeholder fleet utilization metric.
    """
    from app.modules.jobs.models import JobCard
    from app.modules.approvals.models import ApprovalStep

    active_count = await db.scalar(
        select(func.count(JobCard.id)).where(
            JobCard.status.in_(["IN_PROGRESS", "ASSIGNED", "PLANNING", "APPROVED"])
        )
    )

    # Scope active jobs to the user's department if they are not a superuser
    if not getattr(current_user, "is_superuser", False) and current_user.department_id:
        active_count = await db.scalar(
            select(func.count(JobCard.id)).where(
                JobCard.status.in_(["IN_PROGRESS", "ASSIGNED", "PLANNING", "APPROVED"]),
                JobCard.department_id == current_user.department_id,
            )
        )

    pending_approvals = await db.scalar(
        select(func.count(ApprovalStep.id)).where(ApprovalStep.status == "PENDING")
    )

    # Recent activity: last 10 job cards visible to this user
    q = select(JobCard).order_by(JobCard.created_at.desc()).limit(10)
    if not getattr(current_user, "is_superuser", False) and current_user.department_id:
        q = q.where(JobCard.department_id == current_user.department_id)
    recent_result = await db.execute(q)
    recent_jobs = recent_result.scalars().all()

    recent_activity = [
        {
            "id": str(j.id),
            "display_id": getattr(j, "job_number", None) or str(j.id)[:8].upper(),
            "title": j.title,
            "status": j.status,
            "department": str(j.department_id) if j.department_id else "",
        }
        for j in recent_jobs
    ]

    return {
        "active_job_cards": active_count or 0,
        "pending_approvals": pending_approvals or 0,
        "fleet_utilization": "N/A",
        "recent_activity": recent_activity,
    }
