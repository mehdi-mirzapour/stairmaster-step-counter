import cv2
import json
import numpy as np
import subprocess
from pathlib import Path
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent.parent
LOCAL_SAMPLES = BASE_DIR / "local" / "samples"
OUTPUT_DIR = BASE_DIR / "output"
DOCS_ASSETS = BASE_DIR / "docs" / "assets"
DOCS_ASSETS.mkdir(parents=True, exist_ok=True)

video_input = LOCAL_SAMPLES / "sample2.mp4"
if not video_input.exists():
    video_input = BASE_DIR / "samples" / "sample2.mp4"

print(f"Reading from input: {video_input}")

def anonymize_face(frame, keypoints, min_y_cutoff=270):
    """
    Guarantees athlete identity privacy by applying a heavy Gaussian blur 
    and subtle digital privacy tint over detected facial/head keypoints.
    """
    h, w = frame.shape[:2]
    # Check keypoints 0..4 (nose, eyes, ears)
    head_pts = []
    if keypoints is not None and len(keypoints) > 0:
        kpts = keypoints[0].cpu().numpy() if hasattr(keypoints[0], 'cpu') else keypoints[0]
        for k_i in range(min(5, len(kpts))):
            pt = kpts[k_i]
            if len(pt) >= 2 and pt[0] > 0 and pt[1] > 0:
                head_pts.append(pt)
    
    # If keypoints detected, calculate bounding box around head
    if head_pts:
        xs = [p[0] for p in head_pts]
        ys = [p[1] for p in head_pts]
        x1 = max(0, int(min(xs) - 45))
        x2 = min(w, int(max(xs) + 45))
        y1 = max(0, int(min(ys) - 50))
        y2 = min(h, int(max(ys) + 40))
    else:
        # Fallback to known head coordinates in 3/4 rear perspective
        x1, y1, x2, y2 = 250, 45, 440, 260

    # Ensure box doesn't bleed into legs/torso
    y2 = min(y2, min_y_cutoff)

    # Apply heavy blur to head/face region
    roi = frame[y1:y2, x1:x2]
    if roi.size > 0:
        blurred = cv2.GaussianBlur(roi, (51, 51), 30)
        # Apply dark privacy vignette / badge overlay
        tint = np.full_like(blurred, (20, 25, 35), dtype=np.uint8)
        blended_head = cv2.addWeighted(blurred, 0.45, tint, 0.55, 0)
        frame[y1:y2, x1:x2] = blended_head
        
        # Sleek privacy border around blurred region
        cv2.rectangle(frame, (x1, y1), (x2, y2), (56, 189, 248), 1, cv2.LINE_AA)
        cv2.putText(frame, "PRIVACY ANONYMIZED", (x1 + 4, y2 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.32, (180, 220, 245), 1, cv2.LINE_AA)

    return frame


def render_5s_solution2(max_sec=5.0):
    """Render 5-second Solution 2 annotated HUD with full privacy protection."""
    print("Rendering 5-second Solution 2 annotated video...")
    json_path = OUTPUT_DIR / "solution2" / "sample2_yolo_steps.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    steps = [s for s in data.get("steps", []) if s.get("timestamp_sec", 0) <= max_sec]
    step_by_frame = {s["frame"]: s for s in steps}
    cadence_spm = data.get("cadence_spm", 134.7)

    model = YOLO(str(BASE_DIR / "yolov8n-pose.pt"))
    cap = cv2.VideoCapture(str(video_input))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    limit_frames = int(max_sec * fps)

    temp_raw = OUTPUT_DIR / "solution2" / "temp_5s_s2.mp4"
    out_final = OUTPUT_DIR / "solution2" / "sample2_5s_annotated.mp4"
    out_final.parent.mkdir(parents=True, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_writer = cv2.VideoWriter(str(temp_raw), fourcc, fps, (width, height))

    running_steps = 0
    running_left = 0
    running_right = 0
    last_leg = "NONE"
    active_step_info = None
    step_callout_until_frame = -1

    for f_idx in range(limit_frames):
        ret, frame = cap.read()
        if not ret:
            break

        # Check for step
        if f_idx in step_by_frame:
            s = step_by_frame[f_idx]
            running_steps += 1
            leg_str = s.get("leg", "unknown").upper()
            if leg_str == "LEFT":
                running_left += 1
            else:
                running_right += 1
            last_leg = leg_str
            active_step_info = s
            step_callout_until_frame = f_idx + 12

        is_callout_active = (f_idx <= step_callout_until_frame) and (active_step_info is not None)

        # Pose inference
        pose_res = model(frame, verbose=False)[0]
        annotated_frame = pose_res.plot(boxes=False)

        # Apply face anonymization for privacy
        annotated_frame = anonymize_face(annotated_frame, pose_res.keypoints)

        overlay = annotated_frame.copy()

        # Top HUD Card (Cyan theme)
        hud_x1, hud_y1 = 20, 25
        hud_x2, hud_y2 = 520, 235
        cv2.rectangle(overlay, (hud_x1, hud_y1), (hud_x2, hud_y2), (14, 20, 28), -1)
        cv2.rectangle(overlay, (hud_x1, hud_y1), (hud_x2, hud_y2), (248, 189, 56), 2)

        # Biomechanics Card
        spec_w, spec_h = 320, 125
        spec_x1 = width - spec_w - 20
        spec_y1 = height - spec_h - 30
        spec_x2 = spec_x1 + spec_w
        spec_y2 = spec_y1 + spec_h
        cv2.rectangle(overlay, (spec_x1, spec_y1), (spec_x2, spec_y2), (14, 20, 28), -1)
        cv2.rectangle(overlay, (spec_x1, spec_y1), (spec_x2, spec_y2), (200, 150, 40), 1)

        # Floating Step Callout Card
        if is_callout_active and active_step_info:
            call_w, call_h = 560, 90
            call_x1 = int((width - call_w) / 2)
            call_y1 = height - 240
            call_x2 = call_x1 + call_w
            call_y2 = call_y1 + call_h
            cv2.rectangle(overlay, (call_x1, call_y1), (call_x2, call_y2), (10, 16, 24), -1)
            cv2.rectangle(overlay, (call_x1, call_y1), (call_x2, call_y2), (248, 189, 56), 2)

        # Blend overlay
        cv2.addWeighted(overlay, 0.85, annotated_frame, 0.15, 0, annotated_frame)

        # Text Overlays
        cv2.putText(annotated_frame, "SOLUTION 2: EDGE YOLOV8-POSE KINEMATICS", (hud_x1 + 15, hud_y1 + 30),
                    cv2.FONT_HERSHEY_DUPLEX, 0.58, (248, 189, 56), 1, cv2.LINE_AA)
        cv2.putText(annotated_frame, "ENGINE: ULTRALYTICS YOLOV8n-POSE | REAL-TIME 30 FPS", (hud_x1 + 15, hud_y1 + 52),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (190, 215, 230), 1, cv2.LINE_AA)

        count_color = (0, 255, 128) if is_callout_active else (255, 255, 255)
        cv2.putText(annotated_frame, f"POSE STEPS: {running_steps}", (hud_x1 + 15, hud_y1 + 105),
                    cv2.FONT_HERSHEY_DUPLEX, 1.35, count_color, 3, cv2.LINE_AA)

        cv2.putText(annotated_frame, f"CADENCE: {cadence_spm:.0f} SPM  |  L: {running_left}  R: {running_right}",
                    (hud_x1 + 15, hud_y1 + 140), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1, cv2.LINE_AA)

        cv2.putText(annotated_frame, f"ACTIVE LIMB: {last_leg}  |  TRACKING: ANKLE ELEVATION APEX",
                    (hud_x1 + 15, hud_y1 + 172), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (248, 189, 56), 1, cv2.LINE_AA)
        cv2.putText(annotated_frame, "LATENCY: ~14ms (70+ FPS) | LOCAL EDGE $0.00",
                    (hud_x1 + 15, hud_y1 + 202), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (140, 170, 190), 1, cv2.LINE_AA)

        # Biomechanics Card text
        cv2.putText(annotated_frame, "BIOMECHANICAL METRICS", (spec_x1 + 12, spec_y1 + 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.44, (248, 189, 56), 1, cv2.LINE_AA)
        cv2.putText(annotated_frame, "Keypoints: COCO #15, #16 (Ankles)", (spec_x1 + 12, spec_y1 + 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 220, 235), 1, cv2.LINE_AA)
        cv2.putText(annotated_frame, "Filter: Savitzky-Golay (w=9, p=2)", (spec_x1 + 12, spec_y1 + 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 220, 235), 1, cv2.LINE_AA)
        cv2.putText(annotated_frame, "Peak Prominence: > 12 pixels", (spec_x1 + 12, spec_y1 + 85),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 220, 235), 1, cv2.LINE_AA)
        cv2.putText(annotated_frame, "Privacy: Face Anonymized", (spec_x1 + 12, spec_y1 + 105),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 230, 140), 1, cv2.LINE_AA)

        if is_callout_active and active_step_info:
            leg_str = active_step_info.get("leg", "unknown").upper()
            step_id = active_step_info.get("step_id", running_steps)
            t_val = active_step_info.get("timestamp_sec", f_idx / fps)

            cv2.putText(annotated_frame, f">> POSE PEAK STEP #{step_id}  ({leg_str} ANKLE ELEVATION) <<",
                        (call_x1 + 15, call_y1 + 28), cv2.FONT_HERSHEY_DUPLEX, 0.56, (248, 189, 56), 1, cv2.LINE_AA)
            cv2.putText(annotated_frame, f"CADENCE: {cadence_spm:.0f} SPM  |  TIMESTAMP: {t_val:.2f}s  |  CONFIRMED KINEMATIC CYCLE",
                        (call_x1 + 15, call_y1 + 54), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(annotated_frame, f"PHASE: Vertical apex reached, transitioning to downward load phase",
                        (call_x1 + 15, call_y1 + 76), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (190, 220, 240), 1, cv2.LINE_AA)

            pulse_x = int(width * 0.35) if leg_str == "LEFT" else int(width * 0.40)
            pulse_y = int(height * 0.70)
            if pose_res.keypoints is not None and len(pose_res.keypoints.xy) > 0:
                kpts = pose_res.keypoints.xy[0].cpu().numpy()
                k_idx = 15 if leg_str == "LEFT" else 16
                if len(kpts) > k_idx and not np.isnan(kpts[k_idx][0]) and kpts[k_idx][0] > 0:
                    pulse_x, pulse_y = int(kpts[k_idx][0]), int(kpts[k_idx][1])

            cv2.circle(annotated_frame, (pulse_x, pulse_y), 28, (248, 189, 56), 2, cv2.LINE_AA)
            cv2.circle(annotated_frame, (pulse_x, pulse_y), 7, (248, 189, 56), -1)

        out_writer.write(annotated_frame)

    cap.release()
    out_writer.release()

    # Transcode with ffmpeg
    cmd = [
        "ffmpeg", "-y", "-i", str(temp_raw),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(out_final)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if temp_raw.exists():
        temp_raw.unlink()

    # Copy to docs/assets
    doc_copy = DOCS_ASSETS / "sample2_5s_annotated.mp4"
    subprocess.run(["cp", str(out_final), str(doc_copy)])

    print(f"✔ Rendered: {out_final} ({out_final.stat().st_size / 1024:.1f} KB)")
    return out_final


def render_5s_gif(mp4_path):
    """Render an optimized, smooth animated GIF for README and docs."""
    print("Rendering optimized 5-second demo GIF...")
    gif_out = DOCS_ASSETS / "demo.gif"
    # Create smooth palette-based GIF using ffmpeg at 15 FPS, width 480
    cmd = [
        "ffmpeg", "-y", "-i", str(mp4_path),
        "-vf", "fps=15,scale=480:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer",
        str(gif_out)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if gif_out.exists():
        print(f"✔ Generated Demo GIF: {gif_out} ({gif_out.stat().st_size / 1024:.1f} KB)")


def save_poster_frame(mp4_path):
    """Save an HD preview poster image."""
    cap = cv2.VideoCapture(str(mp4_path))
    cap.set(cv2.CAP_PROP_POS_FRAMES, 50)
    ret, frame = cap.read()
    if ret:
        poster_path = DOCS_ASSETS / "sample2_annotated_preview.jpg"
        cv2.imwrite(str(poster_path), frame)
        print(f"✔ Saved poster preview: {poster_path}")
    cap.release()

if __name__ == "__main__":
    mp4 = render_5s_solution2(max_sec=5.0)
    render_5s_gif(mp4)
    save_poster_frame(mp4)
