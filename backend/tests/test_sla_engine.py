import pytest
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.modules.iam.models import User, Department, Role, UserRole
from app.modules.sla.models import (
    SLAPolicy,
    SLATracker,
    SLAEscalationLog,
    SLAPriority,
    SLAStatus,
    SLAHealth,
)
from app.modules.sla.schemas import (
    SLAPolicyCreate,
    SLATrackerCreate,
    SLAAcknowledgeRequest,
    SLAPauseRequest,
    SLAResumeRequest,
)
from app.modules.sla.service import SLAService
from app.core.security import get_password_hash


@pytest.mark.asyncio
async def test_sla_policy_creation_and_dynamic_matching(db: AsyncSession):
    dept = Department(name=f"Instrumentation {uuid.uuid4().hex[:4]}", code=f"INST-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    admin = User(
        email=f"sla_admin_{uuid.uuid4().hex[:4]}@example.com",
        first_name="SLA",
        last_name="Admin",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(admin)
    await db.commit()

    # 1. Create Critical Plant Breakdown Policy
    crit_policy_dto = SLAPolicyCreate(
        name="Critical Breakdown Policy",
        priority="CRITICAL",
        response_time_minutes=15,
        completion_time_minutes=120,
        warning_threshold_percentage=80,
        escalation_rules=[
            {"level": 1, "trigger": "RESPONSE_WARNING", "after_percentage": 80, "target_role": "Supervisor"},
            {"level": 2, "trigger": "RESPONSE_BREACH", "after_percentage": 100, "target_role": "HOD"},
        ],
    )
    crit_policy = await SLAService.create_policy(db, crit_policy_dto, admin)
    assert crit_policy.id is not None
    assert crit_policy.response_time_minutes == 15

    # 2. Create Department Specific Maintenance Policy
    dept_policy_dto = SLAPolicyCreate(
        name="Instrumentation Standard Policy",
        priority="NORMAL",
        department_id=dept.id,
        response_time_minutes=60,
        completion_time_minutes=360,
    )
    dept_policy = await SLAService.create_policy(db, dept_policy_dto, admin)
    assert dept_policy.id is not None

    # 3. Test Dynamic Matching
    matched_crit = await SLAService.match_policy(db, priority="CRITICAL")
    assert matched_crit is not None
    assert matched_crit.id == crit_policy.id

    matched_dept = await SLAService.match_policy(db, priority="NORMAL", department_id=dept.id)
    assert matched_dept is not None
    assert matched_dept.id == dept_policy.id


@pytest.mark.asyncio
async def test_sla_tracker_lifecycle_response_and_completion(db: AsyncSession):
    dept = Department(name=f"Crushing {uuid.uuid4().hex[:4]}", code=f"CRU-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    user = User(
        email=f"shift_boss_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Shift",
        last_name="Boss",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(user)
    await db.commit()

    # Create Tracker for Crusher Jam
    tr_dto = SLATrackerCreate(
        resource_type="JOB_CARD",
        resource_id=uuid.uuid4(),
        resource_reference="JC-2026-901",
        title="Primary Jaw Crusher Chute Jam",
        priority="CRITICAL",
        department_id=dept.id,
    )
    tracker = await SLAService.create_tracker(db, tr_dto, user)
    assert tracker.id is not None
    assert tracker.health == SLAHealth.ON_TRACK.value
    assert tracker.target_response_at is not None
    assert tracker.target_completion_at is not None

    # Record Response / Acknowledge
    tracker = await SLAService.record_response(db, tracker.id, user, notes="Operator dispatched with breaker tool")
    assert tracker.status == SLAStatus.IN_PROGRESS.value
    assert tracker.actual_response_at is not None
    assert tracker.health == SLAHealth.ON_TRACK.value

    # Complete Tracker On-Time
    tracker = await SLAService.complete_tracker(db, tracker.id, user, notes="Chute cleared and feed restarted")
    assert tracker.status == SLAStatus.COMPLETED.value
    assert tracker.actual_completion_at is not None
    assert tracker.health == SLAHealth.MET.value


@pytest.mark.asyncio
async def test_sla_pause_and_resume_duration_extension(db: AsyncSession):
    dept = Department(name=f"Mechanical {uuid.uuid4().hex[:4]}", code=f"MEC-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    user = User(
        email=f"mech_lead_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Mech",
        last_name="Lead",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(user)
    await db.commit()

    tr_dto = SLATrackerCreate(
        resource_type="WORK_ITEM",
        resource_id=uuid.uuid4(),
        resource_reference="WI-2026-440",
        title="Ball Mill Liner Plate Replacement",
        priority="NORMAL",
        department_id=dept.id,
    )
    tracker = await SLAService.create_tracker(db, tr_dto, user)
    initial_comp_target = tracker.target_completion_at

    # Pause SLA (e.g. shift change / awaiting crane)
    tracker = await SLAService.pause_tracker(db, tracker.id, "Awaiting mobile crane arrival", user)
    assert tracker.status == SLAStatus.PAUSED.value
    assert tracker.paused_at is not None

    # Simulate 30-minute pause
    tracker.paused_at = datetime.now(timezone.utc) - timedelta(minutes=30)
    await db.commit()

    # Resume SLA
    tracker = await SLAService.resume_tracker(db, tracker.id, "Crane on site, lifting started", user)
    assert tracker.status == SLAStatus.IN_PROGRESS.value
    assert tracker.paused_at is None
    assert tracker.total_paused_minutes >= 29.0
    assert tracker.target_completion_at > initial_comp_target


@pytest.mark.asyncio
async def test_sla_evaluation_and_multi_tier_escalation(db: AsyncSession):
    dept = Department(name=f"Electrical {uuid.uuid4().hex[:4]}", code=f"ELE-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    user = User(
        email=f"elec_tech_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Elec",
        last_name="Tech",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(user)
    await db.commit()

    # Create Tracker with target response in the past (overdue / breached)
    tr_dto = SLATrackerCreate(
        resource_type="JOB_CARD",
        resource_id=uuid.uuid4(),
        resource_reference="JC-OVERDUE-01",
        title="Main Substation 33kV Transformer Trip",
        priority="CRITICAL",
        department_id=dept.id,
    )
    tracker = await SLAService.create_tracker(db, tr_dto, user)
    tracker.target_response_at = datetime.now(timezone.utc) - timedelta(minutes=20)
    await db.commit()

    # Evaluate SLA Trackers
    escalations_count = await SLAService.evaluate_trackers_and_escalate(db)
    assert escalations_count >= 1

    detail = await SLAService.get_tracker_detail(db, tracker.id, user)
    assert detail.health == SLAHealth.BREACHED_RESPONSE.value
    assert len(detail.escalation_logs) >= 1

    # Second evaluation run: must NOT create duplicate escalation log
    second_count = await SLAService.evaluate_trackers_and_escalate(db)
    assert second_count == 0


@pytest.mark.asyncio
async def test_sla_dashboard_metrics_and_compliance(db: AsyncSession):
    dept = Department(name=f"Plant Ops {uuid.uuid4().hex[:4]}", code=f"PO-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    user = User(
        email=f"plant_mgr_{uuid.uuid4().hex[:4]}@example.com",
        first_name="Plant",
        last_name="Manager",
        is_active=True,
        is_superuser=True,
        department_id=dept.id,
        hashed_password=get_password_hash("Secret123!"),
    )
    db.add(user)
    await db.commit()

    # Create 1 Active Tracker
    tr1 = await SLAService.create_tracker(
        db,
        SLATrackerCreate(
            resource_type="JOB_CARD",
            resource_id=uuid.uuid4(),
            title="Conveyor Belt 1 Splicing",
            priority="NORMAL",
            department_id=dept.id,
        ),
        user,
    )

    # Create 1 Completed Tracker
    tr2 = await SLAService.create_tracker(
        db,
        SLATrackerCreate(
            resource_type="WORK_ITEM",
            resource_id=uuid.uuid4(),
            title="Slurry Pump Packing Replacement",
            priority="HIGH",
            department_id=dept.id,
        ),
        user,
    )
    await SLAService.record_response(db, tr2.id, user)
    await SLAService.complete_tracker(db, tr2.id, user)

    # Query Dashboard
    dash = await SLAService.get_dashboard(db, dept.id)
    assert dash.total_active >= 1
    assert dash.compliance_percentage >= 0.0
