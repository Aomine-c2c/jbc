from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class EscalationRuleSchema(BaseModel):
    level: int = Field(..., ge=1, le=5)
    trigger: str = Field(..., description="RESPONSE_WARNING, RESPONSE_BREACH, COMPLETION_WARNING, COMPLETION_BREACH")
    after_percentage: int = Field(..., ge=1, le=200)
    target_role: Optional[str] = None
    notify_channel: str = Field("PUSH", description="PUSH, SMS, EMAIL, ALL")


class SLAPolicyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    priority: Optional[str] = None  # LOW, NORMAL, HIGH, CRITICAL
    work_type: Optional[str] = None  # MAINTENANCE, INSPECTION, JOB_CARD, etc.
    department_id: Optional[UUID] = None
    asset_category: Optional[str] = None
    risk_level: Optional[str] = None
    response_time_minutes: int = Field(60, ge=1)
    completion_time_minutes: int = Field(480, ge=1)
    warning_threshold_percentage: int = Field(80, ge=1, le=100)
    escalation_rules: List[Dict[str, Any]] = Field(default_factory=list)
    is_active: bool = True
    is_default: bool = False


class SLAPolicyCreate(SLAPolicyBase):
    pass


class SLAPolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    work_type: Optional[str] = None
    department_id: Optional[UUID] = None
    asset_category: Optional[str] = None
    risk_level: Optional[str] = None
    response_time_minutes: Optional[int] = None
    completion_time_minutes: Optional[int] = None
    warning_threshold_percentage: Optional[int] = None
    escalation_rules: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class SLAPolicyResponse(SLAPolicyBase):
    id: UUID
    department_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class SLAEscalationLogResponse(BaseModel):
    id: UUID
    tracker_id: UUID
    escalation_level: int
    trigger_type: str
    notified_role: Optional[str] = None
    notified_user_ids: List[Any] = Field(default_factory=list)
    message: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class SLATrackerBase(BaseModel):
    policy_id: Optional[UUID] = None
    resource_type: str = Field(..., max_length=50)
    resource_id: UUID
    resource_reference: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=255)
    priority: str = Field("NORMAL", max_length=50)
    department_id: Optional[UUID] = None


class SLATrackerCreate(SLATrackerBase):
    work_type: Optional[str] = None
    asset_category: Optional[str] = None
    risk_level: Optional[str] = None


class SLAPauseRequest(BaseModel):
    reason: Optional[str] = None


class SLAResumeRequest(BaseModel):
    notes: Optional[str] = None


class SLAAcknowledgeRequest(BaseModel):
    notes: Optional[str] = None


class SLATrackerResponse(SLATrackerBase):
    id: UUID
    status: str
    health: str
    target_response_at: Optional[datetime] = None
    target_completion_at: Optional[datetime] = None
    actual_response_at: Optional[datetime] = None
    actual_completion_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    total_paused_minutes: float = 0.0
    current_escalation_level: int = 0
    breach_reason: Optional[str] = None
    department_name: Optional[str] = None
    policy_name: Optional[str] = None
    history_logs: List[Any] = Field(default_factory=list)
    escalation_logs: List[SLAEscalationLogResponse] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class SLATrackerListResponse(BaseModel):
    id: UUID
    resource_type: str
    resource_id: UUID
    resource_reference: Optional[str] = None
    title: str
    priority: str
    status: str
    health: str
    target_response_at: Optional[datetime] = None
    target_completion_at: Optional[datetime] = None
    actual_response_at: Optional[datetime] = None
    actual_completion_at: Optional[datetime] = None
    current_escalation_level: int = 0
    department_name: Optional[str] = None
    policy_name: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class SLADashboardResponse(BaseModel):
    total_active: int
    on_track_count: int
    at_risk_count: int
    breached_count: int
    critical_open_count: int
    compliance_percentage: float
    avg_response_minutes: float
    avg_completion_minutes: float
    recent_breaches: List[SLATrackerListResponse] = Field(default_factory=list)
    at_risk_trackers: List[SLATrackerListResponse] = Field(default_factory=list)
