from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import librosa
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_SCRIPT = REPO_ROOT / "infra" / "scripts" / "demo_seed_vc_e2e.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run controlled Seed-VC inference-core experiments.")
    parser.add_argument("--experiment-dir", required=True)
    parser.add_argument("--seed-vc-python", required=True)
    parser.add_argument("--seed-vc-repo-dir", required=True)
    parser.add_argument("--seed-vc-working-root", required=True)
    parser.add_argument("--case-dir", required=True)
    parser.add_argument("--source-file", required=True)
    parser.add_argument("--reference-file", action="append", required=True)
    parser.add_argument("--voiceforge-python", default=sys.executable)
    parser.add_argument("--voiceforge-bucket", default="vfbench")
    parser.add_argument("--email", default="benchmark@voiceforge.dev")
    parser.add_argument("--display-name", default="VoiceForge Benchmark")
    parser.add_argument("--profile-name", default="SeedVC Benchmark Shared")
    parser.add_argument("--diffusion-steps", default="25,20,15,10")
    parser.add_argument("--reference-cache-enabled", default="true")
    parser.add_argument("--source-cache-enabled", default="true")
    parser.add_argument("--resident-reference-runtime-enabled", default="true")
    parser.add_argument("--resident-source-runtime-enabled", default="false")
    parser.add_argument("--reset", action="store_true")
    return parser.parse_args()


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def detect_runtime(seed_vc_python: str) -> dict:
    command = [
        seed_vc_python,
        "-c",
        (
            "import json, torch; "
            "print(json.dumps({"
            "'cuda_available': bool(torch.cuda.is_available()), "
            "'device_count': int(torch.cuda.device_count() if torch.cuda.is_available() else 0)"
            "}))"
        ),
    ]
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "Could not probe Seed-VC runtime for CUDA support.\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return json.loads(completed.stdout.strip())


def run_demo(
    *,
    args: argparse.Namespace,
    diffusion_steps: int,
    fp16: bool,
    reuse_profile: bool,
) -> dict:
    command = [
        args.voiceforge_python,
        str(DEMO_SCRIPT),
        "--case-dir",
        str(Path(args.case_dir).expanduser().resolve()),
        "--seed-vc-python",
        args.seed_vc_python,
        "--seed-vc-repo-dir",
        args.seed_vc_repo_dir,
        "--seed-vc-working-root",
        str(Path(args.seed_vc_working_root).expanduser().resolve()),
        "--source-file",
        str(Path(args.source_file).expanduser().resolve()),
        "--voiceforge-bucket",
        args.voiceforge_bucket,
        "--email",
        args.email,
        "--display-name",
        args.display_name,
        "--profile-name",
        args.profile_name,
        "--reference-cache-enabled",
        args.reference_cache_enabled,
        "--source-cache-enabled",
        args.source_cache_enabled,
        "--resident-reference-runtime-enabled",
        args.resident_reference_runtime_enabled,
        "--resident-source-runtime-enabled",
        args.resident_source_runtime_enabled,
        "--diffusion-steps",
        str(diffusion_steps),
        "--fp16",
        str(fp16).lower(),
    ]
    if reuse_profile:
        command.append("--reuse-profile")
    for reference_file in args.reference_file:
        command.extend(["--reference-file", str(Path(reference_file).expanduser().resolve())])

    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "Inference-core experiment run failed.\n"
            f"Command: {' '.join(command)}\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return json.loads(completed.stdout)


def load_audio(path: Path, *, sample_rate: int = 22050) -> tuple[np.ndarray, int]:
    audio, sr = librosa.load(path, sr=sample_rate, mono=True)
    return audio.astype(np.float32), sr


def cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
    left_norm = float(np.linalg.norm(left))
    right_norm = float(np.linalg.norm(right))
    if left_norm <= 1e-8 or right_norm <= 1e-8:
        return 0.0
    return float(np.dot(left, right) / (left_norm * right_norm))


def compare_outputs(baseline_path: Path, candidate_path: Path) -> dict:
    baseline_audio, sr = load_audio(baseline_path)
    candidate_audio, _ = load_audio(candidate_path, sample_rate=sr)
    baseline_duration_ms = int(round(len(baseline_audio) / sr * 1000))
    candidate_duration_ms = int(round(len(candidate_audio) / sr * 1000))

    min_length = min(len(baseline_audio), len(candidate_audio))
    if min_length == 0:
        raise ValueError("One of the compared outputs is empty.")

    baseline_trimmed = baseline_audio[:min_length]
    candidate_trimmed = candidate_audio[:min_length]

    baseline_mel = librosa.power_to_db(
        librosa.feature.melspectrogram(
            y=baseline_trimmed,
            sr=sr,
            n_fft=1024,
            hop_length=256,
            n_mels=80,
        )
        + 1e-9
    )
    candidate_mel = librosa.power_to_db(
        librosa.feature.melspectrogram(
            y=candidate_trimmed,
            sr=sr,
            n_fft=1024,
            hop_length=256,
            n_mels=80,
        )
        + 1e-9
    )
    min_frames = min(baseline_mel.shape[1], candidate_mel.shape[1])
    log_mel_mae = float(np.mean(np.abs(baseline_mel[:, :min_frames] - candidate_mel[:, :min_frames])))

    baseline_mfcc = librosa.feature.mfcc(y=baseline_trimmed, sr=sr, n_mfcc=20)
    candidate_mfcc = librosa.feature.mfcc(y=candidate_trimmed, sr=sr, n_mfcc=20)
    baseline_vec = baseline_mfcc.mean(axis=1)
    candidate_vec = candidate_mfcc.mean(axis=1)
    mfcc_cosine_similarity = cosine_similarity(baseline_vec, candidate_vec)

    baseline_rms = float(np.sqrt(np.mean(np.square(baseline_trimmed))))
    candidate_rms = float(np.sqrt(np.mean(np.square(candidate_trimmed))))
    rms_delta_db = 20.0 * math.log10(max(candidate_rms, 1e-8) / max(baseline_rms, 1e-8))

    return {
        "baseline_duration_ms": baseline_duration_ms,
        "candidate_duration_ms": candidate_duration_ms,
        "duration_delta_ms": candidate_duration_ms - baseline_duration_ms,
        "log_mel_mae": round(log_mel_mae, 4),
        "mfcc_cosine_similarity": round(mfcc_cosine_similarity, 6),
        "rms_delta_db": round(rms_delta_db, 4),
    }


def safe_stage(summary: dict, stage_name: str) -> int | None:
    profiling = summary.get("profiling_json") or {}
    stages = profiling.get("stages_ms") or {}
    value = stages.get(stage_name)
    return int(value) if value is not None else None


def write_markdown_report(
    *,
    runtime_info: dict,
    results: list[dict],
    report_path: Path,
) -> str:
    baseline = results[0]
    lines = [
        "# Seed-VC Inference-Core Experiments",
        "",
        f"Generated at `{report_path}`.",
        "",
        "## Runtime",
        "",
        f"- CUDA available: `{runtime_info['cuda_available']}`",
        f"- CUDA device count: `{runtime_info['device_count']}`",
        f"- Mixed precision (`fp16`) evaluated: `{'yes' if runtime_info['cuda_available'] else 'no'}`",
        "",
        "## Results",
        "",
        "| Variant | Diffusion steps | FP16 | Total ms | Model ms | Inference core ms | Vocoder ms | Total delta vs baseline | Inference delta vs baseline | Log-mel MAE vs baseline | MFCC cosine sim | Duration delta ms | RMS delta dB |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in results:
        total_delta = item["processing_duration_ms"] - baseline["processing_duration_ms"]
        total_delta_pct = round((total_delta / baseline["processing_duration_ms"]) * 100, 2)
        inference_delta = item["inference_core_ms"] - baseline["inference_core_ms"]
        inference_delta_pct = round((inference_delta / baseline["inference_core_ms"]) * 100, 2)
        quality = item["quality_vs_baseline"]
        lines.append(
            f"| `{item['label']}` | `{item['diffusion_steps']}` | `{str(item['fp16']).lower()}` | "
            f"`{item['processing_duration_ms']}` | `{item['model_invocation_ms']}` | `{item['inference_core_ms']}` | "
            f"`{item['vocoder_postprocess_ms']}` | `{total_delta}` (`{total_delta_pct}%`) | "
            f"`{inference_delta}` (`{inference_delta_pct}%`) | `{quality['log_mel_mae']}` | "
            f"`{quality['mfcc_cosine_similarity']}` | `{quality['duration_delta_ms']}` | `{quality['rms_delta_db']}` |"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `log_mel_mae` and `mfcc_cosine_similarity` are stability proxies against the baseline output, not perceptual MOS.",
            "- Lower `log_mel_mae` and higher `mfcc_cosine_similarity` mean the variant stays closer to the baseline rendering.",
            "- In this host, `fp16` is skipped when CUDA is not available because the current adapter uses `float16` autocast only for GPU paths.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    experiment_dir = Path(args.experiment_dir).expanduser().resolve()
    if args.reset and experiment_dir.exists():
        shutil.rmtree(experiment_dir)
    experiment_dir.mkdir(parents=True, exist_ok=True)
    runs_dir = experiment_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    runtime_info = detect_runtime(args.seed_vc_python)
    diffusion_steps = [int(item.strip()) for item in args.diffusion_steps.split(",") if item.strip()]
    variants = [{"diffusion_steps": step, "fp16": False} for step in diffusion_steps]
    if runtime_info["cuda_available"]:
        variants.append({"diffusion_steps": diffusion_steps[0], "fp16": True})

    results: list[dict] = []
    baseline_output_path: Path | None = None
    reuse_profile = Path(args.case_dir).expanduser().resolve().exists()
    for index, variant in enumerate(variants, start=1):
        summary = run_demo(
            args=args,
            diffusion_steps=variant["diffusion_steps"],
            fp16=variant["fp16"],
            reuse_profile=reuse_profile,
        )
        reuse_profile = True
        run_output = Path(summary["published_output_path"]).expanduser().resolve()
        snapshot_dir = runs_dir / f"r{index:02d}_{variant['diffusion_steps']}_{'fp16' if variant['fp16'] else 'fp32'}"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_output = snapshot_dir / "converted.wav"
        shutil.copy2(run_output, snapshot_output)
        (snapshot_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

        if baseline_output_path is None:
            baseline_output_path = snapshot_output
        quality = compare_outputs(baseline_output_path, snapshot_output)
        results.append(
            {
                "label": "baseline" if index == 1 else f"steps-{variant['diffusion_steps']}",
                "diffusion_steps": variant["diffusion_steps"],
                "fp16": variant["fp16"],
                "processing_duration_ms": int(summary["processing_duration_ms"]),
                "model_invocation_ms": safe_stage(summary, "model_invocation"),
                "inference_core_ms": safe_stage(summary, "inference_core"),
                "vocoder_postprocess_ms": safe_stage(summary, "vocoder_postprocess"),
                "output_path": str(snapshot_output),
                "quality_vs_baseline": quality,
                "job_id": summary["job_id"],
            }
        )

    report_path = experiment_dir / "inference_experiments.md"
    summary_path = experiment_dir / "inference_experiments.json"
    report = write_markdown_report(runtime_info=runtime_info, results=results, report_path=report_path)
    report_path.write_text(report, encoding="utf-8")
    summary_path.write_text(
        json.dumps(
            {
                "runtime": runtime_info,
                "results": results,
                "report_path": str(report_path),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "report_path": str(report_path),
                "summary_path": str(summary_path),
                "variant_count": len(results),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
