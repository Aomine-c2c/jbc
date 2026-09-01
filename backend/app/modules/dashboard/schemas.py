from typing import Optional, List, Any, Dict
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


class DashboardWidgetConfig(BaseModel):
    id: str
    key: str
    title: str
    type: str = "metric"
    visible: bool = True
    position: Dict[str, int] = Field(default_factory=lambda: {"x": 0, "y": 0})
    size: str = "md"
    config: Dict[str, Any] = Field(default_factory=dict)


class DashboardSavedViewBase(BaseModel):
    name: str
    dashboard_key: str = "employee"
    scope: str = "personal"
    filters: Dict[str, Any] = Field(default_factory=dict)
    sorting: Dict[str, Any] = Field(default_factory=dict)
    columns: List[str] = Field(default_factory=list)
    search_query: Optional[str] = None
    date_range: Dict[str, Any] = Field(default_factory=dict)
    department_id: Optional[UUID] = None
    is_default: bool = False


class DashboardSavedViewCreate(DashboardSavedViewBase):
    pass


class DashboardSavedViewResponse(DashboardSavedViewBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


class DashboardConfigResponse(BaseModel):
    dashboard_key: str
    widgets: List[DashboardWidgetConfig]
    saved_views: List[DashboardSavedViewResponse] = Field(default_factory=list)


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


class MetricDefinition(BaseModel):
    name: str
    description: str
    calculation: str
    scope: str
    permission_requirements: List[str] = Field(default_factory=list)
    time_range: str = "current selection"


class TrendView(BaseModel):
    key: str
    title: str
    description: str
    unit: str = "count"
    series: List[TimeSeriesDataPoint] = Field(default_factory=list)


class DashboardDataResponse(BaseModel):
    job_metrics: JobMetricsResponse
    fleet_metrics: FleetMetricsResponse
    department_workload: List[DepartmentWorkload]
    timeseries_data: List[TimeSeriesDataPoint]
    operational_metrics: Dict[str, Any] = Field(default_factory=dict)
    department_metrics: List[DepartmentWorkload] = Field(default_factory=list)
    asset_metrics: Dict[str, Any] = Field(default_factory=dict)
    resource_metrics: Dict[str, Any] = Field(default_factory=dict)
    request_metrics: Dict[str, Any] = Field(default_factory=dict)
    contractor_metrics: Dict[str, Any] = Field(default_factory=dict)
    metric_definitions: List[MetricDefinition] = Field(default_factory=list)
    trend_views: List[TrendView] = Field(default_factory=list)
    future_analytics: Dict[str, Any] = Field(default_factory=dict)
