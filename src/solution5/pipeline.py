import cv2
import json
import time
import wave
import argparse
import subprocess
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from scipy.signal import butter, filtfilt, find_peaks

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SAMPLES_DIR = BASE_DIR / "samples"
OUTPUT_DIR = BASE_DIR / "output" / "solution5"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class AudioStepCounter:
    """
    Solution 5: Acoustic Impact Step Counter (Audio DSP).
    Zero-vision, privacy-preserving, ultra-low-power step tracking using
    acoustic footstrike transient analysis.
    """

    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate

    def extract_audio(self, video_path: Path, wav_path: Path, max_duration_sec: Optional[float] = None) -> np.ndarray:
        """Extracts mono audio from video using ffmpeg."""
        cmd = [
            "ffmpeg", "-y", "-i", str(video_path),
            "-vn", "-ac", "1", "-ar", str(self.sample_rate),
        ]
        if max_duration_sec:
            cmd.extend(["-t", str(max_duration_sec)])
        cmd.append(str(wav_path))

        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if not wav_path.exists():
            raise FileNotFoundError(f"Failed to extract audio to {wav_path}")

        with wave.open(str(wav_path), "rb") as wf:
            n_samples = wf.getnframes()
            audio_bytes = wf.readframes(n_samples)
            audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)

        return audio

    def process_video(
        self,
        video_path: Path,
        output_json: Path,
        max_duration_sec: Optional[float] = None,
    ) -> Dict[str, Any]:
        video_path = Path(video_path)
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        limit_frames = int(max_duration_sec * fps) if max_duration_sec else total_frames
        limit_frames = min(limit_frames, total_frames)
        analyzed_sec = limit_frames / fps

        console.print(Panel(
            f"🔊 [bold cyan]SOLUTION 5: ACOUSTIC FOOTSTRIKE DSP[/bold cyan]\n"
            f"Video: [yellow]{video_path.name}[/yellow] ({analyzed_sec:.1f}s analyzed)",
            border_style="cyan"
        ))

        start_time = time.time()
        wav_path = OUTPUT_DIR / f"{video_path.stem}_audio_track.wav"
        audio = self.extract_audio(video_path, wav_path, max_duration_sec=analyzed_sec)
        sr = self.sample_rate

        # 1. Bandpass filter for StairMaster foot impact (60-350 Hz)
        # Deep thud of foot/shoe impacting rubberized tread step
        nyq = sr / 2.0
        low = max(20.0, min(60.0, nyq - 100)) / nyq
        high = min(350.0, nyq - 50) / nyq
        b, a = butter(4, [low, high], btype='band')
        filtered = filtfilt(b, a, audio)

        # 2. Envelope extraction + smoothing
        envelope = np.abs(filtered)
        window_len = int(sr * 0.10)  # 100ms smoothing window
        smoothed = np.convolve(envelope, np.ones(window_len) / window_len, mode='same')

        # 3. Autocorrelation to detect dominant cadence
        factor = 50
        env_ds = smoothed[::factor]
        sr_ds = sr / factor
        env_centered = env_ds - np.mean(env_ds)
        corr = np.correlate(env_centered, env_centered, mode='full')
        corr = corr[len(corr)//2:]

        # Search lags from 0.30s (200 SPM sprint) to 3.0s (20 SPM slow climb)
        min_lag = max(1, int(0.30 * sr_ds))
        max_lag = min(len(corr) - 1, int(3.0 * sr_ds))
        if max_lag > min_lag:
            lag_peak = min_lag + np.argmax(corr[min_lag:max_lag])
            dominant_period = lag_peak / sr_ds
        else:
            dominant_period = 1.63

        dominant_spm = 60.0 / dominant_period

        # 4. Adaptive Peak Detection
        min_dist_samples = max(int(sr * 0.28), int(sr * min(1.10, dominant_period * 0.67)))
        prom = np.max(smoothed) * 0.105
        peaks, props = find_peaks(smoothed, distance=min_dist_samples, prominence=prom)

        steps = []
        for i, p in enumerate(peaks):
            t_sec = round(float(p) / sr, 3)
            steps.append({
                "step_id": i + 1,
                "timestamp_sec": t_sec,
                "time_str": f"{int(t_sec//60):02d}:{t_sec%60:05.2f}",
                "amplitude": round(float(smoothed[p]), 1),
                "confidence": 0.95,
            })

        total_steps = len(steps)
        cadence_spm = round((total_steps / max(analyzed_sec, 0.1)) * 60.0, 2)
        runtime = round(time.time() - start_time, 3)

        # Print summary
        table = Table(title=f"🔊 Solution 5 Acoustic Results: {video_path.name}", border_style="cyan")
        table.add_column("Metric", style="bold white", width=25)
        table.add_column("Value", style="bold green", width=20)
        table.add_row("Total Acoustic Steps", f"[bold yellow]{total_steps} steps[/bold yellow]")
        table.add_row("Detected Cadence", f"{cadence_spm} Steps/Min")
        table.add_row("Dominant Step Period", f"{dominant_period:.2f}s ({dominant_spm:.1f} SPM)")
        table.add_row("Bandpass Filter", "60 Hz - 350 Hz (Foot Thud)")
        table.add_row("Compute Cost", "$0.00 (Zero Vision / Pure DSP)")
        table.add_row("Processing Latency", f"[magenta]{runtime:.3f} s[/magenta]")
        console.print(table)

        res = {
            "solution": "Solution 5: Acoustic Footstrike DSP",
            "video_name": video_path.name,
            "total_steps": total_steps,
            "cadence_spm": cadence_spm,
            "dominant_period_sec": round(dominant_period, 3),
            "dominant_spm": round(dominant_spm, 1),
            "duration_sec": analyzed_sec,
            "runtime_sec": runtime,
            "compute_cost": 0.0,
            "steps": steps,
        }

        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2)

        console.print(f"[bold green]✔ Saved structured JSON to:[/bold green] {output_json}")
        return res


def main():
    import sys
    sys.path.insert(0, str(BASE_DIR))
    from src.solution5.video_annotator import render_solution5_annotated_video

    parser = argparse.ArgumentParser(description="Solution 5: Acoustic Footstrike DSP Step Counter")
    parser.add_argument("--sample", choices=["1", "2", "all"], default="1")
    parser.add_argument("--max-duration", type=float, default=None)
    parser.add_argument("--save-video", action="store_true", help="Generate annotated video with acoustic HUD")
    args = parser.parse_args()

    counter = AudioStepCounter()
    targets = []
    if args.sample in ["1", "all"]:
        targets.append({
            "video": SAMPLES_DIR / "sample1.mp4",
            "json": OUTPUT_DIR / "sample1_audio_steps.json",
            "video_out": OUTPUT_DIR / "sample1_annotated_hud.mp4" if args.save_video else None,
            "duration": args.max_duration or 60.0,
        })
    if args.sample in ["2", "all"]:
        targets.append({
            "video": SAMPLES_DIR / "sample2.mp4",
            "json": OUTPUT_DIR / "sample2_audio_steps.json",
            "video_out": OUTPUT_DIR / "sample2_annotated_hud.mp4" if args.save_video else None,
            "duration": args.max_duration,
        })

    for t in targets:
        counter.process_video(t["video"], t["json"], t["duration"])
        if t["video_out"]:
            render_solution5_annotated_video(
                video_path=t["video"],
                json_path=t["json"],
                output_video_path=t["video_out"],
                max_duration_sec=t["duration"],
            )


if __name__ == "__main__":
    main()
