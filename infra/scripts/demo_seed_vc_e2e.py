from __future__ import annotations

import argparse
import hashlib
import json
import logging
import shutil
import sys
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_SRC = REPO_ROOT / "packages" / "voiceforge_core" / "src"
if str(CORE_SRC) not in sys.path:
    sys.path.insert(0, str(CORE_SRC))

from voiceforge_core.audio.pipeline import WaveAudioPreprocessor
from voiceforge_core.db.base import Base
from voiceforge_core.db.enums import ConversionMode, EngineBackend, VoiceSampleSource
from voiceforge_core.db.models import ConvertedAudio, User, VoiceProfile, VoiceSample
from voiceforge_core.inference.model_registry import HashSpeakerEmbeddingService, build_default_model_registry
from voiceforge_core.inference.seed_vc import SeedVCBackendConfig, SeedVCError, SeedVCVoiceConversionEngine
from voiceforge_core.modules.auth.service import AuthService
from voiceforge_core.modules.conversion_jobs.service import ConversionJobService
from voiceforge_core.modules.voice_profiles.schemas import VoiceProfileCreate
from voiceforge_core.modules.voice_profiles.service import VoiceProfileService
from voiceforge_core.modules.voice_samples.service import VoiceSampleService
from voiceforge_core.storage.local_s3 import LocalS3CompatibleStorage

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("voiceforge.demo")


def str_to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a local VoiceForge Seed-VC end-to-end demo.")
    parser.add_argument("--case-dir", required=True)
    parser.add_argument("--seed-vc-python", required=True)
    parser.add_argument("--seed-vc-repo-dir", required=True)
    parser.add_argument("--seed-vc-working-root", required=True)
    parser.add_argument("--source-file", required=True)
    parser.add_argument("--reference-file", action="append", required=True)
    parser.add_argument("--voiceforge-bucket", default="voiceforge-demo")
    parser.add_argument("--email", default="demo@voiceforge.dev")
    parser.add_argument("--display-name", default="VoiceForge Demo")
    parser.add_argument("--password", default="ChangeMe123!")
    parser.add_argument("--profile-name", default="SeedVC Demo Voice")
    parser.add_argument("--reference-cache-enabled", default="true")
    parser.add_argument("--source-cache-enabled", default="true")
    parser.add_argument("--resident-reference-runtime-enabled", default="true")
    parser.add_argument("--resident-source-runtime-enabled", default="true")
    parser.add_argument("--diffusion-steps", type=int, default=25)
    parser.add_argument("--fp16", default="false")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--reuse-profile", action="store_true")
    return parser.parse_args()


def fail(message: str, *, category: str, details: dict | None = None, exit_code: int = 1) -> int:
    payload = {"status": "failed", "category": category, "message": message}
    if details:
        payload["details"] = details
    print(json.dumps(payload, indent=2))
    return exit_code


def get_or_create_user(session, *, email: str, display_name: str, password: str) -> User:
    user = session.scalar(select(User).where(User.email == email))
    if user is not None:
        return user
    return AuthService.register_user(session, email, display_name, password)


def get_or_create_profile(session, *, user: User, profile_name: str) -> VoiceProfile:
    profile = session.scalar(
        select(VoiceProfile).where(VoiceProfile.user_id == user.id, VoiceProfile.name == profile_name)
    )
    if profile is not None:
        return profile
    return VoiceProfileService.create_profile(
        session,
        user,
        VoiceProfileCreate(
            name=profile_name,
            preferred_backend=EngineBackend.SEED_VC,
            consent_confirmed=True,
            consent_text="I have explicit consent to use this voice for local Seed-VC validation.",
        ),
    )


def ensure_reference_samples(
    session,
    *,
    storage,
    preprocessor,
    embedding_extractor,
    profile: VoiceProfile,
    reference_files: list[Path],
) -> list[VoiceSample]:
    existing_samples = list(
        session.scalars(
            select(VoiceSample)
            .where(VoiceSample.voice_profile_id == profile.id)
            .order_by(VoiceSample.created_at.asc())
        )
    )
    existing_hashes = {sample.waveform_hash for sample in existing_samples}
    for reference_path in reference_files:
        payload = reference_path.read_bytes()
        waveform_hash = hashlib.sha256(payload).hexdigest()
        if waveform_hash in existing_hashes:
            continue
        sample = VoiceSampleService.create_sample(
            session,
            storage=storage,
            preprocessor=preprocessor,
            embedding_extractor=embedding_extractor,
            profile=profile,
            original_filename=reference_path.name,
            content_type="audio/wav",
            payload=payload,
            source=VoiceSampleSource.UPLOAD,
        )
        existing_samples.append(sample)
        existing_hashes.add(waveform_hash)
    return existing_samples


def main() -> int:
    args = parse_args()
    args.reference_cache_enabled = str_to_bool(args.reference_cache_enabled)
    args.source_cache_enabled = str_to_bool(args.source_cache_enabled)
    args.resident_reference_runtime_enabled = str_to_bool(args.resident_reference_runtime_enabled)
    args.resident_source_runtime_enabled = str_to_bool(args.resident_source_runtime_enabled)
    args.fp16 = str_to_bool(args.fp16)
    case_dir = Path(args.case_dir).expanduser().resolve()
    source_file = Path(args.source_file).expanduser().resolve()
    reference_files = [Path(item).expanduser().resolve() for item in args.reference_file]

    if args.reset and case_dir.exists():
        shutil.rmtree(case_dir)

    input_dir = case_dir / "input"
    output_dir = case_dir / "output"
    storage_root = case_dir / "storage"
    runtime_root = Path(args.seed_vc_working_root).expanduser().resolve()
    database_path = case_dir / "voiceforge_demo.db"
    summary_path = output_dir / "summary.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    input_dir.mkdir(parents=True, exist_ok=True)

    if not source_file.exists():
        return fail(
            f"Source audio was not found: {source_file}",
            category="source_missing",
            details={"expected_source_file": str(source_file)},
        )
    missing_references = [str(path) for path in reference_files if not path.exists()]
    if missing_references:
        return fail(
            "One or more reference audio files are missing.",
            category="invalid_reference",
            details={"missing_reference_files": missing_references},
        )

    engine = create_engine(f"sqlite:///{database_path}", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    storage = LocalS3CompatibleStorage(root=str(storage_root), bucket=args.voiceforge_bucket)
    preprocessor = WaveAudioPreprocessor()
    embedding_extractor = HashSpeakerEmbeddingService()
    seed_config = SeedVCBackendConfig(
        python_executable=args.seed_vc_python,
        repo_dir=args.seed_vc_repo_dir,
        working_root=str(runtime_root),
        diffusion_steps=args.diffusion_steps,
        fp16=args.fp16,
        reference_cache_enabled=args.reference_cache_enabled,
        source_cache_enabled=args.source_cache_enabled,
        resident_reference_runtime_enabled=args.resident_reference_runtime_enabled,
        resident_source_runtime_enabled=args.resident_source_runtime_enabled,
    )
    registry = build_default_model_registry(seed_vc_config=seed_config, preprocessor=preprocessor)
    seed_engine = registry.resolve(EngineBackend.SEED_VC)
    if not isinstance(seed_engine, SeedVCVoiceConversionEngine):
        return fail("Seed-VC engine was not registered correctly.", category="runtime_missing")

    try:
        seed_engine.validate_runtime(job_id="demo-runtime-check")
    except SeedVCError as exc:
        return fail(
            str(exc),
            category=exc.category,
            details=exc.diagnostics,
            exit_code=2,
        )

    logger.info("Seed-VC runtime validation passed.")

    with session_factory() as session:
        if args.reuse_profile:
            user = get_or_create_user(
                session,
                email=args.email,
                display_name=args.display_name,
                password=args.password,
            )
            profile = get_or_create_profile(session, user=user, profile_name=args.profile_name)
            samples = ensure_reference_samples(
                session,
                storage=storage,
                preprocessor=preprocessor,
                embedding_extractor=embedding_extractor,
                profile=profile,
                reference_files=reference_files,
            )
        else:
            user = AuthService.register_user(session, args.email, args.display_name, args.password)
            profile = VoiceProfileService.create_profile(
                session,
                user,
                VoiceProfileCreate(
                    name=args.profile_name,
                    preferred_backend=EngineBackend.SEED_VC,
                    consent_confirmed=True,
                    consent_text="I have explicit consent to use this voice for local Seed-VC validation.",
                ),
            )
            samples = []
            for reference_path in reference_files:
                sample = VoiceSampleService.create_sample(
                    session,
                    storage=storage,
                    preprocessor=preprocessor,
                    embedding_extractor=embedding_extractor,
                    profile=profile,
                    original_filename=reference_path.name,
                    content_type="audio/wav",
                    payload=reference_path.read_bytes(),
                    source=VoiceSampleSource.UPLOAD,
                )
                samples.append(sample)

        job = ConversionJobService.create_job(
            session,
            storage=storage,
            preprocessor=preprocessor,
            queue=None,
            queue_name="demo:inline",
            user=user,
            profile=profile,
            backend=EngineBackend.SEED_VC,
            mode=ConversionMode.STUDIO,
            original_filename=source_file.name,
            content_type="audio/wav",
            payload=source_file.read_bytes(),
            ip_address="demo-script",
            enqueue=False,
        )
        session.commit()

        try:
            ConversionJobService.process_job(
                session,
                storage=storage,
                registry=registry,
                preprocessor=preprocessor,
                conversion_job_id=job.id,
            )
            session.commit()
        except Exception as exc:
            session.rollback()
            failed_job = session.get(type(job), job.id)
            failure_payload = ConversionJobService.failure_payload(exc)
            if failed_job is not None:
                ConversionJobService.mark_failed(
                    session,
                    job=failed_job,
                    error_message=str(exc),
                    error_category=failure_payload["error_category"],
                )
                session.commit()
            return fail(
                str(exc),
                category=failure_payload["error_category"],
                details=failure_payload.get("diagnostics"),
                exit_code=3,
            )

        completed_job = session.get(type(job), job.id)
        output = session.scalar(
            select(ConvertedAudio)
            .where(ConvertedAudio.conversion_job_id == job.id)
            .order_by(ConvertedAudio.created_at.desc())
        )
        if completed_job is None or output is None:
            return fail(
                "Conversion completed without a persisted output artifact.",
                category="storage_failed",
            )

        final_output_path = storage.resolve_path(output.storage_key)
        published_output = output_dir / "converted.wav"
        published_output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(final_output_path, published_output)

        summary = {
            "status": "completed",
            "case_dir": str(case_dir),
            "database_path": str(database_path),
            "source_file": str(source_file),
            "reference_files": [str(path) for path in reference_files],
            "storage_root": str(storage_root),
            "seed_vc_working_root": str(runtime_root),
            "job_id": str(completed_job.id),
            "voice_profile_id": str(profile.id),
            "job_status": completed_job.status.value,
            "error_category": completed_job.error_category,
            "processing_started_at": completed_job.processing_started_at.isoformat()
            if completed_job.processing_started_at
            else None,
            "processing_finished_at": completed_job.processing_finished_at.isoformat()
            if completed_job.processing_finished_at
            else None,
            "processing_duration_ms": completed_job.processing_duration_ms,
            "source_audio_duration_ms": completed_job.source_audio_duration_ms,
            "reference_audio_duration_ms": completed_job.reference_audio_duration_ms,
            "output_audio_duration_ms": completed_job.output_audio_duration_ms,
            "profiling_json": completed_job.profiling_json,
            "final_output_storage_path": str(final_output_path),
            "published_output_path": str(published_output),
            "output_size_bytes": output.size_bytes,
            "reference_sample_ids": [str(sample.id) for sample in samples],
            "subprocess_stdout_log_path": output.traceability_metadata["subprocess"]["stdout_log_path"],
            "subprocess_stderr_log_path": output.traceability_metadata["subprocess"]["stderr_log_path"],
            "subprocess_manifest_path": output.traceability_metadata["subprocess"]["manifest_path"],
            "validation": {
                "output_exists": published_output.exists(),
                "output_is_wav": published_output.suffix.lower() == ".wav",
                "output_duration_ms_gt_zero": (completed_job.output_audio_duration_ms or 0) > 0,
                "subprocess_returncode_zero": output.traceability_metadata["subprocess"]["returncode"] == 0,
            },
            "traceability_metadata": output.traceability_metadata,
            "source_cache_enabled": str(args.source_cache_enabled).lower(),
            "reference_cache_enabled": str(args.reference_cache_enabled).lower(),
            "resident_source_runtime_enabled": str(args.resident_source_runtime_enabled).lower(),
            "resident_reference_runtime_enabled": str(args.resident_reference_runtime_enabled).lower(),
            "diffusion_steps": args.diffusion_steps,
            "fp16": args.fp16,
        }
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
