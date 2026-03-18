from __future__ import annotations

import json
import logging
import secrets
import time
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from voiceforge_core.audio.contracts import AudioPreprocessor
from voiceforge_core.audio.pipeline import AudioProcessingError
from voiceforge_core.db.enums import AuditEventType, EngineBackend, JobStatus, ProcessingStatus
from voiceforge_core.db.models import ConversionJob, ConvertedAudio, User, VoiceProfile, VoiceSample
from voiceforge_core.inference.contracts import ConversionRequest, ReferenceAudioCandidate
from voiceforge_core.inference.model_registry import ModelRegistry
from voiceforge_core.inference.seed_vc import (
    INFERENCE_FAILED,
    INVALID_REFERENCE,
    PREPROCESS_FAILED,
    RUNTIME_MISSING,
    STORAGE_FAILED,
    SeedVCError,
)
from voiceforge_core.jobs.queue import RedisJobQueue
from voiceforge_core.modules.audit.service import AuditService
from voiceforge_core.modules.feature_caches.service import VoiceProfileFeatureCacheService
from voiceforge_core.modules.storage.service import DEFAULT_AUDIO_CONTENT_TYPE, validate_audio_filename
from voiceforge_core.storage.base import StorageProvider

logger = logging.getLogger("voiceforge.conversion_jobs")


class ConversionJobService:
    @staticmethod
    def list_for_user(session: Session, user_id: UUID) -> list[ConversionJob]:
        statement = (
            select(ConversionJob)
            .where(ConversionJob.user_id == user_id)
            .options(selectinload(ConversionJob.converted_audios))
            .order_by(ConversionJob.created_at.desc())
        )
        return list(session.scalars(statement))

    @staticmethod
    def get_for_user(session: Session, user_id: UUID, job_id: UUID) -> ConversionJob | None:
        statement = (
            select(ConversionJob)
            .where(ConversionJob.user_id == user_id, ConversionJob.id == job_id)
            .options(selectinload(ConversionJob.converted_audios))
        )
        return session.scalar(statement)

    @staticmethod
    def create_job(
        session: Session,
        *,
        storage: StorageProvider,
        preprocessor: AudioPreprocessor,
        queue: RedisJobQueue | None,
        queue_name: str,
        user: User,
        profile: VoiceProfile,
        backend: EngineBackend,
        mode,
        original_filename: str,
        content_type: str | None,
        payload: bytes,
        ip_address: str | None,
        enqueue: bool = True,
    ) -> ConversionJob:
        suffix = validate_audio_filename(original_filename)
        key = (
            f"conversion-inputs/{user.id}/{profile.id}/"
            f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}_{uuid4().hex}{suffix}"
        )
        try:
            stored = storage.put_bytes(
                key=key,
                payload=payload,
                content_type=content_type or DEFAULT_AUDIO_CONTENT_TYPE,
            )
        except OSError as exc:
            raise ValueError(f"Source audio could not be stored: {exc}") from exc

        try:
            report = preprocessor.process(file_path=str(stored.path), size_bytes=stored.size_bytes)
        except AudioProcessingError as exc:
            raise ValueError(f"Source audio preprocessing failed: {exc}") from exc

        job = ConversionJob(
            user_id=user.id,
            voice_profile_id=profile.id,
            backend=backend,
            mode=mode,
            status=JobStatus.PENDING,
            queue_name=queue_name,
            source_audio_bucket=stored.bucket,
            source_audio_storage_key=stored.key,
            source_audio_filename=original_filename,
            source_audio_content_type=content_type or DEFAULT_AUDIO_CONTENT_TYPE,
            source_audio_duration_seconds=report.metadata.duration_seconds,
            source_audio_duration_ms=int(round(report.metadata.duration_seconds * 1000)),
            source_audio_sample_rate=report.metadata.sample_rate,
            readiness_snapshot=profile.readiness_score,
            traceability_token=secrets.token_urlsafe(18),
        )
        session.add(job)
        session.flush()

        if enqueue:
            if queue is None:
                raise ValueError("A Redis queue is required to enqueue conversion jobs.")
            queue.enqueue("conversion_requested", {"conversion_job_id": str(job.id)})

        AuditService.record(
            session,
            user_id=user.id,
            actor_email=user.email,
            event_type=AuditEventType.CONVERSION_JOB_CREATED,
            entity_type="conversion_job",
            entity_id=str(job.id),
            ip_address=ip_address,
            payload={
                "voice_profile_id": str(profile.id),
                "backend": backend.value,
                "mode": mode.value,
                "enqueue": enqueue,
            },
        )
        ConversionJobService._log_event(
            "info",
            "conversion_job_created",
            job_id=str(job.id),
            backend=backend.value,
            mode=mode.value,
            source_audio_duration_ms=job.source_audio_duration_ms,
        )
        return job

    @staticmethod
    def mark_failed(
        session: Session,
        *,
        job: ConversionJob,
        error_message: str,
        error_category: str | None = None,
        profiling_json: dict | None = None,
    ) -> ConversionJob:
        finished_at = datetime.now(timezone.utc)
        job.status = JobStatus.FAILED
        job.error_category = error_category or job.error_category or INFERENCE_FAILED
        job.error_message = error_message[:4000]
        if profiling_json is not None:
            job.profiling_json = profiling_json
        job.processing_finished_at = finished_at
        if job.processing_started_at is not None:
            job.processing_duration_ms = int(
                (finished_at - job.processing_started_at).total_seconds() * 1000
            )
        job.completed_at = None
        session.flush()
        ConversionJobService._log_event(
            "error",
            "conversion_job_failed",
            job_id=str(job.id),
            error_category=job.error_category,
            processing_duration_ms=job.processing_duration_ms,
            error_message=job.error_message,
        )
        return job

    @staticmethod
    def can_process(job: ConversionJob) -> bool:
        return job.status in {JobStatus.PENDING, JobStatus.FAILED, JobStatus.QUEUED}

    @staticmethod
    def classify_failure(exc: Exception) -> str:
        if isinstance(exc, SeedVCError):
            return exc.category
        if isinstance(exc, AudioProcessingError):
            return PREPROCESS_FAILED
        if isinstance(exc, (FileNotFoundError, PermissionError, OSError)):
            return STORAGE_FAILED

        message = str(exc).lower()
        if "reference" in message:
            return INVALID_REFERENCE
        if "preprocess" in message:
            return PREPROCESS_FAILED
        if "runtime" in message or "python executable" in message:
            return RUNTIME_MISSING
        return INFERENCE_FAILED

    @staticmethod
    def failure_payload(exc: Exception) -> dict:
        payload = {
            "error": str(exc),
            "error_category": ConversionJobService.classify_failure(exc),
        }
        if isinstance(exc, SeedVCError) and exc.diagnostics:
            payload["diagnostics"] = exc.diagnostics
            if exc.diagnostics.get("profiling"):
                payload["profiling"] = exc.diagnostics["profiling"]
        return payload

    @staticmethod
    def process_job(
        session: Session,
        *,
        storage: StorageProvider,
        registry: ModelRegistry,
        preprocessor: AudioPreprocessor,
        conversion_job_id: UUID,
    ) -> ConversionJob:
        job = session.get(ConversionJob, conversion_job_id)
        if job is None:
            raise ValueError(f"Conversion job not found: {conversion_job_id}")

        profile = session.get(VoiceProfile, job.voice_profile_id)
        if profile is None:
            raise ValueError(f"Voice profile not found for conversion job: {conversion_job_id}")
        if not ConversionJobService.can_process(job):
            raise ValueError(f"Conversion job {job.id} is not in a processable state: {job.status.value}.")

        reference_samples = ConversionJobService._select_reference_samples(session, profile_id=profile.id)
        if not reference_samples:
            raise ValueError(
                "Voice profile has no ready reference samples. Upload at least one processed sample before converting."
            )

        started_at = datetime.now(timezone.utc)
        job.status = JobStatus.PROCESSING
        job.started_at = started_at
        job.processing_started_at = started_at
        job.processing_finished_at = None
        job.processing_duration_ms = None
        job.completed_at = None
        job.output_audio_duration_ms = None
        job.error_category = None
        job.error_message = None
        session.flush()

        reference_sample_duration_ms = int(round(sum(sample.duration_seconds for sample in reference_samples) * 1000))
        ConversionJobService._log_event(
            "info",
            "conversion_job_processing_started",
            job_id=str(job.id),
            source_audio_duration_ms=job.source_audio_duration_ms,
            reference_sample_count=len(reference_samples),
            reference_sample_duration_ms=reference_sample_duration_ms,
        )

        source_bytes = ConversionJobService._read_storage_bytes(
            storage,
            key=job.source_audio_storage_key,
            label="source audio",
        )
        reference_candidates = tuple(
            ReferenceAudioCandidate(
                filename=sample.original_filename,
                content_type=sample.content_type,
                payload=ConversionJobService._read_storage_bytes(
                    storage,
                    key=sample.storage_key,
                    label=f"reference sample {sample.id}",
                ),
                sample_id=str(sample.id),
                storage_key=sample.storage_key,
                waveform_hash=sample.waveform_hash,
            )
            for sample in reference_samples
        )

        engine = registry.resolve(job.backend)
        request = ConversionRequest(
            backend=job.backend,
            mode=job.mode,
            source_audio_bytes=source_bytes,
            source_filename=job.source_audio_filename,
            source_content_type=job.source_audio_content_type,
            voice_profile_name=profile.name,
            readiness_score=profile.readiness_score,
            clip_count=profile.clip_count,
            reference_audio_bytes=reference_candidates[0].payload,
            reference_audio_filename=reference_candidates[0].filename,
            reference_audio_content_type=reference_candidates[0].content_type,
            reference_audio_candidates=reference_candidates,
            voice_profile_id=str(profile.id),
            job_id=str(job.id),
        )
        descriptor = engine.describe_reference_feature_cache(request)
        resolved_feature_cache = VoiceProfileFeatureCacheService.resolve_reference_cache(
            session,
            storage=storage,
            voice_profile_id=profile.id,
            descriptor=descriptor,
            reference_candidates=reference_candidates,
        )
        if resolved_feature_cache is not None:
            request.reference_feature_caches = (resolved_feature_cache,)
            ConversionJobService._log_event(
                "info",
                "conversion_job_reference_cache_hit",
                job_id=str(job.id),
                backend=resolved_feature_cache.backend.value,
                namespace=resolved_feature_cache.namespace,
                storage_key=resolved_feature_cache.storage_key,
            )
        result = engine.convert(request)
        engine_metrics = result.engine_metrics or {}
        if resolved_feature_cache is not None:
            result.traceability_metadata.setdefault("reference_feature_cache", {})
            result.traceability_metadata["reference_feature_cache"]["resolved"] = {
                "namespace": resolved_feature_cache.namespace,
                "backend": resolved_feature_cache.backend.value,
                "artifact_version": resolved_feature_cache.artifact_version,
                "storage_key": resolved_feature_cache.storage_key,
                "checksum": resolved_feature_cache.checksum,
            }
        if result.generated_feature_caches:
            persisted_caches = VoiceProfileFeatureCacheService.persist_generated_caches(
                session,
                storage=storage,
                voice_profile_id=profile.id,
                generated_caches=result.generated_feature_caches,
            )
            result.traceability_metadata.setdefault("reference_feature_cache", {})
            result.traceability_metadata["reference_feature_cache"]["persisted"] = [
                {
                    "namespace": cache.cache_namespace,
                    "backend": cache.backend.value,
                    "version": cache.version,
                    "artifact_version": cache.artifact_version,
                    "storage_key": cache.storage_key,
                    "checksum": cache.checksum,
                }
                for cache in persisted_caches
            ]
            engine_metrics["generated_reference_feature_cache_count"] = len(persisted_caches)
        job.reference_audio_duration_ms = int(
            engine_metrics.get("reference_audio_duration_ms") or reference_sample_duration_ms
        )
        job.profiling_json = ConversionJobService._build_profiling_payload(
            existing=job.profiling_json,
            engine_metrics=engine_metrics,
            output_persistence_ms=None,
            output_validation_ms=None,
        )
        session.flush()

        output_key = f"converted/{job.user_id}/{profile.id}/{job.id}.{result.output_format}"
        try:
            persistence_started = time.monotonic()
            stored = storage.put_bytes(output_key, result.output_bytes, result.content_type)
            output_persistence_ms = int((time.monotonic() - persistence_started) * 1000)
        except OSError as exc:
            raise OSError(f"Converted audio could not be stored: {exc}") from exc

        try:
            validation_started = time.monotonic()
            report = preprocessor.process(file_path=str(stored.path), size_bytes=stored.size_bytes)
            output_validation_ms = int((time.monotonic() - validation_started) * 1000)
        except AudioProcessingError as exc:
            raise AudioProcessingError(f"Converted audio validation failed: {exc}") from exc

        converted_audio = ConvertedAudio(
            conversion_job_id=job.id,
            storage_bucket=stored.bucket,
            storage_key=stored.key,
            format=result.output_format,
            duration_seconds=report.metadata.duration_seconds,
            sample_rate=report.metadata.sample_rate,
            size_bytes=stored.size_bytes,
            watermark_status="reserved",
            traceability_metadata=result.traceability_metadata,
        )
        session.add(converted_audio)

        finished_at = datetime.now(timezone.utc)
        job.status = JobStatus.COMPLETED
        job.output_audio_duration_ms = int(round(report.metadata.duration_seconds * 1000))
        job.profiling_json = ConversionJobService._build_profiling_payload(
            existing=job.profiling_json,
            engine_metrics=engine_metrics,
            output_persistence_ms=output_persistence_ms,
            output_validation_ms=output_validation_ms,
        )
        job.processing_finished_at = finished_at
        job.processing_duration_ms = int((finished_at - started_at).total_seconds() * 1000)
        job.completed_at = finished_at
        session.flush()

        ConversionJobService._log_event(
            "info",
            "conversion_job_completed",
            job_id=str(job.id),
            output_storage_key=stored.key,
            processing_duration_ms=job.processing_duration_ms,
            reference_audio_duration_ms=job.reference_audio_duration_ms,
            output_audio_duration_ms=job.output_audio_duration_ms,
            output_persistence_ms=output_persistence_ms,
        )
        return job

    @staticmethod
    def _select_reference_samples(session: Session, *, profile_id: UUID) -> list[VoiceSample]:
        statement = (
            select(VoiceSample)
            .where(
                VoiceSample.voice_profile_id == profile_id,
                VoiceSample.processing_status == ProcessingStatus.READY,
            )
            .order_by(
                VoiceSample.noise_score.asc(),
                VoiceSample.duration_seconds.desc(),
                VoiceSample.created_at.desc(),
            )
            .limit(3)
        )
        return list(session.scalars(statement))

    @staticmethod
    def _read_storage_bytes(storage: StorageProvider, *, key: str, label: str) -> bytes:
        try:
            return storage.read_bytes(key)
        except OSError as exc:
            raise OSError(f"{label.capitalize()} could not be read from storage: {exc}") from exc

    @staticmethod
    def _build_profiling_payload(
        *,
        existing: dict | None,
        engine_metrics: dict,
        output_persistence_ms: int | None,
        output_validation_ms: int | None,
    ) -> dict:
        profiling = dict(existing or engine_metrics.get("profiling") or {})
        stages = dict(profiling.get("stages_ms", {}))
        details = dict(profiling.get("details_ms", {}))
        if output_persistence_ms is not None:
            stages["output_persistence"] = output_persistence_ms
        if output_validation_ms is not None:
            details["output_validation"] = output_validation_ms
        profiling["stages_ms"] = stages
        profiling["details_ms"] = details
        return profiling

    @staticmethod
    def _log_event(level: str, event: str, **payload: object) -> None:
        message = json.dumps({"event": event, **payload}, default=str)
        getattr(logger, level)(message)
