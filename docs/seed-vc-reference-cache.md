# Seed-VC Reference Cache And Resident Runtime

This document describes the new reference feature cache for Seed-VC, how it is invalidated, how the resident reference runtime works, and what the first optimization benchmark showed in this workspace.

For the follow-up phase with source feature caching, the formal resident-runtime benchmark, and `diffusion_steps` experiments, see `docs/seed-vc-source-optimization.md`.

## What was implemented

The optimization layer keeps the current architecture intact:

- `VoiceConversionEngine` is still the public conversion abstraction.
- the Seed-VC adapter remains the active implementation behind that interface.
- profiling and job observability remain in place.

New pieces:

- `voice_profile_feature_caches` database table
- generic `VoiceProfileFeatureCacheService`
- Seed-VC cache descriptor and artifact generation
- Seed-VC cache consumption path during conversion
- resident reference runtime for reusable semantic/reference components

## What is cached

The cached artifact stores reference-side tensors derived from the prepared reference prompt:

- `S_ori`
- `mel2`
- `style2`
- optional `F0_ori`

Artifact shape:

- namespace: `reference_features`
- backend: `seed_vc`
- artifact version: `seed-vc-ref-v1`
- format: `pt`

These artifacts are persisted per `voice_profile`, not globally.

## Where it lives

Relational metadata:

- `packages/voiceforge_core/src/voiceforge_core/db/models.py`
- `services/api/alembic/versions/20260316_0005_add_voice_profile_feature_caches.py`

Artifact persistence and lookup:

- `packages/voiceforge_core/src/voiceforge_core/modules/feature_caches/service.py`

Seed-VC integration:

- `packages/voiceforge_core/src/voiceforge_core/inference/seed_vc.py`
- `packages/voiceforge_core/src/voiceforge_core/inference/seed_vc_profiled_runner.py`
- `packages/voiceforge_core/src/voiceforge_core/inference/seed_vc_reference_runtime.py`

## Invalidation rules

The cache is invalidated when:

1. a new `voice_sample` is added to the profile
2. the cache artifact version changes
3. the relevant Seed-VC config signature changes
4. the artifact is missing from storage

The sample upload path now invalidates active caches here:

- `packages/voiceforge_core/src/voiceforge_core/modules/voice_samples/service.py`

The config signature currently includes:

- target sample rate
- reference max seconds
- reference clip limit
- `f0_condition`
- checkpoint path
- config path
- repo/runtime identity

## Runtime behavior

### Cache miss

On a cache miss, the Seed-VC adapter can generate a new reference cache artifact and return it to the conversion service, which persists it as a new version.

The first benchmarked cache build in this workspace was generated during the conversion subprocess and persisted as:

- storage key: `feature-caches/e9a3e499-d7c2-460a-a169-bc6b68fbc766/seed_vc/reference_features/v0001_ac065b3786e9_833e404d92af.pt`

### Cache hit

On a cache hit, the adapter injects the artifact into the Seed-VC runner and the runner skips:

- reference semantic extraction
- reference mel extraction
- reference style extraction
- optional reference F0 extraction

The runner still performs lightweight prompt WAV preparation and cache load.

## Resident reference runtime

The resident runtime is a small sidecar process in the external Seed-VC Python environment. It keeps the heavy reference-side components loaded so repeated cache builds do not re-bootstrap them from scratch.

Implementation:

- `packages/voiceforge_core/src/voiceforge_core/inference/seed_vc_reference_runtime.py`

Adapter integration:

- `packages/voiceforge_core/src/voiceforge_core/inference/seed_vc.py`

Current role:

- build reference cache artifacts through a long-lived runtime
- keep semantic and style extraction components warm between cache build requests

## Environment flags

Add these to `.env` when running API or worker:

```env
VF_SEED_VC_REFERENCE_CACHE_ENABLED=true
VF_SEED_VC_RESIDENT_REFERENCE_RUNTIME_ENABLED=true
VF_SEED_VC_RESIDENT_RUNTIME_IDLE_SECONDS=900
VF_SEED_VC_RESIDENT_RUNTIME_LAUNCH_TIMEOUT_SECONDS=120
```

## Benchmark results

Baseline summary:

- `data/bench/seed-vc/benchmark_summary.json`

Optimized summary:

- `data/bench/seed-vc-cache/benchmark_summary.json`
- `data/bench/seed-vc-cache/benchmark_report.md`
- `data/bench/seed-vc-cache/benchmark_vs_baseline.md`

### Baseline warm path

- total: `611287 ms`
- `reference_preprocessing`: `179527 ms`

### Cache-enabled warm path

- total: `432920 ms`
- `reference_preprocessing`: `12 ms`
- `reference_cache_hit`: `1`

### Improvement

- total improvement: `178367 ms`
- total improvement percent: `29.18%`
- `reference_preprocessing` improvement: `179515 ms`
- `reference_preprocessing` improvement percent: `99.99%`

Interpretation:

- the reference cache removed the repeated reference-side bottleneck almost entirely
- after that win, the next dominant stage is source-side semantic extraction

## Cache-enabled benchmark command

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\infra\scripts\run_seed_vc_benchmark.ps1 `
  -SeedVCPython "$env:VF_SEED_VC_PYTHON" `
  -SeedVCRepoDir "$env:VF_SEED_VC_REPO_DIR" `
  -BenchmarkDir "data/bench/seed-vc-cache" `
  -Iterations 2 `
  -ReferenceCacheEnabled "true" `
  -ResidentReferenceRuntimeEnabled "true" `
  -BaselineSummary ".\data\bench\seed-vc\benchmark_summary.json" `
  -Reset
```

## Resident runtime validation command

The resident runtime path was also validated directly after fixing its request timeout handling.

Observed successful result:

- artifact count: `1`
- namespace: `reference_features`
- resident runtime build total: `174112 ms`

That validation reused the same workspace inputs from `data/bench/seed-vc-cache/input/`.

## Consistency risks

- If voice samples are changed outside the service path, the DB invalidation hook will not fire.
- The cache is keyed to the selected reference sample set. If selection policy changes in the future, the cache signature logic must change with it.
- The first post-invalidation conversion may still pay cache rebuild cost if the profile was not pre-warmed ahead of time.
- Old artifacts are invalidated, not deleted. Storage cleanup is still a follow-up item.

## Immediate next optimization target

After this change, the clearest next target is source-side semantic extraction. The current benchmark shows it now dominates the preprocessing budget once reference cache hits are in place.
