"""Audio watermark for free-plan outputs.

Adds a periodic subtle tone embedded throughout the audio to mark
it as produced under the free plan. The tone is:
- A brief 220 Hz sine chirp (~150ms) every 15 seconds
- Mixed at -20 dB below the audio's RMS level
- Starts at a random offset to prevent trivial trimming

The watermark is intentionally non-destructive (low amplitude) but
clearly audible on careful listening, and distributed throughout
the audio to resist simple trimming.
"""

from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger("voiceforge.watermark")

WATERMARK_INTERVAL_SECONDS = 15.0
WATERMARK_DURATION_SECONDS = 0.15
WATERMARK_FREQUENCY_HZ = 220.0
WATERMARK_ATTENUATION_DB = -20.0


def apply_watermark(
    audio: np.ndarray,
    sample_rate: int,
) -> np.ndarray:
    """Apply a periodic tone watermark to the audio signal.

    Args:
        audio: Audio samples as float32 numpy array (mono).
        sample_rate: Sample rate in Hz.

    Returns:
        Watermarked audio as float32 numpy array (same shape).
    """
    if audio.size == 0:
        return audio

    output = audio.astype(np.float32).copy()
    duration_samples = int(WATERMARK_DURATION_SECONDS * sample_rate)
    interval_samples = int(WATERMARK_INTERVAL_SECONDS * sample_rate)

    # Compute RMS of the audio for relative attenuation
    rms = np.sqrt(np.mean(audio.astype(np.float64) ** 2))
    if rms < 1e-8:
        logger.warning("watermark_skipped: audio is silent")
        return output

    # Convert attenuation to linear scale
    attenuation_linear = 10 ** (WATERMARK_ATTENUATION_DB / 20.0)
    tone_amplitude = rms * attenuation_linear

    # Generate the chirp tone (220 Hz sine with smooth envelope)
    t = np.arange(duration_samples, dtype=np.float32) / sample_rate
    chirp = np.sin(2 * np.pi * WATERMARK_FREQUENCY_HZ * t).astype(np.float32)

    # Apply Hann window envelope for smooth onset/offset
    envelope = np.hanning(duration_samples).astype(np.float32)
    tone = chirp * envelope * tone_amplitude

    # Start at a pseudo-random offset (deterministic from audio hash)
    # to prevent users from knowing exactly where the marks are
    audio_hash = int(np.sum(np.abs(audio[:min(1000, len(audio))])) * 1e6) % interval_samples
    start_offset = max(0, min(audio_hash, interval_samples // 2))

    # Place watermark tones throughout the audio
    position = start_offset
    marks_placed = 0
    while position + duration_samples <= len(output):
        output[position : position + duration_samples] += tone
        marks_placed += 1
        position += interval_samples

    # Clip to prevent overflow
    np.clip(output, -1.0, 1.0, out=output)

    logger.info(
        "watermark_applied",
        extra={
            "marks_placed": marks_placed,
            "interval_s": WATERMARK_INTERVAL_SECONDS,
            "tone_hz": WATERMARK_FREQUENCY_HZ,
            "attenuation_db": WATERMARK_ATTENUATION_DB,
        },
    )
    return output
