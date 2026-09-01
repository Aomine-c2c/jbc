import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.iam.models import User
from app.modules.sla.schemas import (
    SLAPolicyCreate,
    SLAPolicyUpdate,
    SLAPolicyResponse,
    SLATrackerCreate,
    SLATrackerResponse,
    SLATrackerListResponse,
    SLADashboardResponse,
    SLAPauseRequest,
    SLAResumeRequest,
    SLAAcknowledgeRequest,
)
from app.modules.sla.service import SLAService

router = APIRouter(prefix="/sla", tags=["Priority, SLA & Escalations"])


def _get_current_user():
    from app.main import get_current_user
    return get_current_user


# ── Dashboard & Analytics ────────────────────────────────────

@router.get("/dashboard", response_model=SLADashboardResponse)
async def get_sla_dashboard(
    department_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await SLAService.get_dashboard(db, department_id)


# ── Policy Endpoints ─────────────────────────────────────────

@router.post("/policies", response_model=SLAPolicyResponse)
async def create_sla_policy(
    data: SLAPolicyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    policy = await SLAService.create_policy(db, data, current_user)
    return SLAPolicyResponse.model_validate(policy)


@router.get("/policies", response_model=List[SLAPolicyResponse])
async def list_sla_policies(
    priority: Optional[str] = Query(None),
    department_id: Optional[uuid.UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await SLAService.list_policies(
        db=db, priority=priority, department_id=department_id, is_active=is_active
    )


# ── Tracker Endpoints ────────────────────────────────────────

@router.post("/trackers", response_model=SLATrackerResponse)
async def create_sla_tracker(
    data: SLATrackerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    tracker = await SLAService.create_tracker(db, data, current_user)
    return await SLAService.get_tracker_detail(db, tracker.id, current_user)


@router.get("/trackers", response_model=List[SLATrackerListResponse])
async def list_sla_trackers(
    department_id: Optional[uuid.UUID] = Query(None),
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    health: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await SLAService.list_trackers(
        db=db,
        department_id=department_id,
        priority=priority,
        status=status,
        health=health,
        resource_type=resource_type,
        search_query=search,
        limit=limit,
        offset=offset,
    )


@router.get("/trackers/{id}", response_model=SLATrackerResponse)
async def get_sla_tracker(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await SLAService.get_tracker_detail(db, id, current_user)


@router.post("/trackers/{id}/acknowledge", response_model=SLATrackerResponse)
async def acknowledge_sla_tracker(
    id: uuid.UUID,
    data: SLAAcknowledgeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    await SLAService.record_response(db, id, current_user, data.notes)
    return await SLAService.get_tracker_detail(db, id, current_user)


@router.post("/trackers/{id}/pause", response_model=SLATrackerResponse)
async def pause_sla_tracker(
    id: uuid.UUID,
    data: SLAPauseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    await SLAService.pause_tracker(db, id, data.reason, current_user)
    return await SLAService.get_tracker_detail(db, id, current_user)


@router.post("/trackers/{id}/resume", response_model=SLATrackerResponse)
async def resume_sla_tracker(
    id: uuid.UUID,
    data: SLAResumeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    await SLAService.resume_tracker(db, id, data.notes, current_user)
    return await SLAService.get_tracker_detail(db, id, current_user)


@router.post("/trackers/{id}/complete", response_model=SLATrackerResponse)
async def complete_sla_tracker(
    id: uuid.UUID,
    notes: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    await SLAService.complete_tracker(db, id, current_user, notes)
    return await SLAService.get_tracker_detail(db, id, current_user)


@router.post("/evaluate")
async def evaluate_sla_escalations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    count = await SLAService.evaluate_trackers_and_escalate(db)
    return {"status": "success", "escalations_fired": count}
