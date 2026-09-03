import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.iam.models import User
from app.modules.approvals.engine import ApprovalEngine, ApprovalContext
from app.modules.approvals.schemas import (
    ApprovalRequestOut,
    ApprovalDecideRequest,
    ApprovalDelegateRequest,
    ApprovalEscalateRequest,
    ApprovalOpenRequest,
    ApprovalDecisionOut,
    ApprovalInboxItem,
)

approvals_router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])


def _get_current_user():
    from app.main import get_current_user as gcu
    return gcu


def _client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@approvals_router.get("/pending", response_model=list[ApprovalInboxItem])
async def get_pending_approvals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    """Return all pending approvals assigned to the current user."""
    return await ApprovalEngine.get_pending_approvals_for_user(db, current_user)


@approvals_router.get("/{resource_type}/{resource_id}", response_model=list[ApprovalRequestOut])
async def get_approval_history(
    resource_type: str,
    resource_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    """Return all approval rounds for a resource (most recent first)."""
    try:
        parsed_id = uuid.UUID(resource_id)
    except ValueError:
        return []
    return await ApprovalEngine.get_all_requests(db, resource_type, parsed_id)


@approvals_router.post("/{resource_type}/{resource_id}/open", response_model=ApprovalRequestOut)
async def open_approval_request(
    resource_type: str,
    resource_id: uuid.UUID,
    data: ApprovalOpenRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    """Open a new approval round. Called when a resource is submitted for approval."""
    ctx = ApprovalContext(
        resource_type=resource_type,
        resource_id=resource_id,
        resource_owner_id=data.resource_owner_id,
        department_id=data.department_id,
        current_status=data.current_status,
        priority=data.priority,
        estimated_cost=data.estimated_cost,
        risk_level=data.risk_level,
        workflow_type=data.workflow_type,
    )
    req = await ApprovalEngine.open_request(db, ctx, current_user)
    return req


@approvals_router.post("/{resource_type}/{resource_id}/decide", response_model=ApprovalDecisionOut)
async def decide_approval(
    resource_type: str,
    resource_id: uuid.UUID,
    data: ApprovalDecideRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    """
    Act on the current pending approval step.
    action: approve | reject | return | delegate | escalate
    """
    if data.action not in ("approve", "reject", "return", "delegate", "escalate"):
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="Invalid action. Must be one of: approve, reject, return, delegate, escalate")

    decision = await ApprovalEngine.decide(
        db=db,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_owner_id=data.resource_owner_id,
        action=data.action,
        actor=current_user,
        comment=data.comment,
        state_from=data.state_from,
        state_to=data.state_to,
        ip_address=_client_ip(request),
    )
    return ApprovalDecisionOut(
        approval_request_id=decision.approval_request_id,
        step_id=decision.step_id,
        action=decision.action,
        next_resource_status=decision.next_resource_status,
        all_resolved=decision.all_resolved,
        signature_token=decision.signature_token,
    )


@approvals_router.post("/{resource_type}/{resource_id}/delegate", response_model=ApprovalRequestOut)
async def delegate_approval(
    resource_type: str,
    resource_id: uuid.UUID,
    data: ApprovalDelegateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    """Delegate the current pending approval step to another user."""
    await ApprovalEngine.delegate(
        db=db,
        resource_type=resource_type,
        resource_id=resource_id,
        actor=current_user,
        delegate_to_id=data.delegate_to_id,
        delegate_to_name=data.delegate_to_name,
        comment=data.comment,
        ip_address=_client_ip(request),
    )
    req = await ApprovalEngine.get_active_request(db, resource_type, resource_id)
    if not req:
        reqs = await ApprovalEngine.get_all_requests(db, resource_type, resource_id)
        req = reqs[0]
    return req


@approvals_router.post("/{resource_type}/{resource_id}/escalate", response_model=ApprovalRequestOut)
async def escalate_approval(
    resource_type: str,
    resource_id: uuid.UUID,
    data: ApprovalEscalateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    """Escalate the current approval round to a final approver."""
    req = await ApprovalEngine.escalate(
        db=db,
        resource_type=resource_type,
        resource_id=resource_id,
        actor=current_user,
        comment=data.comment,
        ip_address=_client_ip(request),
    )
    return req


@approvals_router.get("/{resource_type}/{resource_id}/certificate", response_model=ApprovalRequestOut)
async def get_approval_certificate(
    resource_type: str,
    resource_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    """Return the most recent resolved approval request for certificate generation."""
    reqs = await ApprovalEngine.get_all_requests(db, resource_type, resource_id)
    resolved = [r for r in reqs if r.status in ("APPROVED", "REJECTED", "RETURNED")]
    if resolved:
        return resolved[0]
    if reqs:
        return reqs[0]
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="No approval history found for this resource.")

# --- Workflow Definitions ---
from app.modules.approvals.schemas import (
    WorkflowDefinitionOut,
    WorkflowDefinitionCreate,
    WorkflowDefinitionUpdate
)
from app.modules.approvals.models import WorkflowDefinition, WorkflowStepDef
from sqlalchemy import select
from sqlalchemy.orm import selectinload

@approvals_router.get("/admin/workflows", response_model=list[WorkflowDefinitionOut])
async def list_workflows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    """List all workflow definitions."""
    from app.core.authz import require_permission
    require_permission(current_user, "settings:manage")
    
    result = await db.execute(
        select(WorkflowDefinition)
        .options(selectinload(WorkflowDefinition.steps))
        .order_by(WorkflowDefinition.priority.desc())
    )
    return result.scalars().all()


@approvals_router.post("/admin/workflows", response_model=WorkflowDefinitionOut)
async def create_workflow(
    data: WorkflowDefinitionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    from app.core.authz import require_permission
    from app.modules.audit.service import AuditService
    require_permission(current_user, "settings:manage")

    wf = WorkflowDefinition(
        name=data.name,
        description=data.description,
        resource_type=data.resource_type,
        department_id=data.department_id,
        min_cost=data.min_cost,
        min_priority=data.min_priority,
        risk_level=data.risk_level,
        workflow_type=data.workflow_type,
        is_active=data.is_active,
        priority=data.priority,
    )
    db.add(wf)
    await db.flush()

    for step_data in data.steps:
        step = WorkflowStepDef(
            workflow_id=wf.id,
            step_number=step_data.step_number,
            authority_role=step_data.authority_role,
            required_permission=step_data.required_permission
        )
        db.add(step)

    await db.commit()
    await db.refresh(wf)

    await AuditService.log_event(
        db=db,
        action="CREATE",
        resource="WORKFLOW_DEFINITION",
        resource_id=str(wf.id),
        user=current_user,
        new_value=data.model_dump(),
        ip_address=_client_ip(request)
    )

    return wf


@approvals_router.put("/admin/workflows/{workflow_id}", response_model=WorkflowDefinitionOut)
async def update_workflow(
    workflow_id: uuid.UUID,
    data: WorkflowDefinitionUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    from app.core.authz import require_permission
    from fastapi import HTTPException
    from app.modules.audit.service import AuditService
    require_permission(current_user, "settings:manage")

    result = await db.execute(
        select(WorkflowDefinition)
        .options(selectinload(WorkflowDefinition.steps))
        .where(WorkflowDefinition.id == workflow_id)
    )
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Capture previous state
    previous_state = {
        "name": wf.name,
        "description": wf.description,
        "resource_type": wf.resource_type,
        "department_id": str(wf.department_id) if wf.department_id else None,
        "min_cost": wf.min_cost,
        "min_priority": wf.min_priority,
        "risk_level": wf.risk_level,
        "workflow_type": wf.workflow_type,
        "is_active": wf.is_active,
        "priority": wf.priority,
        "steps": [{"step_number": s.step_number, "authority_role": s.authority_role, "required_permission": s.required_permission} for s in wf.steps]
    }

    update_data = data.model_dump(exclude_unset=True)
    steps_data = update_data.pop("steps", None)

    for k, v in update_data.items():
        setattr(wf, k, v)

    if steps_data is not None:
        # Replace steps entirely
        for step in wf.steps:
            await db.delete(step)
        await db.flush()
        
        for step_data in steps_data:
            step = WorkflowStepDef(
                workflow_id=wf.id,
                step_number=step_data["step_number"],
                authority_role=step_data["authority_role"],
                required_permission=step_data["required_permission"]
            )
            db.add(step)

    await db.commit()
    await db.refresh(wf)

    await AuditService.log_event(
        db=db,
        action="UPDATE",
        resource="WORKFLOW_DEFINITION",
        resource_id=str(wf.id),
        user=current_user,
        previous_value=previous_state,
        new_value=data.model_dump(exclude_unset=True),
        ip_address=_client_ip(request)
    )

    return wf


@approvals_router.delete("/admin/workflows/{workflow_id}")
async def delete_workflow(
    workflow_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    from app.core.authz import require_permission
    from fastapi import HTTPException
    from app.modules.audit.service import AuditService
    require_permission(current_user, "settings:manage")

    result = await db.execute(select(WorkflowDefinition).where(WorkflowDefinition.id == workflow_id))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    await db.delete(wf)
    await db.commit()

    await AuditService.log_event(
        db=db,
        action="DELETE",
        resource="WORKFLOW_DEFINITION",
        resource_id=str(workflow_id),
        user=current_user,
        ip_address=_client_ip(request)
    )

    return {"message": "Workflow deleted successfully"}
