import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, func, or_, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.modules.work.models import (
    WorkItem,
    WorkItemActionLog,
    WorkItemAttachment,
    WorkItemComment,
    WorkItemPart,
    WorkItemType,
    WorkItemStatus,
)
from app.modules.work.schemas import (
    WorkItemCreate,
    WorkItemUpdate,
    WorkItemTransition,
    WorkItemFollowUpCreate,
    WorkItemPartCreate,
    WorkItemResponse,
    WorkItemListResponse,
    WorkItemActionLogResponse,
    WorkItemCommentResponse,
    WorkItemPartResponse,
    WorkItemMigrationSummary,
    PreStartInspectionCreate,
    PreStartInspectionResponse,
    ChecklistItemResult,
)
from app.modules.iam.models import User, Department, Location, Scope
from app.modules.jobs.models import JobCard
from app.modules.fleet.models import Machine
from app.core.authz import AuthzGuard, _get_user_permissions
from app.modules.audit.service import AuditService


# Validated State Transition Graph for Work Items
WORK_ITEM_TRANSITIONS = {
    "DRAFT": ["SUBMITTED", "CANCELLED", "ASSIGNED", "IN_PROGRESS"],
    "SUBMITTED": ["APPROVED", "REJECTED", "RETURNED", "CANCELLED", "ASSIGNED", "IN_PROGRESS"],
    "APPROVED": ["ASSIGNED", "IN_PROGRESS", "ON_HOLD", "CANCELLED"],
    "ASSIGNED": ["IN_PROGRESS", "ON_HOLD", "CANCELLED"],
    "IN_PROGRESS": ["ON_HOLD", "COMPLETED", "CANCELLED"],
    "ON_HOLD": ["IN_PROGRESS", "CANCELLED"],
    "COMPLETED": ["VERIFIED", "RETURNED", "CLOSED"],
    "VERIFIED": ["CLOSED", "RETURNED"],
    "REJECTED": ["DRAFT", "CANCELLED"],
    "RETURNED": ["IN_PROGRESS", "DRAFT"],
    "CANCELLED": ["DRAFT"],
    "CLOSED": [],
}


class WorkItemService:

    @staticmethod
    def _generate_ref_number(work_type: str) -> str:
        year = datetime.utcnow().year
        short_id = uuid.uuid4().hex[:6].upper()
        wt = (work_type or "OTHER").upper()
        if wt == "JOB_CARD":
            return f"JC-{year}-{short_id}"
        elif wt == "MAINTENANCE":
            return f"PM-{year}-{short_id}"
        elif wt == "INSPECTION":
            return f"INS-{year}-{short_id}"
        elif wt == "FOLLOW_UP":
            return f"FLW-{year}-{short_id}"
        else:
            return f"WI-{year}-{short_id}"

    @staticmethod
    async def _compute_sla(db: AsyncSession, department_id: uuid.UUID, priority: int) -> Tuple[float, datetime]:
        """Calculates SLA duration and due timestamp based on department SLA and priority tier."""
        dept_res = await db.execute(select(Department).where(Department.id == department_id))
        dept = dept_res.scalar_one_or_none()
        base_hours = float(dept.sla_hours_default) if (dept and dept.sla_hours_default) else 24.0

        # Priority multipliers: 0 (Low -> 2x), 1 (Medium -> 1x), 2 (High -> 0.5x), 3 (Urgent -> 0.25x), 4 (Critical -> 0.1x)
        multipliers = {0: 2.0, 1: 1.0, 2: 0.5, 3: 0.25, 4: 0.1}
        mult = multipliers.get(priority, 1.0)
        sla_hours = max(1.0, round(base_hours * mult, 1))
        sla_due_at = datetime.utcnow() + timedelta(hours=sla_hours)
        return sla_hours, sla_due_at

    @staticmethod
    def _evaluate_live_sla_status(item: WorkItem) -> str:
        """Determines live SLA state (MET, WITHIN_SLA, AT_RISK, BREACHED)."""
        if item.status in ["COMPLETED", "VERIFIED", "CLOSED"]:
            if item.actual_end_time and item.sla_due_at:
                return "MET" if item.actual_end_time <= item.sla_due_at else "BREACHED"
            return "MET"
        
        if not item.sla_due_at:
            return "WITHIN_SLA"

        now = datetime.utcnow()
        if now > item.sla_due_at:
            return "BREACHED"
        
        # If less than 25% of SLA time remaining -> AT_RISK
        total_seconds = item.sla_hours * 3600.0
        remaining_seconds = (item.sla_due_at - now).total_seconds()
        if remaining_seconds < (total_seconds * 0.25):
            return "AT_RISK"

        return "WITHIN_SLA"

    # ── CRUD Operations ──────────────────────────────────────────

    @staticmethod
    async def create_work_item(db: AsyncSession, data: WorkItemCreate, current_user: User) -> WorkItem:
        user_perms = _get_user_permissions(current_user)
        if not AuthzGuard.check_permission(current_user, "job_card:create", user_perms, resource_dept_id=data.department_id):
            raise HTTPException(status_code=403, detail="Not enough privileges to create work item in this department")

        ref_number = WorkItemService._generate_ref_number(data.work_type)
        sla_hours, sla_due_at = await WorkItemService._compute_sla(db, data.department_id, data.priority)

        # Inherit location text from location node if not provided
        location_text = data.location
        if data.location_id and not location_text:
            loc_res = await db.execute(select(Location).where(Location.id == data.location_id))
            loc = loc_res.scalar_one_or_none()
            if loc:
                location_text = loc.name

        work_item = WorkItem(
            id=uuid.uuid4(),
            reference_number=ref_number,
            work_type=data.work_type.upper().strip(),
            title=data.title.strip(),
            description=data.description,
            status=WorkItemStatus.DRAFT.value,
            priority=data.priority,
            department_id=data.department_id,
            location_id=data.location_id,
            location=location_text,
            plant_area=data.plant_area,
            machine_id=data.machine_id,
            requester_id=current_user.id,
            supervisor_id=data.supervisor_id,
            assigned_personnel=data.assigned_personnel,
            external_contractor=data.external_contractor,
            due_date=data.due_date,
            estimated_hours=data.estimated_hours or 0.0,
            estimated_cost=data.estimated_cost or 0.0,
            parent_work_item_id=data.parent_work_item_id,
            source_request_id=data.source_request_id,
            job_card_id=data.job_card_id,
            sla_hours=sla_hours,
            sla_due_at=sla_due_at,
            sla_status="WITHIN_SLA",
            type_specific_data=data.type_specific_data or {},
        )
        db.add(work_item)
        await db.commit()
        await db.refresh(work_item)

        # Record action log
        log_entry = WorkItemActionLog(
            id=uuid.uuid4(),
            work_item_id=work_item.id,
            user_id=current_user.id,
            action="CREATE",
            state_from=None,
            state_to=work_item.status,
            details=f"Created {work_item.work_type} Work Item",
        )
        db.add(log_entry)
        await db.commit()

        try:
            await AuditService.log_event(
                db=db,
                user=current_user,
                action="WORK_ITEM_CREATE",
                resource="WORK_ITEM",
                resource_id=str(work_item.id),
                new_value={"ref": work_item.reference_number, "type": work_item.work_type, "title": work_item.title},
                reason=f"Created {work_item.work_type} work item {work_item.reference_number}",
            )
        except Exception:
            pass
        return work_item

    @staticmethod
    async def get_work_item(db: AsyncSession, item_id: uuid.UUID, current_user: User) -> WorkItemResponse:
        res = await db.execute(select(WorkItem).where(WorkItem.id == item_id))
        item = res.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Work item not found")

        user_perms = _get_user_permissions(current_user)
        if not AuthzGuard.check_permission(
            current_user,
            "job_card:read",
            user_perms,
            resource_owner_id=item.requester_id,
            resource_dept_id=item.department_id,
            assigned_user_id=item.supervisor_id,
        ):
            raise HTTPException(status_code=403, detail="Not enough privileges to view this work item")

        # Build detailed response
        resp = WorkItemResponse.model_validate(item)
        resp.department_name = item.department.name if item.department else None
        resp.location_breadcrumb = item.location_ref.breadcrumb if item.location_ref else (item.location or None)
        resp.machine_identifier = item.machine.identifier if item.machine else None
        resp.requester_name = f"{item.requester.first_name} {item.requester.last_name}" if item.requester else None
        resp.supervisor_name = f"{item.supervisor.first_name} {item.supervisor.last_name}" if item.supervisor else None
        resp.sla_status = WorkItemService._evaluate_live_sla_status(item)

        # Format action logs
        resp.action_logs = [
            WorkItemActionLogResponse(
                id=l.id,
                work_item_id=l.work_item_id,
                user_id=l.user_id,
                action=l.action,
                state_from=l.state_from,
                state_to=l.state_to,
                details=l.details,
                created_at=l.created_at,
                user_name=f"{l.user.first_name} {l.user.last_name}" if l.user else None,
            )
            for l in (item.action_logs or [])
        ]

        # Format comments
        resp.comments = [
            WorkItemCommentResponse(
                id=c.id,
                work_item_id=c.work_item_id,
                user_id=c.user_id,
                comment=c.comment,
                created_at=c.created_at,
                user_name=f"{c.user.first_name} {c.user.last_name}" if c.user else None,
            )
            for c in (item.comments or [])
        ]

        resp.parts = [WorkItemPartResponse.model_validate(p) for p in (item.parts or [])]
        return resp

    @staticmethod
    async def list_work_items(
        db: AsyncSession,
        current_user: User,
        work_type: Optional[str] = None,
        department_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        machine_id: Optional[uuid.UUID] = None,
        location_id: Optional[uuid.UUID] = None,
        requester_id: Optional[uuid.UUID] = None,
        supervisor_id: Optional[uuid.UUID] = None,
        search_query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[WorkItemListResponse]:
        user_perms = _get_user_permissions(current_user)
        query = select(WorkItem)

        # RBAC Scoping
        if "global_override" not in user_perms and "cross_department_access" not in user_perms:
            if current_user.department_id:
                query = query.where(
                    or_(
                        WorkItem.department_id == current_user.department_id,
                        WorkItem.requester_id == current_user.id,
                        WorkItem.supervisor_id == current_user.id,
                    )
                )

        if work_type:
            query = query.where(WorkItem.work_type == work_type.upper().strip())
        if department_id:
            query = query.where(WorkItem.department_id == department_id)
        if status:
            query = query.where(WorkItem.status == status.upper().strip())
        if priority is not None:
            query = query.where(WorkItem.priority == priority)
        if machine_id:
            query = query.where(WorkItem.machine_id == machine_id)
        if location_id:
            query = query.where(WorkItem.location_id == location_id)
        if requester_id:
            query = query.where(WorkItem.requester_id == requester_id)
        if supervisor_id:
            query = query.where(WorkItem.supervisor_id == supervisor_id)

        if search_query:
            p = f"%{search_query.strip()}%"
            query = query.where(
                or_(
                    WorkItem.reference_number.ilike(p),
                    WorkItem.title.ilike(p),
                    WorkItem.description.ilike(p),
                    WorkItem.assigned_personnel.ilike(p),
                    WorkItem.location.ilike(p),
                )
            )

        query = query.order_by(WorkItem.priority.desc(), WorkItem.created_at.desc()).limit(limit).offset(offset)
        res = await db.execute(query)
        items = res.scalars().all()

        results = []
        for item in items:
            row = WorkItemListResponse(
                id=item.id,
                reference_number=item.reference_number,
                work_type=item.work_type,
                title=item.title,
                status=item.status,
                priority=item.priority,
                department_id=item.department_id,
                department_name=item.department.name if item.department else None,
                location_breadcrumb=item.location_ref.breadcrumb if item.location_ref else (item.location or None),
                machine_identifier=item.machine.identifier if item.machine else None,
                supervisor_name=f"{item.supervisor.first_name} {item.supervisor.last_name}" if item.supervisor else None,
                assigned_personnel=item.assigned_personnel,
                due_date=item.due_date,
                sla_status=WorkItemService._evaluate_live_sla_status(item),
                job_card_id=item.job_card_id,
                created_at=item.created_at,
            )
            results.append(row)
        return results

    @staticmethod
    async def update_work_item(db: AsyncSession, item_id: uuid.UUID, data: WorkItemUpdate, current_user: User) -> WorkItem:
        res = await db.execute(select(WorkItem).where(WorkItem.id == item_id))
        item = res.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Work item not found")

        user_perms = _get_user_permissions(current_user)
        if not AuthzGuard.check_permission(
            current_user,
            "job_card:update",
            user_perms,
            resource_owner_id=item.requester_id,
            resource_dept_id=item.department_id,
            assigned_user_id=item.supervisor_id,
        ):
            raise HTTPException(status_code=403, detail="Not enough privileges to update this work item")

        for k, v in data.model_dump(exclude_unset=True).items():
            if hasattr(item, k) and v is not None:
                setattr(item, k, v)

        await db.commit()
        await db.refresh(item)

        # Record log
        log_entry = WorkItemActionLog(
            id=uuid.uuid4(),
            work_item_id=item.id,
            user_id=current_user.id,
            action="UPDATE",
            state_from=item.status,
            state_to=item.status,
            details="Updated work item parameters",
        )
        db.add(log_entry)
        await db.commit()

        return item

    @staticmethod
    async def transition_status(
        db: AsyncSession, item_id: uuid.UUID, data: WorkItemTransition, current_user: User
    ) -> WorkItem:
        res = await db.execute(select(WorkItem).where(WorkItem.id == item_id))
        item = res.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Work item not found")

        target_status = data.status.upper().strip()
        allowed = WORK_ITEM_TRANSITIONS.get(item.status, [])
        if target_status not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid state transition from '{item.status}' to '{target_status}'. Allowed: {allowed}",
            )

        user_perms = _get_user_permissions(current_user)

        # Check permissions for approval / verification
        if target_status == "APPROVED":
            if not AuthzGuard.check_permission(current_user, "job_card:approve", user_perms, resource_owner_id=item.requester_id, resource_dept_id=item.department_id):
                raise HTTPException(status_code=403, detail="Not authorized to approve this work item")
            item.approver_id = current_user.id
            item.approved_at = datetime.utcnow()
            item.approval_status = "APPROVED"
        elif target_status == "REJECTED":
            item.approval_status = "REJECTED"

        if target_status == "IN_PROGRESS" and not item.actual_start_time:
            item.actual_start_time = data.actual_start_time or datetime.utcnow()

        if target_status in ["COMPLETED", "VERIFIED", "CLOSED"]:
            if not item.actual_end_time:
                item.actual_end_time = data.actual_end_time or datetime.utcnow()
            item.sla_status = WorkItemService._evaluate_live_sla_status(item)

        if data.actual_hours is not None:
            item.actual_hours = data.actual_hours
        if data.actual_cost is not None:
            item.actual_cost = data.actual_cost

        old_status = item.status
        item.status = target_status
        await db.commit()
        await db.refresh(item)

        # Record action log
        log_entry = WorkItemActionLog(
            id=uuid.uuid4(),
            work_item_id=item.id,
            user_id=current_user.id,
            action=f"TRANSITION_{target_status}",
            state_from=old_status,
            state_to=target_status,
            details=data.comments or f"Transitioned to {target_status}",
        )
        db.add(log_entry)
        await db.commit()

        # Synchronize linked Job Card if present
        if item.job_card_id:
            jc_res = await db.execute(select(JobCard).where(JobCard.id == item.job_card_id))
            jc = jc_res.scalar_one_or_none()
            if jc and jc.status != target_status:
                jc.status = target_status
                if target_status == "IN_PROGRESS" and not jc.actual_start_time:
                    jc.actual_start_time = item.actual_start_time
                if target_status in ["COMPLETED", "VERIFIED", "CLOSED"] and not jc.actual_end_time:
                    jc.actual_end_time = item.actual_end_time
                await db.commit()

        return item

    @staticmethod
    async def create_follow_up(
        db: AsyncSession, parent_item_id: uuid.UUID, data: WorkItemFollowUpCreate, current_user: User
    ) -> WorkItem:
        """Spawns a linked corrective action / follow-up work item."""
        res = await db.execute(select(WorkItem).where(WorkItem.id == parent_item_id))
        parent = res.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent work item not found")

        create_dto = WorkItemCreate(
            title=data.title,
            description=data.description,
            work_type="FOLLOW_UP",
            department_id=parent.department_id,
            location_id=parent.location_id,
            location=parent.location,
            plant_area=parent.plant_area,
            machine_id=parent.machine_id,
            priority=data.priority,
            assigned_personnel=data.assigned_personnel,
            due_date=data.due_date,
            parent_work_item_id=parent.id,
            type_specific_data={
                "findings": data.findings,
                "corrective_actions": data.corrective_actions,
                "parent_reference": parent.reference_number,
            },
        )
        return await WorkItemService.create_work_item(db, create_dto, current_user)

    # ── Job Card Sync & Migration ─────────────────────────────────

    @staticmethod
    async def sync_job_card_to_work_item(db: AsyncSession, job: JobCard) -> WorkItem:
        """Ensures a JobCard instance is indexed into a corresponding WorkItem."""
        res = await db.execute(select(WorkItem).where(WorkItem.job_card_id == job.id))
        item = res.scalar_one_or_none()

        if not item:
            item = WorkItem(
                id=uuid.uuid4(),
                reference_number=job.job_number or f"JC-{datetime.utcnow().year}-{job.id.hex[:6].upper()}",
                work_type="JOB_CARD",
                title=job.title,
                description=job.description,
                status=job.status,
                priority=job.priority,
                department_id=job.department_id,
                location_id=job.location_id,
                location=job.location,
                plant_area=job.plant_area,
                machine_id=job.machine_id,
                requester_id=job.creator_id,
                supervisor_id=job.supervisor_id,
                assigned_personnel=job.assigned_personnel,
                external_contractor=job.external_contractor,
                due_date=job.required_date,
                actual_start_time=job.actual_start_time,
                actual_end_time=job.actual_end_time,
                estimated_hours=job.estimated_hours or 0.0,
                actual_hours=job.downtime_hours or 0.0,
                estimated_cost=job.estimated_cost or 0.0,
                job_card_id=job.id,
                approver_id=job.approver_id,
                approved_at=job.approved_at,
                approval_status="APPROVED" if job.approver_id else ("PENDING" if job.status == "SUBMITTED" else "NONE"),
                type_specific_data={
                    "job_type": job.job_type,
                    "maintenance_type": job.maintenance_type,
                    "reported_issue": job.reported_issue,
                    "job_instruction": job.job_instruction,
                    "workshop_code": job.workshop_code,
                },
            )
            db.add(item)
        else:
            item.title = job.title
            item.description = job.description
            item.status = job.status
            item.priority = job.priority
            item.location_id = job.location_id
            item.location = job.location
            item.plant_area = job.plant_area
            item.machine_id = job.machine_id
            item.supervisor_id = job.supervisor_id
            item.assigned_personnel = job.assigned_personnel
            item.actual_start_time = job.actual_start_time
            item.actual_end_time = job.actual_end_time
            item.approver_id = job.approver_id
            item.approved_at = job.approved_at

        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def migrate_historical_job_cards(db: AsyncSession) -> WorkItemMigrationSummary:
        """Non-destructively generates WorkItem records for all existing JobCards."""
        summary = WorkItemMigrationSummary()
        res = await db.execute(select(JobCard))
        job_cards = res.scalars().all()
        summary.scanned_job_cards = len(job_cards)

        for job in job_cards:
            existing = await db.execute(select(WorkItem).where(WorkItem.job_card_id == job.id))
            if not existing.scalar_one_or_none():
                await WorkItemService.sync_job_card_to_work_item(db, job)
                summary.created_work_items += 1
                summary.details.append(f"Provisioned WorkItem for Job Card {job.job_number or job.id}")
            else:
                summary.skipped += 1

        return summary

    @staticmethod
    async def record_pre_start_inspection(
        db: AsyncSession, data: PreStartInspectionCreate, current_user: User
    ) -> PreStartInspectionResponse:
        """
        Records a mandatory daily equipment pre-start walkaround inspection.
        Enforces two-tier defect gating:
        - Critical Red-Tag: Machine status -> OUT_OF_SERVICE, auto-spawns urgent JobCard.
        - Minor Defect: Spawns maintenance follow-up WorkItem, machine remains operational.
        - Clean Pass: Updates hour meter telemetry, confirms equipment operational readiness.
        """
        # 1. Fetch machine
        machine_res = await db.execute(select(Machine).where(Machine.id == data.machine_id))
        machine = machine_res.scalar_one_or_none()
        if not machine:
            raise HTTPException(status_code=404, detail=f"Machine {data.machine_id} not found")

        # 2. Update hour meter (must not decrease)
        if data.hour_meter_reading < (machine.current_hour_meter or 0.0):
            raise HTTPException(
                status_code=400,
                detail=f"Hour-meter reading ({data.hour_meter_reading}) cannot be less than current recorded hours ({machine.current_hour_meter})"
            )
        machine.current_hour_meter = data.hour_meter_reading

        # 3. Analyze checklist for defects
        has_critical = False
        has_minor = False
        critical_items = []
        minor_items = []
        for chk in data.checklist_results:
            if chk.status == "CRITICAL_RED_TAG":
                has_critical = True
                critical_items.append(chk)
            elif chk.status == "MINOR_DEFECT":
                has_minor = True
                minor_items.append(chk)

        if has_critical:
            overall_status = "CRITICAL_RED_TAG"
            is_grounded = True
        elif has_minor:
            overall_status = "DEFECTS_NOTED"
            is_grounded = False
        else:
            overall_status = "PASSED"
            is_grounded = False

        # 4. Create WorkItem for the inspection
        now = datetime.now(timezone.utc)
        count_res = await db.execute(select(func.count(WorkItem.id)).where(WorkItem.work_type == WorkItemType.INSPECTION.value))
        count = (count_res.scalar() or 0) + 1
        ref_num = f"PSI-{now.year}-{count:04d}"

        dept_id = current_user.department_id
        if not dept_id:
            dept_res = await db.execute(select(Department.id))
            dept_id = dept_res.scalars().first()

        inspection_item = WorkItem(
            id=uuid.uuid4(),
            reference_number=ref_num,
            work_type=WorkItemType.INSPECTION.value,
            title=f"Pre-Start Inspection: {machine.identifier} ({overall_status})",
            description=f"Shift pre-start equipment walkaround completed by {current_user.first_name} {current_user.last_name}. "
                        f"Hour meter: {data.hour_meter_reading} hrs. Result: {overall_status}.",
            status=WorkItemStatus.COMPLETED.value if not is_grounded else WorkItemStatus.ON_HOLD.value,
            priority=4 if has_critical else (2 if has_minor else 1),
            department_id=dept_id,
            location_id=machine.location_id,
            location=machine.location,
            machine_id=machine.id,
            requester_id=current_user.id,
            type_specific_data={
                "inspection_type": "PRE_START",
                "hour_meter_reading": data.hour_meter_reading,
                "overall_status": overall_status,
                "is_grounded": is_grounded,
                "operator_notes": data.operator_notes,
                "checklist_results": [c.model_dump() for c in data.checklist_results],
            },
        )
        db.add(inspection_item)

        spawned_jc = None
        # 5. Two-Tier Defect Gating
        if has_critical:
            # Transition machine to OUT_OF_SERVICE
            machine.status = "OUT_OF_SERVICE"

            # Auto-spawn Urgent Maintenance Job Card
            jc_count_res = await db.execute(select(func.count(JobCard.id)))
            jc_count = (jc_count_res.scalar() or 0) + 1
            jc_num = f"JC-{now.year}-{1000 + jc_count}"
            defects_summary = ", ".join([f"{c.category}: {c.item}" for c in critical_items])

            spawned_jc = JobCard(
                id=uuid.uuid4(),
                job_number=jc_num,
                title=f"CRITICAL RED-TAG DEFECT: {machine.identifier}",
                description=f"Auto-generated from pre-start walkaround safety failure ({ref_num}) by Operator {current_user.first_name} {current_user.last_name}. "
                            f"Critical defects flagged: {defects_summary}. Operator notes: {data.operator_notes or 'None'}.",
                status="SUBMITTED",
                priority=4,
                department_id=dept_id,
                location_id=machine.location_id,
                location=machine.location,
                machine_id=machine.id,
                creator_id=current_user.id,
                reported_issue=defects_summary,
                job_instruction="Unit grounded. Perform immediate mechanical/safety diagnostic and repair before returning to service.",
            )
            db.add(spawned_jc)
            await db.flush()

            inspection_item.job_card_id = spawned_jc.id

            try:
                await AuditService.log_event(
                    db=db,
                    user=current_user,
                    action="PRE_START_CRITICAL_LOCKOUT",
                    resource="MACHINE",
                    resource_id=str(machine.id),
                    new_value={
                        "machine": machine.identifier,
                        "inspection_ref": ref_num,
                        "spawned_job_card": jc_num,
                        "defects": [c.item for c in critical_items],
                    },
                    reason="Machine grounded due to critical safety defect during pre-start inspection",
                )
            except Exception:
                pass
        elif has_minor:
            minor_summary = ", ".join([f"{c.category}: {c.item}" for c in minor_items])
            minor_work = WorkItem(
                id=uuid.uuid4(),
                reference_number=f"WI-{now.year}-{count + 100:04d}",
                work_type=WorkItemType.MAINTENANCE.value,
                title=f"Maintenance Follow-up: {machine.identifier} Minor Defects",
                description=f"Non-critical defect reported during pre-start ({ref_num}): {minor_summary}. Notes: {data.operator_notes or 'None'}.",
                status=WorkItemStatus.SUBMITTED.value,
                priority=2,
                department_id=dept_id,
                location_id=machine.location_id,
                location=machine.location,
                machine_id=machine.id,
                requester_id=current_user.id,
                parent_work_item_id=inspection_item.id,
            )
            db.add(minor_work)

        await db.commit()
        await db.refresh(inspection_item)
        await db.refresh(machine)

        return PreStartInspectionResponse(
            id=inspection_item.id,
            reference_number=inspection_item.reference_number,
            machine_id=machine.id,
            machine_name=machine.identifier,
            machine_status=machine.status,
            hour_meter_reading=data.hour_meter_reading,
            overall_status=overall_status,
            is_grounded=is_grounded,
            spawned_job_card_id=spawned_jc.id if spawned_jc else None,
            spawned_job_card_number=spawned_jc.job_number if spawned_jc else None,
            created_at=inspection_item.created_at,
            operator_name=f"{current_user.first_name} {current_user.last_name}",
            checklist_results=data.checklist_results,
            operator_notes=data.operator_notes,
        )

    @staticmethod
    async def list_pre_start_inspections(
        db: AsyncSession,
        machine_id: Optional[uuid.UUID] = None,
        operator_id: Optional[uuid.UUID] = None,
        limit: int = 50,
    ) -> List[PreStartInspectionResponse]:
        query = select(WorkItem).where(
            WorkItem.work_type == WorkItemType.INSPECTION.value,
            WorkItem.reference_number.like("PSI-%"),
        )
        if machine_id:
            query = query.where(WorkItem.machine_id == machine_id)
        if operator_id:
            query = query.where(WorkItem.requester_id == operator_id)

        query = query.order_by(WorkItem.created_at.desc()).limit(limit)
        res = await db.execute(query)
        items = res.scalars().all()

        out = []
        for item in items:
            t_data = item.type_specific_data or {}
            m_res = await db.execute(select(Machine).where(Machine.id == item.machine_id))
            m = m_res.scalar_one_or_none()
            u_res = await db.execute(select(User).where(User.id == item.requester_id))
            u = u_res.scalar_one_or_none()
            jc_num = None
            if item.job_card_id:
                jc_res = await db.execute(select(JobCard.job_number).where(JobCard.id == item.job_card_id))
                jc_num = jc_res.scalar()

            chks = []
            for c in t_data.get("checklist_results", []):
                chks.append(ChecklistItemResult(**c))

            out.append(
                PreStartInspectionResponse(
                    id=item.id,
                    reference_number=item.reference_number,
                    machine_id=item.machine_id or uuid.uuid4(),
                    machine_name=m.identifier if m else "Equipment",
                    machine_status=m.status if m else "UNKNOWN",
                    hour_meter_reading=float(t_data.get("hour_meter_reading", 0.0)),
                    overall_status=t_data.get("overall_status", "PASSED"),
                    is_grounded=bool(t_data.get("is_grounded", False)),
                    spawned_job_card_id=item.job_card_id,
                    spawned_job_card_number=jc_num,
                    created_at=item.created_at,
                    operator_name=f"{u.first_name} {u.last_name}" if u else "Operator",
                    checklist_results=chks,
                    operator_notes=t_data.get("operator_notes"),
                )
            )
        return out

