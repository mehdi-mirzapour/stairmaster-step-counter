import cv2
import json
import numpy as np
from pathlib import Path
from ultralytics import YOLO
from scipy.signal import find_peaks, savgol_filter

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")
model = YOLO(str(BASE / "yolov8n-pose.pt"))
cap = cv2.VideoCapture(str(BASE / "samples/sample1.mp4"))
fps = cap.get(cv2.CAP_PROP_FPS)

limit_frames = int(fps * 60)
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
    inv = -s
    # Smooth with ~0.6s window
    w = 19
    return savgol_filter(inv, w, 2)

la_smooth = clean(raw_la_y)
ra_smooth = clean(raw_ra_y)

# Since each leg steps once every ~3.5 seconds (alternate legs every 1.75s):
# Min distance for same leg is ~2.2s (66 frames)
for dist in [60, 65, 70, 75]:
    for prom in [15, 20, 25]:
        lp, _ = find_peaks(la_smooth, distance=dist, prominence=prom)
        rp, _ = find_peaks(ra_smooth, distance=dist, prominence=prom)
        print(f"dist={dist} (frames), prom={prom} -> L: {len(lp)}, R: {len(rp)}, Total: {len(lp)+len(rp)}")
