"""Unit tests for the audio preprocessing pipeline.

All tests use synthetic audio generated with numpy — no real audio
files are needed. Each test validates a specific stage of the pipeline
independently.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from voiceforge_core.audio.contracts import AudioSegment, DatasetQualityMetrics
from voiceforge_core.audio.pipeline import (
    AudioProcessingError,
    WaveAudioPreprocessor,
    build_vad_segments,
    compute_dataset_quality,
    estimate_diversity_score,
    estimate_lufs,
    estimate_noise_score,
    load_audio,
    normalize_audio,
    resample_audio,
    to_mono,
    trim_silence,
)

SAMPLE_RATE = 16000
DURATION_SECONDS = 2.0


@pytest.fixture()
def sine_wave() -> np.ndarray:
    """Generate a 440 Hz sine wave, mono, float32."""
    t = np.linspace(0, DURATION_SECONDS, int(SAMPLE_RATE * DURATION_SECONDS), dtype=np.float32)
    return np.sin(2 * np.pi * 440 * t).astype(np.float32)


@pytest.fixture()
def stereo_wave(sine_wave: np.ndarray) -> np.ndarray:
    """Generate a stereo signal (2 channels)."""
    return np.stack([sine_wave, sine_wave * 0.8], axis=0)


@pytest.fixture()
def wav_path(sine_wave: np.ndarray, tmp_path: Path) -> Path:
    """Write a mono sine wave to a temporary WAV file."""
    path = tmp_path / "test_mono.wav"
    sf.write(str(path), sine_wave, SAMPLE_RATE, subtype="PCM_16")
    return path


@pytest.fixture()
def silent_wav_path(tmp_path: Path) -> Path:
    """Write a near-silent WAV for trim/VAD edge cases."""
    silence = np.zeros(SAMPLE_RATE * 2, dtype=np.float32)
    path = tmp_path / "silence.wav"
    sf.write(str(path), silence, SAMPLE_RATE, subtype="PCM_16")
    return path


# -----------------------------------------------------------------------
# load_audio
# -----------------------------------------------------------------------

class TestLoadAudio:
    def test_loads_wav_successfully(self, wav_path: Path) -> None:
        waveform, sr = load_audio(str(wav_path))
        assert sr == SAMPLE_RATE
        assert waveform.ndim >= 1
        assert waveform.dtype == np.float32

    def test_raises_on_nonexistent_file(self, tmp_path: Path) -> None:
        with pytest.raises(AudioProcessingError):
            load_audio(str(tmp_path / "nonexistent.wav"))

    def test_raises_on_corrupt_file(self, tmp_path: Path) -> None:
        corrupt = tmp_path / "corrupt.wav"
        corrupt.write_bytes(b"not a wav file")
        with pytest.raises(AudioProcessingError):
            load_audio(str(corrupt))


# -----------------------------------------------------------------------
# to_mono
# -----------------------------------------------------------------------

class TestToMono:
    def test_mono_passthrough(self, sine_wave: np.ndarray) -> None:
        result = to_mono(sine_wave)
        assert result.ndim == 1
        assert result.shape[0] == sine_wave.shape[0]

    def test_single_channel_2d(self, sine_wave: np.ndarray) -> None:
        two_d = sine_wave.reshape(1, -1)
        result = to_mono(two_d)
        assert result.ndim == 1
        np.testing.assert_allclose(result, sine_wave, atol=1e-6)

    def test_stereo_to_mono(self, stereo_wave: np.ndarray) -> None:
        result = to_mono(stereo_wave)
        assert result.ndim == 1
        expected = np.mean(stereo_wave, axis=0)
        np.testing.assert_allclose(result, expected, atol=1e-6)


# -----------------------------------------------------------------------
# trim_silence
# -----------------------------------------------------------------------

class TestTrimSilence:
    def test_preserves_non_silent_audio(self, sine_wave: np.ndarray) -> None:
        trimmed, removed = trim_silence(
            sine_wave, sample_rate=SAMPLE_RATE, top_db=35.0,
            frame_length=2048, hop_length=512,
        )
        assert trimmed.size > 0
        assert removed >= 0.0

    def test_handles_empty_waveform(self) -> None:
        empty = np.array([], dtype=np.float32)
        trimmed, removed = trim_silence(
            empty, sample_rate=SAMPLE_RATE, top_db=35.0,
            frame_length=2048, hop_length=512,
        )
        assert trimmed.size == 0
        assert removed == 0.0

    def test_removes_leading_trailing_silence(self) -> None:
        silence = np.zeros(SAMPLE_RATE, dtype=np.float32)
        t = np.linspace(0, 0.5, SAMPLE_RATE // 2, dtype=np.float32)
        tone = np.sin(2 * np.pi * 440 * t) * 0.8
        padded = np.concatenate([silence, tone, silence])
        trimmed, removed = trim_silence(
            padded, sample_rate=SAMPLE_RATE, top_db=35.0,
            frame_length=2048, hop_length=512,
        )
        assert trimmed.size < padded.size
        assert removed > 0.0


# -----------------------------------------------------------------------
# normalize_audio
# -----------------------------------------------------------------------

class TestNormalizeAudio:
    def test_scales_to_target_peak(self, sine_wave: np.ndarray) -> None:
        target = 0.95
        normalized, peak = normalize_audio(sine_wave * 0.3, target_peak=target)
        actual_peak = float(np.max(np.abs(normalized)))
        assert abs(actual_peak - target) < 0.01

    def test_handles_silent_audio(self) -> None:
        silent = np.zeros(1000, dtype=np.float32)
        normalized, peak = normalize_audio(silent, target_peak=0.95)
        assert peak == 0.0
        np.testing.assert_array_equal(normalized, silent)

    def test_handles_empty_audio(self) -> None:
        empty = np.array([], dtype=np.float32)
        normalized, peak = normalize_audio(empty, target_peak=0.95)
        assert peak == 0.0
        assert normalized.size == 0

    def test_clips_to_valid_range(self) -> None:
        loud = np.ones(100, dtype=np.float32) * 2.0
        normalized, peak = normalize_audio(loud, target_peak=0.95)
        assert float(np.max(np.abs(normalized))) <= 1.0


# -----------------------------------------------------------------------
# resample_audio
# -----------------------------------------------------------------------

class TestResampleAudio:
    def test_same_rate_passthrough(self, sine_wave: np.ndarray) -> None:
        result = resample_audio(sine_wave, orig_sr=SAMPLE_RATE, target_sr=SAMPLE_RATE)
        np.testing.assert_array_equal(result, sine_wave)

    def test_downsample(self, sine_wave: np.ndarray) -> None:
        target_sr = 8000
        result = resample_audio(sine_wave, orig_sr=SAMPLE_RATE, target_sr=target_sr)
        expected_samples = int(len(sine_wave) * target_sr / SAMPLE_RATE)
        assert abs(result.shape[0] - expected_samples) < 10
        assert result.dtype == np.float32

    def test_upsample(self, sine_wave: np.ndarray) -> None:
        target_sr = 44100
        result = resample_audio(sine_wave, orig_sr=SAMPLE_RATE, target_sr=target_sr)
        expected_samples = int(len(sine_wave) * target_sr / SAMPLE_RATE)
        assert abs(result.shape[0] - expected_samples) < 10


# -----------------------------------------------------------------------
# VAD segments
# -----------------------------------------------------------------------

class TestBuildVadSegments:
    def test_returns_segments_for_speech(self, sine_wave: np.ndarray) -> None:
        segments = build_vad_segments(
            sine_wave, sample_rate=SAMPLE_RATE,
            frame_length=2048, hop_length=512,
        )
        assert len(segments) >= 1
        assert all(isinstance(s, AudioSegment) for s in segments)
        assert all(s.end_seconds > s.start_seconds for s in segments)

    def test_empty_waveform(self) -> None:
        segments = build_vad_segments(
            np.array([], dtype=np.float32),
            sample_rate=SAMPLE_RATE, frame_length=2048, hop_length=512,
        )
        assert segments == []

    def test_silent_waveform_returns_full_span(self) -> None:
        silent = np.zeros(SAMPLE_RATE, dtype=np.float32) + 1e-10
        segments = build_vad_segments(
            silent, sample_rate=SAMPLE_RATE,
            frame_length=2048, hop_length=512,
        )
        assert len(segments) >= 1


# -----------------------------------------------------------------------
# Scoring functions
# -----------------------------------------------------------------------

class TestEstimateLufs:
    def test_returns_reasonable_value(self, sine_wave: np.ndarray) -> None:
        lufs = estimate_lufs(sine_wave)
        assert -60.0 < lufs < 0.0

    def test_silent_returns_floor(self) -> None:
        assert estimate_lufs(np.zeros(100, dtype=np.float32)) == -70.0

    def test_empty_returns_floor(self) -> None:
        assert estimate_lufs(np.array([], dtype=np.float32)) == -70.0


class TestEstimateNoiseScore:
    def test_clean_signal_low_score(self, sine_wave: np.ndarray) -> None:
        normalized, _ = normalize_audio(sine_wave, target_peak=0.95)
        score = estimate_noise_score(sine_wave, normalized)
        assert 0.0 <= score <= 1.0

    def test_empty_signals(self) -> None:
        empty = np.array([], dtype=np.float32)
        assert estimate_noise_score(empty, empty) == 1.0


class TestEstimateDiversityScore:
    def test_returns_bounded_value(self, sine_wave: np.ndarray) -> None:
        segments = [AudioSegment(start_seconds=0.0, end_seconds=2.0)]
        score = estimate_diversity_score(sine_wave, SAMPLE_RATE, segments)
        assert 0.0 <= score <= 1.0

    def test_empty_waveform(self) -> None:
        score = estimate_diversity_score(np.array([], dtype=np.float32), SAMPLE_RATE, [])
        assert score == 0.0


# -----------------------------------------------------------------------
# Quality scoring
# -----------------------------------------------------------------------

class TestComputeDatasetQuality:
    def test_basic_quality_metrics(self) -> None:
        metrics = compute_dataset_quality(
            durations=[10.0, 15.0, 20.0],
            noise_scores=[0.1, 0.15, 0.12],
            sample_rates=[16000, 16000, 16000],
        )
        assert isinstance(metrics, DatasetQualityMetrics)
        assert metrics.clip_count == 3
        assert metrics.total_duration_seconds == 45.0
        assert 0.0 <= metrics.noise_score <= 1.0
        assert 0.0 <= metrics.diversity_score <= 1.0
        assert metrics.sample_rate == 16000

    def test_readiness_score_range(self) -> None:
        metrics = compute_dataset_quality(
            durations=[30.0] * 20,
            noise_scores=[0.05] * 20,
            sample_rates=[48000] * 20,
        )
        score = metrics.readiness_score()
        assert 0.0 <= score <= 100.0
        assert score > 50.0  # Good data should score well

    def test_empty_dataset(self) -> None:
        metrics = compute_dataset_quality([], [], [])
        assert metrics.clip_count == 0
        assert metrics.total_duration_seconds == 0.0
        assert metrics.readiness_score() == 0.0

    def test_single_clip(self) -> None:
        metrics = compute_dataset_quality(
            durations=[5.0],
            noise_scores=[0.1],
            sample_rates=[16000],
        )
        assert metrics.clip_count == 1
        assert metrics.diversity_score == 0.2


# -----------------------------------------------------------------------
# Full pipeline
# -----------------------------------------------------------------------

class TestWaveAudioPreprocessor:
    def test_process_returns_valid_result(self, wav_path: Path) -> None:
        preprocessor = WaveAudioPreprocessor()
        result = preprocessor.process(str(wav_path), wav_path.stat().st_size)
        assert result.metadata.duration_seconds > 0
        assert result.metadata.sample_rate == SAMPLE_RATE
        assert result.metadata.channels == 1
        assert 0.0 <= result.noise_score <= 1.0
        assert 0.0 <= result.diversity_score <= 1.0
        assert len(result.vad_segments) >= 1

    def test_prepare_for_seed_vc(self, wav_path: Path, tmp_path: Path) -> None:
        preprocessor = WaveAudioPreprocessor()
        output_path = tmp_path / "prepared.wav"
        artifact = preprocessor.prepare_for_seed_vc(
            input_path=wav_path,
            output_path=output_path,
            target_sample_rate=22050,
            max_duration_seconds=10.0,
        )
        assert output_path.exists()
        assert artifact.metadata.sample_rate == 22050
        assert artifact.metadata.channels == 1
        assert artifact.metadata.duration_seconds > 0

    def test_prepare_reference_prompt(self, wav_path: Path, tmp_path: Path) -> None:
        preprocessor = WaveAudioPreprocessor()
        output_path = tmp_path / "reference_prompt.wav"
        artifact = preprocessor.prepare_reference_prompt(
            input_paths=[wav_path, wav_path],
            output_path=output_path,
            target_sample_rate=22050,
            max_duration_seconds=25.0,
        )
        assert output_path.exists()
        assert artifact.metadata.sample_rate == 22050
        assert artifact.metadata.duration_seconds > 0

    def test_prepare_reference_prompt_empty_raises(self, tmp_path: Path) -> None:
        preprocessor = WaveAudioPreprocessor()
        with pytest.raises(ValueError, match="At least one reference"):
            preprocessor.prepare_reference_prompt(
                input_paths=[],
                output_path=tmp_path / "empty.wav",
                target_sample_rate=22050,
            )
