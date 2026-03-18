from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from voiceforge_core.db.enums import AuditEventType


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None
    actor_email: str | None
    event_type: AuditEventType
    entity_type: str
    entity_id: str
    ip_address: str | None
    payload_json: dict | None
    created_at: datetime

