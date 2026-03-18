from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, get_runtime
from app.settings import Settings, get_settings
from voiceforge_core.db.models import User
from voiceforge_core.modules.training_jobs.schemas import TrainingJobCreate, TrainingJobRead
from voiceforge_core.modules.training_jobs.service import TrainingJobService
from voiceforge_core.modules.voice_profiles.service import VoiceProfileService
from voiceforge_core.runtime import RuntimeContainer

router = APIRouter()


@router.get("", response_model=list[TrainingJobRead])
def list_training_jobs(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> list[TrainingJobRead]:
    jobs = TrainingJobService.list_for_user(session, current_user.id)
    return [TrainingJobRead.model_validate(job) for job in jobs]


@router.post("", response_model=TrainingJobRead, status_code=status.HTTP_201_CREATED)
def create_training_job(
    payload: TrainingJobCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    runtime: RuntimeContainer = Depends(get_runtime),
    settings: Settings = Depends(get_settings),
) -> TrainingJobRead:
    profile = VoiceProfileService.get_for_user(session, current_user.id, payload.voice_profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice profile not found.")
    backend = payload.backend or profile.preferred_backend
    job = TrainingJobService.create_job(
        session,
        queue=runtime.queue,
        queue_name=settings.job_queue_name,
        user=current_user,
        profile=profile,
        backend=backend,
        ip_address=request.client.host if request.client else None,
    )
    session.commit()
    session.refresh(job)
    return TrainingJobRead.model_validate(job)

