import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO
from scipy.signal import find_peaks, savgol_filter

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")
model = YOLO(str(BASE / "yolov8n-pose.pt"))
cap = cv2.VideoCapture(str(BASE / "samples/sample1.mp4"))
fps = cap.get(cv2.CAP_PROP_FPS)

limit_frames = int(fps * 60) # 60 seconds
timestamps = []
raw_la_y, raw_ra_y = [], []

for f in range(limit_frames):
    ret, frame = cap.read()
    if not ret:
        break
    timestamps.append(f / fps)
    res = model(frame, verbose=False)[0]
    if res.keypoints is not None and len(res.keypoints.xy) > 0:
        kpts = res.keypoints.xy[0].cpu().numpy()
        raw_la_y.append(kpts[15][1] if len(kpts) > 15 else np.nan)
        raw_ra_y.append(kpts[16][1] if len(kpts) > 16 else np.nan)
    else:
        raw_la_y.append(np.nan)
        raw_ra_y.append(np.nan)

cap.release()

def clean(arr):
    s = np.array(arr, dtype=float)
    nans = np.isnan(s)
    if np.all(nans):
        return np.zeros_like(s)
    s[nans] = np.interp(np.flatnonzero(nans), np.flatnonzero(~nans), s[~nans])
    inv = -s # Invert Y so up is positive
    # Use wider window for smoother signal (approx 0.5s = 15 frames)
    w = 17
    return savgol_filter(inv, w, 2)

la_smooth = clean(raw_la_y)
ra_smooth = clean(raw_ra_y)

# For each leg, a step happens every ~1.6s to 1.8s (i.e. ~48-54 frames)
# Minimum distance between same-leg steps is at least 1.0s (30 frames)
for p_prom in [15, 20, 25, 30]:
    for dist in [28, 32, 36]:
        l_peaks, _ = find_peaks(la_smooth, distance=dist, prominence=p_prom)
        r_peaks, _ = find_peaks(ra_smooth, distance=dist, prominence=p_prom)
        print(f"prom={p_prom:2d}, dist={dist:2d} -> Left: {len(l_peaks):2d}, Right: {len(r_peaks):2d}, Total: {len(l_peaks)+len(r_peaks):2d}")
