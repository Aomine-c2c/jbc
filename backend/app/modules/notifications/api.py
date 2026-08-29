import uuid
from typing import List
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.db.session import get_db
from app.modules.iam.models import User
from app.modules.notifications.models import Notification
from app.modules.notifications.schemas import NotificationResponse, NotificationList
from app.modules.notifications.engine import manager

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])

def _get_current_user():
    from app.main import get_current_user as _gcu
    return _gcu

@router.get("", response_model=NotificationList)
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user())
):
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    items = result.scalars().all()
    
    unread_result = await db.execute(
        select(func.count(Notification.id))
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
    )
    unread = unread_result.scalar() or 0

    return NotificationList(
        total_unread=unread,
        items=[NotificationResponse.model_validate(n) for n in items]
    )

@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user())
):
    result = await db.execute(
        select(Notification)
        .where(Notification.id == notification_id, Notification.user_id == current_user.id)
    )
    notif = result.scalar_one_or_none()
    if not notif:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notif.is_read = True
    await db.commit()
    await db.refresh(notif)
    return NotificationResponse.model_validate(notif)

@router.put("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user())
):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
        .values(is_read=True)
    )
    await db.commit()
    return {"status": "ok"}

async def _authenticate_websocket(websocket: WebSocket, token: str | None) -> uuid.UUID | None:
    from jose import jwt
    from app.core.config import settings
    jwt_token = token or websocket.cookies.get("dwrms_access_token")
    if not jwt_token:
        return None
    try:
        payload = jwt.decode(jwt_token, settings.get_secret_key, algorithms=[settings.ALGORITHM])
        subject = payload.get("sub")
        return uuid.UUID(subject) if subject else None
    except Exception:
        return None


async def _notification_websocket(websocket: WebSocket, token: str | None = None):
    user_id = await _authenticate_websocket(websocket, token)
    if not user_id:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "PING":
                await websocket.send_text("PONG")
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)


@router.websocket("/ws")
async def websocket_cookie_endpoint(websocket: WebSocket):
    await _notification_websocket(websocket)


@router.websocket("/ws/{token}")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
):
    """Legacy bearer-token WebSocket endpoint for non-browser clients."""
    await _notification_websocket(websocket, token)


# ── Web Push Notifications Endpoints ─────────────────────────

from app.modules.notifications.push import (
    push_manager,
    PushSubscriptionPayload,
    PushNotificationMessage,
)


@router.get("/push/vapid-public-key")
async def get_vapid_public_key():
    """Returns the application server VAPID public key for Web Push subscriptions."""
    return {"vapid_public_key": push_manager.get_public_vapid_key()}


@router.post("/push/subscribe")
async def subscribe_push_notifications(
    payload: PushSubscriptionPayload,
    current_user: User = Depends(_get_current_user()),
):
    """Registers a browser or PWA push subscription for the authenticated user."""
    subscription = push_manager.add_subscription(
        user_id=str(current_user.id),
        subscription=payload.model_dump(),
    )
    return {"status": "subscribed", "subscription": subscription}


@router.post("/push/unsubscribe")
async def unsubscribe_push_notifications(
    payload: PushSubscriptionPayload,
    current_user: User = Depends(_get_current_user()),
):
    """Unregisters a push subscription endpoint."""
    removed = push_manager.remove_subscription(
        user_id=str(current_user.id),
        endpoint=payload.endpoint,
    )
    return {"status": "unsubscribed" if removed else "not_found"}


@router.post("/push/test")
async def send_test_push_notification(
    current_user: User = Depends(_get_current_user()),
):
    """Sends a test push notification to all active devices of the authenticated user."""
    count = await push_manager.send_push_notification(
        user_id=str(current_user.id),
        message=PushNotificationMessage(
            title="DWRMS System Test",
            body="Push notification transport verified successfully.",
            url="/dashboard",
        ),
    )
    return {"status": "dispatched", "devices_notified": count}
