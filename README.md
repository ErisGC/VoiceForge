# VoiceForge

VoiceForge is a production-oriented monorepo for a cross-platform voice conversion platform that targets Android and Web with a single Flutter frontend, plus a modular Python backend built on FastAPI, PostgreSQL, Redis, and S3-compatible storage abstractions.

## Seed-VC status

Seed-VC is now wired as the first real offline conversion backend.  
Integration details, installation, and the end-to-end reproducible test flow live in [docs/seed-vc.md](C:/Users/Ruben%20Gutierrez/Proyectos%20Rub%C3%A9n/VoiceForge/docs/seed-vc.md).

## Seed-VC profiling status

VoiceForge now includes stage-level profiling and a reproducible cold vs warm benchmark for the real offline Seed-VC path.  
Benchmark flow, measured results, and optimization opportunities live in [docs/seed-vc-profiling.md](C:/Users/Ruben%20Gutierrez/Proyectos%20Rub%C3%A9n/VoiceForge/docs/seed-vc-profiling.md).

## Seed-VC cache optimization status

VoiceForge now also includes versioned reference feature caching per `voice_profile` plus a resident reference runtime for Seed-VC cache builds.  
Design details, invalidation rules, and the optimized benchmark comparison live in [docs/seed-vc-reference-cache.md](C:/Users/Ruben%20Gutierrez/Proyectos%20Rub%C3%A9n/VoiceForge/docs/seed-vc-reference-cache.md).

## Seed-VC source optimization status

VoiceForge now also includes reusable source feature caching, a formal resident-runtime benchmark, and controlled `diffusion_steps` experiments for the remaining `inference_core` cost.  
Measured results and rerun commands live in [docs/seed-vc-source-optimization.md](C:/Users/Ruben%20Gutierrez/Proyectos%20Rub%C3%A9n/VoiceForge/docs/seed-vc-source-optimization.md).

## Seed-VC quality-vs-speed status

VoiceForge now also includes a preset evaluation package for `diffusion_steps`, plus a manual perceptual protocol and scorecard for Studio-mode preset decisions.  
The current recommendation and evaluation framework live in [docs/seed-vc-quality-vs-speed.md](C:/Users/Ruben%20Gutierrez/Proyectos%20Rub%C3%A9n/VoiceForge/docs/seed-vc-quality-vs-speed.md).

## Seed-VC local validation

VoiceForge now includes a repeatable local Seed-VC validation harness:

- `infra/scripts/install_seed_vc.ps1`: installs the official upstream runtime in `external/seed-vc`
- `infra/scripts/run_seed_vc_demo.ps1`: generates demo WAVs, runs a real conversion, and prints the final WAV path
- `infra/scripts/demo_seed_vc_e2e.py`: service-layer runner used by the wrapper

The latest successful local validation in this workspace produced:

- `data/demo/seed-vc-case-01/output/converted.wav`
- `data/demo/seed-vc-case-01/output/summary.json`

The latest profiling benchmark in this workspace produced:

- `data/bench/seed-vc/benchmark_summary.json`
- `data/bench/seed-vc/benchmark_report.md`

The latest cache-optimized benchmark in this workspace produced:

- `data/bench/seed-vc-cache/benchmark_summary.json`
- `data/bench/seed-vc-cache/benchmark_report.md`
- `data/bench/seed-vc-cache/benchmark_vs_baseline.md`

The latest source-cache benchmark in this workspace produced:

- `data/bench/seed-vc-source-cache/benchmark_summary.json`
- `data/bench/seed-vc-source-cache/benchmark_report.md`
- `data/bench/seed-vc-source-cache/benchmark_vs_baseline.md`

The latest resident-runtime benchmark in this workspace produced:

- `data/bench/seed-vc-res/benchmark_summary.json`
- `data/bench/seed-vc-res/benchmark_report.md`
- `data/bench/seed-vc-res/benchmark_vs_baseline.md`

The latest inference-core experiment in this workspace produced:

- `data/bench/seed-vc-inference/inference_experiments.json`
- `data/bench/seed-vc-inference/inference_experiments.md`

The latest quality-vs-speed evaluation package in this workspace produced:

- `data/bench/seed-vc-quality-eval/quality_vs_speed_report.md`
- `data/bench/seed-vc-quality-eval/manual_evaluation_protocol.md`
- `data/bench/seed-vc-quality-eval/manual_evaluation_scorecard.csv`

## What is included

- `apps/voiceforge_flutter`: Flutter application for Android and Web with responsive navigation and the core product surfaces.
- `services/api`: FastAPI service with OpenAPI docs, JWT-ready auth, modular REST endpoints, and Alembic migrations.
- `services/worker`: Redis-backed background worker for training and conversion jobs.
- `packages/voiceforge_core`: Shared backend domain package with SQLAlchemy models, audio pipeline abstractions, storage adapters, model registry, and job queue integration.
- `docs/architecture.md`: System architecture, module boundaries, and flow documentation.
- `docs/seed-vc.md`: Real offline Seed-VC integration, installation, and local validation flow.
- `docs/seed-vc-profiling.md`: Stage-level profiling, cold vs warm benchmark, and optimization findings for Seed-VC offline conversion.
- `docs/seed-vc-reference-cache.md`: Reference cache design, invalidation, resident runtime support, and optimized benchmark results.
- `docs/seed-vc-source-optimization.md`: Source cache design, resident runtime benchmark, and inference-core experiments after the reference-cache phase.
- `docs/seed-vc-quality-vs-speed.md`: Preset evaluation, quality-vs-speed recommendation, and the manual listening framework for Studio mode.
- `TODO.md`: Next implementation phases to evolve from starter platform to production-grade inference system.

## Product scope in this starter

- Multiple saved voices per user.
- Multiple training/reference samples per saved voice.
- Consent-aware voice profile creation.
- Dataset metadata capture:
  - total duration
  - clip count
  - noise score
  - diversity score
  - sample rate
  - voice profile readiness score
- Background jobs for training orchestration and conversion orchestration.
- Backend registry prepared for Seed-VC, RVC, and OpenVoice.
- Real zero-shot offline conversion through Seed-VC.
- Two conversion modes:
  - `studio`
  - `live`

## Repository layout

```text
VoiceForge/
|- apps/
|  |- voiceforge_flutter/
|- docs/
|  |- architecture.md
|- infra/
|  |- docker/
|- packages/
|  |- voiceforge_core/
|- services/
|  |- api/
|  |- worker/
|- docker-compose.yml
|- README.md
|- TODO.md
```

## Backend architecture summary

- FastAPI exposes REST endpoints for auth, users, voice profiles, voice samples, training jobs, conversion jobs, and audit logs.
- SQLAlchemy models live in the shared `voiceforge_core` package so the API and the worker operate on the same schema and domain language.
- Redis is used as a real background queue through a lightweight envelope abstraction.
- Local storage uses an S3-compatible interface and currently persists to the filesystem under a bucket-style path layout.
- The audio/inference layer is intentionally swappable:
  - `AudioPreprocessor`
  - `SpeakerEmbeddingService`
  - `VoiceConversionEngine`
  - `ModelRegistry`
  - `TrainingOrchestrator`

### Current backend reality

- `seed_vc`: real offline conversion adapter via the official Seed-VC CLI.
- `rvc`: placeholder adapter.
- `openvoice`: placeholder adapter.

## Quick start

1. Copy `.env.example` to `.env`.
2. Install backend dependencies:

```powershell
pip install -r services/api/requirements.txt
pip install -r services/worker/requirements.txt
```

3. Run the API:

```powershell
cd services/api
alembic upgrade head
uvicorn app.main:app --reload
```

4. Run the worker:

```powershell
cd services/worker
python worker.py
```

5. Run Flutter:

```powershell
cd apps/voiceforge_flutter
flutter run -d chrome
```

6. Or run the infrastructure stack with Docker Compose once Docker is available on the host:

```powershell
docker compose up --build
```

## Main REST flows already prepared

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/users/me`
- `POST /api/v1/voice-profiles`
- `GET /api/v1/voice-profiles`
- `GET /api/v1/voice-profiles/{profile_id}`
- `POST /api/v1/voice-profiles/{profile_id}/samples`
- `GET /api/v1/voice-profiles/{profile_id}/samples`
- `POST /api/v1/training-jobs`
- `GET /api/v1/training-jobs`
- `POST /api/v1/conversion-jobs`
- `POST /api/v1/conversion-jobs/{job_id}/process-now`
- `GET /api/v1/conversion-jobs`
- `GET /api/v1/conversion-jobs/{job_id}`
- `GET /api/v1/conversion-jobs/{job_id}/outputs`
- `GET /api/v1/conversion-jobs/{job_id}/outputs/{output_id}/download`
- `GET /api/v1/audit-logs`

## Notes

- The audio pipeline now performs real mono WAV preparation, resampling, normalization, and silence trimming for Seed-VC offline conversion.
- Seed-VC runs through an isolated external runtime because its upstream stack is heavy and version-sensitive.
- The training orchestrator currently emits backend-ready manifests rather than launching GPU training. This keeps the queue, schema, storage, and audit trail production-shaped from the start.
- `docker` was not available in the current environment while scaffolding this repository, so Docker assets were authored but not executed locally here.
