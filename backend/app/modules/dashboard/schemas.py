from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class DashboardFilterParams(BaseModel):
    department_id: Optional[UUID] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    job_type: Optional[str] = None
    equipment_id: Optional[UUID] = None
    requester_id: Optional[UUID] = None
    assigned_worker_id: Optional[UUID] = None
    location: Optional[str] = None
    cost_centre: Optional[str] = None

class JobMetricsResponse(BaseModel):
    total_jobs: int = 0
    open_jobs: int = 0
    pending_approval: int = 0
    assigned: int = 0
    in_progress: int = 0
    on_hold: int = 0
    completed: int = 0
    overdue: int = 0
    avg_completion_time_hours: float = 0.0
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    cost_variance: float = 0.0

class DepartmentWorkload(BaseModel):
    department_name: str
    active_jobs: int

class EquipmentUtilization(BaseModel):
    status: str
    count: int

class FleetMetricsResponse(BaseModel):
    total_equipment: int = 0
    in_use: int = 0
    utilization_percentage: float = 0.0
    pending_requisitions: int = 0
    equipment_utilization_breakdown: List[EquipmentUtilization] = Field(default_factory=list)

class TimeSeriesDataPoint(BaseModel):
    date: str
    jobs_created: int
    jobs_completed: int

class DashboardDataResponse(BaseModel):
    job_metrics: JobMetricsResponse
    fleet_metrics: FleetMetricsResponse
    department_workload: List[DepartmentWorkload]
    timeseries_data: List[TimeSeriesDataPoint]
