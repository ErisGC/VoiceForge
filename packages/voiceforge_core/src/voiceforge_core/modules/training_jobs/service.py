from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from voiceforge_core.db.enums import AuditEventType, EngineBackend, JobStatus, VoiceProfileStatus
from voiceforge_core.db.models import TrainingJob, User, VoiceProfile
from voiceforge_core.jobs.queue import RedisJobQueue
from voiceforge_core.modules.audit.service import AuditService
from voiceforge_core.storage.base import StorageProvider


class TrainingOrchestrator(ABC):
    @abstractmethod
    def prepare_artifact(self, profile: VoiceProfile) -> tuple[bytes, dict]:
        raise NotImplementedError


class ManifestTrainingOrchestrator(TrainingOrchestrator):
    def prepare_artifact(self, profile: VoiceProfile) -> tuple[bytes, dict]:
        manifest = {
            "voice_profile_id": str(profile.id),
            "backend": profile.preferred_backend.value,
            "readiness_score": profile.readiness_score,
            "clip_count": profile.clip_count,
            "dataset_quality": {
                "total_duration_seconds": profile.total_duration_seconds,
                "noise_score": profile.noise_score,
                "diversity_score": profile.diversity_score,
                "sample_rate": profile.sample_rate,
            },
            "prepared_at": datetime.now(timezone.utc).isoformat(),
            "notes": "Replace manifest-only training with backend-specific orchestration for Seed-VC or RVC.",
        }
        return json.dumps(manifest, indent=2).encode("utf-8"), manifest


class TrainingJobService:
    @staticmethod
    def create_job(
        session: Session,
        *,
        queue: RedisJobQueue,
        queue_name: str,
        user: User,
        profile: VoiceProfile,
        backend: EngineBackend,
        ip_address: str | None,
    ) -> TrainingJob:
        job = TrainingJob(
            voice_profile_id=profile.id,
            requested_by_user_id=user.id,
            backend=backend,
            status=JobStatus.QUEUED,
            queue_name=queue_name,
        )
        session.add(job)
        profile.status = VoiceProfileStatus.TRAINING
        session.flush()

        queue.enqueue("training_requested", {"training_job_id": str(job.id)})
        AuditService.record(
            session,
            user_id=user.id,
            actor_email=user.email,
            event_type=AuditEventType.TRAINING_JOB_CREATED,
            entity_type="training_job",
            entity_id=str(job.id),
            ip_address=ip_address,
            payload={"voice_profile_id": str(profile.id), "backend": backend.value},
        )
        return job

    @staticmethod
    def list_for_user(session: Session, user_id: UUID) -> list[TrainingJob]:
        statement = (
            select(TrainingJob)
            .join(VoiceProfile, VoiceProfile.id == TrainingJob.voice_profile_id)
            .where(VoiceProfile.user_id == user_id)
            .order_by(TrainingJob.created_at.desc())
        )
        return list(session.scalars(statement))

    @staticmethod
    def process_job(
        session: Session,
        *,
        storage: StorageProvider,
        orchestrator: TrainingOrchestrator,
        training_job_id: UUID,
    ) -> TrainingJob:
        job = session.get(TrainingJob, training_job_id)
        if job is None:
            raise ValueError(f"Training job not found: {training_job_id}")

        profile = session.get(VoiceProfile, job.voice_profile_id)
        if profile is None:
            raise ValueError(f"Voice profile not found for job: {training_job_id}")

        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        session.flush()

        artifact_bytes, manifest = orchestrator.prepare_artifact(profile)
        artifact_key = f"training/{profile.user_id}/{profile.id}/{job.id}.json"
        storage.put_bytes(artifact_key, artifact_bytes, "application/json")

        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now(timezone.utc)
        job.metrics_json = manifest
        job.model_artifact_storage_key = artifact_key
        profile.status = VoiceProfileStatus.ACTIVE if profile.readiness_score >= 60 else VoiceProfileStatus.READY
        session.flush()
        return job

