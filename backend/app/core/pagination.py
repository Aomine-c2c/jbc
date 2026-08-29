from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel
from fastapi import Query
from sqlalchemy import Select

T = TypeVar("T")

class PaginationParams(BaseModel):
    page: int = Query(1, ge=1, description="Page number")
    size: int = Query(20, ge=1, le=100, description="Page size")

class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    total: int
    page: int
    size: int
    pages: int

def apply_pagination(query: Select, params: PaginationParams) -> Select:
    return query.offset((params.page - 1) * params.size).limit(params.size)
