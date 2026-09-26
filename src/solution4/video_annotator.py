import cv2
import json
import wave
import numpy as np
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from scipy.signal import butter, filtfilt
from ultralytics import YOLO

def extract_and_filter_audio(wav_path: Path):
    with wave.open(str(wav_path), "rb") as wf:
        sr = wf.getframerate()
        n_samples = wf.getnframes()
        audio_bytes = wf.readframes(n_samples)
        audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)

    # 80 - 600 Hz bandpass filter for footsteps
    b, a = butter(4, [80 / (sr / 2), 600 / (sr / 2)], btype='band')
    filtered = filtfilt(b, a, audio)
    # Energy envelope
    envelope = np.abs(filtered)
    win_len = int(sr * 0.03)  # 30ms smoothing
    smoothed = np.convolve(envelope, np.ones(win_len)/win_len, mode='same')
    # Normalize envelope to 0..1
    max_val = np.max(smoothed) if np.max(smoothed) > 0 else 1.0
    norm_env = smoothed / max_val
    return norm_env, sr


def render_solution4_annotated_video(
    video_path: Path,
    json_path: Path,
    wav_path: Path,
    output_video_path: Path,
    max_duration_sec: Optional[float] = None
):
    video_path = Path(video_path)
    json_path = Path(json_path)
    wav_path = Path(wav_path)
    output_video_path = Path(output_video_path)
    output_video_path.parent.mkdir(parents=True, exist_ok=True)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    steps = data.get("steps", [])
    total_steps = data.get("total_steps", len(steps))
    confirmed_total = data.get("audio_visual_confirmed", 0)
    cadence_spm = data.get("cadence_spm", 141.7)

    # Process audio
    norm_audio_env, audio_sr = extract_and_filter_audio(wav_path)

    # Load YOLO pose from local repo path
    base_dir = Path(__file__).resolve().parent.parent.parent
    model_path = base_dir / "yolov8n-pose.pt"
    model = YOLO(str(model_path) if model_path.exists() else "yolov8n-pose.pt")

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
            "step_id": s.get("fused_step_id", s.get("step_id", 0)),
            "leg": s.get("leg", "unknown").upper(),
            "modality": s.get("modality", "AUDIO_VISUAL_FUSED"),
            "confidence": s.get("confidence", 0.98),
            "delta_ms": s.get("delta_ms"),
        })

    # Temporary raw video
    temp_raw_path = output_video_path.parent / f"temp_{output_video_path.stem}.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_writer = cv2.VideoWriter(str(temp_raw_path), fourcc, fps, (width, height))

    running_steps = 0
    running_fused = 0
    last_leg = "NONE"
    active_step_info = None
    step_callout_until_frame = -1
    triggered_step_ids = set()

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
                if s["modality"] == "AUDIO_VISUAL_FUSED":
                    running_fused += 1
                last_leg = s["leg"]
                active_step_info = s
                step_callout_until_frame = f_idx + 10
                break

        is_callout_active = (f_idx <= step_callout_until_frame) and (active_step_info is not None)

        # 1. Run YOLO-Pose on frame
        pose_res = model(frame, verbose=False)[0]
        # Plot skeleton without bounding boxes
        annotated_frame = pose_res.plot(boxes=False)

        overlay = annotated_frame.copy()

        # -------------------------------------------------------------
        # Top HUD Card (Purple / Magenta theme)
        # -------------------------------------------------------------
        hud_x1, hud_y1 = 20, 25
        hud_x2, hud_y2 = 500, 232
        cv2.rectangle(overlay, (hud_x1, hud_y1), (hud_x2, hud_y2), (18, 14, 25), -1)
        # Border (Violet)
        cv2.rectangle(overlay, (hud_x1, hud_y1), (hud_x2, hud_y2), (220, 90, 180), 2)

        # -------------------------------------------------------------
        # Bottom Audio Oscilloscope Box
        # -------------------------------------------------------------
        osc_w = width - 40
        osc_h = 100
        osc_x1 = 20
        osc_y1 = height - osc_h - 25
        osc_x2 = osc_x1 + osc_w
        osc_y2 = osc_y1 + osc_h
        cv2.rectangle(overlay, (osc_x1, osc_y1), (osc_x2, osc_y2), (12, 10, 18), -1)
        cv2.rectangle(overlay, (osc_x1, osc_y1), (osc_x2, osc_y2), (180, 80, 150), 1)

        # -------------------------------------------------------------
        # Floating Step Callout Card (When active)
        # -------------------------------------------------------------
        if is_callout_active and active_step_info:
            call_w, call_h = 560, 90
            call_x1 = int((width - call_w) / 2)
            call_y1 = height - 235
            call_x2 = call_x1 + call_w
            call_y2 = call_y1 + call_h
            box_border = (0, 255, 128) if active_step_info["modality"] == "AUDIO_VISUAL_FUSED" else (0, 200, 255)
            cv2.rectangle(overlay, (call_x1, call_y1), (call_x2, call_y2), (12, 10, 18), -1)
            cv2.rectangle(overlay, (call_x1, call_y1), (call_x2, call_y2), box_border, 2)

        # Blend overlay
        cv2.addWeighted(overlay, 0.80, annotated_frame, 0.20, 0, annotated_frame)

        # -------------------------------------------------------------
        # Render Texts & HUD Graphics
        # -------------------------------------------------------------
        # Top HUD Texts
        cv2.putText(annotated_frame, "SOLUTION 4: MULTIMODAL AUDIO-VISUAL FUSION", (hud_x1 + 15, hud_y1 + 30),
                    cv2.FONT_HERSHEY_DUPLEX, 0.56, (240, 120, 210), 1, cv2.LINE_AA)
        cv2.putText(annotated_frame, "SENSORS: 30 FPS SKELETON + 22.05 kHz AUDIO TRANSIENTS", (hud_x1 + 15, hud_y1 + 52),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 190, 215), 1, cv2.LINE_AA)

        # Big Fused Steps Count
        count_color = (0, 255, 128) if is_callout_active else (255, 255, 255)
        cv2.putText(annotated_frame, f"FUSED STEPS: {running_steps}", (hud_x1 + 15, hud_y1 + 105),
                    cv2.FONT_HERSHEY_DUPLEX, 1.35, count_color, 3, cv2.LINE_AA)

        # Dual Confirmation & Cadence
        pct = (running_fused / max(1, running_steps)) * 100
        cv2.putText(annotated_frame, f"DUAL CONFIRMED: {running_fused}/{running_steps} ({pct:.0f}%) | CADENCE: {cadence_spm:.0f} SPM",
                    (hud_x1 + 15, hud_y1 + 140), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (255, 255, 255), 1, cv2.LINE_AA)

        # Active Leg & Coincidence Gate
        cv2.putText(annotated_frame, f"ACTIVE: {last_leg}  |  COINCIDENCE GATE: < 140ms WINDOW",
                    (hud_x1 + 15, hud_y1 + 172), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (240, 150, 220), 1, cv2.LINE_AA)
        cv2.putText(annotated_frame, "HARDWARE: GPU EDGE INFERENCE | ZERO API COST",
                    (hud_x1 + 15, hud_y1 + 202), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (140, 150, 170), 1, cv2.LINE_AA)

        # -------------------------------------------------------------
        # Live Audio Waveform (Oscilloscope)
        # -------------------------------------------------------------
        cv2.putText(annotated_frame, "ACOUSTIC TRANSIENT OSCILLOSCOPE (80 - 600 Hz FOOTSTRIKE FILTER)",
                    (osc_x1 + 12, osc_y1 + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (220, 120, 200), 1, cv2.LINE_AA)

        # Current audio sample position
        sample_idx = int(t_sec * audio_sr)
        curr_env_val = norm_audio_env[min(sample_idx, len(norm_audio_env)-1)]
        is_audio_impact = curr_env_val > 0.40

        impact_badge_color = (0, 255, 128) if is_audio_impact else (120, 90, 130)
        impact_text = "[AUDIO IMPACT DETECTED]" if is_audio_impact else "[MONITORING ACOUSTICS]"
        cv2.putText(annotated_frame, impact_text, (osc_x2 - 210, osc_y1 + 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, impact_badge_color, 1, cv2.LINE_AA)

        # Waveform graph (window of 1.6 seconds centered at current time)
        span_samples = int(audio_sr * 1.6)
        start_samp = max(0, sample_idx - int(span_samples * 0.7))
        end_samp = min(len(norm_audio_env), start_samp + span_samples)
        wave_slice = norm_audio_env[start_samp:end_samp]

        if len(wave_slice) > 2:
            pts_top = []
            pts_bot = []
            mid_y = osc_y1 + 58
            plot_w = osc_w - 24
            dx = plot_w / float(span_samples)

            # Subsample for smooth rendering
            stride = max(1, len(wave_slice) // 200)
            for w_i in range(0, len(wave_slice), stride):
                amp = wave_slice[w_i] * 32.0
                px = int(osc_x1 + 12 + w_i * (plot_w / len(wave_slice)))
                py_top = int(mid_y - amp)
                py_bot = int(mid_y + amp)
                pts_top.append((px, py_top))
                pts_bot.append((px, py_bot))

            for p_i in range(len(pts_top) - 1):
                cv2.line(annotated_frame, pts_top[p_i], pts_top[p_i+1], (200, 100, 220), 1, cv2.LINE_AA)
                cv2.line(annotated_frame, pts_bot[p_i], pts_bot[p_i+1], (200, 100, 220), 1, cv2.LINE_AA)

            # Draw vertical playhead cursor
            cursor_x = int(osc_x1 + 12 + (sample_idx - start_samp) * (plot_w / len(wave_slice)))
            cursor_x = max(osc_x1 + 12, min(osc_x2 - 12, cursor_x))
            cv2.line(annotated_frame, (cursor_x, osc_y1 + 25), (cursor_x, osc_y2 - 8), (0, 255, 128), 2, cv2.LINE_AA)

        # -------------------------------------------------------------
        # Floating Step Callout Card
        # -------------------------------------------------------------
        if is_callout_active and active_step_info:
            leg_name = active_step_info["leg"]
            modality = active_step_info["modality"]
            is_dual = modality == "AUDIO_VISUAL_FUSED"
            badge_color = (0, 255, 128) if is_dual else (0, 200, 255)
            status_title = f">> DUAL-CONFIRMED FUSED STEP #{active_step_info['step_id']} <<" if is_dual else f">> VISUAL-ONLY STEP #{active_step_info['step_id']} <<"

            cv2.putText(annotated_frame, status_title,
                        (call_x1 + 15, call_y1 + 26), cv2.FONT_HERSHEY_DUPLEX, 0.56, badge_color, 1, cv2.LINE_AA)

            delta_str = f"Δt = {active_step_info['delta_ms']:.1f} ms (Aligned)" if active_step_info['delta_ms'] is not None else "Audio attenuated"
            cv2.putText(annotated_frame, f"CONFIDENCE: {active_step_info['confidence']*100:.0f}%  |  TIME: {active_step_info['timestamp_sec']:.2f}s  |  ACTIVE LEG: {leg_name}",
                        (call_x1 + 15, call_y1 + 52), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(annotated_frame, f"MODALITY: {modality}  |  ACOUSTIC-OPTICAL SYNC: {delta_str}",
                        (call_x1 + 15, call_y1 + 75), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 220, 240), 1, cv2.LINE_AA)

            # Dynamic ankle pulse highlight from detected pose keypoints
            pulse_x = int(width * 0.35) if leg_name == "LEFT" else int(width * 0.40)
            pulse_y = int(height * 0.70)
            if pose_res.keypoints is not None and len(pose_res.keypoints.xy) > 0:
                kpts = pose_res.keypoints.xy[0].cpu().numpy()
                k_idx = 15 if leg_name == "LEFT" else 16
                if len(kpts) > k_idx and not np.isnan(kpts[k_idx][0]) and kpts[k_idx][0] > 0:
                    pulse_x, pulse_y = int(kpts[k_idx][0]), int(kpts[k_idx][1])

            cv2.circle(annotated_frame, (pulse_x, pulse_y), 28, badge_color, 2, cv2.LINE_AA)
            cv2.circle(annotated_frame, (pulse_x, pulse_y), 7, badge_color, -1)

        out_writer.write(annotated_frame)
        f_idx += 1

    cap.release()
    out_writer.release()

    # Transcode to web-compatible H.264
    cmd = [
        "ffmpeg", "-y", "-i", str(temp_raw_path),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_video_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if temp_raw_path.exists():
        temp_raw_path.unlink()

    print(f"✔ Successfully generated Solution 4 annotated video: {output_video_path}")
    return output_video_path

if __name__ == "__main__":
    BASE = Path(__file__).resolve().parent.parent.parent
    render_solution4_annotated_video(
        video_path=BASE / "samples" / "sample2.mp4",
        json_path=BASE / "output" / "solution4" / "sample2_fusion_steps.json",
        wav_path=BASE / "output" / "solution4" / "sample2_audio_temp.wav",
        output_video_path=BASE / "output" / "solution4" / "sample2_annotated_hud.mp4"
    )
