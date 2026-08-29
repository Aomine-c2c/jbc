import os
import uuid
import time
from datetime import datetime, timezone
from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.logging_config import logger
from app.modules.common.models import SMSMessage
from app.modules.common.sms_provider import get_sms_provider


@shared_task(name="app.worker._send_sms_async", bind=True, max_retries=3, default_retry_delay=60)
def _send_sms_async(self, sms_id: str):
    """Celery task to dispatch an SMS notification."""
    import asyncio
    return asyncio.run(_send_sms_coro(self, sms_id))


async def _send_sms_coro(task_instance, sms_id: str):
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        result = await session.execute(
            select(SMSMessage).where(SMSMessage.id == uuid.UUID(sms_id))
        )
        sms = result.scalar_one_or_none()
        if not sms:
            return

        provider = get_sms_provider()
        try:
            success = provider.send_sms(sms.recipient_phone, sms.content)
            if success:
                sms.provider_status = "SENT"
                sms.sent_at = datetime.now(timezone.utc)
            else:
                sms.provider_status = "FAILED"
                sms.error_message = "Provider returned failure"
        except Exception as e:
            sms.provider_status = "FAILED"
            sms.error_message = str(e)
            raise task_instance.retry(exc=e)

        await session.commit()
    await engine.dispose()


@shared_task(name="app.worker.check_and_escalate_overdue_approvals")
def check_and_escalate_overdue_approvals():
    """Scheduled task to evaluate pending approvals against SLA escalation windows."""
    import asyncio

    async def _sweep():
        from app.db.session import SessionLocal
        from app.modules.notifications.worker import process_escalations
        async with SessionLocal() as session:
            try:
                count = await process_escalations(session)
                if count > 0:
                    logger.info(f"Escalation sweep completed: {count} approvals escalated.")
            except Exception as e:
                logger.error(f"Error during escalation sweep: {e}")

    asyncio.run(_sweep())


@shared_task(name="app.worker.purge_temp_storage")
def purge_temp_storage():
    """Scheduled task to clean temporary uploads and probe artifacts older than 24 hours."""
    from pathlib import Path
    temp_dir = Path(settings.STORAGE_PATH) / "temp"
    if not temp_dir.exists():
        return

    now = time.time()
    count = 0
    for item in temp_dir.iterdir():
        if item.is_file():
            # Delete files older than 24h (86400s)
            if now - item.stat().st_mtime > 86400:
                try:
                    item.unlink()
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to remove stale temp file {item}: {e}")
    if count > 0:
        logger.info(f"Purged {count} temporary files from {temp_dir}")


@shared_task(name="app.worker.heartbeat_task")
def heartbeat_task():
    """Periodic worker heartbeat verification."""
    logger.info(f"DWRMS Celery Worker Heartbeat OK at {datetime.now(timezone.utc).isoformat()}")
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
