import cv2
import numpy as np
from pathlib import Path
from scipy.signal import find_peaks, savgol_filter
import json

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")
cap = cv2.VideoCapture(str(BASE / "samples" / "sample1.mp4"))
fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
limit_frames = int(60.0 * fps)

# Candidate Exit ROIs
# Let's test a few variations:
# 1: (0.14, 0.75, 0.24, 0.83)
# 2: (0.15, 0.74, 0.25, 0.82)
# 3: (0.13, 0.76, 0.23, 0.84)

test_configs = [
    {"name": "Exit_ROI_1", "roi": (0.14, 0.75, 0.24, 0.83)},
    {"name": "Exit_ROI_2", "roi": (0.15, 0.74, 0.25, 0.82)},
    {"name": "Exit_ROI_3", "roi": (0.13, 0.76, 0.23, 0.84)},
]

for cfg in test_configs:
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    x1, y1 = int(w * cfg["roi"][0]), int(h * cfg["roi"][1])
    x2, y2 = int(w * cfg["roi"][2]), int(h * cfg["roi"][3])
    
    signals = []
    f_idx = 0
    while cap.isOpened() and f_idx < limit_frames:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        crop = gray[y1:y2, x1:x2]
        signals.append(np.mean(crop))
        f_idx += 1

    sig = np.array(signals)
    # Smooth with Savitzky-Golay
    smoothed = savgol_filter(sig, window_length=9, polyorder=2)
    
    # Peak detection:
    # Machine revolving stairs in sample 1 have period around 1.1 - 1.2s (~34-36 frames)
    # distance = 20 frames (~0.66s), prominence = 3.0
    peaks, props = find_peaks(smoothed, distance=20, prominence=3.0)
    
    print(f"=== {cfg['name']} (ROI: {cfg['roi']}) ===")
    print(f"Total Frames: {len(sig)}")
    print(f"Total Revolving Tread Peaks: {len(peaks)}")
    if len(peaks) > 1:
        first_p = peaks[0] / fps
        last_p = peaks[-1] / fps
        dur = last_p - first_p
        cadence = (len(peaks) - 1) / (dur / 60.0)
        print(f"First Peak: {first_p:.2f}s | Last Peak: {last_p:.2f}s | Cadence: {cadence:.1f} Steps/Min")
    print(f"Mean Prominence: {np.mean(props['prominences']):.2f}")
    print()

cap.release()
