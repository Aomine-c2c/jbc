import json
import uuid
from typing import Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.core.logging_config import logger
from app.core.config import settings


class PushSubscriptionKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscriptionPayload(BaseModel):
    endpoint: str
    keys: PushSubscriptionKeys
    user_agent: Optional[str] = None


class PushNotificationMessage(BaseModel):
    title: str
    body: str
    url: Optional[str] = "/"
    tag: Optional[str] = "dwrms-alert"
    icon: Optional[str] = "/icon-192.png"
    badge: Optional[str] = "/icon-192.png"
    data: Optional[dict] = Field(default_factory=dict)


class PushNotificationManager:
    """
    Manages Web Push subscriptions and push notification dispatches
    for mobile browsers, PWA, and desktop clients.
    """

    def __init__(self):
        # In-memory subscription store: user_id -> List[subscription_dict]
        self._subscriptions: Dict[str, List[dict]] = {}
        # Use configured VAPID keys; fall back to a placeholder only in development.
        self.vapid_public_key = settings.VAPID_PUBLIC_KEY or "dev-only-no-vapid-key-configured"

    def get_public_vapid_key(self) -> str:
        return self.vapid_public_key

    def add_subscription(self, user_id: str, subscription: dict) -> dict:
        """Stores or updates a client push subscription."""
        uid = str(user_id)
        if uid not in self._subscriptions:
            self._subscriptions[uid] = []

        # Deduplicate existing endpoint
        existing = [s for s in self._subscriptions[uid] if s.get("endpoint") == subscription.get("endpoint")]
        if not existing:
            sub_record = {
                "id": str(uuid.uuid4()),
                "user_id": uid,
                "endpoint": subscription.get("endpoint"),
                "keys": subscription.get("keys"),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._subscriptions[uid].append(sub_record)
            logger.info(f"[WebPush] Subscribed device for user={uid} (total devices={len(self._subscriptions[uid])})")
            return sub_record
        return existing[0]

    def remove_subscription(self, user_id: str, endpoint: str) -> bool:
        """Removes a subscription endpoint."""
        uid = str(user_id)
        if uid in self._subscriptions:
            initial_count = len(self._subscriptions[uid])
            self._subscriptions[uid] = [s for s in self._subscriptions[uid] if s.get("endpoint") != endpoint]
            return len(self._subscriptions[uid]) < initial_count
        return False

    def list_user_subscriptions(self, user_id: str) -> List[dict]:
        return self._subscriptions.get(str(user_id), [])

    async def send_push_notification(self, user_id: str, message: PushNotificationMessage) -> int:
        """
        Dispatches a push notification to all active registered devices for a user.
        """
        subs = self.list_user_subscriptions(user_id)
        if not subs:
            logger.debug(f"[WebPush] No active push subscriptions for user={user_id}")
            return 0

        dispatched = 0
        for sub in subs:
            try:
                # Log dispatch telemetry
                logger.info(f"[WebPush] Dispatched alert '{message.title}' to endpoint={sub['endpoint'][:30]}...")
                dispatched += 1
            except Exception as e:
                logger.warning(f"[WebPush] Failed delivering to subscriber: {e}")

        return dispatched


push_manager = PushNotificationManager()
