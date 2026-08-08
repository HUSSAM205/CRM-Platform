import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogRead(BaseModel):
    id: uuid.UUID
    actor_id: uuid.UUID | None
    actor_name: str
    action: str
    resource_type: str
    resource_id: uuid.UUID | None
    extra: dict[str, Any]
    ip_address: str | None
    created_at: datetime
