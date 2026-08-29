import re
import uuid
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.common.models import SMSMessage
from app.modules.common.sms_provider import get_sms_provider


class NotificationService:
    """Handles SMS notifications and duplicate prevention."""

    PHONE_PATTERN = re.compile(r"^\+?[0-9]{7,15}$")

    @staticmethod
    def validate_phone(phone: str) -> bool:
        if not phone:
            return False
        cleaned = phone.replace("+", "").replace("*", "").replace(" ", "")
        return bool(NotificationService.PHONE_PATTERN.match(cleaned))

    @staticmethod
    async def trigger_sms(
        db: AsyncSession,
        recipient_phone: str,
        content: str,
        event_name: str,
        entity_id: uuid.UUID,
    ) -> bool:
        """Queue an SMS message with duplicate prevention within a time window."""
        if not NotificationService.validate_phone(recipient_phone):
            return False

        # Check for duplicate within last 5 minutes
        five_min_ago = datetime.utcnow() - timedelta(minutes=5)
        dup_stmt = select(SMSMessage).where(
            SMSMessage.recipient_phone == recipient_phone,
            SMSMessage.provider_status.in_(["QUEUED", "SENT"]),
            SMSMessage.created_at >= five_min_ago,
        )
        result = await db.execute(dup_stmt)
        if result.scalars().first():
            return False

        sms = SMSMessage(
            recipient_phone=recipient_phone,
            content=content,
            provider_status="QUEUED",
        )
        db.add(sms)
        await db.commit()
        await db.refresh(sms)
        return True
