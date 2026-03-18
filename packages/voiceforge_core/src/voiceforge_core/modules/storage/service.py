from __future__ import annotations

from pathlib import Path

ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".m4a", ".ogg"}
DEFAULT_AUDIO_CONTENT_TYPE = "application/octet-stream"


def validate_audio_filename(filename: str | None) -> str:
    if not filename:
        raise ValueError("Audio filename is required.")
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_AUDIO_EXTENSIONS:
        raise ValueError(
            f"Unsupported audio format '{suffix}'. Allowed formats: {', '.join(sorted(ALLOWED_AUDIO_EXTENSIONS))}."
        )
    return suffix

