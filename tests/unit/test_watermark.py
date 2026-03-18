"""Tests for audio watermark application."""

from __future__ import annotations

import numpy as np
import pytest

from voiceforge_core.audio.watermark import (
    WATERMARK_INTERVAL_SECONDS,
    apply_watermark,
)


@pytest.fixture()
def sample_audio() -> np.ndarray:
    """Generate a 30-second sine wave at 440 Hz for testing."""
    sample_rate = 22050
    duration = 30.0
    t = np.arange(int(sample_rate * duration), dtype=np.float32) / sample_rate
    return 0.5 * np.sin(2 * np.pi * 440 * t).astype(np.float32)


class TestWatermark:
    def test_watermark_changes_audio(self, sample_audio: np.ndarray) -> None:
        """Watermarked audio should differ from original."""
        result = apply_watermark(sample_audio, sample_rate=22050)
        assert not np.array_equal(result, sample_audio)

    def test_watermark_preserves_length(self, sample_audio: np.ndarray) -> None:
        """Output should have the same length as input."""
        result = apply_watermark(sample_audio, sample_rate=22050)
        assert result.shape == sample_audio.shape

    def test_watermark_preserves_range(self, sample_audio: np.ndarray) -> None:
        """Output should stay within [-1, 1]."""
        result = apply_watermark(sample_audio, sample_rate=22050)
        assert np.all(result >= -1.0)
        assert np.all(result <= 1.0)

    def test_watermark_places_multiple_marks(self, sample_audio: np.ndarray) -> None:
        """30-second audio with 15s interval should have at least 1 mark."""
        sr = 22050
        result = apply_watermark(sample_audio, sample_rate=sr)
        diff = np.abs(result - sample_audio)
        # There should be non-zero differences at multiple locations
        nonzero_regions = np.where(diff > 1e-8)[0]
        assert len(nonzero_regions) > 0
        # Check that marks span a significant portion (not just start/end)
        span = nonzero_regions[-1] - nonzero_regions[0]
        min_span = int(WATERMARK_INTERVAL_SECONDS * sr * 0.5)
        assert span >= min_span

    def test_watermark_silent_audio_returned_unchanged(self) -> None:
        """Silent audio should be returned as-is (no marks on silence)."""
        silent = np.zeros(22050 * 10, dtype=np.float32)
        result = apply_watermark(silent, sample_rate=22050)
        assert np.array_equal(result, silent)

    def test_watermark_empty_audio(self) -> None:
        """Empty array should be returned as-is."""
        empty = np.array([], dtype=np.float32)
        result = apply_watermark(empty, sample_rate=22050)
        assert result.size == 0

    def test_watermark_is_subtle(self, sample_audio: np.ndarray) -> None:
        """Watermark should not significantly change RMS."""
        rms_before = np.sqrt(np.mean(sample_audio.astype(np.float64) ** 2))
        result = apply_watermark(sample_audio, sample_rate=22050)
        rms_after = np.sqrt(np.mean(result.astype(np.float64) ** 2))
        # RMS should change by less than 5%
        change = abs(rms_after - rms_before) / rms_before
        assert change < 0.05

    def test_watermark_deterministic(self, sample_audio: np.ndarray) -> None:
        """Same input should produce same output."""
        result1 = apply_watermark(sample_audio, sample_rate=22050)
        result2 = apply_watermark(sample_audio, sample_rate=22050)
        assert np.array_equal(result1, result2)
