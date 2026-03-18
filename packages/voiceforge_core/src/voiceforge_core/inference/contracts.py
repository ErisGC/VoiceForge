from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from voiceforge_core.db.enums import ConversionMode, EngineBackend


@dataclass(slots=True)
class EmbeddingArtifact:
    backend_name: str
    embedding_version: str
    dimension: int
    checksum: str
    vector: list[float]
    metadata: dict


@dataclass(slots=True)
class ConversionRequest:
    backend: EngineBackend
    mode: ConversionMode
    source_audio_bytes: bytes
    source_filename: str
    source_content_type: str
    voice_profile_name: str
    readiness_score: float
    clip_count: int
    reference_audio_bytes: bytes | None = None
    reference_audio_filename: str | None = None
    reference_audio_content_type: str | None = None
    reference_audio_candidates: tuple["ReferenceAudioCandidate", ...] = ()
    reference_feature_caches: tuple["FeatureCacheReference", ...] = ()
    voice_profile_id: str | None = None
    job_id: str | None = None


@dataclass(slots=True)
class ReferenceAudioCandidate:
    filename: str
    content_type: str
    payload: bytes
    sample_id: str | None = None
    storage_key: str | None = None
    waveform_hash: str | None = None


@dataclass(slots=True)
class FeatureCacheDescriptor:
    backend: EngineBackend
    namespace: str
    artifact_version: str
    cache_format: str
    config_signature: str
    metadata: dict


@dataclass(slots=True)
class FeatureCacheReference:
    backend: EngineBackend
    namespace: str
    artifact_version: str
    cache_format: str
    sample_signature: str
    config_signature: str
    checksum: str
    payload: bytes
    metadata: dict
    storage_bucket: str | None = None
    storage_key: str | None = None


@dataclass(slots=True)
class FeatureCacheArtifact:
    backend: EngineBackend
    namespace: str
    artifact_version: str
    cache_format: str
    sample_signature: str
    config_signature: str
    checksum: str
    payload: bytes
    metadata: dict


@dataclass(slots=True)
class ConversionResult:
    output_bytes: bytes
    content_type: str
    output_format: str
    traceability_metadata: dict
    engine_metrics: dict | None = None
    generated_feature_caches: tuple[FeatureCacheArtifact, ...] = ()


class SpeakerEmbeddingService(ABC):
    @abstractmethod
    def extract(self, audio_bytes: bytes, sample_rate: int) -> EmbeddingArtifact:
        raise NotImplementedError


class VoiceConversionEngine(ABC):
    backend: EngineBackend

    @abstractmethod
    def convert(self, request: ConversionRequest) -> ConversionResult:
        raise NotImplementedError

    def describe_reference_feature_cache(self, request: ConversionRequest) -> FeatureCacheDescriptor | None:
        return None

    def prepare_reference_feature_cache(
        self,
        request: ConversionRequest,
    ) -> tuple[FeatureCacheArtifact, ...]:
        return ()
