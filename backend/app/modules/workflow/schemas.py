import uuid
from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator


class WorkflowStateSchema(BaseModel):
    """Definition of a single state within a workflow template."""
    name: str = Field(..., min_length=1, max_length=100)
    label: Optional[str] = None
    is_initial: bool = False
    is_terminal: bool = False
    requires_approval: bool = False
    sla_minutes: Optional[int] = None

    model_config = {"from_attributes": True}


class WorkflowTransitionSchema(BaseModel):
    """Definition of a single allowed transition between two states."""
    from_state: str
    to_state: str
    action: str = Field(..., min_length=1, max_length=100, description="Machine-readable action key e.g. 'approve', 'reject', 'submit'")
    label: Optional[str] = None
    required_role: Optional[str] = None
    required_permission: Optional[str] = None
    # Conditions evaluated at transition time
    conditions: Optional[Dict[str, Any]] = None
    auto_create_sla: bool = False

    model_config = {"from_attributes": True}


class WorkflowTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    entity_type: str = "ANY"
    department_id: Optional[uuid.UUID] = None
    min_priority: Optional[int] = None
    risk_level: Optional[str] = None
    request_type: Optional[str] = None
    is_default: bool = False
    states: List[WorkflowStateSchema] = Field(..., min_length=1)
    transitions: List[WorkflowTransitionSchema] = Field(..., min_length=1)

    model_config = {"from_attributes": True}


class WorkflowTemplateActivate(BaseModel):
    description: Optional[str] = None  # Optional change note for this activation


class WorkflowValidationResult(BaseModel):
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []


class WorkflowStepDefOut(BaseModel):
    step_number: int
    authority_role: str
    required_permission: str

    model_config = {"from_attributes": True}


class WorkflowTemplateListResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    entity_type: str
    version: int
    is_active: bool
    is_default: bool
    states_count: int = 0
    transitions_count: int = 0
    department_name: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class WorkflowTemplateResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    entity_type: str
    version: int
    is_active: bool
    is_default: bool
    department_id: Optional[uuid.UUID] = None
    department_name: Optional[str] = None
    min_priority: Optional[int] = None
    risk_level: Optional[str] = None
    request_type: Optional[str] = None
    states: List[Dict[str, Any]] = []
    transitions: List[Dict[str, Any]] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class WorkflowTransitionRequest(BaseModel):
    action: str = Field(..., min_length=1)
    notes: Optional[str] = None


class WorkflowTransitionLogResponse(BaseModel):
    id: uuid.UUID
    action: str
    from_state: str
    to_state: str
    actor_name: Optional[str] = None
    actor_role: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkflowInstanceResponse(BaseModel):
    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    current_state: str
    template_id: uuid.UUID
    template_version: int
    template_name: Optional[str] = None
    completed_at: Optional[datetime] = None
    available_transitions: List[Dict[str, Any]] = []
    transition_logs: List[WorkflowTransitionLogResponse] = []
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
