import pytest
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.modules.iam.models import User, Department
from app.modules.work.models import WorkItem
from app.modules.assets.models import Asset
from app.modules.materials.models import (
    MaterialCatalogItem,
    MaterialRequirement,
    MaterialTransaction,
    MaterialRequirementStatus,
)
from app.modules.materials.schemas import (
    MaterialCatalogCreate,
    MaterialRequirementCreate,
    MaterialRequirementApprove,
    MaterialIssueRequest,
    MaterialUsageRequest,
    MaterialReturnRequest,
)
from app.modules.materials.service import MaterialService
from app.modules.materials.adapters import inventory_adapter
from app.core.security import get_password_hash


@pytest.mark.asyncio
async def test_material_catalog_and_requirement_creation(db: AsyncSession):
    dept = Department(name=f"Plant Maintenance {uuid.uuid4().hex[:4]}", code=f"PM-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    user = User(
        email=f"fitter_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Plant",
        last_name="Fitter",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(user)
    await db.commit()

    # 1. Register catalog item
    cat_dto = MaterialCatalogCreate(
        part_number=f"SKF-23152-{uuid.uuid4().hex[:4].upper()}",
        name="Spherical Roller Bearing 23152 CC/W33",
        description="Heavy duty double row spherical roller bearing for ball mill drive",
        category="Bearings & Seals",
        unit_of_measure="units",
        default_unit_cost=850.0,
        primary_store="Central Warehouse Bay 4",
    )
    cat_item = await MaterialService.create_catalog_item(db, cat_dto, user)
    assert cat_item.id is not None
    assert cat_item.default_unit_cost == 850.0

    # 2. Submit requirement referencing catalog item
    req_dto = MaterialRequirementCreate(
        catalog_item_id=cat_item.id,
        material_name="Ignored - Will Auto-fill",
        quantity_required=2.0,
        department_id=dept.id,
        purpose="Ball Mill 1 drive trunnion overhaul",
    )
    req = await MaterialService.create_requirement(db, req_dto, user)
    assert req.id is not None
    assert req.material_name == "Spherical Roller Bearing 23152 CC/W33"
    assert req.part_number == cat_item.part_number
    assert req.unit_cost == 850.0
    assert req.requirement_number.startswith("MTR-")
    assert req.status == "REQUESTED"


@pytest.mark.asyncio
async def test_material_lifecycle_issue_usage_and_return(db: AsyncSession):
    dept = Department(name=f"Pumps & Valves {uuid.uuid4().hex[:4]}", code=f"PV-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    requester = User(
        email=f"pump_tech_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Pump",
        last_name="Tech",
        is_active=True,
        is_superuser=False,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    approver = User(
        email=f"pump_foreman_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Pump",
        last_name="Foreman",
        is_active=True,
        is_superuser=False,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    storekeeper = User(
        email=f"stores_clerk_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Stores",
        last_name="Clerk",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(requester)
    db.add(approver)
    db.add(storekeeper)
    await db.commit()

    # Step 1: Create Requirement for 10 meters of Gland Packing
    req_dto = MaterialRequirementCreate(
        material_name="Teflon Carbon Gland Packing 1 inch",
        part_number=f"GP-TC-100-{uuid.uuid4().hex[:4].upper()}",
        category="Gaskets & Seals",
        unit="meters",
        unit_cost=25.0,
        quantity_required=10.0,
        department_id=dept.id,
        purpose="Slurry pump gland repacking",
    )
    req = await MaterialService.create_requirement(db, req_dto, requester)

    # Step 2: SoD check - Requester cannot approve their own material request
    with pytest.raises(HTTPException) as exc:
        await MaterialService.approve_requirement(db, req.id, MaterialRequirementApprove(quantity_approved=10.0), requester)
    assert exc.value.status_code == 409

    # Independent Approval
    req = await MaterialService.approve_requirement(db, req.id, MaterialRequirementApprove(quantity_approved=10.0), approver)
    assert req.status == "APPROVED"
    assert req.quantity_approved == 10.0

    # Step 3: Partial Issue - Storekeeper issues 6 meters
    tx_issue1 = await MaterialService.issue_material(
        db, req.id, MaterialIssueRequest(quantity=6.0, received_by_id=requester.id, notes="First shift allocation"), storekeeper
    )
    assert tx_issue1.transaction_type == "ISSUE"
    assert tx_issue1.total_cost == 150.0  # 6 * 25.0
    assert tx_issue1.external_reference.startswith("ERP-GI-")

    detail = await MaterialService.get_requirement(db, req.id, requester)
    assert detail.status == "PARTIALLY_ISSUED"
    assert detail.quantity_issued == 6.0

    # Step 4: Record Usage - Technician consumes 4 meters on site
    tx_usage = await MaterialService.record_usage(db, req.id, MaterialUsageRequest(quantity=4.0, notes="Fitted to Pump P-03"), requester)
    assert tx_usage.transaction_type == "USAGE"

    detail = await MaterialService.get_requirement(db, req.id, requester)
    assert detail.status == "IN_USE"
    assert detail.quantity_used == 4.0

    # Step 5: Return - Technician returns 2 meters unused back to Store
    tx_return = await MaterialService.return_material(
        db, req.id, MaterialReturnRequest(quantity=2.0, notes="Surplus unneeded"), storekeeper
    )
    assert tx_return.transaction_type == "RETURN"
    assert tx_return.external_reference.startswith("ERP-GR-")

    detail = await MaterialService.get_requirement(db, req.id, requester)
    assert detail.quantity_returned == 2.0
    # All 6 issued meters accounted for (4 used + 2 returned)
    assert (detail.quantity_used + detail.quantity_returned) == detail.quantity_issued


@pytest.mark.asyncio
async def test_over_issue_prevention_safeguard(db: AsyncSession):
    dept = Department(name=f"Stores Security {uuid.uuid4().hex[:4]}", code=f"SS-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    user = User(
        email=f"store_sec_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Store",
        last_name="Officer",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(user)
    await db.commit()

    req_dto = MaterialRequirementCreate(
        material_name="Warman Impeller 8/6",
        quantity_required=2.0,
        department_id=dept.id,
    )
    req = await MaterialService.create_requirement(db, req_dto, user)
    await MaterialService.approve_requirement(db, req.id, MaterialRequirementApprove(quantity_approved=2.0), user)

    # Attempt to issue 5 units (exceeding approved allocation of 2)
    with pytest.raises(HTTPException) as exc:
        await MaterialService.issue_material(db, req.id, MaterialIssueRequest(quantity=5.0), user)
    assert exc.value.status_code == 400
    assert "Over-issue prevented" in exc.value.detail


@pytest.mark.asyncio
async def test_over_consumption_and_over_return_prevention(db: AsyncSession):
    dept = Department(name=f"Electrical Spares {uuid.uuid4().hex[:4]}", code=f"ES-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    user = User(
        email=f"elec_store_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Elec",
        last_name="Admin",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(user)
    await db.commit()

    req_dto = MaterialRequirementCreate(
        material_name="Copper Cable 35mm2",
        quantity_required=50.0,
        unit="meters",
        department_id=dept.id,
    )
    req = await MaterialService.create_requirement(db, req_dto, user)
    await MaterialService.approve_requirement(db, req.id, MaterialRequirementApprove(quantity_approved=50.0), user)

    # Issue 20 meters
    await MaterialService.issue_material(db, req.id, MaterialIssueRequest(quantity=20.0), user)

    # Attempt to record usage of 30 meters (exceeding 20 issued)
    with pytest.raises(HTTPException) as exc:
        await MaterialService.record_usage(db, req.id, MaterialUsageRequest(quantity=30.0), user)
    assert exc.value.status_code == 400

    # Attempt to return 25 meters (exceeding 20 issued)
    with pytest.raises(HTTPException) as exc:
        await MaterialService.return_material(db, req.id, MaterialReturnRequest(quantity=25.0), user)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_work_item_and_asset_material_integration(db: AsyncSession):
    dept = Department(name=f"Fixed Plant {uuid.uuid4().hex[:4]}", code=f"FP-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    user = User(
        email=f"fixed_eng_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Fixed",
        last_name="Engineer",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(user)
    await db.commit()

    # Create Asset & WorkItem
    asset = Asset(
        name="Ball Mill 01 Primary",
        asset_tag=f"AST-BM1-{uuid.uuid4().hex[:4].upper()}",
        asset_type="PRODUCTION_EQUIPMENT",
        department_id=dept.id,
        status="AVAILABLE",
    )
    db.add(asset)
    await db.commit()

    work_item = WorkItem(
        id=uuid.uuid4(),
        reference_number=f"PM-2026-{uuid.uuid4().hex[:6].upper()}",
        work_type="MAINTENANCE",
        title="Ball Mill Liner Plate Replacement",
        department_id=dept.id,
        asset_id=asset.id,
        requester_id=user.id,
        status="IN_PROGRESS",
    )
    db.add(work_item)
    await db.commit()

    # Submit Material Requirement linked to both WorkItem and Asset
    req_dto = MaterialRequirementCreate(
        material_name="Cr-Mo Mill Liner Bolt M30x180",
        part_number="BOLT-CRMO-30180",
        quantity_required=120.0,
        unit="units",
        unit_cost=18.50,
        work_item_id=work_item.id,
        asset_id=asset.id,
        department_id=dept.id,
    )
    req = await MaterialService.create_requirement(db, req_dto, user)
    assert req.work_item_id == work_item.id
    assert req.asset_id == asset.id

    detail = await MaterialService.get_requirement(db, req.id, user)
    assert detail.work_item_reference == work_item.reference_number
    assert detail.asset_name == asset.name


@pytest.mark.asyncio
async def test_inventory_adapter_erp_integration_readiness():
    stock_info = await inventory_adapter.check_stock_availability("SKF-23152", "CENTRAL_WAREHOUSE")
    assert stock_info["part_number"] == "SKF-23152"
    assert stock_info["status"] == "IN_STOCK"

    issue_info = await inventory_adapter.post_goods_issue("req-123", "SKF-23152", 2.0, "units")
    assert issue_info["success"] is True
    assert issue_info["external_document_number"].startswith("ERP-GI-")

    return_info = await inventory_adapter.post_goods_return("req-123", "SKF-23152", 1.0, "units")
    assert return_info["success"] is True
    assert return_info["external_document_number"].startswith("ERP-GR-")
