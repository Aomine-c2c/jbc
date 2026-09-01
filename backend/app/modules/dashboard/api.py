from uuid import UUID as UUIDType
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.db.session import get_db
from app.main import get_current_user
from app.modules.iam.models import User
from app.modules.dashboard.schemas import (
    DashboardFilterParams,
    DashboardDataResponse,
    DashboardConfigResponse,
    DashboardSavedViewCreate,
    DashboardSavedViewResponse,
)
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


@dashboard_router.get("/config", response_model=DashboardConfigResponse)
async def get_dashboard_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the default dashboard config and the saved views visible to the current user."""
    return await DashboardService.get_dashboard_config(db, current_user)


@dashboard_router.get("/views", response_model=list[DashboardSavedViewResponse])
async def list_dashboard_views(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await DashboardService.list_saved_views(db, current_user)


@dashboard_router.post("/views", response_model=DashboardSavedViewResponse)
async def create_dashboard_view(
    payload: DashboardSavedViewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await DashboardService.create_saved_view(db, current_user, payload)


@dashboard_router.get("/views/{view_id}", response_model=DashboardSavedViewResponse)
async def get_dashboard_view(
    view_id: UUIDType,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await DashboardService.get_saved_view(db, current_user, view_id)


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
