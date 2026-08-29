import datetime
from uuid import UUID
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, extract
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.modules.dashboard.schemas import (
    DashboardFilterParams,
    DashboardDataResponse,
    JobMetricsResponse,
    FleetMetricsResponse,
    DepartmentWorkload,
    EquipmentUtilization,
    TimeSeriesDataPoint
)
from app.modules.jobs.models import JobCard
from app.modules.fleet.models import Machine, MachineRequisition
from app.modules.iam.models import User, Scope, Department
from app.modules.iam.api import _get_user_permissions

class DashboardService:

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
        current_user: User
    ) -> DashboardDataResponse:
        
        # Base Job Query
        base_query = select(JobCard)
        filtered_query = DashboardService._apply_job_filters(base_query, filters, current_user)
        
        result = await db.execute(filtered_query)
        jobs = result.scalars().all()

        job_metrics = JobMetricsResponse()
        
        total_time_seconds = 0
        completed_with_time = 0

        for job in jobs:
            job_metrics.total_jobs += 1
            job_metrics.estimated_cost += float(job.estimated_cost or 0)
            # if job has no actual_cost field on model, we skip or assume 0 for now unless added
            # Note: The JobCard model doesn't have actual_cost, it calculates from parts and labor
            # We will approximate or leave actual_cost=0 until joined.

            if job.status not in ["CLOSED", "CANCELLED", "REJECTED"]:
                job_metrics.open_jobs += 1
                
                if job.required_date and job.required_date < datetime.datetime.now(datetime.timezone.utc):
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
            
        # Department Workload (active jobs by department)
        dept_query = (
            select(Department.name, func.count(JobCard.id))
            .join(JobCard, JobCard.department_id == Department.id)
            .where(JobCard.status.notin_(["DRAFT", "CLOSED", "CANCELLED"]))
            .group_by(Department.name)
        )
        # Apply filters to subquery logic? Actually just run overall for cross-dept if allowed
        dept_result = await db.execute(dept_query)
        dept_workload = [DepartmentWorkload(department_name=row[0], active_jobs=row[1]) for row in dept_result.all()]

        # Fleet Metrics
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

        # Timeseries
        # For simplicity, grouping by date (YYYY-MM-DD)
        timeseries_dict = {}
        for job in jobs:
            created_date = job.created_at.strftime("%Y-%m-%d")
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

        return DashboardDataResponse(
            job_metrics=job_metrics,
            fleet_metrics=fleet_metrics,
            department_workload=dept_workload,
            timeseries_data=timeseries_data
        )
