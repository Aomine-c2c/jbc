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
    resource_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    """Return all approval rounds for a resource (most recent first)."""
    return await ApprovalEngine.get_all_requests(db, resource_type, resource_id)


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
