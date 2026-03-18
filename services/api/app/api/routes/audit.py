from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from voiceforge_core.db.models import User
from voiceforge_core.modules.audit.schemas import AuditLogRead
from voiceforge_core.modules.audit.service import AuditService

router = APIRouter()


@router.get("", response_model=list[AuditLogRead])
def list_audit_logs(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> list[AuditLogRead]:
    logs = AuditService.list_for_user(session, current_user.id)
    return [AuditLogRead.model_validate(log) for log in logs]

