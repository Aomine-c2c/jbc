from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.main import get_current_user
from app.modules.iam.models import User
from app.modules.search.schemas import GlobalSearchResponse
from app.modules.search.service import GlobalSearchService

search_router = APIRouter(prefix="/api/v1", tags=["search"])


@search_router.get("/search", response_model=GlobalSearchResponse)
async def global_search(
    q: str = Query(..., min_length=1, description="Search across authorized records"),
    limit: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await GlobalSearchService.search(db, current_user, q, limit=limit)
