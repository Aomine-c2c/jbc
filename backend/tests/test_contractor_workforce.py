import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.modules.iam.models import User, Department
from app.modules.work.models import WorkItem
from app.modules.contractors.models import (
    ContractorCompany,
    ContractorWorker,
    ContractorAssignment,
    ContractorWorkerAssignment,
)
from app.modules.contractors.schemas import (
    ContractorCompanyCreate,
    ContractorWorkerCreate,
    ContractorAssignmentCreate,
    ContractorAssignmentVerify,
)
from app.modules.contractors.service import ContractorService
from app.core.security import get_password_hash


@pytest.mark.asyncio
async def test_contractor_company_and_worker_creation(db: AsyncSession):
    dept = Department(name=f"Engineering Services {uuid.uuid4().hex[:4]}", code=f"ENG-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    admin = User(
        email=f"vendor_mgr_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Vendor",
        last_name="Manager",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(admin)
    await db.commit()

    # 1. Register Contractor Company
    co_dto = ContractorCompanyCreate(
        name="ABB High Voltage Engineering Ltd",
        registration_number="VAT-8849102",
        primary_contact_name="Mark Zondo",
        contact_email="mark.zondo@abb-services.com",
        contact_phone="+263 772 112 334",
        service_categories=["High Voltage Electrical", "Transformer Overhaul", "Substation Automation"],
        safety_induction_valid_until=datetime.utcnow() + timedelta(days=365),
    )
    co = await ContractorService.create_company(db, co_dto, admin)
    assert co.id is not None
    assert co.company_code.startswith("CON-")
    assert "High Voltage Electrical" in co.service_categories

    # 2. Register Contractor Worker
    worker_dto = ContractorWorkerCreate(
        contractor_company_id=co.id,
        full_name="Tendai Chiweshe",
        skill_or_role="33kV Certified High Voltage Specialist",
        certification_records=[
            {"certification": "High Voltage Switching & Safety", "number": "HV-33KV-9081", "expiry": "2027-12-31"},
            {"certification": "First Aid at Work Level 3", "number": "FA-4412", "expiry": "2026-10-15"},
        ],
        certification_expiry=datetime.utcnow() + timedelta(days=300),
        phone_number="+263 773 998 112",
        badge_number="EXT-ABB-001",
    )
    worker = await ContractorService.create_worker(db, worker_dto, admin)
    assert worker.id is not None
    assert worker.worker_code.startswith("CW-")
    assert len(worker.certification_records) == 2


@pytest.mark.asyncio
async def test_contractor_assignment_linked_to_work_item_and_verification(db: AsyncSession):
    dept = Department(name=f"Substation Ops {uuid.uuid4().hex[:4]}", code=f"SUB-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    supervisor = User(
        email=f"sub_super_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Elec",
        last_name="Supervisor",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(supervisor)
    await db.commit()

    # Create Company & Worker
    co = await ContractorService.create_company(
        db,
        ContractorCompanyCreate(name="Siemens Energy Field Services", service_categories=["Switchgear"]),
        supervisor,
    )
    worker = await ContractorService.create_worker(
        db,
        ContractorWorkerCreate(
            contractor_company_id=co.id,
            full_name="John Mpofu",
            skill_or_role="Switchgear Commissioning Engineer",
        ),
        supervisor,
    )

    # Create WorkItem
    work_item = WorkItem(
        id=uuid.uuid4(),
        reference_number=f"WI-HV-{uuid.uuid4().hex[:6].upper()}",
        work_type="MAINTENANCE",
        title="33kV Substation SF6 Circuit Breaker Overhaul",
        department_id=dept.id,
        requester_id=supervisor.id,
        status="IN_PROGRESS",
    )
    db.add(work_item)
    await db.commit()

    # Create Contractor Assignment
    assign_dto = ContractorAssignmentCreate(
        contractor_company_id=co.id,
        worker_ids=[worker.id],
        work_item_id=work_item.id,
        work_scope="Annual SF6 gas testing, contact resistance measurement, and mechanism timing tests on CB-01 and CB-02",
        start_date=datetime.utcnow(),
        completion_date=datetime.utcnow() + timedelta(days=2),
        cost_agreed=4500.0,
    )
    assignment = await ContractorService.create_assignment(db, assign_dto, supervisor)
    assert assignment.id is not None
    assert assignment.assignment_number.startswith("CAS-")
    assert assignment.verification_status == "PENDING"
    assert assignment.cost_agreed == 4500.0

    # Verify Detail view with linked workers
    detail = await ContractorService.get_assignment(db, assignment.id, supervisor)
    assert detail.company_name == "Siemens Energy Field Services"
    assert detail.work_item_reference == work_item.reference_number
    assert len(detail.assigned_workers) == 1
    assert detail.assigned_workers[0].full_name == "John Mpofu"

    # Internal Supervisor Verification & Sign-off
    verify_dto = ContractorAssignmentVerify(
        verification_status="VERIFIED_ACCEPTED",
        performance_rating=5,
        performance_notes="Outstanding execution. Breaker timing within OEM tolerance. Zero safety non-conformances.",
        actual_cost=4500.0,
    )
    verified = await ContractorService.verify_assignment(db, assignment.id, verify_dto, supervisor)
    assert verified.verification_status == "VERIFIED_ACCEPTED"
    assert verified.performance_rating == 5
    assert verified.verified_by_id == supervisor.id
    assert verified.verified_at is not None


@pytest.mark.asyncio
async def test_contractor_company_archival_and_history_preservation(db: AsyncSession):
    dept = Department(name=f"Procurement {uuid.uuid4().hex[:4]}", code=f"PRO-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    user = User(
        email=f"proc_officer_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Proc",
        last_name="Officer",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(user)
    await db.commit()

    co = await ContractorService.create_company(
        db,
        ContractorCompanyCreate(name="Legacy Cranes & Rigging Ltd"),
        user,
    )

    # Soft-archive company
    archived = await ContractorService.archive_company(
        db, co.id, "Contract agreement expired at year end", user
    )
    assert archived.is_archived is True
    assert archived.status == "INACTIVE"
    assert archived.archived_reason == "Contract agreement expired at year end"

    # Verify excluded from active list but visible with include_archived=True
    active_list = await ContractorService.list_companies(db, user, include_archived=False)
    assert not any(c.id == co.id for c in active_list)

    all_list = await ContractorService.list_companies(db, user, include_archived=True)
    assert any(c.id == co.id for c in all_list)
