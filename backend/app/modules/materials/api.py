import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.iam.models import User
from app.modules.materials.schemas import (
    MaterialCatalogCreate,
    MaterialCatalogResponse,
    MaterialRequirementCreate,
    MaterialRequirementApprove,
    MaterialIssueRequest,
    MaterialUsageRequest,
    MaterialReturnRequest,
    MaterialRequirementResponse,
    MaterialRequirementListResponse,
    MaterialTransactionResponse,
    StockAvailabilityResponse,
)
from app.modules.materials.service import MaterialService
from app.modules.materials.adapters import inventory_adapter

router = APIRouter(prefix="/materials", tags=["Materials & Operational Inventory"])


def _get_current_user():
    from app.main import get_current_user
    return get_current_user


# ── Catalog Endpoints ────────────────────────────────────────

@router.post("/catalog", response_model=MaterialCatalogResponse)
async def create_catalog_item(
    data: MaterialCatalogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    item = await MaterialService.create_catalog_item(db, data, current_user)
    return MaterialCatalogResponse.model_validate(item)


@router.get("/catalog", response_model=List[MaterialCatalogResponse])
async def list_catalog_items(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_active: bool = Query(True),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    items = await MaterialService.list_catalog(
        db=db, search_query=search, category=category, is_active=is_active, limit=limit, offset=offset
    )
    return [MaterialCatalogResponse.model_validate(i) for i in items]


# ── Requirement & Operational Usage Endpoints ────────────────

@router.post("/requirements", response_model=MaterialRequirementResponse)
async def create_material_requirement(
    data: MaterialRequirementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    req = await MaterialService.create_requirement(db, data, current_user)
    return await MaterialService.get_requirement(db, req.id, current_user)


@router.get("/requirements", response_model=List[MaterialRequirementListResponse])
async def list_material_requirements(
    department_id: Optional[uuid.UUID] = Query(None),
    work_item_id: Optional[uuid.UUID] = Query(None),
    job_card_id: Optional[uuid.UUID] = Query(None),
    asset_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await MaterialService.list_requirements(
        db=db,
        current_user=current_user,
        department_id=department_id,
        work_item_id=work_item_id,
        job_card_id=job_card_id,
        asset_id=asset_id,
        status=status,
        search_query=search,
        limit=limit,
        offset=offset,
    )


@router.get("/requirements/{id}", response_model=MaterialRequirementResponse)
async def get_material_requirement(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await MaterialService.get_requirement(db, id, current_user)


@router.post("/requirements/{id}/approve", response_model=MaterialRequirementResponse)
async def approve_material_requirement(
    id: uuid.UUID,
    data: MaterialRequirementApprove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    await MaterialService.approve_requirement(db, id, data, current_user)
    return await MaterialService.get_requirement(db, id, current_user)


@router.post("/requirements/{id}/issue", response_model=MaterialTransactionResponse)
async def issue_material(
    id: uuid.UUID,
    data: MaterialIssueRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    tx = await MaterialService.issue_material(db, id, data, current_user)
    return MaterialTransactionResponse.model_validate(tx)


@router.post("/requirements/{id}/usage", response_model=MaterialTransactionResponse)
async def record_material_usage(
    id: uuid.UUID,
    data: MaterialUsageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    tx = await MaterialService.record_usage(db, id, data, current_user)
    return MaterialTransactionResponse.model_validate(tx)


@router.post("/requirements/{id}/return", response_model=MaterialTransactionResponse)
async def return_material(
    id: uuid.UUID,
    data: MaterialReturnRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    tx = await MaterialService.return_material(db, id, data, current_user)
    return MaterialTransactionResponse.model_validate(tx)


@router.get("/stock-check", response_model=StockAvailabilityResponse)
async def check_inventory_stock(
    part_number: str = Query(...),
    store_location: Optional[str] = Query(None),
    current_user: User = Depends(_get_current_user()),
):
    stock_info = await inventory_adapter.check_stock_availability(part_number, store_location)
    return StockAvailabilityResponse(
        part_number=stock_info["part_number"],
        store_location=stock_info["store_location"],
        available_quantity=stock_info["available_quantity"],
        status=stock_info["status"],
        queried_at=stock_info["queried_at"],
    )
