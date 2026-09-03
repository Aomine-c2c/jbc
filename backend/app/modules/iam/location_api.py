import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.iam.models import User
from app.modules.iam.location_schemas import (
    LocationCreate,
    LocationUpdate,
    LocationArchive,
    LocationResponse,
    LocationTreeNode,
    LocationSearchResult,
    LocationMigrationSummary,
)
from app.modules.iam.location_service import LocationService
from app.core.authz import AuthzGuard


def _get_current_user():
    """Lazy import to avoid circular dependency."""
    from app.main import get_current_user as gcu
    return gcu


location_router = APIRouter(prefix="/api/v1/locations", tags=["locations"])


@location_router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    data: LocationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    user_perms = _get_user_permissions(current_user)
    if not AuthzGuard.check_permission(current_user, "settings:manage", user_perms):
        raise HTTPException(status_code=403, detail="Not enough privileges to create locations")
    return await LocationService.create_location(db, data, current_user)


@location_router.get("", response_model=List[LocationResponse])
async def list_locations(
    site_id: Optional[uuid.UUID] = Query(None, description="Filter by Site ID"),
    parent_id: Optional[uuid.UUID] = Query(None, description="Filter by Parent Location ID"),
    location_type: Optional[str] = Query(None, description="Filter by hierarchy level type"),
    is_active: Optional[bool] = Query(None, description="Filter active/inactive"),
    include_archived: bool = Query(False, description="Include archived locations"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await LocationService.list_locations(
        db=db,
        site_id=site_id,
        parent_id=parent_id,
        location_type=location_type,
        is_active=is_active,
        include_archived=include_archived,
    )


@location_router.get("/tree", response_model=List[LocationTreeNode])
async def get_location_hierarchy_tree(
    site_id: Optional[uuid.UUID] = Query(None, description="Filter tree by Site ID"),
    include_archived: bool = Query(False, description="Include archived locations in tree"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await LocationService.get_hierarchy_tree(db, site_id=site_id, include_archived=include_archived)


@location_router.get("/search", response_model=List[LocationSearchResult])
async def search_locations(
    q: str = Query(..., min_length=1, description="Search query across code, name, barcode, breadcrumb"),
    location_type: Optional[str] = Query(None, description="Filter by location type"),
    site_id: Optional[uuid.UUID] = Query(None, description="Filter by site"),
    limit: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await LocationService.search_locations(
        db=db, query_str=q, location_type=location_type, site_id=site_id, limit=limit
    )


@location_router.get("/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await LocationService.get_location(db, location_id)


@location_router.patch("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: uuid.UUID,
    data: LocationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    user_perms = _get_user_permissions(current_user)
    if not AuthzGuard.check_permission(current_user, "settings:manage", user_perms):
        raise HTTPException(status_code=403, detail="Not enough privileges to update locations")
    return await LocationService.update_location(db, location_id, data, current_user)


@location_router.post("/{location_id}/archive", response_model=LocationResponse)
async def archive_location(
    location_id: uuid.UUID,
    data: Optional[LocationArchive] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    user_perms = _get_user_permissions(current_user)
    if not AuthzGuard.check_permission(current_user, "settings:manage", user_perms):
        raise HTTPException(status_code=403, detail="Not enough privileges to archive locations")
    return await LocationService.archive_location(db, location_id, data.reason if data else None, current_user)


@location_router.post("/{location_id}/restore", response_model=LocationResponse)
async def restore_location(
    location_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    user_perms = _get_user_permissions(current_user)
    if not AuthzGuard.check_permission(current_user, "settings:manage", user_perms):
        raise HTTPException(status_code=403, detail="Not enough privileges to restore locations")
    return await LocationService.restore_location(db, location_id, current_user)


@location_router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    user_perms = _get_user_permissions(current_user)
    if not AuthzGuard.check_permission(current_user, "settings:manage", user_perms):
        raise HTTPException(status_code=403, detail="Not enough privileges to delete locations")
    await LocationService.delete_location(db, location_id, current_user)


@location_router.post("/migrate", response_model=LocationMigrationSummary)
async def migrate_text_locations(
    site_id: Optional[uuid.UUID] = Query(None, description="Target Site ID for unlinked records"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    user_perms = _get_user_permissions(current_user)
    if not AuthzGuard.check_permission(current_user, "settings:manage", user_perms):
        raise HTTPException(status_code=403, detail="Not enough privileges to trigger migration")
    return await LocationService.migrate_text_locations(db, default_site_id=site_id)
