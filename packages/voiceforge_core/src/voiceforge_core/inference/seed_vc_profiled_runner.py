from __future__ import annotations

import argparse
import json
import math
import os
import threading
import time
from pathlib import Path


def str_to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


class ResourceMonitor:
    def __init__(self, process, *, interval_seconds: float = 0.25) -> None:
        self.process = process
        self.interval_seconds = interval_seconds
        self._running = False
        self._thread: threading.Thread | None = None
        self.peak_rss_bytes = 0
        self.cpu_start = None

    def start(self) -> None:
        self.cpu_start = self.process.cpu_times()
        self._running = True
        self._thread = threading.Thread(target=self._sample, daemon=True)
        self._thread.start()

    def stop(self, *, wall_seconds: float) -> dict:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=self.interval_seconds * 2)
        cpu_end = self.process.cpu_times()
        cpu_time_seconds = (
            (cpu_end.user - self.cpu_start.user) + (cpu_end.system - self.cpu_start.system)
            if self.cpu_start is not None
            else 0.0
        )
        logical_cpu_count = max(os.cpu_count() or 1, 1)
        avg_cpu_percent = 0.0
        if wall_seconds > 0:
            avg_cpu_percent = (cpu_time_seconds / wall_seconds) / logical_cpu_count * 100.0
        return {
            "cpu_time_seconds": round(cpu_time_seconds, 3),
            "estimated_avg_cpu_percent": round(avg_cpu_percent, 2),
            "logical_cpu_count": logical_cpu_count,
            "peak_rss_mb": round(self.peak_rss_bytes / (1024 * 1024), 2),
        }

    def _sample(self) -> None:
        while self._running:
            try:
                rss = self.process.memory_info().rss
                if rss > self.peak_rss_bytes:
                    self.peak_rss_bytes = rss
            except Exception:
                pass
            time.sleep(self.interval_seconds)


def now_ms(started_at: float) -> int:
    return int((time.perf_counter() - started_at) * 1000)


def write_metrics(metrics_path: str | None, payload: dict) -> None:
    if not metrics_path:
        return
    path = Path(metrics_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=str, required=True)
    parser.add_argument("--target", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--source-cache-input", type=str, default=None)
    parser.add_argument("--source-cache-output", type=str, default=None)
    parser.add_argument("--reference-cache-input", type=str, default=None)
    parser.add_argument("--reference-cache-output", type=str, default=None)
    parser.add_argument("--diffusion-steps", type=int, default=30)
    parser.add_argument("--length-adjust", type=float, default=1.0)
    parser.add_argument("--inference-cfg-rate", type=float, default=0.7)
    parser.add_argument("--f0-condition", type=str, default="false")
    parser.add_argument("--auto-f0-adjust", type=str, default="false")
    parser.add_argument("--semi-tone-shift", type=int, default=0)
    parser.add_argument("--checkpoint", type=str, default=None)
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--fp16", type=str, default="true")
    parser.add_argument("--voiceforge-metrics-output", type=str, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.f0_condition = str_to_bool(args.f0_condition)
    args.auto_f0_adjust = str_to_bool(args.auto_f0_adjust)
    args.fp16 = str_to_bool(args.fp16)

    metrics = {
        "status": "failed",
        "stages_ms": {},
        "details_ms": {},
        "resources": {},
        "artifacts": {},
    }
    total_started = time.perf_counter()
    monitor = None

    try:
        import psutil

        process = psutil.Process(os.getpid())
        monitor = ResourceMonitor(process)
        monitor.start()

        stage_started = time.perf_counter()
        import librosa
        import numpy as np
        import torch
        import torchaudio
        import inference as upstream
        torch.set_grad_enabled(False)

        model, semantic_fn, f0_fn, vocoder_fn, campplus_model, mel_fn, mel_fn_args = upstream.load_models(args)
        metrics["stages_ms"]["runtime_bootstrap"] = now_ms(stage_started)

        device = upstream.device
        sr = mel_fn_args["sampling_rate"]
        f0_condition = args.f0_condition
        auto_f0_adjust = args.auto_f0_adjust
        pitch_shift = args.semi_tone_shift
        metrics["artifacts"]["device_type"] = device.type
        metrics["artifacts"]["precision_mode"] = "fp16" if upstream.fp16 else "fp32"
        metrics["artifacts"]["diffusion_steps"] = args.diffusion_steps

        stage_started = time.perf_counter()
        shifted_f0_alt = None
        F0_alt = None
        if args.source_cache_input and Path(args.source_cache_input).exists():
            cache_started = time.perf_counter()
            cache_payload = torch.load(args.source_cache_input, map_location="cpu")
            if cache_payload.get("schema_version") != "seed-vc-source-v1":
                raise ValueError("Unsupported Seed-VC source cache schema.")
            if bool(cache_payload.get("f0_condition")) != bool(f0_condition):
                raise ValueError("Seed-VC source cache was built with a different f0_condition setting.")
            S_alt = cache_payload["S_alt"].to(device)
            mel = cache_payload["mel"].to(device)
            cached_f0 = cache_payload.get("F0_alt")
            if cached_f0 is not None:
                F0_alt = cached_f0.to(device)
            metrics["details_ms"]["source_cache_load"] = now_ms(cache_started)
            metrics["details_ms"]["source_cache_hit"] = 1
            metrics["artifacts"]["source_cache_input"] = args.source_cache_input
        else:
            source_audio_np = librosa.load(args.source, sr=sr)[0]
            source_audio = torch.from_numpy(source_audio_np).unsqueeze(0).float().to(device)
            converted_waves_16k = torchaudio.functional.resample(source_audio, sr, 16000).contiguous()
            semantic_started = time.perf_counter()
            with torch.inference_mode():
                if converted_waves_16k.size(-1) <= 16000 * 30:
                    S_alt = semantic_fn(converted_waves_16k)
                else:
                    overlapping_time = 5
                    S_alt_list = []
                    buffer = None
                    traversed_time = 0
                    while traversed_time < converted_waves_16k.size(-1):
                        if buffer is None:
                            chunk = converted_waves_16k[:, traversed_time : traversed_time + 16000 * 30]
                        else:
                            chunk = torch.cat(
                                [
                                    buffer,
                                    converted_waves_16k[
                                        :,
                                        traversed_time : traversed_time + 16000 * (30 - overlapping_time),
                                    ],
                                ],
                                dim=-1,
                            )
                        S_alt_chunk = semantic_fn(chunk)
                        if traversed_time == 0:
                            S_alt_list.append(S_alt_chunk)
                        else:
                            S_alt_list.append(S_alt_chunk[:, 50 * overlapping_time :])
                        buffer = chunk[:, -16000 * overlapping_time :]
                        traversed_time += 30 * 16000 if traversed_time == 0 else chunk.size(-1) - 16000 * overlapping_time
                    S_alt = torch.cat(S_alt_list, dim=1)
            metrics["details_ms"]["source_semantic_extraction"] = now_ms(semantic_started)

            mel_started = time.perf_counter()
            with torch.inference_mode():
                mel = mel_fn(source_audio.float())
            metrics["details_ms"]["source_mel_extraction"] = now_ms(mel_started)

            if f0_condition:
                f0_started = time.perf_counter()
                F0_alt_np = f0_fn(converted_waves_16k[0], thred=0.03)
                F0_alt = torch.from_numpy(F0_alt_np).to(device)[None]
                metrics["details_ms"]["source_f0_extraction"] = now_ms(f0_started)

            if args.source_cache_output:
                cache_save_started = time.perf_counter()
                cache_path = Path(args.source_cache_output)
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                torch.save(
                    {
                        "schema_version": "seed-vc-source-v1",
                        "f0_condition": f0_condition,
                        "sample_rate": sr,
                        "S_alt": S_alt.detach().cpu(),
                        "mel": mel.detach().cpu(),
                        "F0_alt": F0_alt.detach().cpu() if F0_alt is not None else None,
                    },
                    cache_path,
                )
                metrics["details_ms"]["source_cache_save"] = now_ms(cache_save_started)
                metrics["artifacts"]["source_cache_output"] = str(cache_path)

        if "source_cache_hit" not in metrics["details_ms"]:
            metrics["details_ms"]["source_cache_hit"] = 0

        metrics["stages_ms"]["source_preprocessing"] = now_ms(stage_started)

        stage_started = time.perf_counter()
        F0_ori = None
        if args.reference_cache_input and Path(args.reference_cache_input).exists():
            cache_started = time.perf_counter()
            cache_payload = torch.load(args.reference_cache_input, map_location="cpu")
            if cache_payload.get("schema_version") != "seed-vc-ref-v1":
                raise ValueError("Unsupported Seed-VC reference cache schema.")
            if bool(cache_payload.get("f0_condition")) != bool(f0_condition):
                raise ValueError("Seed-VC reference cache was built with a different f0_condition setting.")
            S_ori = cache_payload["S_ori"].to(device)
            mel2 = cache_payload["mel2"].to(device)
            style2 = cache_payload["style2"].to(device)
            cached_f0 = cache_payload.get("F0_ori")
            if cached_f0 is not None:
                F0_ori = cached_f0.to(device)
            metrics["details_ms"]["reference_cache_load"] = now_ms(cache_started)
            metrics["details_ms"]["reference_cache_hit"] = 1
            metrics["artifacts"]["reference_cache_input"] = args.reference_cache_input
        else:
            ref_audio_np = librosa.load(args.target, sr=sr)[0]
            ref_audio = torch.tensor(ref_audio_np[: sr * 25]).unsqueeze(0).float().to(device)
            ori_waves_16k = torchaudio.functional.resample(ref_audio, sr, 16000)

            semantic_started = time.perf_counter()
            S_ori = semantic_fn(ori_waves_16k)
            metrics["details_ms"]["reference_semantic_extraction"] = now_ms(semantic_started)

            mel_started = time.perf_counter()
            mel2 = mel_fn(ref_audio.float())
            metrics["details_ms"]["reference_mel_extraction"] = now_ms(mel_started)

            style_started = time.perf_counter()
            feat2 = torchaudio.compliance.kaldi.fbank(
                ori_waves_16k,
                num_mel_bins=80,
                dither=0,
                sample_frequency=16000,
            )
            feat2 = feat2 - feat2.mean(dim=0, keepdim=True)
            style2 = campplus_model(feat2.unsqueeze(0))
            metrics["details_ms"]["reference_style_extraction"] = now_ms(style_started)

            if f0_condition:
                f0_started = time.perf_counter()
                F0_ori_np = f0_fn(ori_waves_16k[0], thred=0.03)
                F0_ori = torch.from_numpy(F0_ori_np).to(device)[None]
                metrics["details_ms"]["reference_f0_extraction"] = now_ms(f0_started)

            if args.reference_cache_output:
                cache_save_started = time.perf_counter()
                cache_path = Path(args.reference_cache_output)
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                torch.save(
                    {
                        "schema_version": "seed-vc-ref-v1",
                        "f0_condition": f0_condition,
                        "sample_rate": sr,
                        "S_ori": S_ori.detach().cpu(),
                        "mel2": mel2.detach().cpu(),
                        "style2": style2.detach().cpu(),
                        "F0_ori": F0_ori.detach().cpu() if F0_ori is not None else None,
                    },
                    cache_path,
                )
                metrics["details_ms"]["reference_cache_save"] = now_ms(cache_save_started)
                metrics["artifacts"]["reference_cache_output"] = str(cache_path)

        if "reference_cache_hit" not in metrics["details_ms"]:
            metrics["details_ms"]["reference_cache_hit"] = 0
        if f0_condition and F0_ori is not None:
            f0_alignment_started = time.perf_counter()
            voiced_F0_ori = F0_ori[F0_ori > 1]
            voiced_F0_alt = F0_alt[F0_alt > 1]
            log_f0_alt = torch.log(F0_alt + 1e-5)
            voiced_log_f0_ori = torch.log(voiced_F0_ori + 1e-5)
            voiced_log_f0_alt = torch.log(voiced_F0_alt + 1e-5)
            median_log_f0_ori = torch.median(voiced_log_f0_ori)
            median_log_f0_alt = torch.median(voiced_log_f0_alt)
            shifted_log_f0_alt = log_f0_alt.clone()
            if auto_f0_adjust:
                shifted_log_f0_alt[F0_alt > 1] = log_f0_alt[F0_alt > 1] - median_log_f0_alt + median_log_f0_ori
            shifted_f0_alt = torch.exp(shifted_log_f0_alt)
            if pitch_shift != 0:
                shifted_f0_alt[F0_alt > 1] = upstream.adjust_f0_semitones(
                    shifted_f0_alt[F0_alt > 1], pitch_shift
                )
            metrics["details_ms"]["reference_f0_alignment"] = now_ms(f0_alignment_started)

        metrics["stages_ms"]["reference_preprocessing"] = now_ms(stage_started)

        stage_started = time.perf_counter()
        target_lengths = torch.LongTensor([int(mel.size(2) * args.length_adjust)]).to(mel.device)
        target2_lengths = torch.LongTensor([mel2.size(2)]).to(mel2.device)

        length_reg_started = time.perf_counter()
        cond, _, _, _, _ = model.length_regulator(
            S_alt,
            ylens=target_lengths,
            n_quantizers=3,
            f0=shifted_f0_alt,
        )
        prompt_condition, _, _, _, _ = model.length_regulator(
            S_ori,
            ylens=target2_lengths,
            n_quantizers=3,
            f0=F0_ori,
        )
        metrics["details_ms"]["length_regulation"] = now_ms(length_reg_started)

        sr_out = 22050 if not f0_condition else 44100
        hop_length = 256 if not f0_condition else 512
        max_context_window = sr_out // hop_length * 30
        overlap_frame_len = 16
        overlap_wave_len = overlap_frame_len * hop_length
        max_source_window = max_context_window - mel2.size(2)

        processed_frames = 0
        generated_wave_chunks = []
        previous_chunk = None
        inference_core_ms = 0
        vocoder_postprocess_ms = 0
        chunk_count = 0

        while processed_frames < cond.size(1):
            chunk_cond = cond[:, processed_frames : processed_frames + max_source_window]
            is_last_chunk = processed_frames + max_source_window >= cond.size(1)
            cat_condition = torch.cat([prompt_condition, chunk_cond], dim=1)

            inference_started = time.perf_counter()
            with torch.autocast(
                device_type=device.type,
                dtype=torch.float16 if upstream.fp16 else torch.float32,
            ):
                vc_target = model.cfm.inference(
                    cat_condition,
                    torch.LongTensor([cat_condition.size(1)]).to(mel2.device),
                    mel2,
                    style2,
                    None,
                    args.diffusion_steps,
                    inference_cfg_rate=args.inference_cfg_rate,
                )
                vc_target = vc_target[:, :, mel2.size(-1) :]
            inference_core_ms += now_ms(inference_started)

            vocoder_started = time.perf_counter()
            vc_wave = vocoder_fn(vc_target.float()).squeeze()
            vc_wave = vc_wave[None, :]
            if processed_frames == 0:
                if is_last_chunk:
                    generated_wave_chunks.append(vc_wave[0].cpu().numpy())
                    processed_frames += vc_target.size(2)
                    vocoder_postprocess_ms += now_ms(vocoder_started)
                    chunk_count += 1
                    break
                generated_wave_chunks.append(vc_wave[0, :-overlap_wave_len].cpu().numpy())
                previous_chunk = vc_wave[0, -overlap_wave_len:]
                processed_frames += vc_target.size(2) - overlap_frame_len
            elif is_last_chunk:
                output_wave = upstream.crossfade(
                    previous_chunk.cpu().numpy(),
                    vc_wave[0].cpu().numpy(),
                    overlap_wave_len,
                )
                generated_wave_chunks.append(output_wave)
                processed_frames += vc_target.size(2) - overlap_frame_len
            else:
                output_wave = upstream.crossfade(
                    previous_chunk.cpu().numpy(),
                    vc_wave[0, :-overlap_wave_len].cpu().numpy(),
                    overlap_wave_len,
                )
                generated_wave_chunks.append(output_wave)
                previous_chunk = vc_wave[0, -overlap_wave_len:]
                processed_frames += vc_target.size(2) - overlap_frame_len
            vocoder_postprocess_ms += now_ms(vocoder_started)
            chunk_count += 1

        concat_started = time.perf_counter()
        final_wave_np = np.concatenate(generated_wave_chunks)
        vc_wave = torch.tensor(final_wave_np)[None, :].float()
        vocoder_postprocess_ms += now_ms(concat_started)

        metrics["stages_ms"]["model_invocation"] = now_ms(stage_started)
        metrics["stages_ms"]["inference_core"] = inference_core_ms
        metrics["stages_ms"]["vocoder_postprocess"] = vocoder_postprocess_ms
        metrics["details_ms"]["chunk_count"] = chunk_count

        output_write_started = time.perf_counter()
        source_name = os.path.basename(args.source).split(".")[0]
        target_name = os.path.basename(args.target).split(".")[0]
        os.makedirs(args.output, exist_ok=True)
        output_path = os.path.join(
            args.output,
            f"vc_{source_name}_{target_name}_{args.length_adjust}_{args.diffusion_steps}_{args.inference_cfg_rate}.wav",
        )
        torchaudio.save(output_path, vc_wave.cpu(), sr_out)
        metrics["details_ms"]["subprocess_output_write"] = now_ms(output_write_started)

        total_wall_ms = now_ms(total_started)
        rtf = 0.0
        if vc_wave.size(-1) > 0:
            rtf = ((total_wall_ms / 1000.0) / vc_wave.size(-1)) * sr_out
        metrics["status"] = "completed"
        metrics["total_wall_ms"] = total_wall_ms
        metrics["artifacts"] = {
            "saved_output_path": output_path,
            "output_sample_rate": sr_out,
            "output_num_samples": int(vc_wave.size(-1)),
            "rtf_estimate": round(rtf, 3),
        }
        print(f"RTF: {rtf}")
    except Exception as exc:
        metrics["status"] = "failed"
        metrics["error"] = str(exc)
        metrics["total_wall_ms"] = now_ms(total_started)
        raise
    finally:
        if monitor is not None:
            metrics["resources"] = monitor.stop(wall_seconds=max((time.perf_counter() - total_started), 0.001))
        write_metrics(args.voiceforge_metrics_output, metrics)


if __name__ == "__main__":
    main()
