# Seed-VC Profiling And Benchmarking

This document captures the current profiling surface for the real offline Seed-VC path in VoiceForge, the exact benchmark command, the folder layout it produces, and the first cold vs warm measurements collected in this workspace.

For the follow-up optimization phase with reference cache hits and the resident runtime, see `docs/seed-vc-reference-cache.md`.
For the next phase with source cache hits, the resident-runtime benchmark, and `diffusion_steps` experiments, see `docs/seed-vc-source-optimization.md`.

## What is instrumented

The offline conversion path now records timing and resource estimates for each conversion job.

Persisted on `conversion_jobs.profiling_json`:

- `runtime_bootstrap`
- `source_preprocessing`
- `reference_preprocessing`
- `model_invocation`
- `inference_core`
- `vocoder_postprocess`
- `output_persistence`
- detailed sub-timers from the profiled Seed-VC runner
- process CPU time
- estimated average CPU percent
- peak RSS in MB
- subprocess log artifact paths

Where the metrics come from:

- adapter-side preprocessing and runtime validation are measured in `packages/voiceforge_core/src/voiceforge_core/inference/seed_vc.py`
- upstream model timings are measured inside `packages/voiceforge_core/src/voiceforge_core/inference/seed_vc_profiled_runner.py`
- final persistence and output validation are merged in `packages/voiceforge_core/src/voiceforge_core/modules/conversion_jobs/service.py`

## Benchmark scripts

Primary wrapper:

- `infra/scripts/run_seed_vc_benchmark.ps1`

Underlying runner:

- `infra/scripts/benchmark_seed_vc.py`

The wrapper:

1. validates the configured Seed-VC runtime
2. generates one source WAV plus two reference WAVs
3. runs the same conversion case multiple times
4. forces the first run to start cold by clearing Hugging Face caches
5. keeps the shared runtime directory for warm runs
6. writes a machine-readable summary and a markdown report

## Exact command

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\infra\scripts\run_seed_vc_benchmark.ps1 `
  -SeedVCPython "$env:VF_SEED_VC_PYTHON" `
  -SeedVCRepoDir "$env:VF_SEED_VC_REPO_DIR" `
  -Iterations 2 `
  -Reset
```

## Regenerate the report without rerunning inference

If the benchmark already ran and only the report logic changed, rebuild the summary and markdown report from the captured run payloads:

```powershell
python .\infra\scripts\benchmark_seed_vc.py `
  --existing-summary .\data\bench\seed-vc\benchmark_summary.json
```

## Expected folder layout

```text
data/bench/seed-vc/
|- benchmark_report.md
|- benchmark_summary.json
|- input/
|  |- reference_01.wav
|  |- reference_02.wav
|  |- source.wav
|- runs/
|  |- r01c/
|  |  |- output/
|  |  |  |- converted.wav
|  |  |- storage/
|  |  |- voiceforge_demo.db
|  |- r02w/
|     |- output/
|     |  |- converted.wav
|     |- storage/
|     |- voiceforge_demo.db
|- runtime_shared/
|  |- hf_cache/
|  |- hf_home/
|  |- logs/
|     |- <job_id>/
|        |- <timestamp>/
|           |- run.json
|           |- stderr.log
|           |- stdout.log
```

## Validated benchmark in this workspace

A real two-run benchmark completed in this workspace on March 17, 2026 using:

- Seed-VC repo: `external/seed-vc`
- Seed-VC runtime: `external/seed-vc/.venv/Scripts/python.exe`
- benchmark wrapper: `infra/scripts/run_seed_vc_benchmark.ps1`
- benchmark output dir: `data/bench/seed-vc`

Generated artifacts:

- summary: `data/bench/seed-vc/benchmark_summary.json`
- report: `data/bench/seed-vc/benchmark_report.md`
- cold output WAV: `data/bench/seed-vc/runs/r01c/output/converted.wav`
- warm output WAV: `data/bench/seed-vc/runs/r02w/output/converted.wav`

## Observed totals

- cold run total: `623499 ms`
- warm run total: `611287 ms`
- cold to warm delta: `12212 ms`
- cold to warm delta percent: `1.96%`

Interpretation:

- the cold start penalty is real, but it is not the dominant latency once the job is already running
- after caches are warm, the path remains compute-bound

## Top-level stage timings

These are end-to-end, non-overlapping slices of the offline job.

| Stage | Cold ms | Warm avg ms | Warm share of total |
| --- | ---: | ---: | ---: |
| `runtime_bootstrap` | `39814` | `17539` | `2.87%` |
| `source_preprocessing` | `175836` | `181142` | `29.63%` |
| `reference_preprocessing` | `176149` | `179527` | `29.37%` |
| `model_invocation` | `228084` | `229546` | `37.55%` |
| `output_persistence` | `1` | `2` | `0.00%` |

Warm-path interpretation:

- source plus reference preprocessing account for about `59.00%` of the offline job
- model invocation accounts for about `37.55%`
- persistence is operationally irrelevant on the current path

## Model invocation breakdown

`inference_core` and `vocoder_postprocess` live inside `model_invocation`.

| Component | Cold ms | Warm avg ms | Warm share of model |
| --- | ---: | ---: | ---: |
| `inference_core` | `200075` | `202358` | `88.16%` |
| `vocoder_postprocess` | `27831` | `27033` | `11.78%` |
| `model_invocation_overhead` | `178` | `155` | `0.07%` |

Interpretation:

- once the model is invoked, almost all of the time is inside the core diffusion/inference step
- the vocoder is meaningful but clearly secondary

## Preprocessing detail

The dominant preprocessing cost is semantic extraction, not decode/resample/trim.

| Component | Cold ms | Warm avg ms |
| --- | ---: | ---: |
| `source_decode_resample_trim` | `4` | `4` |
| `source_semantic_extraction` | `175788` | `181128` |
| `source_mel_extraction` | `44` | `10` |
| `reference_decode_resample_trim` | `6` | `7` |
| `reference_semantic_extraction` | `175811` | `179235` |
| `reference_mel_extraction` | `18` | `18` |
| `reference_style_extraction` | `314` | `267` |

Interpretation:

- semantic extraction alone consumes most of source preprocessing and most of reference preprocessing
- basic WAV preparation is effectively free compared with upstream feature extraction

## Estimated CPU and RAM usage

These are per-process estimates taken during the Seed-VC subprocess, not full-host telemetry.

- cold peak RSS: `2892.79 MB`
- warm peak RSS: `2879.01 MB`
- cold CPU time: `579.84 s`
- warm CPU time: `589.27 s`
- cold equivalent busy cores: `0.93`
- warm equivalent busy cores: `0.96`
- host logical CPU count seen by the subprocess: `12`

Interpretation:

- on this CPU-only host, the process behaved close to one saturated core on average
- memory footprint is high enough that worker concurrency must be planned deliberately

## Optimization opportunities

The current data points suggest these priorities:

1. Precompute and cache reference features after sample upload so conversion jobs do not recompute reference semantic extraction every time.
2. Keep the semantic encoder resident inside a dedicated worker process to reduce repeated initialization and repeated feature extraction overhead.
3. Tune Seed-VC compute cost after quality validation:
   lower diffusion steps, mixed precision, and chunk strategy are the most direct knobs.
4. Preserve warm caches across jobs because cold bootstrap still costs about `22.3 s`.
5. Treat output persistence as a low-priority area; it is not where offline latency is being lost.
6. Cap or isolate offline worker concurrency because peak RSS is near `2.9 GB` per job.

## What is still pending

- This benchmark sample size is intentionally small. More iterations are still needed before making queue-level scheduling decisions.
- GPU benchmarking is still pending.
- Host-wide telemetry integration is still pending. Current CPU and RAM figures come from the Seed-VC subprocess only.
- RVC and OpenVoice do not yet participate in the benchmark harness.
