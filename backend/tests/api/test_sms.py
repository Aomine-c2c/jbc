import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.common.sms_provider import MockSMSProvider, get_sms_provider
from app.modules.common.models import SMSMessage
from app.modules.common.notifications import NotificationService
from datetime import datetime, timedelta
import asyncio

@pytest.mark.asyncio
async def test_mock_sms_provider():
    provider = get_sms_provider()
    assert isinstance(provider, MockSMSProvider)
    
    # Run mock multiple times to ensure it generally returns True but doesn't crash on random False
    successes = 0
    for _ in range(20):
        if provider.send_sms("+15551234567", "Test"):
            successes += 1
    
    assert successes > 0

@pytest.mark.asyncio
async def test_phone_validation():
    assert NotificationService.validate_phone("+15551234567") == True
    assert NotificationService.validate_phone("15551234567") == True
    assert NotificationService.validate_phone("invalid") == False
    assert NotificationService.validate_phone("") == False

@pytest.mark.asyncio
async def test_duplicate_sms_prevention(db: AsyncSession):
    # This requires an actual DB session, assuming pytest fixtures provide `db`
    # We will simulate the queue logic
    test_phone = "+15559998888"
    test_event = "test.event"
    test_entity = uuid.uuid4()
    
    # 1. First trigger should succeed and queue
    queued_1 = await NotificationService.trigger_sms(
        db=db,
        recipient_phone=test_phone,
        content="First Message",
        event_name=test_event,
        entity_id=test_entity
    )
    assert queued_1 == True
    
    # 2. Second trigger immediately after should be blocked by duplicate prevention
    queued_2 = await NotificationService.trigger_sms(
        db=db,
        recipient_phone=test_phone,
        content="Second Message",
        event_name=test_event,
        entity_id=test_entity
    )
    assert queued_2 == False

@pytest.mark.asyncio
async def test_celery_task_execution_state_transitions(db: AsyncSession):
    """
    Since we cannot natively run Celery inside an async pytest without complex mocking,
    we will simulate the async inner function `_send_sms_async` directly to verify 
    the state changes from QUEUED to SENT/FAILED/RETRY.
    """
    from app.worker import _send_sms_coro
    from unittest.mock import patch, AsyncMock, MagicMock
    import contextlib

    sms = SMSMessage(
        recipient_phone="+15550001111",
        content="Test Task",
        provider_status="QUEUED"
    )
    db.add(sms)
    await db.commit()
    await db.refresh(sms)

    @contextlib.asynccontextmanager
    async def mock_session():
        yield db

    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()

    with patch("app.worker.create_async_engine", return_value=mock_engine), \
         patch("app.worker.async_sessionmaker", return_value=mock_session):
        await _send_sms_coro(None, str(sms.id))
        
    await db.refresh(sms)
    assert sms.provider_status == "SENT"
    assert sms.sent_at is not None
    assert sms.error_message is None
