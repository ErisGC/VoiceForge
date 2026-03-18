from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AudioSegment:
    start_seconds: float
    end_seconds: float


@dataclass(slots=True)
class AudioMetadata:
    duration_seconds: float
    sample_rate: int
    channels: int
    format: str
    size_bytes: int


@dataclass(slots=True)
class PreparedAudioArtifact:
    path: Path
    metadata: AudioMetadata
    trimmed_seconds: float
    normalized_peak: float


@dataclass(slots=True)
class PreprocessingResult:
    metadata: AudioMetadata
    normalized_lufs: float
    noise_score: float
    diversity_score: float
    vad_segments: list[AudioSegment]


@dataclass(slots=True)
class DatasetQualityMetrics:
    total_duration_seconds: float
    clip_count: int
    noise_score: float
    diversity_score: float
    sample_rate: int

    def readiness_score(self) -> float:
        duration_component = min(self.total_duration_seconds / 180.0, 1.0) * 35.0
        clips_component = min(self.clip_count / 20.0, 1.0) * 20.0
        cleanliness_component = max(0.0, 1.0 - self.noise_score) * 20.0
        diversity_component = min(max(self.diversity_score, 0.0), 1.0) * 15.0
        sample_rate_component = min(self.sample_rate / 48000.0, 1.0) * 10.0
        return round(
            duration_component
            + clips_component
            + cleanliness_component
            + diversity_component
            + sample_rate_component,
            2,
        )


class AudioPreprocessor(ABC):
    @abstractmethod
    def process(self, file_path: str, size_bytes: int) -> PreprocessingResult:
        raise NotImplementedError
