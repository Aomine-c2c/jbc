import uuid
from datetime import datetime
from typing import Optional
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.iam.models import User
from app.modules.iam.api import _get_user_permissions
from app.core.authz import AuthzGuard
from app.modules.jobs.models import (
    JobCard,
    JobCardPart,
    JobCardLabour,
    JobCardExecutionEvent,
    JobCardAmendment,
    JobCardAttachment,
    JobCardComment,
    JobCardActionLog,
    JobCardCollaborator,
    WorkPackage,
    WorkPackageActionLog,
    validate_transition,
    validate_wp_transition,
    WP_TERMINAL_STATES,
    COLLABORATION_ROLES,
    WORK_PACKAGE_TYPES,
)
from app.modules.approvals.engine import ApprovalEngine
from app.modules.audit.service import AuditService
from app.modules.jobs.schemas import (
    JobCardCreate,
    JobCardUpdate,
    JobCardSubmit,
    JobCardApprove,
    JobCardReject,
    JobCardReturn,
    JobCardPlan,
    JobCardAssign,
    JobCardStart,
    JobCardHold,
    JobCardComplete,
    JobCardReview,
    JobCardVerify,
    JobCardConfirm,
    JobCardClose,
    JobCardCancel,
    JobCardAmendmentCreate,
    JobCardAttachmentCreate,
    JobReportCalculations,
    WorkPackageCreate,
    WorkPackageUpdate,
    WorkPackageTransition,
    JobCardCollaboratorCreate,
)


def compute_job_calculations(job: JobCard) -> JobReportCalculations:
    """Compute automated actual duration, labor totals, materials totals, and variances."""
    # 1. Total Labour Time & Cost
    labour_entries = getattr(job, "labour_entries", []) or []
    total_labour_hours = sum(l.hours_spent for l in labour_entries)
    total_labour_cost = sum(l.hours_spent * l.hourly_rate for l in labour_entries)

    # If no structured labour records were provided, fallback to downtime_hours with standard technician rate $25/hr
    if total_labour_hours == 0 and (job.downtime_hours or 0) > 0:
        total_labour_hours = float(job.downtime_hours)
        total_labour_cost = total_labour_hours * 25.0

    # 2. Total Spares & Materials
    parts = getattr(job, "parts", []) or []
    total_spares_cost = sum(p.quantity * (p.unit_cost or 0.0) for p in parts if not getattr(p, "is_material", False))
    total_materials_cost = sum(p.quantity * (p.unit_cost or 0.0) for p in parts if getattr(p, "is_material", False))
    total_material_cost = total_spares_cost + total_materials_cost

    # 3. Total Actual Cost
    total_actual_cost = total_labour_cost + total_material_cost

    # 4. Actual Duration Hours
    actual_duration_hours = 0.0
    if job.actual_start_time and job.actual_end_time:
        actual_duration_hours = round(max(0.0, (job.actual_end_time - job.actual_start_time).total_seconds() / 3600.0), 2)
    elif job.downtime_hours and job.downtime_hours > 0:
        actual_duration_hours = round(float(job.downtime_hours), 2)

    # 5. Variances against Estimates
    est_hours = float(job.estimated_hours or 0.0)
    est_cost = float(job.estimated_cost or 0.0)

    duration_variance_hours = round(actual_duration_hours - est_hours, 2)
    cost_variance = round(total_actual_cost - est_cost, 2)

    cost_variance_percentage = 0.0
    if est_cost > 0:
        cost_variance_percentage = round((cost_variance / est_cost) * 100.0, 1)

    variance_status = "ON_BUDGET"
    if cost_variance > 50.0:
        variance_status = "OVER_BUDGET"
    elif cost_variance < -50.0:
        variance_status = "UNDER_BUDGET"

    return JobReportCalculations(
        actual_duration_hours=actual_duration_hours,
        total_labour_hours=round(total_labour_hours, 2),
        total_labour_cost=round(total_labour_cost, 2),
        total_spares_cost=round(total_spares_cost, 2),
        total_materials_cost=round(total_materials_cost, 2),
        total_material_cost=round(total_material_cost, 2),
        total_actual_cost=round(total_actual_cost, 2),
        duration_variance_hours=duration_variance_hours,
        cost_variance=cost_variance,
        cost_variance_percentage=cost_variance_percentage,
        variance_status=variance_status,
    )


class JobCardService:

    @staticmethod
    async def create(db: AsyncSession, data: JobCardCreate, current_user: User) -> JobCard:
        user_perms = _get_user_permissions(current_user)
        print(f"DEBUG create user_perms: {user_perms}, current_user: {current_user.email}, roles: {current_user.roles}")
        if not AuthzGuard.check_permission(current_user, "job_card:create", user_perms, resource_dept_id=data.department_id):
            raise HTTPException(status_code=403, detail="Not enough privileges")
        
        # Generate human-readable Job Card Number
        year = datetime.utcnow().year
        short_id = uuid.uuid4().hex[:6].upper()
        job_number = f"JC-{year}-{short_id}"

        job = JobCard(
            job_number=job_number,
            title=data.title,
            description=data.description,
            department_id=data.department_id,
            priority=data.priority,
            creator_id=current_user.id,
            status="DRAFT",
            machine_id=data.machine_id,
            job_type=data.job_type,
            maintenance_type=data.maintenance_type,
            workshop_code=data.workshop_code,
            location=data.location,
            plant_area=data.plant_area,
            required_date=data.required_date,
            reported_issue=data.reported_issue,
            job_instruction=data.job_instruction,
            estimated_hours=data.estimated_hours or 0.0,
            estimated_cost=data.estimated_cost or 0.0,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)

        await JobCardService._record_event(
            db, job.id, "REQUESTED", operator_name=f"{current_user.first_name} {current_user.last_name}", notes="Job Card draft requested"
        )
        await JobCardService._log(
            db, job.id, current_user.id, "create", state_from=None, state_to="DRAFT", details="Created new Job Card"
        )
        return job

    @staticmethod
    async def get(db: AsyncSession, job_id: uuid.UUID, current_user: User) -> JobCard:
        user_perms = _get_user_permissions(current_user)
        result = await db.execute(select(JobCard).where(JobCard.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job card not found")
        if not AuthzGuard.check_permission(
            current_user,
            "job_card:read",
            user_perms,
            resource_owner_id=job.creator_id,
            resource_dept_id=job.department_id,
            assigned_user_id=job.supervisor_id,
        ):
            raise HTTPException(status_code=403, detail="Not enough privileges")
        return job

    @staticmethod
    async def list(db: AsyncSession, department_id: Optional[uuid.UUID], current_user: User) -> list[JobCard]:
        user_perms = _get_user_permissions(current_user)
        if department_id:
            if not AuthzGuard.check_permission(current_user, "job_card:read", user_perms, resource_dept_id=department_id):
                raise HTTPException(status_code=403, detail="Not enough privileges")

        query = select(JobCard)
        if department_id:
            query = query.where(JobCard.department_id == department_id)
        else:
            if current_user.department_id and "global_override" not in user_perms and "cross_department_access" not in user_perms:
                query = query.where(JobCard.department_id == current_user.department_id)

        query = query.order_by(JobCard.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update(db: AsyncSession, job_id: uuid.UUID, data: JobCardUpdate, current_user: User, x_draft_timestamp: Optional[str] = None) -> JobCard:
        user_perms = _get_user_permissions(current_user)
        result = await db.execute(select(JobCard).where(JobCard.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job card not found")
        if not AuthzGuard.check_permission(
            current_user,
            "job_card:update",
            user_perms,
            resource_owner_id=job.creator_id,
            resource_dept_id=job.department_id,
            assigned_user_id=job.supervisor_id,
        ):
            raise HTTPException(status_code=403, detail="Not enough privileges")

        # Optimistic concurrency control for offline sync
        if x_draft_timestamp and job.updated_at:
            from datetime import datetime
            try:
                draft_time = datetime.fromisoformat(x_draft_timestamp.replace('Z', '+00:00'))
                # If server has newer data, block it
                if job.updated_at > draft_time:
                    raise HTTPException(
                        status_code=412,
                        detail="Conflict: Job Card was updated by another user while you were offline."
                    )
            except ValueError:
                pass # Ignore malformed timestamps

        for key, value in data.model_dump(exclude_unset=True).items():
            if hasattr(job, key) and value is not None:
                setattr(job, key, value)

        await db.commit()
        await db.refresh(job)
        await JobCardService._log(
            db, job.id, current_user.id, "update", state_from=job.status, state_to=job.status, details="Updated job specifications"
        )
        return job

    @staticmethod
    async def submit(db: AsyncSession, job_id: uuid.UUID, data: Optional[JobCardSubmit], current_user: User) -> JobCard:
        result = await db.execute(select(JobCard).where(JobCard.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job card not found")

        old_state = job.status
        try:
            target_status = validate_transition(job.status, "submit")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        user_perms = _get_user_permissions(current_user)
        if not AuthzGuard.check_permission(
            current_user,
            "job_card:update",
            user_perms,
            resource_owner_id=job.creator_id,
            resource_dept_id=job.department_id,
            assigned_user_id=job.supervisor_id,
        ):
            raise HTTPException(status_code=403, detail="Not enough privileges")

        job.status = target_status
        if data and data.comments:
            db.add(JobCardComment(job_card_id=job.id, author_id=current_user.id, comment=data.comments))

        await db.commit()
        await db.refresh(job)
        await JobCardService._record_event(
            db, job.id, "SUBMITTED", operator_name=f"{current_user.first_name} {current_user.last_name}", notes="Submitted for authorization"
        )
        await JobCardService._log(
            db, job.id, current_user.id, "submit", state_from=old_state, state_to=job.status, details="Submitted for authorization"
        )
        from app.modules.notifications.engine import NotificationEngine
        await NotificationEngine.dispatch_to_role(
            db=db,
            role_name="SUPERVISOR",
            department_id=job.department_id,
            event_type="APPROVAL_REQUIRED",
            title="Job Card Submitted",
            message=f"Job Card {job.job_number} requires supervisor approval.",
            resource_type="job_card",
            resource_id=job.id,
            priority=1
        )
        return job

    @staticmethod
    async def approve(db: AsyncSession, job_id: uuid.UUID, data: JobCardApprove, current_user: User) -> JobCard:
        result = await db.execute(select(JobCard).where(JobCard.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job card not found")

        old_state = job.status
        try:
            target_status = validate_transition(job.status, "approve")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        # Delegate self-approval guard + permission check + audit to ApprovalEngine
        await ApprovalEngine.decide(
            db=db,
            resource_type="job_card",
            resource_id=job.id,
            resource_owner_id=job.creator_id,
            action="approve",
            actor=current_user,
            comment=data.comments or "Approved",
            state_from=old_state,
            state_to=target_status,
        )

        # Drive the job card state machine
        job.status = target_status
        job.approver_id = current_user.id
        job.approved_at = datetime.utcnow()
        db.add(JobCardComment(job_card_id=job.id, author_id=current_user.id, comment=f"APPROVED: {data.comments}"))

        await db.commit()
        await db.refresh(job)
        await JobCardService._record_event(
            db, job.id, "APPROVED", operator_name=f"{current_user.first_name} {current_user.last_name}", notes=data.comments
        )
        await JobCardService._log(
            db, job.id, current_user.id, "approve", state_from=old_state, state_to=job.status, details=data.comments
        )
        return job

    @staticmethod
    async def reject(db: AsyncSession, job_id: uuid.UUID, data: JobCardReject, current_user: User) -> JobCard:
        result = await db.execute(select(JobCard).where(JobCard.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job card not found")

        old_state = job.status
        try:
            target_status = validate_transition(job.status, "reject")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        # Delegate self-approval guard + audit to ApprovalEngine
        await ApprovalEngine.decide(
            db=db,
            resource_type="job_card",
            resource_id=job.id,
            resource_owner_id=job.creator_id,
            action="reject",
            actor=current_user,
            comment=data.comments or "Rejected",
            state_from=old_state,
            state_to=target_status,
        )

        job.status = target_status
        job.approver_id = current_user.id
        db.add(JobCardComment(job_card_id=job.id, author_id=current_user.id, comment=f"REJECTED: {data.comments}"))

        await db.commit()
        await db.refresh(job)
        await JobCardService._record_event(
            db, job.id, "REJECTED", operator_name=f"{current_user.first_name} {current_user.last_name}", reason=data.comments
        )
        await JobCardService._log(
            db, job.id, current_user.id, "reject", state_from=old_state, state_to=job.status, details=data.comments
        )
        return job

    @staticmethod
    async def return_for_correction(db: AsyncSession, job_id: uuid.UUID, data: JobCardReturn, current_user: User) -> JobCard:
        result = await db.execute(select(JobCard).where(JobCard.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job card not found")

        old_state = job.status
        try:
            target_status = validate_transition(job.status, "return")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        # Delegate to ApprovalEngine
        await ApprovalEngine.decide(
            db=db,
            resource_type="job_card",
            resource_id=job.id,
            resource_owner_id=job.creator_id,
            action="return",
            actor=current_user,
            comment=data.comments or "Returned for correction",
            state_from=old_state,
            state_to=target_status,
        )

        job.status = target_status
        db.add(JobCardComment(job_card_id=job.id, author_id=current_user.id, comment=f"RETURNED FOR CORRECTION: {data.comments}"))

        await db.commit()
        await db.refresh(job)
        await JobCardService._record_event(
            db, job.id, "RETURNED", operator_name=f"{current_user.first_name} {current_user.last_name}", reason=data.comments
        )
        await JobCardService._log(
            db, job.id, current_user.id, "return", state_from=old_state, state_to=job.status, details=data.comments
        )
        return job


    @staticmethod
    async def plan(db: AsyncSession, job_id: uuid.UUID, data: JobCardPlan, current_user: User) -> JobCard:
        result = await db.execute(select(JobCard).where(JobCard.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job card not found")

        old_state = job.status
        try:
            target_status = validate_transition(job.status, "plan")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        user_perms = _get_user_permissions(current_user)
        if not AuthzGuard.check_permission(
            current_user,
            "job_card:update",
            user_perms,
            resource_owner_id=job.creator_id,
            resource_dept_id=job.department_id,
            assigned_user_id=job.supervisor_id,
        ):
            raise HTTPException(status_code=403, detail="Not enough privileges")

        job.status = target_status
        if data.estimated_hours is not None:
            job.estimated_hours = data.estimated_hours
        if data.estimated_cost is not None:
            job.estimated_cost = data.estimated_cost
        if data.job_instruction is not None:
            job.job_instruction = data.job_instruction

        if data.comments:
            db.add(JobCardComment(job_card_id=job.id, author_id=current_user.id, comment=f"PLANNING NOTE: {data.comments}"))

        await db.commit()
        await db.refresh(job)
        await JobCardService._record_event(
            db, job.id, "PLANNED", operator_name=f"{current_user.first_name} {current_user.last_name}", notes="Shift planning window configured"
        )
        await JobCardService._log(
            db, job.id, current_user.id, "plan", state_from=old_state, state_to=job.status, details="Shift planning window configured"
        )
        return job

    @staticmethod
    async def assign(db: AsyncSession, job_id: uuid.UUID, data: JobCardAssign, current_user: User) -> JobCard:
        result = await db.execute(select(JobCard).where(JobCard.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job card not found")

        old_state = job.status
        try:
            target_status = validate_transition(job.status, "assign")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        user_perms = _get_user_permissions(current_user)
        if not AuthzGuard.check_permission(
            current_user,
            "job_card:update",
            user_perms,
            resource_owner_id=job.creator_id,
            resource_dept_id=job.department_id,
            assigned_user_id=job.supervisor_id,
        ):
            raise HTTPException(status_code=403, detail="Not enough privileges")

        job.status = target_status
        job.supervisor_id = data.supervisor_id
        job.assigned_date = datetime.utcnow()

        if data.assigned_personnel:
            job.assigned_personnel = data.assigned_personnel
        elif data.assigned_tech_ids:
            job.assigned_personnel = ", ".join(data.assigned_tech_ids)

        if data.comments:
            db.add(JobCardComment(job_card_id=job.id, author_id=current_user.id, comment=f"CREW ASSIGNMENT: {data.comments}"))

        await db.commit()
        await db.refresh(job)
        await JobCardService._record_event(
            db, job.id, "ASSIGNED", operator_name=f"{current_user.first_name} {current_user.last_name}", notes=f"Assigned to {job.assigned_personnel}"
        )
        await JobCardService._log(
            db, job.id, current_user.id, "assign", state_from=old_state, state_to=job.status, details=f"Assigned supervisor {data.supervisor_id}"
        )
        return job

    @staticmethod
    async def start(db: AsyncSession, job_id: uuid.UUID, data: Optional[JobCardStart], current_user: User) -> JobCard:
        result = await db.execute(select(JobCard).where(JobCard.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job card not found")

        old_state = job.status
        try:
            target_status = validate_transition(job.status, "start")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        user_perms = _get_user_permissions(current_user)
        if not AuthzGuard.check_permission(
            current_user,
            "job_card:update",
            user_perms,
            resource_owner_id=job.creator_id,
            resource_dept_id=job.department_id,
            assigned_user_id=job.supervisor_id,
        ):
            raise HTTPException(status_code=403, detail="Not enough privileges")

        job.status = target_status
        if not job.actual_start_time or old_state in ["ASSIGNED"]:
            job.actual_start_time = (data.actual_start_time if data and data.actual_start_time else datetime.utcnow())

        event_name = "RESUMED" if old_state == "ON_HOLD" else "STARTED"

        if data and data.comments:
            db.add(JobCardComment(job_card_id=job.id, author_id=current_user.id, comment=data.comments))

        await db.commit()
        await db.refresh(job)
        await JobCardService._record_event(
            db, job.id, event_name, operator_name=f"{current_user.first_name} {current_user.last_name}", notes="Execution active on site"
        )
        await JobCardService._log(
            db, job.id, current_user.id, "start", state_from=old_state, state_to=job.status, details=f"Execution {event_name.lower()} on site"
        )
        return job

    @staticmethod
    async def hold(db: AsyncSession, job_id: uuid.UUID, data: JobCardHold, current_user: User) -> JobCard:
        result = await db.execute(select(JobCard).where(JobCard.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job card not found")

        old_state = job.status
        try:
            target_status = validate_transition(job.status, "hold")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        user_perms = _get_user_permissions(current_user)
        if not AuthzGuard.check_permission(
            current_user,
            "job_card:update",
            user_perms,
            resource_owner_id=job.creator_id,
            resource_dept_id=job.department_id,
            assigned_user_id=job.supervisor_id,
        ):
            raise HTTPException(status_code=403, detail="Not enough privileges")

        job.status = target_status
        db.add(JobCardComment(job_card_id=job.id, author_id=current_user.id, comment=f"ON HOLD: {data.reason}"))

        await db.commit()
        await db.refresh(job)
        await JobCardService._record_event(
            db, job.id, "PAUSED", operator_name=f"{current_user.first_name} {current_user.last_name}", reason=data.reason
        )
        await JobCardService._log(
            db, job.id, current_user.id, "hold", state_from=old_state, state_to=job.status, details=data.reason
        )
        return job

    @staticmethod
    async def complete(db: AsyncSession, job_id: uuid.UUID, data: JobCardComplete, current_user: User) -> JobCard:
        result = await db.execute(select(JobCard).where(JobCard.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job card not found")

        old_state = job.status
        try:
            target_status = validate_transition(job.status, "complete")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        user_perms = _get_user_permissions(current_user)
        if not AuthzGuard.check_permission(
            current_user,
            "job_card:update",
            user_perms,
            resource_owner_id=job.creator_id,
            resource_dept_id=job.department_id,
            assigned_user_id=job.supervisor_id,
        ):
            raise HTTPException(status_code=403, detail="Not enough privileges")

        job.status = target_status
        job.action_taken = data.action_taken
        job.downtime_hours = data.downtime_hours
        job.actual_end_time = data.actual_end_time or datetime.utcnow()

        if data.labour_details:
            job.labour_details = data.labour_details

        # Save structured labour entries
        if data.labour_entries:
            for l in data.labour_entries:
                labour = JobCardLabour(
                    job_card_id=job.id,
                    technician_name=l.technician_name,
                    trade=l.trade,
                    hours_spent=l.hours_spent,
                    hourly_rate=l.hourly_rate,
                    notes=l.notes,
                )
                db.add(labour)

        # Save parts / materials
        if data.parts_used:
            for p in data.parts_used:
                part = JobCardPart(
                    job_card_id=job.id,
                    part_name=p.part_name,
                    part_number=p.part_number,
                    quantity=p.quantity,
                    unit_cost=p.unit_cost,
                    is_material=getattr(p, "is_material", False),
                )
                db.add(part)

        if data.completion_notes:
            job.completion_notes = data.completion_notes
            db.add(JobCardComment(job_card_id=job.id, author_id=current_user.id, comment=data.completion_notes))
        if data.comments:
            db.add(JobCardComment(job_card_id=job.id, author_id=current_user.id, comment=data.comments))

        await db.commit()
        await db.refresh(job)
        await JobCardService._record_event(
            db, job.id, "COMPLETED", operator_name=f"{current_user.first_name} {current_user.last_name}", notes="Work completed & technical report filed"
        )
        await JobCardService._log(
            db, job.id, current_user.id, "complete", state_from=old_state, state_to=job.status, details="Work completed and spares reported"
        )
        return job

    @staticmethod
    async def review(db: AsyncSession, job_id: uuid.UUID, data: Optional[JobCardReview], current_user: User) -> JobCard:
        result = await db.execute(select(JobCard).where(JobCard.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job card not found")

        old_state = job.status
        try:
            target_status = validate_transition(job.status, "review")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        user_perms = _get_user_permissions(current_user)
        if not AuthzGuard.check_permission(
            current_user,
            "job_card:update",
            user_perms,
            resource_owner_id=job.creator_id,
            resource_dept_id=job.department_id,
            assigned_user_id=job.supervisor_id,
        ):
            raise HTTPException(status_code=403, detail="Not enough privileges")

        job.status = target_status
        if data and data.comments:
            db.add(JobCardComment(job_card_id=job.id, author_id=current_user.id, comment=f"PENDING REVIEW: {data.comments}"))

        await db.commit()
        await db.refresh(job)
        await JobCardService._log(
            db, job.id, current_user.id, "review", state_from=old_state, state_to=job.status, details="Submitted for QA supervisor review"
        )
        return job

    @staticmethod
    async def verify(db: AsyncSession, job_id: uuid.UUID, data: JobCardVerify, current_user: User) -> JobCard:
        result = await db.execute(select(JobCard).where(JobCard.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job card not found")

        old_state = job.status
        try:
            target_status = validate_transition(job.status, "verify")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        user_perms = _get_user_permissions(current_user)
        if not AuthzGuard.check_permission(
            current_user,
            "job_card:verify",
            user_perms,
            resource_owner_id=job.creator_id,
            resource_dept_id=job.department_id,
            assigned_user_id=job.supervisor_id,
        ):
            raise HTTPException(status_code=403, detail="Not enough privileges")

        job.status = target_status
        job.verified_at = datetime.utcnow()
        db.add(JobCardComment(job_card_id=job.id, author_id=current_user.id, comment=f"QA VERIFIED: {data.comments}"))

        await db.commit()
        await db.refresh(job)
        await JobCardService._record_event(
            db, job.id, "SUPERVISOR_APPROVED", operator_name=f"{current_user.first_name} {current_user.last_name}", notes=data.comments
        )
        await JobCardService._log(
            db, job.id, current_user.id, "verify", state_from=old_state, state_to=job.status, details=data.comments
        )
        return job

    @staticmethod
    async def confirm(db: AsyncSession, job_id: uuid.UUID, data: JobCardConfirm, current_user: User) -> JobCard:
        result = await db.execute(select(JobCard).where(JobCard.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job card not found")

        job.requester_confirmed = data.requester_confirmed
        job.requester_notes = data.requester_notes
        job.requester_confirmed_at = datetime.utcnow()

        if data.comments:
            db.add(JobCardComment(job_card_id=job.id, author_id=current_user.id, comment=f"REQUESTER CONFIRMATION: {data.comments}"))

        await db.commit()
        await db.refresh(job)
        await JobCardService._record_event(
            db, job.id, "CONFIRMED", operator_name=f"{current_user.first_name} {current_user.last_name}", notes="Requester trial run confirmed"
        )
        await JobCardService._log(
            db, job.id, current_user.id, "confirm", state_from=job.status, state_to=job.status, details="Requester handover confirmation recorded"
        )
        return job

    @staticmethod
    async def close(db: AsyncSession, job_id: uuid.UUID, data: Optional[JobCardClose], current_user: User) -> JobCard:
        result = await db.execute(select(JobCard).where(JobCard.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job card not found")

        old_state = job.status
        try:
            target_status = validate_transition(job.status, "close")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        user_perms = _get_user_permissions(current_user)
        if not AuthzGuard.check_permission(
            current_user,
            "job_card:verify",
            user_perms,
            resource_owner_id=job.creator_id,
            resource_dept_id=job.department_id,
            assigned_user_id=job.supervisor_id,
        ):
            raise HTTPException(status_code=403, detail="Not enough privileges")

        # ── PREMATURE CLOSURE PREVENTION ───────────────────────────────────
        # Block parent JC closure if any Work Package is still active
        incomplete_wps = await db.execute(
            select(WorkPackage).where(
                WorkPackage.job_card_id == job_id,
                WorkPackage.status.notin_(list(WP_TERMINAL_STATES))
            )
        )
        still_open = incomplete_wps.scalars().all()
        if still_open:
            pkg_numbers = ", ".join(wp.package_number for wp in still_open)
            raise HTTPException(
                status_code=409,
                detail=f"Cannot close Job Card: the following Work Packages are still active: {pkg_numbers}. "
                       f"Each must be COMPLETED, VERIFIED, CANCELLED, or REJECTED before closure."
            )
        # ───────────────────────────────────────────────────────────────────

        job.status = target_status
        job.closure_date = datetime.utcnow()
        job.closed_by_id = current_user.id

        if data and data.comments:
            db.add(JobCardComment(job_card_id=job.id, author_id=current_user.id, comment=f"CLOSED: {data.comments}"))

        await db.commit()
        await db.refresh(job)
        await JobCardService._record_event(
            db, job.id, "CLOSED", operator_name=f"{current_user.first_name} {current_user.last_name}", notes="Formally closed & archived"
        )
        await JobCardService._log(
            db, job.id, current_user.id, "close", state_from=old_state, state_to=job.status, details="Formally closed and archived"
        )
        return job

    @staticmethod
    async def cancel(db: AsyncSession, job_id: uuid.UUID, data: JobCardCancel, current_user: User) -> JobCard:
        result = await db.execute(select(JobCard).where(JobCard.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job card not found")

        old_state = job.status
        try:
            target_status = validate_transition(job.status, "cancel")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        user_perms = _get_user_permissions(current_user)
        if not AuthzGuard.check_permission(
            current_user,
            "job_card:update",
            user_perms,
            resource_owner_id=job.creator_id,
            resource_dept_id=job.department_id,
            assigned_user_id=job.supervisor_id,
        ):
            raise HTTPException(status_code=403, detail="Not enough privileges")

        job.status = target_status
        db.add(JobCardComment(job_card_id=job.id, author_id=current_user.id, comment=f"CANCELLED: {data.reason}"))

        await db.commit()
        await db.refresh(job)
        await JobCardService._record_event(
            db, job.id, "CANCELLED", operator_name=f"{current_user.first_name} {current_user.last_name}", reason=data.reason
        )
        await JobCardService._log(
            db, job.id, current_user.id, "cancel", state_from=old_state, state_to=job.status, details=data.reason
        )
        return job

    @staticmethod
    async def amend(db: AsyncSession, job_id: uuid.UUID, data: JobCardAmendmentCreate, current_user: User) -> JobCard:
        """Controlled post-submission correction of report fields with strict audit trail."""
        result = await db.execute(select(JobCard).where(JobCard.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job card not found")

        user_perms = _get_user_permissions(current_user)
        if not AuthzGuard.check_permission(
            current_user,
            "job_card:update",
            user_perms,
            resource_owner_id=job.creator_id,
            resource_dept_id=job.department_id,
            assigned_user_id=job.supervisor_id,
        ):
            raise HTTPException(status_code=403, detail="Not enough privileges to perform controlled amendments")

        old_val = str(getattr(job, data.field_name, "") or "")
        
        # Apply change based on field type
        if hasattr(job, data.field_name):
            target_attr = getattr(job, data.field_name)
            if isinstance(target_attr, float):
                setattr(job, data.field_name, float(data.new_value))
            elif isinstance(target_attr, int):
                setattr(job, data.field_name, int(data.new_value))
            else:
                setattr(job, data.field_name, data.new_value)

        # Log Amendment
        amendment = JobCardAmendment(
            job_card_id=job.id,
            amended_by_id=current_user.id,
            field_name=data.field_name,
            old_value=old_val,
            new_value=data.new_value,
            amendment_reason=data.amendment_reason,
        )
        db.add(amendment)

        await db.commit()
        await db.refresh(job)

        audit_msg = f"AMENDMENT on '{data.field_name}': '{old_val}' -> '{data.new_value}'. Reason: {data.amendment_reason}"
        await JobCardService._log(
            db, job.id, current_user.id, "amend", state_from=job.status, state_to=job.status, details=audit_msg
        )
        return job

    @staticmethod
    async def add_attachment(db: AsyncSession, job_id: uuid.UUID, data: JobCardAttachmentCreate, current_user: User) -> JobCardAttachment:
        result = await db.execute(select(JobCard).where(JobCard.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job card not found")

        attachment = JobCardAttachment(
            job_card_id=job.id,
            filename=data.filename,
            file_url=data.file_url,
            file_type=data.file_type,
            file_size_kb=data.file_size_kb,
        )
        db.add(attachment)
        await db.commit()
        await db.refresh(attachment)

        await JobCardService._log(
            db, job.id, current_user.id, "attachment_added", details=f"Uploaded {data.filename}"
        )
        return attachment

    @staticmethod
    async def _record_event(
        db: AsyncSession,
        job_id: uuid.UUID,
        event_type: str,
        operator_name: Optional[str] = None,
        reason: Optional[str] = None,
        notes: Optional[str] = None,
    ):
        event = JobCardExecutionEvent(
            job_card_id=job_id,
            event_type=event_type,
            timestamp=datetime.utcnow(),
            operator_name=operator_name,
            reason=reason,
            notes=notes,
        )
        db.add(event)
        await db.commit()

    @staticmethod
    async def _log(
        db: AsyncSession,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
        action: str,
        state_from: Optional[str] = None,
        state_to: Optional[str] = None,
        details: Optional[str] = None,
    ):
        db.add(
            JobCardActionLog(
                job_card_id=job_id,
                user_id=user_id,
                action=action,
                state_from=state_from,
                state_to=state_to,
                details=details,
            )
        )
        await db.commit()

        user_res = await db.execute(select(User).where(User.id == user_id))
        user_obj = user_res.scalar_one_or_none()
        if user_obj:
            await AuditService.log_event(
                db=db,
                action=action.upper(),
                resource="JOB_CARD",
                resource_id=str(job_id),
                user=user_obj,
                previous_value={"status": state_from} if state_from else None,
                new_value={"status": state_to} if state_to else None,
                reason=details
            )

        # Publish real-time live event to SSE subscribers
        try:
            from app.core.events import event_broker
            await event_broker.publish(
                event_type=f"job_card.{action.lower()}",
                payload={
                    "job_card_id": str(job_id),
                    "action": action,
                    "state_from": state_from,
                    "state_to": state_to,
                    "details": details,
                    "actor_id": str(user_id),
                },
                channel="jobs",
            )
        except Exception:
            pass


# ── Work Package Service ────────────────────────────────────────────────

class WorkPackageService:
    """
    Handles cross-department Work Package lifecycle.
    Enforces departmental edit boundaries — only users belonging to the owning department
    (or superusers / global-permission users) may mutate a Work Package.
    """

    @staticmethod
    def _guard_dept_scope(wp: WorkPackage, current_user: User):
        """Raise 403 if user is not in the owning department and is not a superuser."""
        if current_user.is_superuser:
            return
        perms = _get_user_permissions(current_user)
        if "global_override" in perms:
            return
        if current_user.department_id != wp.owning_department_id:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Departmental boundary violation: you are not in the department that owns "
                    f"Work Package {wp.package_number}. Only the owning department may modify this WP."
                )
            )

    @staticmethod
    async def _auto_number(db: AsyncSession, job_card_id: uuid.UUID) -> str:
        """Generate next sequential WP number (WP-001, WP-002...) for the given Job Card."""
        result = await db.execute(
            select(WorkPackage).where(WorkPackage.job_card_id == job_card_id)
        )
        existing = result.scalars().all()
        n = len(existing) + 1
        return f"WP-{n:03d}"

    @staticmethod
    async def create(
        db: AsyncSession, job_card_id: uuid.UUID, data: WorkPackageCreate, current_user: User
    ) -> WorkPackage:
        # Verify parent Job Card exists
        result = await db.execute(select(JobCard).where(JobCard.id == job_card_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job Card not found")
        if job.status in ("CLOSED", "CANCELLED"):
            raise HTTPException(status_code=409, detail="Cannot add Work Packages to a closed or cancelled Job Card")

        # Validate package type
        if data.package_type not in WORK_PACKAGE_TYPES:
            raise HTTPException(status_code=422, detail=f"Invalid package_type. Choose from: {WORK_PACKAGE_TYPES}")

        # Validate prerequisite WP exists on same job card
        if data.prerequisite_wp_id:
            prereq_result = await db.execute(
                select(WorkPackage).where(
                    WorkPackage.id == data.prerequisite_wp_id,
                    WorkPackage.job_card_id == job_card_id
                )
            )
            if not prereq_result.scalar_one_or_none():
                raise HTTPException(status_code=422, detail="prerequisite_wp_id must reference a WP on the same Job Card")

        pkg_number = await WorkPackageService._auto_number(db, job_card_id)
        wp = WorkPackage(
            job_card_id=job_card_id,
            package_number=pkg_number,
            title=data.title,
            description=data.description,
            package_type=data.package_type,
            owning_department_id=data.owning_department_id,
            responsible_supervisor_id=data.responsible_supervisor_id,
            assigned_personnel=data.assigned_personnel,
            planned_start_date=data.planned_start_date,
            planned_end_date=data.planned_end_date,
            estimated_hours=data.estimated_hours,
            special_requirements=data.special_requirements,
            safety_notes=data.safety_notes,
            prerequisite_wp_id=data.prerequisite_wp_id,
            status="DRAFT",
        )
        db.add(wp)
        await db.commit()
        await db.refresh(wp)

        db.add(WorkPackageActionLog(
            work_package_id=wp.id,
            user_id=current_user.id,
            action="create",
            state_from=None,
            state_to="DRAFT",
            details=f"Work Package {pkg_number} created by {current_user.email}",
        ))
        await db.commit()

        await AuditService.log_event(
            db=db,
            action="CREATE",
            resource="WORK_PACKAGE",
            resource_id=str(wp.id),
            user=current_user,
            new_value={"status": "DRAFT", "package_number": pkg_number}
        )
        await db.refresh(wp)
        return wp

    @staticmethod
    async def list(db: AsyncSession, job_card_id: uuid.UUID, current_user: User) -> list[WorkPackage]:
        result = await db.execute(
            select(WorkPackage)
            .where(WorkPackage.job_card_id == job_card_id)
            .order_by(WorkPackage.package_number.asc())
        )
        return result.scalars().all()

    @staticmethod
    async def get(db: AsyncSession, wp_id: uuid.UUID, current_user: User) -> WorkPackage:
        result = await db.execute(select(WorkPackage).where(WorkPackage.id == wp_id))
        wp = result.scalar_one_or_none()
        if not wp:
            raise HTTPException(status_code=404, detail="Work Package not found")
        return wp

    @staticmethod
    async def update(
        db: AsyncSession, wp_id: uuid.UUID, data: WorkPackageUpdate, current_user: User
    ) -> WorkPackage:
        result = await db.execute(select(WorkPackage).where(WorkPackage.id == wp_id))
        wp = result.scalar_one_or_none()
        if not wp:
            raise HTTPException(status_code=404, detail="Work Package not found")

        # Enforce departmental edit boundary
        WorkPackageService._guard_dept_scope(wp, current_user)

        if wp.status in ("CANCELLED", "CLOSED"):
            raise HTTPException(status_code=409, detail="Cannot update a cancelled or closed Work Package")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(wp, field, value)

        await db.commit()
        await db.refresh(wp)
        db.add(WorkPackageActionLog(
            work_package_id=wp.id,
            user_id=current_user.id,
            action="update",
            state_from=wp.status,
            state_to=wp.status,
            details=f"Fields updated: {list(data.model_dump(exclude_unset=True).keys())}",
        ))
        await db.commit()

        await AuditService.log_event(
            db=db,
            action="UPDATE",
            resource="WORK_PACKAGE",
            resource_id=str(wp.id),
            user=current_user,
            reason=f"Fields updated: {list(data.model_dump(exclude_unset=True).keys())}"
        )
        await db.refresh(wp)
        return wp

    @staticmethod
    async def transition(
        db: AsyncSession, wp_id: uuid.UUID, action: str, data: WorkPackageTransition, current_user: User
    ) -> WorkPackage:
        result = await db.execute(select(WorkPackage).where(WorkPackage.id == wp_id))
        wp = result.scalar_one_or_none()
        if not wp:
            raise HTTPException(status_code=404, detail="Work Package not found")

        # Enforce departmental edit boundary
        WorkPackageService._guard_dept_scope(wp, current_user)

        old_status = wp.status
        try:
            new_status = validate_wp_transition(old_status, action)
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        # Prerequisite enforcement: WP cannot START unless its prerequisite is terminal
        if action == "start" and wp.prerequisite_wp_id:
            prereq_result = await db.execute(
                select(WorkPackage).where(WorkPackage.id == wp.prerequisite_wp_id)
            )
            prereq = prereq_result.scalar_one_or_none()
            if prereq and prereq.status not in ("COMPLETED", "VERIFIED"):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"Dependency constraint: Work Package {wp.package_number} cannot start until "
                        f"prerequisite {prereq.package_number} is COMPLETED or VERIFIED "
                        f"(current status: {prereq.status})."
                    )
                )

        wp.status = new_status
        now = datetime.utcnow()

        if action == "start" and not wp.started_at:
            wp.started_at = now
        elif action in ("complete",):
            wp.completed_at = now
            if data.work_performed:
                wp.work_performed = data.work_performed
            if data.actual_hours is not None:
                wp.actual_hours = data.actual_hours
        elif action == "verify":
            wp.verified_at = now
            wp.verified_by_id = current_user.id
        elif action == "reject":
            if data.rejection_reason:
                wp.rejection_reason = data.rejection_reason

        await db.commit()
        await db.refresh(wp)

        detail_msg = data.comments or f"{action.upper()} transition by {current_user.email}"
        db.add(WorkPackageActionLog(
            work_package_id=wp.id,
            user_id=current_user.id,
            action=action,
            state_from=old_status,
            state_to=new_status,
            details=detail_msg,
        ))
        await db.commit()

        await AuditService.log_event(
            db=db,
            action=action.upper(),
            resource="WORK_PACKAGE",
            resource_id=str(wp.id),
            user=current_user,
            previous_value={"status": old_status},
            new_value={"status": new_status},
            reason=detail_msg
        )
        await db.refresh(wp)
        return wp


# ── Collaborator Service ───────────────────────────────────────────────

class CollaboratorService:

    @staticmethod
    async def add(
        db: AsyncSession, job_card_id: uuid.UUID, data: JobCardCollaboratorCreate, current_user: User
    ) -> JobCardCollaborator:
        result = await db.execute(select(JobCard).where(JobCard.id == job_card_id))
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job Card not found")
        if job.status in ("CLOSED", "CANCELLED"):
            raise HTTPException(status_code=409, detail="Cannot modify collaborators on a closed Job Card")

        if data.role not in COLLABORATION_ROLES:
            raise HTTPException(status_code=422, detail=f"Invalid role. Choose from: {COLLABORATION_ROLES}")

        # Check for duplicate
        dup = await db.execute(
            select(JobCardCollaborator).where(
                JobCardCollaborator.job_card_id == job_card_id,
                JobCardCollaborator.department_id == data.department_id,
                JobCardCollaborator.role == data.role,
            )
        )
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="This department already has that collaboration role on this Job Card")

        collab = JobCardCollaborator(
            job_card_id=job_card_id,
            department_id=data.department_id,
            role=data.role,
            added_by_id=current_user.id,
            notes=data.notes,
        )
        db.add(collab)
        await db.commit()
        await db.refresh(collab)
        return collab

    @staticmethod
    async def list(
        db: AsyncSession, job_card_id: uuid.UUID
    ) -> list[JobCardCollaborator]:
        result = await db.execute(
            select(JobCardCollaborator).where(JobCardCollaborator.job_card_id == job_card_id)
        )
        return result.scalars().all()


def compute_overall_completion_pct(work_packages: list) -> float:
    """Compute 0-100 completion percentage from the WP collection."""
    if not work_packages:
        return 0.0
    terminal_count = sum(1 for wp in work_packages if wp.status in WP_TERMINAL_STATES)
    return round((terminal_count / len(work_packages)) * 100.0, 1)
