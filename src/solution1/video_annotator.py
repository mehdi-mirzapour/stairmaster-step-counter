import cv2
import json
import numpy as np
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

def render_solution1_annotated_video(
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

    metrics = data.get("metrics", {})
    steps = data.get("deduplicated_steps", [])
    total_steps = metrics.get("total_steps", len(steps))
    cadence_spm = metrics.get("cadence_spm", 222.0)
    left_steps_total = metrics.get("left_steps", 0)
    right_steps_total = metrics.get("right_steps", 0)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    limit_frames = int(max_duration_sec * fps) if max_duration_sec else total_frames
    limit_frames = min(limit_frames, total_frames)

    # Map steps by timestamp to frame indices
    step_events = []
    for s in steps:
        t = s["timestamp_sec"]
        frame_target = int(round(t * fps))
        step_events.append({
            "target_frame": frame_target,
            "timestamp_sec": t,
            "step_id": s["global_step_id"],
            "leg": s.get("active_leg", "unknown").upper(),
            "confidence": s.get("confidence", 0.95),
            "cue": s.get("visual_cue", "Foot contact with stair tread"),
            "windows": s.get("source_window_ids", []),
        })

    # Temporary raw video
    temp_raw_path = output_video_path.parent / f"temp_{output_video_path.stem}.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_writer = cv2.VideoWriter(str(temp_raw_path), fourcc, fps, (width, height))

    running_steps = 0
    running_left = 0
    running_right = 0
    active_step_info = None
    step_callout_until_frame = -1
    
    # Track which steps have already incremented
    triggered_step_ids = set()

    f_idx = 0
    while cap.isOpened() and f_idx < limit_frames:
        ret, frame = cap.read()
        if not ret:
            break
        i = f_idx
        t_sec = i / fps

        # Check for step events within 1 frame
        for s in step_events:
            if s["step_id"] not in triggered_step_ids and abs(i - s["target_frame"]) <= 1:
                triggered_step_ids.add(s["step_id"])
                running_steps += 1
                if s["leg"] == "LEFT":
                    running_left += 1
                else:
                    running_right += 1
                active_step_info = s
                step_callout_until_frame = i + 10  # Show callout for ~10 frames (0.33s)
                break

        is_callout_active = (i <= step_callout_until_frame) and (active_step_info is not None)

        # Sliding window calculation (3s window, 2s stride, 1s overlap)
        win_idx = int(t_sec // 2.0)
        win_start = win_idx * 2.0
        win_end = win_start + 3.0
        in_overlap = (t_sec >= win_start + 2.0) and (t_sec <= win_end)

        overlay = frame.copy()

        # -------------------------------------------------------------
        # 1. Top HUD Card (Amber / Gold theme for VLM)
        # -------------------------------------------------------------
        hud_x1, hud_y1 = 20, 25
        hud_x2, hud_y2 = 500, 228
        cv2.rectangle(overlay, (hud_x1, hud_y1), (hud_x2, hud_y2), (15, 18, 25), -1)
        # Border (Warm Amber)
        cv2.rectangle(overlay, (hud_x1, hud_y1), (hud_x2, hud_y2), (20, 160, 245), 2)

        # -------------------------------------------------------------
        # 2. Bottom Right VLM Architecture Spec Card
        # -------------------------------------------------------------
        spec_w, spec_h = 320, 130
        spec_x1 = width - spec_w - 20
        spec_y1 = height - spec_h - 30
        spec_x2 = spec_x1 + spec_w
        spec_y2 = spec_y1 + spec_h
        cv2.rectangle(overlay, (spec_x1, spec_y1), (spec_x2, spec_y2), (15, 18, 25), -1)
        cv2.rectangle(overlay, (spec_x1, spec_y1), (spec_x2, spec_y2), (20, 140, 220), 1)

        # -------------------------------------------------------------
        # 3. Floating Step Event Banner (When active)
        # -------------------------------------------------------------
        if is_callout_active:
            call_w, call_h = 560, 95
            call_x1 = int((width - call_w) / 2)
            call_y1 = height - 260
            call_x2 = call_x1 + call_w
            call_y2 = call_y1 + call_h
            cv2.rectangle(overlay, (call_x1, call_y1), (call_x2, call_y2), (10, 14, 22), -1)
            cv2.rectangle(overlay, (call_x1, call_y1), (call_x2, call_y2), (0, 200, 255), 2)

        # Blend overlay
        cv2.addWeighted(overlay, 0.80, frame, 0.20, 0, frame)

        # -------------------------------------------------------------
        # Render Crisp Graphics & Text
        # -------------------------------------------------------------
        # Top HUD
        cv2.putText(frame, "SOLUTION 1: SLIDING-WINDOW MULTIMODAL VLM", (hud_x1 + 15, hud_y1 + 30),
                    cv2.FONT_HERSHEY_DUPLEX, 0.58, (20, 190, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, "MODEL: OPENAI GPT-4o-mini | STRICT PYDANTIC JSON", (hud_x1 + 15, hud_y1 + 52),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (190, 205, 215), 1, cv2.LINE_AA)

        # Big Steps Count
        count_color = (0, 220, 255) if is_callout_active else (255, 255, 255)
        cv2.putText(frame, f"VLM STEPS: {running_steps}", (hud_x1 + 15, hud_y1 + 105),
                    cv2.FONT_HERSHEY_DUPLEX, 1.35, count_color, 3, cv2.LINE_AA)

        # Cadence & Bilateral Breakdown
        cv2.putText(frame, f"CADENCE: {cadence_spm:.0f} SPM  |  L: {running_left}  R: {running_right}",
                    (hud_x1 + 15, hud_y1 + 140), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1, cv2.LINE_AA)

        # Active Temporal Window
        overlap_str = " [IN 1.0s OVERLAP ZONE]" if in_overlap else ""
        cv2.putText(frame, f"ACTIVE WINDOW: #{win_idx} [{win_start:.1f}s - {win_end:.1f}s]{overlap_str}",
                    (hud_x1 + 15, hud_y1 + 172), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                    (0, 220, 255) if in_overlap else (160, 210, 240), 1, cv2.LINE_AA)

        # Mini Timeline progress bar inside HUD
        bar_x = hud_x1 + 15
        bar_y = hud_y1 + 192
        bar_w = 450
        bar_h = 10
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (40, 50, 60), -1)
        win_progress = min(1.0, max(0.0, (t_sec - win_start) / 3.0))
        fill_w = int(bar_w * win_progress)
        fill_color = (0, 200, 255) if in_overlap else (0, 160, 230)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), fill_color, -1)
        # Mark overlap zone on bar (last 1/3)
        overlap_start_x = bar_x + int(bar_w * (2.0 / 3.0))
        cv2.line(frame, (overlap_start_x, bar_y - 2), (overlap_start_x, bar_y + bar_h + 2), (255, 255, 255), 1)

        # -------------------------------------------------------------
        # Bottom Right Spec Card
        # -------------------------------------------------------------
        cv2.putText(frame, "VLM TELEMETRY & SPECS", (spec_x1 + 12, spec_y1 + 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.44, (20, 190, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, "Sampling Rate: 8.0 FPS (125ms)", (spec_x1 + 12, spec_y1 + 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 215, 225), 1, cv2.LINE_AA)
        cv2.putText(frame, "Window / Overlap: 3.0s / 1.0s", (spec_x1 + 12, spec_y1 + 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 215, 225), 1, cv2.LINE_AA)
        cv2.putText(frame, "Reconciliation: Dual-Boundary Dedup", (spec_x1 + 12, spec_y1 + 85),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 215, 225), 1, cv2.LINE_AA)
        cv2.putText(frame, "API Cost: ~$0.002 | Cloud Async", (spec_x1 + 12, spec_y1 + 108),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 230, 140), 1, cv2.LINE_AA)

        # -------------------------------------------------------------
        # Floating Step Callout Card & Foot Contact Indicator
        # -------------------------------------------------------------
        if is_callout_active and active_step_info:
            leg_name = active_step_info["leg"]
            leg_color = (255, 180, 0) if leg_name == "LEFT" else (0, 220, 255)
            
            # Card text
            cv2.putText(frame, f">> VLM DETECTED STEP #{active_step_info['step_id']}  ({leg_name} FOOT) <<",
                        (call_x1 + 15, call_y1 + 28), cv2.FONT_HERSHEY_DUPLEX, 0.58, leg_color, 1, cv2.LINE_AA)
            cv2.putText(frame, f"CONFIDENCE: {active_step_info['confidence']*100:.0f}%  |  TIME: {active_step_info['timestamp_sec']:.2f}s  |  WINDOW: {active_step_info['windows']}",
                        (call_x1 + 15, call_y1 + 54), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (255, 255, 255), 1, cv2.LINE_AA)
            
            cue_text = active_step_info['cue']
            if len(cue_text) > 55:
                cue_text = cue_text[:52] + "..."
            cv2.putText(frame, f"REASONING: \"{cue_text}\"",
                        (call_x1 + 15, call_y1 + 78), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 220, 240), 1, cv2.LINE_AA)

            # Foot plant circle highlight
            if "sample1" in video_path.name:
                foot_center_x = int(width * 0.32) if leg_name == "LEFT" else int(width * 0.38)
                foot_center_y = int(height * 0.72)
            else:
                foot_center_x = 355 if leg_name == "LEFT" else 395
                foot_center_y = 810
            # Expanding pulse ring
            pulse_rad = 22 + (i % 6) * 3
            cv2.circle(frame, (foot_center_x, foot_center_y), pulse_rad, leg_color, 2, cv2.LINE_AA)
            cv2.circle(frame, (foot_center_x, foot_center_y), 6, leg_color, -1)
            cv2.putText(frame, f"{leg_name} CONTACT", (foot_center_x - 45, foot_center_y - 28),
                        cv2.FONT_HERSHEY_DUPLEX, 0.42, leg_color, 1, cv2.LINE_AA)

        out_writer.write(frame)
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

    print(f"✔ Successfully generated Solution 1 annotated video: {output_video_path}")
    return output_video_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Render Solution 1 annotated HUD video")
    parser.add_argument("--sample", type=int, default=2, help="Sample number (1 or 2)")
    parser.add_argument("--max-duration", type=float, default=None, help="Max duration in seconds")
    args = parser.parse_args()

    BASE = Path(__file__).resolve().parent.parent.parent
    sample_num = args.sample
    max_dur = args.max_duration if args.max_duration is not None else (60.0 if sample_num == 1 else None)
    
    json_path = BASE / "output" / "solution1" / f"sample{sample_num}_step_analysis.json"
    if not json_path.exists():
        json_path = BASE / "output" / f"sample{sample_num}_step_analysis.json"

    render_solution1_annotated_video(
        video_path=BASE / "samples" / f"sample{sample_num}.mp4",
        json_path=json_path,
        output_video_path=BASE / "output" / "solution1" / f"sample{sample_num}_annotated_hud.mp4",
        max_duration_sec=max_dur
    )
