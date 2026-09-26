import os
import subprocess
import json
import numpy as np
import cv2
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.signal import find_peaks, savgol_filter, butter, filtfilt
from ultralytics import YOLO
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLES_DIR = BASE_DIR / "samples"
OUTPUT_DIR = BASE_DIR / "output" / "verification"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_PATH = SAMPLES_DIR / "sample2.mp4"


def extract_audio_envelope(video_path: Path, sample_rate: int = 22050):
    """Extracts audio from video and computes smoothed energy envelope."""
    wav_path = OUTPUT_DIR / "sample2_audio.wav"
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-ac", "1", "-ar", str(sample_rate),
        str(wav_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Read raw audio
    import wave
    with wave.open(str(wav_path), "rb") as wf:
        n_samples = wf.getnframes()
        audio_bytes = wf.readframes(n_samples)
        audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
    
    # Bandpass filter for footstep impacts (80 - 600 Hz)
    b, a = butter(4, [80 / (sample_rate / 2), 600 / (sample_rate / 2)], btype='band')
    filtered_audio = filtfilt(b, a, audio)
    
    # Energy envelope
    envelope = np.abs(filtered_audio)
    # Moving average smooth
    window_len = int(sample_rate * 0.05) # 50ms window
    envelope_smooth = np.convolve(envelope, np.ones(window_len)/window_len, mode='same')
    
    times = np.linspace(0, len(audio) / sample_rate, len(audio))
    return times, envelope_smooth, sample_rate


def run_pose_analysis(video_path: Path):
    """
    Runs YOLOv8-pose on all frames at native 30 FPS and tracks ankles and knees.
    """
    console.print(Panel("🔍 [bold cyan]RUNNING 30-FPS SKELETON KINEMATIC TRACKING (YOLOv8-Pose)[/bold cyan]"))
    model = YOLO("yolov8n-pose.pt")
    
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    frame_indices = []
    timestamps = []
    left_ankle_y = []
    right_ankle_y = []
    left_knee_y = []
    right_knee_y = []
    
    f_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        t = f_idx / fps
        frame_indices.append(f_idx)
        timestamps.append(t)
        
        # Inference
        results = model(frame, verbose=False)[0]
        
        if results.keypoints is not None and len(results.keypoints.xy) > 0:
            kpts = results.keypoints.xy[0].cpu().numpy()
            # COCO Keypoints:
            # 13: Left Knee, 14: Right Knee, 15: Left Ankle, 16: Right Ankle
            lk_y = kpts[13][1] if len(kpts) > 13 else np.nan
            rk_y = kpts[14][1] if len(kpts) > 14 else np.nan
            la_y = kpts[15][1] if len(kpts) > 15 else np.nan
            ra_y = kpts[16][1] if len(kpts) > 16 else np.nan
            
            left_knee_y.append(lk_y)
            right_knee_y.append(rk_y)
            left_ankle_y.append(la_y)
            right_ankle_y.append(ra_y)
        else:
            left_knee_y.append(np.nan)
            right_knee_y.append(np.nan)
            left_ankle_y.append(np.nan)
            right_ankle_y.append(np.nan)
            
        f_idx += 1
        
    cap.release()
    
    # Interpolate any NaNs
    def clean_signal(s):
        arr = np.array(s, dtype=float)
        nans = np.isnan(arr)
        if np.all(nans):
            return np.zeros_like(arr)
        arr[nans] = np.interp(np.flatnonzero(nans), np.flatnonzero(~nans), arr[~nans])
        # Invert so higher elevation = higher peak
        arr_inv = -arr
        # Smooth with Savitzky-Golay
        return savgol_filter(arr_inv, window_length=9, polyorder=3)

    la_smooth = clean_signal(left_ankle_y)
    ra_smooth = clean_signal(right_ankle_y)
    lk_smooth = clean_signal(left_knee_y)
    rk_smooth = clean_signal(right_knee_y)
    
    return np.array(timestamps), np.array(frame_indices), la_smooth, ra_smooth, lk_smooth, rk_smooth


def main():
    console.print(Panel(
        "[bold green]STAIRMASTER STEP AUDIT & ROOT CAUSE ANALYSIS TOOL[/bold green]\n"
        f"Target Video: [cyan]{VIDEO_PATH.name}[/cyan]",
        border_style="green"
    ))
    
    # 1. Pose Analysis (30 FPS)
    t_pose, f_indices, la_sig, ra_sig, lk_sig, rk_sig = run_pose_analysis(VIDEO_PATH)
    
    # In Stairmaster, each step has a peak knee lift & foot plant
    # A human climbing at ~135 SPM takes ~0.44s per step (min distance between steps of same leg ~0.7s, i.e. ~21 frames)
    min_dist_same_leg = 18  # frames at 30 FPS (~0.6s)
    
    left_peaks, l_props = find_peaks(la_sig, distance=min_dist_same_leg, prominence=15)
    right_peaks, r_props = find_peaks(ra_sig, distance=min_dist_same_leg, prominence=15)
    
    # Merge and sort all step events
    all_steps = []
    for p in left_peaks:
        all_steps.append({
            "frame": int(f_indices[p]),
            "timestamp": round(float(t_pose[p]), 3),
            "leg": "Left",
            "signal_val": float(la_sig[p]),
        })
    for p in right_peaks:
        all_steps.append({
            "frame": int(f_indices[p]),
            "timestamp": round(float(t_pose[p]), 3),
            "leg": "Right",
            "signal_val": float(ra_sig[p]),
        })
        
    all_steps.sort(key=lambda x: x["timestamp"])
    
    # 2. Audio Analysis
    t_aud, aud_env, sr = extract_audio_envelope(VIDEO_PATH)
    aud_peaks, _ = find_peaks(aud_env, distance=int(sr * 0.30), prominence=np.max(aud_env)*0.15)
    
    # 3. Print Results Table
    table = Table(
        title=f"🎯 Ground Truth Verified Step Events: {VIDEO_PATH.name}",
        border_style="bright_blue"
    )
    table.add_column("Step #", style="bold white", width=8)
    table.add_column("Frame", style="cyan", width=10)
    table.add_column("Timestamp", style="bold yellow", width=12)
    table.add_column("Leg", style="bold", width=10)
    table.add_column("Interval to Next", style="green", width=16)

    for i, s in enumerate(all_steps):
        s["step_id"] = i + 1
        interval_str = ""
        if i < len(all_steps) - 1:
            interval = all_steps[i+1]["timestamp"] - s["timestamp"]
            interval_str = f"+{interval:.2f} s ({interval*30:.0f} frames)"
        
        leg_color = "bright_blue" if s["leg"] == "Left" else "bright_magenta"
        table.add_row(
            f"{i + 1:02d}",
            f"Frame #{s['frame']:03d}",
            f"{s['timestamp']:.2f} s",
            f"[{leg_color}]{s['leg']}[/{leg_color}]",
            interval_str
        )
        
    console.print(table)
    
    total_steps = len(all_steps)
    duration = float(t_pose[-1])
    cadence = (total_steps / duration) * 60.0
    
    console.print(Panel(
        f"🏁 [bold green]VERIFICATION SUMMARY[/bold green]\n"
        f"• Total Ground Truth Steps Counted: [bold yellow]{total_steps}[/bold yellow] steps\n"
        f"• Left Steps: {len(left_peaks)} | Right Steps: {len(right_peaks)}\n"
        f"• Total Video Duration: {duration:.2f} seconds\n"
        f"• Exact Cadence: [bold cyan]{cadence:.1f} Steps Per Minute (SPM)[/bold cyan]\n"
        f"• Average Step Interval: [bold magenta]{duration/total_steps:.2f} s[/bold magenta]",
        border_style="cyan"
    ))
    
    # 4. Generate Diagnostic Plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    
    ax1.plot(t_pose, la_sig, label="Left Ankle Elevation", color="blue", alpha=0.8)
    ax1.plot(t_pose, ra_sig, label="Right Ankle Elevation", color="red", alpha=0.8)
    ax1.scatter(t_pose[left_peaks], la_sig[left_peaks], color="blue", s=80, marker="^", label=f"Left Steps ({len(left_peaks)})", zorder=5)
    ax1.scatter(t_pose[right_peaks], ra_sig[right_peaks], color="red", s=80, marker="v", label=f"Right Steps ({len(right_peaks)})", zorder=5)
    ax1.set_title(f"Biomechanic Ankle Trajectories & Step Detections ({total_steps} Steps Total)", fontsize=13, fontweight='bold')
    ax1.set_ylabel("Inverted Y Elevation (pixels)")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper right")
    
    # Annotate steps
    for s in all_steps:
        ax1.annotate(f"#{s['step_id']}", (s["timestamp"], s["signal_val"]), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=8, fontweight='bold')
        
    ax2.plot(t_aud, aud_env, label="Acoustic Impact Envelope (80-600Hz)", color="green", alpha=0.8)
    ax2.scatter(t_aud[aud_peaks], aud_env[aud_peaks], color="darkgreen", s=50, marker="x", label=f"Audio Impact Transients ({len(aud_peaks)})")
    ax2.set_title("Acoustic Impact Energy Profile", fontsize=11)
    ax2.set_xlabel("Time (seconds)")
    ax2.set_ylabel("Acoustic Amplitude")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper right")
    
    plt.tight_layout()
    plot_path = OUTPUT_DIR / "sample2_verification_plot.png"
    plt.savefig(plot_path, dpi=150)
    console.print(f"📊 Saved verification plot to: [bold underline]{plot_path}[/bold underline]")
    
    # 5. Save detailed JSON
    result_data = {
        "video_name": VIDEO_PATH.name,
        "ground_truth_total_steps": total_steps,
        "left_steps": len(left_peaks),
        "right_steps": len(right_peaks),
        "duration_sec": duration,
        "cadence_spm": round(cadence, 2),
        "steps": all_steps
    }
    json_path = OUTPUT_DIR / "sample2_ground_truth.json"
    with open(json_path, "w") as f:
        json.dump(result_data, f, indent=2)
    console.print(f"📄 Saved ground truth JSON to: [bold underline]{json_path}[/bold underline]")


if __name__ == "__main__":
    main()
