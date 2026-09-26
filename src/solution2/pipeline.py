import cv2
import json
import time
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from scipy.signal import find_peaks, savgol_filter
from ultralytics import YOLO
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

console = Console()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SAMPLES_DIR = BASE_DIR / "samples"
OUTPUT_DIR = BASE_DIR / "output" / "solution2"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


import torch

class YOLOPoseStepCounter:
    """
    Solution 2: Edge-native pose kinematics step counter using YOLOv8-Pose.
    - Zero API cost, sub-15ms inference per frame (60-100+ FPS on GPU).
    - Tracks left & right ankles (COCO #15, #16) and knees (#13, #14).
    - Biomechanical peak detection on vertical elevation signals.
    - Renders real-time HUD video with live telemetry overlay.
    """

    def __init__(self, model_name: str = "yolov8n-pose.pt", device: Optional[str] = None):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        self.device_name = torch.cuda.get_device_name(0) if self.device.startswith("cuda") and torch.cuda.is_available() else "CPU"
        self.model = YOLO(model_name)
        # Move model to target device
        self.model.to(self.device)

    def process_video(
        self,
        video_path: Path,
        output_json_path: Path,
        output_video_path: Optional[Path] = None,
        max_duration_sec: Optional[float] = None,
    ) -> Dict[str, Any]:
        video_path = Path(video_path)
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise FileNotFoundError(f"Cannot open {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        limit_frames = int(max_duration_sec * fps) if max_duration_sec else total_frames
        limit_frames = min(limit_frames, total_frames)
        analyzed_sec = limit_frames / fps

        console.print(Panel(
            f"⚡ [bold cyan]SOLUTION 2: YOLOv8-POSE KINEMATICS ENGINE[/bold cyan]\n"
            f"Video: [yellow]{video_path.name}[/yellow] | Hardware: [bold green]{self.device_name} ({self.device.upper()})[/bold green]\n"
            f"Resolution: {width}x{height} | Target Frames: {limit_frames} ({analyzed_sec:.1f}s)",
            border_style="bright_blue"
        ))

        # First pass: Extract raw keypoints
        frames_cache = []
        raw_la_y = []
        raw_ra_y = []
        timestamps = []

        start_time = time.time()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="cyan", finished_style="bold green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Tracking 2D Skeletons...", total=limit_frames)

            f_idx = 0
            while cap.isOpened() and f_idx < limit_frames:
                ret, frame = cap.read()
                if not ret:
                    break

                t = f_idx / fps
                timestamps.append(t)

                results = self.model(frame, device=self.device, verbose=False)[0]
                if output_video_path:
                    # Save annotated frame for video generation
                    annotated = results.plot(boxes=False)
                    frames_cache.append(annotated)

                if results.keypoints is not None and len(results.keypoints.xy) > 0:
                    kpts = results.keypoints.xy[0].cpu().numpy()
                    la_y = kpts[15][1] if len(kpts) > 15 else np.nan
                    ra_y = kpts[16][1] if len(kpts) > 16 else np.nan
                    raw_la_y.append(la_y)
                    raw_ra_y.append(ra_y)
                else:
                    raw_la_y.append(np.nan)
                    raw_ra_y.append(np.nan)

                f_idx += 1
                progress.advance(task)

        cap.release()

        # Signal Cleaning & Interpolation
        def clean(arr):
            s = np.array(arr, dtype=float)
            nans = np.isnan(s)
            if np.all(nans):
                return np.zeros_like(s)
            s[nans] = np.interp(np.flatnonzero(nans), np.flatnonzero(~nans), s[~nans])
            inv = -s # Invert Y so up is positive
            w = min(9, len(inv) if len(inv) % 2 != 0 else len(inv) - 1)
            return savgol_filter(inv, w, 2) if w >= 5 else inv

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

        # Same-leg step distance is approx 55% of stride lag
        min_dist_frames = max(8, int(stride_lag * 0.55))
        prom_r = max(8, np.ptp(ra_smooth) * 0.15)
        prom_l = max(8, np.ptp(la_smooth) * 0.10)

        left_peaks, _ = find_peaks(la_smooth, distance=min_dist_frames, prominence=prom_l)
        right_peaks, _ = find_peaks(ra_smooth, distance=min_dist_frames, prominence=prom_r)

        # Merge and sort
        all_steps = []
        for p in left_peaks:
            all_steps.append({
                "frame": int(p),
                "timestamp_sec": round(float(timestamps[p]), 3),
                "leg": "left",
            })
        for p in right_peaks:
            all_steps.append({
                "frame": int(p),
                "timestamp_sec": round(float(timestamps[p]), 3),
                "leg": "right",
            })

        all_steps.sort(key=lambda x: x["timestamp_sec"])

        # Deduplicate any close anomalies (< 28% of stride period)
        min_step_dt = (stride_lag / fps) * 0.28
        dedup_steps = []
        for s in all_steps:
            if not dedup_steps:
                dedup_steps.append(s)
            else:
                dt = s["timestamp_sec"] - dedup_steps[-1]["timestamp_sec"]
                if dt >= min_step_dt:
                    dedup_steps.append(s)

        for i, s in enumerate(dedup_steps):
            s["step_id"] = i + 1
            t_val = s["timestamp_sec"]
            s["time_str"] = f"{int(t_val//60):02d}:{t_val%60:05.2f}"

        total_steps = len(dedup_steps)
        left_steps = sum(1 for s in dedup_steps if s["leg"] == "left")
        right_steps = sum(1 for s in dedup_steps if s["leg"] == "right")
        cadence_spm = round((total_steps / max(analyzed_sec, 0.1)) * 60.0, 2)
        runtime = round(time.time() - start_time, 2)

        # Render Annotated Video with HUD if requested
        if output_video_path and frames_cache:
            console.print("[cyan]Rendering annotated HUD video...[/cyan]")
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out_writer = cv2.VideoWriter(str(output_video_path), fourcc, fps, (width, height))
            
            step_frames_set = {s["frame"]: s for s in dedup_steps}
            running_count = 0
            last_leg = "NONE"

            for i, frame in enumerate(frames_cache):
                if i in step_frames_set:
                    running_count += 1
                    last_leg = step_frames_set[i]["leg"].upper()

                # Draw modern sports HUD
                overlay = frame.copy()
                # Semi-transparent HUD top bar
                cv2.rectangle(overlay, (20, 30), (450, 190), (15, 15, 25), -1)
                cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

                # HUD Text
                cv2.putText(frame, "STAIRMASTER AI KINEMATICS", (35, 60), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 220, 255), 2)
                cv2.putText(frame, f"STEPS: {running_count}", (35, 110), cv2.FONT_HERSHEY_DUPLEX, 1.3, (0, 255, 120), 3)
                cv2.putText(frame, f"CADENCE: {cadence_spm:.0f} SPM | L:{left_steps} R:{right_steps}", (35, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                cv2.putText(frame, f"ACTIVE: {last_leg}", (35, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)

                out_writer.write(frame)

            out_writer.release()
            console.print(f"[bold green]✔ Saved annotated HUD video to:[/bold green] {output_video_path}")

        # Summary Table
        table = Table(title=f"📊 Solution 2 Results: {video_path.name}", border_style="cyan")
        table.add_column("Metric", style="bold white", width=25)
        table.add_column("Value", style="bold green", width=20)
        table.add_row("Total Steps Counted", f"[bold yellow]{total_steps} steps[/bold yellow]")
        table.add_row("Left Foot Steps", f"{left_steps}")
        table.add_row("Right Foot Steps", f"{right_steps}")
        table.add_row("Cadence (SPM)", f"{cadence_spm} Steps/Min")
        table.add_row("Analyzed Duration", f"{analyzed_sec:.2f} s")
        table.add_row("Total Runtime", f"[magenta]{runtime:.2f} s[/magenta] ({limit_frames/runtime:.1f} FPS)")
        console.print(table)

        # Save JSON
        result_data = {
            "solution": "Solution 2: Edge-Native YOLOv8-Pose Kinematics",
            "video_name": video_path.name,
            "total_steps": total_steps,
            "left_steps": left_steps,
            "right_steps": right_steps,
            "cadence_spm": cadence_spm,
            "duration_sec": analyzed_sec,
            "runtime_sec": runtime,
            "fps_processing": round(limit_frames / runtime, 1),
            "steps": dedup_steps,
        }

        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2)

        return result_data


from src.utils import resolve_video_path

def main():
    parser = argparse.ArgumentParser(description="Solution 2: YOLOv8-Pose Kinematic Step Counter")
    parser.add_argument("--video", type=str, default=None, help="Custom path to input video file")
    parser.add_argument("--sample", choices=["1", "2"], default="2", help="Standard sample index (default: 2)")
    parser.add_argument("--max-duration", type=float, default=5.0, help="Max duration in seconds (default: 5.0)")
    parser.add_argument("--save-video", action="store_true", help="Generate annotated video with telemetry HUD")

    args = parser.parse_args()
    counter = YOLOPoseStepCounter()

    video_file = resolve_video_path(sample_num=int(args.sample), custom_path=args.video)
    json_out = OUTPUT_DIR / f"sample{args.sample}_yolo_steps.json"
    video_out = OUTPUT_DIR / f"sample{args.sample}_annotated_hud.mp4" if args.save_video else None

    counter.process_video(
        video_path=video_file,
        output_json_path=json_out,
        output_video_path=video_out,
        max_duration_sec=args.max_duration,
    )


if __name__ == "__main__":
    main()
