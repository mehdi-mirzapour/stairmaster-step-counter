import cv2
import json
import wave
import numpy as np
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from scipy.signal import butter, filtfilt

def extract_and_filter_audio(wav_path: Path):
    with wave.open(str(wav_path), "rb") as wf:
        sr = wf.getframerate()
        n_samples = wf.getnframes()
        audio_bytes = wf.readframes(n_samples)
        audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)

    # 60 - 350 Hz bandpass filter for mechanical footstrike thuds
    nyq = sr / 2.0
    b, a = butter(4, [60.0 / nyq, 350.0 / nyq], btype='band')
    filtered = filtfilt(b, a, audio)
    envelope = np.abs(filtered)
    win_len = int(sr * 0.08)  # 80ms smoothing
    smoothed = np.convolve(envelope, np.ones(win_len) / win_len, mode='same')
    max_val = np.max(smoothed) if np.max(smoothed) > 0 else 1.0
    norm_env = smoothed / max_val
    return norm_env, sr


def render_solution5_annotated_video(
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
    total_steps = data.get("total_steps", len(steps))
    cadence_spm = data.get("cadence_spm", 34.0)

    # Extract audio track if not already present
    wav_path = output_video_path.parent / f"{video_path.stem}_audio_track.wav"
    if not wav_path.exists():
        cmd = [
            "ffmpeg", "-y", "-i", str(video_path),
            "-vn", "-ac", "1", "-ar", "22050",
            str(wav_path)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    norm_audio_env, audio_sr = extract_and_filter_audio(wav_path)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    limit_frames = int(max_duration_sec * fps) if max_duration_sec else total_frames
    limit_frames = min(limit_frames, total_frames)

    # Map step events to target frames
    step_events = []
    for s in steps:
        t = s["timestamp_sec"]
        frame_target = int(round(t * fps))
        step_events.append({
            "target_frame": frame_target,
            "timestamp_sec": t,
            "step_id": s.get("step_id", 0),
            "amplitude": s.get("amplitude", 0.0),
        })

    temp_raw_path = output_video_path.parent / f"temp_{output_video_path.stem}.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_writer = cv2.VideoWriter(str(temp_raw_path), fourcc, fps, (width, height))

    running_steps = 0
    active_step_info = None
    step_callout_until_frame = -1
    triggered_step_ids = set()

    # Pre-calculate audio oscilloscope parameters
    osc_h = int(height * 0.16)
    osc_w = int(width * 0.92)
    osc_x = int((width - osc_w) / 2)
    osc_y = height - osc_h - int(height * 0.04)

    f_idx = 0
    while cap.isOpened() and f_idx < limit_frames:
        ret, frame = cap.read()
        if not ret:
            break

        t_sec = f_idx / fps

        # Check for step event
        for s in step_events:
            if s["step_id"] not in triggered_step_ids and abs(f_idx - s["target_frame"]) <= 1:
                triggered_step_ids.add(s["step_id"])
                running_steps += 1
                active_step_info = s
                step_callout_until_frame = f_idx + 12
                break

        is_callout_active = (f_idx <= step_callout_until_frame) and (active_step_info is not None)

        # -------------------------------------------------------------
        # Top HUD Banner
        # -------------------------------------------------------------
        hud_w = int(width * 0.92)
        hud_h = int(height * 0.13)
        hud_x = int((width - hud_w) / 2)
        hud_y = int(height * 0.03)

        overlay = frame.copy()
        cv2.rectangle(overlay, (hud_x, hud_y), (hud_x + hud_w, hud_y + hud_h), (12, 18, 26), -1)
        border_col = (0, 255, 120) if is_callout_active else (220, 140, 20)
        cv2.rectangle(overlay, (hud_x, hud_y), (hud_x + hud_w, hud_y + hud_h), border_col, 3)
        cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)

        # Title & Status
        cv2.putText(frame, "SOLUTION 5: ACOUSTIC FOOTSTRIKE DSP", (hud_x + 25, hud_y + 40),
                    cv2.FONT_HERSHEY_DUPLEX, 0.85, (0, 240, 255), 2, cv2.LINE_AA)
        
        # Step counter
        count_col = (0, 255, 100) if is_callout_active else (255, 255, 255)
        cv2.putText(frame, f"STEPS: {running_steps} / {total_steps}", (hud_x + 25, hud_y + 95),
                    cv2.FONT_HERSHEY_DUPLEX, 1.45, count_col, 3, cv2.LINE_AA)

        # Cadence & Privacy Tag
        cv2.putText(frame, f"CADENCE: {cadence_spm:.1f} SPM", (hud_x + 480, hud_y + 90),
                    cv2.FONT_HERSHEY_DUPLEX, 0.80, (0, 255, 200), 2, cv2.LINE_AA)
        cv2.putText(frame, "ZERO VISION  |  100% PRIVACY PRESERVING", (hud_x + 25, hud_y + 130),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (140, 180, 210), 1, cv2.LINE_AA)

        # Pulse indicator badge if active
        if is_callout_active:
            badge_x = hud_x + hud_w - 240
            badge_y = hud_y + 30
            cv2.rectangle(frame, (badge_x, badge_y), (badge_x + 220, badge_y + 50), (0, 220, 100), -1)
            cv2.putText(frame, "IMPACT DETECTED", (badge_x + 12, badge_y + 34),
                        cv2.FONT_HERSHEY_DUPLEX, 0.58, (0, 0, 0), 2, cv2.LINE_AA)

        # -------------------------------------------------------------
        # Bottom Audio Oscilloscope
        # -------------------------------------------------------------
        osc_overlay = frame.copy()
        cv2.rectangle(osc_overlay, (osc_x, osc_y), (osc_x + osc_w, osc_y + osc_h), (10, 14, 22), -1)
        cv2.rectangle(osc_overlay, (osc_x, osc_y), (osc_x + osc_w, osc_y + osc_h), (0, 180, 255), 2)
        cv2.addWeighted(osc_overlay, 0.85, frame, 0.15, 0, frame)

        # Oscilloscope Title
        cv2.putText(frame, "ACOUSTIC TRANSIENT OSCILLOSCOPE (60-350Hz BANDPASS)", (osc_x + 20, osc_y + 28),
                    cv2.FONT_HERSHEY_DUPLEX, 0.55, (0, 220, 255), 1, cv2.LINE_AA)

        # Rolling window of audio around current time: [-2.0s, +1.0s]
        win_start_t = t_sec - 2.0
        win_end_t = t_sec + 1.0
        win_dur = win_end_t - win_start_t

        s_start = max(0, int(win_start_t * audio_sr))
        s_end = min(len(norm_audio_env), int(win_end_t * audio_sr))

        if s_end > s_start:
            sub_env = norm_audio_env[s_start:s_end]
            sub_t = np.linspace(win_start_t, win_end_t, len(sub_env))

            pts = []
            plot_h = osc_h - 45
            base_y = osc_y + osc_h - 12
            for val_i, env_val in enumerate(sub_env):
                px = int(osc_x + 20 + (val_i / len(sub_env)) * (osc_w - 40))
                py = int(base_y - env_val * plot_h * 0.95)
                pts.append((px, py))

            if len(pts) > 1:
                cv2.polylines(frame, [np.array(pts, dtype=np.int32)], False, (0, 255, 140), 2, cv2.LINE_AA)

            # Center Playhead Marker (at 2.0 / 3.0 of width)
            playhead_x = int(osc_x + 20 + (2.0 / win_dur) * (osc_w - 40))
            cv2.line(frame, (playhead_x, osc_y + 35), (playhead_x, base_y), (0, 255, 255), 2)
            cv2.putText(frame, "NOW", (playhead_x - 18, osc_y + 48),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 255, 255), 1, cv2.LINE_AA)

            # Draw impact event markers in the window
            for s in step_events:
                if win_start_t <= s["timestamp_sec"] <= win_end_t:
                    marker_x = int(osc_x + 20 + ((s["timestamp_sec"] - win_start_t) / win_dur) * (osc_w - 40))
                    cv2.circle(frame, (marker_x, base_y - int(plot_h * 0.5)), 6, (0, 255, 0), -1)
                    cv2.line(frame, (marker_x, osc_y + 38), (marker_x, base_y), (0, 200, 0), 1, cv2.LINE_AA)

        out_writer.write(frame)
        f_idx += 1

    cap.release()
    out_writer.release()

    # Transcode with ffmpeg
    cmd = [
        "ffmpeg", "-y", "-i", str(temp_raw_path),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_video_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if temp_raw_path.exists():
        temp_raw_path.unlink()

    print(f"✔ Successfully rendered Solution 5 Annotated Video: {output_video_path}")
    return output_video_path
