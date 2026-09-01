import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.iam.models import User
from app.modules.workflow.schemas import (
    WorkflowTemplateCreate,
    WorkflowTemplateListResponse,
    WorkflowTemplateResponse,
    WorkflowInstanceResponse,
    WorkflowTransitionRequest,
    WorkflowTransitionLogResponse,
    WorkflowValidationResult,
)
from app.modules.workflow.service import WorkflowService, validate_workflow_definition

router = APIRouter(prefix="/workflows", tags=["Configurable Workflow Engine"])


def _get_current_user():
    from app.main import get_current_user
    return get_current_user


def _require_admin(current_user: User) -> None:
    if not current_user.is_superuser:
        from app.core.authz import require_permission
        require_permission(current_user, "settings:manage")


# ── Template Endpoints ─────────────────────────────────────────────────────

@router.post("/templates/validate", response_model=WorkflowValidationResult)
async def validate_template(
    data: WorkflowTemplateCreate,
    current_user: User = Depends(_get_current_user()),
):
    """
    Dry-run validation of a workflow definition without persisting.
    Returns all structural errors and warnings.
    """
    states_raw = [s.model_dump() for s in data.states]
    transitions_raw = [t.model_dump() for t in data.transitions]
    return validate_workflow_definition(states_raw, transitions_raw)


@router.post("/templates", response_model=WorkflowTemplateResponse)
async def create_template(
    data: WorkflowTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    """
    Create a new workflow template (saved as inactive, version N).
    Must pass structural validation before being accepted.
    Activate explicitly with PUT /templates/{id}/activate.
    """
    _require_admin(current_user)
    template = await WorkflowService.create_template(db, data, current_user)
    return await WorkflowService.get_template(db, template.id)


@router.get("/templates", response_model=List[WorkflowTemplateListResponse])
async def list_templates(
    entity_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    name: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    """List all workflow templates, optionally filtered."""
    return await WorkflowService.list_templates(db, entity_type=entity_type, is_active=is_active, name=name)


@router.get("/templates/{template_id}", response_model=WorkflowTemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    """Get a single workflow template with full states and transitions."""
    return await WorkflowService.get_template(db, template_id)


@router.put("/templates/{template_id}/activate", response_model=WorkflowTemplateResponse)
async def activate_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    """
    Activate a workflow template version.
    Deactivates all other versions of the same name.
    """
    _require_admin(current_user)
    template = await WorkflowService.activate_template(db, template_id, current_user)
    return await WorkflowService.get_template(db, template.id)


# ── Instance Endpoints ─────────────────────────────────────────────────────

@router.post("/instances", response_model=WorkflowInstanceResponse)
async def start_workflow_instance(
    entity_type: str = Query(...),
    entity_id: uuid.UUID = Query(...),
    template_id: Optional[uuid.UUID] = Query(None),
    priority: Optional[int] = Query(None),
    department_id: Optional[uuid.UUID] = Query(None),
    risk_level: Optional[str] = Query(None),
    request_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    """
    Start a workflow instance for any entity.
    If template_id is not provided, the best matching active template is selected automatically.
    """
    instance = await WorkflowService.create_instance(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        current_user=current_user,
        template_id=template_id,
        priority=priority,
        department_id=department_id,
        risk_level=risk_level,
        request_type=request_type,
    )
    return await WorkflowService.build_instance_response(db, instance)


@router.get("/instances/{entity_type}/{entity_id}", response_model=WorkflowInstanceResponse)
async def get_entity_workflow_state(
    entity_type: str,
    entity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    """Get the current workflow state for any entity (most recent instance)."""
    instance = await WorkflowService.get_instance(db, entity_type, entity_id)
    if not instance:
        raise HTTPException(
            status_code=404,
            detail=f"No workflow instance found for {entity_type}/{entity_id}.",
        )
    return await WorkflowService.build_instance_response(db, instance)


@router.get("/instances/{instance_id}/detail", response_model=WorkflowInstanceResponse)
async def get_instance_by_id(
    instance_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    """Get a workflow instance by its own ID."""
    instance = await WorkflowService.get_instance_by_id(db, instance_id)
    return await WorkflowService.build_instance_response(db, instance)


@router.post("/instances/{instance_id}/transition", response_model=WorkflowInstanceResponse)
async def execute_transition(
    instance_id: uuid.UUID,
    data: WorkflowTransitionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    """
    Execute a state transition on a workflow instance.
    Server-side validates: action exists from current state, actor has required role/permission, conditions are met.
    """
    instance = await WorkflowService.execute_transition(
        db=db,
        instance_id=instance_id,
        action=data.action,
        actor=current_user,
        notes=data.notes,
        entity_context=data.entity_context,
    )
    return await WorkflowService.build_instance_response(db, instance)


@router.get("/instances/{instance_id}/history", response_model=List[WorkflowTransitionLogResponse])
async def get_instance_history(
    instance_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    """Full immutable transition log for a workflow instance."""
    from sqlalchemy import select
    from app.modules.workflow.models import WorkflowTransitionLog
    res = await db.execute(
        select(WorkflowTransitionLog)
        .where(WorkflowTransitionLog.instance_id == instance_id)
        .order_by(WorkflowTransitionLog.created_at.asc())
    )
    logs = res.scalars().all()
    return [WorkflowTransitionLogResponse.model_validate(l) for l in logs]
