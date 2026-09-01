import datetime
from uuid import UUID
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, cast
from fastapi import HTTPException

from app.modules.dashboard.models import DashboardSavedView
from app.modules.dashboard.schemas import (
    DashboardFilterParams,
    DashboardDataResponse,
    DashboardWidgetConfig,
    DashboardConfigResponse,
    DashboardSavedViewCreate,
    DashboardSavedViewResponse,
    JobMetricsResponse,
    FleetMetricsResponse,
    DepartmentWorkload,
    EquipmentUtilization,
    TimeSeriesDataPoint,
    MetricDefinition,
    TrendView,
)
from app.modules.jobs.models import JobCard
from app.modules.fleet.models import Machine, MachineRequisition
from app.modules.iam.models import User, Department
from app.modules.iam.api import _get_user_permissions
from app.modules.assets.models import Asset
from app.modules.requests.models import OperationalRequest
from app.modules.contractors.models import ContractorAssignment, ContractorCompany
from app.modules.work.models import WorkItem


class DashboardService:
    @staticmethod
    def _default_dashboard_key(current_user: User) -> str:
        if getattr(current_user, "is_superuser", False):
            return "admin"
        if any(getattr(role, "name", "").upper() in {"MANAGER", "HOD"} for role in getattr(current_user, "roles", [])):
            return "manager"
        return "employee"

    @staticmethod
    def _default_widgets(dashboard_key: str) -> List[DashboardWidgetConfig]:
        base = [
            DashboardWidgetConfig(id="job_cards", key="job_cards", title="Job cards", type="metric", visible=True, position={"x": 0, "y": 0}, size="md", config={"metric": "total_jobs"}),
            DashboardWidgetConfig(id="open_jobs", key="open_jobs", title="Open jobs", type="metric", visible=True, position={"x": 1, "y": 0}, size="sm", config={"metric": "open_jobs"}),
            DashboardWidgetConfig(id="pending_approvals", key="pending_approvals", title="Approvals", type="metric", visible=True, position={"x": 2, "y": 0}, size="sm", config={"metric": "pending_approval"}),
            DashboardWidgetConfig(id="fleet_utilization", key="fleet_utilization", title="Fleet utilization", type="metric", visible=True, position={"x": 0, "y": 1}, size="md", config={"metric": "utilization_percentage"}),
        ]
        if dashboard_key == "admin":
            base.append(DashboardWidgetConfig(id="department_load", key="department_load", title="Department load", type="table", visible=True, position={"x": 1, "y": 1}, size="lg", config={"metric": "department_workload"}))
        return base

    @staticmethod
    async def get_dashboard_config(db: AsyncSession, current_user: User) -> DashboardConfigResponse:
        dashboard_key = DashboardService._default_dashboard_key(current_user)
        saved_views = await DashboardService.list_saved_views(db, current_user)
        return DashboardConfigResponse(
            dashboard_key=dashboard_key,
            widgets=DashboardService._default_widgets(dashboard_key),
            saved_views=saved_views,
        )

    @staticmethod
    async def list_saved_views(db: AsyncSession, current_user: User) -> List[DashboardSavedViewResponse]:
        if getattr(current_user, "is_superuser", False):
            query = select(DashboardSavedView)
        else:
            query = select(DashboardSavedView).where(
                or_(
                    DashboardSavedView.user_id == current_user.id,
                    DashboardSavedView.scope == "global",
                    and_(
                        DashboardSavedView.scope == "department",
                        DashboardSavedView.department_id == current_user.department_id,
                    ),
                )
            )
        result = await db.execute(query.order_by(DashboardSavedView.updated_at.desc()))
        views = result.scalars().all()
        return [DashboardSavedViewResponse.model_validate(view, from_attributes=True) for view in views]

    @staticmethod
    async def get_saved_view(db: AsyncSession, current_user: User, view_id: UUID) -> DashboardSavedViewResponse:
        result = await db.execute(select(DashboardSavedView).where(DashboardSavedView.id == view_id))
        view = result.scalar_one_or_none()
        if not view:
            raise HTTPException(status_code=404, detail="Saved view not found.")
        if not (
            view.user_id == current_user.id
            or getattr(current_user, "is_superuser", False)
            or (view.scope == "department" and current_user.department_id and view.department_id == current_user.department_id)
            or view.scope == "global"
        ):
            raise HTTPException(status_code=403, detail="You do not have access to this saved view.")
        return DashboardSavedViewResponse.model_validate(view, from_attributes=True)

    @staticmethod
    async def create_saved_view(
        db: AsyncSession,
        current_user: User,
        payload: DashboardSavedViewCreate,
    ) -> DashboardSavedViewResponse:
        if not payload.name or not payload.name.strip():
            raise HTTPException(status_code=400, detail="Saved view name is required.")

        scope = payload.scope.lower()
        if scope not in {"personal", "department", "global"}:
            raise HTTPException(status_code=400, detail="Unsupported saved view scope.")
        if scope == "global" and not getattr(current_user, "is_superuser", False):
            raise HTTPException(status_code=403, detail="Only admins can create global dashboard views.")
        if scope == "department" and not current_user.department_id:
            raise HTTPException(status_code=400, detail="Department scope requires a department assignment.")

        view = DashboardSavedView(
            user_id=current_user.id,
            department_id=payload.department_id or (current_user.department_id if scope == "department" else None),
            name=payload.name.strip(),
            dashboard_key=payload.dashboard_key or DashboardService._default_dashboard_key(current_user),
            scope=scope,
            filters=payload.filters or {},
            sorting=payload.sorting or {},
            columns=payload.columns or [],
            search_query=payload.search_query,
            date_range=payload.date_range or {},
            is_default=bool(payload.is_default),
        )
        db.add(view)
        await db.commit()
        await db.refresh(view)
        return DashboardSavedViewResponse.model_validate(view, from_attributes=True)

    @staticmethod
    def _apply_job_filters(query, filters: DashboardFilterParams, current_user: User):
        perms = _get_user_permissions(current_user)
        has_global = "global_override" in perms
        has_cross_dept = "job_card:read:cross_department" in perms

        if not has_global and not has_cross_dept:
            query = query.where(JobCard.department_id == current_user.department_id)

        if filters.department_id:
            if not has_global and not has_cross_dept and str(filters.department_id) != str(current_user.department_id):
                raise HTTPException(status_code=403, detail="Cannot view dashboard for other departments.")
            query = query.where(JobCard.department_id == filters.department_id)

        if filters.date_from:
            query = query.where(JobCard.created_at >= filters.date_from)
        if filters.date_to:
            query = query.where(JobCard.created_at <= filters.date_to)

        if filters.status:
            query = query.where(JobCard.status == filters.status)
        if filters.priority is not None:
            query = query.where(JobCard.priority == filters.priority)
        if filters.job_type:
            query = query.where(JobCard.job_type == filters.job_type)
        if filters.equipment_id:
            query = query.where(JobCard.machine_id == filters.equipment_id)
        if filters.requester_id:
            query = query.where(JobCard.creator_id == filters.requester_id)
        if filters.assigned_worker_id:
            query = query.where(JobCard.supervisor_id == filters.assigned_worker_id)
        if filters.location:
            query = query.where(JobCard.location.ilike(f"%{filters.location}%"))

        return query

    @staticmethod
    async def get_dashboard_data(
        db: AsyncSession,
        filters: DashboardFilterParams,
        current_user: User,
    ) -> DashboardDataResponse:
        base_query = select(JobCard)
        filtered_query = DashboardService._apply_job_filters(base_query, filters, current_user)

        result = await db.execute(filtered_query)
        jobs = result.scalars().all()

        job_metrics = JobMetricsResponse()
        total_time_seconds = 0
        completed_with_time = 0

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        for job in jobs:
            job_metrics.total_jobs += 1
            job_metrics.estimated_cost += float(job.estimated_cost or 0)

            if job.status not in ["CLOSED", "CANCELLED", "REJECTED"]:
                job_metrics.open_jobs += 1

                if job.required_date:
                    required_date = job.required_date
                    if required_date.tzinfo is None:
                        required_date = required_date.replace(tzinfo=datetime.timezone.utc)
                    if required_date < now_utc:
                        job_metrics.overdue += 1

            if job.status == "PENDING_APPROVAL":
                job_metrics.pending_approval += 1
            elif job.status == "ASSIGNED":
                job_metrics.assigned += 1
            elif job.status == "IN_PROGRESS":
                job_metrics.in_progress += 1
            elif job.status == "ON_HOLD":
                job_metrics.on_hold += 1
            elif job.status in ["COMPLETED", "VERIFIED"]:
                job_metrics.completed += 1
                if job.actual_start_time and job.actual_end_time:
                    diff = job.actual_end_time - job.actual_start_time
                    total_time_seconds += diff.total_seconds()
                    completed_with_time += 1

        if completed_with_time > 0:
            job_metrics.avg_completion_time_hours = round(total_time_seconds / 3600 / completed_with_time, 2)

        dept_query = (
            select(Department.name, func.count(JobCard.id))
            .join(JobCard, JobCard.department_id == Department.id)
            .where(JobCard.status.notin_(["DRAFT", "CLOSED", "CANCELLED"]))
            .group_by(Department.name)
        )
        dept_result = await db.execute(dept_query)
        dept_workload = [DepartmentWorkload(department_name=row[0], active_jobs=row[1]) for row in dept_result.all()]

        machines_result = await db.execute(select(Machine.status, func.count(Machine.id)).group_by(Machine.status))
        machine_counts = {row[0]: row[1] for row in machines_result.all()}

        fleet_metrics = FleetMetricsResponse()
        fleet_metrics.total_equipment = sum(machine_counts.values())
        fleet_metrics.in_use = machine_counts.get("IN_USE", 0)

        if fleet_metrics.total_equipment > 0:
            fleet_metrics.utilization_percentage = round((fleet_metrics.in_use / fleet_metrics.total_equipment) * 100, 1)

        for status, count in machine_counts.items():
            fleet_metrics.equipment_utilization_breakdown.append(EquipmentUtilization(status=status, count=count))

        req_result = await db.execute(
            select(func.count(MachineRequisition.id))
            .where(MachineRequisition.status.in_(["SUBMITTED", "DEPARTMENT_APPROVAL", "EQUIPMENT_CHECK"]))
        )
        fleet_metrics.pending_requisitions = req_result.scalar_one_or_none() or 0

        timeseries_dict = {}
        for job in jobs:
            created_date = job.created_at.strftime("%Y-%m-%d") if job.created_at else "unknown"
            if created_date not in timeseries_dict:
                timeseries_dict[created_date] = {"jobs_created": 0, "jobs_completed": 0}
            timeseries_dict[created_date]["jobs_created"] += 1

            if job.status in ["COMPLETED", "VERIFIED"] and job.actual_end_time:
                completed_date = job.actual_end_time.strftime("%Y-%m-%d")
                if completed_date not in timeseries_dict:
                    timeseries_dict[completed_date] = {"jobs_created": 0, "jobs_completed": 0}
                timeseries_dict[completed_date]["jobs_completed"] += 1

        timeseries_data = [
            TimeSeriesDataPoint(date=k, jobs_created=v["jobs_created"], jobs_completed=v["jobs_completed"])
            for k, v in sorted(timeseries_dict.items())
        ]

        operational_metrics = {
            "total_work": job_metrics.total_jobs,
            "active_jobs": job_metrics.open_jobs,
            "completed_jobs": job_metrics.completed,
            "overdue_jobs": job_metrics.overdue,
            "avg_completion_hours": job_metrics.avg_completion_time_hours,
        }

        department_metrics = dept_workload
        asset_query = select(func.count(Asset.id)).where(Asset.is_archived.is_(False))
        asset_result = await db.execute(asset_query)
        active_assets = asset_result.scalar_one_or_none() or 0

        request_query = select(func.count(OperationalRequest.id)).where(
            OperationalRequest.status.notin_(["CANCELLED", "REJECTED", "CLOSED"])
        )
        request_result = await db.execute(request_query)
        active_requests = request_result.scalar_one_or_none() or 0

        contractor_query = select(func.count(ContractorAssignment.id))
        contractor_result = await db.execute(contractor_query)
        active_contractors = contractor_result.scalar_one_or_none() or 0

        work_query = select(func.count(WorkItem.id)).where(
            WorkItem.status.notin_(["CANCELLED", "REJECTED", "CLOSED"])
        )
        work_result = await db.execute(work_query)
        active_work = work_result.scalar_one_or_none() or 0

        metric_definitions = [
            MetricDefinition(
                name="Total Work",
                description="Count of authoritative work records in scope for the selected department and time range.",
                calculation="COUNT(job_cards.id) for all jobs matching filters; excludes cancelled, rejected, and closed rows only when they are intentionally filtered out.",
                scope="department or global depending on RBAC scope",
                permission_requirements=["job_card:read:cross_department"],
            ),
            MetricDefinition(
                name="Open Work",
                description="Operational work still active or requiring attention.",
                calculation="COUNT(job_cards.id) WHERE status not in (CLOSED, CANCELLED, REJECTED)",
                scope="department or global depending on RBAC scope",
                permission_requirements=["job_card:read:cross_department"],
            ),
            MetricDefinition(
                name="Fleet Utilization",
                description="Share of equipment currently in active use versus available inventory.",
                calculation="IN_USE / total_equipment * 100",
                scope="site or global",
                permission_requirements=["asset:read:cross_department"],
            ),
            MetricDefinition(
                name="Request Backlog",
                description="Requests still in process and not yet closed or rejected.",
                calculation="COUNT(operational_requests.id) WHERE status not in (CANCELLED, REJECTED, CLOSED)",
                scope="department or global depending on RBAC scope",
                permission_requirements=["request:read:cross_department"],
            ),
        ]

        trend_views = [
            TrendView(
                key="job_volume",
                title="Job volume trend",
                description="Created versus completed job cards over the selected date range.",
                unit="jobs",
                series=timeseries_data,
            ),
            TrendView(
                key="workload_by_department",
                title="Department workload trend",
                description="Current workload by department summary for the selected scope.",
                unit="jobs",
                series=[TimeSeriesDataPoint(date=item.department_name, jobs_created=item.active_jobs, jobs_completed=0) for item in dept_workload],
            ),
        ]

        future_analytics = {
            "status": "ready_for_early_signal_tracking",
            "next_primitives": [
                "lead_time_by_department",
                "asset_utilization_drift",
                "request_fulfillment_latency",
                "contractor_performance_rating",
            ],
            "notes": "No AI-generated operational forecasts are exposed until there is sufficient historical data and explicit metric definitions for the selected scope.",
        }

        return DashboardDataResponse(
            job_metrics=job_metrics,
            fleet_metrics=fleet_metrics,
            department_workload=dept_workload,
            timeseries_data=timeseries_data,
            operational_metrics=operational_metrics,
            department_metrics=department_metrics,
            asset_metrics={"active_assets": active_assets, "total_equipment": fleet_metrics.total_equipment},
            resource_metrics={"active_work": active_work, "pending_requisitions": fleet_metrics.pending_requisitions},
            request_metrics={"active_requests": active_requests},
            contractor_metrics={"active_assignments": active_contractors},
            metric_definitions=metric_definitions,
            trend_views=trend_views,
            future_analytics=future_analytics,
        )
