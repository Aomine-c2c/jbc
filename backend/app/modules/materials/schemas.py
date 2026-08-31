from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class MaterialCatalogBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    part_number: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    unit_of_measure: str = Field("units", max_length=50)
    default_unit_cost: float = Field(0.0, ge=0)
    primary_store: Optional[str] = None
    is_active: bool = True
    external_erp_id: Optional[str] = None


class MaterialCatalogCreate(MaterialCatalogBase):
    pass


class MaterialCatalogUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    unit_of_measure: Optional[str] = None
    default_unit_cost: Optional[float] = None
    primary_store: Optional[str] = None
    is_active: Optional[bool] = None
    external_erp_id: Optional[str] = None


class MaterialCatalogResponse(MaterialCatalogBase):
    id: UUID
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class MaterialRequirementCreate(BaseModel):
    catalog_item_id: Optional[UUID] = None
    material_name: str = Field(..., min_length=1, max_length=255)
    part_number: Optional[str] = None
    category: Optional[str] = None
    unit: str = Field("units", max_length=50)
    unit_cost: Optional[float] = 0.0
    quantity_required: float = Field(..., gt=0)
    store_location: Optional[str] = None
    purpose: Optional[str] = None
    work_item_id: Optional[UUID] = None
    job_card_id: Optional[UUID] = None
    asset_id: Optional[UUID] = None
    request_id: Optional[UUID] = None
    department_id: UUID
    notes: Optional[str] = None


class MaterialRequirementApprove(BaseModel):
    quantity_approved: float = Field(..., gt=0)
    notes: Optional[str] = None


class MaterialIssueRequest(BaseModel):
    quantity: float = Field(..., gt=0)
    store_location: Optional[str] = None
    received_by_id: Optional[UUID] = None
    batch_or_serial: Optional[str] = None
    notes: Optional[str] = None


class MaterialUsageRequest(BaseModel):
    quantity: float = Field(..., gt=0)
    notes: Optional[str] = None


class MaterialReturnRequest(BaseModel):
    quantity: float = Field(..., gt=0)
    store_location: Optional[str] = None
    notes: Optional[str] = None


class MaterialTransactionResponse(BaseModel):
    id: UUID
    requirement_id: Optional[UUID] = None
    catalog_item_id: Optional[UUID] = None
    transaction_type: str
    quantity: float
    unit: str
    unit_cost: float
    total_cost: float
    store_location: Optional[str] = None
    batch_or_serial: Optional[str] = None
    issued_by_id: Optional[UUID] = None
    received_by_id: Optional[UUID] = None
    issued_by_name: Optional[str] = None
    received_by_name: Optional[str] = None
    notes: Optional[str] = None
    external_reference: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class MaterialRequirementResponse(BaseModel):
    id: UUID
    requirement_number: str
    catalog_item_id: Optional[UUID] = None
    material_name: str
    part_number: Optional[str] = None
    category: Optional[str] = None
    unit: str
    unit_cost: float
    quantity_required: float
    quantity_approved: float
    quantity_issued: float
    quantity_used: float
    quantity_returned: float
    status: str
    store_location: Optional[str] = None
    purpose: Optional[str] = None
    work_item_id: Optional[UUID] = None
    job_card_id: Optional[UUID] = None
    asset_id: Optional[UUID] = None
    request_id: Optional[UUID] = None
    department_id: UUID
    requester_id: UUID
    approver_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None
    external_reservation_id: Optional[str] = None
    
    requester_name: Optional[str] = None
    approver_name: Optional[str] = None
    department_name: Optional[str] = None
    work_item_reference: Optional[str] = None
    asset_name: Optional[str] = None
    
    transactions: List[MaterialTransactionResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class MaterialRequirementListResponse(BaseModel):
    id: UUID
    requirement_number: str
    material_name: str
    part_number: Optional[str] = None
    category: Optional[str] = None
    unit: str
    unit_cost: float
    quantity_required: float
    quantity_approved: float
    quantity_issued: float
    quantity_used: float
    quantity_returned: float
    status: str
    store_location: Optional[str] = None
    department_name: Optional[str] = None
    requester_name: Optional[str] = None
    work_item_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class StockAvailabilityResponse(BaseModel):
    part_number: str
    store_location: str
    available_quantity: float
    status: str
    queried_at: str
