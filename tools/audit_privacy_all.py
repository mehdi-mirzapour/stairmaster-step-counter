import cv2
import glob
from pathlib import Path
from ultralytics import YOLO

base_dir = Path("/home/mehdi/volvo/stairmaster-step-counter")
model = YOLO(str(base_dir / "yolov8n-pose.pt"))

print("=== AUDITING ALL TRACKED / COMMITTED IMAGE FILES ===")
for p in sorted(glob.glob(str(base_dir / "**/*.jpg"), recursive=True)) + sorted(glob.glob(str(base_dir / "**/*.png"), recursive=True)):
    if "local" in p or ".venv" in p:
        continue
    rel = Path(p).relative_to(base_dir)
    img = cv2.imread(p)
    if img is None:
        continue
    res = model(img, verbose=False)[0]
    head_detected = False
    if res.keypoints is not None and len(res.keypoints.xy) > 0:
        kpts = res.keypoints.xy[0].cpu().numpy()
        head_pts = [pt for pt in kpts[0:5] if pt[0] > 0 and pt[1] > 0]
        if len(head_pts) > 0:
            head_detected = True
            print(f"⚠️  [POTENTIAL LEAK] {rel}: Detected {len(head_pts)} head keypoints! Y-coords: {[round(float(p[1]), 1) for p in head_pts]}")
    if not head_detected:
        print(f"✅ [SAFE] {rel}: No head keypoints detected ({img.shape})")

print("\n=== AUDITING ALL MP4 FILES ===")
for p in sorted(glob.glob(str(base_dir / "**/*.mp4"), recursive=True)):
    if "local" in p or ".venv" in p:
        continue
    rel = Path(p).relative_to(base_dir)
    cap = cv2.VideoCapture(p)
    f_count = 0
    head_frames = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        f_count += 1
        res = model(frame, verbose=False)[0]
        if res.keypoints is not None and len(res.keypoints.xy) > 0:
            kpts = res.keypoints.xy[0].cpu().numpy()
            head_pts = [pt for pt in kpts[0:5] if pt[0] > 0 and pt[1] > 0]
            if len(head_pts) > 0:
                head_frames += 1
    cap.release()
    print(f"MP4 {rel}: {f_count} frames, {head_frames} frames with detected head/face keypoints.")

print("\n=== AUDITING ALL GIF FILES ===")
for p in sorted(glob.glob(str(base_dir / "**/*.gif"), recursive=True)):
    if "local" in p or ".venv" in p:
        continue
    rel = Path(p).relative_to(base_dir)
    cap = cv2.VideoCapture(p)
    f_count = 0
    head_frames = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        f_count += 1
        res = model(frame, verbose=False)[0]
        if res.keypoints is not None and len(res.keypoints.xy) > 0:
            kpts = res.keypoints.xy[0].cpu().numpy()
            head_pts = [pt for pt in kpts[0:5] if pt[0] > 0 and pt[1] > 0]
            if len(head_pts) > 0:
                head_frames += 1
    cap.release()
    print(f"GIF {rel}: {f_count} frames, {head_frames} frames with detected head/face keypoints.")
