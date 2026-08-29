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
    RequisitionResponse,
    RequisitionListResponse,
    MachineAvailabilityItem,
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


@fleet_router.post("/requisitions/{req_id}/dept-approve", response_model=RequisitionResponse)
async def dept_approve_requisition(
    req_id: uuid.UUID,
    data: Optional[RequisitionDeptApprove] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.dept_approve_requisition(
        db, req_id, data or RequisitionDeptApprove(), current_user
    )


@fleet_router.post("/requisitions/{req_id}/equipment-check", response_model=RequisitionResponse)
async def equipment_check_requisition(
    req_id: uuid.UUID,
    data: Optional[RequisitionEquipmentCheck] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.equipment_check_requisition(
        db, req_id, data or RequisitionEquipmentCheck(), current_user
    )


@fleet_router.post("/requisitions/{req_id}/approve", response_model=RequisitionResponse)
async def approve_requisition(
    req_id: uuid.UUID,
    data: RequisitionApprove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.approve_requisition(db, req_id, data, current_user)


@fleet_router.post("/requisitions/{req_id}/schedule", response_model=RequisitionResponse)
async def schedule_requisition(
    req_id: uuid.UUID,
    data: RequisitionSchedule,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.schedule_requisition(db, req_id, data, current_user)


@fleet_router.post("/requisitions/{req_id}/reserve", response_model=RequisitionResponse)
async def reserve_requisition(
    req_id: uuid.UUID,
    data: RequisitionReserve,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    sched_data = RequisitionSchedule(machine_id=data.machine_id)
    return await FleetService.schedule_requisition(db, req_id, sched_data, current_user)


@fleet_router.post("/requisitions/{req_id}/dispatch", response_model=RequisitionResponse)
async def dispatch_requisition(
    req_id: uuid.UUID,
    data: RequisitionDispatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.dispatch_requisition(db, req_id, data, current_user)


@fleet_router.post("/requisitions/{req_id}/start-use", response_model=RequisitionResponse)
async def start_use_requisition(
    req_id: uuid.UUID,
    data: Optional[RequisitionStartUse] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.start_use_requisition(db, req_id, data, current_user)


@fleet_router.post("/requisitions/{req_id}/confirm", response_model=RequisitionResponse)
async def confirm_requisition(
    req_id: uuid.UUID,
    data: Optional[RequisitionConfirm] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.start_use_requisition(db, req_id, None, current_user)


@fleet_router.post("/requisitions/{req_id}/finish", response_model=RequisitionResponse)
async def finish_requisition(
    req_id: uuid.UUID,
    data: Optional[RequisitionFinish] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.request_return_requisition(db, req_id, None, current_user)


@fleet_router.post("/requisitions/{req_id}/request-return", response_model=RequisitionResponse)
async def request_return_requisition(
    req_id: uuid.UUID,
    data: Optional[RequisitionRequestReturn] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.request_return_requisition(db, req_id, data, current_user)


@fleet_router.post("/requisitions/{req_id}/return", response_model=RequisitionResponse)
async def return_requisition(
    req_id: uuid.UUID,
    data: RequisitionReturn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.return_requisition(db, req_id, data, current_user)


@fleet_router.post("/requisitions/{req_id}/inspect", response_model=RequisitionResponse)
async def inspect_requisition(
    req_id: uuid.UUID,
    data: RequisitionInspect,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await FleetService.inspect_requisition(db, req_id, data, current_user)


@fleet_router.post("/requisitions/{req_id}/complete", response_model=RequisitionResponse)
async def complete_requisition(
    req_id: uuid.UUID,
    data: Optional[RequisitionInspect] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    inspect_data = data or RequisitionInspect(inspection_notes="Completed and inspected.")
    return await FleetService.inspect_requisition(db, req_id, inspect_data, current_user)


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
