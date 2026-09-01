import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, func, or_, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

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
    SLAPolicyUpdate,
    SLAPolicyResponse,
    SLATrackerCreate,
    SLATrackerResponse,
    SLATrackerListResponse,
    SLAEscalationLogResponse,
    SLADashboardResponse,
)
from app.modules.iam.models import User, Department, Role, UserRole
from app.modules.notifications.engine import NotificationEngine
from app.core.events import event_broker


def _to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SLAService:

    # ── Policy Management ────────────────────────────────────────

    @staticmethod
    async def create_policy(
        db: AsyncSession, data: SLAPolicyCreate, current_user: User
    ) -> SLAPolicy:
        existing = await db.execute(select(SLAPolicy).where(SLAPolicy.name == data.name.strip()))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"SLA Policy '{data.name}' already exists")

        if data.is_default:
            await db.execute(update(SLAPolicy).values(is_default=False))

        policy = SLAPolicy(
            id=uuid.uuid4(),
            name=data.name.strip(),
            description=data.description,
            priority=data.priority.upper().strip() if data.priority else None,
            work_type=data.work_type.upper().strip() if data.work_type else None,
            department_id=data.department_id,
            asset_category=data.asset_category.strip() if data.asset_category else None,
            risk_level=data.risk_level.upper().strip() if data.risk_level else None,
            response_time_minutes=data.response_time_minutes,
            completion_time_minutes=data.completion_time_minutes,
            warning_threshold_percentage=data.warning_threshold_percentage,
            escalation_rules=data.escalation_rules or [],
            is_active=data.is_active,
            is_default=data.is_default,
        )
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
        return policy

    @staticmethod
    async def list_policies(
        db: AsyncSession,
        priority: Optional[str] = None,
        department_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
    ) -> List[SLAPolicyResponse]:
        query = select(SLAPolicy)
        if priority:
            query = query.where(SLAPolicy.priority == priority.upper().strip())
        if department_id:
            query = query.where(SLAPolicy.department_id == department_id)
        if is_active is not None:
            query = query.where(SLAPolicy.is_active == is_active)

        query = query.order_by(SLAPolicy.priority.asc(), SLAPolicy.name.asc())
        res = await db.execute(query)
        policies = res.scalars().all()

        results = []
        for p in policies:
            resp = SLAPolicyResponse.model_validate(p)
            resp.department_name = p.department.name if p.department else None
            results.append(resp)
        return results

    @staticmethod
    async def match_policy(
        db: AsyncSession,
        priority: Optional[str] = None,
        work_type: Optional[str] = None,
        department_id: Optional[uuid.UUID] = None,
        asset_category: Optional[str] = None,
        risk_level: Optional[str] = None,
    ) -> Optional[SLAPolicy]:
        """
        Calculates highest specificity match score across active SLA policies.
        """
        res = await db.execute(select(SLAPolicy).where(SLAPolicy.is_active == True))
        policies = res.scalars().all()
        if not policies:
            return None

        best_policy = None
        best_score = -1

        norm_pri = priority.upper().strip() if priority else None
        norm_wt = work_type.upper().strip() if work_type else None
        norm_cat = asset_category.lower().strip() if asset_category else None
        norm_risk = risk_level.upper().strip() if risk_level else None

        for p in policies:
            score = 0
            if p.priority:
                if p.priority.upper() == norm_pri:
                    score += 15
                else:
                    continue

            if p.department_id:
                if p.department_id == department_id:
                    score += 20
                else:
                    continue

            if p.work_type:
                if p.work_type.upper() == norm_wt:
                    score += 15
                else:
                    continue

            if p.asset_category:
                if norm_cat and p.asset_category.lower() in norm_cat:
                    score += 10
                else:
                    continue

            if p.risk_level:
                if p.risk_level.upper() == norm_risk:
                    score += 10
                else:
                    continue

            if p.is_default:
                score += 1

            if score > best_score:
                best_score = score
                best_policy = p

        return best_policy

    # ── SLA Tracker Operations ───────────────────────────────────

    @staticmethod
    async def create_tracker(
        db: AsyncSession, data: SLATrackerCreate, current_user: User
    ) -> SLATracker:
        policy = None
        if data.policy_id:
            p_res = await db.execute(select(SLAPolicy).where(SLAPolicy.id == data.policy_id))
            policy = p_res.scalar_one_or_none()

        if not policy:
            policy = await SLAService.match_policy(
                db=db,
                priority=data.priority,
                work_type=data.work_type,
                department_id=data.department_id,
                asset_category=data.asset_category,
                risk_level=data.risk_level,
            )

        resp_mins = policy.response_time_minutes if policy else (15 if data.priority == "CRITICAL" else 60)
        comp_mins = policy.completion_time_minutes if policy else (120 if data.priority == "CRITICAL" else 480)

        now = _utcnow()
        target_resp = now + timedelta(minutes=resp_mins)
        target_comp = now + timedelta(minutes=comp_mins)

        tracker = SLATracker(
            id=uuid.uuid4(),
            policy_id=policy.id if policy else None,
            resource_type=data.resource_type.upper().strip(),
            resource_id=data.resource_id,
            resource_reference=data.resource_reference,
            title=data.title.strip(),
            priority=data.priority.upper().strip() if data.priority else "NORMAL",
            department_id=data.department_id,
            status=SLAStatus.CREATED.value,
            health=SLAHealth.ON_TRACK.value,
            target_response_at=target_resp,
            target_completion_at=target_comp,
            actual_response_at=None,
            actual_completion_at=None,
            total_paused_minutes=0.0,
            current_escalation_level=0,
            history_logs=[{
                "event": "TRACKER_INITIALIZED",
                "timestamp": now.isoformat(),
                "policy_name": policy.name if policy else "Default Dynamic SLA",
                "response_target_mins": resp_mins,
                "completion_target_mins": comp_mins,
            }],
        )
        db.add(tracker)
        await db.commit()
        await db.refresh(tracker)
        return tracker

    @staticmethod
    async def record_response(
        db: AsyncSession, tracker_id: uuid.UUID, current_user: User, notes: Optional[str] = None
    ) -> SLATracker:
        res = await db.execute(select(SLATracker).where(SLATracker.id == tracker_id))
        tracker = res.scalar_one_or_none()
        if not tracker:
            raise HTTPException(status_code=404, detail="SLA tracker not found")

        if tracker.actual_response_at is not None:
            return tracker

        now = _utcnow()
        tracker.actual_response_at = now
        tracker.status = SLAStatus.IN_PROGRESS.value

        target_resp = _to_utc(tracker.target_response_at)
        is_breached = bool(target_resp and now > target_resp)
        if is_breached:
            tracker.health = SLAHealth.BREACHED_RESPONSE.value
            tracker.breach_reason = notes or "Response deadline exceeded"
        else:
            tracker.health = SLAHealth.ON_TRACK.value

        logs = list(tracker.history_logs or [])
        logs.append({
            "event": "RESPONSE_RECORDED",
            "timestamp": now.isoformat(),
            "acknowledged_by": f"{current_user.first_name} {current_user.last_name}",
            "is_breached": is_breached,
            "notes": notes,
        })
        tracker.history_logs = logs

        await db.commit()
        await db.refresh(tracker)
        return tracker

    @staticmethod
    async def pause_tracker(
        db: AsyncSession, tracker_id: uuid.UUID, reason: Optional[str], current_user: User
    ) -> SLATracker:
        res = await db.execute(select(SLATracker).where(SLATracker.id == tracker_id))
        tracker = res.scalar_one_or_none()
        if not tracker:
            raise HTTPException(status_code=404, detail="SLA tracker not found")

        if tracker.status == SLAStatus.PAUSED.value:
            return tracker

        now = _utcnow()
        tracker.paused_at = now
        tracker.status = SLAStatus.PAUSED.value

        logs = list(tracker.history_logs or [])
        logs.append({
            "event": "TRACKER_PAUSED",
            "timestamp": now.isoformat(),
            "paused_by": f"{current_user.first_name} {current_user.last_name}",
            "reason": reason or "Awaiting parts / weather / shift change",
        })
        tracker.history_logs = logs

        await db.commit()
        await db.refresh(tracker)
        return tracker

    @staticmethod
    async def resume_tracker(
        db: AsyncSession, tracker_id: uuid.UUID, notes: Optional[str], current_user: User
    ) -> SLATracker:
        res = await db.execute(select(SLATracker).where(SLATracker.id == tracker_id))
        tracker = res.scalar_one_or_none()
        if not tracker:
            raise HTTPException(status_code=404, detail="SLA tracker not found")

        if tracker.status != SLAStatus.PAUSED.value or not tracker.paused_at:
            return tracker

        now = _utcnow()
        paused_at_utc = _to_utc(tracker.paused_at)
        paused_duration = (now - paused_at_utc).total_seconds() / 60.0
        tracker.total_paused_minutes += paused_duration

        target_resp = _to_utc(tracker.target_response_at)
        if target_resp and target_resp > paused_at_utc:
            tracker.target_response_at = target_resp + timedelta(minutes=paused_duration)

        target_comp = _to_utc(tracker.target_completion_at)
        if target_comp and target_comp > paused_at_utc:
            tracker.target_completion_at = target_comp + timedelta(minutes=paused_duration)

        tracker.paused_at = None
        tracker.status = SLAStatus.IN_PROGRESS.value

        logs = list(tracker.history_logs or [])
        logs.append({
            "event": "TRACKER_RESUMED",
            "timestamp": now.isoformat(),
            "resumed_by": f"{current_user.first_name} {current_user.last_name}",
            "paused_duration_minutes": round(paused_duration, 2),
            "notes": notes,
        })
        tracker.history_logs = logs

        await db.commit()
        await db.refresh(tracker)
        return tracker

    @staticmethod
    async def complete_tracker(
        db: AsyncSession, tracker_id: uuid.UUID, current_user: User, notes: Optional[str] = None
    ) -> SLATracker:
        res = await db.execute(select(SLATracker).where(SLATracker.id == tracker_id))
        tracker = res.scalar_one_or_none()
        if not tracker:
            raise HTTPException(status_code=404, detail="SLA tracker not found")

        now = _utcnow()
        tracker.actual_completion_at = now
        tracker.status = SLAStatus.COMPLETED.value

        target_comp = _to_utc(tracker.target_completion_at)
        is_completion_breached = bool(target_comp and now > target_comp)
        was_response_breached = tracker.health == SLAHealth.BREACHED_RESPONSE.value

        if is_completion_breached:
            tracker.health = SLAHealth.BREACHED_COMPLETION.value
            tracker.breach_reason = notes or "Completion deadline exceeded"
        elif was_response_breached:
            tracker.health = SLAHealth.BREACHED_MET.value
        else:
            tracker.health = SLAHealth.MET.value

        logs = list(tracker.history_logs or [])
        logs.append({
            "event": "TRACKER_COMPLETED",
            "timestamp": now.isoformat(),
            "completed_by": f"{current_user.first_name} {current_user.last_name}",
            "final_health": tracker.health,
            "notes": notes,
        })
        tracker.history_logs = logs

        await db.commit()
        await db.refresh(tracker)
        return tracker

    # ── SLA Health Evaluation & Escalation Engine ────────────────

    @staticmethod
    async def evaluate_trackers_and_escalate(db: AsyncSession) -> int:
        """
        Background worker evaluation loop.
        Computes SLA health, identifies warning/breach thresholds,
        and fires tiered escalations preventing duplicates.
        """
        now = _utcnow()
        escalations_fired = 0

        res = await db.execute(
            select(SLATracker).where(
                SLATracker.status.in_([SLAStatus.CREATED.value, SLAStatus.IN_PROGRESS.value])
            )
        )
        trackers = res.scalars().all()

        for tracker in trackers:
            policy = tracker.policy
            warn_pct = policy.warning_threshold_percentage if policy else 80
            rules = policy.escalation_rules if (policy and policy.escalation_rules) else [
                {"level": 1, "trigger": "RESPONSE_WARNING", "after_percentage": warn_pct, "target_role": "Supervisor", "notify_channel": "PUSH"},
                {"level": 2, "trigger": "RESPONSE_BREACH", "after_percentage": 100, "target_role": "Department Manager", "notify_channel": "PUSH"},
                {"level": 3, "trigger": "COMPLETION_BREACH", "after_percentage": 100, "target_role": "Plant Manager", "notify_channel": "ALL"},
            ]

            created_at_utc = _to_utc(tracker.created_at) or now
            target_resp_utc = _to_utc(tracker.target_response_at)
            target_comp_utc = _to_utc(tracker.target_completion_at)

            # 1. Evaluate Response SLA
            if not tracker.actual_response_at and target_resp_utc:
                if now > target_resp_utc:
                    tracker.health = SLAHealth.BREACHED_RESPONSE.value
                elif now >= (created_at_utc + (target_resp_utc - created_at_utc) * (warn_pct / 100.0)):
                    if tracker.health == SLAHealth.ON_TRACK.value:
                        tracker.health = SLAHealth.AT_RISK.value

            # 2. Evaluate Completion SLA
            if target_comp_utc:
                if now > target_comp_utc:
                    tracker.health = SLAHealth.BREACHED_COMPLETION.value
                elif now >= (created_at_utc + (target_comp_utc - created_at_utc) * (warn_pct / 100.0)):
                    if tracker.health == SLAHealth.ON_TRACK.value:
                        tracker.health = SLAHealth.AT_RISK.value

            # 3. Process Escalation Rules (Preventing duplicate logs)
            for rule in rules:
                level = rule.get("level", 1)
                trigger = rule.get("trigger", "RESPONSE_WARNING")
                target_role = rule.get("target_role")

                should_fire = False
                if trigger == "RESPONSE_WARNING" and tracker.health in (SLAHealth.AT_RISK.value, SLAHealth.BREACHED_RESPONSE.value) and not tracker.actual_response_at:
                    should_fire = True
                elif trigger == "RESPONSE_BREACH" and tracker.health == SLAHealth.BREACHED_RESPONSE.value and not tracker.actual_response_at:
                    should_fire = True
                elif trigger == "COMPLETION_WARNING" and tracker.health in (SLAHealth.AT_RISK.value, SLAHealth.BREACHED_COMPLETION.value):
                    should_fire = True
                elif trigger == "COMPLETION_BREACH" and tracker.health == SLAHealth.BREACHED_COMPLETION.value:
                    should_fire = True

                if should_fire and level > tracker.current_escalation_level:
                    existing_log = await db.execute(
                        select(SLAEscalationLog).where(
                            SLAEscalationLog.tracker_id == tracker.id,
                            SLAEscalationLog.escalation_level == level,
                            SLAEscalationLog.trigger_type == trigger,
                        )
                    )
                    if not existing_log.scalar_one_or_none():
                        msg = f"SLA {trigger.replace('_', ' ')}: '{tracker.title}' [{tracker.resource_reference or 'N/A'}] priority {tracker.priority} requires escalation to {target_role or 'management'}."
                        
                        notified_ids = []
                        if target_role:
                            try:
                                await NotificationEngine.dispatch_to_role(
                                    db=db,
                                    role_name=target_role,
                                    department_id=tracker.department_id,
                                    event_type="SLA_ESCALATION",
                                    title=f"SLA Escalation Level {level}: {tracker.title}",
                                    message=msg,
                                    resource_type=tracker.resource_type,
                                    resource_id=tracker.resource_id,
                                    priority=3 if tracker.priority == "CRITICAL" else 2,
                                )
                            except Exception:
                                pass

                        esc_log = SLAEscalationLog(
                            id=uuid.uuid4(),
                            tracker_id=tracker.id,
                            escalation_level=level,
                            trigger_type=trigger,
                            notified_role=target_role,
                            notified_user_ids=notified_ids,
                            message=msg,
                        )
                        db.add(esc_log)
                        tracker.current_escalation_level = level
                        escalations_fired += 1

                        try:
                            await event_broker.publish(
                                event_type="sla.escalated",
                                payload={
                                    "tracker_id": str(tracker.id),
                                    "level": level,
                                    "trigger": trigger,
                                    "title": tracker.title,
                                    "priority": tracker.priority,
                                },
                                channel="sla",
                            )
                        except Exception:
                            pass

        await db.commit()
        return escalations_fired

    # ── Dashboard & Analytics ────────────────────────────────────

    @staticmethod
    async def get_dashboard(
        db: AsyncSession, department_id: Optional[uuid.UUID] = None
    ) -> SLADashboardResponse:
        query = select(SLATracker)
        if department_id:
            query = query.where(SLATracker.department_id == department_id)

        res = await db.execute(query)
        trackers = res.scalars().all()

        total_active = 0
        on_track = 0
        at_risk = 0
        breached = 0
        critical_open = 0
        total_completed = 0
        met_count = 0

        resp_times = []
        comp_times = []
        recent_breaches = []
        at_risk_list = []

        for t in trackers:
            if t.status in (SLAStatus.CREATED.value, SLAStatus.IN_PROGRESS.value, SLAStatus.PAUSED.value):
                total_active += 1
                if t.priority == SLAPriority.CRITICAL.value:
                    critical_open += 1

                if t.health == SLAHealth.ON_TRACK.value:
                    on_track += 1
                elif t.health == SLAHealth.AT_RISK.value:
                    at_risk += 1
                    at_risk_list.append(t)
                elif "BREACHED" in t.health:
                    breached += 1
                    recent_breaches.append(t)

            if t.status == SLAStatus.COMPLETED.value:
                total_completed += 1
                if t.health in (SLAHealth.MET.value, SLAHealth.BREACHED_MET.value):
                    met_count += 1

            c_at = _to_utc(t.created_at)
            if t.actual_response_at and c_at:
                dur = (_to_utc(t.actual_response_at) - c_at).total_seconds() / 60.0
                resp_times.append(dur)

            if t.actual_completion_at and c_at:
                dur = ((_to_utc(t.actual_completion_at) - c_at).total_seconds() / 60.0) - (t.total_paused_minutes or 0.0)
                comp_times.append(max(0.0, dur))

        compliance_pct = round((met_count / total_completed * 100.0), 1) if total_completed > 0 else 100.0
        avg_resp = round(sum(resp_times) / len(resp_times), 1) if resp_times else 0.0
        avg_comp = round(sum(comp_times) / len(comp_times), 1) if comp_times else 0.0

        def to_list_row(t: SLATracker) -> SLATrackerListResponse:
            return SLATrackerListResponse(
                id=t.id,
                resource_type=t.resource_type,
                resource_id=t.resource_id,
                resource_reference=t.resource_reference,
                title=t.title,
                priority=t.priority,
                status=t.status,
                health=t.health,
                target_response_at=t.target_response_at,
                target_completion_at=t.target_completion_at,
                actual_response_at=t.actual_response_at,
                actual_completion_at=t.actual_completion_at,
                current_escalation_level=t.current_escalation_level,
                department_name=t.department.name if t.department else None,
                policy_name=t.policy.name if t.policy else None,
                created_at=t.created_at,
            )

        return SLADashboardResponse(
            total_active=total_active,
            on_track_count=on_track,
            at_risk_count=at_risk,
            breached_count=breached,
            critical_open_count=critical_open,
            compliance_percentage=compliance_pct,
            avg_response_minutes=avg_resp,
            avg_completion_minutes=avg_comp,
            recent_breaches=[to_list_row(t) for t in recent_breaches[:10]],
            at_risk_trackers=[to_list_row(t) for t in at_risk_list[:10]],
        )

    @staticmethod
    async def get_tracker_detail(
        db: AsyncSession, tracker_id: uuid.UUID, current_user: User
    ) -> SLATrackerResponse:
        res = await db.execute(select(SLATracker).where(SLATracker.id == tracker_id))
        tracker = res.scalar_one_or_none()
        if not tracker:
            raise HTTPException(status_code=404, detail="SLA tracker not found")

        logs_res = await db.execute(
            select(SLAEscalationLog)
            .where(SLAEscalationLog.tracker_id == tracker.id)
            .order_by(SLAEscalationLog.created_at.desc())
        )
        logs = logs_res.scalars().all()

        resp = SLATrackerResponse.model_validate(tracker)
        resp.department_name = tracker.department.name if tracker.department else None
        resp.policy_name = tracker.policy.name if tracker.policy else None
        resp.escalation_logs = [SLAEscalationLogResponse.model_validate(l) for l in logs]
        return resp

    @staticmethod
    async def list_trackers(
        db: AsyncSession,
        department_id: Optional[uuid.UUID] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        health: Optional[str] = None,
        resource_type: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SLATrackerListResponse]:
        query = select(SLATracker)
        if department_id:
            query = query.where(SLATracker.department_id == department_id)
        if priority:
            query = query.where(SLATracker.priority == priority.upper().strip())
        if status:
            query = query.where(SLATracker.status == status.upper().strip())
        if health:
            query = query.where(SLATracker.health == health.upper().strip())
        if resource_type:
            query = query.where(SLATracker.resource_type == resource_type.upper().strip())

        if search_query:
            p = f"%{search_query.strip()}%"
            query = query.where(
                or_(
                    SLATracker.title.ilike(p),
                    SLATracker.resource_reference.ilike(p),
                )
            )

        query = query.order_by(SLATracker.created_at.desc()).limit(limit).offset(offset)
        res = await db.execute(query)
        trackers = res.scalars().all()

        results = []
        for t in trackers:
            results.append(
                SLATrackerListResponse(
                    id=t.id,
                    resource_type=t.resource_type,
                    resource_id=t.resource_id,
                    resource_reference=t.resource_reference,
                    title=t.title,
                    priority=t.priority,
                    status=t.status,
                    health=t.health,
                    target_response_at=t.target_response_at,
                    target_completion_at=t.target_completion_at,
                    actual_response_at=t.actual_response_at,
                    actual_completion_at=t.actual_completion_at,
                    current_escalation_level=t.current_escalation_level,
                    department_name=t.department.name if t.department else None,
                    policy_name=t.policy.name if t.policy else None,
                    created_at=t.created_at,
                )
            )
        return results
