from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from voiceforge_core.db.enums import AuditEventType
from voiceforge_core.db.models import AuditLog


class AuditService:
    @staticmethod
    def record(
        session: Session,
        *,
        user_id: UUID | None,
        actor_email: str | None,
        event_type: AuditEventType,
        entity_type: str,
        entity_id: str,
        ip_address: str | None,
        payload: dict | None = None,
    ) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            actor_email=actor_email,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ip_address,
            payload_json=payload,
            created_at=datetime.now(timezone.utc),
        )
        session.add(log)
        session.flush()
        return log

    @staticmethod
    def list_for_user(session: Session, user_id: UUID | None, limit: int = 100) -> list[AuditLog]:
        statement = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        if user_id is not None:
            statement = statement.where(AuditLog.user_id == user_id)
        return list(session.scalars(statement))

