from __future__ import annotations

import hashlib
import json
import math

from voiceforge_core.audio.pipeline import WaveAudioPreprocessor
from voiceforge_core.db.enums import EngineBackend
from voiceforge_core.inference.contracts import (
    ConversionRequest,
    ConversionResult,
    EmbeddingArtifact,
    SpeakerEmbeddingService,
    VoiceConversionEngine,
)
from voiceforge_core.inference.seed_vc import SeedVCBackendConfig, SeedVCVoiceConversionEngine


class HashSpeakerEmbeddingService(SpeakerEmbeddingService):
    def extract(self, audio_bytes: bytes, sample_rate: int) -> EmbeddingArtifact:
        digest = hashlib.sha256(audio_bytes).digest()
        raw = [((digest[index % len(digest)] / 255.0) * 2.0) - 1.0 for index in range(32)]
        norm = math.sqrt(sum(value * value for value in raw)) or 1.0
        vector = [round(value / norm, 6) for value in raw]
        checksum = hashlib.sha256(json.dumps(vector).encode("utf-8")).hexdigest()
        return EmbeddingArtifact(
            backend_name="hash-speaker-embedding",
            embedding_version="0.1.0",
            dimension=len(vector),
            checksum=checksum,
            vector=vector,
            metadata={"sample_rate": sample_rate, "strategy": "sha256_projection"},
        )


class PlaceholderVoiceConversionEngine(VoiceConversionEngine):
    def __init__(self, backend: EngineBackend) -> None:
        self.backend = backend

    def convert(self, request: ConversionRequest) -> ConversionResult:
        traceability_metadata = {
            "backend": self.backend.value,
            "mode": request.mode.value,
            "voice_profile_name": request.voice_profile_name,
            "readiness_score": request.readiness_score,
            "clip_count": request.clip_count,
            "implementation": "placeholder",
            "watermark_plan": "voiceforge-trace-v1",
        }
        source_format = request.source_filename.split(".")[-1].lower() if "." in request.source_filename else "wav"
        return ConversionResult(
            output_bytes=request.source_audio_bytes,
            content_type=request.source_content_type,
            output_format=source_format,
            traceability_metadata=traceability_metadata,
        )


class ModelRegistry:
    def __init__(self) -> None:
        self._engines: dict[EngineBackend, VoiceConversionEngine] = {}

    def register(self, engine: VoiceConversionEngine) -> None:
        self._engines[engine.backend] = engine

    def resolve(self, backend: EngineBackend) -> VoiceConversionEngine:
        if backend not in self._engines:
            raise KeyError(f"Backend not registered: {backend}")
        return self._engines[backend]


def build_default_model_registry(
    *,
    seed_vc_config: SeedVCBackendConfig,
    preprocessor: WaveAudioPreprocessor,
) -> ModelRegistry:
    registry = ModelRegistry()
    registry.register(SeedVCVoiceConversionEngine(config=seed_vc_config, preprocessor=preprocessor))
    registry.register(PlaceholderVoiceConversionEngine(EngineBackend.RVC))
    registry.register(PlaceholderVoiceConversionEngine(EngineBackend.OPENVOICE))
    return registry
