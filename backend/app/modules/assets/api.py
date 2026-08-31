import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.iam.models import User
from app.modules.assets.schemas import (
    AssetCreate,
    AssetUpdate,
    AssetStatusTransition,
    AssetArchiveRequest,
    AssetMaintenanceCreate,
    AssetResponse,
    AssetListResponse,
    AssetMaintenanceResponse,
    AssetMigrationSummary,
)
from app.modules.assets.service import AssetService

router = APIRouter(prefix="/assets", tags=["Asset & Equipment Management"])


def _get_current_user():
    from app.main import get_current_user
    return get_current_user


@router.post("", response_model=AssetResponse)
async def create_asset(
    data: AssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    asset = await AssetService.create_asset(db, data, current_user)
    return await AssetService.get_asset(db, asset.id, current_user)


@router.get("", response_model=List[AssetListResponse])
async def list_assets(
    asset_type: Optional[str] = Query(None, description="Filter by type: MACHINE, EQUIPMENT, VEHICLE, TOOL, INFRASTRUCTURE, IT_EQUIPMENT, PRODUCTION_EQUIPMENT, OTHER"),
    category: Optional[str] = Query(None),
    department_id: Optional[uuid.UUID] = Query(None),
    location_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    criticality: Optional[str] = Query(None),
    include_archived: bool = Query(False),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await AssetService.list_assets(
        db=db,
        current_user=current_user,
        asset_type=asset_type,
        category=category,
        department_id=department_id,
        location_id=location_id,
        status=status,
        criticality=criticality,
        include_archived=include_archived,
        search_query=search,
        limit=limit,
        offset=offset,
    )


@router.get("/{id}", response_model=AssetResponse)
async def get_asset(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await AssetService.get_asset(db, id, current_user)


@router.patch("/{id}", response_model=AssetResponse)
async def update_asset(
    id: uuid.UUID,
    data: AssetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    await AssetService.update_asset(db, id, data, current_user)
    return await AssetService.get_asset(db, id, current_user)


@router.post("/{id}/status", response_model=AssetResponse)
async def transition_asset_status(
    id: uuid.UUID,
    data: AssetStatusTransition,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    await AssetService.transition_status(db, id, data, current_user)
    return await AssetService.get_asset(db, id, current_user)


@router.post("/{id}/maintenance", response_model=AssetMaintenanceResponse)
async def record_asset_maintenance(
    id: uuid.UUID,
    data: AssetMaintenanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await AssetService.record_maintenance(db, id, data, current_user)


@router.post("/{id}/archive", response_model=AssetResponse)
async def archive_asset(
    id: uuid.UUID,
    data: AssetArchiveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    await AssetService.archive_asset(db, id, data.reason, current_user)
    return await AssetService.get_asset(db, id, current_user)


@router.post("/{id}/restore", response_model=AssetResponse)
async def restore_asset(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    await AssetService.restore_asset(db, id, current_user)
    return await AssetService.get_asset(db, id, current_user)


@router.post("/migrate-machines", response_model=AssetMigrationSummary)
async def migrate_machines_to_assets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser required to run migrations")
    return await AssetService.migrate_machines_to_assets(db)
