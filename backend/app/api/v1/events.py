import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, Header, HTTPException, status, Request, Cookie
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt, JWTError

from app.db.session import get_db
from app.core.config import settings
from app.core.events import event_broker
from app.modules.iam.models import User

events_router = APIRouter(prefix="/api/v1/events", tags=["Real-time Events"])


async def authenticate_sse_user(
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Query(default=None),
    authorization: Optional[str] = Header(default=None),
    access_token: Optional[str] = Cookie(default=None, alias="dwrms_access_token"),
) -> User:
    """
    Authenticates an SSE subscriber with a bearer token, legacy query token,
    or the secure browser authentication cookie.
    """
    jwt_token = None
    if authorization and authorization.startswith("Bearer "):
        jwt_token = authorization.split(" ", 1)[1]
    elif token:
        jwt_token = token
    elif access_token:
        jwt_token = access_token

    if not jwt_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required for live event stream.",
        )

    try:
        payload = jwt.decode(jwt_token, settings.get_secret_key, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

        result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found")
        return user
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


@events_router.get("/stream")
async def live_event_stream(
    request: Request,
    current_user: User = Depends(authenticate_sse_user),
):
    """
    Establishes an authenticated Server-Sent Events (SSE) stream for real-time
    Job Card lifecycle updates, approval dispatches, and SLA escalation alerts.
    """
    sub_id, queue = await event_broker.register_subscriber(
        user_id=str(current_user.id),
        department_id=str(current_user.department_id) if current_user.department_id else None,
        is_admin=current_user.is_superuser,
    )

    return StreamingResponse(
        event_broker.event_generator(sub_id, queue, heartbeat_interval=15),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream",
        },
    )


@events_router.post("/broadcast")
async def broadcast_event(
    event_type: str = Query(...),
    message: str = Query("Test broadcast event"),
    department_id: Optional[str] = Query(None),
    current_user: User = Depends(authenticate_sse_user),
):
    """Admin utility endpoint to test or trigger manual event broadcasts."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required.")

    event = await event_broker.publish(
        event_type=event_type,
        payload={"message": message, "sender": current_user.email},
        department_id=department_id,
        channel="broadcast",
    )
    return {"status": "dispatched", "event_id": event.id, "event_type": event.event_type}
