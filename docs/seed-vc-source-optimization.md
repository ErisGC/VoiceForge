# Seed-VC Source Cache, Resident Runtime, And Inference Experiments

This document captures the next optimization phase after the validated reference cache rollout. The focus here is:

- eliminate repeated `source_preprocessing` cost for repeated inputs
- benchmark the current resident runtime formally
- measure the remaining `inference_core` cost with controlled `diffusion_steps` experiments

For the preset recommendation layer and the manual perceptual evaluation framework built on top of these experiments, see `docs/seed-vc-quality-vs-speed.md`.

## What changed

The architecture stays the same:

- `VoiceConversionEngine` remains the public engine boundary
- Seed-VC remains the real offline implementation behind that boundary
- the worker/API flow and persisted `conversion_jobs.profiling_json` contract stay intact

New implementation pieces:

- generic local runtime feature cache store:
  - `packages/voiceforge_core/src/voiceforge_core/inference/local_feature_cache_store.py`
- source feature cache support in the Seed-VC adapter:
  - `packages/voiceforge_core/src/voiceforge_core/inference/seed_vc.py`
- source cache build support in the profiled runner:
  - `packages/voiceforge_core/src/voiceforge_core/inference/seed_vc_profiled_runner.py`
- source cache build support in the resident runtime sidecar:
  - `packages/voiceforge_core/src/voiceforge_core/inference/seed_vc_reference_runtime.py`
- benchmark and experiment harness updates:
  - `infra/scripts/run_seed_vc_benchmark.ps1`
  - `infra/scripts/benchmark_seed_vc.py`
  - `infra/scripts/experiment_seed_vc_inference_core.py`

## What is cached on the source side

The source cache stores reusable Seed-VC source-side tensors derived from the prepared source WAV:

- `S_alt`
- `mel`
- optional `F0_alt`

Artifact identity:

- namespace: `source_features`
- backend: `seed_vc`
- artifact version: `seed-vc-source-v1`
- format: `pt`

Storage model:

- reference cache remains persisted per `voice_profile` in database-backed storage
- source cache is a backend-local runtime cache on disk under:
  - `data/.../runtime_shared/runtime-feature-caches/seed_vc/source_features/...`

That separation is intentional:

- reference features are profile assets
- source features are transient optimization artifacts keyed by input content plus engine/preprocessor config

## Source cache keying and invalidation

The source cache key includes:

- source audio SHA-256
- source filename and content type
- target sample rate
- `f0_condition`
- checkpoint/config path
- repo identity
- preprocessor settings:
  - `trim_top_db`
  - `target_peak`
  - `frame_length`
  - `hop_length`

This means the source cache is invalidated automatically when:

- the input audio changes
- the preprocessing behavior changes
- the model/runtime identity changes
- the cache artifact version changes

Old local runtime artifacts are currently replaced by new key paths rather than aggressively garbage-collected.

## Runtime flags

Add these to `.env` for API/worker execution:

```env
VF_SEED_VC_REFERENCE_CACHE_ENABLED=true
VF_SEED_VC_SOURCE_CACHE_ENABLED=true
VF_SEED_VC_RESIDENT_REFERENCE_RUNTIME_ENABLED=true
VF_SEED_VC_RESIDENT_SOURCE_RUNTIME_ENABLED=true
VF_SEED_VC_RESIDENT_RUNTIME_IDLE_SECONDS=900
VF_SEED_VC_RESIDENT_RUNTIME_LAUNCH_TIMEOUT_SECONDS=120
```

## Source preprocessing results

Baseline for this phase:

- reference-cache-only warm run:
  - `data/bench/seed-vc-cache/benchmark_summary.json`
  - warm total: `432920 ms`
  - warm `source_preprocessing`: `173968 ms`

New source-cache benchmark:

- `data/bench/seed-vc-source-cache/benchmark_summary.json`
- `data/bench/seed-vc-source-cache/benchmark_report.md`
- `data/bench/seed-vc-source-cache/benchmark_vs_baseline.md`

Observed warm results:

- total: `296851 ms`
- `source_preprocessing`: `10 ms`
- `reference_preprocessing`: `10 ms`
- `model_invocation`: `273632 ms`
- `inference_core`: `239833 ms`

Measured warm improvement vs the previous cache baseline:

- total improvement: `136069 ms`
- total improvement percent: `31.43%`
- `source_preprocessing` improvement: `173958 ms`
- `source_preprocessing` improvement percent: `99.99%`

Interpretation:

- repeated source-side semantic extraction was the correct next bottleneck to remove
- once both caches hit, the offline job is now dominated by `model_invocation`, especially `inference_core`

## Resident runtime benchmark

Resident benchmark artifacts:

- `data/bench/seed-vc-res/benchmark_summary.json`
- `data/bench/seed-vc-res/benchmark_report.md`
- `data/bench/seed-vc-res/benchmark_vs_baseline.md`

Scenario:

- source cache enabled
- reference cache enabled
- resident runtime enabled for both source and reference cache builds

Observed results:

- cold run total: `746789 ms`
- warm run total: `303326 ms`

Comparison against the non-resident source-cache warm path:

- non-resident source-cache warm total: `296851 ms`
- resident warm total: `303326 ms`
- delta: `-6475 ms` (`-2.18%`)

What the resident benchmark shows in the current architecture:

- cold run:
  - `source_cache_prepare`: `240306 ms`
  - `reference_cache_prepare`: `198966 ms`
- warm run:
  - both caches hit and preprocessing stays near zero
- end-to-end warm gain:
  - no material improvement over the already-persisted source-cache path

Interpretation:

- the current resident sidecar is operational and measurable
- it helps move cache builds outside the conversion subprocess
- but it does not yet create a significant end-to-end warm-path win while final Seed-VC inference still happens in a separate subprocess that reboots the full model stack

This is still valuable groundwork for a future fully resident inference worker.

## Inference-core experiments

Artifacts:

- `data/bench/seed-vc-inference/inference_experiments.json`
- `data/bench/seed-vc-inference/inference_experiments.md`

Runtime probe on this host:

- CUDA available: `false`
- CUDA device count: `0`
- `fp16` experiment status: not applicable on this host

Because the current adapter uses `float16` autocast only for GPU execution, mixed precision was intentionally skipped instead of producing a misleading CPU number.

### Controlled diffusion-step results

Baseline:

- `25` steps
- total: `306059 ms`
- `inference_core`: `244736 ms`

Variants:

| Variant | Total ms | Delta vs baseline | Inference core ms | Delta vs baseline | Log-mel MAE | MFCC cosine sim |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `20` steps | `248070` | `-18.95%` | `193503` | `-20.93%` | `4.0604` | `0.999825` |
| `15` steps | `200861` | `-34.37%` | `145905` | `-40.38%` | `4.0209` | `0.999810` |
| `10` steps | `151437` | `-50.52%` | `96640` | `-60.51%` | `3.7349` | `0.999690` |

Quality note:

- `log_mel_mae` and `mfcc_cosine_similarity` are internal stability proxies against the `25`-step baseline output
- they are useful for fast regression screening
- they are not a replacement for subjective listening or MOS-style evaluation

Interpretation:

- lowering `diffusion_steps` produces a direct, monotonic latency win on this host
- the proxy metrics stayed very close to the baseline output in this sample
- subjective listening is still required before changing the production default away from `25`

## Exact commands

### Source-cache benchmark

```powershell
powershell -ExecutionPolicy Bypass -File .\infra\scripts\run_seed_vc_benchmark.ps1 `
  -SeedVCPython "$env:VF_SEED_VC_PYTHON" `
  -SeedVCRepoDir "$env:VF_SEED_VC_REPO_DIR" `
  -BenchmarkDir "data/bench/seed-vc-source-cache" `
  -Iterations 2 `
  -ReferenceCacheEnabled "true" `
  -SourceCacheEnabled "true" `
  -ResidentReferenceRuntimeEnabled "true" `
  -ResidentSourceRuntimeEnabled "false" `
  -BaselineSummary ".\data\bench\seed-vc-cache\benchmark_summary.json" `
  -Reset
```

### Resident benchmark

Use a short output directory on Windows to avoid path-length issues during nested artifact writes.

```powershell
powershell -ExecutionPolicy Bypass -File .\infra\scripts\run_seed_vc_benchmark.ps1 `
  -SeedVCPython "$env:VF_SEED_VC_PYTHON" `
  -SeedVCRepoDir "$env:VF_SEED_VC_REPO_DIR" `
  -BenchmarkDir "data/bench/seed-vc-res" `
  -Iterations 2 `
  -ReferenceCacheEnabled "true" `
  -SourceCacheEnabled "true" `
  -ResidentReferenceRuntimeEnabled "true" `
  -ResidentSourceRuntimeEnabled "true" `
  -BaselineSummary ".\data\bench\seed-vc-source-cache\benchmark_summary.json" `
  -Reset
```

### Inference-core experiment

```powershell
python .\infra\scripts\experiment_seed_vc_inference_core.py `
  --experiment-dir .\data\bench\seed-vc-inference `
  --seed-vc-python "$env:VF_SEED_VC_PYTHON" `
  --seed-vc-repo-dir "$env:VF_SEED_VC_REPO_DIR" `
  --seed-vc-working-root .\data\bench\seed-vc-source-cache\runtime_shared `
  --case-dir .\data\bench\seed-vc-source-cache\shared_case `
  --source-file .\data\bench\seed-vc-source-cache\input\source.wav `
  --reference-file .\data\bench\seed-vc-source-cache\input\reference_01.wav `
  --reference-file .\data\bench\seed-vc-source-cache\input\reference_02.wav `
  --reset
```

## Main takeaways

1. The biggest new win is real and repeatable: source caching removed the remaining preprocessing bottleneck on warm runs.
2. The resident runtime is useful infrastructure, but not yet a major warm-path latency lever while inference still lives in a separate subprocess.
3. The system is now primarily model-bound on warm runs.
4. The next large optimization should target one of these:
   - a truly resident inference worker
   - GPU execution
   - a product-backed reduction of default `diffusion_steps` after subjective quality review
