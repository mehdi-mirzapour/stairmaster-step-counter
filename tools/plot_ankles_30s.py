import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from ultralytics import YOLO

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")
model = YOLO(str(BASE / "yolov8n-pose.pt"))
cap = cv2.VideoCapture(str(BASE / "samples/sample1.mp4"))
fps = cap.get(cv2.CAP_PROP_FPS)

# Inspect 30 seconds (900 frames)
frames_to_read = int(fps * 30)
timestamps = []
la_y, ra_y = [], []
la_x, ra_x = [], []

for f in range(frames_to_read):
    ret, frame = cap.read()
    if not ret:
        break
    timestamps.append(f / fps)
    res = model(frame, verbose=False)[0]
    if res.keypoints is not None and len(res.keypoints.xy) > 0:
        kpts = res.keypoints.xy[0].cpu().numpy()
        la_y.append(kpts[15][1])
        ra_y.append(kpts[16][1])
        la_x.append(kpts[15][0])
        ra_x.append(kpts[16][0])
    else:
        la_y.append(np.nan)
        ra_y.append(np.nan)
        la_x.append(np.nan)
        ra_x.append(np.nan)

cap.release()

# Plot ankle Y trajectories
plt.figure(figsize=(16, 6))
# Invert Y so up is higher
t = np.array(timestamps)
plt.plot(t, -np.array(ra_y), 'b-', label="Right Ankle (Inverted Y - Up is Higher)", lw=1.5)
plt.plot(t, -np.array(la_y), 'm-', label="Left Ankle (Inverted Y - Up is Higher)", lw=1.5, alpha=0.7)
plt.title("Sample 1: Ankle Trajectory over First 30s")
plt.xlabel("Time (s)")
plt.ylabel("Vertical Position (Inverted pixels)")
plt.legend()
plt.grid(True)
plt.savefig(str(BASE / "output/sample1_ankle_trajectory_30s.png"), dpi=150)
print("Saved sample1_ankle_trajectory_30s.png")
