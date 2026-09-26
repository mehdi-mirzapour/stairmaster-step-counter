import cv2
import json
import time
import argparse
import subprocess
import wave
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from scipy.signal import find_peaks, savgol_filter, butter, filtfilt
from ultralytics import YOLO
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SAMPLES_DIR = BASE_DIR / "samples"
OUTPUT_DIR = BASE_DIR / "output" / "solution4"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


import torch

class AudioVisualStepCounter:
    """
    Solution 4: Multimodal Audio-Visual Fusion Step Counter.
    Combines optical human kinematic keypoints with acoustic shoe/step impact transients.
    """

    def __init__(self, model_name: str = "yolov8n-pose.pt", device: Optional[str] = None):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        self.device_name = torch.cuda.get_device_name(0) if self.device.startswith("cuda") and torch.cuda.is_available() else "CPU"
        self.model = YOLO(model_name)
        self.model.to(self.device)

    def extract_audio_impact_times(self, video_path: Path, max_duration_sec: Optional[float] = None) -> List[float]:
        """Extracts audio and returns detected footstrike impact timestamps."""
        wav_path = OUTPUT_DIR / f"{video_path.stem}_audio_temp.wav"
        cmd = [
            "ffmpeg", "-y", "-i", str(video_path),
            "-vn", "-ac", "1", "-ar", "22050",
            str(wav_path)
        ]
        if max_duration_sec:
            cmd.extend(["-t", str(max_duration_sec)])
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if not wav_path.exists():
            return []

        with wave.open(str(wav_path), "rb") as wf:
            n_samples = wf.getnframes()
            audio_bytes = wf.readframes(n_samples)
            audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)

        sr = 22050
        nyq = sr / 2.0
        low = max(20.0, min(60.0, nyq - 100)) / nyq
        high = min(350.0, nyq - 50) / nyq
        b, a = butter(4, [low, high], btype='band')
        filtered = filtfilt(b, a, audio)
        envelope = np.abs(filtered)
        window_len = int(sr * 0.08)
        smoothed = np.convolve(envelope, np.ones(window_len)/window_len, mode='same')

        # Autocorrelation to detect dominant cadence
        factor = 50
        env_ds = smoothed[::factor]
        sr_ds = sr / factor
        env_centered = env_ds - np.mean(env_ds)
        corr = np.correlate(env_centered, env_centered, mode='full')
        corr = corr[len(corr)//2:]
        min_lag = max(1, int(0.30 * sr_ds))
        max_lag = min(len(corr) - 1, int(3.0 * sr_ds))
        dominant_period = (min_lag + np.argmax(corr[min_lag:max_lag])) / sr_ds if max_lag > min_lag else 1.63

        min_dist_samples = max(int(sr * 0.28), int(sr * min(1.10, dominant_period * 0.67)))
        prom = np.max(smoothed) * 0.105
        peaks, _ = find_peaks(smoothed, distance=min_dist_samples, prominence=prom)
        impact_times = [round(float(p) / sr, 3) for p in peaks]
        return impact_times

    def process_video(self, video_path: Path, output_json: Path, max_duration_sec: Optional[float] = None):
        video_path = Path(video_path)
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        limit_frames = int(max_duration_sec * fps) if max_duration_sec else total_frames
        limit_frames = min(limit_frames, total_frames)
        analyzed_sec = limit_frames / fps

        console.print(Panel(
            f"🎧 [bold cyan]SOLUTION 4: MULTIMODAL AUDIO-VISUAL FUSION[/bold cyan]\n"
            f"Video: [yellow]{video_path.name}[/yellow] ({analyzed_sec:.1f}s analyzed)",
            border_style="magenta"
        ))

        start_time = time.time()

        # 1. Visual Keypoints
        raw_la_y, raw_ra_y, timestamps = [], [], []
        f_idx = 0
        while cap.isOpened() and f_idx < limit_frames:
            ret, frame = cap.read()
            if not ret:
                break
            timestamps.append(f_idx / fps)
            res = self.model(frame, device=self.device, verbose=False)[0]
            if res.keypoints is not None and len(res.keypoints.xy) > 0:
                kpts = res.keypoints.xy[0].cpu().numpy()
                raw_la_y.append(kpts[15][1] if len(kpts) > 15 else np.nan)
                raw_ra_y.append(kpts[16][1] if len(kpts) > 16 else np.nan)
            else:
                raw_la_y.append(np.nan)
                raw_ra_y.append(np.nan)
            f_idx += 1
        cap.release()

        # Clean signals
        def clean(arr):
            s = np.array(arr, dtype=float)
            nans = np.isnan(s)
            if np.all(nans):
                return np.zeros_like(s)
            s[nans] = np.interp(np.flatnonzero(nans), np.flatnonzero(~nans), s[~nans])
            inv = -s
            w = 19
            return savgol_filter(inv, w, 2) if len(inv) >= 19 else inv

        la_smooth = clean(raw_la_y)
        ra_smooth = clean(raw_ra_y)

        # Adaptive Stride Period Detection via Autocorrelation
        ra_centered = ra_smooth - np.mean(ra_smooth)
        corr = np.correlate(ra_centered, ra_centered, mode='full')
        corr = corr[len(corr)//2:]
        min_lag = max(8, int(fps * 0.40))
        max_lag = min(len(corr) - 1, int(fps * 4.0))
        if max_lag > min_lag:
            stride_lag = min_lag + np.argmax(corr[min_lag:max_lag])
        else:
            stride_lag = int(fps * 1.6)

        min_dist_frames = max(8, int(stride_lag * 0.55))
        prom_r = max(8, np.ptp(ra_smooth) * 0.15)
        prom_l = max(8, np.ptp(la_smooth) * 0.10)

        left_peaks, _ = find_peaks(la_smooth, distance=min_dist_frames, prominence=prom_l)
        right_peaks, _ = find_peaks(ra_smooth, distance=min_dist_frames, prominence=prom_r)

        visual_steps = []
        for p in left_peaks:
            visual_steps.append({"timestamp": float(timestamps[p]), "leg": "left"})
        for p in right_peaks:
            visual_steps.append({"timestamp": float(timestamps[p]), "leg": "right"})
        visual_steps.sort(key=lambda x: x["timestamp"])

        # Deduplicate any close anomalies (< 28% of stride period)
        min_step_dt = (stride_lag / fps) * 0.28
        dedup_visual = []
        for s in visual_steps:
            if not dedup_visual:
                dedup_visual.append(s)
            else:
                dt = s["timestamp"] - dedup_visual[-1]["timestamp"]
                if dt >= min_step_dt:
                    dedup_visual.append(s)

        # 2. Audio Impacts
        audio_impacts = self.extract_audio_impact_times(video_path, max_duration_sec=analyzed_sec)

        # 3. Multimodal Fusion (Coincidence window < 250ms)
        fused_steps = []
        matched_audio = set()

        for v_step in dedup_visual:
            t_v = v_step["timestamp"]
            best_diff = 999.0
            best_a_idx = -1
            for a_idx, t_a in enumerate(audio_impacts):
                diff = abs(t_v - t_a)
                if diff < best_diff:
                    best_diff = diff
                    best_a_idx = a_idx

            if best_diff <= 0.25:  # Within 250ms coincidence window
                matched_audio.add(best_a_idx)
                fused_steps.append({
                    "timestamp_sec": round((t_v + audio_impacts[best_a_idx]) / 2.0, 3),
                    "leg": v_step["leg"],
                    "modality": "AUDIO_VISUAL_FUSED",
                    "confidence": 0.98,
                    "delta_ms": round(best_diff * 1000, 1),
                })
            else:
                fused_steps.append({
                    "timestamp_sec": round(t_v, 3),
                    "leg": v_step["leg"],
                    "modality": "VISUAL_ONLY",
                    "confidence": 0.85,
                    "delta_ms": None,
                })

        for i, s in enumerate(fused_steps):
            s["fused_step_id"] = i + 1
            s["time_str"] = f"{int(s['timestamp_sec']//60):02d}:{s['timestamp_sec']%60:05.2f}"

        runtime = round(time.time() - start_time, 2)
        total_steps = len(fused_steps)
        fused_count = sum(1 for s in fused_steps if s["modality"] == "AUDIO_VISUAL_FUSED")
        cadence_spm = round((total_steps / max(analyzed_sec, 0.1)) * 60.0, 2)

        # Display Table
        table = Table(title=f"🎧 Audio-Visual Fused Steps: {video_path.name}", border_style="magenta")
        table.add_column("Step #", style="bold white", width=8)
        table.add_column("Timestamp", style="bold yellow", width=12)
        table.add_column("Leg", style="bold", width=8)
        table.add_column("Modality", style="cyan", width=22)
        table.add_column("Confidence", style="green", width=12)
        table.add_column("Sync Δt", style="dim", width=12)

        for s in fused_steps[:15]:
            leg_color = "bright_blue" if s["leg"] == "left" else "bright_magenta"
            delta_str = f"{s['delta_ms']} ms" if s['delta_ms'] is not None else "N/A"
            table.add_row(
                f"{s['fused_step_id']:02d}",
                f"{s['timestamp_sec']}s",
                f"[{leg_color}]{s['leg'].upper()}[/{leg_color}]",
                s["modality"],
                f"{s['confidence']*100:.0f}%",
                delta_str,
            )

        console.print(table)

        console.print(Panel(
            f"🏁 [bold green]SOLUTION 4 FUSION SUMMARY[/bold green]\n"
            f"• Total Fused Steps: [bold yellow]{total_steps}[/bold yellow] steps\n"
            f"• Dual-Confirmed (Audio + Visual): [bold green]{fused_count} steps[/bold green] ({fused_count/total_steps*100:.0f}% correlation)\n"
            f"• Cadence: [bold cyan]{cadence_spm} Steps/Min[/bold cyan]\n"
            f"• Processing Time: [magenta]{runtime} s[/magenta]",
            border_style="magenta"
        ))

        res = {
            "solution": "Solution 4: Multimodal Audio-Visual Fusion",
            "video_name": video_path.name,
            "total_steps": total_steps,
            "audio_visual_confirmed": fused_count,
            "cadence_spm": cadence_spm,
            "duration_sec": analyzed_sec,
            "runtime_sec": runtime,
            "steps": fused_steps,
        }

        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2)
        console.print(f"[bold green]✔ Saved structured JSON to:[/bold green] {output_json}")
        return res


def main():
    parser = argparse.ArgumentParser(description="Solution 4: Audio-Visual Fusion Step Counter")
    parser.add_argument("--sample", choices=["1", "2", "all"], default="2")
    parser.add_argument("--max-duration", type=float, default=None)
    parser.add_argument("--save-video", action="store_true", help="Generate annotated video with telemetry HUD")

    args = parser.parse_args()
    fusion = AudioVisualStepCounter()

    targets = []
    if args.sample in ["2", "all"]:
        targets.append({
            "video": SAMPLES_DIR / "sample2.mp4",
            "json": OUTPUT_DIR / "sample2_fusion_steps.json",
            "video_out": OUTPUT_DIR / "sample2_annotated_hud.mp4" if args.save_video else None,
            "duration": args.max_duration,
        })
    if args.sample in ["1", "all"]:
        targets.append({
            "video": SAMPLES_DIR / "sample1.mp4",
            "json": OUTPUT_DIR / "sample1_fusion_steps.json",
            "video_out": OUTPUT_DIR / "sample1_annotated_hud.mp4" if args.save_video else None,
            "duration": args.max_duration or 60.0,
        })

    for t in targets:
        fusion.process_video(t["video"], t["json"], t["duration"])
        if t["video_out"]:
            from .video_annotator import render_solution4_annotated_video
            wav_path = OUTPUT_DIR / f"{t['video'].stem}_audio_temp.wav"
            render_solution4_annotated_video(
                video_path=t["video"],
                json_path=t["json"],
                wav_path=wav_path,
                output_video_path=t["video_out"],
                max_duration_sec=t["duration"],
            )


if __name__ == "__main__":
    main()
