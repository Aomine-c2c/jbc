from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class LocationBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=100, description="Unique code or identifier (e.g. CRUSH-01, CONV-C01)")
    name: str = Field(..., min_length=1, max_length=255, description="Display name of the location")
    location_type: str = Field("AREA", description="Hierarchy level: SITE, FACILITY, PLANT, AREA, SECTION, SPECIFIC_LOCATION, WORK_CENTER, ROOM, OTHER")
    description: Optional[str] = None
    gps_coordinates: Optional[str] = None
    barcode_or_nfc: Optional[str] = None
    criticality_rating: Optional[str] = "MEDIUM"


class LocationCreate(LocationBase):
    organization_id: Optional[UUID] = None
    site_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None


class LocationUpdate(BaseModel):
    parent_id: Optional[UUID] = None
    code: Optional[str] = None
    name: Optional[str] = None
    location_type: Optional[str] = None
    description: Optional[str] = None
    gps_coordinates: Optional[str] = None
    barcode_or_nfc: Optional[str] = None
    criticality_rating: Optional[str] = None
    is_active: Optional[bool] = None


class LocationArchive(BaseModel):
    reason: Optional[str] = Field(None, description="Operational reason for archiving this location")


class LocationResponse(LocationBase):
    id: UUID
    organization_id: Optional[UUID] = None
    site_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None
    breadcrumb: Optional[str] = None
    hierarchy_level: int = 1
    is_active: bool = True
    is_archived: bool = False
    archived_at: Optional[datetime] = None
    archived_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    reference_count: Optional[int] = 0
    children_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class LocationTreeNode(BaseModel):
    id: UUID
    code: str
    name: str
    location_type: str
    breadcrumb: Optional[str] = None
    hierarchy_level: int
    is_active: bool
    is_archived: bool
    gps_coordinates: Optional[str] = None
    barcode_or_nfc: Optional[str] = None
    criticality_rating: Optional[str] = None
    children: List["LocationTreeNode"] = []
    reference_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class LocationSearchResult(BaseModel):
    id: UUID
    code: str
    name: str
    location_type: str
    breadcrumb: Optional[str] = None
    hierarchy_level: int
    site_name: Optional[str] = None
    is_active: bool
    barcode_or_nfc: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LocationMigrationSummary(BaseModel):
    scanned_job_cards: int = 0
    scanned_machines: int = 0
    scanned_requisitions: int = 0
    created_locations: int = 0
    matched_locations: int = 0
    details: List[str] = []
