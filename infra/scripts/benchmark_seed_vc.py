from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_SCRIPT = REPO_ROOT / "infra" / "scripts" / "demo_seed_vc_e2e.py"

STAGE_ORDER = [
    "runtime_bootstrap",
    "source_preprocessing",
    "reference_preprocessing",
    "model_invocation",
    "inference_core",
    "vocoder_postprocess",
    "output_persistence",
]

TOP_LEVEL_STAGE_ORDER = [
    "runtime_bootstrap",
    "source_preprocessing",
    "reference_preprocessing",
    "model_invocation",
    "output_persistence",
]

MODEL_INVOCATION_BREAKDOWN_ORDER = [
    "inference_core",
    "vocoder_postprocess",
    "model_invocation_overhead",
]

PREPROCESS_DETAIL_ORDER = [
    "adapter_source_preprocessing",
    "source_cache_prepare",
    "source_cache_load",
    "source_semantic_extraction",
    "source_mel_extraction",
    "source_f0_extraction",
    "source_cache_save",
    "reference_cache_prepare",
    "reference_cache_load",
    "adapter_reference_preprocessing",
    "reference_semantic_extraction",
    "reference_mel_extraction",
    "reference_style_extraction",
    "reference_f0_extraction",
    "reference_f0_alignment",
]

DETAIL_LABELS = {
    "adapter_source_preprocessing": "source_decode_resample_trim",
    "source_cache_prepare": "source_cache_prepare",
    "source_cache_load": "source_cache_load",
    "source_semantic_extraction": "source_semantic_extraction",
    "source_mel_extraction": "source_mel_extraction",
    "source_f0_extraction": "source_f0_extraction",
    "source_cache_save": "source_cache_save",
    "reference_cache_prepare": "reference_cache_prepare",
    "reference_cache_load": "reference_cache_load",
    "adapter_reference_preprocessing": "reference_decode_resample_trim",
    "reference_semantic_extraction": "reference_semantic_extraction",
    "reference_mel_extraction": "reference_mel_extraction",
    "reference_style_extraction": "reference_style_extraction",
    "reference_f0_extraction": "reference_f0_extraction",
    "reference_f0_alignment": "reference_f0_alignment",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark VoiceForge Seed-VC cold vs warm runs.")
    parser.add_argument("--benchmark-dir")
    parser.add_argument("--existing-summary")
    parser.add_argument("--baseline-summary")
    parser.add_argument("--seed-vc-python")
    parser.add_argument("--seed-vc-repo-dir")
    parser.add_argument("--source-file")
    parser.add_argument("--reference-file", action="append")
    parser.add_argument("--iterations", type=int, default=2)
    parser.add_argument("--voiceforge-python", default=sys.executable)
    parser.add_argument("--reference-cache-enabled", default="true")
    parser.add_argument("--source-cache-enabled", default="true")
    parser.add_argument("--resident-reference-runtime-enabled", default="true")
    parser.add_argument("--resident-source-runtime-enabled", default="true")
    parser.add_argument("--diffusion-steps", type=int, default=25)
    parser.add_argument("--fp16", default="false")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    if args.existing_summary:
        summary_path = Path(args.existing_summary).expanduser()
        if not summary_path.exists():
            parser.error(f"--existing-summary does not exist: {summary_path}")
        if not args.benchmark_dir:
            args.benchmark_dir = str(summary_path.resolve().parent)
        return args

    missing: list[str] = []
    for argument_name in ("benchmark_dir", "seed_vc_python", "seed_vc_repo_dir", "source_file"):
        if not getattr(args, argument_name):
            missing.append(f"--{argument_name.replace('_', '-')}")
    if not args.reference_file:
        missing.append("--reference-file")
    if missing:
        parser.error(
            "The following arguments are required unless --existing-summary is used: " + ", ".join(missing)
        )
    return args


def average(values: list[float | int | None]) -> float | None:
    filtered = [float(value) for value in values if value is not None]
    if not filtered:
        return None
    return round(sum(filtered) / len(filtered), 2)


def format_value(value: float | int | str | None) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def processing_total_ms(run: dict | None) -> int | None:
    if run is None:
        return None
    value = run.get("processing_duration_ms")
    return int(value) if value is not None else None


def stage_value(run: dict, stage_name: str) -> int | None:
    profiling = run.get("profiling_json") or {}
    stages = profiling.get("stages_ms") or {}
    details = profiling.get("details_ms") or {}

    if stage_name == "runtime_bootstrap" and (
        "runtime_validation" in details or "subprocess_runtime_bootstrap" in details
    ):
        return int(details.get("runtime_validation", 0)) + int(details.get("subprocess_runtime_bootstrap", 0))

    if stage_name == "source_preprocessing" and details:
        adapter_value = details.get("adapter_source_preprocessing", stages.get(stage_name, 0))
        return (
            int(adapter_value)
            + int(details.get("source_cache_prepare", 0))
            + int(details.get("source_cache_load", 0))
            + int(details.get("source_semantic_extraction", 0))
            + int(details.get("source_mel_extraction", 0))
            + int(details.get("source_f0_extraction", 0))
        )

    if stage_name == "reference_preprocessing" and details:
        adapter_value = details.get("adapter_reference_preprocessing", stages.get(stage_name, 0))
        return (
            int(adapter_value)
            + int(details.get("reference_cache_prepare", 0))
            + int(details.get("reference_cache_load", 0))
            + int(details.get("reference_semantic_extraction", 0))
            + int(details.get("reference_mel_extraction", 0))
            + int(details.get("reference_style_extraction", 0))
            + int(details.get("reference_f0_extraction", 0))
            + int(details.get("reference_f0_alignment", 0))
        )

    value = stages.get(stage_name)
    return int(value) if value is not None else None


def detail_value(run: dict, detail_name: str) -> int | None:
    profiling = run.get("profiling_json") or {}
    details = profiling.get("details_ms") or {}
    stages = profiling.get("stages_ms") or {}
    value = details.get(detail_name)
    if value is None and detail_name == "adapter_source_preprocessing":
        value = stages.get("source_preprocessing")
    if value is None and detail_name == "adapter_reference_preprocessing":
        value = stages.get("reference_preprocessing")
    return int(value) if value is not None else None


def resource_value(run: dict | None, key: str) -> float | None:
    if run is None:
        return None
    profiling = run.get("profiling_json") or {}
    resources = profiling.get("resources") or {}
    value = resources.get(key)
    return float(value) if value is not None else None


def stage_share_of_total(run: dict, stage_name: str) -> float | None:
    total_ms = processing_total_ms(run)
    stage_ms = stage_value(run, stage_name)
    if total_ms in (None, 0) or stage_ms is None:
        return None
    return round((stage_ms / total_ms) * 100, 2)


def invocation_overhead_ms(run: dict) -> int | None:
    model_invocation_ms = stage_value(run, "model_invocation")
    if model_invocation_ms is None:
        return None
    inference_core_ms = stage_value(run, "inference_core") or 0
    vocoder_postprocess_ms = stage_value(run, "vocoder_postprocess") or 0
    return max(model_invocation_ms - inference_core_ms - vocoder_postprocess_ms, 0)


def invocation_component_ms(run: dict, component_name: str) -> int | None:
    if component_name == "model_invocation_overhead":
        return invocation_overhead_ms(run)
    return stage_value(run, component_name)


def invocation_component_share(run: dict, component_name: str) -> float | None:
    model_invocation_ms = stage_value(run, "model_invocation")
    component_ms = invocation_component_ms(run, component_name)
    if model_invocation_ms in (None, 0) or component_ms is None:
        return None
    return round((component_ms / model_invocation_ms) * 100, 2)


def equivalent_busy_cores(run: dict | None) -> float | None:
    cpu_time_seconds = resource_value(run, "cpu_time_seconds")
    total_ms = processing_total_ms(run)
    if cpu_time_seconds is None or total_ms in (None, 0):
        return None
    return round(cpu_time_seconds / (total_ms / 1000), 2)


def analyze_opportunities(runs: list[dict]) -> list[str]:
    if not runs:
        return []
    warm_runs = runs[1:] or runs
    warm_stage_avgs = {
        stage: average([stage_value(run, stage) for run in warm_runs if stage_value(run, stage) is not None])
        for stage in STAGE_ORDER
    }
    opportunities: list[str] = []

    model_invocation_avg = warm_stage_avgs.get("model_invocation") or 0
    inference_core_avg = warm_stage_avgs.get("inference_core") or 0
    runtime_bootstrap_cold = stage_value(runs[0], "runtime_bootstrap") or 0
    runtime_bootstrap_warm = warm_stage_avgs.get("runtime_bootstrap") or 0
    source_pre_avg = warm_stage_avgs.get("source_preprocessing") or 0
    reference_pre_avg = warm_stage_avgs.get("reference_preprocessing") or 0
    total_warm = average([processing_total_ms(run) for run in warm_runs]) or 0
    total_cold = processing_total_ms(runs[0]) or 0
    warm_semantic_avg = average(
        [
            (detail_value(run, "source_semantic_extraction") or 0)
            + (detail_value(run, "reference_semantic_extraction") or 0)
            for run in warm_runs
        ]
    ) or 0
    warm_peak_rss_avg = average([resource_value(run, "peak_rss_mb") for run in warm_runs])
    warm_source_cache_hit = average([detail_value(run, "source_cache_hit") for run in warm_runs]) or 0
    warm_reference_cache_hit = average([detail_value(run, "reference_cache_hit") for run in warm_runs]) or 0

    if total_warm and source_pre_avg / total_warm < 0.05 and reference_pre_avg / total_warm < 0.05:
        opportunities.append(
            "Source and reference preprocessing are both near-eliminated on warm runs. The remaining dominant target is the inference core inside model invocation."
        )
    if total_warm and reference_pre_avg / total_warm < 0.1 and warm_reference_cache_hit >= 1 and source_pre_avg / total_warm >= 0.1:
        opportunities.append(
            "Reference preprocessing is now materially reduced on cache hits. The next best optimization target is source-side semantic extraction."
        )
    if total_warm and source_pre_avg / total_warm > 0.25:
        opportunities.append(
            "Source preprocessing now dominates more clearly. If more latency reduction is needed, the next major lever is source semantic feature reuse or a resident source-side encoder path."
        )
    if total_warm and source_pre_avg / total_warm < 0.05 and warm_source_cache_hit >= 1:
        opportunities.append(
            "Source feature caching is doing its job on repeated inputs. Additional warm-run wins will now come mostly from model-side changes, not audio preprocessing."
        )
    if total_warm and warm_semantic_avg / total_warm > 0.25:
        opportunities.append(
            "Semantic extraction remains a heavy compute consumer even after reference cache hits. Keeping the semantic encoder resident is still valuable for future source-side optimization."
        )
    if model_invocation_avg and inference_core_avg / model_invocation_avg > 0.7:
        opportunities.append(
            "The inference core is still the largest share inside model invocation. Candidate optimizations: lower diffusion steps, chunk strategy tuning, and mixed precision once accuracy is validated."
        )
    if runtime_bootstrap_cold and runtime_bootstrap_warm and runtime_bootstrap_cold > runtime_bootstrap_warm * 1.5:
        opportunities.append(
            "Cold bootstrap is materially slower than warm bootstrap. Reusing model weights and preserving Hugging Face caches is still a clear win."
        )
    if total_cold and total_warm and ((total_cold - total_warm) / total_cold) < 0.05:
        opportunities.append(
            "Warm runs only improved modestly, so the remaining latency is mostly real compute. After caches are hot, larger gains will require model-side or hardware-side changes."
        )
    if warm_peak_rss_avg and warm_peak_rss_avg > 2500:
        opportunities.append(
            "Peak RSS is near 2.9 GB per offline job. Plan worker concurrency carefully or isolate Seed-VC into a dedicated pool before scaling CPU execution."
        )
    output_persist_avg = warm_stage_avgs.get("output_persistence") or 0
    if total_warm and output_persist_avg / total_warm < 0.02:
        opportunities.append("Output persistence is a low-priority optimization target on the current offline path.")
    return opportunities


def build_benchmark_summary(runs: list[dict]) -> dict:
    cold_run = runs[0] if runs else None
    warm_runs = runs[1:]
    cold_total = processing_total_ms(cold_run)
    warm_total = average([processing_total_ms(run) for run in warm_runs])
    delta_total_ms = round((cold_total or 0) - (warm_total or 0), 2) if cold_run and warm_total is not None else None
    delta_total_pct = round((delta_total_ms / cold_total) * 100, 2) if cold_total and delta_total_ms is not None else None

    return {
        "iterations": len(runs),
        "runs": runs,
        "cold_run_total_ms": cold_total,
        "warm_run_average_total_ms": warm_total,
        "cold_vs_warm_delta_ms": delta_total_ms,
        "cold_vs_warm_delta_pct": delta_total_pct,
        "stage_comparison_ms": {
            stage: {
                "cold": stage_value(runs[0], stage) if runs else None,
                "warm_avg": average([stage_value(run, stage) for run in warm_runs if stage_value(run, stage) is not None]),
            }
            for stage in STAGE_ORDER
        },
        "top_level_stage_share_pct": {
            stage: {
                "cold": stage_share_of_total(runs[0], stage) if runs else None,
                "warm_avg": average(
                    [stage_share_of_total(run, stage) for run in warm_runs if stage_share_of_total(run, stage) is not None]
                ),
            }
            for stage in TOP_LEVEL_STAGE_ORDER
        },
        "model_invocation_breakdown_ms": {
            component: {
                "cold": invocation_component_ms(runs[0], component) if runs else None,
                "warm_avg": average(
                    [
                        invocation_component_ms(run, component)
                        for run in warm_runs
                        if invocation_component_ms(run, component) is not None
                    ]
                ),
                "cold_share_of_model_pct": invocation_component_share(runs[0], component) if runs else None,
                "warm_avg_share_of_model_pct": average(
                    [
                        invocation_component_share(run, component)
                        for run in warm_runs
                        if invocation_component_share(run, component) is not None
                    ]
                ),
            }
            for component in MODEL_INVOCATION_BREAKDOWN_ORDER
        },
        "preprocess_detail_ms": {
            detail: {
                "cold": detail_value(runs[0], detail) if runs else None,
                "warm_avg": average([detail_value(run, detail) for run in warm_runs if detail_value(run, detail) is not None]),
            }
            for detail in PREPROCESS_DETAIL_ORDER
        },
        "resources": {
            "cold_peak_rss_mb": resource_value(runs[0], "peak_rss_mb") if runs else None,
            "warm_avg_peak_rss_mb": average(
                [resource_value(run, "peak_rss_mb") for run in warm_runs if resource_value(run, "peak_rss_mb") is not None]
            ),
            "cold_cpu_time_seconds": resource_value(runs[0], "cpu_time_seconds") if runs else None,
            "warm_avg_cpu_time_seconds": average(
                [resource_value(run, "cpu_time_seconds") for run in warm_runs if resource_value(run, "cpu_time_seconds") is not None]
            ),
            "cold_estimated_avg_cpu_percent": resource_value(runs[0], "estimated_avg_cpu_percent") if runs else None,
            "warm_avg_estimated_avg_cpu_percent": average(
                [
                    resource_value(run, "estimated_avg_cpu_percent")
                    for run in warm_runs
                    if resource_value(run, "estimated_avg_cpu_percent") is not None
                ]
            ),
            "cold_equivalent_busy_cores": equivalent_busy_cores(runs[0]) if runs else None,
            "warm_avg_equivalent_busy_cores": average(
                [equivalent_busy_cores(run) for run in warm_runs if equivalent_busy_cores(run) is not None]
            ),
        },
        "optimization_opportunities": analyze_opportunities(runs),
    }


def build_markdown_report(runs: list[dict], *, report_path: Path) -> str:
    cold_run = runs[0] if runs else None
    warm_runs = runs[1:]
    cold_total = processing_total_ms(cold_run)
    warm_total = average([processing_total_ms(run) for run in warm_runs])
    total_delta_ms = round((cold_total or 0) - (warm_total or 0), 2) if cold_run and warm_total is not None else None
    total_delta_pct = round((total_delta_ms / cold_total) * 100, 2) if cold_total and total_delta_ms is not None else None

    lines = [
        "# Seed-VC Benchmark Report",
        "",
        f"Generated at `{report_path}`.",
        "",
    ]

    if cold_run:
        lines.extend(
            [
                "## Run Summary",
                "",
                f"- Iterations: `{len(runs)}`",
                f"- Cold run total: `{format_value(cold_total)} ms`",
                f"- Warm run average total: `{format_value(warm_total)} ms`",
                f"- Cold to warm delta: `{format_value(total_delta_ms)} ms` (`{format_value(total_delta_pct)}%`)",
                f"- Cold run peak RSS: `{format_value(resource_value(cold_run, 'peak_rss_mb'))} MB`",
                f"- Warm run average peak RSS: `{format_value(average([resource_value(run, 'peak_rss_mb') for run in warm_runs]))} MB`",
                f"- Cold run CPU time: `{format_value(resource_value(cold_run, 'cpu_time_seconds'))} s`",
                f"- Warm run average CPU time: `{format_value(average([resource_value(run, 'cpu_time_seconds') for run in warm_runs]))} s`",
                f"- Cold run equivalent busy cores: `{format_value(equivalent_busy_cores(cold_run))}`",
                f"- Warm run average equivalent busy cores: `{format_value(average([equivalent_busy_cores(run) for run in warm_runs]))}`",
                "",
                "## Per Run",
                "",
                "| Run | Cache state | Cache hits | Total ms | Peak RSS MB | CPU time s | Avg CPU % | Busy cores |",
                "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for index, run in enumerate(runs, start=1):
            profiling = run.get("profiling_json") or {}
            details = profiling.get("details_ms") or {}
            cache_state = profiling.get("cache_state_before_run")
            lines.append(
                f"| `{index}` | `{cache_state}` | `src:{format_value(details.get('source_cache_hit'))} / ref:{format_value(details.get('reference_cache_hit'))}` | "
                f"`{format_value(processing_total_ms(run))}` | `{format_value(resource_value(run, 'peak_rss_mb'))}` | "
                f"`{format_value(resource_value(run, 'cpu_time_seconds'))}` | `{format_value(resource_value(run, 'estimated_avg_cpu_percent'))}` | "
                f"`{format_value(equivalent_busy_cores(run))}` |"
            )

        lines.extend(
            [
                "",
                "## Top-Level Stage Comparison",
                "",
                "These stages are end-to-end, non-overlapping slices of the offline job.",
                "",
                "| Stage | Cold ms | Cold % total | Warm avg ms | Warm % total | Delta ms | Delta % |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for stage in TOP_LEVEL_STAGE_ORDER:
            cold_value = stage_value(cold_run, stage) or 0
            warm_avg = average([stage_value(run, stage) for run in warm_runs if stage_value(run, stage) is not None])
            warm_number = warm_avg or 0
            delta_ms = round(cold_value - warm_number, 2)
            delta_pct = round((delta_ms / cold_value) * 100, 2) if cold_value else 0.0
            lines.append(
                f"| `{stage}` | `{format_value(cold_value)}` | `{format_value(stage_share_of_total(cold_run, stage))}` | "
                f"`{format_value(warm_avg)}` | `{format_value(average([stage_share_of_total(run, stage) for run in warm_runs]))}` | "
                f"`{format_value(delta_ms)}` | `{format_value(delta_pct)}` |"
            )

        lines.extend(
            [
                "",
                "## Model Invocation Breakdown",
                "",
                "`inference_core` and `vocoder_postprocess` are nested inside `model_invocation`.",
                "",
                "| Component | Cold ms | Cold % of model | Warm avg ms | Warm % of model |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for component in MODEL_INVOCATION_BREAKDOWN_ORDER:
            lines.append(
                f"| `{component}` | `{format_value(invocation_component_ms(cold_run, component))}` | "
                f"`{format_value(invocation_component_share(cold_run, component))}` | "
                f"`{format_value(average([invocation_component_ms(run, component) for run in warm_runs]))}` | "
                f"`{format_value(average([invocation_component_share(run, component) for run in warm_runs]))}` |"
            )

        lines.extend(
            [
                "",
                "## Preprocessing Detail",
                "",
                "| Component | Cold ms | Warm avg ms |",
                "| --- | ---: | ---: |",
            ]
        )
        for detail_name in PREPROCESS_DETAIL_ORDER:
            lines.append(
                f"| `{DETAIL_LABELS.get(detail_name, detail_name)}` | "
                f"`{format_value(detail_value(cold_run, detail_name))}` | "
                f"`{format_value(average([detail_value(run, detail_name) for run in warm_runs]))}` |"
            )

    opportunities = analyze_opportunities(runs)
    lines.extend(["", "## Optimization Opportunities", ""])
    if opportunities:
        for item in opportunities:
            lines.append(f"- {item}")
    else:
        lines.append("- No clear opportunity signal was detected from the current sample size.")
    lines.append("")
    return "\n".join(lines)


def load_existing_runs(summary_path: Path) -> list[dict]:
    existing_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    runs = existing_summary.get("runs") or []
    if not runs:
        raise ValueError(f"No runs were found inside {summary_path}.")
    return runs


def load_existing_summary(summary_path: Path) -> dict:
    return json.loads(summary_path.read_text(encoding="utf-8"))


def build_baseline_comparison_report(
    baseline_summary: dict,
    current_summary: dict,
    *,
    report_path: Path,
) -> str:
    baseline_total = baseline_summary.get("warm_run_average_total_ms")
    current_total = current_summary.get("warm_run_average_total_ms")
    delta_ms = round(float(baseline_total) - float(current_total), 2) if baseline_total and current_total else None
    delta_pct = round((delta_ms / float(baseline_total)) * 100, 2) if baseline_total and delta_ms is not None else None
    lines = [
        "# Seed-VC Baseline Comparison",
        "",
        f"Generated at `{report_path}`.",
        "",
        f"- Warm total baseline: `{format_value(baseline_total)} ms`",
        f"- Warm total current: `{format_value(current_total)} ms`",
        f"- Improvement: `{format_value(delta_ms)} ms` (`{format_value(delta_pct)}%`)",
        "",
        "## Stage Comparison",
        "",
        "| Stage | Baseline warm ms | Current warm ms | Improvement ms | Improvement % |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for stage in TOP_LEVEL_STAGE_ORDER:
        baseline_stage = ((baseline_summary.get("stage_comparison_ms") or {}).get(stage) or {}).get("warm_avg")
        current_stage = ((current_summary.get("stage_comparison_ms") or {}).get(stage) or {}).get("warm_avg")
        if baseline_stage is None or current_stage is None:
            improvement_ms = None
            improvement_pct = None
        else:
            improvement_ms = round(float(baseline_stage) - float(current_stage), 2)
            improvement_pct = round((improvement_ms / float(baseline_stage)) * 100, 2) if float(baseline_stage) else None
        lines.append(
            f"| `{stage}` | `{format_value(baseline_stage)}` | `{format_value(current_stage)}` | "
            f"`{format_value(improvement_ms)}` | `{format_value(improvement_pct)}` |"
        )
    lines.append("")
    return "\n".join(lines)


def execute_runs(args: argparse.Namespace, *, benchmark_dir: Path) -> list[dict]:
    source_file = Path(args.source_file).expanduser().resolve()
    reference_files = [Path(item).expanduser().resolve() for item in args.reference_file]
    runtime_shared = benchmark_dir / "runtime_shared"
    runs_dir = benchmark_dir / "runs"
    shared_case_dir = benchmark_dir / "shared_case"

    if args.reset and benchmark_dir.exists():
        shutil.rmtree(benchmark_dir)
    benchmark_dir.mkdir(parents=True, exist_ok=True)
    runs_dir.mkdir(parents=True, exist_ok=True)
    runtime_shared.mkdir(parents=True, exist_ok=True)

    if not source_file.exists():
        raise FileNotFoundError(f"Source audio was not found: {source_file}")
    for reference_file in reference_files:
        if not reference_file.exists():
            raise FileNotFoundError(f"Reference audio was not found: {reference_file}")

    cold_cache_candidates = [
        runtime_shared / "hf_cache",
        runtime_shared / "hf_home",
        Path(args.seed_vc_repo_dir).expanduser().resolve() / "checkpoints" / "hf_cache",
    ]
    for candidate in cold_cache_candidates:
        if candidate.exists():
            shutil.rmtree(candidate, ignore_errors=True)

    runs: list[dict] = []
    for run_index in range(1, args.iterations + 1):
        label = "cold" if run_index == 1 else "warm"
        snapshot_dir = runs_dir / (f"r{run_index:02d}c" if label == "cold" else f"r{run_index:02d}w")
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        reuse_profile = run_index > 1 or shared_case_dir.exists()
        command = [
            args.voiceforge_python,
            str(DEMO_SCRIPT),
            "--case-dir",
            str(shared_case_dir),
            "--seed-vc-python",
            args.seed_vc_python,
            "--seed-vc-repo-dir",
            args.seed_vc_repo_dir,
            "--seed-vc-working-root",
            str(runtime_shared),
            "--source-file",
            str(source_file),
            "--voiceforge-bucket",
            "vfbench",
            "--email",
            "benchmark@voiceforge.dev",
            "--display-name",
            "VoiceForge Benchmark",
            "--profile-name",
            "SeedVC Benchmark Shared",
            "--reference-cache-enabled",
            args.reference_cache_enabled,
            "--source-cache-enabled",
            args.source_cache_enabled,
            "--resident-reference-runtime-enabled",
            args.resident_reference_runtime_enabled,
            "--resident-source-runtime-enabled",
            args.resident_source_runtime_enabled,
            "--diffusion-steps",
            str(args.diffusion_steps),
            "--fp16",
            args.fp16,
        ]
        if args.reset and run_index == 1:
            command.append("--reset")
        if reuse_profile:
            command.append("--reuse-profile")
        for reference_file in reference_files:
            command.extend(["--reference-file", str(reference_file)])

        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "Benchmark run failed.\n"
                f"Run: {run_index}\n"
                f"STDOUT:\n{completed.stdout}\n"
                f"STDERR:\n{completed.stderr}"
            )
        summary = json.loads(completed.stdout)
        summary["benchmark_run_index"] = run_index
        summary["benchmark_label"] = label
        summary["source_cache_enabled"] = args.source_cache_enabled
        summary["reference_cache_enabled"] = args.reference_cache_enabled
        summary["resident_source_runtime_enabled"] = args.resident_source_runtime_enabled
        summary["resident_reference_runtime_enabled"] = args.resident_reference_runtime_enabled
        summary["diffusion_steps"] = args.diffusion_steps
        summary["fp16"] = args.fp16
        published_output_path = Path(summary.get("published_output_path", ""))
        if published_output_path.exists():
            shutil.copy2(published_output_path, snapshot_dir / "converted.wav")
        shared_summary_path = shared_case_dir / "output" / "summary.json"
        if shared_summary_path.exists():
            shutil.copy2(shared_summary_path, snapshot_dir / "summary.json")
        runs.append(summary)
    return runs


def main() -> int:
    args = parse_args()
    benchmark_dir = Path(args.benchmark_dir).expanduser().resolve()
    report_path = benchmark_dir / "benchmark_report.md"
    summary_path = benchmark_dir / "benchmark_summary.json"
    baseline_report_path = benchmark_dir / "benchmark_vs_baseline.md"

    if args.existing_summary:
        runs = load_existing_runs(Path(args.existing_summary).expanduser().resolve())
    else:
        runs = execute_runs(args, benchmark_dir=benchmark_dir)

    benchmark_dir.mkdir(parents=True, exist_ok=True)
    benchmark_summary = build_benchmark_summary(runs)
    benchmark_summary["summary_path"] = str(summary_path)
    benchmark_summary["source_cache_enabled"] = args.source_cache_enabled
    benchmark_summary["reference_cache_enabled"] = args.reference_cache_enabled
    benchmark_summary["resident_source_runtime_enabled"] = args.resident_source_runtime_enabled
    benchmark_summary["resident_reference_runtime_enabled"] = args.resident_reference_runtime_enabled
    benchmark_summary["diffusion_steps"] = args.diffusion_steps
    benchmark_summary["fp16"] = args.fp16
    if args.baseline_summary:
        benchmark_summary["baseline_summary_path"] = str(Path(args.baseline_summary).expanduser().resolve())

    report = build_markdown_report(runs, report_path=report_path)
    report_path.write_text(report, encoding="utf-8")
    summary_path.write_text(json.dumps(benchmark_summary, indent=2), encoding="utf-8")
    if args.baseline_summary:
        baseline_summary = load_existing_summary(Path(args.baseline_summary).expanduser().resolve())
        baseline_report = build_baseline_comparison_report(
            baseline_summary,
            benchmark_summary,
            report_path=baseline_report_path,
        )
        baseline_report_path.write_text(baseline_report, encoding="utf-8")
    print(
        json.dumps(
            {
                "benchmark_summary_path": str(summary_path),
                "benchmark_report_path": str(report_path),
                "baseline_report_path": str(baseline_report_path) if args.baseline_summary else None,
                "iterations": len(runs),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
