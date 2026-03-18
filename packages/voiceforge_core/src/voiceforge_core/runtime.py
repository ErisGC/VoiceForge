from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from voiceforge_core.audio.contracts import AudioPreprocessor
from voiceforge_core.audio.pipeline import WaveAudioPreprocessor
from voiceforge_core.inference.contracts import SpeakerEmbeddingService
from voiceforge_core.inference.model_registry import (
    build_default_model_registry,
    build_speaker_embedding_service,
)
from voiceforge_core.inference.seed_vc import SeedVCBackendConfig
from voiceforge_core.jobs.queue import RedisJobQueue
from voiceforge_core.modules.training_jobs.service import ManifestTrainingOrchestrator
from voiceforge_core.storage.local_s3 import LocalS3CompatibleStorage


@dataclass(slots=True)
class RuntimeConfig:
    database_url: str
    redis_url: str
    queue_name: str
    storage_root: str
    storage_bucket: str
    seed_vc_python: str
    seed_vc_repo_dir: str
    seed_vc_working_root: str
    seed_vc_diffusion_steps: int
    seed_vc_length_adjust: float
    seed_vc_inference_cfg_rate: float
    seed_vc_f0_condition: bool
    seed_vc_auto_f0_adjust: bool
    seed_vc_semi_tone_shift: int
    seed_vc_fp16: bool
    seed_vc_timeout_seconds: int
    seed_vc_checkpoint_path: str | None
    seed_vc_config_path: str | None
    seed_vc_hf_endpoint: str | None
    seed_vc_target_sample_rate: int
    seed_vc_reference_max_seconds: float
    seed_vc_reference_clip_limit: int
    seed_vc_reference_cache_enabled: bool
    seed_vc_source_cache_enabled: bool
    seed_vc_resident_reference_runtime_enabled: bool
    seed_vc_resident_source_runtime_enabled: bool
    seed_vc_resident_runtime_idle_seconds: int
    seed_vc_resident_runtime_launch_timeout_seconds: int


@dataclass(slots=True)
class RuntimeContainer:
    session_factory: sessionmaker[Session]
    storage: LocalS3CompatibleStorage
    queue: RedisJobQueue
    audio_preprocessor: AudioPreprocessor
    embedding_extractor: SpeakerEmbeddingService
    model_registry: Any
    training_orchestrator: ManifestTrainingOrchestrator


def build_runtime(config: RuntimeConfig) -> RuntimeContainer:
    engine = create_engine(config.database_url, future=True)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    storage = LocalS3CompatibleStorage(root=config.storage_root, bucket=config.storage_bucket)
    queue = RedisJobQueue(redis_url=config.redis_url, queue_name=config.queue_name)
    audio_preprocessor = WaveAudioPreprocessor()
    embedding_extractor = build_speaker_embedding_service()
    seed_vc_config = SeedVCBackendConfig(
        python_executable=config.seed_vc_python,
        repo_dir=config.seed_vc_repo_dir,
        working_root=config.seed_vc_working_root,
        diffusion_steps=config.seed_vc_diffusion_steps,
        length_adjust=config.seed_vc_length_adjust,
        inference_cfg_rate=config.seed_vc_inference_cfg_rate,
        f0_condition=config.seed_vc_f0_condition,
        auto_f0_adjust=config.seed_vc_auto_f0_adjust,
        semi_tone_shift=config.seed_vc_semi_tone_shift,
        fp16=config.seed_vc_fp16,
        timeout_seconds=config.seed_vc_timeout_seconds,
        checkpoint_path=config.seed_vc_checkpoint_path,
        config_path=config.seed_vc_config_path,
        hf_endpoint=config.seed_vc_hf_endpoint,
        target_sample_rate=config.seed_vc_target_sample_rate,
        reference_max_seconds=config.seed_vc_reference_max_seconds,
        reference_clip_limit=config.seed_vc_reference_clip_limit,
        reference_cache_enabled=config.seed_vc_reference_cache_enabled,
        source_cache_enabled=config.seed_vc_source_cache_enabled,
        resident_reference_runtime_enabled=config.seed_vc_resident_reference_runtime_enabled,
        resident_source_runtime_enabled=config.seed_vc_resident_source_runtime_enabled,
        resident_runtime_idle_seconds=config.seed_vc_resident_runtime_idle_seconds,
        resident_runtime_launch_timeout_seconds=config.seed_vc_resident_runtime_launch_timeout_seconds,
    )
    model_registry = build_default_model_registry(
        seed_vc_config=seed_vc_config,
        preprocessor=audio_preprocessor,
    )
    training_orchestrator = ManifestTrainingOrchestrator()
    return RuntimeContainer(
        session_factory=session_factory,
        storage=storage,
        queue=queue,
        audio_preprocessor=audio_preprocessor,
        embedding_extractor=embedding_extractor,
        model_registry=model_registry,
        training_orchestrator=training_orchestrator,
    )
