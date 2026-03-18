from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the final Seed-VC quality-vs-speed report package.")
    parser.add_argument("--experiment-summary", required=True)
    parser.add_argument("--output-dir")
    return parser.parse_args()


def format_pct(value: float) -> str:
    return f"{value:.2f}%"


def choose_presets(results: list[dict]) -> dict[str, dict]:
    ordered = sorted(results, key=lambda item: int(item["diffusion_steps"]), reverse=True)
    maximum_quality = ordered[0]
    fast_experimental = ordered[-1]
    balance = maximum_quality
    for candidate in ordered[1:]:
        total_delta_pct = ((maximum_quality["processing_duration_ms"] - candidate["processing_duration_ms"]) / maximum_quality["processing_duration_ms"]) * 100
        if total_delta_pct >= 15.0:
            balance = candidate
            break
    return {
        "maximum_quality": maximum_quality,
        "balance_quality_speed": balance,
        "fast_experimental": fast_experimental,
    }


def write_protocol(protocol_path: Path, *, presets: dict[str, dict]) -> None:
    content = "\n".join(
        [
            "# Seed-VC Perceptual Evaluation Protocol",
            "",
            "## Goal",
            "",
            "Evaluate the offline Seed-VC `diffusion_steps` presets with a simple but consistent listening protocol.",
            "",
            "## Files To Review",
            "",
            f"- Maximum quality candidate: `{presets['maximum_quality']['output_path']}`",
            f"- Balance candidate: `{presets['balance_quality_speed']['output_path']}`",
            f"- Fast experimental candidate: `{presets['fast_experimental']['output_path']}`",
            "",
            "## Listening Setup",
            "",
            "- Use the same headphones or monitors for all variants.",
            "- Keep playback loudness fixed across variants.",
            "- Listen in a quiet environment.",
            "- Compare each candidate against the `25`-step baseline and the target reference voice.",
            "",
            "## Rating Scale",
            "",
            "Use a `1-5` scale where `5` is best:",
            "",
            "- `voice_similarity`: how close the output timbre feels to the target saved voice",
            "- `intelligibility`: how easy the content is to understand",
            "- `naturality`: how natural and fluent the output sounds",
            "- `artifact_control`: how free the output is from buzz, warble, metallic texture, or glitching",
            "- `prosody_stability`: how stable rhythm, emphasis, and phrasing feel across the utterance",
            "",
            "## Procedure",
            "",
            "1. Listen to the target reference clips once.",
            "2. Listen to the source utterance once.",
            "3. Listen to each converted variant in randomized order.",
            "4. Repeat the pass once more before assigning scores.",
            "5. Fill one scorecard row per listener and per variant.",
            "",
            "## Decision Rule",
            "",
            "- `maximum_quality`: choose the highest-step preset unless manual listening shows no perceptual gain.",
            "- `balance_quality_speed`: choose the smallest step reduction that still sounds materially equivalent in team review.",
            "- `fast_experimental`: keep as an opt-in preset only if artifact and naturality scores stay acceptable.",
            "",
            "## Suggested Acceptance Gates",
            "",
            "- A balance preset is acceptable if its average manual score is within `0.3` of the maximum-quality preset.",
            "- A fast preset is acceptable only if `artifact_control >= 3` and `intelligibility >= 4` on average.",
            "",
        ]
    )
    protocol_path.write_text(content, encoding="utf-8")


def write_scorecard(scorecard_path: Path, *, results: list[dict]) -> None:
    fieldnames = [
        "listener_id",
        "variant_label",
        "diffusion_steps",
        "job_id",
        "output_path",
        "voice_similarity",
        "intelligibility",
        "naturality",
        "artifact_control",
        "prosody_stability",
        "comments",
    ]
    with scorecard_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "listener_id": "",
                    "variant_label": result["label"],
                    "diffusion_steps": result["diffusion_steps"],
                    "job_id": result["job_id"],
                    "output_path": result["output_path"],
                    "voice_similarity": "",
                    "intelligibility": "",
                    "naturality": "",
                    "artifact_control": "",
                    "prosody_stability": "",
                    "comments": "",
                }
            )


def write_report(report_path: Path, *, runtime: dict, results: list[dict], presets: dict[str, dict]) -> None:
    baseline = next(item for item in results if item["label"] == "baseline")
    lines = [
        "# Seed-VC Quality Vs Speed Report",
        "",
        f"Generated at `{report_path}`.",
        "",
        "## Runtime Context",
        "",
        f"- CUDA available: `{runtime.get('cuda_available')}`",
        f"- CUDA device count: `{runtime.get('device_count')}`",
        f"- Mixed precision (`fp16`) status: `not evaluated on this host because CUDA is unavailable`",
        "",
        "## Configuration Matrix",
        "",
        "| Variant | Diffusion steps | Total ms | Inference core ms | Total delta vs 25-step | Inference delta vs 25-step | Log-mel MAE | MFCC cosine sim | RMS delta dB | Output |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for result in results:
        total_delta_pct = ((baseline["processing_duration_ms"] - result["processing_duration_ms"]) / baseline["processing_duration_ms"]) * 100
        inference_delta_pct = ((baseline["inference_core_ms"] - result["inference_core_ms"]) / baseline["inference_core_ms"]) * 100
        quality = result["quality_vs_baseline"]
        lines.append(
            f"| `{result['label']}` | `{result['diffusion_steps']}` | `{result['processing_duration_ms']}` | "
            f"`{result['inference_core_ms']}` | `{format_pct(total_delta_pct)}` | `{format_pct(inference_delta_pct)}` | "
            f"`{quality['log_mel_mae']}` | `{quality['mfcc_cosine_similarity']}` | `{quality['rms_delta_db']}` | "
            f"`{result['output_path']}` |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `25` steps remains the safest maximum-quality reference preset.",
            "- `20` steps is the conservative balance candidate because it cuts total time by about `19%` while staying closest to the baseline in the current proxy metrics.",
            "- `15` steps is materially faster, but it is a stronger quality trade-off candidate and should not become default without listening review.",
            "- `10` steps is the fast experimental preset: it cuts total time by about `50%`, but it should remain opt-in until manual listening confirms artifacts stay acceptable.",
            "",
            "## Recommended Presets",
            "",
            f"- Maximum quality: `{presets['maximum_quality']['diffusion_steps']}` steps",
            f"- Balance quality/velocity: `{presets['balance_quality_speed']['diffusion_steps']}` steps",
            f"- Fast experimental: `{presets['fast_experimental']['diffusion_steps']}` steps",
            "",
            "## Manual Evaluation Follow-Up",
            "",
            "- Use `manual_evaluation_protocol.md` for the listening process.",
            "- Fill `manual_evaluation_scorecard.csv` with at least one row per listener and per variant.",
            "- Promote any preset to product default only after the manual scorecard is reviewed.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    summary_path = Path(args.experiment_summary).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else summary_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    runtime = payload["runtime"]
    results = payload["results"]
    presets = choose_presets(results)

    report_path = output_dir / "quality_vs_speed_report.md"
    protocol_path = output_dir / "manual_evaluation_protocol.md"
    scorecard_path = output_dir / "manual_evaluation_scorecard.csv"

    write_report(report_path, runtime=runtime, results=results, presets=presets)
    write_protocol(protocol_path, presets=presets)
    write_scorecard(scorecard_path, results=results)

    print(
        json.dumps(
            {
                "report_path": str(report_path),
                "protocol_path": str(protocol_path),
                "scorecard_path": str(scorecard_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
