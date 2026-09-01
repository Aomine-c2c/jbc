import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.workflow.models import (
    WorkflowTemplate,
    WorkflowInstance,
    WorkflowTransitionLog,
    WorkflowEntityType,
)
from app.modules.workflow.schemas import (
    WorkflowTemplateCreate,
    WorkflowTemplateListResponse,
    WorkflowTemplateResponse,
    WorkflowInstanceResponse,
    WorkflowTransitionLogResponse,
    WorkflowValidationResult,
)
from app.modules.iam.models import User


# ── Structural Validation ─────────────────────────────────────────────────────

def validate_workflow_definition(
    states: List[Dict[str, Any]],
    transitions: List[Dict[str, Any]],
) -> WorkflowValidationResult:
    """
    Server-side structural validation of a workflow definition.
    Returns a WorkflowValidationResult with errors and warnings.
    """
    errors: list[str] = []
    warnings: list[str] = []

    state_names = {s["name"] for s in states}
    initial_states = [s["name"] for s in states if s.get("is_initial", False)]
    terminal_states = [s["name"] for s in states if s.get("is_terminal", False)]

    # Rule 1: At least one initial state
    if not initial_states:
        errors.append("Workflow must have at least one initial state (set is_initial=true on one state).")

    # Rule 2: At least one terminal state
    if not terminal_states:
        errors.append("Workflow must have at least one terminal state (set is_terminal=true on one state).")

    # Rule 3: All transition states must be declared
    for t in transitions:
        fs = t.get("from_state", "")
        ts = t.get("to_state", "")
        if fs not in state_names:
            errors.append(f"Transition '{t.get('action', '?')}' references unknown from_state: '{fs}'.")
        if ts not in state_names:
            errors.append(f"Transition '{t.get('action', '?')}' references unknown to_state: '{ts}'.")

    # Rule 4: Every transition must specify required_role OR required_permission
    for t in transitions:
        if not t.get("required_role") and not t.get("required_permission"):
            action = t.get("action", "?")
            errors.append(
                f"Transition '{action}' ({t.get('from_state','?')} → {t.get('to_state','?')}) "
                f"must define required_role or required_permission."
            )

    # Rule 5: Unreachable states (non-initial states that no transition leads to)
    reachable_via_transition = {t.get("to_state") for t in transitions if t.get("to_state")}
    for state in states:
        name = state["name"]
        if not state.get("is_initial", False) and name not in reachable_via_transition:
            errors.append(
                f"State '{name}' is unreachable — no transition leads to it and it is not an initial state."
            )

    # Warning: terminal states should not have outgoing transitions
    for state in states:
        if state.get("is_terminal", False):
            outgoing = [t for t in transitions if t.get("from_state") == state["name"]]
            if outgoing:
                warnings.append(
                    f"Terminal state '{state['name']}' has outgoing transitions — these will never fire."
                )

    return WorkflowValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


# ── WorkflowService ───────────────────────────────────────────────────────────

class WorkflowService:

    # ── Template Management ───────────────────────────────────────────────────

    @staticmethod
    async def create_template(
        db: AsyncSession,
        data: WorkflowTemplateCreate,
        current_user: User,
    ) -> WorkflowTemplate:
        """
        Validate and create a new workflow template (version 1, inactive).
        Templates must be explicitly activated before use.
        """
        states_raw = [s.model_dump() for s in data.states]
        transitions_raw = [t.model_dump() for t in data.transitions]

        result = validate_workflow_definition(states_raw, transitions_raw)
        if not result.valid:
            raise HTTPException(
                status_code=422,
                detail={"message": "Workflow definition is invalid.", "errors": result.errors},
            )

        # Determine next version for this name
        existing = await db.execute(
            select(WorkflowTemplate)
            .where(WorkflowTemplate.name == data.name.strip())
            .order_by(WorkflowTemplate.version.desc())
        )
        latest = existing.scalars().first()
        next_version = (latest.version + 1) if latest else 1

        template = WorkflowTemplate(
            id=uuid.uuid4(),
            name=data.name.strip(),
            description=data.description,
            entity_type=data.entity_type.upper().strip(),
            department_id=data.department_id,
            min_priority=data.min_priority,
            risk_level=data.risk_level.upper().strip() if data.risk_level else None,
            request_type=data.request_type.upper().strip() if data.request_type else None,
            version=next_version,
            is_active=False,
            is_default=data.is_default,
            states=states_raw,
            transitions=transitions_raw,
            created_by_id=current_user.id,
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def activate_template(
        db: AsyncSession,
        template_id: uuid.UUID,
        current_user: User,
    ) -> WorkflowTemplate:
        """
        Activate a workflow template version.
        Deactivates all other versions of the same name.
        """
        res = await db.execute(
            select(WorkflowTemplate).where(WorkflowTemplate.id == template_id)
        )
        template = res.scalar_one_or_none()
        if not template:
            raise HTTPException(status_code=404, detail="Workflow template not found.")

        # Deactivate all other versions with this name
        await db.execute(
            update(WorkflowTemplate)
            .where(
                WorkflowTemplate.name == template.name,
                WorkflowTemplate.id != template.id,
            )
            .values(is_active=False)
        )
        template.is_active = True
        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def list_templates(
        db: AsyncSession,
        entity_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> List[WorkflowTemplateListResponse]:
        query = select(WorkflowTemplate).order_by(
            WorkflowTemplate.name.asc(), WorkflowTemplate.version.desc()
        )
        if entity_type:
            query = query.where(
                WorkflowTemplate.entity_type.in_([entity_type.upper(), WorkflowEntityType.ANY.value])
            )
        if is_active is not None:
            query = query.where(WorkflowTemplate.is_active == is_active)
        if name:
            query = query.where(WorkflowTemplate.name.ilike(f"%{name.strip()}%"))

        res = await db.execute(query)
        templates = res.scalars().all()

        return [
            WorkflowTemplateListResponse(
                id=t.id,
                name=t.name,
                description=t.description,
                entity_type=t.entity_type,
                version=t.version,
                is_active=t.is_active,
                is_default=t.is_default,
                states_count=len(t.states or []),
                transitions_count=len(t.transitions or []),
                department_name=t.department.name if t.department else None,
                created_at=t.created_at,
            )
            for t in templates
        ]

    @staticmethod
    async def get_template(
        db: AsyncSession, template_id: uuid.UUID
    ) -> WorkflowTemplateResponse:
        res = await db.execute(
            select(WorkflowTemplate).where(WorkflowTemplate.id == template_id)
        )
        t = res.scalar_one_or_none()
        if not t:
            raise HTTPException(status_code=404, detail="Workflow template not found.")

        resp = WorkflowTemplateResponse.model_validate(t)
        resp.department_name = t.department.name if t.department else None
        return resp

    @staticmethod
    async def match_template(
        db: AsyncSession,
        entity_type: str,
        priority: Optional[int] = None,
        department_id: Optional[uuid.UUID] = None,
        risk_level: Optional[str] = None,
        request_type: Optional[str] = None,
    ) -> Optional[WorkflowTemplate]:
        """
        Return the highest-specificity active template matching the given criteria.
        Specificity: department_id (+20), priority (+15), risk_level (+10), request_type (+10), is_default (+1).
        """
        res = await db.execute(
            select(WorkflowTemplate).where(
                WorkflowTemplate.is_active == True,
                WorkflowTemplate.entity_type.in_(
                    [entity_type.upper(), WorkflowEntityType.ANY.value]
                ),
            )
        )
        templates = res.scalars().all()
        if not templates:
            return None

        best: Optional[WorkflowTemplate] = None
        best_score = -1

        norm_risk = risk_level.upper().strip() if risk_level else None
        norm_rt = request_type.upper().strip() if request_type else None

        for t in templates:
            score = 0
            if t.department_id:
                if t.department_id == department_id:
                    score += 20
                else:
                    continue
            if t.min_priority is not None:
                if priority is not None and priority >= t.min_priority:
                    score += 15
                else:
                    continue
            if t.risk_level:
                if t.risk_level == norm_risk:
                    score += 10
                else:
                    continue
            if t.request_type:
                if t.request_type == norm_rt:
                    score += 10
                else:
                    continue
            if t.is_default:
                score += 1
            if score > best_score:
                best_score = score
                best = t

        return best

    # ── Workflow Instance Operations ──────────────────────────────────────────

    @staticmethod
    async def create_instance(
        db: AsyncSession,
        entity_type: str,
        entity_id: uuid.UUID,
        current_user: User,
        template_id: Optional[uuid.UUID] = None,
        priority: Optional[int] = None,
        department_id: Optional[uuid.UUID] = None,
        risk_level: Optional[str] = None,
        request_type: Optional[str] = None,
    ) -> WorkflowInstance:
        """Start a workflow instance for any entity."""
        # Resolve template
        template: Optional[WorkflowTemplate] = None
        if template_id:
            res = await db.execute(
                select(WorkflowTemplate).where(WorkflowTemplate.id == template_id)
            )
            template = res.scalar_one_or_none()
            if not template:
                raise HTTPException(status_code=404, detail="Workflow template not found.")
        else:
            template = await WorkflowService.match_template(
                db=db,
                entity_type=entity_type,
                priority=priority,
                department_id=department_id,
                risk_level=risk_level,
                request_type=request_type,
            )

        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"No active workflow template found for entity_type='{entity_type}'. "
                       f"Create and activate a workflow template first.",
            )

        initial_states = template.get_initial_states()
        if not initial_states:
            raise HTTPException(
                status_code=422,
                detail="Template has no initial state defined.",
            )

        snapshot = {
            "states": template.states,
            "transitions": template.transitions,
        }

        instance = WorkflowInstance(
            id=uuid.uuid4(),
            template_id=template.id,
            template_version=template.version,
            entity_type=entity_type.upper().strip(),
            entity_id=entity_id,
            current_state=initial_states[0],
            template_snapshot=snapshot,
        )
        db.add(instance)

        # Record initialization log
        log = WorkflowTransitionLog(
            id=uuid.uuid4(),
            instance_id=instance.id,
            action="INITIALIZE",
            from_state="—",
            to_state=initial_states[0],
            actor_id=current_user.id,
            actor_name=f"{current_user.first_name} {current_user.last_name}",
            notes=f"Workflow instance created using template '{template.name}' v{template.version}.",
        )
        db.add(log)
        await db.commit()
        await db.refresh(instance)
        return instance

    @staticmethod
    async def get_instance(
        db: AsyncSession,
        entity_type: str,
        entity_id: uuid.UUID,
    ) -> Optional[WorkflowInstance]:
        res = await db.execute(
            select(WorkflowInstance).where(
                WorkflowInstance.entity_type == entity_type.upper().strip(),
                WorkflowInstance.entity_id == entity_id,
            )
            .order_by(WorkflowInstance.created_at.desc())
        )
        return res.scalars().first()

    @staticmethod
    async def get_instance_by_id(
        db: AsyncSession, instance_id: uuid.UUID
    ) -> WorkflowInstance:
        res = await db.execute(
            select(WorkflowInstance).where(WorkflowInstance.id == instance_id)
        )
        instance = res.scalar_one_or_none()
        if not instance:
            raise HTTPException(status_code=404, detail="Workflow instance not found.")
        return instance

    @staticmethod
    async def execute_transition(
        db: AsyncSession,
        instance_id: uuid.UUID,
        action: str,
        actor: User,
        notes: Optional[str] = None,
    ) -> WorkflowInstance:
        """
        Execute a state transition on a workflow instance.
        Validates:
          - Instance is not already completed
          - Transition exists from current state with this action
          - Actor has required_role or required_permission
          - Conditions are met
        """
        res = await db.execute(
            select(WorkflowInstance).where(WorkflowInstance.id == instance_id)
        )
        instance = res.scalar_one_or_none()
        if not instance:
            raise HTTPException(status_code=404, detail="Workflow instance not found.")

        if instance.completed_at:
            raise HTTPException(
                status_code=409,
                detail="This workflow instance is already completed. No further transitions are allowed.",
            )

        # Find matching transition
        available = instance.get_available_transitions()
        matching = [t for t in available if t.get("action") == action.strip()]
        if not matching:
            available_actions = [t.get("action") for t in available]
            raise HTTPException(
                status_code=422,
                detail=f"Action '{action}' is not a valid transition from state '{instance.current_state}'. "
                       f"Available actions: {available_actions}.",
            )

        transition = matching[0]

        # Authorization check
        required_role = transition.get("required_role")
        required_permission = transition.get("required_permission")
        actor_role_names = []
        if hasattr(actor, "user_roles") and actor.user_roles:
            actor_role_names = [ur.role.name for ur in actor.user_roles if ur.role]

        authorized = actor.is_superuser
        if not authorized and required_role:
            authorized = required_role in actor_role_names
        if not authorized and required_permission:
            try:
                from app.core.authz import require_permission
                require_permission(actor, required_permission)
                authorized = True
            except Exception:
                pass

        if not authorized:
            raise HTTPException(
                status_code=403,
                detail=f"You are not authorized to perform action '{action}'. "
                       f"Required role: {required_role or 'N/A'} / permission: {required_permission or 'N/A'}.",
            )

        # Condition check (priority, risk_level)
        conditions = transition.get("conditions") or {}
        if conditions:
            # Conditions are informational for now — future: enforce dynamically
            pass

        old_state = instance.current_state
        new_state = transition["to_state"]

        # Advance state
        instance.current_state = new_state

        # Check if terminal
        snapshot_states = instance.template_snapshot.get("states", [])
        terminal_names = {s["name"] for s in snapshot_states if s.get("is_terminal", False)}
        if new_state in terminal_names:
            instance.completed_at = datetime.now(timezone.utc)

        # Log the transition
        primary_role = actor_role_names[0] if actor_role_names else ("Superuser" if actor.is_superuser else "User")
        log = WorkflowTransitionLog(
            id=uuid.uuid4(),
            instance_id=instance.id,
            action=action.strip(),
            from_state=old_state,
            to_state=new_state,
            actor_id=actor.id,
            actor_name=f"{actor.first_name} {actor.last_name}",
            actor_role=primary_role,
            notes=notes,
        )
        db.add(log)
        await db.commit()
        await db.refresh(instance)
        return instance

    @staticmethod
    async def build_instance_response(
        db: AsyncSession, instance: WorkflowInstance
    ) -> WorkflowInstanceResponse:
        logs_res = await db.execute(
            select(WorkflowTransitionLog)
            .where(WorkflowTransitionLog.instance_id == instance.id)
            .order_by(WorkflowTransitionLog.created_at.asc())
        )
        logs = logs_res.scalars().all()

        return WorkflowInstanceResponse(
            id=instance.id,
            entity_type=instance.entity_type,
            entity_id=instance.entity_id,
            current_state=instance.current_state,
            template_id=instance.template_id,
            template_version=instance.template_version,
            template_name=instance.template.name if instance.template else None,
            completed_at=instance.completed_at,
            available_transitions=instance.get_available_transitions(),
            transition_logs=[WorkflowTransitionLogResponse.model_validate(l) for l in logs],
            created_at=instance.created_at,
        )
