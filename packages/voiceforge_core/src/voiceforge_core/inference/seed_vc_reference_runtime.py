from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import time
from pathlib import Path


def str_to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-file", required=True)
    parser.add_argument("--working-root", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--idle-timeout-seconds", type=int, default=900)
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument("--config", default=None)
    parser.add_argument("--f0-condition", default="false")
    parser.add_argument("--fp16", default="false")
    return parser.parse_args()


def now_ms(started_at: float) -> int:
    return int((time.perf_counter() - started_at) * 1000)


def build_source_cache(runtime: dict, *, input_path: str, output_path: str) -> dict:
    librosa = runtime["librosa"]
    torch = runtime["torch"]
    torchaudio = runtime["torchaudio"]
    semantic_fn = runtime["semantic_fn"]
    f0_fn = runtime["f0_fn"]
    mel_fn = runtime["mel_fn"]
    sr = runtime["sampling_rate"]
    device = runtime["device"]
    f0_condition = runtime["f0_condition"]

    metrics: dict[str, int | str | bool | None] = {"status": "ok"}
    stage_started = time.perf_counter()
    source_audio_np = librosa.load(input_path, sr=sr)[0]
    source_audio = torch.from_numpy(source_audio_np).unsqueeze(0).float().to(device)
    converted_waves_16k = torchaudio.functional.resample(source_audio, sr, 16000).contiguous()

    semantic_started = time.perf_counter()
    with torch.inference_mode():
        S_alt = semantic_fn(converted_waves_16k)
    metrics["source_semantic_extraction"] = now_ms(semantic_started)

    mel_started = time.perf_counter()
    with torch.inference_mode():
        mel = mel_fn(source_audio.float())
    metrics["source_mel_extraction"] = now_ms(mel_started)

    F0_alt = None
    if f0_condition:
        f0_started = time.perf_counter()
        F0_alt_np = f0_fn(converted_waves_16k[0], thred=0.03)
        F0_alt = torch.from_numpy(F0_alt_np).to(device)[None]
        metrics["source_f0_extraction"] = now_ms(f0_started)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    save_started = time.perf_counter()
    torch.save(
        {
            "schema_version": "seed-vc-source-v1",
            "f0_condition": f0_condition,
            "sample_rate": sr,
            "S_alt": S_alt.detach().cpu(),
            "mel": mel.detach().cpu(),
            "F0_alt": F0_alt.detach().cpu() if F0_alt is not None else None,
        },
        output,
    )
    metrics["source_cache_save"] = now_ms(save_started)
    metrics["source_cache_build_total"] = now_ms(stage_started)
    metrics["output_path"] = str(output)
    return metrics


def build_reference_cache(runtime: dict, *, input_path: str, output_path: str) -> dict:
    librosa = runtime["librosa"]
    torch = runtime["torch"]
    torchaudio = runtime["torchaudio"]
    semantic_fn = runtime["semantic_fn"]
    f0_fn = runtime["f0_fn"]
    campplus_model = runtime["campplus_model"]
    mel_fn = runtime["mel_fn"]
    sr = runtime["sampling_rate"]
    device = runtime["device"]
    f0_condition = runtime["f0_condition"]

    metrics: dict[str, int | str | bool | None] = {"status": "ok"}
    stage_started = time.perf_counter()
    ref_audio_np = librosa.load(input_path, sr=sr)[0]
    ref_audio = torch.tensor(ref_audio_np[: sr * 25]).unsqueeze(0).float().to(device)
    ori_waves_16k = torchaudio.functional.resample(ref_audio, sr, 16000)

    semantic_started = time.perf_counter()
    S_ori = semantic_fn(ori_waves_16k)
    metrics["reference_semantic_extraction"] = now_ms(semantic_started)

    mel_started = time.perf_counter()
    mel2 = mel_fn(ref_audio.float())
    metrics["reference_mel_extraction"] = now_ms(mel_started)

    style_started = time.perf_counter()
    feat2 = torchaudio.compliance.kaldi.fbank(
        ori_waves_16k,
        num_mel_bins=80,
        dither=0,
        sample_frequency=16000,
    )
    feat2 = feat2 - feat2.mean(dim=0, keepdim=True)
    style2 = campplus_model(feat2.unsqueeze(0))
    metrics["reference_style_extraction"] = now_ms(style_started)

    F0_ori = None
    if f0_condition:
        f0_started = time.perf_counter()
        F0_ori_np = f0_fn(ori_waves_16k[0], thred=0.03)
        F0_ori = torch.from_numpy(F0_ori_np).to(device)[None]
        metrics["reference_f0_extraction"] = now_ms(f0_started)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    save_started = time.perf_counter()
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
        output,
    )
    metrics["reference_cache_save"] = now_ms(save_started)
    metrics["reference_cache_build_total"] = now_ms(stage_started)
    metrics["output_path"] = str(output)
    return metrics


def handle_payload(runtime: dict, payload: dict) -> dict:
    action = payload.get("action")
    if action == "ping":
        return {
            "status": "ok",
            "pid": os.getpid(),
            "started_at": runtime["started_at"],
        }
    if action == "build_source_cache":
        build_started = time.perf_counter()
        result = build_source_cache(
            runtime,
            input_path=str(payload["input_path"]),
            output_path=str(payload["output_path"]),
        )
        return {
            "status": "ok",
            "pid": os.getpid(),
            "job_id": payload.get("job_id"),
            "metrics": result,
            "duration_ms": now_ms(build_started),
        }
    if action == "build_reference_cache":
        build_started = time.perf_counter()
        result = build_reference_cache(
            runtime,
            input_path=str(payload["input_path"]),
            output_path=str(payload["output_path"]),
        )
        return {
            "status": "ok",
            "pid": os.getpid(),
            "job_id": payload.get("job_id"),
            "metrics": result,
            "duration_ms": now_ms(build_started),
        }
    return {"status": "error", "error": f"Unknown action: {action}"}


def load_runtime(args: argparse.Namespace) -> dict:
    import librosa
    import torch
    import torchaudio
    import inference as upstream

    torch.set_grad_enabled(False)
    args.f0_condition = str_to_bool(args.f0_condition)
    args.fp16 = str_to_bool(args.fp16)

    stage_started = time.perf_counter()
    model, semantic_fn, f0_fn, _vocoder_fn, campplus_model, mel_fn, mel_fn_args = upstream.load_models(args)
    return {
        "model": model,
        "semantic_fn": semantic_fn,
        "f0_fn": f0_fn,
        "campplus_model": campplus_model,
        "mel_fn": mel_fn,
        "sampling_rate": mel_fn_args["sampling_rate"],
        "device": upstream.device,
        "f0_condition": args.f0_condition,
        "librosa": librosa,
        "torch": torch,
        "torchaudio": torchaudio,
        "started_at": time.time(),
        "runtime_bootstrap_ms": now_ms(stage_started),
    }


def write_state_file(state_file: Path, *, host: str, port: int, runtime: dict) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(
        json.dumps(
            {
                "host": host,
                "port": port,
                "pid": os.getpid(),
                "started_at": runtime["started_at"],
                "runtime_bootstrap_ms": runtime["runtime_bootstrap_ms"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    state_file = Path(args.state_file).expanduser().resolve()
    runtime = load_runtime(args)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((args.host, args.port))
    server_socket.listen(4)
    server_socket.settimeout(1.0)
    host, port = server_socket.getsockname()
    write_state_file(state_file, host=host, port=port, runtime=runtime)
    last_activity = time.monotonic()

    try:
        while True:
            if time.monotonic() - last_activity > args.idle_timeout_seconds:
                break
            try:
                connection, _address = server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            with connection:
                try:
                    data = b""
                    while b"\n" not in data:
                        chunk = connection.recv(65536)
                        if not chunk:
                            break
                        data += chunk
                    if not data:
                        continue
                    payload = json.loads(data.splitlines()[0].decode("utf-8"))
                    response = handle_payload(runtime, payload)
                except Exception as exc:  # pragma: no cover - runtime safety net
                    response = {"status": "error", "error": str(exc)}
                try:
                    connection.sendall((json.dumps(response) + "\n").encode("utf-8"))
                except OSError:
                    pass
                last_activity = time.monotonic()
    finally:
        try:
            server_socket.close()
        finally:
            try:
                state_file.unlink()
            except OSError:
                pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
