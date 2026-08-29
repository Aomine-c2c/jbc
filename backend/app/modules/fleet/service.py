import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.iam.models import User
from app.modules.iam.api import _get_user_permissions
from app.core.authz import AuthzGuard
from app.modules.approvals.engine import ApprovalEngine
from app.modules.audit.service import AuditService
from app.modules.fleet.models import (
    MachineType,
    Machine,
    MachineRequisition,
    MachineReservation,
    RequisitionActionLog,
    validate_machine_transition,
    validate_requisition_transition,
)
from app.modules.fleet.schemas import (
    MachineTypeCreate,
    MachineCreate,
    MachineUpdate,
    RequisitionCreate,
    RequisitionSubmit,
    RequisitionDeptApprove,
    RequisitionEquipmentCheck,
    RequisitionApprove,
    RequisitionSchedule,
    RequisitionReserve,
    RequisitionDispatch,
    RequisitionConfirm,
    RequisitionStartUse,
    RequisitionFinish,
    RequisitionRequestReturn,
    RequisitionReturn,
    RequisitionInspect,
    RequisitionClose,
    RequisitionReject,
    RequisitionCancel,
    MachineAvailabilityItem,
    ScheduledSlot,
)


class FleetService:
    # ── Machine Types ────────────────────────────────────────────

    @staticmethod
    async def create_machine_type(db: AsyncSession, data: MachineTypeCreate) -> MachineType:
        existing = await db.execute(select(MachineType).where(MachineType.name == data.name))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Machine type already exists")
        mt = MachineType(
            name=data.name,
            description=data.description,
            category=data.category,
            hourly_rate=data.hourly_rate,
        )
        db.add(mt)
        await db.commit()
        await db.refresh(mt)
        return mt

    @staticmethod
    async def get_machine_type(db: AsyncSession, mt_id: uuid.UUID) -> MachineType:
        result = await db.execute(select(MachineType).where(MachineType.id == mt_id))
        mt = result.scalar_one_or_none()
        if not mt:
            raise HTTPException(status_code=404, detail="Machine type not found")
        return mt

    @staticmethod
    async def list_machine_types(db: AsyncSession) -> list[MachineType]:
        result = await db.execute(select(MachineType).order_by(MachineType.name))
        return result.scalars().all()

    # ── Machines ─────────────────────────────────────────────────

    @staticmethod
    async def create_machine(db: AsyncSession, data: MachineCreate, current_user: User) -> Machine:
        user_perms = _get_user_permissions(current_user)
        if not AuthzGuard.check_permission(current_user, "machines:manage", user_perms):
            raise HTTPException(status_code=403, detail="Not enough privileges")
        result = await db.execute(select(MachineType).where(MachineType.id == data.machine_type_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Machine type not found")
        m = Machine(
            machine_type_id=data.machine_type_id,
            identifier=data.identifier,
            serial_number=data.serial_number,
            location=data.location,
            capacity_rating=data.capacity_rating,
            current_hour_meter=data.current_hour_meter or 0.0,
        )
        db.add(m)
        await db.commit()
        await db.refresh(m)
        return m

    @staticmethod
    async def list_machines(db: AsyncSession, machine_type_id: Optional[uuid.UUID] = None) -> list[Machine]:
        query = select(Machine)
        if machine_type_id:
            query = query.where(Machine.machine_type_id == machine_type_id)
        query = query.order_by(Machine.identifier)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_machine(db: AsyncSession, m_id: uuid.UUID) -> Machine:
        result = await db.execute(select(Machine).where(Machine.id == m_id))
        m = result.scalar_one_or_none()
        if not m:
            raise HTTPException(status_code=404, detail="Machine not found")
        return m

    @staticmethod
    async def update_machine_status(db: AsyncSession, m_id: uuid.UUID, status: str) -> Machine:
        result = await db.execute(select(Machine).where(Machine.id == m_id))
        m = result.scalar_one_or_none()
        if not m:
            raise HTTPException(status_code=404, detail="Machine not found")
        try:
            m.status = validate_machine_transition(m.status, status)
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))
        await db.commit()
        await db.refresh(m)
        return m

    # ── Equipment Availability & Conflict Prevention ─────────────

    @staticmethod
    async def get_equipment_availability(
        db: AsyncSession,
        machine_type_id: Optional[uuid.UUID] = None,
        target_date: Optional[datetime] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[MachineAvailabilityItem]:
        """Compute live schedule slots and open booking availability for equipment."""
        query = select(Machine)
        if machine_type_id:
            query = query.where(Machine.machine_type_id == machine_type_id)
        result = await db.execute(query)
        machines = result.scalars().all()

        # Date filtering window (default: today 00:00 to +3 days)
        ref_start = start_time or (target_date or datetime.utcnow()).replace(hour=0, minute=0, second=0, microsecond=0)
        ref_end = end_time or (ref_start + timedelta(days=2))

        # Query all active reservations overlapping the window
        active_req_query = select(MachineRequisition).where(
            MachineRequisition.machine_id.is_not(None),
            MachineRequisition.status.in_(["SCHEDULED", "DISPATCHED", "IN_USE", "RETURN_REQUESTED"]),
            MachineRequisition.start_time < ref_end,
            MachineRequisition.end_time > ref_start,
        )
        active_reqs_res = await db.execute(active_req_query)
        active_reqs = active_reqs_res.scalars().all()

        # Map by machine_id
        reqs_by_machine: dict[uuid.UUID, list[MachineRequisition]] = {}
        for r in active_reqs:
            if r.machine_id:
                reqs_by_machine.setdefault(r.machine_id, []).append(r)

        availability_list: list[MachineAvailabilityItem] = []
        for m in machines:
            slots = []
            m_reqs = reqs_by_machine.get(m.id, [])
            is_avail = m.status != "MAINTENANCE"

            for r in m_reqs:
                slots.append(
                    ScheduledSlot(
                        requisition_id=r.id,
                        requisition_number=r.requisition_number,
                        purpose=r.purpose,
                        start_time=r.start_time,
                        end_time=r.end_time,
                        status=r.status,
                    )
                )
                if start_time and end_time:
                    if not (end_time <= r.start_time or start_time >= r.end_time):
                        is_avail = False

            availability_list.append(
                MachineAvailabilityItem(
                    machine_id=m.id,
                    identifier=m.identifier,
                    machine_type_id=m.machine_type_id,
                    machine_type_name=m.machine_type.name if m.machine_type else "Heavy Machine",
                    status=m.status,
                    location=m.location,
                    capacity_rating=m.capacity_rating,
                    is_available_for_window=is_avail,
                    scheduled_slots=slots,
                )
            )

        return availability_list

    @staticmethod
    async def _check_double_booking(
        db: AsyncSession,
        machine_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime,
        exclude_req_id: Optional[uuid.UUID] = None,
    ):
        """Prevent double booking: verifies no overlapping active reservations exist."""
        query = select(MachineRequisition).where(
            MachineRequisition.machine_id == machine_id,
            MachineRequisition.status.in_(["SCHEDULED", "DISPATCHED", "IN_USE", "RETURN_REQUESTED"]),
            MachineRequisition.start_time < end_time,
            MachineRequisition.end_time > start_time,
        )
        if exclude_req_id:
            query = query.where(MachineRequisition.id != exclude_req_id)

        res = await db.execute(query)
        conflict = res.scalar_one_or_none()
        if conflict:
            m_res = await db.execute(select(Machine).where(Machine.id == machine_id))
            m = m_res.scalar_one_or_none()
            m_name = m.identifier if m else str(machine_id)
            c_start = conflict.start_time.strftime("%Y-%m-%d %H:%M")
            c_end = conflict.end_time.strftime("%Y-%m-%d %H:%M")
            raise HTTPException(
                status_code=409,
                detail=f"Double booking conflict: Machine '{m_name}' is already reserved/in use from {c_start} to {c_end} on {conflict.requisition_number or 'active requisition'}.",
            )

    # ── Generic Requisition Lifecycle Service ─────────────────────

    @staticmethod
    async def create_requisition(db: AsyncSession, data: RequisitionCreate, current_user: User) -> MachineRequisition:
        user_perms = _get_user_permissions(current_user)
        if not AuthzGuard.check_permission(current_user, "requisition:create", user_perms, resource_dept_id=data.department_id):
            raise HTTPException(status_code=403, detail="Not enough privileges")
        if data.end_time <= data.start_time:
            raise HTTPException(status_code=400, detail="end_time must be after start_time")

        # Fetch machine type to calculate estimated cost
        mt_res = await db.execute(select(MachineType).where(MachineType.id == data.machine_type_id))
        mt = mt_res.scalar_one_or_none()
        if not mt:
            raise HTTPException(status_code=404, detail="Machine type not found")

        duration_hours = max(0.5, (data.end_time - data.start_time).total_seconds() / 3600.0)
        est_cost = duration_hours * (mt.hourly_rate or 50.0)

        # Generate Requisition Number
        year = datetime.utcnow().year
        short_code = uuid.uuid4().hex[:6].upper()
        req_number = f"REQ-{year}-{short_code}"

        req = MachineRequisition(
            requisition_number=req_number,
            department_id=data.department_id,
            collaborating_department_id=data.collaborating_department_id,
            requester_id=current_user.id,
            purpose=data.purpose,
            job_card_id=data.job_card_id,
            machine_type_id=data.machine_type_id,
            machine_id=data.machine_id,
            quantity=data.quantity,
            location=data.location,
            required_date=data.required_date or data.start_time,
            start_time=data.start_time,
            end_time=data.end_time,
            estimated_duration_hours=round(duration_hours, 2),
            priority=data.priority,
            operator_required=data.operator_required,
            operator_name=data.operator_name,
            special_requirements=data.special_requirements,
            safety_requirements=data.safety_requirements,
            cost_centre=data.cost_centre,
            estimated_cost=round(est_cost, 2),
            status="DRAFT",
            notes=data.notes,
        )
        db.add(req)
        await db.commit()
        await db.refresh(req)

        await FleetService._log(
            db, req.id, current_user.id, "create", state_from=None, state_to="DRAFT", details="Created new equipment requisition draft"
        )
        return req

    @staticmethod
    async def get_requisition(db: AsyncSession, req_id: uuid.UUID, current_user: User) -> MachineRequisition:
        user_perms = _get_user_permissions(current_user)
        result = await db.execute(select(MachineRequisition).where(MachineRequisition.id == req_id))
        req = result.scalar_one_or_none()
        if not req:
            raise HTTPException(status_code=404, detail="Requisition not found")
        if not AuthzGuard.check_permission(
            current_user,
            "requisition:read",
            user_perms,
            resource_owner_id=req.requester_id,
            resource_dept_id=req.department_id,
        ):
            raise HTTPException(status_code=403, detail="Not enough privileges")
        return req

    @staticmethod
    async def list_requisitions(
        db: AsyncSession,
        department_id: Optional[uuid.UUID],
        job_card_id: Optional[uuid.UUID],
        current_user: User,
    ) -> list[MachineRequisition]:
        user_perms = _get_user_permissions(current_user)
        query = select(MachineRequisition)
        if department_id:
            query = query.where(
                or_(
                    MachineRequisition.department_id == department_id,
                    MachineRequisition.collaborating_department_id == department_id,
                )
            )
        if job_card_id:
            query = query.where(MachineRequisition.job_card_id == job_card_id)

        query = query.order_by(MachineRequisition.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def submit_requisition(db: AsyncSession, req_id: uuid.UUID, data: Optional[RequisitionSubmit], current_user: User) -> MachineRequisition:
        req = await FleetService.get_requisition(db, req_id, current_user)
        old_state = req.status
        try:
            target = validate_requisition_transition(req.status, "submit")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        req.status = target
        if data and data.comments:
            req.comments = data.comments

        await db.commit()
        await db.refresh(req)
        await FleetService._log(
            db, req.id, current_user.id, "submit", state_from=old_state, state_to=req.status, details="Submitted requisition for department review"
        )
        return req

    @staticmethod
    async def dept_approve_requisition(db: AsyncSession, req_id: uuid.UUID, data: RequisitionDeptApprove, current_user: User) -> MachineRequisition:
        req = await FleetService.get_requisition(db, req_id, current_user)
        user_perms = _get_user_permissions(current_user)
        if not AuthzGuard.check_permission(current_user, "requisition:approve", user_perms, resource_dept_id=req.department_id):
            raise HTTPException(status_code=403, detail="Not enough privileges")

        old_state = req.status
        try:
            target = validate_requisition_transition(req.status, "dept_approve")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        req.status = target
        req.dept_approver_id = current_user.id
        req.dept_approved_at = datetime.utcnow()
        if data.comments:
            req.comments = data.comments

        await db.commit()
        await db.refresh(req)
        await FleetService._log(
            db, req.id, current_user.id, "dept_approve", state_from=old_state, state_to=req.status, details=data.comments or "Department approval authorized"
        )
        return req

    @staticmethod
    async def equipment_check_requisition(db: AsyncSession, req_id: uuid.UUID, data: RequisitionEquipmentCheck, current_user: User) -> MachineRequisition:
        req = await FleetService.get_requisition(db, req_id, current_user)
        user_perms = _get_user_permissions(current_user)
        if not AuthzGuard.check_permission(current_user, "machines:manage", user_perms):
            raise HTTPException(status_code=403, detail="Not enough privileges to perform equipment check")

        old_state = req.status
        try:
            target = validate_requisition_transition(req.status, "equipment_check")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        if data.machine_id:
            await FleetService._check_double_booking(db, data.machine_id, req.start_time, req.end_time, req.id)
            req.machine_id = data.machine_id

        req.status = target
        req.equipment_checker_id = current_user.id
        req.equipment_checked_at = datetime.utcnow()
        if data.comments:
            req.comments = data.comments

        await db.commit()
        await db.refresh(req)
        await FleetService._log(
            db, req.id, current_user.id, "equipment_check", state_from=old_state, state_to=req.status, details=data.comments or "Equipment check verified"
        )
        return req

    @staticmethod
    async def approve_requisition(db: AsyncSession, req_id: uuid.UUID, data: RequisitionApprove, current_user: User) -> MachineRequisition:
        req = await FleetService.get_requisition(db, req_id, current_user)

        old_state = req.status
        try:
            target = validate_requisition_transition(req.status, "approve")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        # Delegate self-approval guard + audit to ApprovalEngine
        await ApprovalEngine.decide(
            db=db,
            resource_type="machine_requisition",
            resource_id=req.id,
            resource_owner_id=req.requester_id,
            action="approve",
            actor=current_user,
            comment=data.comments or "Approved",
            state_from=old_state,
            state_to=target,
        )

        req.status = target
        req.approver_id = current_user.id
        req.approved_at = datetime.utcnow()
        req.comments = data.comments

        await db.commit()
        await db.refresh(req)
        await FleetService._log(
            db, req.id, current_user.id, "approve", state_from=old_state, state_to=req.status, details=data.comments
        )
        return req

    @staticmethod
    async def schedule_requisition(db: AsyncSession, req_id: uuid.UUID, data: RequisitionSchedule, current_user: User) -> MachineRequisition:
        req = await FleetService.get_requisition(db, req_id, current_user)
        user_perms = _get_user_permissions(current_user)
        if not AuthzGuard.check_permission(current_user, "machines:manage", user_perms):
            raise HTTPException(status_code=403, detail="Not enough privileges to schedule equipment")

        old_state = req.status
        try:
            target = validate_requisition_transition(req.status, "schedule")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        # Check double booking
        await FleetService._check_double_booking(db, data.machine_id, req.start_time, req.end_time, req.id)

        req.status = target
        req.machine_id = data.machine_id
        if data.operator_name:
            req.operator_name = data.operator_name
        req.scheduler_id = current_user.id
        req.scheduled_at = datetime.utcnow()

        # Add reservation record
        res = MachineReservation(
            requisition_id=req.id,
            machine_id=data.machine_id,
            start_time=req.start_time,
            end_time=req.end_time,
            reservation_status="SCHEDULED",
        )
        db.add(res)

        await db.commit()
        await db.refresh(req)
        await FleetService._log(
            db, req.id, current_user.id, "schedule", state_from=old_state, state_to=req.status, details=f"Scheduled equipment {data.machine_id}"
        )
        return req

    @staticmethod
    async def dispatch_requisition(db: AsyncSession, req_id: uuid.UUID, data: RequisitionDispatch, current_user: User) -> MachineRequisition:
        req = await FleetService.get_requisition(db, req_id, current_user)
        user_perms = _get_user_permissions(current_user)
        if not AuthzGuard.check_permission(current_user, "machines:manage", user_perms):
            raise HTTPException(status_code=403, detail="Not enough privileges to dispatch equipment")

        old_state = req.status
        try:
            target = validate_requisition_transition(req.status, "dispatch")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        req.status = target
        req.dispatcher_id = current_user.id
        req.dispatched_at = datetime.utcnow()

        start_meter = data.start_hour_meter or (float(data.start_hours) if data.start_hours else 0.0)
        req.start_hour_meter = start_meter
        if data.operator_name:
            req.operator_name = data.operator_name

        if req.machine_id:
            m_res = await db.execute(select(Machine).where(Machine.id == req.machine_id))
            m = m_res.scalar_one_or_none()
            if m:
                m.status = "IN_USE"

        await db.commit()
        await db.refresh(req)
        
        # Refresh the allocated machine to prevent MissingGreenlet in serialization
        if req.machine_id and m:
            await db.refresh(m)
            
        await FleetService._log(
            db, req.id, current_user.id, "dispatch", state_from=old_state, state_to=req.status, details=f"Dispatched with hour meter {start_meter}"
        )
        return req

    @staticmethod
    async def start_use_requisition(db: AsyncSession, req_id: uuid.UUID, data: Optional[RequisitionStartUse], current_user: User) -> MachineRequisition:
        req = await FleetService.get_requisition(db, req_id, current_user)
        old_state = req.status
        try:
            target = validate_requisition_transition(req.status, "start_use")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        req.status = target
        await db.commit()
        await db.refresh(req)
        await FleetService._log(
            db, req.id, current_user.id, "start_use", state_from=old_state, state_to=req.status, details="Equipment active in use on site"
        )
        return req

    @staticmethod
    async def request_return_requisition(db: AsyncSession, req_id: uuid.UUID, data: Optional[RequisitionRequestReturn], current_user: User) -> MachineRequisition:
        req = await FleetService.get_requisition(db, req_id, current_user)
        old_state = req.status
        try:
            target = validate_requisition_transition(req.status, "request_return")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        req.status = target
        req.return_requested_at = datetime.utcnow()
        await db.commit()
        await db.refresh(req)
        await FleetService._log(
            db, req.id, current_user.id, "request_return", state_from=old_state, state_to=req.status, details="Site requested equipment return / pickup"
        )
        return req

    @staticmethod
    async def return_requisition(db: AsyncSession, req_id: uuid.UUID, data: RequisitionReturn, current_user: User) -> MachineRequisition:
        req = await FleetService.get_requisition(db, req_id, current_user)
        old_state = req.status
        try:
            target = validate_requisition_transition(req.status, "return")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        req.status = target
        req.returned_at = datetime.utcnow()
        end_meter = data.end_hour_meter or (float(data.end_hours) if data.end_hours is not None else None)
        req.end_hour_meter = end_meter

        if req.machine_id:
            m_res = await db.execute(select(Machine).where(Machine.id == req.machine_id))
            m = m_res.scalar_one_or_none()
            if m:
                m.status = "AVAILABLE"
                if end_meter is not None:
                    m.current_hour_meter = end_meter

        if req.start_hour_meter is not None and end_meter is not None:
            actual_hours = max(0.5, end_meter - req.start_hour_meter)
            rate = req.machine_type.hourly_rate if req.machine_type else 50.0
            req.actual_cost = round(actual_hours * rate, 2)

        await db.commit()
        await db.refresh(req)
        
        if req.machine_id and m:
            await db.refresh(m)
            
        await FleetService._log(
            db, req.id, current_user.id, "return", state_from=old_state, state_to=req.status, details=f"Returned to yard, end meter {end_meter}"
        )
        return req

    @staticmethod
    async def inspect_requisition(db: AsyncSession, req_id: uuid.UUID, data: RequisitionInspect, current_user: User) -> MachineRequisition:
        req = await FleetService.get_requisition(db, req_id, current_user)
        user_perms = _get_user_permissions(current_user)
        if not AuthzGuard.check_permission(current_user, "machines:manage", user_perms):
            raise HTTPException(status_code=403, detail="Not enough privileges to inspect equipment")

        old_state = req.status
        try:
            target = validate_requisition_transition(req.status, "inspect")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        req.status = target
        req.inspector_id = current_user.id
        req.inspected_at = datetime.utcnow()
        req.inspection_notes = data.inspection_notes

        await db.commit()
        await db.refresh(req)
        await FleetService._log(
            db, req.id, current_user.id, "inspect", state_from=old_state, state_to=req.status, details=f"Inspection passed: {data.inspection_notes}"
        )
        return req

    @staticmethod
    async def close_requisition(db: AsyncSession, req_id: uuid.UUID, data: Optional[RequisitionClose], current_user: User) -> MachineRequisition:
        req = await FleetService.get_requisition(db, req_id, current_user)
        old_state = req.status
        try:
            target = validate_requisition_transition(req.status, "close")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        req.status = target
        req.closed_at = datetime.utcnow()
        if data and data.comments:
            req.comments = data.comments

        await db.commit()
        await db.refresh(req)
        await FleetService._log(
            db, req.id, current_user.id, "close", state_from=old_state, state_to=req.status, details="Requisition closed and archived"
        )
        return req

    @staticmethod
    async def reject_requisition(db: AsyncSession, req_id: uuid.UUID, data: RequisitionReject, current_user: User) -> MachineRequisition:
        req = await FleetService.get_requisition(db, req_id, current_user)
        user_perms = _get_user_permissions(current_user)
        if not AuthzGuard.check_permission(current_user, "requisition:approve", user_perms):
            raise HTTPException(status_code=403, detail="Not enough privileges to reject requisition")

        old_state = req.status
        try:
            target = validate_requisition_transition(req.status, "reject")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        req.status = target
        req.rejection_reason = data.comments
        req.comments = data.comments

        await db.commit()
        await db.refresh(req)
        await FleetService._log(
            db, req.id, current_user.id, "reject", state_from=old_state, state_to=req.status, details=data.comments
        )
        return req

    @staticmethod
    async def cancel_requisition(db: AsyncSession, req_id: uuid.UUID, data: RequisitionCancel, current_user: User) -> MachineRequisition:
        req = await FleetService.get_requisition(db, req_id, current_user)
        old_state = req.status
        try:
            target = validate_requisition_transition(req.status, "cancel")
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))

        req.status = target
        req.comments = f"CANCELLED: {data.reason}"

        if req.machine_id:
            m_res = await db.execute(select(Machine).where(Machine.id == req.machine_id))
            m = m_res.scalar_one_or_none()
            if m:
                m.status = "AVAILABLE"

        await db.commit()
        await db.refresh(req)
        
        if req.machine_id and m:
            await db.refresh(m)
            
        await FleetService._log(
            db, req.id, current_user.id, "cancel", state_from=old_state, state_to=req.status, details=data.reason
        )
        return req

    @staticmethod
    async def _log(
        db: AsyncSession,
        requisition_id: uuid.UUID,
        user_id: uuid.UUID,
        action: str,
        state_from: Optional[str] = None,
        state_to: Optional[str] = None,
        details: Optional[str] = None,
    ):
        db.add(
            RequisitionActionLog(
                requisition_id=requisition_id,
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
                resource="MACHINE_REQUISITION",
                resource_id=str(requisition_id),
                user=user_obj,
                previous_value={"status": state_from} if state_from else None,
                new_value={"status": state_to} if state_to else None,
                reason=details
            )
