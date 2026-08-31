import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.iam.models import User
from app.modules.fleet.service import FleetService
from app.modules.fleet.schemas import (
    MachineTypeCreate,
    MachineTypeResponse,
    MachineCreate,
    MachineUpdate,
    MachineResponse,
    RequisitionCreate,
    RequisitionSubmit,
    RequisitionReview,
    RequisitionReturnForCorrection,
    RequisitionApprove,
    RequisitionAllocate,
    RequisitionAllocatePartial,
    RequisitionDispatch,
    RequisitionMarkUnavailable,
    RequisitionReserve,
    RequisitionStartUse,
    RequisitionReturn,
    RequisitionClose,
    RequisitionReject,
    RequisitionCancel,
    RequisitionResponse,
    RequisitionListResponse,
    MachineAvailabilityItem,
    MaintenanceScheduleCreate,
    ReservationResponse,
)


def _get_current_user():
    """Lazy import to avoid circular imports."""
    from app.main import get_current_user as gcu
    return gcu


fleet_router = APIRouter(prefix="/api/v1/fleet", tags=["fleet"])


# ── Machine Types ───────────────────────────────────────────────

@fleet_router.post("/machine-types", response_model=MachineTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_machine_type(
    data: MachineTypeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.create_machine_type(db, data)


@fleet_router.get("/machine-types", response_model=list[MachineTypeResponse])
async def list_machine_types(db: AsyncSession = Depends(get_db)):
    return await FleetService.list_machine_types(db)


@fleet_router.get("/machine-types/{machine_type_id}", response_model=MachineTypeResponse)
async def get_machine_type(machine_type_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await FleetService.get_machine_type(db, machine_type_id)


# ── Machines ────────────────────────────────────────────────────

@fleet_router.post("/machines", response_model=MachineResponse, status_code=status.HTTP_201_CREATED)
async def create_machine(
    data: MachineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.create_machine(db, data, current_user)


@fleet_router.get("/machines", response_model=list[MachineResponse])
async def list_machines(
    machine_type_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    return await FleetService.list_machines(db, machine_type_id)


@fleet_router.get("/machines/{machine_id}", response_model=MachineResponse)
async def get_machine(machine_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await FleetService.get_machine(db, machine_id)


@fleet_router.patch("/machines/{machine_id}", response_model=MachineResponse)
async def update_machine(
    machine_id: uuid.UUID,
    data: MachineUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    if data.status:
        return await FleetService.update_machine_status(db, machine_id, data.status)
    raise HTTPException(status_code=400, detail="No valid fields provided for update")

@fleet_router.post("/machines/{machine_id}/maintenance", response_model=ReservationResponse)
async def schedule_machine_maintenance(
    machine_id: uuid.UUID,
    data: MaintenanceScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.schedule_maintenance(db, machine_id, data, current_user)


# ── Availability Visual Telemetry ──────────────────────────────

@fleet_router.get("/availability", response_model=list[MachineAvailabilityItem])
async def get_equipment_availability(
    machine_type_id: Optional[uuid.UUID] = None,
    target_date: Optional[datetime] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    return await FleetService.get_equipment_availability(
        db, machine_type_id, target_date, start_time, end_time
    )


# ── Requisitions ─────────────────────────────────────────────────

@fleet_router.post("/requisitions", response_model=RequisitionResponse, status_code=status.HTTP_201_CREATED)
async def create_requisition(
    data: RequisitionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.create_requisition(db, data, current_user)


@fleet_router.get("/requisitions", response_model=list[RequisitionListResponse])
async def list_requisitions(
    department_id: Optional[uuid.UUID] = None,
    job_card_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.list_requisitions(db, department_id, job_card_id, current_user)


@fleet_router.get("/requisitions/{req_id}", response_model=RequisitionResponse)
async def get_requisition(
    req_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.get_requisition(db, req_id, current_user)


@fleet_router.post("/requisitions/{req_id}/submit", response_model=RequisitionResponse)
async def submit_requisition(
    req_id: uuid.UUID,
    data: Optional[RequisitionSubmit] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.submit_requisition(db, req_id, data, current_user)


@fleet_router.post("/requisitions/{req_id}/review", response_model=RequisitionResponse)
async def review_requisition(
    req_id: uuid.UUID,
    data: Optional[RequisitionReview] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.review_requisition(
        db, req_id, data or RequisitionReview(), current_user
    )


@fleet_router.post("/requisitions/{req_id}/return-for-correction", response_model=RequisitionResponse)
async def return_for_correction_requisition(
    req_id: uuid.UUID,
    data: RequisitionReturnForCorrection,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.return_for_correction_requisition(
        db, req_id, data, current_user
    )


@fleet_router.post("/requisitions/{req_id}/approve", response_model=RequisitionResponse)
async def approve_requisition(
    req_id: uuid.UUID,
    data: RequisitionApprove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.approve_requisition(db, req_id, data, current_user)


@fleet_router.post("/requisitions/{req_id}/allocate", response_model=RequisitionResponse)
async def allocate_requisition(
    req_id: uuid.UUID,
    data: RequisitionAllocate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.allocate_requisition(db, req_id, data, current_user)


@fleet_router.post("/requisitions/{req_id}/allocate-partial", response_model=RequisitionResponse)
async def allocate_partial_requisition(
    req_id: uuid.UUID,
    data: RequisitionAllocatePartial,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.allocate_partial_requisition(db, req_id, data, current_user)


@fleet_router.post("/requisitions/{req_id}/mark-unavailable", response_model=RequisitionResponse)
async def mark_unavailable_requisition(
    req_id: uuid.UUID,
    data: RequisitionMarkUnavailable,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.mark_unavailable_requisition(db, req_id, data, current_user)


@fleet_router.post("/requisitions/{req_id}/reserve", response_model=RequisitionResponse)
async def reserve_requisition(
    req_id: uuid.UUID,
    data: RequisitionReserve,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    sched_data = RequisitionAllocate(machine_id=data.machine_id)
    return await FleetService.allocate_requisition(db, req_id, sched_data, current_user)


@fleet_router.post("/requisitions/{req_id}/start-use", response_model=RequisitionResponse)
async def start_use_requisition(
    req_id: uuid.UUID,
    data: Optional[RequisitionStartUse] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.start_use_requisition(db, req_id, data, current_user)


@fleet_router.post("/requisitions/{req_id}/return", response_model=RequisitionResponse)
async def return_requisition(
    req_id: uuid.UUID,
    data: RequisitionReturn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.return_requisition(db, req_id, data, current_user)


@fleet_router.post("/requisitions/{req_id}/close", response_model=RequisitionResponse)
async def close_requisition(
    req_id: uuid.UUID,
    data: Optional[RequisitionClose] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.close_requisition(db, req_id, data, current_user)


@fleet_router.post("/requisitions/{req_id}/reject", response_model=RequisitionResponse)
async def reject_requisition(
    req_id: uuid.UUID,
    data: RequisitionReject,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.reject_requisition(db, req_id, data, current_user)


@fleet_router.post("/requisitions/{req_id}/cancel", response_model=RequisitionResponse)
async def cancel_requisition(
    req_id: uuid.UUID,
    data: RequisitionCancel,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.cancel_requisition(db, req_id, data, current_user)


# ── Stage Aliases ────────────────────────────────────────────────

@fleet_router.post("/requisitions/{req_id}/dept-approve", response_model=RequisitionResponse)
async def dept_approve_requisition(
    req_id: uuid.UUID,
    data: Optional[RequisitionApprove] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    req = await FleetService.get_requisition(db, req_id, current_user)
    from app.modules.iam.api import _get_user_permissions
    user_perms = _get_user_permissions(current_user)
    from app.core.authz import AuthzGuard
    if not AuthzGuard.check_permission(current_user, "requisition:approve", user_perms, resource_dept_id=req.department_id):
        raise HTTPException(status_code=403, detail="Not enough privileges")
    
    old_state = req.status
    from app.modules.fleet.models import validate_requisition_transition
    target = validate_requisition_transition(req.status, "dept_approve")
    req.status = target
    req.dept_approver_id = current_user.id
    req.dept_approved_at = datetime.utcnow()
    if data and data.comments:
        req.comments = data.comments
    await db.commit()
    await db.refresh(req)
    await FleetService._log(db, req.id, current_user.id, "dept_approve", state_from=old_state, state_to=req.status, details=data.comments if data else "Department approval granted")
    return req


@fleet_router.post("/requisitions/{req_id}/equipment-check", response_model=RequisitionResponse)
async def equipment_check_requisition(
    req_id: uuid.UUID,
    data: Optional[RequisitionAllocate] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    req = await FleetService.get_requisition(db, req_id, current_user)
    from app.modules.iam.api import _get_user_permissions
    user_perms = _get_user_permissions(current_user)
    from app.core.authz import AuthzGuard
    if not AuthzGuard.check_permission(current_user, "machines:manage", user_perms):
        raise HTTPException(status_code=403, detail="Not enough privileges")
    
    old_state = req.status
    from app.modules.fleet.models import validate_requisition_transition
    target = validate_requisition_transition(req.status, "equipment_check")
    req.status = target
    if data and data.machine_id:
        req.machine_id = data.machine_id
    await db.commit()
    await db.refresh(req)
    await FleetService._log(db, req.id, current_user.id, "equipment_check", state_from=old_state, state_to=req.status, details="Equipment checked")
    return req


@fleet_router.post("/requisitions/{req_id}/schedule", response_model=RequisitionResponse)
async def schedule_requisition(
    req_id: uuid.UUID,
    data: RequisitionAllocate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    req = await FleetService.get_requisition(db, req_id, current_user)
    from app.modules.iam.api import _get_user_permissions
    user_perms = _get_user_permissions(current_user)
    from app.core.authz import AuthzGuard
    if not AuthzGuard.check_permission(current_user, "machines:manage", user_perms):
        raise HTTPException(status_code=403, detail="Not enough privileges to schedule equipment")
    
    old_state = req.status
    from app.modules.fleet.models import validate_requisition_transition
    target = validate_requisition_transition(req.status, "schedule")
    
    await FleetService._check_double_booking(db, data.machine_id, req.start_time, req.end_time, req.id)
    
    req.status = target
    req.machine_id = data.machine_id
    if data.operator_name:
        req.operator_name = data.operator_name
    req.scheduler_id = current_user.id
    req.scheduled_at = datetime.utcnow()
    
    from app.modules.fleet.models import MachineReservation
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
    await FleetService._log(db, req.id, current_user.id, "schedule", state_from=old_state, state_to=req.status, details=data.comments or "Equipment scheduled")
    return req


@fleet_router.post("/requisitions/{req_id}/dispatch", response_model=RequisitionResponse)
async def dispatch_requisition(
    req_id: uuid.UUID,
    data: Optional[RequisitionDispatch] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    req = await FleetService.get_requisition(db, req_id, current_user)
    from app.modules.iam.api import _get_user_permissions
    user_perms = _get_user_permissions(current_user)
    from app.core.authz import AuthzGuard
    if not AuthzGuard.check_permission(current_user, "machines:manage", user_perms):
        raise HTTPException(status_code=403, detail="Not enough privileges to dispatch equipment")
    
    old_state = req.status
    from app.modules.fleet.models import validate_requisition_transition
    target = validate_requisition_transition(req.status, "dispatch")
    
    req.status = target
    if data:
        if data.start_hour_meter is not None:
            req.start_hour_meter = data.start_hour_meter
            req.start_hours = data.start_hour_meter
        elif data.start_hours is not None:
            req.start_hour_meter = data.start_hours
            req.start_hours = data.start_hours
        if data.operator_name:
            req.operator_name = data.operator_name
    req.actual_start_time = datetime.utcnow()
    
    await db.commit()
    await db.refresh(req)
    await FleetService._log(db, req.id, current_user.id, "dispatch", state_from=old_state, state_to=req.status, details="Equipment dispatched")
    return req


@fleet_router.post("/requisitions/{req_id}/request-return", response_model=RequisitionResponse)
async def request_return_requisition(
    req_id: uuid.UUID,
    data: Optional[RequisitionReturn] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    req = await FleetService.get_requisition(db, req_id, current_user)
    old_state = req.status
    from app.modules.fleet.models import validate_requisition_transition
    target = validate_requisition_transition(req.status, "request_return")
    req.status = target
    await db.commit()
    await db.refresh(req)
    await FleetService._log(db, req.id, current_user.id, "request_return", state_from=old_state, state_to=req.status, details="Return requested")
    return req


@fleet_router.post("/requisitions/{req_id}/inspect", response_model=RequisitionResponse)
async def inspect_requisition(
    req_id: uuid.UUID,
    data: Optional[dict] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    req = await FleetService.get_requisition(db, req_id, current_user)
    from app.modules.iam.api import _get_user_permissions
    user_perms = _get_user_permissions(current_user)
    from app.core.authz import AuthzGuard
    if not AuthzGuard.check_permission(current_user, "machines:manage", user_perms):
        raise HTTPException(status_code=403, detail="Not enough privileges")
    
    old_state = req.status
    from app.modules.fleet.models import validate_requisition_transition
    target = validate_requisition_transition(req.status, "inspect")
    req.status = target
    await db.commit()
    await db.refresh(req)
    await FleetService._log(db, req.id, current_user.id, "inspect", state_from=old_state, state_to=req.status, details="Inspection passed")
    return req
