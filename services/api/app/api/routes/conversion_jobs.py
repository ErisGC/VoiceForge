from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, get_runtime
from app.settings import Settings, get_settings
from voiceforge_core.db.enums import AuditEventType, ConversionMode, EngineBackend
from voiceforge_core.db.models import User
from voiceforge_core.modules.audit.service import AuditService
from voiceforge_core.modules.conversion_jobs.schemas import ConversionJobRead, ConvertedAudioRead
from voiceforge_core.modules.conversion_jobs.service import ConversionJobService
from voiceforge_core.modules.voice_profiles.service import VoiceProfileService
from voiceforge_core.runtime import RuntimeContainer

router = APIRouter()


@router.get("", response_model=list[ConversionJobRead])
def list_conversion_jobs(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> list[ConversionJobRead]:
    jobs = ConversionJobService.list_for_user(session, current_user.id)
    return [ConversionJobRead.model_validate(job) for job in jobs]


@router.get("/{job_id}", response_model=ConversionJobRead)
def get_conversion_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> ConversionJobRead:
    job = ConversionJobService.get_for_user(session, current_user.id, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversion job not found.")
    return ConversionJobRead.model_validate(job)


@router.get("/{job_id}/outputs", response_model=list[ConvertedAudioRead])
def get_conversion_outputs(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> list[ConvertedAudioRead]:
    job = ConversionJobService.get_for_user(session, current_user.id, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversion job not found.")
    return [ConvertedAudioRead.model_validate(output) for output in job.converted_audios]


@router.get("/{job_id}/outputs/{output_id}/download")
def download_converted_output(
    job_id: UUID,
    output_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    runtime: RuntimeContainer = Depends(get_runtime),
):
    job = ConversionJobService.get_for_user(session, current_user.id, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversion job not found.")
    output = next((item for item in job.converted_audios if item.id == output_id), None)
    if output is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Converted output not found.")
    file_path = runtime.storage.resolve_path(output.storage_key)
    media_type = "audio/wav" if output.format.lower() == "wav" else "application/octet-stream"
    return FileResponse(path=file_path, filename=file_path.name, media_type=media_type)


@router.post("", response_model=ConversionJobRead, status_code=status.HTTP_201_CREATED)
async def create_conversion_job(
    request: Request,
    voice_profile_id: UUID = Form(...),
    mode: ConversionMode = Form(default=ConversionMode.STUDIO),
    backend: str | None = Form(default=None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    runtime: RuntimeContainer = Depends(get_runtime),
    settings: Settings = Depends(get_settings),
) -> ConversionJobRead:
    profile = VoiceProfileService.get_for_user(session, current_user.id, voice_profile_id)
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

    selected_backend = profile.preferred_backend if backend is None else EngineBackend(backend)
    try:
        job = ConversionJobService.create_job(
            session,
            storage=runtime.storage,
            preprocessor=runtime.audio_preprocessor,
            queue=runtime.queue,
            queue_name=settings.job_queue_name,
            user=current_user,
            profile=profile,
            backend=selected_backend,
            mode=mode,
            original_filename=file.filename or "conversion-input.wav",
            content_type=file.content_type,
            payload=payload,
            ip_address=request.client.host if request.client else None,
        )
        session.commit()
        session.refresh(job)
        return ConversionJobRead.model_validate(job)
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{job_id}/process-now", response_model=ConversionJobRead)
def process_conversion_job_now(
    job_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    runtime: RuntimeContainer = Depends(get_runtime),
) -> ConversionJobRead:
    job = ConversionJobService.get_for_user(session, current_user.id, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversion job not found.")
    if not ConversionJobService.can_process(job):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Conversion job is not processable from state '{job.status.value}'.",
        )

    try:
        AuditService.record(
            session,
            user_id=current_user.id,
            actor_email=current_user.email,
            event_type=AuditEventType.CONVERSION_JOB_STARTED,
            entity_type="conversion_job",
            entity_id=str(job.id),
            ip_address=request.client.host if request.client else None,
            payload={"voice_profile_id": str(job.voice_profile_id), "mode": "inline"},
        )
        ConversionJobService.process_job(
            session,
            storage=runtime.storage,
            registry=runtime.model_registry,
            preprocessor=runtime.audio_preprocessor,
            conversion_job_id=job.id,
        )
        AuditService.record(
            session,
            user_id=current_user.id,
            actor_email=current_user.email,
            event_type=AuditEventType.CONVERSION_JOB_COMPLETED,
            entity_type="conversion_job",
            entity_id=str(job.id),
            ip_address=request.client.host if request.client else None,
            payload={"voice_profile_id": str(job.voice_profile_id), "mode": "inline"},
        )
        session.commit()
        session.refresh(job)
        return ConversionJobRead.model_validate(job)
    except Exception as exc:
        session.rollback()
        failed_job = ConversionJobService.get_for_user(session, current_user.id, job_id)
        failure_payload = ConversionJobService.failure_payload(exc)
        if failed_job is not None:
            ConversionJobService.mark_failed(
                session,
                job=failed_job,
                error_message=str(exc),
                error_category=failure_payload["error_category"],
                profiling_json=failure_payload.get("profiling"),
            )
            AuditService.record(
                session,
                user_id=current_user.id,
                actor_email=current_user.email,
                event_type=AuditEventType.CONVERSION_JOB_FAILED,
                entity_type="conversion_job",
                entity_id=str(failed_job.id),
                ip_address=request.client.host if request.client else None,
                payload={**failure_payload, "mode": "inline"},
            )
            session.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"[{failure_payload['error_category']}] {exc}",
        ) from exc
