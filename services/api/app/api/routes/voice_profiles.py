from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, get_runtime
from app.settings import Settings, get_settings
from voiceforge_core.db.enums import AuditEventType, VoiceSampleSource
from voiceforge_core.db.models import User
from voiceforge_core.modules.audit.service import AuditService
from voiceforge_core.modules.voice_profiles.schemas import VoiceProfileCreate, VoiceProfileRead
from voiceforge_core.modules.voice_profiles.service import VoiceProfileService
from voiceforge_core.modules.voice_samples.schemas import VoiceSampleRead
from voiceforge_core.modules.voice_samples.service import VoiceSampleService
from voiceforge_core.runtime import RuntimeContainer

router = APIRouter()


@router.get("", response_model=list[VoiceProfileRead])
def list_voice_profiles(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> list[VoiceProfileRead]:
    profiles = VoiceProfileService.list_for_user(session, current_user.id)
    return [VoiceProfileRead.model_validate(profile) for profile in profiles]


@router.post("", response_model=VoiceProfileRead, status_code=status.HTTP_201_CREATED)
def create_voice_profile(
    payload: VoiceProfileCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> VoiceProfileRead:
    try:
        profile = VoiceProfileService.create_profile(session, current_user, payload)
        AuditService.record(
            session,
            user_id=current_user.id,
            actor_email=current_user.email,
            event_type=AuditEventType.VOICE_PROFILE_CREATED,
            entity_type="voice_profile",
            entity_id=str(profile.id),
            ip_address=request.client.host if request.client else None,
            payload={"preferred_backend": profile.preferred_backend.value},
        )
        session.commit()
        session.refresh(profile)
        return VoiceProfileRead.model_validate(profile)
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{profile_id}", response_model=VoiceProfileRead)
def get_voice_profile(
    profile_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> VoiceProfileRead:
    profile = VoiceProfileService.get_for_user(session, current_user.id, profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice profile not found.")
    return VoiceProfileRead.model_validate(profile)


@router.get("/{profile_id}/samples", response_model=list[VoiceSampleRead])
def list_voice_profile_samples(
    profile_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> list[VoiceSampleRead]:
    profile = VoiceProfileService.get_for_user(session, current_user.id, profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice profile not found.")
    samples = VoiceSampleService.list_for_profile(session, profile.id)
    return [VoiceSampleRead.model_validate(sample) for sample in samples]


@router.post(
    "/{profile_id}/samples",
    response_model=VoiceSampleRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_voice_profile_sample(
    profile_id: UUID,
    request: Request,
    source: VoiceSampleSource = Form(default=VoiceSampleSource.UPLOAD),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    runtime: RuntimeContainer = Depends(get_runtime),
    settings: Settings = Depends(get_settings),
) -> VoiceSampleRead:
    profile = VoiceProfileService.get_for_user(session, current_user.id, profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice profile not found.")

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")
    if len(payload) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {settings.max_upload_mb} MB limit.",
        )

    try:
        sample = VoiceSampleService.create_sample(
            session,
            storage=runtime.storage,
            preprocessor=runtime.audio_preprocessor,
            embedding_extractor=runtime.embedding_extractor,
            profile=profile,
            original_filename=file.filename or "sample.wav",
            content_type=file.content_type,
            payload=payload,
            source=source,
        )
        AuditService.record(
            session,
            user_id=current_user.id,
            actor_email=current_user.email,
            event_type=AuditEventType.VOICE_SAMPLE_UPLOADED,
            entity_type="voice_sample",
            entity_id=str(sample.id),
            ip_address=request.client.host if request.client else None,
            payload={"voice_profile_id": str(profile.id), "source": source.value},
        )
        session.commit()
        session.refresh(sample)
        return VoiceSampleRead.model_validate(sample)
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

