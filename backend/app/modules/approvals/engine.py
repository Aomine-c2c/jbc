import uuid
import hmac
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.iam.models import User
from app.modules.approvals.models import ApprovalRequest, ApprovalStep, WorkflowDefinition
from app.core.config import settings
from app.modules.audit.service import AuditService
from sqlalchemy.orm import selectinload


@dataclass
class ApprovalContext:
    resource_type: str
    resource_id: uuid.UUID
    resource_owner_id: uuid.UUID
    department_id: uuid.UUID
    current_status: str
    priority: int = 0
    estimated_cost: float = 0.0
    risk_level: str = "LOW"
    workflow_type: str = "STANDARD"


@dataclass
class ApprovalDecision:
    approval_request_id: uuid.UUID
    step_id: uuid.UUID
    action: str
    next_resource_status: str
    all_resolved: bool
    signature_token: str


async def get_required_steps(db: AsyncSession, ctx: ApprovalContext) -> list[dict]:
    # Fetch all active workflows, ordered by priority DESC
    result = await db.execute(
        select(WorkflowDefinition)
        .where(WorkflowDefinition.is_active == True)
        .options(selectinload(WorkflowDefinition.steps))
        .order_by(WorkflowDefinition.priority.desc())
    )
    workflows = result.scalars().all()
    
    for wf in workflows:
        match = True
        if wf.resource_type and wf.resource_type != ctx.resource_type:
            match = False
        if match and wf.department_id and str(wf.department_id) != str(ctx.department_id):
            match = False
        if match and wf.min_cost is not None and ctx.estimated_cost < wf.min_cost:
            match = False
        if match and wf.min_priority is not None and ctx.priority < wf.min_priority:
            match = False
        if match and wf.risk_level and wf.risk_level != ctx.risk_level:
            match = False
        if match and wf.workflow_type and wf.workflow_type != ctx.workflow_type:
            match = False
            
        if match:
            # Sort steps by step_number
            sorted_steps = sorted(wf.steps, key=lambda s: s.step_number)
            return [
                {
                    "authority_role": s.authority_role,
                    "required_permission": s.required_permission
                }
                for s in sorted_steps
            ]
            
    # Fallback if no matching workflow found
    return [
        {
            "authority_role": "SUPERVISOR",
            "required_permission": "job_card:approve",
        }
    ]


def _generate_signature_token(
    approver_id: uuid.UUID,
    resource_id: uuid.UUID,
    action: str,
    timestamp_iso: str,
) -> str:
    payload = f"{approver_id}:{resource_id}:{action}:{timestamp_iso}"
    key = settings.get_secret_key.encode("utf-8")
    raw = hmac.new(key, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"SIG-{raw[:32].upper()}"


def _user_can_act_on_step(user: User, step: ApprovalStep) -> bool:
    if getattr(user, "is_superuser", False):
        return True
    mock_perms = getattr(user, "mock_permissions", None)
    if mock_perms:
        return step.required_permission in mock_perms or "approval:decide" in mock_perms
    from app.modules.iam.api import _get_user_permissions
    user_perms = _get_user_permissions(user)
    return step.required_permission in user_perms or "global_override" in user_perms


def _get_actor_role_name(user: User) -> str:
    try:
        roles = getattr(user, "roles", []) or []
        for ur in roles:
            if ur.role:
                return ur.role.name
    except Exception:
        pass
    if getattr(user, "is_superuser", False):
        return "System Administrator"
    return "Authorized User"


class ApprovalEngine:

    @staticmethod
    async def open_request(
        db: AsyncSession,
        ctx: ApprovalContext,
        actor: User,
    ) -> ApprovalRequest:
        existing = await db.execute(
            select(ApprovalRequest)
            .where(
                ApprovalRequest.resource_type == ctx.resource_type,
                ApprovalRequest.resource_id == ctx.resource_id,
                ApprovalRequest.status == "OPEN",
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail="An open approval request already exists for this resource.",
            )
        step_defs = await get_required_steps(db, ctx)
        req = ApprovalRequest(
            resource_type=ctx.resource_type,
            resource_id=ctx.resource_id,
            workflow_type=ctx.workflow_type,
            priority=ctx.priority,
            risk_level=ctx.risk_level,
            estimated_cost=ctx.estimated_cost,
            status="OPEN",
            created_by_id=actor.id,
        )
        db.add(req)
        await db.flush()
        
        first_step_role = None
        for i, step_def in enumerate(step_defs, start=1):
            if i == 1:
                first_step_role = step_def["authority_role"]
                
            step = ApprovalStep(
                approval_request_id=req.id,
                step_number=i,
                authority_role=step_def["authority_role"],
                required_permission=step_def["required_permission"],
                status="PENDING",
            )
            db.add(step)
            
        await db.commit()
        await db.refresh(req)
        
        # Notify the approvers for the first step
        if first_step_role:
            from app.modules.notifications.engine import NotificationEngine
            await NotificationEngine.dispatch_to_role(
                db=db,
                role_name=first_step_role,
                department_id=actor.department_id,
                event_type="APPROVAL_REQUIRED",
                title="New Approval Required",
                message=f"{actor.first_name} {actor.last_name} submitted a {ctx.resource_type} for approval.",
                resource_type=ctx.resource_type,
                resource_id=ctx.resource_id,
                priority=1 if ctx.priority >= 3 else 0
            )

        # Publish SSE real-time event
        try:
            from app.core.events import event_broker
            await event_broker.publish(
                event_type="approval.requested",
                payload={
                    "request_id": str(req.id),
                    "resource_type": ctx.resource_type,
                    "resource_id": str(ctx.resource_id),
                    "first_step_role": first_step_role,
                    "workflow_type": ctx.workflow_type,
                    "requester_name": f"{actor.first_name} {actor.last_name}",
                },
                department_id=str(actor.department_id) if actor.department_id else None,
                channel="approvals",
            )
        except Exception:
            pass
            
        return req

    @staticmethod
    async def get_active_request(
        db: AsyncSession,
        resource_type: str,
        resource_id: uuid.UUID,
    ) -> Optional[ApprovalRequest]:
        result = await db.execute(
            select(ApprovalRequest)
            .where(
                ApprovalRequest.resource_type == resource_type,
                ApprovalRequest.resource_id == resource_id,
                ApprovalRequest.status == "OPEN",
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_request_by_id(
        db: AsyncSession,
        request_id: uuid.UUID,
    ) -> ApprovalRequest:
        result = await db.execute(
            select(ApprovalRequest).where(ApprovalRequest.id == request_id)
        )
        req = result.scalar_one_or_none()
        if not req:
            raise HTTPException(status_code=404, detail="Approval request not found.")
        return req

    @staticmethod
    async def get_all_requests(
        db: AsyncSession,
        resource_type: str,
        resource_id: uuid.UUID,
    ) -> list[ApprovalRequest]:
        result = await db.execute(
            select(ApprovalRequest)
            .where(
                ApprovalRequest.resource_type == resource_type,
                ApprovalRequest.resource_id == resource_id,
            )
            .order_by(ApprovalRequest.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def decide(
        db: AsyncSession,
        resource_type: str,
        resource_id: uuid.UUID,
        resource_owner_id: uuid.UUID,
        action: str,
        actor: User,
        comment: str,
        state_from: str,
        state_to: str,
        ip_address: Optional[str] = None,
    ) -> ApprovalDecision:
        from app.modules.iam.api import _get_user_permissions
        user_perms = _get_user_permissions(actor)
        has_global = "global_override" in user_perms

        if str(actor.id) == str(resource_owner_id) and not has_global:
            raise HTTPException(
                status_code=409,
                detail="Separation of Duties: You cannot approve a request you created.",
            )

        req = await ApprovalEngine.get_active_request(db, resource_type, resource_id)
        if not req:
            req = ApprovalRequest(
                resource_type=resource_type,
                resource_id=resource_id,
                workflow_type="STANDARD",
                priority=0,
                risk_level="LOW",
                estimated_cost=0.0,
                status="OPEN",
                created_by_id=resource_owner_id,
            )
            db.add(req)
            await db.flush()
            step = ApprovalStep(
                approval_request_id=req.id,
                step_number=1,
                authority_role="SUPERVISOR",
                required_permission="job_card:approve",
                status="PENDING",
            )
            db.add(step)
            await db.flush()
            await db.refresh(req)

        pending_step: Optional[ApprovalStep] = None
        for step in sorted(req.steps, key=lambda s: s.step_number):
            if step.status == "PENDING":
                pending_step = step
                break

        if not pending_step:
            raise HTTPException(
                status_code=409,
                detail="No pending approval step found. This request may already be resolved.",
            )

        if not _user_can_act_on_step(actor, pending_step):
            raise HTTPException(
                status_code=403,
                detail=f"You do not have the required authority ({pending_step.authority_role}) for this approval step.",
            )

        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        sig_token = _generate_signature_token(actor.id, resource_id, action, now_iso)

        actor_name = f"{actor.first_name} {actor.last_name}".strip()
        role_name = _get_actor_role_name(actor)

        pending_step.approver_id = actor.id
        pending_step.approver_name = actor_name
        pending_step.approver_role_name = role_name
        pending_step.action = action
        pending_step.comment = comment
        pending_step.state_from = state_from
        pending_step.state_to = state_to
        pending_step.signature_token = sig_token
        pending_step.ip_address = ip_address
        pending_step.timestamp = now

        if action == "approve":
            pending_step.status = "APPROVED"
        elif action == "reject":
            pending_step.status = "REJECTED"
        elif action == "return":
            pending_step.status = "RETURNED"
        elif action == "delegate":
            pending_step.status = "DELEGATED"
        elif action == "escalate":
            pending_step.status = "ESCALATED"

        all_resolved = False
        if action == "approve":
            remaining = [s for s in req.steps if s.status == "PENDING" and s.id != pending_step.id]
            all_resolved = len(remaining) == 0
        elif action in ("reject", "return"):
            for s in req.steps:
                if s.status == "PENDING" and s.id != pending_step.id:
                    s.status = "SKIPPED"
            all_resolved = True

        if all_resolved:
            if action == "approve":
                req.status = "APPROVED"
            elif action == "reject":
                req.status = "REJECTED"
            elif action == "return":
                req.status = "RETURNED"
            req.resolved_at = now

        await db.commit()
        await db.refresh(req)

        await AuditService.log_event(
            db=db,
            action=action.upper(),
            resource="APPROVAL_REQUEST",
            resource_id=str(req.id),
            user=actor,
            reason=comment
        )

        # Notify resource owner of decision
        from app.modules.notifications.engine import NotificationEngine
        event_type = f"APPROVAL_{action.upper()}D"
        title = f"Request {action.capitalize()}d"
        message = f"Your request for {resource_type} has been {action.capitalize()}d by {actor_name}."
        await NotificationEngine.dispatch(
            db=db,
            user_ids=[resource_owner_id],
            event_type=event_type,
            title=title,
            message=message,
            resource_type=resource_type,
            resource_id=resource_id,
            priority=1 if action in ("reject", "return") else 0
        )

        # Publish SSE real-time event
        try:
            from app.core.events import event_broker
            await event_broker.publish(
                event_type="approval.decided",
                payload={
                    "request_id": str(req.id),
                    "resource_type": resource_type,
                    "resource_id": str(resource_id),
                    "action": action,
                    "state_to": state_to,
                    "all_resolved": all_resolved,
                    "decider_name": actor_name,
                },
                user_id=str(resource_owner_id),
                channel="approvals",
            )
        except Exception:
            pass

        return ApprovalDecision(
            approval_request_id=req.id,
            step_id=pending_step.id,
            action=action,
            next_resource_status=state_to,
            all_resolved=all_resolved,
            signature_token=sig_token,
        )

    @staticmethod
    async def delegate(
        db: AsyncSession,
        resource_type: str,
        resource_id: uuid.UUID,
        actor: User,
        delegate_to_id: uuid.UUID,
        delegate_to_name: str,
        comment: str,
        ip_address: Optional[str] = None,
    ) -> ApprovalStep:
        req = await ApprovalEngine.get_active_request(db, resource_type, resource_id)
        if not req:
            raise HTTPException(status_code=404, detail="No open approval request.")
        pending_step = next(
            (s for s in sorted(req.steps, key=lambda s: s.step_number) if s.status == "PENDING"),
            None
        )
        if not pending_step:
            raise HTTPException(status_code=409, detail="No pending step to delegate.")
        if not _user_can_act_on_step(actor, pending_step):
            raise HTTPException(status_code=403, detail="Not authorized to delegate this step.")
        now = datetime.now(timezone.utc)
        sig_token = _generate_signature_token(actor.id, resource_id, "delegate", now.isoformat())
        actor_name = f"{actor.first_name} {actor.last_name}".strip()
        pending_step.approver_id = actor.id
        pending_step.approver_name = actor_name
        pending_step.approver_role_name = _get_actor_role_name(actor)
        pending_step.action = "delegate"
        pending_step.comment = comment
        pending_step.status = "DELEGATED"
        pending_step.delegated_to_id = delegate_to_id
        pending_step.delegated_to_name = delegate_to_name
        pending_step.signature_token = sig_token
        pending_step.ip_address = ip_address
        pending_step.timestamp = now
        new_step = ApprovalStep(
            approval_request_id=req.id,
            step_number=pending_step.step_number,
            authority_role=pending_step.authority_role,
            required_permission=pending_step.required_permission,
            status="PENDING",
        )
        db.add(new_step)
        await db.commit()
        await db.refresh(new_step)
        
        await AuditService.log_event(
            db=db,
            action="DELEGATE",
            resource="APPROVAL_REQUEST",
            resource_id=str(req.id),
            user=actor,
            reason=comment,
            new_value={"delegated_to_id": str(delegate_to_id)}
        )
        
        return new_step

    @staticmethod
    async def escalate(
        db: AsyncSession,
        resource_type: str,
        resource_id: uuid.UUID,
        actor: User,
        comment: str,
        ip_address: Optional[str] = None,
    ) -> ApprovalRequest:
        req = await ApprovalEngine.get_active_request(db, resource_type, resource_id)
        if not req:
            raise HTTPException(status_code=404, detail="No open approval request.")
        pending_step = next(
            (s for s in sorted(req.steps, key=lambda s: s.step_number) if s.status == "PENDING"),
            None
        )
        if not pending_step:
            raise HTTPException(status_code=409, detail="No pending step to escalate.")
        now = datetime.now(timezone.utc)
        sig_token = _generate_signature_token(actor.id, resource_id, "escalate", now.isoformat())
        actor_name = f"{actor.first_name} {actor.last_name}".strip()
        pending_step.approver_id = actor.id
        pending_step.approver_name = actor_name
        pending_step.approver_role_name = _get_actor_role_name(actor)
        pending_step.action = "escalate"
        pending_step.comment = comment
        pending_step.status = "ESCALATED"
        pending_step.signature_token = sig_token
        pending_step.ip_address = ip_address
        pending_step.timestamp = now
        max_step = max(s.step_number for s in req.steps)
        escalation_step = ApprovalStep(
            approval_request_id=req.id,
            step_number=max_step + 1,
            authority_role="FINAL_APPROVER",
            required_permission="approval:final_approve",
            status="PENDING",
        )
        db.add(escalation_step)
        req.status = "ESCALATED"
        await db.commit()
        await db.refresh(req)
        
        await AuditService.log_event(
            db=db,
            action="ESCALATE",
            resource="APPROVAL_REQUEST",
            resource_id=str(req.id),
            user=actor,
            reason=comment
        )
        
        return req

    @staticmethod
    async def get_pending_approvals_for_user(
        db: AsyncSession,
        user: User
    ) -> list[dict]:
        from app.core.authz import AuthzGuard
        from app.modules.jobs.models import JobCard
        from app.modules.fleet.models import MachineRequisition
        from sqlalchemy.orm import selectinload

        user_perms = AuthzGuard.get_user_permissions(user)
        has_global = "global_override" in user_perms

        # Get all OPEN requests
        result = await db.execute(
            select(ApprovalRequest)
            .options(selectinload(ApprovalRequest.steps))
            .where(ApprovalRequest.status == "OPEN")
        )
        all_open_reqs = result.scalars().all()

        pending_inbox = []
        for req in all_open_reqs:
            # Find the active step
            pending_step = None
            for step in sorted(req.steps, key=lambda s: s.step_number):
                if step.status == "PENDING":
                    pending_step = step
                    break

            if not pending_step:
                continue

            # Check if user can act on this step
            can_act = False
            if has_global:
                can_act = True
            elif pending_step.delegated_to_id == user.id:
                can_act = True
            elif pending_step.required_permission in user_perms:
                # If they have the required permission (e.g. 'job_card:approve')
                # Wait, they also need the authority role matching their actual role, 
                # OR we just rely on the permission. engine.py relies on both in some cases.
                # Let's simplify: if they have the permission and their role matches the authority role, 
                # or if the required_permission is enough.
                # From _user_can_act_on_step:
                # has_role = any(r.name == pending_step.authority_role for r in actor.roles)
                # For this, let's just use _user_can_act_on_step
                can_act = _user_can_act_on_step(user, pending_step)

            if can_act:
                # Resolve preview
                title = ""
                description = ""
                requester_name = "Unknown"
                department_name = None

                if req.resource_type == "job_card":
                    jc = await db.execute(select(JobCard).options(selectinload(JobCard.creator)).where(JobCard.id == req.resource_id))
                    job = jc.scalar_one_or_none()
                    if job:
                        title = job.title
                        description = job.description or ""
                        creator = getattr(job, "creator", None)
                        if creator:
                            first_name = getattr(creator, "first_name", "") or ""
                            last_name = getattr(creator, "last_name", "") or ""
                            requester_name = f"{first_name} {last_name}".strip() or "Unknown"
                elif req.resource_type == "machine_requisition":
                    mr = await db.execute(select(MachineRequisition).options(selectinload(MachineRequisition.requester), selectinload(MachineRequisition.department)).where(MachineRequisition.id == req.resource_id))
                    req_obj = mr.scalar_one_or_none()
                    if req_obj:
                        title = f"Machine Requisition {req_obj.requisition_number or ''}"
                        description = req_obj.reason or ""
                        if req_obj.requester:
                            requester_name = f"{req_obj.requester.first_name} {req_obj.requester.last_name}".strip()
                        if req_obj.department:
                            department_name = req_obj.department.name

                pending_inbox.append({
                    "approval_request": req,
                    "pending_step": pending_step,
                    "resource_title": title,
                    "resource_description": description,
                    "requester_name": requester_name,
                    "department_name": department_name
                })

        # Sort by priority desc, created_at asc
        pending_inbox.sort(key=lambda x: (-x["approval_request"].priority, x["approval_request"].created_at))
        return pending_inbox
