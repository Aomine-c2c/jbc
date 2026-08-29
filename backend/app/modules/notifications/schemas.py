import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class NotificationBase(BaseModel):
    title: str
    message: str
    type: str
    resource_type: str
    resource_id: uuid.UUID
    priority: int = 0

class NotificationResponse(NotificationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    is_read: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class NotificationList(BaseModel):
    total_unread: int
    items: List[NotificationResponse]
