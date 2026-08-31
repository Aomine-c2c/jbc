import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.iam.models import User
from app.modules.requests.schemas import (
    RequestCreate,
    RequestUpdate,
    RequestTransition,
    RequestFulfill,
    MaterialIssueRequest,
    MaterialReturnRequest,
    RequestCommentCreate,
    RequestResponse,
    RequestListResponse,
    RequestMaterialItemResponse,
    RequestCommentResponse,
)
from app.modules.requests.service import RequestService

router = APIRouter(prefix="/requests", tags=["Universal Request & Requisition Engine"])


def _get_current_user():
    from app.main import get_current_user
    return get_current_user


@router.post("", response_model=RequestResponse)
async def create_request(
    data: RequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    req = await RequestService.create_request(db, data, current_user)
    return await RequestService.get_request(db, req.id, current_user)


@router.get("", response_model=List[RequestListResponse])
async def list_requests(
    request_type: Optional[str] = Query(None, description="MACHINE_REQUEST, EQUIPMENT_REQUEST, VEHICLE_REQUEST, MATERIAL_REQUEST, PERSONNEL_REQUEST, CONTRACTOR_REQUEST, OTHER"),
    department_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    fulfillment_status: Optional[str] = Query(None),
    priority: Optional[int] = Query(None),
    work_item_id: Optional[uuid.UUID] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await RequestService.list_requests(
        db=db,
        current_user=current_user,
        request_type=request_type,
        department_id=department_id,
        status=status,
        fulfillment_status=fulfillment_status,
        priority=priority,
        work_item_id=work_item_id,
        search_query=search,
        limit=limit,
        offset=offset,
    )


@router.get("/{id}", response_model=RequestResponse)
async def get_request(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await RequestService.get_request(db, id, current_user)


@router.post("/{id}/transition", response_model=RequestResponse)
async def transition_request_lifecycle(
    id: uuid.UUID,
    data: RequestTransition,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    await RequestService.transition_lifecycle(db, id, data, current_user)
    return await RequestService.get_request(db, id, current_user)


@router.post("/{id}/fulfill", response_model=RequestResponse)
async def fulfill_request(
    id: uuid.UUID,
    data: RequestFulfill,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    await RequestService.fulfill_request(db, id, data, current_user)
    return await RequestService.get_request(db, id, current_user)


@router.post("/{id}/materials/issue", response_model=RequestMaterialItemResponse)
async def issue_material_item(
    id: uuid.UUID,
    data: MaterialIssueRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await RequestService.issue_material_items(db, id, data, current_user)


@router.post("/{id}/materials/return", response_model=RequestMaterialItemResponse)
async def return_material_item(
    id: uuid.UUID,
    data: MaterialReturnRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await RequestService.return_material_items(db, id, data, current_user)


@router.post("/{id}/comments", response_model=RequestCommentResponse)
async def add_request_comment(
    id: uuid.UUID,
    data: RequestCommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    c = await RequestService.add_comment(db, id, data, current_user)
    return RequestCommentResponse(
        id=c.id,
        request_id=c.request_id,
        user_id=c.user_id,
        comment=c.comment,
        created_at=c.created_at,
        user_name=f"{current_user.first_name} {current_user.last_name}",
    )
