from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class AssetBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    name: str = Field(..., min_length=1, max_length=255)
    asset_tag: Optional[str] = Field(None, max_length=50, description="Unique tag e.g. AST-2026-0001, CR-001")
    asset_type: str = Field("EQUIPMENT", description="MACHINE, EQUIPMENT, VEHICLE, TOOL, INFRASTRUCTURE, IT_EQUIPMENT, PRODUCTION_EQUIPMENT, OTHER")
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    serial_number: Optional[str] = None
    department_id: UUID
    location_id: Optional[UUID] = None
    location: Optional[str] = None
    custodian_id: Optional[UUID] = None
    status: str = Field("AVAILABLE", description="AVAILABLE, IN_USE, RESERVED, UNDER_MAINTENANCE, OUT_OF_SERVICE, INACTIVE, RETIRED")
    criticality: str = Field("MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")
    commissioned_date: Optional[datetime] = None
    retired_date: Optional[datetime] = None
    purchase_cost: Optional[float] = 0.0
    current_value: Optional[float] = 0.0
    barcode_or_nfc: Optional[str] = None
    notes: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    machine_id: Optional[UUID] = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    name: Optional[str] = None
    asset_type: Optional[str] = None
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    serial_number: Optional[str] = None
    department_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    location: Optional[str] = None
    custodian_id: Optional[UUID] = None
    status: Optional[str] = None
    criticality: Optional[str] = None
    commissioned_date: Optional[datetime] = None
    retired_date: Optional[datetime] = None
    purchase_cost: Optional[float] = None
    current_value: Optional[float] = None
    barcode_or_nfc: Optional[str] = None
    notes: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    machine_id: Optional[UUID] = None


class AssetStatusTransition(BaseModel):
    status: str = Field(..., description="Target status: AVAILABLE, IN_USE, RESERVED, UNDER_MAINTENANCE, OUT_OF_SERVICE, INACTIVE, RETIRED")
    notes: Optional[str] = None


class AssetArchiveRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


class AssetMaintenanceCreate(BaseModel):
    maintenance_type: str = Field("PREVENTIVE", description="PREVENTIVE, CORRECTIVE, CALIBRATION, OVERHAUL, INSPECTION")
    summary: str = Field(..., min_length=1, max_length=2000)
    service_date: Optional[datetime] = None
    performed_by: Optional[str] = None
    meter_reading: Optional[float] = 0.0
    cost: Optional[float] = 0.0
    work_item_id: Optional[UUID] = None
    job_card_id: Optional[UUID] = None


class AssetMaintenanceResponse(BaseModel):
    id: UUID
    asset_id: UUID
    maintenance_type: str
    summary: str
    service_date: datetime
    performed_by: Optional[str] = None
    meter_reading: Optional[float] = 0.0
    cost: float = 0.0
    work_item_id: Optional[UUID] = None
    job_card_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class AssetActivityLogResponse(BaseModel):
    id: UUID
    asset_id: UUID
    user_id: UUID
    activity_type: str
    previous_value: Optional[str] = None
    new_value: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    user_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class AssetAttachmentResponse(BaseModel):
    id: UUID
    asset_id: UUID
    filename: str
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    file_size_kb: float = 0.0
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class AssetResponse(AssetBase):
    id: UUID
    asset_tag: str
    is_archived: bool = False
    archived_at: Optional[datetime] = None
    archived_reason: Optional[str] = None
    
    department_name: Optional[str] = None
    location_breadcrumb: Optional[str] = None
    custodian_name: Optional[str] = None
    machine_identifier: Optional[str] = None
    open_work_items_count: int = 0
    
    activity_logs: List[AssetActivityLogResponse] = []
    maintenance_records: List[AssetMaintenanceResponse] = []
    attachments: List[AssetAttachmentResponse] = []
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class AssetListResponse(BaseModel):
    id: UUID
    asset_tag: str
    name: str
    asset_type: str
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    serial_number: Optional[str] = None
    department_id: UUID
    department_name: Optional[str] = None
    location_breadcrumb: Optional[str] = None
    custodian_name: Optional[str] = None
    status: str
    criticality: str
    is_archived: bool = False
    machine_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class AssetMigrationSummary(BaseModel):
    scanned_machines: int = 0
    created_assets: int = 0
    linked_machines: int = 0
    skipped: int = 0
    details: List[str] = []
