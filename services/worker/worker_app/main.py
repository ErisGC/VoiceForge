from __future__ import annotations

import logging
import time
from uuid import UUID

from voiceforge_core.db.enums import AuditEventType, JobStatus
from voiceforge_core.db.models import ConversionJob, TrainingJob
from voiceforge_core.modules.audit.service import AuditService
from voiceforge_core.modules.conversion_jobs.service import ConversionJobService
from voiceforge_core.modules.training_jobs.service import TrainingJobService
from voiceforge_core.runtime import RuntimeConfig, build_runtime
from worker_app.settings import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("voiceforge-worker")


def process_training_job(runtime, training_job_id: UUID) -> None:
    with runtime.session_factory() as session:
        job = session.get(TrainingJob, training_job_id)
        if job is None:
            logger.warning("Training job %s not found.", training_job_id)
            return
        try:
            TrainingJobService.process_job(
                session,
                storage=runtime.storage,
                orchestrator=runtime.training_orchestrator,
                training_job_id=training_job_id,
            )
            AuditService.record(
                session,
                user_id=job.requested_by_user_id,
                actor_email=None,
                event_type=AuditEventType.TRAINING_JOB_COMPLETED,
                entity_type="training_job",
                entity_id=str(job.id),
                ip_address="worker",
                payload={"voice_profile_id": str(job.voice_profile_id)},
            )
            session.commit()
            logger.info("Training job %s completed.", training_job_id)
        except Exception as exc:  # pragma: no cover - worker safety net
            session.rollback()
            failed_job = session.get(TrainingJob, training_job_id)
            if failed_job is not None:
                failed_job.status = JobStatus.FAILED
                failed_job.error_message = str(exc)
                AuditService.record(
                    session,
                    user_id=failed_job.requested_by_user_id,
                    actor_email=None,
                    event_type=AuditEventType.TRAINING_JOB_FAILED,
                    entity_type="training_job",
                    entity_id=str(failed_job.id),
                    ip_address="worker",
                    payload={"error": str(exc)},
                )
                session.commit()
            logger.exception("Training job %s failed.", training_job_id)


def process_conversion_job(runtime, conversion_job_id: UUID) -> None:
    with runtime.session_factory() as session:
        job = session.get(ConversionJob, conversion_job_id)
        if job is None:
            logger.warning("Conversion job %s not found.", conversion_job_id)
            return
        try:
            AuditService.record(
                session,
                user_id=job.user_id,
                actor_email=None,
                event_type=AuditEventType.CONVERSION_JOB_STARTED,
                entity_type="conversion_job",
                entity_id=str(job.id),
                ip_address="worker",
                payload={"voice_profile_id": str(job.voice_profile_id)},
            )
            ConversionJobService.process_job(
                session,
                storage=runtime.storage,
                registry=runtime.model_registry,
                preprocessor=runtime.audio_preprocessor,
                conversion_job_id=conversion_job_id,
            )
            AuditService.record(
                session,
                user_id=job.user_id,
                actor_email=None,
                event_type=AuditEventType.CONVERSION_JOB_COMPLETED,
                entity_type="conversion_job",
                entity_id=str(job.id),
                ip_address="worker",
                payload={"voice_profile_id": str(job.voice_profile_id)},
            )
            session.commit()
            logger.info("Conversion job %s completed.", conversion_job_id)
        except Exception as exc:  # pragma: no cover - worker safety net
            session.rollback()
            failed_job = session.get(ConversionJob, conversion_job_id)
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
                    user_id=failed_job.user_id,
                    actor_email=None,
                    event_type=AuditEventType.CONVERSION_JOB_FAILED,
                    entity_type="conversion_job",
                    entity_id=str(failed_job.id),
                    ip_address="worker",
                    payload=failure_payload,
                )
                session.commit()
            logger.exception("Conversion job %s failed.", conversion_job_id)


def main() -> None:
    settings = get_settings()
    runtime = build_runtime(
        RuntimeConfig(
            database_url=settings.database_url,
            redis_url=settings.redis_url,
            queue_name=settings.job_queue_name,
            storage_root=settings.storage_root,
            storage_bucket=settings.storage_bucket,
            seed_vc_python=settings.seed_vc_python,
            seed_vc_repo_dir=settings.seed_vc_repo_dir,
            seed_vc_working_root=settings.seed_vc_working_root,
            seed_vc_diffusion_steps=settings.seed_vc_diffusion_steps,
            seed_vc_length_adjust=settings.seed_vc_length_adjust,
            seed_vc_inference_cfg_rate=settings.seed_vc_inference_cfg_rate,
            seed_vc_f0_condition=settings.seed_vc_f0_condition,
            seed_vc_auto_f0_adjust=settings.seed_vc_auto_f0_adjust,
            seed_vc_semi_tone_shift=settings.seed_vc_semi_tone_shift,
            seed_vc_fp16=settings.seed_vc_fp16,
            seed_vc_timeout_seconds=settings.seed_vc_timeout_seconds,
            seed_vc_checkpoint_path=settings.seed_vc_checkpoint_path,
            seed_vc_config_path=settings.seed_vc_config_path,
            seed_vc_hf_endpoint=settings.seed_vc_hf_endpoint,
            seed_vc_target_sample_rate=settings.seed_vc_target_sample_rate,
            seed_vc_reference_max_seconds=settings.seed_vc_reference_max_seconds,
            seed_vc_reference_clip_limit=settings.seed_vc_reference_clip_limit,
            seed_vc_reference_cache_enabled=settings.seed_vc_reference_cache_enabled,
            seed_vc_source_cache_enabled=settings.seed_vc_source_cache_enabled,
            seed_vc_resident_reference_runtime_enabled=settings.seed_vc_resident_reference_runtime_enabled,
            seed_vc_resident_source_runtime_enabled=settings.seed_vc_resident_source_runtime_enabled,
            seed_vc_resident_runtime_idle_seconds=settings.seed_vc_resident_runtime_idle_seconds,
            seed_vc_resident_runtime_launch_timeout_seconds=settings.seed_vc_resident_runtime_launch_timeout_seconds,
        )
    )

    logger.info("VoiceForge worker listening on queue %s", settings.job_queue_name)
    while True:
        envelope = runtime.queue.dequeue(timeout=5)
        if envelope is None:
            time.sleep(0.2)
            continue

        if envelope.job_type == "training_requested":
            process_training_job(runtime, UUID(envelope.payload["training_job_id"]))
        elif envelope.job_type == "conversion_requested":
            process_conversion_job(runtime, UUID(envelope.payload["conversion_job_id"]))
        else:
            logger.warning("Unknown job type received: %s", envelope.job_type)


if __name__ == "__main__":
    main()
