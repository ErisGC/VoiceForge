from __future__ import annotations

import math
from collections import Counter
from pathlib import Path
from statistics import mean, pstdev

import librosa
import numpy as np
import soundfile as sf

from voiceforge_core.audio.contracts import (
    AudioMetadata,
    AudioPreprocessor,
    AudioSegment,
    DatasetQualityMetrics,
    PreparedAudioArtifact,
    PreprocessingResult,
)


class AudioProcessingError(ValueError):
    """Raised when an audio asset cannot be decoded or prepared safely."""


class WaveAudioPreprocessor(AudioPreprocessor):
    """Real preprocessing for offline workflows and Seed-VC preparation."""

    def __init__(
        self,
        *,
        trim_top_db: float = 35.0,
        target_peak: float = 0.95,
        frame_length: int = 2048,
        hop_length: int = 512,
        reference_pause_ms: int = 200,
    ) -> None:
        self.trim_top_db = trim_top_db
        self.target_peak = target_peak
        self.frame_length = frame_length
        self.hop_length = hop_length
        self.reference_pause_ms = reference_pause_ms

    def process(self, file_path: str, size_bytes: int) -> PreprocessingResult:
        waveform, sample_rate = load_audio(file_path)
        mono = to_mono(waveform)
        trimmed, trimmed_seconds = trim_silence(
            mono,
            sample_rate=sample_rate,
            top_db=self.trim_top_db,
            frame_length=self.frame_length,
            hop_length=self.hop_length,
        )
        normalized, normalized_peak = normalize_audio(trimmed, target_peak=self.target_peak)
        metadata = AudioMetadata(
            duration_seconds=round(normalized.shape[-1] / sample_rate, 3),
            sample_rate=sample_rate,
            channels=1,
            format=Path(file_path).suffix.lower().lstrip(".") or "wav",
            size_bytes=size_bytes,
        )
        vad_segments = build_vad_segments(
            normalized,
            sample_rate=sample_rate,
            frame_length=self.frame_length,
            hop_length=self.hop_length,
        )
        return PreprocessingResult(
            metadata=metadata,
            normalized_lufs=estimate_lufs(normalized),
            noise_score=estimate_noise_score(mono, normalized),
            diversity_score=estimate_diversity_score(normalized, sample_rate, vad_segments),
            vad_segments=vad_segments,
        )

    def prepare_for_seed_vc(
        self,
        *,
        input_path: str | Path,
        output_path: str | Path,
        target_sample_rate: int,
        max_duration_seconds: float | None = None,
    ) -> PreparedAudioArtifact:
        waveform, sample_rate = load_audio(str(input_path))
        mono = to_mono(waveform)
        trimmed, trimmed_seconds = trim_silence(
            mono,
            sample_rate=sample_rate,
            top_db=self.trim_top_db,
            frame_length=self.frame_length,
            hop_length=self.hop_length,
        )
        if max_duration_seconds is not None:
            max_samples = int(target_sample_rate * max_duration_seconds)
        else:
            max_samples = None
        processed = resample_audio(trimmed, orig_sr=sample_rate, target_sr=target_sample_rate)
        if max_samples is not None:
            processed = processed[:max_samples]
        normalized, normalized_peak = normalize_audio(processed, target_peak=self.target_peak)
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        sf.write(output, normalized, target_sample_rate, subtype="PCM_16")
        metadata = AudioMetadata(
            duration_seconds=round(normalized.shape[-1] / target_sample_rate, 3),
            sample_rate=target_sample_rate,
            channels=1,
            format="wav",
            size_bytes=output.stat().st_size,
        )
        return PreparedAudioArtifact(
            path=output,
            metadata=metadata,
            trimmed_seconds=trimmed_seconds,
            normalized_peak=normalized_peak,
        )

    def prepare_reference_prompt(
        self,
        *,
        input_paths: list[str | Path],
        output_path: str | Path,
        target_sample_rate: int,
        max_duration_seconds: float = 25.0,
    ) -> PreparedAudioArtifact:
        if not input_paths:
            raise ValueError("At least one reference audio path is required for Seed-VC.")

        pause = np.zeros(int(target_sample_rate * self.reference_pause_ms / 1000.0), dtype=np.float32)
        max_samples = int(target_sample_rate * max_duration_seconds)
        prepared_segments: list[np.ndarray] = []
        total_samples = 0
        trimmed_seconds_total = 0.0
        last_peak = 0.0

        for input_path in input_paths:
            waveform, sample_rate = load_audio(str(input_path))
            mono = to_mono(waveform)
            trimmed, trimmed_seconds = trim_silence(
                mono,
                sample_rate=sample_rate,
                top_db=self.trim_top_db,
                frame_length=self.frame_length,
                hop_length=self.hop_length,
            )
            resampled = resample_audio(trimmed, orig_sr=sample_rate, target_sr=target_sample_rate)
            normalized, last_peak = normalize_audio(resampled, target_peak=self.target_peak)
            remaining = max_samples - total_samples
            if remaining <= 0:
                break
            if normalized.shape[-1] > remaining:
                normalized = normalized[:remaining]
            if normalized.size == 0:
                continue
            prepared_segments.append(normalized)
            total_samples += normalized.shape[-1]
            trimmed_seconds_total += trimmed_seconds
            if total_samples < max_samples:
                prepared_segments.append(pause[: max_samples - total_samples])
                total_samples += min(pause.shape[-1], max_samples - total_samples)

        if not prepared_segments:
            raise ValueError("Reference audio preparation produced an empty prompt.")

        prompt = np.concatenate(prepared_segments)[:max_samples]
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        sf.write(output, prompt, target_sample_rate, subtype="PCM_16")
        metadata = AudioMetadata(
            duration_seconds=round(prompt.shape[-1] / target_sample_rate, 3),
            sample_rate=target_sample_rate,
            channels=1,
            format="wav",
            size_bytes=output.stat().st_size,
        )
        return PreparedAudioArtifact(
            path=output,
            metadata=metadata,
            trimmed_seconds=round(trimmed_seconds_total, 3),
            normalized_peak=last_peak,
        )


# Backward compatible alias for the runtime created in the first scaffold.
HeuristicAudioPreprocessor = WaveAudioPreprocessor


def load_audio(file_path: str) -> tuple[np.ndarray, int]:
    path = Path(file_path)
    try:
        waveform, sample_rate = sf.read(path, dtype="float32", always_2d=True)
        return waveform.T, int(sample_rate)
    except RuntimeError:
        try:
            waveform, sample_rate = librosa.load(path, sr=None, mono=False)
            if waveform.ndim == 1:
                waveform = np.expand_dims(waveform, axis=0)
            return waveform.astype(np.float32), int(sample_rate)
        except Exception as exc:
            raise AudioProcessingError(
                f"Audio file '{path.name}' could not be decoded. Validate the format and file integrity."
            ) from exc


def to_mono(waveform: np.ndarray) -> np.ndarray:
    if waveform.ndim == 1:
        mono = waveform
    elif waveform.shape[0] == 1:
        mono = waveform[0]
    else:
        mono = np.mean(waveform, axis=0)
    return np.asarray(mono, dtype=np.float32)


def trim_silence(
    waveform: np.ndarray,
    *,
    sample_rate: int,
    top_db: float,
    frame_length: int,
    hop_length: int,
) -> tuple[np.ndarray, float]:
    if waveform.size == 0:
        return waveform, 0.0
    trimmed, index = librosa.effects.trim(
        waveform,
        top_db=top_db,
        frame_length=frame_length,
        hop_length=hop_length,
    )
    if trimmed.size == 0:
        return waveform, 0.0
    removed_seconds = max(0.0, (waveform.shape[-1] - trimmed.shape[-1]) / sample_rate)
    return trimmed.astype(np.float32), round(removed_seconds, 3)


def normalize_audio(waveform: np.ndarray, *, target_peak: float) -> tuple[np.ndarray, float]:
    if waveform.size == 0:
        return waveform.astype(np.float32), 0.0
    peak = float(np.max(np.abs(waveform)))
    if peak <= 1e-6:
        return waveform.astype(np.float32), 0.0
    normalized = np.clip(waveform * (target_peak / peak), -1.0, 1.0)
    return normalized.astype(np.float32), round(float(np.max(np.abs(normalized))), 4)


def resample_audio(waveform: np.ndarray, *, orig_sr: int, target_sr: int) -> np.ndarray:
    if orig_sr == target_sr:
        return waveform.astype(np.float32)
    return librosa.resample(waveform, orig_sr=orig_sr, target_sr=target_sr).astype(np.float32)


def build_vad_segments(
    waveform: np.ndarray,
    *,
    sample_rate: int,
    frame_length: int,
    hop_length: int,
) -> list[AudioSegment]:
    if waveform.size == 0:
        return []

    rms = librosa.feature.rms(y=waveform, frame_length=frame_length, hop_length=hop_length)[0]
    if rms.size == 0:
        return []

    threshold = max(float(np.max(rms)) * 0.15, 0.01)
    active = rms > threshold
    segments: list[AudioSegment] = []
    start_frame: int | None = None

    for frame_index, is_active in enumerate(active):
        if is_active and start_frame is None:
            start_frame = frame_index
        elif not is_active and start_frame is not None:
            segments.append(
                AudioSegment(
                    start_seconds=round(start_frame * hop_length / sample_rate, 3),
                    end_seconds=round(frame_index * hop_length / sample_rate, 3),
                )
            )
            start_frame = None

    if start_frame is not None:
        segments.append(
            AudioSegment(
                start_seconds=round(start_frame * hop_length / sample_rate, 3),
                end_seconds=round(waveform.shape[-1] / sample_rate, 3),
            )
        )

    if not segments:
        return [AudioSegment(start_seconds=0.0, end_seconds=round(waveform.shape[-1] / sample_rate, 3))]
    return segments


def estimate_lufs(waveform: np.ndarray) -> float:
    if waveform.size == 0:
        return -70.0
    rms = float(np.sqrt(np.mean(np.square(waveform))))
    if rms <= 1e-8:
        return -70.0
    return round(20.0 * math.log10(rms), 2)


def estimate_noise_score(original: np.ndarray, processed: np.ndarray) -> float:
    if original.size == 0 or processed.size == 0:
        return 1.0
    original_peak = float(np.percentile(np.abs(original), 95))
    processed_floor = float(np.percentile(np.abs(processed), 20))
    trim_ratio = max(0.0, 1.0 - (processed.shape[-1] / max(original.shape[-1], 1)))
    floor_ratio = processed_floor / max(original_peak, 1e-6)
    return round(min(1.0, max(0.02, floor_ratio * 1.5 + trim_ratio * 0.35)), 3)


def estimate_diversity_score(
    waveform: np.ndarray,
    sample_rate: int,
    segments: list[AudioSegment],
) -> float:
    if waveform.size == 0:
        return 0.0
    duration = waveform.shape[-1] / sample_rate
    segment_count = len(segments)
    density = min(duration / 60.0, 1.0) * 0.35
    segmentation = min(segment_count / 8.0, 1.0) * 0.45
    variation = min(float(np.std(waveform)) * 4.0, 0.2)
    return round(min(1.0, 0.1 + density + segmentation + variation), 3)


def probe_audio_file(file_path: str, size_bytes: int) -> AudioMetadata:
    waveform, sample_rate = load_audio(file_path)
    mono = to_mono(waveform)
    return AudioMetadata(
        duration_seconds=round(mono.shape[-1] / sample_rate, 3),
        sample_rate=sample_rate,
        channels=1,
        format=Path(file_path).suffix.lower().lstrip(".") or "wav",
        size_bytes=size_bytes,
    )


def compute_dataset_quality(
    durations: list[float],
    noise_scores: list[float],
    sample_rates: list[int],
) -> DatasetQualityMetrics:
    clip_count = len(durations)
    total_duration = round(sum(durations), 3)
    noise_score = round(mean(noise_scores), 3) if noise_scores else 1.0

    if not durations:
        diversity_score = 0.0
    elif len(durations) == 1:
        diversity_score = 0.2
    else:
        spread = min(pstdev(durations) / 20.0, 1.0)
        coverage = min(clip_count / 12.0, 1.0)
        density = min(total_duration / 180.0, 1.0)
        diversity_score = round(min(1.0, 0.1 + spread * 0.45 + coverage * 0.25 + density * 0.2), 3)

    sample_rate = Counter(sample_rates).most_common(1)[0][0] if sample_rates else 0
    return DatasetQualityMetrics(
        total_duration_seconds=total_duration,
        clip_count=clip_count,
        noise_score=noise_score,
        diversity_score=diversity_score,
        sample_rate=sample_rate,
    )
