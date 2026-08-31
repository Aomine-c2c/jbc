import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.modules.iam.models import User, Department, Organization, Site, Location
from app.modules.work.models import WorkItem
from app.modules.requests.models import (
    OperationalRequest,
    RequestMaterialItem,
    RequestActionLog,
    RequestType,
    RequestStatus,
    FulfillmentStatus,
)
from app.modules.requests.schemas import (
    RequestCreate,
    RequestUpdate,
    RequestTransition,
    RequestFulfill,
    RequestMaterialItemCreate,
    MaterialIssueRequest,
    MaterialReturnRequest,
    RequestCommentCreate,
)
from app.modules.requests.service import RequestService
from app.core.security import get_password_hash


@pytest.mark.asyncio
async def test_create_all_request_types_and_number_prefixes(db: AsyncSession):
    dept = Department(name=f"Operations Planning {uuid.uuid4().hex[:4]}", code=f"OPL-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    user = User(
        email=f"requester_{uuid.uuid4().hex[:4]}@example.com",
        first_name="John",
        last_name="Requester",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(user)
    await db.commit()

    types = [
        "MACHINE_REQUEST",
        "EQUIPMENT_REQUEST",
        "VEHICLE_REQUEST",
        "MATERIAL_REQUEST",
        "PERSONNEL_REQUEST",
        "CONTRACTOR_REQUEST",
        "OTHER",
    ]
    created = []

    for t in types:
        dto = RequestCreate(
            request_type=t,
            title=f"Requisition for {t}",
            purpose="Routine operational maintenance requirement",
            priority=2,
            department_id=dept.id,
        )
        req = await RequestService.create_request(db, dto, user)
        assert req.id is not None
        assert req.request_type == t
        assert req.status == "DRAFT"
        assert req.fulfillment_status == "UNALLOCATED"
        created.append(req)

    assert created[0].request_number.startswith("MR-")
    assert created[1].request_number.startswith("EQ-")
    assert created[2].request_number.startswith("VEH-")
    assert created[3].request_number.startswith("MAT-")
    assert created[4].request_number.startswith("PRS-")
    assert created[5].request_number.startswith("CON-")
    assert created[6].request_number.startswith("REQ-")


@pytest.mark.asyncio
async def test_full_lifecycle_and_separation_of_duties(db: AsyncSession):
    dept = Department(name=f"Civil Engineering {uuid.uuid4().hex[:4]}", code=f"CE-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    requester = User(
        email=f"civil_req_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Civil",
        last_name="Requester",
        is_active=True,
        is_superuser=False,  # Regular user to test SoD
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    approver = User(
        email=f"civil_app_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Civil",
        last_name="Approver",
        is_active=True,
        is_superuser=False,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    fulfiller = User(
        email=f"civil_ful_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Dispatcher",
        last_name="Officer",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(requester)
    db.add(approver)
    db.add(fulfiller)
    await db.commit()

    dto = RequestCreate(
        request_type="MACHINE_REQUEST",
        title="50T Mobile Crane for Ball Mill Trommel Lift",
        purpose="Scheduled maintenance heavy lifting requirement",
        priority=3,
        department_id=dept.id,
        estimated_duration_hours=8.0,
    )
    req = await RequestService.create_request(db, dto, requester)
    assert req.status == "DRAFT"

    # Step 1: Submit
    req = await RequestService.transition_lifecycle(db, req.id, RequestTransition(action="SUBMIT", notes="Submitted for engineering review"), requester)
    assert req.status == "SUBMITTED"

    # Step 2: Review
    req = await RequestService.transition_lifecycle(db, req.id, RequestTransition(action="REVIEW", notes="Reviewed by section planner"), approver)
    assert req.status == "UNDER_REVIEW"

    # Step 3: Separation of Duties Check - Requester cannot self-approve
    with pytest.raises(HTTPException) as exc:
        await RequestService.transition_lifecycle(db, req.id, RequestTransition(action="APPROVE"), requester)
    assert exc.value.status_code == 409

    # Step 4: Legitimate Approval by independent user
    req = await RequestService.transition_lifecycle(db, req.id, RequestTransition(action="APPROVE", notes="Approved within budget"), approver)
    assert req.status == "APPROVED"
    assert req.fulfillment_status == "AWAITING_FULFILLMENT"
    assert req.approver_id == approver.id

    # Step 5: Fulfillment / Resource Dispatch
    req = await RequestService.fulfill_request(db, req.id, RequestFulfill(fulfillment_status="FULFILLED", notes="Crane CR-002 dispatched with operator", actual_cost=650.0), fulfiller)
    assert req.status == "FULFILLED"
    assert req.fulfillment_status == "FULFILLED"
    assert req.fulfillment_user_id == fulfiller.id
    assert req.actual_cost == 650.0


@pytest.mark.asyncio
async def test_material_request_line_items_issue_and_return(db: AsyncSession):
    dept = Department(name=f"Mechanical Stores {uuid.uuid4().hex[:4]}", code=f"MS-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    user = User(
        email=f"store_clerk_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Store",
        last_name="Clerk",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(user)
    await db.commit()

    dto = RequestCreate(
        request_type="MATERIAL_REQUEST",
        title="Spares for Slurry Pump Overhaul",
        purpose="Replacement impellers and gland packing rings",
        department_id=dept.id,
        material_items=[
            RequestMaterialItemCreate(
                material_name="Warman 8/6 Impeller 5-Vane",
                part_number="W86-IMP-5",
                quantity_requested=2.0,
                unit="units",
                store_location="Warehouse Bay 4B",
                unit_cost=1200.0,
            ),
            RequestMaterialItemCreate(
                material_name="PTFE Gland Packing 1/2 inch",
                part_number="GP-PTFE-050",
                quantity_requested=10.0,
                unit="meters",
                store_location="Spares Bin 12",
                unit_cost=15.0,
            ),
        ],
    )
    req = await RequestService.create_request(db, dto, user)
    detail = await RequestService.get_request(db, req.id, user)
    assert len(detail.material_items) == 2

    item1_id = detail.material_items[0].id
    item2_id = detail.material_items[1].id

    # Approve request to allow stores issuance
    await RequestService.transition_lifecycle(db, req.id, RequestTransition(action="SUBMIT"), user)
    await RequestService.transition_lifecycle(db, req.id, RequestTransition(action="APPROVE"), user)

    # Partial Issue: Issue 1 impeller
    await RequestService.issue_material_items(db, req.id, MaterialIssueRequest(item_id=item1_id, quantity=1.0), user)
    req_state = await RequestService.get_request(db, req.id, user)
    assert req_state.fulfillment_status == "PARTIALLY_FULFILLED"

    # Issue Remaining Items: 1 impeller + 10m packing
    await RequestService.issue_material_items(db, req.id, MaterialIssueRequest(item_id=item1_id, quantity=1.0), user)
    await RequestService.issue_material_items(db, req.id, MaterialIssueRequest(item_id=item2_id, quantity=10.0), user)
    
    req_state = await RequestService.get_request(db, req.id, user)
    assert req_state.fulfillment_status == "FULFILLED"
    assert req_state.status == "FULFILLED"

    # Return Unused: 2 meters of packing returned
    await RequestService.return_material_items(db, req.id, MaterialReturnRequest(item_id=item2_id, quantity=2.0), user)
    req_state = await RequestService.get_request(db, req.id, user)
    updated_item2 = next(i for i in req_state.material_items if i.id == item2_id)
    assert updated_item2.quantity_returned == 2.0


@pytest.mark.asyncio
async def test_work_item_and_request_bidirectional_linking(db: AsyncSession):
    dept = Department(name=f"Electrical Engineering {uuid.uuid4().hex[:4]}", code=f"EE-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    user = User(
        email=f"elec_lead_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Elec",
        last_name="Lead",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(user)
    await db.commit()

    # 1. Create a Work Item
    work_item = WorkItem(
        id=uuid.uuid4(),
        reference_number=f"JC-2026-{uuid.uuid4().hex[:6].upper()}",
        work_type="JOB_CARD",
        title="Overhead Powerline Sag Correction",
        department_id=dept.id,
        requester_id=user.id,
        status="IN_PROGRESS",
    )
    db.add(work_item)
    await db.commit()

    # 2. Create a Contractor Requisition linked to the Work Item
    req_dto = RequestCreate(
        request_type="CONTRACTOR_REQUEST",
        title="High-Voltage Certified Lineman Team",
        purpose="Specialized 33kV tensioning and splicing team required",
        department_id=dept.id,
        work_item_id=work_item.id,
        type_specific_data={
            "required_service": "High Voltage Line Splicing",
            "required_skill": "33kV Certified Lineman",
            "work_scope": "Re-tension spans 12-18 and replace damaged insulator discs",
            "contractor_name": "ZESA Transmission Services",
        },
    )
    req = await RequestService.create_request(db, req_dto, user)
    assert req.work_item_id == work_item.id

    # 3. Verify cross-referencing in details
    detail = await RequestService.get_request(db, req.id, user)
    assert detail.work_item_reference == work_item.reference_number
    assert detail.type_specific_data["contractor_name"] == "ZESA Transmission Services"
    assert detail.type_specific_data["required_skill"] == "33kV Certified Lineman"

    # Add a comment
    comment = await RequestService.add_comment(db, req.id, RequestCommentCreate(comment="Contractor arrival confirmed for 08:00 tomorrow"), user)
    assert comment.id is not None

    detail_with_comment = await RequestService.get_request(db, req.id, user)
    assert len(detail_with_comment.comments) == 1
    assert detail_with_comment.comments[0].comment == "Contractor arrival confirmed for 08:00 tomorrow"
