import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field


class SearchScopeItem(BaseModel):
    id: uuid.UUID
    reference: str
    title: str
    entity: str
    entity_label: str
    department_id: uuid.UUID | None = None
    department_name: str | None = None
    status: str | None = None
    priority: int | None = None
    url: str | None = None
    relevance: float = 0.0
    snippet: str | None = None


class SearchGroup(BaseModel):
    entity: str
    entity_label: str
    total: int = 0
    items: list[SearchScopeItem] = Field(default_factory=list)


class GlobalSearchResponse(BaseModel):
    query: str
    total: int = 0
    groups: list[SearchGroup] = Field(default_factory=list)
