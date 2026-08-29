import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.modules.notifications.models import Notification, EscalationTimer
from app.modules.notifications.schemas import NotificationResponse

class WebSocketManager:
    def __init__(self):
        # Maps user_id to a list of active WebSockets
        self.active_connections: Dict[uuid.UUID, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: uuid.UUID):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: uuid.UUID):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: uuid.UUID):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    pass

manager = WebSocketManager()

class NotificationEngine:
    @staticmethod
    async def dispatch(
        db: AsyncSession,
        user_ids: List[uuid.UUID],
        event_type: str,
        title: str,
        message: str,
        resource_type: str,
        resource_id: uuid.UUID,
        priority: int = 0
    ):
        notifications_to_send = []
        for uid in user_ids:
            notif = Notification(
                user_id=uid,
                type=event_type,
                title=title,
                message=message,
                resource_type=resource_type,
                resource_id=resource_id,
                priority=priority
            )
            db.add(notif)
            notifications_to_send.append(notif)

        await db.commit()
        
        # Send WS updates
        for notif in notifications_to_send:
            await db.refresh(notif)
            schema = NotificationResponse.model_validate(notif)
            payload = json.dumps({"type": "NEW_NOTIFICATION", "payload": schema.model_dump(mode='json')})
            await manager.send_personal_message(payload, notif.user_id)

    @staticmethod
    async def dispatch_to_role(
        db: AsyncSession,
        role_name: str,
        department_id: Optional[uuid.UUID],
        event_type: str,
        title: str,
        message: str,
        resource_type: str,
        resource_id: uuid.UUID,
        priority: int = 0
    ):
        from app.modules.iam.models import User, UserRole, Role
        
        query = select(User).join(UserRole, UserRole.user_id == User.id).join(Role, Role.id == UserRole.role_id).where(Role.name == role_name)
        if department_id:
            query = query.where(User.department_id == department_id)
            
        result = await db.execute(query)
        users = result.scalars().all()
        user_ids = [u.id for u in users]
        
        if user_ids:
            await NotificationEngine.dispatch(
                db=db,
                user_ids=user_ids,
                event_type=event_type,
                title=title,
                message=message,
                resource_type=resource_type,
                resource_id=resource_id,
                priority=priority
            )
            
    @staticmethod
    async def schedule_escalation(
        db: AsyncSession,
        resource_type: str,
        resource_id: uuid.UUID,
        event_type: str,
        delay_hours: int
    ):
        due = datetime.now(timezone.utc) + timedelta(hours=delay_hours)
        timer = EscalationTimer(
            resource_type=resource_type,
            resource_id=resource_id,
            event_type=event_type,
            due_at=due,
            status="PENDING"
        )
        db.add(timer)
        await db.commit()

    @staticmethod
    async def cancel_escalation(
        db: AsyncSession,
        resource_type: str,
        resource_id: uuid.UUID,
        event_type: str
    ):
        await db.execute(
            update(EscalationTimer)
            .where(
                EscalationTimer.resource_type == resource_type,
                EscalationTimer.resource_id == resource_id,
                EscalationTimer.event_type == event_type,
                EscalationTimer.status == "PENDING"
            )
            .values(status="CANCELLED")
        )
        await db.commit()
