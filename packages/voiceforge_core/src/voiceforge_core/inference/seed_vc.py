from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from voiceforge_core.audio.pipeline import AudioProcessingError, WaveAudioPreprocessor
from voiceforge_core.db.enums import EngineBackend
from voiceforge_core.inference.contracts import (
    ConversionRequest,
    ConversionResult,
    FeatureCacheArtifact,
    FeatureCacheDescriptor,
    FeatureCacheReference,
    ReferenceAudioCandidate,
    VoiceConversionEngine,
)
from voiceforge_core.inference.local_feature_cache_store import LocalFeatureCacheStore

logger = logging.getLogger("voiceforge.seed_vc")

PROFILED_RUNNER_MODULE = "voiceforge_core.inference.seed_vc_profiled_runner"
REFERENCE_CACHE_RUNTIME_MODULE = "voiceforge_core.inference.seed_vc_reference_runtime"
SOURCE_CACHE_NAMESPACE = "source_features"
SOURCE_CACHE_ARTIFACT_VERSION = "seed-vc-source-v1"
REFERENCE_CACHE_NAMESPACE = "reference_features"
REFERENCE_CACHE_ARTIFACT_VERSION = "seed-vc-ref-v1"

RUNTIME_MISSING = "runtime_missing"
PREPROCESS_FAILED = "preprocess_failed"
INFERENCE_FAILED = "inference_failed"
STORAGE_FAILED = "storage_failed"
INVALID_REFERENCE = "invalid_reference"


class SeedVCError(RuntimeError):
    default_category = INFERENCE_FAILED

    def __init__(self, message: str, *, category: str | None = None, diagnostics: dict | None = None) -> None:
        super().__init__(message)
        self.category = category or self.default_category
        self.diagnostics = diagnostics or {}


class SeedVCConfigurationError(SeedVCError):
    default_category = RUNTIME_MISSING


class SeedVCPreprocessError(SeedVCError):
    default_category = PREPROCESS_FAILED


class SeedVCInferenceError(SeedVCError):
    default_category = INFERENCE_FAILED


class SeedVCInvalidReferenceError(SeedVCError):
    default_category = INVALID_REFERENCE


@dataclass(slots=True)
class SeedVCBackendConfig:
    python_executable: str
    repo_dir: str
    working_root: str
    diffusion_steps: int = 25
    length_adjust: float = 1.0
    inference_cfg_rate: float = 0.7
    f0_condition: bool = False
    auto_f0_adjust: bool = False
    semi_tone_shift: int = 0
    fp16: bool = False
    timeout_seconds: int = 3600
    checkpoint_path: str | None = None
    config_path: str | None = None
    hf_endpoint: str | None = None
    target_sample_rate: int = 22050
    reference_max_seconds: float = 25.0
    reference_clip_limit: int = 3
    reference_cache_enabled: bool = True
    source_cache_enabled: bool = True
    resident_reference_runtime_enabled: bool = True
    resident_source_runtime_enabled: bool = True
    resident_runtime_idle_seconds: int = 900
    resident_runtime_launch_timeout_seconds: int = 120


class SeedVCVoiceConversionEngine(VoiceConversionEngine):
    backend = EngineBackend.SEED_VC

    def __init__(self, *, config: SeedVCBackendConfig, preprocessor: WaveAudioPreprocessor) -> None:
        self.config = config
        self.preprocessor = preprocessor
        self._runtime_verified = False
        self._local_feature_cache_store = LocalFeatureCacheStore(self._working_root() / "runtime-feature-caches")

    def validate_runtime(self, *, job_id: str = "runtime-check") -> None:
        self._validate_environment(job_id=job_id)

    def describe_source_feature_cache(self, request: ConversionRequest) -> FeatureCacheDescriptor | None:
        if not self.config.source_cache_enabled:
            return None
        return FeatureCacheDescriptor(
            backend=self.backend,
            namespace=SOURCE_CACHE_NAMESPACE,
            artifact_version=SOURCE_CACHE_ARTIFACT_VERSION,
            cache_format="pt",
            config_signature=self._build_source_cache_config_signature(),
            metadata={
                "target_sample_rate": self.config.target_sample_rate,
                "f0_condition": self.config.f0_condition,
                "checkpoint_path": self.config.checkpoint_path,
                "config_path": self.config.config_path,
                "preprocessor": {
                    "trim_top_db": self.preprocessor.trim_top_db,
                    "target_peak": self.preprocessor.target_peak,
                    "frame_length": self.preprocessor.frame_length,
                    "hop_length": self.preprocessor.hop_length,
                },
            },
        )

    def describe_reference_feature_cache(self, request: ConversionRequest) -> FeatureCacheDescriptor | None:
        if not self.config.reference_cache_enabled:
            return None
        reference_candidates = self._select_reference_candidates(request)
        if not reference_candidates:
            return None
        return FeatureCacheDescriptor(
            backend=self.backend,
            namespace=REFERENCE_CACHE_NAMESPACE,
            artifact_version=REFERENCE_CACHE_ARTIFACT_VERSION,
            cache_format="pt",
            config_signature=self._build_reference_cache_config_signature(),
            metadata={
                "target_sample_rate": self.config.target_sample_rate,
                "reference_max_seconds": self.config.reference_max_seconds,
                "reference_clip_limit": self.config.reference_clip_limit,
                "f0_condition": self.config.f0_condition,
                "checkpoint_path": self.config.checkpoint_path,
                "config_path": self.config.config_path,
                "reference_candidate_count": len(reference_candidates),
            },
        )

    def prepare_reference_feature_cache(
        self,
        request: ConversionRequest,
    ) -> tuple[FeatureCacheArtifact, ...]:
        if not self.config.reference_cache_enabled or not self.config.resident_reference_runtime_enabled:
            return ()
        descriptor = self.describe_reference_feature_cache(request)
        if descriptor is None:
            return ()

        job_id = request.job_id or "adhoc"
        reference_candidates = self._select_reference_candidates(request)
        working_root = self._working_root()
        working_root.mkdir(parents=True, exist_ok=True)

        with TemporaryDirectory(prefix="seed-vc-cache-", dir=working_root) as temp_dir:
            temp_path = Path(temp_dir)
            raw_reference_paths: list[Path] = []
            for index, candidate in enumerate(reference_candidates, start=1):
                candidate_path = temp_path / f"reference_{index}{Path(candidate.filename).suffix or '.wav'}"
                candidate_path.write_bytes(candidate.payload)
                raw_reference_paths.append(candidate_path)

            try:
                prepared_reference = self.preprocessor.prepare_reference_prompt(
                    input_paths=raw_reference_paths,
                    output_path=temp_path / "prepared_reference.wav",
                    target_sample_rate=self.config.target_sample_rate,
                    max_duration_seconds=self.config.reference_max_seconds,
                )
            except AudioProcessingError as exc:
                raise SeedVCPreprocessError(
                    f"Seed-VC reference cache preprocessing failed: {exc}",
                    diagnostics={"workspace": str(temp_path)},
                ) from exc
            except ValueError as exc:
                raise SeedVCInvalidReferenceError(
                    f"Reference audio is invalid for Seed-VC cache preparation: {exc}",
                    diagnostics={"workspace": str(temp_path)},
                ) from exc

            if prepared_reference.metadata.duration_seconds < 0.5:
                raise SeedVCInvalidReferenceError(
                    "Reference prompt is too short after preprocessing. Provide at least 0.5 seconds of clear speech.",
                    diagnostics={"reference_duration_seconds": prepared_reference.metadata.duration_seconds},
                )

            artifact_path = temp_path / f"{REFERENCE_CACHE_NAMESPACE}.{descriptor.cache_format}"
            response = self._build_reference_cache_via_resident_runtime(
                job_id=job_id,
                prepared_reference_path=prepared_reference.path,
                artifact_path=artifact_path,
            )
            payload = artifact_path.read_bytes()
            checksum = hashlib.sha256(payload).hexdigest()
            return (
                FeatureCacheArtifact(
                    backend=self.backend,
                    namespace=descriptor.namespace,
                    artifact_version=descriptor.artifact_version,
                    cache_format=descriptor.cache_format,
                    sample_signature=self._build_reference_cache_sample_signature(reference_candidates),
                    config_signature=descriptor.config_signature,
                    checksum=checksum,
                    payload=payload,
                    metadata={
                        **descriptor.metadata,
                        "resident_runtime": {
                            "enabled": True,
                            "job_id": job_id,
                            **response,
                        },
                        "reference_prompt": {
                            "sample_rate": prepared_reference.metadata.sample_rate,
                            "duration_seconds": prepared_reference.metadata.duration_seconds,
                            "trimmed_seconds": prepared_reference.trimmed_seconds,
                            "normalized_peak": prepared_reference.normalized_peak,
                        },
                    },
                ),
            )

    def prepare_source_feature_cache(
        self,
        request: ConversionRequest,
    ) -> tuple[FeatureCacheArtifact, ...]:
        if not self.config.source_cache_enabled or not self.config.resident_source_runtime_enabled:
            return ()
        descriptor = self.describe_source_feature_cache(request)
        if descriptor is None:
            return ()

        job_id = request.job_id or "adhoc"
        working_root = self._working_root()
        working_root.mkdir(parents=True, exist_ok=True)

        with TemporaryDirectory(prefix="seed-vc-source-cache-", dir=working_root) as temp_dir:
            temp_path = Path(temp_dir)
            raw_source_path = temp_path / f"source{Path(request.source_filename).suffix or '.wav'}"
            raw_source_path.write_bytes(request.source_audio_bytes)

            try:
                prepared_source = self.preprocessor.prepare_for_seed_vc(
                    input_path=raw_source_path,
                    output_path=temp_path / "prepared_source.wav",
                    target_sample_rate=self.config.target_sample_rate,
                )
            except AudioProcessingError as exc:
                raise SeedVCPreprocessError(
                    f"Seed-VC source cache preprocessing failed: {exc}",
                    diagnostics={"workspace": str(temp_path)},
                ) from exc

            artifact_path = temp_path / f"{SOURCE_CACHE_NAMESPACE}.{descriptor.cache_format}"
            response = self._build_source_cache_via_resident_runtime(
                job_id=job_id,
                prepared_source_path=prepared_source.path,
                artifact_path=artifact_path,
            )
            payload = artifact_path.read_bytes()
            checksum = hashlib.sha256(payload).hexdigest()
            return (
                FeatureCacheArtifact(
                    backend=self.backend,
                    namespace=descriptor.namespace,
                    artifact_version=descriptor.artifact_version,
                    cache_format=descriptor.cache_format,
                    sample_signature=self._build_source_cache_sample_signature(request),
                    config_signature=descriptor.config_signature,
                    checksum=checksum,
                    payload=payload,
                    metadata={
                        **descriptor.metadata,
                        "resident_runtime": {
                            "enabled": True,
                            "job_id": job_id,
                            **response,
                        },
                        "source_prompt": {
                            "sample_rate": prepared_source.metadata.sample_rate,
                            "duration_seconds": prepared_source.metadata.duration_seconds,
                            "trimmed_seconds": prepared_source.trimmed_seconds,
                            "normalized_peak": prepared_source.normalized_peak,
                        },
                    },
                ),
            )

    def convert(self, request: ConversionRequest) -> ConversionResult:
        job_id = request.job_id or "adhoc"
        self._log_event(
            "info",
            "seed_vc_conversion_started",
            job_id=job_id,
            backend=self.backend.value,
            voice_profile_name=request.voice_profile_name,
            reference_candidate_count=len(request.reference_audio_candidates),
        )

        cache_state = "warm" if self._has_warm_cache() else "cold"
        validation_started = time.monotonic()
        self.validate_runtime(job_id=job_id)
        runtime_validation_ms = int((time.monotonic() - validation_started) * 1000)
        reference_candidates = self._select_reference_candidates(request)
        start_monotonic = time.monotonic()
        source_cache_descriptor = self.describe_source_feature_cache(request)
        source_cache_sample_signature = (
            self._build_source_cache_sample_signature(request) if source_cache_descriptor is not None else None
        )
        selected_source_cache = (
            self._select_local_feature_cache(
                descriptor=source_cache_descriptor,
                sample_signature=source_cache_sample_signature,
            )
            if source_cache_descriptor is not None and source_cache_sample_signature is not None
            else None
        )
        source_cache_hit = selected_source_cache is not None
        source_cache_generated = False
        if selected_source_cache is not None:
            self._log_event(
                "info",
                "seed_vc_source_cache_hit",
                job_id=job_id,
                namespace=selected_source_cache.namespace,
                storage_key=selected_source_cache.storage_key,
            )
        reference_cache_descriptor = self.describe_reference_feature_cache(request)
        generated_feature_caches: tuple[FeatureCacheArtifact, ...] = ()
        selected_reference_cache = self._select_reference_feature_cache(request, descriptor=reference_cache_descriptor)
        reference_cache_hit = selected_reference_cache is not None
        if selected_reference_cache is not None:
            self._log_event(
                "info",
                "seed_vc_reference_cache_hit",
                job_id=job_id,
                namespace=selected_reference_cache.namespace,
                storage_key=selected_reference_cache.storage_key,
            )
        source_cache_prepare_ms = 0
        reference_cache_prepare_ms = 0
        source_cache_persisted: FeatureCacheReference | None = selected_source_cache
        if (
            selected_source_cache is None
            and self.config.source_cache_enabled
            and self.config.resident_source_runtime_enabled
            and source_cache_descriptor is not None
        ):
            try:
                cache_prepare_started = time.monotonic()
                generated_source_caches = self.prepare_source_feature_cache(request)
                source_cache_prepare_ms = int((time.monotonic() - cache_prepare_started) * 1000)
                if generated_source_caches:
                    source_cache_persisted = self._local_feature_cache_store.persist(generated_source_caches[0])
                    selected_source_cache = source_cache_persisted
                    source_cache_generated = True
                    self._log_event(
                        "info",
                        "seed_vc_source_cache_persisted",
                        job_id=job_id,
                        namespace=source_cache_persisted.namespace,
                        storage_key=source_cache_persisted.storage_key,
                    )
            except SeedVCError as exc:
                if exc.category == PREPROCESS_FAILED:
                    raise
                self._log_event(
                    "warning",
                    "seed_vc_source_cache_prepare_failed",
                    job_id=job_id,
                    error=str(exc),
                    category=exc.category,
                )

        if (
            selected_reference_cache is None
            and self.config.reference_cache_enabled
            and self.config.resident_reference_runtime_enabled
        ):
            try:
                cache_prepare_started = time.monotonic()
                generated_feature_caches = self.prepare_reference_feature_cache(request)
                reference_cache_prepare_ms = int((time.monotonic() - cache_prepare_started) * 1000)
                if generated_feature_caches:
                    generated_cache = generated_feature_caches[0]
                    selected_reference_cache = FeatureCacheReference(
                        backend=generated_cache.backend,
                        namespace=generated_cache.namespace,
                        artifact_version=generated_cache.artifact_version,
                        cache_format=generated_cache.cache_format,
                        sample_signature=generated_cache.sample_signature,
                        config_signature=generated_cache.config_signature,
                        checksum=generated_cache.checksum,
                        payload=generated_cache.payload,
                        metadata=generated_cache.metadata,
                    )
            except SeedVCError as exc:
                if exc.category in {INVALID_REFERENCE, PREPROCESS_FAILED}:
                    raise
                self._log_event(
                    "warning",
                    "seed_vc_reference_cache_prepare_failed",
                    job_id=job_id,
                    error=str(exc),
                    category=exc.category,
                )

        working_root = self._working_root()
        working_root.mkdir(parents=True, exist_ok=True)

        with TemporaryDirectory(prefix="seed-vc-", dir=working_root) as temp_dir:
            temp_path = Path(temp_dir)
            self._log_event("info", "seed_vc_temp_workspace_created", job_id=job_id, workspace=str(temp_path))
            try:
                raw_source_path = temp_path / f"source{Path(request.source_filename).suffix or '.wav'}"
                raw_source_path.write_bytes(request.source_audio_bytes)

                raw_reference_paths: list[Path] = []
                for index, candidate in enumerate(reference_candidates, start=1):
                    candidate_path = temp_path / f"reference_{index}{Path(candidate.filename).suffix or '.wav'}"
                    candidate_path.write_bytes(candidate.payload)
                    raw_reference_paths.append(candidate_path)

                try:
                    stage_started = time.monotonic()
                    prepared_source = self.preprocessor.prepare_for_seed_vc(
                        input_path=raw_source_path,
                        output_path=temp_path / "prepared_source.wav",
                        target_sample_rate=self.config.target_sample_rate,
                    )
                    source_preprocessing_ms = int((time.monotonic() - stage_started) * 1000)

                    stage_started = time.monotonic()
                    prepared_reference = self.preprocessor.prepare_reference_prompt(
                        input_paths=raw_reference_paths,
                        output_path=temp_path / "prepared_reference.wav",
                        target_sample_rate=self.config.target_sample_rate,
                        max_duration_seconds=self.config.reference_max_seconds,
                    )
                    reference_preprocessing_ms = int((time.monotonic() - stage_started) * 1000)
                except AudioProcessingError as exc:
                    raise SeedVCPreprocessError(
                        f"Seed-VC preprocessing failed: {exc}",
                        diagnostics={"workspace": str(temp_path)},
                    ) from exc
                except ValueError as exc:
                    raise SeedVCInvalidReferenceError(
                        f"Reference audio is invalid for Seed-VC: {exc}",
                        diagnostics={"workspace": str(temp_path)},
                    ) from exc

                if prepared_reference.metadata.duration_seconds < 0.5:
                    raise SeedVCInvalidReferenceError(
                        "Reference prompt is too short after preprocessing. Provide at least 0.5 seconds of clear speech.",
                        diagnostics={"reference_duration_seconds": prepared_reference.metadata.duration_seconds},
                    )

                output_dir = temp_path / "output"
                output_dir.mkdir(parents=True, exist_ok=True)
                metrics_path = temp_path / "seed_vc_metrics.json"
                source_cache_input_path = None
                source_cache_output_path = None
                reference_cache_input_path = None
                reference_cache_output_path = None
                if selected_source_cache is not None:
                    source_cache_input_path = temp_path / f"source_cache.{selected_source_cache.cache_format}"
                    source_cache_input_path.write_bytes(selected_source_cache.payload)
                elif self.config.source_cache_enabled and source_cache_descriptor is not None:
                    source_cache_output_path = temp_path / f"generated_source_cache.{source_cache_descriptor.cache_format}"
                if selected_reference_cache is not None:
                    reference_cache_input_path = temp_path / f"reference_cache.{selected_reference_cache.cache_format}"
                    reference_cache_input_path.write_bytes(selected_reference_cache.payload)
                elif self.config.reference_cache_enabled and reference_cache_descriptor is not None:
                    reference_cache_output_path = (
                        temp_path / f"generated_reference_cache.{reference_cache_descriptor.cache_format}"
                    )
                command = self._build_command(
                    source_path=prepared_source.path,
                    reference_path=prepared_reference.path,
                    output_dir=output_dir,
                    metrics_output_path=metrics_path,
                    source_cache_input_path=source_cache_input_path,
                    source_cache_output_path=source_cache_output_path,
                    reference_cache_input_path=reference_cache_input_path,
                    reference_cache_output_path=reference_cache_output_path,
                )
                env = self._build_environment()

                completed, log_artifacts, subprocess_duration_ms, profiled_metrics = self._run_seed_vc(
                    job_id=job_id,
                    command=command,
                    env=env,
                    metrics_output_path=metrics_path,
                )
                output_file = self._resolve_output_file(output_dir)
                output_bytes = output_file.read_bytes()
                generated_source_cache: FeatureCacheReference | None = source_cache_persisted
                if (
                    source_cache_output_path is not None
                    and source_cache_output_path.exists()
                    and selected_source_cache is None
                    and source_cache_descriptor is not None
                    and source_cache_sample_signature is not None
                ):
                    cache_payload = source_cache_output_path.read_bytes()
                    source_artifact = FeatureCacheArtifact(
                        backend=self.backend,
                        namespace=source_cache_descriptor.namespace,
                        artifact_version=source_cache_descriptor.artifact_version,
                        cache_format=source_cache_descriptor.cache_format,
                        sample_signature=source_cache_sample_signature,
                        config_signature=source_cache_descriptor.config_signature,
                        checksum=hashlib.sha256(cache_payload).hexdigest(),
                        payload=cache_payload,
                        metadata={
                            **source_cache_descriptor.metadata,
                            "generated_during_conversion": True,
                            "job_id": job_id,
                        },
                    )
                    generated_source_cache = self._local_feature_cache_store.persist(source_artifact)
                    source_cache_generated = True
                    self._log_event(
                        "info",
                        "seed_vc_source_cache_persisted",
                        job_id=job_id,
                        namespace=generated_source_cache.namespace,
                        storage_key=generated_source_cache.storage_key,
                    )
                if (
                    reference_cache_output_path is not None
                    and reference_cache_output_path.exists()
                    and not generated_feature_caches
                    and reference_cache_descriptor is not None
                ):
                    cache_payload = reference_cache_output_path.read_bytes()
                    generated_feature_caches = (
                        FeatureCacheArtifact(
                            backend=self.backend,
                            namespace=reference_cache_descriptor.namespace,
                            artifact_version=reference_cache_descriptor.artifact_version,
                            cache_format=reference_cache_descriptor.cache_format,
                            sample_signature=self._build_reference_cache_sample_signature(reference_candidates),
                            config_signature=reference_cache_descriptor.config_signature,
                            checksum=hashlib.sha256(cache_payload).hexdigest(),
                            payload=cache_payload,
                            metadata={
                                **reference_cache_descriptor.metadata,
                                "generated_during_conversion": True,
                                "job_id": job_id,
                            },
                        ),
                    )

                profiling_payload = self._build_profiling_payload(
                    cache_state=cache_state,
                    runtime_validation_ms=runtime_validation_ms,
                    source_preprocessing_ms=source_preprocessing_ms,
                    reference_preprocessing_ms=reference_preprocessing_ms,
                    source_cache_prepare_ms=source_cache_prepare_ms,
                    reference_cache_prepare_ms=reference_cache_prepare_ms,
                    subprocess_duration_ms=subprocess_duration_ms,
                    profiled_metrics=profiled_metrics,
                    log_artifacts=log_artifacts,
                )

                traceability_metadata = {
                    "backend": self.backend.value,
                    "engine": "seed-vc",
                    "job_id": request.job_id,
                    "voice_profile_name": request.voice_profile_name,
                    "readiness_score": request.readiness_score,
                    "clip_count": request.clip_count,
                    "seed_vc": {
                        "repo_dir": str(Path(self.config.repo_dir).expanduser().resolve()),
                        "diffusion_steps": self.config.diffusion_steps,
                        "length_adjust": self.config.length_adjust,
                        "inference_cfg_rate": self.config.inference_cfg_rate,
                        "f0_condition": self.config.f0_condition,
                        "auto_f0_adjust": self.config.auto_f0_adjust,
                        "semi_tone_shift": self.config.semi_tone_shift,
                        "fp16": self.config.fp16,
                        "timeout_seconds": self.config.timeout_seconds,
                    },
                    "preprocessing": {
                        "source": {
                            "sample_rate": prepared_source.metadata.sample_rate,
                            "duration_seconds": prepared_source.metadata.duration_seconds,
                            "trimmed_seconds": prepared_source.trimmed_seconds,
                            "normalized_peak": prepared_source.normalized_peak,
                            "feature_cache": {
                                "enabled": self.config.source_cache_enabled,
                                "selected": selected_source_cache is not None,
                                "generated": source_cache_generated,
                                "artifact_version": source_cache_descriptor.artifact_version
                                if source_cache_descriptor
                                else None,
                                "sample_signature": source_cache_sample_signature,
                                "config_signature": source_cache_descriptor.config_signature
                                if source_cache_descriptor
                                else None,
                                "storage_key": generated_source_cache.storage_key if generated_source_cache else None,
                            },
                        },
                        "reference": {
                            "sample_rate": prepared_reference.metadata.sample_rate,
                            "duration_seconds": prepared_reference.metadata.duration_seconds,
                            "trimmed_seconds": prepared_reference.trimmed_seconds,
                            "normalized_peak": prepared_reference.normalized_peak,
                            "feature_cache": {
                                "enabled": self.config.reference_cache_enabled,
                                "selected": selected_reference_cache is not None,
                                "generated": bool(generated_feature_caches),
                                "artifact_version": reference_cache_descriptor.artifact_version
                                if reference_cache_descriptor
                                else None,
                                "sample_signature": self._build_reference_cache_sample_signature(reference_candidates)
                                if reference_cache_descriptor
                                else None,
                                "config_signature": reference_cache_descriptor.config_signature
                                if reference_cache_descriptor
                                else None,
                            },
                            "reference_candidates": [
                                {
                                    "filename": candidate.filename,
                                    "sample_id": candidate.sample_id,
                                    "storage_key": candidate.storage_key,
                                }
                                for candidate in reference_candidates
                            ],
                        },
                    },
                    "subprocess": {
                        "returncode": completed.returncode,
                        "duration_ms": subprocess_duration_ms,
                        "stdout_log_path": log_artifacts["stdout_log_path"],
                        "stderr_log_path": log_artifacts["stderr_log_path"],
                        "manifest_path": log_artifacts["manifest_path"],
                        "stdout_tail": completed.stdout[-2000:],
                        "stderr_tail": completed.stderr[-2000:],
                    },
                    "profiling": profiling_payload,
                    "temporary_workspace": str(temp_path),
                    "engine_duration_ms": int((time.monotonic() - start_monotonic) * 1000),
                    "watermark_plan": "voiceforge-trace-v1",
                }
                engine_metrics = {
                    "source_audio_duration_ms": int(round(prepared_source.metadata.duration_seconds * 1000)),
                    "reference_audio_duration_ms": int(round(prepared_reference.metadata.duration_seconds * 1000)),
                    "subprocess_duration_ms": subprocess_duration_ms,
                    "source_feature_cache_hit": 1 if source_cache_hit else 0,
                    "reference_feature_cache_hit": 1 if reference_cache_hit else 0,
                    "profiling": profiling_payload,
                }
                self._log_event(
                    "info",
                    "seed_vc_conversion_completed",
                    job_id=job_id,
                    output_path=str(output_file),
                    output_size_bytes=len(output_bytes),
                    source_audio_duration_ms=engine_metrics["source_audio_duration_ms"],
                    reference_audio_duration_ms=engine_metrics["reference_audio_duration_ms"],
                    subprocess_duration_ms=subprocess_duration_ms,
                    runtime_bootstrap_ms=profiling_payload["stages_ms"]["runtime_bootstrap"],
                )
                return ConversionResult(
                    output_bytes=output_bytes,
                    content_type="audio/wav",
                    output_format="wav",
                    traceability_metadata=traceability_metadata,
                    engine_metrics=engine_metrics,
                    generated_feature_caches=generated_feature_caches,
                )
            except SeedVCError:
                raise
            except OSError as exc:
                raise SeedVCError(
                    f"Seed-VC workspace could not be prepared: {exc}",
                    category=STORAGE_FAILED,
                    diagnostics={"workspace": str(temp_path)},
                ) from exc
            finally:
                self._log_event("info", "seed_vc_temp_workspace_cleaned", job_id=job_id, workspace=str(temp_path))

    def _validate_environment(self, *, job_id: str) -> None:
        python_path = shutil.which(self.config.python_executable) or self.config.python_executable
        repo_dir = Path(self.config.repo_dir).expanduser().resolve()
        if not Path(python_path).exists() and shutil.which(self.config.python_executable) is None:
            raise SeedVCConfigurationError(
                "Seed-VC Python executable was not found. Configure VF_SEED_VC_PYTHON with a Python 3.10 runtime.",
                diagnostics={"configured_python": self.config.python_executable},
            )
        if not repo_dir.exists():
            raise SeedVCConfigurationError(
                "Seed-VC repository directory was not found. Configure VF_SEED_VC_REPO_DIR or run infra/scripts/install_seed_vc.ps1.",
                diagnostics={"configured_repo_dir": str(repo_dir)},
            )
        inference_script = repo_dir / "inference.py"
        if not inference_script.exists():
            raise SeedVCConfigurationError(
                f"Seed-VC inference.py was not found in {repo_dir}.",
                diagnostics={"configured_repo_dir": str(repo_dir)},
            )
        if self._runtime_verified:
            return

        command = [
            self.config.python_executable,
            "-c",
            (
                "import platform, torch, torchaudio; "
                "print(platform.python_version()); "
                "print(torch.__version__); "
                "print(torchaudio.__version__)"
            ),
        ]
        completed, log_artifacts = self._run_validation_command(
            job_id=job_id,
            command=command,
            env=self._build_environment(),
            timeout_seconds=min(60, self.config.timeout_seconds),
        )
        if completed.returncode != 0:
            raise SeedVCConfigurationError(
                "Seed-VC runtime is present but required dependencies are missing or broken. "
                "Install the upstream environment with infra/scripts/install_seed_vc.ps1.",
                diagnostics={
                    "stdout_log_path": log_artifacts["stdout_log_path"],
                    "stderr_log_path": log_artifacts["stderr_log_path"],
                    "manifest_path": log_artifacts["manifest_path"],
                },
            )
        self._runtime_verified = True
        self._log_event(
            "info",
            "seed_vc_runtime_validated",
            job_id=job_id,
            python=self.config.python_executable,
            repo_dir=str(repo_dir),
            stdout_log_path=log_artifacts["stdout_log_path"],
        )

    def _select_reference_candidates(self, request: ConversionRequest) -> tuple[ReferenceAudioCandidate, ...]:
        if request.reference_audio_candidates:
            candidates = request.reference_audio_candidates[: self.config.reference_clip_limit]
        elif request.reference_audio_bytes and request.reference_audio_filename:
            candidates = (
                ReferenceAudioCandidate(
                    filename=request.reference_audio_filename,
                    content_type=request.reference_audio_content_type or "audio/wav",
                    payload=request.reference_audio_bytes,
                ),
            )
        else:
            raise SeedVCInvalidReferenceError("No reference audio was provided to the Seed-VC adapter.")

        non_empty = tuple(candidate for candidate in candidates if candidate.payload)
        if not non_empty:
            raise SeedVCInvalidReferenceError("All provided reference audio files are empty.")
        return non_empty

    def _build_command(
        self,
        *,
        source_path: Path,
        reference_path: Path,
        output_dir: Path,
        metrics_output_path: Path,
        source_cache_input_path: Path | None,
        source_cache_output_path: Path | None,
        reference_cache_input_path: Path | None,
        reference_cache_output_path: Path | None,
    ) -> list[str]:
        command = [
            self.config.python_executable,
            "-m",
            PROFILED_RUNNER_MODULE,
            "--source",
            str(source_path),
            "--target",
            str(reference_path),
            "--output",
            str(output_dir),
            "--diffusion-steps",
            str(self.config.diffusion_steps),
            "--length-adjust",
            str(self.config.length_adjust),
            "--inference-cfg-rate",
            str(self.config.inference_cfg_rate),
            "--f0-condition",
            str(self.config.f0_condition).lower(),
            "--auto-f0-adjust",
            str(self.config.auto_f0_adjust).lower(),
            "--semi-tone-shift",
            str(self.config.semi_tone_shift),
            "--fp16",
            str(self.config.fp16).lower(),
            "--voiceforge-metrics-output",
            str(metrics_output_path),
        ]
        if source_cache_input_path is not None:
            command.extend(["--source-cache-input", str(source_cache_input_path)])
        if source_cache_output_path is not None:
            command.extend(["--source-cache-output", str(source_cache_output_path)])
        if reference_cache_input_path is not None:
            command.extend(["--reference-cache-input", str(reference_cache_input_path)])
        if reference_cache_output_path is not None:
            command.extend(["--reference-cache-output", str(reference_cache_output_path)])
        if self.config.checkpoint_path:
            command.extend(["--checkpoint", self.config.checkpoint_path])
        if self.config.config_path:
            command.extend(["--config", self.config.config_path])
        return command

    def _build_environment(self) -> dict[str, str]:
        env = os.environ.copy()
        repo_dir = Path(self.config.repo_dir).expanduser().resolve()
        core_src = Path(__file__).resolve().parents[2]
        working_root = self._working_root()
        working_root.mkdir(parents=True, exist_ok=True)
        env["PYTHONIOENCODING"] = "utf-8"
        env["HF_HUB_CACHE"] = str(working_root / "hf_cache")
        env["HF_HOME"] = str(working_root / "hf_home")
        env["TRANSFORMERS_CACHE"] = str(working_root / "hf_cache")
        if self.config.hf_endpoint:
            env["HF_ENDPOINT"] = self.config.hf_endpoint
        python_paths = [str(core_src), str(repo_dir)]
        existing_pythonpath = env.get("PYTHONPATH")
        if existing_pythonpath:
            python_paths.append(existing_pythonpath)
        env["PYTHONPATH"] = os.pathsep.join(python_paths)
        return env

    def _run_validation_command(
        self,
        *,
        job_id: str,
        command: list[str],
        env: dict[str, str],
        timeout_seconds: int,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, str]]:
        repo_dir = Path(self.config.repo_dir).expanduser().resolve()
        try:
            completed = subprocess.run(
                command,
                cwd=repo_dir,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            log_artifacts = self._persist_subprocess_logs(
                job_id=job_id,
                command=command,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
                returncode=None,
                context={"timeout_seconds": timeout_seconds, "phase": "runtime_validation", "timed_out": True},
            )
            raise SeedVCConfigurationError(
                "Seed-VC runtime validation timed out. Verify the configured Python environment is healthy.",
                diagnostics=log_artifacts,
            ) from exc
        except OSError as exc:
            raise SeedVCConfigurationError(
                f"Seed-VC runtime validation could not start: {exc}",
                diagnostics={"configured_python": self.config.python_executable},
            ) from exc

        log_artifacts = self._persist_subprocess_logs(
            job_id=job_id,
            command=command,
            stdout=completed.stdout,
            stderr=completed.stderr,
            returncode=completed.returncode,
            context={"phase": "runtime_validation"},
        )
        return completed, log_artifacts

    def _run_seed_vc(
        self,
        *,
        job_id: str,
        command: list[str],
        env: dict[str, str],
        metrics_output_path: Path,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, str], int, dict]:
        repo_dir = Path(self.config.repo_dir).expanduser().resolve()
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                cwd=repo_dir,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.config.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            duration_ms = int((time.monotonic() - started) * 1000)
            profiling_payload = self._read_profile_metrics(metrics_output_path)
            log_artifacts = self._persist_subprocess_logs(
                job_id=job_id,
                command=command,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
                returncode=None,
                context={"timeout_seconds": self.config.timeout_seconds, "duration_ms": duration_ms, "timed_out": True},
            )
            raise SeedVCInferenceError(
                f"Seed-VC exceeded the configured timeout of {self.config.timeout_seconds} seconds.",
                diagnostics={**log_artifacts, "duration_ms": duration_ms, "profiling": profiling_payload},
            ) from exc
        except OSError as exc:
            raise SeedVCInferenceError(
                f"Seed-VC process could not be launched: {exc}",
                diagnostics={"configured_python": self.config.python_executable},
            ) from exc

        duration_ms = int((time.monotonic() - started) * 1000)
        profiled_metrics = self._read_profile_metrics(metrics_output_path)
        log_artifacts = self._persist_subprocess_logs(
            job_id=job_id,
            command=command,
            stdout=completed.stdout,
            stderr=completed.stderr,
            returncode=completed.returncode,
            context={"timeout_seconds": self.config.timeout_seconds, "duration_ms": duration_ms, "phase": "inference"},
        )

        if completed.returncode != 0:
            raise SeedVCInferenceError(
                "Seed-VC inference failed. Inspect the captured stdout/stderr logs for the upstream error.",
                diagnostics={
                    **log_artifacts,
                    "returncode": completed.returncode,
                    "duration_ms": duration_ms,
                    "profiling": profiled_metrics,
                },
            )
        return completed, log_artifacts, duration_ms, profiled_metrics

    def _persist_subprocess_logs(
        self,
        *,
        job_id: str,
        command: list[str],
        stdout: str,
        stderr: str,
        returncode: int | None,
        context: dict,
    ) -> dict[str, str]:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        log_dir = self._working_root() / "logs" / job_id / timestamp
        log_dir.mkdir(parents=True, exist_ok=True)
        stdout_path = log_dir / "stdout.log"
        stderr_path = log_dir / "stderr.log"
        manifest_path = log_dir / "run.json"
        stdout_path.write_text(stdout or "", encoding="utf-8")
        stderr_path.write_text(stderr or "", encoding="utf-8")
        manifest_path.write_text(
            json.dumps(
                {
                    "command": command,
                    "returncode": returncode,
                    "repo_dir": str(Path(self.config.repo_dir).expanduser().resolve()),
                    "context": context,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        self._log_event(
            "info",
            "seed_vc_subprocess_logs_persisted",
            job_id=job_id,
            stdout_log_path=str(stdout_path),
            stderr_log_path=str(stderr_path),
            manifest_path=str(manifest_path),
            returncode=returncode,
        )
        return {
            "log_dir": str(log_dir),
            "stdout_log_path": str(stdout_path),
            "stderr_log_path": str(stderr_path),
            "manifest_path": str(manifest_path),
        }

    def _resolve_output_file(self, output_dir: Path) -> Path:
        candidates = sorted(output_dir.glob("*.wav"), key=lambda item: item.stat().st_mtime, reverse=True)
        if not candidates:
            raise SeedVCInferenceError("Seed-VC finished without producing an output WAV file.")
        return candidates[0]

    def _working_root(self) -> Path:
        return Path(self.config.working_root).expanduser().resolve()

    def _read_profile_metrics(self, metrics_output_path: Path) -> dict:
        if not metrics_output_path.exists():
            return {}
        try:
            return json.loads(metrics_output_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def _has_warm_cache(self) -> bool:
        cache_candidates = [
            self._working_root() / "hf_cache",
            self._working_root() / "hf_home",
            Path(self.config.repo_dir).expanduser().resolve() / "checkpoints" / "hf_cache",
        ]
        for candidate in cache_candidates:
            if candidate.exists():
                try:
                    if any(candidate.iterdir()):
                        return True
                except OSError:
                    continue
        return False

    def _build_source_cache_config_signature(self) -> str:
        payload = {
            "artifact_version": SOURCE_CACHE_ARTIFACT_VERSION,
            "target_sample_rate": self.config.target_sample_rate,
            "f0_condition": self.config.f0_condition,
            "checkpoint_path": self.config.checkpoint_path,
            "config_path": self.config.config_path,
            "repo_dir": str(Path(self.config.repo_dir).expanduser().resolve()),
            "preprocessor": {
                "trim_top_db": self.preprocessor.trim_top_db,
                "target_peak": self.preprocessor.target_peak,
                "frame_length": self.preprocessor.frame_length,
                "hop_length": self.preprocessor.hop_length,
            },
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    def _build_reference_cache_config_signature(self) -> str:
        payload = {
            "artifact_version": REFERENCE_CACHE_ARTIFACT_VERSION,
            "target_sample_rate": self.config.target_sample_rate,
            "reference_max_seconds": self.config.reference_max_seconds,
            "reference_clip_limit": self.config.reference_clip_limit,
            "f0_condition": self.config.f0_condition,
            "checkpoint_path": self.config.checkpoint_path,
            "config_path": self.config.config_path,
            "repo_dir": str(Path(self.config.repo_dir).expanduser().resolve()),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    def _build_source_cache_sample_signature(self, request: ConversionRequest) -> str:
        payload = {
            "source_filename": request.source_filename,
            "source_sha256": hashlib.sha256(request.source_audio_bytes).hexdigest(),
            "source_content_type": request.source_content_type,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    def _build_reference_cache_sample_signature(
        self,
        reference_candidates: tuple[ReferenceAudioCandidate, ...],
    ) -> str:
        normalized = [
            {
                "sample_id": candidate.sample_id,
                "storage_key": candidate.storage_key,
                "waveform_hash": candidate.waveform_hash,
                "filename": candidate.filename,
            }
            for candidate in reference_candidates
        ]
        return hashlib.sha256(
            json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    def _select_local_feature_cache(
        self,
        *,
        descriptor: FeatureCacheDescriptor | None,
        sample_signature: str | None,
    ) -> FeatureCacheReference | None:
        if descriptor is None or sample_signature is None:
            return None
        return self._local_feature_cache_store.resolve(
            descriptor=descriptor,
            sample_signature=sample_signature,
        )

    def _select_reference_feature_cache(
        self,
        request: ConversionRequest,
        *,
        descriptor: FeatureCacheDescriptor | None,
    ) -> FeatureCacheReference | None:
        if descriptor is None:
            return None
        for candidate in request.reference_feature_caches:
            if candidate.backend != self.backend:
                continue
            if candidate.namespace != descriptor.namespace:
                continue
            if candidate.artifact_version != descriptor.artifact_version:
                continue
            if candidate.config_signature != descriptor.config_signature:
                continue
            return candidate
        return None

    def _build_reference_cache_via_resident_runtime(
        self,
        *,
        job_id: str,
        prepared_reference_path: Path,
        artifact_path: Path,
    ) -> dict:
        runtime_state = self._ensure_reference_cache_runtime(job_id=job_id)
        response = self._send_reference_runtime_request(
            state=runtime_state,
            payload={
                "action": "build_reference_cache",
                "job_id": job_id,
                "input_path": str(prepared_reference_path),
                "output_path": str(artifact_path),
                "f0_condition": self.config.f0_condition,
            },
            timeout_seconds=self.config.timeout_seconds,
        )
        if response.get("status") != "ok":
            raise SeedVCInferenceError(
                "Seed-VC resident reference runtime failed to build the reference cache.",
                diagnostics=response,
            )
        if not artifact_path.exists():
            raise SeedVCInferenceError(
                "Seed-VC resident reference runtime reported success but did not produce a cache artifact.",
                diagnostics=response,
            )
        return response

    def _build_source_cache_via_resident_runtime(
        self,
        *,
        job_id: str,
        prepared_source_path: Path,
        artifact_path: Path,
    ) -> dict:
        runtime_state = self._ensure_reference_cache_runtime(job_id=job_id)
        response = self._send_reference_runtime_request(
            state=runtime_state,
            payload={
                "action": "build_source_cache",
                "job_id": job_id,
                "input_path": str(prepared_source_path),
                "output_path": str(artifact_path),
                "f0_condition": self.config.f0_condition,
            },
            timeout_seconds=self.config.timeout_seconds,
        )
        if response.get("status") != "ok":
            raise SeedVCInferenceError(
                "Seed-VC resident runtime failed to build the source cache.",
                diagnostics=response,
            )
        if not artifact_path.exists():
            raise SeedVCInferenceError(
                "Seed-VC resident runtime reported success but did not produce a source cache artifact.",
                diagnostics=response,
            )
        return response

    def _ensure_reference_cache_runtime(self, *, job_id: str) -> dict[str, object]:
        existing = self._read_reference_runtime_state()
        if existing is not None and self._ping_reference_runtime(existing):
            return existing

        state_file = self._reference_runtime_state_file()
        state_file.parent.mkdir(parents=True, exist_ok=True)
        if state_file.exists():
            try:
                state_file.unlink()
            except OSError:
                pass

        logs_dir = self._working_root() / "resident-runtime" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        launch_timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        stdout_path = logs_dir / f"{launch_timestamp}_stdout.log"
        stderr_path = logs_dir / f"{launch_timestamp}_stderr.log"
        command = self._build_reference_runtime_command(state_file=state_file)
        with stdout_path.open("a", encoding="utf-8") as stdout_handle, stderr_path.open(
            "a", encoding="utf-8"
        ) as stderr_handle:
            try:
                subprocess.Popen(
                    command,
                    cwd=Path(self.config.repo_dir).expanduser().resolve(),
                    env=self._build_environment(),
                    stdout=stdout_handle,
                    stderr=stderr_handle,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
            except OSError as exc:
                raise SeedVCConfigurationError(
                    f"Seed-VC resident runtime could not be launched: {exc}",
                    diagnostics={
                        "command": command,
                        "stdout_log_path": str(stdout_path),
                        "stderr_log_path": str(stderr_path),
                    },
                ) from exc

        started = time.monotonic()
        while time.monotonic() - started < self.config.resident_runtime_launch_timeout_seconds:
            runtime_state = self._read_reference_runtime_state()
            if runtime_state is not None and self._ping_reference_runtime(runtime_state):
                runtime_state["stdout_log_path"] = str(stdout_path)
                runtime_state["stderr_log_path"] = str(stderr_path)
                self._log_event(
                    "info",
                    "seed_vc_resident_runtime_ready",
                    job_id=job_id,
                    host=runtime_state.get("host"),
                    port=runtime_state.get("port"),
                    pid=runtime_state.get("pid"),
                )
                return runtime_state
            time.sleep(0.5)

        raise SeedVCConfigurationError(
            "Seed-VC resident runtime did not become ready before the launch timeout expired.",
            diagnostics={
                "state_file": str(state_file),
                "stdout_log_path": str(stdout_path),
                "stderr_log_path": str(stderr_path),
                "timeout_seconds": self.config.resident_runtime_launch_timeout_seconds,
            },
        )

    def _build_reference_runtime_command(self, *, state_file: Path) -> list[str]:
        command = [
            self.config.python_executable,
            "-m",
            REFERENCE_CACHE_RUNTIME_MODULE,
            "--state-file",
            str(state_file),
            "--working-root",
            str(self._working_root()),
            "--idle-timeout-seconds",
            str(self.config.resident_runtime_idle_seconds),
            "--f0-condition",
            str(self.config.f0_condition).lower(),
        ]
        if self.config.checkpoint_path:
            command.extend(["--checkpoint", self.config.checkpoint_path])
        if self.config.config_path:
            command.extend(["--config", self.config.config_path])
        return command

    def _reference_runtime_state_file(self) -> Path:
        state_dir = self._working_root() / "resident-runtime"
        state_key = hashlib.sha256(
            json.dumps(
                {
                    "repo_dir": str(Path(self.config.repo_dir).expanduser().resolve()),
                    "checkpoint_path": self.config.checkpoint_path,
                    "config_path": self.config.config_path,
                    "f0_condition": self.config.f0_condition,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()[:16]
        return state_dir / f"{state_key}.json"

    def _read_reference_runtime_state(self) -> dict[str, object] | None:
        state_file = self._reference_runtime_state_file()
        if not state_file.exists():
            return None
        try:
            payload = json.loads(state_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not payload.get("host") or not payload.get("port"):
            return None
        return payload

    def _ping_reference_runtime(self, state: dict[str, object]) -> bool:
        try:
            response = self._send_reference_runtime_request(
                state=state,
                payload={"action": "ping"},
                timeout_seconds=2,
            )
        except SeedVCConfigurationError:
            return False
        return response.get("status") == "ok"

    def _send_reference_runtime_request(
        self,
        *,
        state: dict[str, object],
        payload: dict[str, object],
        timeout_seconds: int | None = None,
    ) -> dict[str, object]:
        host = str(state.get("host") or "127.0.0.1")
        port = int(state.get("port") or 0)
        if port <= 0:
            raise SeedVCConfigurationError("Seed-VC resident runtime state is missing a valid TCP port.")
        client_timeout = float(timeout_seconds or min(self.config.timeout_seconds, 120))
        try:
            with socket.create_connection((host, port), timeout=client_timeout) as connection:
                connection.settimeout(client_timeout)
                connection.sendall((json.dumps(payload) + "\n").encode("utf-8"))
                buffer = b""
                while b"\n" not in buffer:
                    chunk = connection.recv(65536)
                    if not chunk:
                        break
                    buffer += chunk
        except OSError as exc:
            raise SeedVCConfigurationError(
                f"Seed-VC resident runtime request failed: {exc}",
                diagnostics={"host": host, "port": port, "payload": payload},
            ) from exc
        line = buffer.splitlines()[0] if buffer else b""
        if not line:
            raise SeedVCConfigurationError(
                "Seed-VC resident runtime returned an empty response.",
                diagnostics={"host": host, "port": port, "payload": payload},
            )
        try:
            return json.loads(line.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise SeedVCConfigurationError(
                "Seed-VC resident runtime returned invalid JSON.",
                diagnostics={"host": host, "port": port, "raw_response": line.decode("utf-8", errors="replace")},
            ) from exc

    def _build_profiling_payload(
        self,
        *,
        cache_state: str,
        runtime_validation_ms: int,
        source_preprocessing_ms: int,
        reference_preprocessing_ms: int,
        source_cache_prepare_ms: int,
        reference_cache_prepare_ms: int,
        subprocess_duration_ms: int,
        profiled_metrics: dict,
        log_artifacts: dict[str, str],
    ) -> dict:
        subprocess_stages = profiled_metrics.get("stages_ms", {})
        subprocess_details = profiled_metrics.get("details_ms", {})
        runtime_bootstrap_total = runtime_validation_ms + int(subprocess_stages.get("runtime_bootstrap", 0))
        source_feature_ms = (
            int(subprocess_details.get("source_cache_load", 0))
            + int(subprocess_details.get("source_semantic_extraction", 0))
            + int(subprocess_details.get("source_mel_extraction", 0))
            + int(subprocess_details.get("source_f0_extraction", 0))
        )
        reference_feature_ms = (
            int(subprocess_details.get("reference_cache_load", 0))
            + int(subprocess_details.get("reference_semantic_extraction", 0))
            + int(subprocess_details.get("reference_mel_extraction", 0))
            + int(subprocess_details.get("reference_style_extraction", 0))
            + int(subprocess_details.get("reference_f0_alignment", 0))
            + int(subprocess_details.get("reference_f0_extraction", 0))
        )
        return {
            "cache_state_before_run": cache_state,
            "status": profiled_metrics.get("status", "completed"),
            "stages_ms": {
                "runtime_bootstrap": runtime_bootstrap_total,
                "source_preprocessing": source_cache_prepare_ms + source_preprocessing_ms + source_feature_ms,
                "reference_preprocessing": reference_cache_prepare_ms + reference_preprocessing_ms + reference_feature_ms,
                "model_invocation": int(subprocess_stages.get("model_invocation", 0)),
                "inference_core": int(subprocess_stages.get("inference_core", 0)),
                "vocoder_postprocess": int(subprocess_stages.get("vocoder_postprocess", 0)),
            },
            "details_ms": {
                "adapter_source_preprocessing": source_preprocessing_ms,
                "adapter_reference_preprocessing": reference_preprocessing_ms,
                "source_cache_prepare": source_cache_prepare_ms,
                "reference_cache_prepare": reference_cache_prepare_ms,
                "runtime_validation": runtime_validation_ms,
                "subprocess_runtime_bootstrap": int(subprocess_stages.get("runtime_bootstrap", 0)),
                "subprocess_total": subprocess_duration_ms,
                **subprocess_details,
            },
            "resources": profiled_metrics.get("resources", {}),
            "artifacts": {
                **profiled_metrics.get("artifacts", {}),
                "stdout_log_path": log_artifacts["stdout_log_path"],
                "stderr_log_path": log_artifacts["stderr_log_path"],
                "manifest_path": log_artifacts["manifest_path"],
            },
        }

    def _log_event(self, level: str, event: str, **payload: object) -> None:
        message = json.dumps({"event": event, **payload}, default=str)
        getattr(logger, level)(message)
