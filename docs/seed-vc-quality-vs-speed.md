# Seed-VC Quality Vs Speed Evaluation

This document captures the current Seed-VC preset evaluation for VoiceForge `studio` mode after both source and reference cache optimizations are active.

The active baseline is the warm offline path with:

- source cache enabled
- reference cache enabled
- current profiling and timing instrumentation enabled
- no architecture changes beyond the existing Seed-VC adapter and benchmark harness

## Experiment scope

Evaluated `diffusion_steps`:

- `25`
- `20`
- `15`
- `10`

Measured for each variant:

- total job time
- `inference_core` time
- reproducible WAV output
- exact config and output path

Artifacts:

- experiment summary:
  - `data/bench/seed-vc-inference/inference_experiments.json`
- experiment report:
  - `data/bench/seed-vc-inference/inference_experiments.md`
- final preset report:
  - `data/bench/seed-vc-quality-eval/quality_vs_speed_report.md`
- manual listening protocol:
  - `data/bench/seed-vc-quality-eval/manual_evaluation_protocol.md`
- manual scorecard:
  - `data/bench/seed-vc-quality-eval/manual_evaluation_scorecard.csv`

## Current measured matrix

Baseline `25` steps:

- total: `306059 ms`
- `inference_core`: `244736 ms`

Variants:

| Steps | Total ms | Total delta vs 25 | Inference core ms | Inference delta vs 25 |
| --- | ---: | ---: | ---: | ---: |
| `20` | `248070` | `18.95%` faster | `193503` | `20.93%` faster |
| `15` | `200861` | `34.37%` faster | `145905` | `40.38%` faster |
| `10` | `151437` | `50.52%` faster | `96640` | `60.51%` faster |

## Quality handling

Automated quality in this phase is intentionally limited to internal stability proxies against the `25`-step baseline:

- log-mel MAE
- MFCC cosine similarity
- RMS delta

These are useful for screening but are not enough to ship a preset decision alone.

For perceptual review, the repository now includes a manual framework with these dimensions:

- similarity with target voice
- intelligibility
- naturality
- artifacts
- prosodic stability

Scale:

- `1` to `5`
- `5` is best

## Recommendation

Current operating recommendation in this environment:

- maximum quality:
  - `25` steps
  - keep as the safest Studio preset when quality is the primary goal
- balance quality/velocity:
  - `20` steps
  - current recommendation because it delivers a meaningful speed win with the smallest reduction from the maximum-quality preset
- fast experimental:
  - `10` steps
  - keep as opt-in only until manual listening confirms artifacts and naturality remain acceptable

## Shipping rule

Do not promote `20` or `10` steps to the default product preset based only on timing and proxy metrics.

Required before shipping:

1. fill `manual_evaluation_scorecard.csv`
2. compare each candidate against the `25`-step baseline and target references
3. review the average perceptual scores
4. only then lock the Studio-mode product presets

## Why this recommendation is conservative

- `25` steps is still the cleanest quality anchor
- `20` steps is the lowest-risk speed tradeoff
- `15` steps is attractive on timing, but it is a stronger quality tradeoff candidate and needs listening approval before becoming operational
- `10` steps is best treated as a fast experiment, not a default
