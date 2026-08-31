import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.iam.models import User
from app.modules.contractors.schemas import (
    ContractorCompanyCreate,
    ContractorCompanyUpdate,
    ContractorCompanyResponse,
    ContractorCompanyListResponse,
    ContractorWorkerCreate,
    ContractorWorkerUpdate,
    ContractorWorkerResponse,
    ContractorWorkerListResponse,
    ContractorAssignmentCreate,
    ContractorAssignmentVerify,
    ContractorAssignmentResponse,
    ContractorAssignmentListResponse,
)
from app.modules.contractors.service import ContractorService

router = APIRouter(prefix="/contractors", tags=["Contractor & External Workforce"])


def _get_current_user():
    from app.main import get_current_user
    return get_current_user


# ── Company Endpoints ────────────────────────────────────────

@router.post("/companies", response_model=ContractorCompanyResponse)
async def create_contractor_company(
    data: ContractorCompanyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    company = await ContractorService.create_company(db, data, current_user)
    return await ContractorService.get_company(db, company.id, current_user)


@router.get("/companies", response_model=List[ContractorCompanyListResponse])
async def list_contractor_companies(
    status: Optional[str] = Query(None),
    include_archived: bool = Query(False),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await ContractorService.list_companies(
        db=db,
        current_user=current_user,
        status=status,
        include_archived=include_archived,
        search_query=search,
        limit=limit,
        offset=offset,
    )


@router.get("/companies/{id}", response_model=ContractorCompanyResponse)
async def get_contractor_company(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await ContractorService.get_company(db, id, current_user)


@router.patch("/companies/{id}", response_model=ContractorCompanyResponse)
async def update_contractor_company(
    id: uuid.UUID,
    data: ContractorCompanyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    await ContractorService.update_company(db, id, data, current_user)
    return await ContractorService.get_company(db, id, current_user)


@router.post("/companies/{id}/archive", response_model=ContractorCompanyResponse)
async def archive_contractor_company(
    id: uuid.UUID,
    reason: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    await ContractorService.archive_company(db, id, reason, current_user)
    return await ContractorService.get_company(db, id, current_user)


# ── Worker Endpoints ─────────────────────────────────────────

@router.post("/workers", response_model=ContractorWorkerResponse)
async def create_contractor_worker(
    data: ContractorWorkerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    worker = await ContractorService.create_worker(db, data, current_user)
    return ContractorWorkerResponse.model_validate(worker)


@router.get("/workers", response_model=List[ContractorWorkerListResponse])
async def list_contractor_workers(
    company_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    skill: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await ContractorService.list_workers(
        db=db,
        current_user=current_user,
        company_id=company_id,
        status=status,
        skill=skill,
        search_query=search,
        limit=limit,
        offset=offset,
    )


# ── Assignment & Sign-off Endpoints ──────────────────────────

@router.post("/assignments", response_model=ContractorAssignmentResponse)
async def create_contractor_assignment(
    data: ContractorAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    assignment = await ContractorService.create_assignment(db, data, current_user)
    return await ContractorService.get_assignment(db, assignment.id, current_user)


@router.get("/assignments", response_model=List[ContractorAssignmentListResponse])
async def list_contractor_assignments(
    company_id: Optional[uuid.UUID] = Query(None),
    work_item_id: Optional[uuid.UUID] = Query(None),
    verification_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await ContractorService.list_assignments(
        db=db,
        current_user=current_user,
        company_id=company_id,
        work_item_id=work_item_id,
        verification_status=verification_status,
        search_query=search,
        limit=limit,
        offset=offset,
    )


@router.get("/assignments/{id}", response_model=ContractorAssignmentResponse)
async def get_contractor_assignment(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await ContractorService.get_assignment(db, id, current_user)


@router.post("/assignments/{id}/verify", response_model=ContractorAssignmentResponse)
async def verify_contractor_assignment(
    id: uuid.UUID,
    data: ContractorAssignmentVerify,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    await ContractorService.verify_assignment(db, id, data, current_user)
    return await ContractorService.get_assignment(db, id, current_user)
