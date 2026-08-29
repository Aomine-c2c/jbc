import asyncio
import json
import uuid
from typing import Dict, Set, Optional, AsyncGenerator
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

from app.core.logging_config import logger


@dataclass
class LiveEvent:
    id: str
    event_type: str
    payload: dict
    timestamp: str
    department_id: Optional[str] = None
    user_id: Optional[str] = None
    channel: str = "global"

    def to_sse_message(self) -> str:
        """Formats the event into standard Server-Sent Events (SSE) format."""
        data_json = json.dumps({
            "id": self.id,
            "type": self.event_type,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "department_id": self.department_id,
            "user_id": self.user_id,
            "channel": self.channel,
        })
        return f"id: {self.id}\nevent: {self.event_type}\ndata: {data_json}\n\n"


class EventBroker:
    """
    High-performance asynchronous pub/sub event broker for live telemetry,
    approval dispatches, Job Card state transitions, and SLA warnings.
    """

    def __init__(self):
        # Map subscriber_id -> asyncio.Queue
        self._subscribers: Dict[str, asyncio.Queue] = {}
        # Map subscriber_id -> (user_id, department_id, is_admin)
        self._subscriber_meta: Dict[str, dict] = {}
        self._lock = asyncio.Lock()

    async def register_subscriber(
        self,
        user_id: str,
        department_id: Optional[str] = None,
        is_admin: bool = False,
    ) -> tuple[str, asyncio.Queue]:
        """Registers a new client stream connection and returns a dedicated queue."""
        sub_id = str(uuid.uuid4())
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)

        async with self._lock:
            self._subscribers[sub_id] = queue
            self._subscriber_meta[sub_id] = {
                "user_id": str(user_id),
                "department_id": str(department_id) if department_id else None,
                "is_admin": is_admin,
                "connected_at": datetime.now(timezone.utc).isoformat(),
            }

        logger.debug(f"[SSE Broker] Client {sub_id} subscribed for user={user_id} dept={department_id}")
        return sub_id, queue

    async def remove_subscriber(self, sub_id: str) -> None:
        """Cleans up disconnected client subscriber resources."""
        async with self._lock:
            if sub_id in self._subscribers:
                del self._subscribers[sub_id]
            if sub_id in self._subscriber_meta:
                del self._subscriber_meta[sub_id]
        logger.debug(f"[SSE Broker] Client {sub_id} unsubscribed.")

    async def publish(
        self,
        event_type: str,
        payload: dict,
        department_id: Optional[str] = None,
        user_id: Optional[str] = None,
        channel: str = "global",
    ) -> LiveEvent:
        """
        Publishes a real-time event to all targeted active subscribers.
        Filters appropriately by targeted user ID or department ID.
        """
        event = LiveEvent(
            id=str(uuid.uuid4()),
            event_type=event_type,
            payload=payload,
            timestamp=datetime.now(timezone.utc).isoformat(),
            department_id=str(department_id) if department_id else None,
            user_id=str(user_id) if user_id else None,
            channel=channel,
        )

        async with self._lock:
            active_subscribers = list(self._subscribers.items())

        dispatch_count = 0
        for sub_id, queue in active_subscribers:
            meta = self._subscriber_meta.get(sub_id, {})
            # Check target filtering
            if event.user_id and meta.get("user_id") != event.user_id:
                # Unless subscriber is admin, skip non-matching users
                if not meta.get("is_admin"):
                    continue

            if event.department_id and meta.get("department_id") != event.department_id:
                # Unless subscriber is admin or global event, skip non-matching depts
                if not meta.get("is_admin") and event.channel != "global":
                    continue

            try:
                queue.put_nowait(event)
                dispatch_count += 1
            except asyncio.QueueFull:
                logger.warning(f"[SSE Broker] Queue full for subscriber {sub_id}; dropping oldest event.")
                try:
                    queue.get_nowait()
                    queue.put_nowait(event)
                except Exception:
                    pass

        logger.debug(f"[SSE Broker] Event '{event_type}' dispatched to {dispatch_count} active subscriber(s).")
        return event

    async def event_generator(
        self,
        sub_id: str,
        queue: asyncio.Queue,
        heartbeat_interval: int = 15,
    ) -> AsyncGenerator[str, None]:
        """
        Asynchronous generator yielding SSE formatted strings to the client stream.
        Periodically emits comments (: heartbeat) to keep connection alive.
        """
        try:
            # Yield initial connection confirmation event
            welcome = LiveEvent(
                id=str(uuid.uuid4()),
                event_type="connection.ready",
                payload={"subscriber_id": sub_id, "status": "CONNECTED"},
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            yield welcome.to_sse_message()

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=heartbeat_interval)
                    yield event.to_sse_message()
                except asyncio.TimeoutError:
                    # Send periodic keep-alive ping
                    yield f": heartbeat {datetime.now(timezone.utc).isoformat()}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            await self.remove_subscriber(sub_id)


# Global singleton instance
event_broker = EventBroker()
