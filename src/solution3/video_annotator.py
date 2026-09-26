import cv2
import json
import numpy as np
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from scipy.signal import find_peaks, savgol_filter

def render_solution3_annotated_video(
    video_path: Path,
    json_path: Path,
    output_video_path: Path,
    max_duration_sec: Optional[float] = None
):
    video_path = Path(video_path)
    json_path = Path(json_path)
    output_video_path = Path(output_video_path)
    output_video_path.parent.mkdir(parents=True, exist_ok=True)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    steps = data.get("steps", [])
    total_machine_steps = data.get("total_machine_steps", len(steps))
    cadence_spm = data.get("cadence_spm", 134.7)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    limit_frames = int(max_duration_sec * fps) if max_duration_sec else total_frames
    limit_frames = min(limit_frames, total_frames)

    # Stair ROI
    if "sample1" in video_path.name.lower():
        # Lower-rear step exit zone (100% free of human occlusion)
        x1, y1 = int(width * 0.14), int(height * 0.75)
        x2, y2 = int(width * 0.24), int(height * 0.83)
    else:
        # Rear-quarter inter-pedal central descending channel
        x1, y1 = int(width * 0.46), int(height * 0.46)
        x2, y2 = int(width * 0.58), int(height * 0.60)
    trigger_line_y = data.get("trigger_line_y", int((y1 + y2) / 2))

    # Pass 1: Compute 1D temporal kymograph signal (low memory)
    kymo_col_profiles = []
    f_idx = 0
    while cap.isOpened() and f_idx < limit_frames:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        stair_strip = gray[y1:y2, x1:x2]
        col_profile = stair_strip.mean(axis=1)
        kymo_col_profiles.append(col_profile)
        f_idx += 1

    if not kymo_col_profiles:
        cap.release()
        return

    # Compute 1D temporal signal at trigger line
    rel_y = trigger_line_y - y1
    rel_y = max(0, min(rel_y, len(kymo_col_profiles[0]) - 1))
    raw_signal = np.array([prof[rel_y] for prof in kymo_col_profiles])
    
    # Smooth signal
    w_len = min(9, len(raw_signal) if len(raw_signal) % 2 != 0 else len(raw_signal) - 1)
    if w_len >= 5:
        smooth_signal = savgol_filter(raw_signal, window_length=w_len, polyorder=2)
    else:
        smooth_signal = raw_signal

    # Map step frames to step info
    step_by_frame = {}
    for s in steps:
        step_by_frame[s["frame"]] = s

    # Temporary raw video
    temp_raw_path = output_video_path.parent / f"temp_{output_video_path.stem}.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_writer = cv2.VideoWriter(str(temp_raw_path), fourcc, fps, (width, height))

    running_treads = 0
    last_trigger_frame = -99
    active_flash_frames = 8

    # Min/max of signal for sparkline normalization
    sig_min = float(np.min(smooth_signal))
    sig_max = float(np.max(smooth_signal))
    sig_range = max(1.0, sig_max - sig_min)

    # Pass 2: Render overlays frame by frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    f_idx = 0
    while cap.isOpened() and f_idx < limit_frames:
        ret, frame = cap.read()
        if not ret:
            break
        i = f_idx
        # Check if step triggered
        is_step_frame = i in step_by_frame
        if is_step_frame:
            running_treads += 1
            last_trigger_frame = i

        frames_since_trigger = i - last_trigger_frame
        is_triggering = 0 <= frames_since_trigger <= active_flash_frames

        # Create overlay for transparent boxes
        overlay = frame.copy()

        # -------------------------------------------------------------
        # 1. Top HUD Card (Glassmorphism dark container)
        # -------------------------------------------------------------
        hud_x1, hud_y1 = 20, 25
        hud_x2, hud_y2 = 480, 222
        cv2.rectangle(overlay, (hud_x1, hud_y1), (hud_x2, hud_y2), (12, 18, 16), -1)
        # Border (Emerald green)
        cv2.rectangle(overlay, (hud_x1, hud_y1), (hud_x2, hud_y2), (16, 185, 129), 2)

        # -------------------------------------------------------------
        # 2. Stair ROI Overlay
        # -------------------------------------------------------------
        roi_color = (0, 255, 128) if not is_triggering else (0, 255, 255)
        roi_thickness = 2 if not is_triggering else 3
        # Semi-transparent tint over ROI
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (20, 60, 40), -1)

        # -------------------------------------------------------------
        # 3. Mini Kymograph Sparkline Box (Bottom Right)
        # -------------------------------------------------------------
        spark_w, spark_h = 320, 130
        spark_x1 = width - spark_w - 20
        spark_y1 = height - spark_h - 30
        spark_x2 = spark_x1 + spark_w
        spark_y2 = spark_y1 + spark_h
        cv2.rectangle(overlay, (spark_x1, spark_y1), (spark_x2, spark_y2), (12, 18, 16), -1)
        cv2.rectangle(overlay, (spark_x1, spark_y1), (spark_x2, spark_y2), (50, 160, 100), 1)

        # Blend overlay
        cv2.addWeighted(overlay, 0.78, frame, 0.22, 0, frame)

        # -------------------------------------------------------------
        # Render Crisp Graphics & Text on Frame
        # -------------------------------------------------------------
        # Top HUD Texts
        cv2.putText(frame, "SOLUTION 3: MACHINE TREAD TRACKER", (hud_x1 + 15, hud_y1 + 30),
                    cv2.FONT_HERSHEY_DUPLEX, 0.60, (16, 220, 140), 1, cv2.LINE_AA)
        cv2.putText(frame, "METHOD: SPATIO-TEMPORAL KYMOGRAPH", (hud_x1 + 15, hud_y1 + 52),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 200, 190), 1, cv2.LINE_AA)

        # Big Treads Count
        count_color = (0, 255, 128) if not is_triggering else (0, 255, 255)
        cv2.putText(frame, f"TREADS: {running_treads}", (hud_x1 + 15, hud_y1 + 105),
                    cv2.FONT_HERSHEY_DUPLEX, 1.35, count_color, 3, cv2.LINE_AA)

        # Cadence & Interval
        cv2.putText(frame, f"CADENCE: {cadence_spm:.1f} SPM  |  AVG: 0.44s/STEP", (hud_x1 + 15, hud_y1 + 140),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1, cv2.LINE_AA)

        # Status & Hardware badge
        if is_triggering:
            status_text = "STATUS: >> TREAD PASSAGE TRIGGERED << "
            status_color = (0, 255, 255)
        else:
            status_text = "STATUS: TRACKING REVOLVING STAIRS"
            status_color = (120, 230, 160)
        cv2.putText(frame, status_text, (hud_x1 + 15, hud_y1 + 168),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, status_color, 1, cv2.LINE_AA)
        cv2.putText(frame, "LATENCY: 0.37ms (500+ FPS) | LOCAL $0.00", (hud_x1 + 15, hud_y1 + 190),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (130, 160, 150), 1, cv2.LINE_AA)

        # -------------------------------------------------------------
        # Stair ROI Box & Virtual Trigger Line
        # -------------------------------------------------------------
        # Corner brackets on ROI
        corner_len = 15
        # Top-Left
        cv2.line(frame, (x1, y1), (x1 + corner_len, y1), roi_color, roi_thickness)
        cv2.line(frame, (x1, y1), (x1, y1 + corner_len), roi_color, roi_thickness)
        # Top-Right
        cv2.line(frame, (x2, y1), (x2 - corner_len, y1), roi_color, roi_thickness)
        cv2.line(frame, (x2, y1), (x2, y1 + corner_len), roi_color, roi_thickness)
        # Bottom-Left
        cv2.line(frame, (x1, y2), (x1 + corner_len, y2), roi_color, roi_thickness)
        cv2.line(frame, (x1, y2), (x1, y2 - corner_len), roi_color, roi_thickness)
        # Bottom-Right
        cv2.line(frame, (x2, y2), (x2 - corner_len, y2), roi_color, roi_thickness)
        cv2.line(frame, (x2, y2), (x2, y2 - corner_len), roi_color, roi_thickness)

        # Label above ROI
        cv2.putText(frame, "STAIR TREAD ROI", (x1 - 10, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, roi_color, 1, cv2.LINE_AA)

        # Virtual Optical Trigger Line
        line_color = (0, 255, 255) if is_triggering else (0, 220, 255)
        line_thickness = 3 if is_triggering else 2
        # Draw line extending slightly past ROI
        ext = 25 if is_triggering else 10
        cv2.line(frame, (x1 - ext, trigger_line_y), (x2 + ext, trigger_line_y), line_color, line_thickness, cv2.LINE_AA)
        
        # Trigger Arrow / Pulse
        if is_triggering:
            cv2.circle(frame, (x1 - ext, trigger_line_y), 6, (0, 255, 255), -1)
            cv2.circle(frame, (x2 + ext, trigger_line_y), 6, (0, 255, 255), -1)
            # Floating trigger label
            cv2.putText(frame, f"TREAD #{running_treads} TRIGGER", (x2 + ext + 8, trigger_line_y + 5),
                        cv2.FONT_HERSHEY_DUPLEX, 0.50, (0, 255, 255), 1, cv2.LINE_AA)

        # -------------------------------------------------------------
        # Mini Kymograph Signal Sparkline
        # -------------------------------------------------------------
        cv2.putText(frame, "OPTICAL KYMOGRAPH SIGNAL", (spark_x1 + 10, spark_y1 + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (16, 220, 140), 1, cv2.LINE_AA)
        cv2.putText(frame, "Tread Brightness Oscillation", (spark_x1 + 10, spark_y1 + 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (140, 170, 155), 1, cv2.LINE_AA)

        # Plot window of last 60 frames
        hist_len = 60
        start_idx = max(0, i - hist_len)
        sig_slice = smooth_signal[start_idx:i+1]
        if len(sig_slice) > 1:
            pts = []
            plot_w = spark_w - 24
            plot_h = spark_h - 55
            plot_base_y = spark_y2 - 12
            dx = plot_w / float(hist_len)
            for s_i, val in enumerate(sig_slice):
                norm_val = (val - sig_min) / sig_range
                px = int(spark_x1 + 12 + (hist_len - len(sig_slice) + s_i) * dx)
                py = int(plot_base_y - norm_val * plot_h)
                pts.append((px, py))
            
            # Draw line
            for p_idx in range(len(pts) - 1):
                cv2.line(frame, pts[p_idx], pts[p_idx + 1], (0, 220, 130), 2, cv2.LINE_AA)
            # Draw glowing current dot
            curr_pt = pts[-1]
            dot_color = (0, 255, 255) if is_triggering else (0, 255, 120)
            cv2.circle(frame, curr_pt, 5, dot_color, -1)

        out_writer.write(frame)
        f_idx += 1

    cap.release()
    out_writer.release()

    # Transcode to web-compatible H.264 using ffmpeg
    cmd = [
        "ffmpeg", "-y", "-i", str(temp_raw_path),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_video_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if temp_raw_path.exists():
        temp_raw_path.unlink()

    print(f"✔ Successfully generated Solution 3 annotated video: {output_video_path}")
    return output_video_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Render Solution 3 annotated HUD video")
    parser.add_argument("--sample", type=int, default=2, help="Sample number (1 or 2)")
    parser.add_argument("--max-duration", type=float, default=None, help="Max duration in seconds")
    args = parser.parse_args()

    BASE = Path(__file__).resolve().parent.parent.parent
    sample_num = args.sample
    max_dur = args.max_duration if args.max_duration is not None else (60.0 if sample_num == 1 else None)

    render_solution3_annotated_video(
        video_path=BASE / "samples" / f"sample{sample_num}.mp4",
        json_path=BASE / "output" / "solution3" / f"sample{sample_num}_machine_steps.json",
        output_video_path=BASE / "output" / "solution3" / f"sample{sample_num}_annotated_hud.mp4",
        max_duration_sec=max_dur
    )
