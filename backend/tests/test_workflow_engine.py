import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.iam.models import User, Department
from app.modules.workflow.schemas import (
    WorkflowStateSchema,
    WorkflowTransitionSchema,
    WorkflowTemplateCreate,
)
from app.modules.workflow.service import WorkflowService, validate_workflow_definition
from app.core.security import get_password_hash


# ── Shared helper fixtures ────────────────────────────────────────────────────

def _make_simple_states():
    return [
        WorkflowStateSchema(name="DRAFT", label="Draft", is_initial=True, is_terminal=False),
        WorkflowStateSchema(name="SUBMITTED", label="Submitted", is_initial=False, is_terminal=False),
        WorkflowStateSchema(name="APPROVED", label="Approved", is_initial=False, is_terminal=False),
        WorkflowStateSchema(name="CLOSED", label="Closed", is_initial=False, is_terminal=True),
    ]


def _make_simple_transitions():
    return [
        WorkflowTransitionSchema(
            from_state="DRAFT", to_state="SUBMITTED", action="submit",
            required_role="Operator", label="Submit for Review"
        ),
        WorkflowTransitionSchema(
            from_state="SUBMITTED", to_state="APPROVED", action="approve",
            required_role="Supervisor", required_permission="job_card:approve", label="Approve"
        ),
        WorkflowTransitionSchema(
            from_state="SUBMITTED", to_state="DRAFT", action="return",
            required_role="Supervisor", label="Return for Correction"
        ),
        WorkflowTransitionSchema(
            from_state="APPROVED", to_state="CLOSED", action="close",
            required_role="Supervisor", label="Close Work"
        ),
    ]


async def _create_user(db: AsyncSession, dept: Department, superuser: bool = True) -> User:
    user = User(
        email=f"wf_{uuid.uuid4().hex[:6]}@plant.local",
        first_name="Workflow",
        last_name="User",
        is_active=True,
        is_superuser=superuser,
        department_id=dept.id,
        hashed_password=get_password_hash("Pass1234!"),
    )
    db.add(user)
    await db.commit()
    return user


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_workflow_template_creation_and_validation(db: AsyncSession):
    """Template must pass structural validation before being accepted."""
    dept = Department(name=f"WF Dept {uuid.uuid4().hex[:4]}", code=f"WF-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()
    admin = await _create_user(db, dept)

    dto = WorkflowTemplateCreate(
        name="Machine Request Standard",
        description="Standard machine request workflow",
        entity_type="REQUEST",
        states=_make_simple_states(),
        transitions=_make_simple_transitions(),
    )
    template = await WorkflowService.create_template(db, dto, admin)
    assert template.id is not None
    assert template.version == 1
    assert template.is_active is False
    assert len(template.states) == 4
    assert len(template.transitions) == 4


@pytest.mark.asyncio
async def test_invalid_template_rejection_missing_terminal_state(db: AsyncSession):
    """Template with no terminal state must be rejected with a validation error."""
    dept = Department(name=f"WF Val {uuid.uuid4().hex[:4]}", code=f"WFV-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()
    admin = await _create_user(db, dept)

    states = [
        WorkflowStateSchema(name="DRAFT", is_initial=True, is_terminal=False),
        WorkflowStateSchema(name="SUBMITTED", is_initial=False, is_terminal=False),
    ]
    transitions = [
        WorkflowTransitionSchema(
            from_state="DRAFT", to_state="SUBMITTED", action="submit", required_role="Operator"
        ),
    ]

    result = validate_workflow_definition(
        [s.model_dump() for s in states],
        [t.model_dump() for t in transitions],
    )
    assert result.valid is False
    assert any("terminal" in e.lower() for e in result.errors)


@pytest.mark.asyncio
async def test_invalid_template_rejection_unknown_state_in_transition(db: AsyncSession):
    """Transition referencing a state not declared in states must be rejected."""
    states = [
        WorkflowStateSchema(name="DRAFT", is_initial=True, is_terminal=False),
        WorkflowStateSchema(name="DONE", is_initial=False, is_terminal=True),
    ]
    transitions = [
        WorkflowTransitionSchema(
            from_state="DRAFT", to_state="NONEXISTENT_STATE", action="go",
            required_role="Operator"
        ),
    ]
    result = validate_workflow_definition(
        [s.model_dump() for s in states],
        [t.model_dump() for t in transitions],
    )
    assert result.valid is False
    assert any("NONEXISTENT_STATE" in e for e in result.errors)


@pytest.mark.asyncio
async def test_invalid_template_rejection_missing_authority(db: AsyncSession):
    """Transition with neither required_role nor required_permission must be rejected."""
    states = [
        WorkflowStateSchema(name="OPEN", is_initial=True, is_terminal=False),
        WorkflowStateSchema(name="CLOSED", is_initial=False, is_terminal=True),
    ]
    transitions = [
        WorkflowTransitionSchema(
            from_state="OPEN", to_state="CLOSED", action="close",
            required_role=None, required_permission=None,
        ),
    ]
    result = validate_workflow_definition(
        [s.model_dump() for s in states],
        [t.model_dump() for t in transitions],
    )
    assert result.valid is False
    assert any("required_role or required_permission" in e for e in result.errors)


@pytest.mark.asyncio
async def test_workflow_instance_creation_and_initial_state(db: AsyncSession):
    """A workflow instance must be created at the template's initial state."""
    dept = Department(name=f"WF Inst {uuid.uuid4().hex[:4]}", code=f"WFI-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()
    admin = await _create_user(db, dept)

    # Create and activate template
    dto = WorkflowTemplateCreate(
        name=f"Work Item WF {uuid.uuid4().hex[:4]}",
        entity_type="WORK_ITEM",
        states=_make_simple_states(),
        transitions=_make_simple_transitions(),
    )
    template = await WorkflowService.create_template(db, dto, admin)
    await WorkflowService.activate_template(db, template.id, admin)

    entity_id = uuid.uuid4()
    instance = await WorkflowService.create_instance(
        db=db,
        entity_type="WORK_ITEM",
        entity_id=entity_id,
        current_user=admin,
    )
    assert instance.id is not None
    assert instance.current_state == "DRAFT"
    assert instance.template_id == template.id
    assert instance.completed_at is None
    assert len(instance.template_snapshot.get("states", [])) == 4


@pytest.mark.asyncio
async def test_authorized_transition_execution(db: AsyncSession):
    """Superuser must be able to execute any valid transition."""
    dept = Department(name=f"WF Trans {uuid.uuid4().hex[:4]}", code=f"WFT-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()
    admin = await _create_user(db, dept)

    dto = WorkflowTemplateCreate(
        name=f"Auth Transition WF {uuid.uuid4().hex[:4]}",
        entity_type="WORK_ITEM",
        states=_make_simple_states(),
        transitions=_make_simple_transitions(),
    )
    template = await WorkflowService.create_template(db, dto, admin)
    await WorkflowService.activate_template(db, template.id, admin)

    entity_id = uuid.uuid4()
    instance = await WorkflowService.create_instance(
        db=db, entity_type="WORK_ITEM", entity_id=entity_id, current_user=admin
    )
    assert instance.current_state == "DRAFT"

    # Submit
    instance = await WorkflowService.execute_transition(db, instance.id, "submit", admin)
    assert instance.current_state == "SUBMITTED"

    # Approve
    instance = await WorkflowService.execute_transition(db, instance.id, "approve", admin)
    assert instance.current_state == "APPROVED"

    # Close — must mark completed
    instance = await WorkflowService.execute_transition(db, instance.id, "close", admin, notes="Work verified and closed")
    assert instance.current_state == "CLOSED"
    assert instance.completed_at is not None


@pytest.mark.asyncio
async def test_unauthorized_transition_rejection(db: AsyncSession):
    """Non-superuser without the required role must be rejected."""
    dept = Department(name=f"WF AuthZ {uuid.uuid4().hex[:4]}", code=f"WFA-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()

    admin = await _create_user(db, dept, superuser=True)
    regular_user = await _create_user(db, dept, superuser=False)

    dto = WorkflowTemplateCreate(
        name=f"AuthZ WF {uuid.uuid4().hex[:4]}",
        entity_type="REQUEST",
        states=_make_simple_states(),
        transitions=_make_simple_transitions(),
    )
    template = await WorkflowService.create_template(db, dto, admin)
    await WorkflowService.activate_template(db, template.id, admin)

    entity_id = uuid.uuid4()
    instance = await WorkflowService.create_instance(
        db=db, entity_type="REQUEST", entity_id=entity_id, current_user=admin
    )
    # Submit with admin to advance
    instance = await WorkflowService.execute_transition(db, instance.id, "submit", admin)
    assert instance.current_state == "SUBMITTED"

    # Non-superuser tries to approve (requires role "Supervisor")
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await WorkflowService.execute_transition(db, instance.id, "approve", regular_user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_invalid_action_from_current_state_rejected(db: AsyncSession):
    """Executing an action not valid from the current state must raise 422."""
    dept = Department(name=f"WF Bad {uuid.uuid4().hex[:4]}", code=f"WFB-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()
    admin = await _create_user(db, dept)

    dto = WorkflowTemplateCreate(
        name=f"BadAction WF {uuid.uuid4().hex[:4]}",
        entity_type="WORK_ITEM",
        states=_make_simple_states(),
        transitions=_make_simple_transitions(),
    )
    template = await WorkflowService.create_template(db, dto, admin)
    await WorkflowService.activate_template(db, template.id, admin)

    entity_id = uuid.uuid4()
    instance = await WorkflowService.create_instance(
        db=db, entity_type="WORK_ITEM", entity_id=entity_id, current_user=admin
    )
    assert instance.current_state == "DRAFT"

    # "approve" is not valid from DRAFT state
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await WorkflowService.execute_transition(db, instance.id, "approve", admin)
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_workflow_template_versioning(db: AsyncSession):
    """
    Creating a new template with the same name increments version.
    Activating a new version deactivates the old one.
    """
    dept = Department(name=f"WF Ver {uuid.uuid4().hex[:4]}", code=f"WFVr-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()
    admin = await _create_user(db, dept)

    name = f"Versioned WF {uuid.uuid4().hex[:6]}"

    # Version 1
    dto1 = WorkflowTemplateCreate(
        name=name,
        entity_type="WORK_ITEM",
        states=_make_simple_states(),
        transitions=_make_simple_transitions(),
    )
    t1 = await WorkflowService.create_template(db, dto1, admin)
    assert t1.version == 1
    await WorkflowService.activate_template(db, t1.id, admin)

    # Version 2 — same name
    dto2 = WorkflowTemplateCreate(
        name=name,
        entity_type="WORK_ITEM",
        states=_make_simple_states(),
        transitions=_make_simple_transitions(),
    )
    t2 = await WorkflowService.create_template(db, dto2, admin)
    assert t2.version == 2
    assert t2.is_active is False

    await WorkflowService.activate_template(db, t2.id, admin)

    # Re-fetch t1 — must now be inactive
    from sqlalchemy import select
    from app.modules.workflow.models import WorkflowTemplate
    res = await db.execute(select(WorkflowTemplate).where(WorkflowTemplate.id == t1.id))
    t1_refreshed = res.scalar_one()
    assert t1_refreshed.is_active is False

    res2 = await db.execute(select(WorkflowTemplate).where(WorkflowTemplate.id == t2.id))
    t2_refreshed = res2.scalar_one()
    assert t2_refreshed.is_active is True


@pytest.mark.asyncio
async def test_historical_instance_not_affected_by_template_changes(db: AsyncSession):
    """
    A WorkflowInstance snapshot is frozen at creation time.
    Changing/deactivating the template must not affect existing instances.
    """
    dept = Department(name=f"WF Snap {uuid.uuid4().hex[:4]}", code=f"WFS-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()
    admin = await _create_user(db, dept)

    dto = WorkflowTemplateCreate(
        name=f"Snap WF {uuid.uuid4().hex[:6]}",
        entity_type="WORK_ITEM",
        states=_make_simple_states(),
        transitions=_make_simple_transitions(),
    )
    template = await WorkflowService.create_template(db, dto, admin)
    await WorkflowService.activate_template(db, template.id, admin)

    entity_id = uuid.uuid4()
    instance = await WorkflowService.create_instance(
        db=db, entity_type="WORK_ITEM", entity_id=entity_id, current_user=admin
    )
    original_snapshot = dict(instance.template_snapshot)

    # Deactivate template (simulates replacing with a new version)
    from sqlalchemy import update
    from app.modules.workflow.models import WorkflowTemplate
    await db.execute(
        update(WorkflowTemplate).where(WorkflowTemplate.id == template.id).values(is_active=False)
    )
    await db.commit()

    # Instance snapshot must be unchanged
    from sqlalchemy import select
    from app.modules.workflow.models import WorkflowInstance
    res = await db.execute(select(WorkflowInstance).where(WorkflowInstance.id == instance.id))
    refreshed = res.scalar_one()
    assert refreshed.template_snapshot == original_snapshot
    assert refreshed.current_state == "DRAFT"


@pytest.mark.asyncio
async def test_immutable_transition_log_append_only(db: AsyncSession):
    """Transition log must accumulate entries; completing must not remove history."""
    dept = Department(name=f"WF Log {uuid.uuid4().hex[:4]}", code=f"WFL-{uuid.uuid4().hex[:4]}")
    db.add(dept)
    await db.commit()
    admin = await _create_user(db, dept)

    dto = WorkflowTemplateCreate(
        name=f"Log WF {uuid.uuid4().hex[:6]}",
        entity_type="WORK_ITEM",
        states=_make_simple_states(),
        transitions=_make_simple_transitions(),
    )
    template = await WorkflowService.create_template(db, dto, admin)
    await WorkflowService.activate_template(db, template.id, admin)

    entity_id = uuid.uuid4()
    instance = await WorkflowService.create_instance(
        db=db, entity_type="WORK_ITEM", entity_id=entity_id, current_user=admin
    )
    # 1 INITIALIZE log already written

    await WorkflowService.execute_transition(db, instance.id, "submit", admin)
    await WorkflowService.execute_transition(db, instance.id, "approve", admin)
    await WorkflowService.execute_transition(db, instance.id, "close", admin, notes="All verified")

    detail = await WorkflowService.build_instance_response(db, instance)
    # INITIALIZE + submit + approve + close = 4 entries
    assert len(detail.transition_logs) == 4
    assert detail.transition_logs[0].action == "INITIALIZE"
    assert detail.transition_logs[-1].action == "close"
    assert detail.transition_logs[-1].to_state == "CLOSED"
