from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VF_", case_sensitive=False, extra="ignore")

    database_url: str = "postgresql+psycopg://voiceforge:voiceforge@localhost:5432/voiceforge"
    redis_url: str = "redis://localhost:6379/0"
    storage_root: str = "./data/storage"
    storage_bucket: str = "voiceforge-local"
    job_queue_name: str = "voiceforge:jobs"
    seed_vc_python: str = "python"
    seed_vc_repo_dir: str = str(REPO_ROOT / "external" / "seed-vc")
    seed_vc_working_root: str = str(REPO_ROOT / "data" / "seed-vc")
    seed_vc_diffusion_steps: int = 25
    seed_vc_length_adjust: float = 1.0
    seed_vc_inference_cfg_rate: float = 0.7
    seed_vc_f0_condition: bool = False
    seed_vc_auto_f0_adjust: bool = False
    seed_vc_semi_tone_shift: int = 0
    seed_vc_fp16: bool = False
    seed_vc_timeout_seconds: int = 3600
    seed_vc_checkpoint_path: str | None = None
    seed_vc_config_path: str | None = None
    seed_vc_hf_endpoint: str | None = None
    seed_vc_target_sample_rate: int = 22050
    seed_vc_reference_max_seconds: float = 25.0
    seed_vc_reference_clip_limit: int = 3
    seed_vc_reference_cache_enabled: bool = True
    seed_vc_source_cache_enabled: bool = True
    seed_vc_resident_reference_runtime_enabled: bool = True
    seed_vc_resident_source_runtime_enabled: bool = True
    seed_vc_resident_runtime_idle_seconds: int = 900
    seed_vc_resident_runtime_launch_timeout_seconds: int = 120


@lru_cache(maxsize=1)
def get_settings() -> WorkerSettings:
    return WorkerSettings()
