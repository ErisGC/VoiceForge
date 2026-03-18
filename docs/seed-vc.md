# Seed-VC Offline Validation

This document describes the real offline Seed-VC path now wired into VoiceForge, how to run the local validation harness, and what to inspect when a conversion fails.

For cold vs warm profiling, stage-level timing analysis, and the current benchmark results, see `docs/seed-vc-profiling.md`.
For the reference cache design, invalidation rules, resident runtime support, and the optimized benchmark, see `docs/seed-vc-reference-cache.md`.
For the next optimization phase with source caching, the resident-runtime benchmark, and `diffusion_steps` experiments, see `docs/seed-vc-source-optimization.md`.

## What is real now

- `seed_vc` is no longer a placeholder backend.
- The `VoiceConversionEngine` interface resolves a real `SeedVCVoiceConversionEngine`.
- The conversion path now performs:
  - source audio load from VoiceForge storage
  - target reference audio load from saved voice samples
  - mono WAV conversion
  - resampling to the model sample rate
  - basic peak normalization
  - silence trimming
  - real upstream `inference.py` execution from the official Seed-VC repository
  - converted WAV persistence back into VoiceForge storage
  - `conversion_jobs` status, timing, duration, and error-category updates

## What remains pending

- `rvc` and `openvoice` are still placeholder backends.
- Seed-VC training or fine-tuning is not wired into `training_jobs` yet.
- Live streaming remains architecture-only.
- The preprocessing chain is intentionally minimal and production-safe, not yet a full DSP stack.

## Runtime boundary

VoiceForge keeps Seed-VC in a dedicated external Python runtime because the upstream dependency stack is heavy and version-sensitive.

VoiceForge runtime:

- API and worker stay on the project Python environment.
- The Seed-VC adapter launches the upstream CLI through subprocess.
- Full stdout and stderr are captured to per-job log files.

Seed-VC runtime:

- official repo checkout
- isolated Python 3.10 virtual environment
- upstream dependencies installed from the official `requirements.txt`

## Required environment variables

Set these in `.env` for the API and worker:

```env
VF_SEED_VC_PYTHON=C:\path\to\seed-vc\.venv\Scripts\python.exe
VF_SEED_VC_REPO_DIR=C:\path\to\seed-vc
VF_SEED_VC_WORKING_ROOT=./data/seed-vc
VF_SEED_VC_DIFFUSION_STEPS=25
VF_SEED_VC_LENGTH_ADJUST=1.0
VF_SEED_VC_INFERENCE_CFG_RATE=0.7
VF_SEED_VC_F0_CONDITION=false
VF_SEED_VC_AUTO_F0_ADJUST=false
VF_SEED_VC_SEMI_TONE_SHIFT=0
VF_SEED_VC_FP16=false
VF_SEED_VC_TIMEOUT_SECONDS=3600
VF_SEED_VC_TARGET_SAMPLE_RATE=22050
VF_SEED_VC_REFERENCE_MAX_SECONDS=25.0
VF_SEED_VC_REFERENCE_CLIP_LIMIT=3
VF_SEED_VC_REFERENCE_CACHE_ENABLED=true
VF_SEED_VC_SOURCE_CACHE_ENABLED=true
VF_SEED_VC_RESIDENT_REFERENCE_RUNTIME_ENABLED=true
VF_SEED_VC_RESIDENT_SOURCE_RUNTIME_ENABLED=true
VF_SEED_VC_RESIDENT_RUNTIME_IDLE_SECONDS=900
VF_SEED_VC_RESIDENT_RUNTIME_LAUNCH_TIMEOUT_SECONDS=120
```

Optional:

```env
VF_SEED_VC_CHECKPOINT_PATH=
VF_SEED_VC_CONFIG_PATH=
VF_SEED_VC_HF_ENDPOINT=
```

## Installation

Install the upstream runtime:

```powershell
powershell -ExecutionPolicy Bypass -File .\infra\scripts\install_seed_vc.ps1 -RepoDir "external/seed-vc" -PythonExe "py -3.10"
```

Then export the runtime for local runs:

```powershell
$env:VF_SEED_VC_PYTHON = "$PWD\external\seed-vc\.venv\Scripts\python.exe"
$env:VF_SEED_VC_REPO_DIR = "$PWD\external\seed-vc"
```

## Error categories

The active conversion path now classifies failures into these categories:

- `runtime_missing`
- `preprocess_failed`
- `inference_failed`
- `storage_failed`
- `invalid_reference`

Where they appear:

- `conversion_jobs.error_category`
- inline `process-now` HTTP failure detail prefix
- worker and API audit payloads
- demo script JSON output

## Per-job metrics

`conversion_jobs` now persists:

- `processing_started_at`
- `processing_finished_at`
- `processing_duration_ms`
- `source_audio_duration_ms`
- `reference_audio_duration_ms`
- `output_audio_duration_ms`

The converted output traceability metadata also stores:

- subprocess return code
- subprocess duration
- full stdout log path
- full stderr log path
- manifest path with command and context

## Local demo harness

The fastest repeatable local validation path is the demo harness, which exercises the same service-layer conversion path used by the inline `process-now` flow, but avoids needing a full PostgreSQL and Redis stack on the host.

Scripts:

- `infra/scripts/run_seed_vc_demo.ps1`
- `infra/scripts/demo_seed_vc_e2e.py`

What it does:

1. validates the Seed-VC runtime explicitly
2. generates `source.wav` plus two reference WAVs on Windows through `System.Speech`
3. creates a local SQLite demo database
4. creates a user and a voice profile
5. uploads the reference samples through the same service layer
6. creates a conversion job
7. runs the real Seed-VC subprocess
8. validates the output WAV
9. writes a JSON summary with log paths and durations

## Exact command

From the repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\infra\scripts\run_seed_vc_demo.ps1 `
  -SeedVCPython "$env:VF_SEED_VC_PYTHON" `
  -SeedVCRepoDir "$env:VF_SEED_VC_REPO_DIR" `
  -Reset
```

## Expected folder layout

After a successful run, the demo case lives at `data/demo/seed-vc-case-01/`:

```text
data/demo/seed-vc-case-01/
|- input/
|  |- reference_01.wav
|  |- reference_02.wav
|  |- source.wav
|- output/
|  |- converted.wav
|  |- summary.json
|- runtime/
|  |- logs/
|     |- demo-runtime-check/
|     |- <job_id>/
|        |- <timestamp>/
|           |- stdout.log
|           |- stderr.log
|           |- run.json
|- storage/
|  |- voiceforge-demo/
|- voiceforge_demo.db
```

## Expected success signals

Inspect `data/demo/seed-vc-case-01/output/summary.json`.

A healthy run should show:

- `"status": "completed"`
- `"job_status": "completed"`
- `"error_category": null`
- `"validation.output_exists": true`
- `"validation.output_is_wav": true`
- `"validation.subprocess_returncode_zero": true`
- a concrete `published_output_path`
- concrete `subprocess_stdout_log_path` and `subprocess_stderr_log_path`

The final published WAV should be here:

```text
data/demo/seed-vc-case-01/output/converted.wav
```

## Validated local run

A full real end-to-end run was completed in this workspace on March 16, 2026 using:

- Seed-VC repo: `external/seed-vc`
- Seed-VC runtime: `external/seed-vc/.venv/Scripts/python.exe`
- demo wrapper: `infra/scripts/run_seed_vc_demo.ps1`

That run produced:

- final WAV: `data/demo/seed-vc-case-01/output/converted.wav`
- summary: `data/demo/seed-vc-case-01/output/summary.json`
- stdout log: `data/demo/seed-vc-case-01/runtime/logs/4fb97d45-4797-4d1c-a7d1-a8061e984943/20260316T232723320903Z/stdout.log`
- stderr log: `data/demo/seed-vc-case-01/runtime/logs/4fb97d45-4797-4d1c-a7d1-a8061e984943/20260316T232723320903Z/stderr.log`

Observed metrics for that run:

- processing duration: `1481148 ms`
- source duration: `4249 ms`
- reference duration: `10385 ms`
- output duration: `4226 ms`

On this CPU-only host, the first real conversion took about 24 minutes because Seed-VC ran offline without GPU acceleration.

## Full API path

The REST API path is still available and continues to use the same real conversion backend:

1. `POST /api/v1/voice-profiles`
2. `POST /api/v1/voice-profiles/{profile_id}/samples`
3. `POST /api/v1/conversion-jobs`
4. `POST /api/v1/conversion-jobs/{job_id}/process-now`
5. `GET /api/v1/conversion-jobs/{job_id}/outputs`
6. `GET /api/v1/conversion-jobs/{job_id}/outputs/{output_id}/download`

Use this path when PostgreSQL and Redis are available and you want to validate the HTTP boundary as well.

## Failure diagnosis

If the demo fails:

- `runtime_missing`
  - verify `VF_SEED_VC_PYTHON`
  - verify `VF_SEED_VC_REPO_DIR`
  - rerun `infra/scripts/install_seed_vc.ps1`
- `invalid_reference`
  - use clear speech WAVs
  - ensure the reference clips are not empty and survive silence trimming
- `preprocess_failed`
  - confirm the WAVs are readable and not corrupted
  - inspect the adapter log paths from the JSON output
- `inference_failed`
  - inspect `stdout.log`, `stderr.log`, and `run.json`
  - look for upstream checkpoint download failures or model-side exceptions
- `storage_failed`
  - verify the demo case directory is writable
  - verify local filesystem permissions and free space

## Notes

- Temporary working directories are created under `VF_SEED_VC_WORKING_ROOT` and cleaned automatically.
- Subprocess logs are persisted outside the temp workspace before cleanup.
- The adapter performs a runtime import check before starting inference so misconfigured environments fail early and explicitly.

## Sources

- Official Seed-VC repository: [Plachtaa/seed-vc](https://github.com/Plachtaa/seed-vc)
- Official usage reference: [README.md](https://github.com/Plachtaa/seed-vc/blob/main/README.md)
