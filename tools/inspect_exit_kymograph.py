import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.signal import find_peaks, savgol_filter

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")
cap = cv2.VideoCapture(str(BASE / "samples" / "sample1.mp4"))
fps = 30.0
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# ROI at the exit step: (0.14, 0.75, 0.24, 0.83)
x1, y1 = int(w * 0.14), int(h * 0.75)
x2, y2 = int(w * 0.24), int(h * 0.83)

kymo = []
signals = []
for f_idx in range(900): # 30 seconds
    ret, frame = cap.read()
    if not ret:
        break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    crop = gray[y1:y2, x1:x2]
    kymo.append(crop.mean(axis=1))
    signals.append(np.mean(crop))

cap.release()

kymo_arr = np.array(kymo).T # shape: (height_px, time_frames)
sig = savgol_filter(np.array(signals), 9, 2)
peaks, props = find_peaks(sig, distance=20, prominence=3.0)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
ax1.imshow(kymo_arr, aspect='auto', cmap='magma', extent=[0, 30, kymo_arr.shape[0], 0])
ax1.set_title("Spatio-Temporal Kymograph at Step Exit ROI (Sample 1)")
ax1.set_ylabel("Vertical Position (px)")

ax2.plot(np.arange(len(sig)) / fps, sig, color='cyan', label="Tread Exit Luminance")
ax2.plot(peaks / fps, sig[peaks], 'ro', label=f"Detected Treads ({len(peaks)} in 30s)")
ax2.set_xlabel("Time (seconds)")
ax2.set_ylabel("Intensity")
ax2.legend()
ax2.grid(True)

plt.tight_layout()
plt.savefig(str(BASE / "output" / "sample1_exit_kymograph.png"))
print(f"Detected {len(peaks)} peaks in first 30s: {peaks/fps}")
