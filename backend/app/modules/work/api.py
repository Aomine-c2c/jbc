import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.modules.iam.models import User
from app.modules.work.models import WorkItemComment, WorkItemPart
from app.modules.work.schemas import (
    WorkItemCreate,
    WorkItemUpdate,
    WorkItemTransition,
    WorkItemFollowUpCreate,
    WorkItemPartCreate,
    WorkItemCommentCreate,
    WorkItemResponse,
    WorkItemListResponse,
    WorkItemMigrationSummary,
)
from app.modules.work.service import WorkItemService

router = APIRouter(prefix="/work-items", tags=["Unified Work Management"])


def _get_current_user():
    from app.main import get_current_user
    return get_current_user


@router.post("", response_model=WorkItemResponse)
async def create_work_item(
    data: WorkItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    item = await WorkItemService.create_work_item(db, data, current_user)
    return await WorkItemService.get_work_item(db, item.id, current_user)


@router.get("", response_model=List[WorkItemListResponse])
async def list_work_items(
    work_type: Optional[str] = Query(None, description="Filter by type: JOB_CARD, MAINTENANCE, INSPECTION, FOLLOW_UP, OTHER"),
    department_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[int] = Query(None),
    machine_id: Optional[uuid.UUID] = Query(None),
    location_id: Optional[uuid.UUID] = Query(None),
    requester_id: Optional[uuid.UUID] = Query(None),
    supervisor_id: Optional[uuid.UUID] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await WorkItemService.list_work_items(
        db=db,
        current_user=current_user,
        work_type=work_type,
        department_id=department_id,
        status=status,
        priority=priority,
        machine_id=machine_id,
        location_id=location_id,
        requester_id=requester_id,
        supervisor_id=supervisor_id,
        search_query=search,
        limit=limit,
        offset=offset,
    )


@router.get("/{id}", response_model=WorkItemResponse)
async def get_work_item(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await WorkItemService.get_work_item(db, id, current_user)


@router.patch("/{id}", response_model=WorkItemResponse)
async def update_work_item(
    id: uuid.UUID,
    data: WorkItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    await WorkItemService.update_work_item(db, id, data, current_user)
    return await WorkItemService.get_work_item(db, id, current_user)


@router.post("/{id}/transition", response_model=WorkItemResponse)
async def transition_work_item_status(
    id: uuid.UUID,
    data: WorkItemTransition,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    await WorkItemService.transition_status(db, id, data, current_user)
    return await WorkItemService.get_work_item(db, id, current_user)


@router.post("/{id}/follow-up", response_model=WorkItemResponse)
async def create_follow_up_action(
    id: uuid.UUID,
    data: WorkItemFollowUpCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    item = await WorkItemService.create_follow_up(db, id, data, current_user)
    return await WorkItemService.get_work_item(db, item.id, current_user)


@router.post("/{id}/comments", response_model=WorkItemResponse)
async def add_work_item_comment(
    id: uuid.UUID,
    data: WorkItemCommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    await WorkItemService.get_work_item(db, id, current_user)
    comment = WorkItemComment(
        id=uuid.uuid4(),
        work_item_id=id,
        user_id=current_user.id,
        comment=data.comment.strip(),
    )
    db.add(comment)
    await db.commit()
    return await WorkItemService.get_work_item(db, id, current_user)


@router.post("/{id}/parts", response_model=WorkItemResponse)
async def add_work_item_part(
    id: uuid.UUID,
    data: WorkItemPartCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    await WorkItemService.get_work_item(db, id, current_user)
    part = WorkItemPart(
        id=uuid.uuid4(),
        work_item_id=id,
        part_name=data.part_name.strip(),
        part_number=data.part_number,
        quantity=data.quantity,
        unit_cost=data.unit_cost,
        is_material=data.is_material,
    )
    db.add(part)
    await db.commit()
    return await WorkItemService.get_work_item(db, id, current_user)


@router.post("/migrate-job-cards", response_model=WorkItemMigrationSummary)
async def migrate_historical_job_cards(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser required to run historical migrations")
    return await WorkItemService.migrate_historical_job_cards(db)
