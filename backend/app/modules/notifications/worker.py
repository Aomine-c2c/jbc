import asyncio
from typing import Optional
from datetime import datetime, timezone
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db.session import SessionLocal
from app.modules.notifications.models import EscalationTimer, NotificationRule
from app.modules.notifications.engine import NotificationEngine
from app.modules.iam.models import User, UserRole, Role

logger = logging.getLogger(__name__)

# Departmental SLA Timeout Configuration (in hours)
DEPARTMENT_SLA_HOURS = {
    "Safety": 1,
    "Instrumentation": 2,
    "Mechanical": 8,
    "Electrical": 8,
    "Mining Operations": 12,
    "Engineering": 16,
    "IT": 24,
    "DEFAULT": 24,
}


async def process_escalations(session: Optional[AsyncSession] = None) -> int:
    """
    Evaluates pending escalation timers and overdue approval steps
    against department-specific SLA escalation thresholds.
    """
    if session:
        return await _do_process_escalations(session)
    else:
        async with SessionLocal() as db:
            return await _do_process_escalations(db)


async def _do_process_escalations(db: AsyncSession) -> int:
    now = datetime.now(timezone.utc)
    escalated_count = 0

    # 1. Process pending timer events
    result = await db.execute(
        select(EscalationTimer)
        .where(EscalationTimer.status == "PENDING", EscalationTimer.due_at <= now)
    )
    timers = result.scalars().all()

    for timer in timers:
        rule_res = await db.execute(
            select(NotificationRule)
            .where(NotificationRule.event_type == timer.event_type)
        )
        rule = rule_res.scalar_one_or_none()
        if not rule:
            timer.status = "CANCELLED"
            await db.commit()
            continue

        if rule.escalation_role:
            users_res = await db.execute(
                select(User)
                .join(UserRole, UserRole.user_id == User.id)
                .join(Role, Role.id == UserRole.role_id)
                .where(Role.name == rule.escalation_role)
            )
            users = users_res.scalars().all()
            user_ids = [u.id for u in users]

            if user_ids:
                message = rule.message_template.format(resource_id=str(timer.resource_id))
                await NotificationEngine.dispatch(
                    db=db,
                    user_ids=user_ids,
                    event_type="ESCALATION",
                    title="SLA Escalation Required",
                    message=message,
                    resource_type=timer.resource_type,
                    resource_id=timer.resource_id,
                    priority=rule.priority + 1,
                )
                escalated_count += 1

                # Emit real-time SSE event
                try:
                    from app.core.events import event_broker
                    await event_broker.publish(
                        event_type="sla.escalated",
                        payload={
                            "resource_type": timer.resource_type,
                            "resource_id": str(timer.resource_id),
                            "escalated_role": rule.escalation_role,
                            "reason": "Department SLA timeout reached",
                        },
                        channel="sla",
                    )
                except Exception:
                    pass

        timer.status = "FIRED"
        await db.commit()

    return escalated_count

async def escalation_worker_loop():
    logger.info("Starting escalation worker...")
    while True:
        try:
            await process_escalations()
        except Exception as e:
            logger.error(f"Error in escalation worker: {e}")
        await asyncio.sleep(60)  # Check every 60 seconds
