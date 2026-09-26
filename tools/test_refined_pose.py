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
    w = 19
    return savgol_filter(inv, w, 2)

la_smooth = clean(raw_la_y)
ra_smooth = clean(raw_ra_y)

# Let's inspect peak timestamps for prom=22, dist=58
lp, _ = find_peaks(la_smooth, distance=58, prominence=20)
rp, _ = find_peaks(ra_smooth, distance=58, prominence=20)

all_steps = []
for p in lp:
    all_steps.append({"frame": int(p), "timestamp_sec": round(float(timestamps[p]), 3), "leg": "left"})
for p in rp:
    all_steps.append({"frame": int(p), "timestamp_sec": round(float(timestamps[p]), 3), "leg": "right"})

all_steps.sort(key=lambda x: x["timestamp_sec"])

# Alternating filter: if two consecutive steps are same leg within < 2.0s, take the stronger peak
cleaned_steps = []
for s in all_steps:
    if not cleaned_steps:
        cleaned_steps.append(s)
    else:
        dt = s["timestamp_sec"] - cleaned_steps[-1]["timestamp_sec"]
        if dt < 0.9:  # Cannot take steps < 0.9s apart at 34 SPM
            continue
        cleaned_steps.append(s)

print(f"Total Cleaned Steps: {len(cleaned_steps)}")
l_c = sum(1 for s in cleaned_steps if s['leg'] == 'left')
r_c = sum(1 for s in cleaned_steps if s['leg'] == 'right')
print(f"Left: {l_c}, Right: {r_c}")
for i, s in enumerate(cleaned_steps[:15]):
    print(f"#{i+1:2d} | {s['timestamp_sec']:5.2f}s | {s['leg']:5s}")
