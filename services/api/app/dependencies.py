from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.settings import Settings, get_settings
from voiceforge_core.db.models import User
from voiceforge_core.modules.auth.service import AuthService
from voiceforge_core.modules.users.service import UsersService
from voiceforge_core.runtime import RuntimeConfig, RuntimeContainer, build_runtime

security = HTTPBearer(auto_error=False)


@lru_cache(maxsize=1)
def get_runtime() -> RuntimeContainer:
    settings = get_settings()
    return build_runtime(
        RuntimeConfig(
            database_url=settings.database_url,
            redis_url=settings.redis_url,
            queue_name=settings.job_queue_name,
            storage_root=settings.storage_root,
            storage_bucket=settings.storage_bucket,
            seed_vc_python=settings.seed_vc_python,
            seed_vc_repo_dir=settings.seed_vc_repo_dir,
            seed_vc_working_root=settings.seed_vc_working_root,
            seed_vc_diffusion_steps=settings.seed_vc_diffusion_steps,
            seed_vc_length_adjust=settings.seed_vc_length_adjust,
            seed_vc_inference_cfg_rate=settings.seed_vc_inference_cfg_rate,
            seed_vc_f0_condition=settings.seed_vc_f0_condition,
            seed_vc_auto_f0_adjust=settings.seed_vc_auto_f0_adjust,
            seed_vc_semi_tone_shift=settings.seed_vc_semi_tone_shift,
            seed_vc_fp16=settings.seed_vc_fp16,
            seed_vc_timeout_seconds=settings.seed_vc_timeout_seconds,
            seed_vc_checkpoint_path=settings.seed_vc_checkpoint_path,
            seed_vc_config_path=settings.seed_vc_config_path,
            seed_vc_hf_endpoint=settings.seed_vc_hf_endpoint,
            seed_vc_target_sample_rate=settings.seed_vc_target_sample_rate,
            seed_vc_reference_max_seconds=settings.seed_vc_reference_max_seconds,
            seed_vc_reference_clip_limit=settings.seed_vc_reference_clip_limit,
            seed_vc_reference_cache_enabled=settings.seed_vc_reference_cache_enabled,
            seed_vc_source_cache_enabled=settings.seed_vc_source_cache_enabled,
            seed_vc_resident_reference_runtime_enabled=settings.seed_vc_resident_reference_runtime_enabled,
            seed_vc_resident_source_runtime_enabled=settings.seed_vc_resident_source_runtime_enabled,
            seed_vc_resident_runtime_idle_seconds=settings.seed_vc_resident_runtime_idle_seconds,
            seed_vc_resident_runtime_launch_timeout_seconds=settings.seed_vc_resident_runtime_launch_timeout_seconds,
        )
    )


def get_db(runtime: RuntimeContainer = Depends(get_runtime)) -> Generator[Session, None, None]:
    session = runtime.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token.")
    try:
        payload = AuthService.decode_access_token(credentials.credentials, settings.jwt_secret)
    except Exception as exc:  # pragma: no cover - defensive branch
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token.") from exc

    user = UsersService.get_by_id(session, payload["sub"])
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    return user
