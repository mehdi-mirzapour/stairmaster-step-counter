import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from ultralytics import YOLO
from scipy.signal import find_peaks, savgol_filter

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")
model = YOLO(str(BASE / "yolov8n-pose.pt"))
cap = cv2.VideoCapture(str(BASE / "samples/sample1.mp4"))
fps = cap.get(cv2.CAP_PROP_FPS)

# Inspect first 20 seconds (600 frames)
timestamps, raw_la_y, raw_ra_y = [], [], []
for f in range(600):
    ret, frame = cap.read()
    if not ret:
        break
    timestamps.append(f / fps)
    res = model(frame, verbose=False)[0]
    if res.keypoints is not None and len(res.keypoints.xy) > 0:
        kpts = res.keypoints.xy[0].cpu().numpy()
        raw_la_y.append(kpts[15][1])
        raw_ra_y.append(kpts[16][1])

cap.release()

def clean(arr):
    s = np.array(arr, dtype=float)
    nans = np.isnan(s)
    if np.all(nans):
        return np.zeros_like(s)
    s[nans] = np.interp(np.flatnonzero(nans), np.flatnonzero(~nans), s[~nans])
    inv = -s
    return savgol_filter(inv, 15, 2)

la = clean(raw_la_y)
ra = clean(raw_ra_y)
t = np.array(timestamps)

# Plot both with detected peaks
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 8), sharex=True)

# Right leg (foreground)
# Notice in sample 1, right leg steps every ~1.63s (min_dist ~ 35 frames = 1.16s)
r_p, _ = find_peaks(ra, distance=35, prominence=15)
ax1.plot(t, ra, 'b-', label="Right Ankle (Foreground)")
ax1.plot(t[r_p], ra[r_p], 'ro', label=f"Right Peaks ({len(r_p)})")
for p in r_p:
    ax1.axvline(t[p], color='r', linestyle='--', alpha=0.3)
ax1.legend()
ax1.grid(True)
ax1.set_title("Right Ankle Signal & Peaks")

# Left leg (background)
l_p, _ = find_peaks(la, distance=35, prominence=15)
ax2.plot(t, la, 'm-', label="Left Ankle (Background)")
ax2.plot(t[l_p], la[l_p], 'go', label=f"Left Peaks ({len(l_p)})")
for p in l_p:
    ax2.axvline(t[p], color='g', linestyle='--', alpha=0.3)
ax2.legend()
ax2.grid(True)
ax2.set_title("Left Ankle Signal & Peaks")

plt.tight_layout()
plt.savefig(str(BASE / "output/sample1_leg_peaks_debug.png"), dpi=150)
print("Saved sample1_leg_peaks_debug.png")
print("Right peak times:", [round(float(t[p]), 2) for p in r_p])
print("Left peak times:", [round(float(t[p]), 2) for p in l_p])
