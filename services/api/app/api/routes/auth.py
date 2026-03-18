from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.settings import Settings, get_settings
from voiceforge_core.db.enums import AuditEventType
from voiceforge_core.modules.audit.service import AuditService
from voiceforge_core.modules.auth.schemas import AuthToken, LoginRequest, RegisterRequest
from voiceforge_core.modules.auth.service import AuthService
from voiceforge_core.modules.users.schemas import UserRead

router = APIRouter()


@router.post("/register", response_model=AuthToken, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    request: Request,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthToken:
    try:
        user = AuthService.register_user(
            session,
            email=payload.email,
            display_name=payload.display_name,
            password=payload.password,
        )
        AuditService.record(
            session,
            user_id=user.id,
            actor_email=user.email,
            event_type=AuditEventType.AUTH_REGISTER,
            entity_type="user",
            entity_id=str(user.id),
            ip_address=request.client.host if request.client else None,
            payload={"display_name": user.display_name},
        )
        session.commit()
        token, expires_in = AuthService.create_access_token(user, settings.jwt_secret, settings.access_token_exp_minutes)
        return AuthToken(access_token=token, expires_in_seconds=expires_in)
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/login", response_model=AuthToken)
def login(
    payload: LoginRequest,
    request: Request,
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthToken:
    try:
        user = AuthService.authenticate(session, payload.email, payload.password)
        AuditService.record(
            session,
            user_id=user.id,
            actor_email=user.email,
            event_type=AuditEventType.AUTH_LOGIN,
            entity_type="user",
            entity_id=str(user.id),
            ip_address=request.client.host if request.client else None,
            payload=None,
        )
        session.commit()
        token, expires_in = AuthService.create_access_token(user, settings.jwt_secret, settings.access_token_exp_minutes)
        return AuthToken(access_token=token, expires_in_seconds=expires_in)
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

