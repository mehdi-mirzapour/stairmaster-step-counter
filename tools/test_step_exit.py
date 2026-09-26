import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")
cap = cv2.VideoCapture(str(BASE / "samples" / "sample1.mp4"))
fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Let's test candidate ROIs around the bottom step exit:
# Candidate A: x: [0.14, 0.24], y: [0.76, 0.82]
# Candidate B: x: [0.15, 0.25], y: [0.75, 0.83]
# Candidate C: x: [0.16, 0.25], y: [0.76, 0.84]

rois = {
    "A (0.14, 0.76, 0.24, 0.82)": (int(0.14 * w), int(0.76 * h), int(0.24 * w), int(0.82 * h)),
    "B (0.15, 0.74, 0.25, 0.83)": (int(0.15 * w), int(0.74 * h), int(0.25 * w), int(0.83 * h)),
    "C (0.16, 0.76, 0.25, 0.84)": (int(0.16 * w), int(0.76 * h), int(0.25 * w), int(0.84 * h)),
}

frames_to_test = 600 # 20 seconds
signals = {name: [] for name in rois}

for f_idx in range(frames_to_test):
    ret, frame = cap.read()
    if not ret:
        break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    for name, (x1, y1, x2, y2) in rois.items():
        crop = gray[y1:y2, x1:x2]
        # Average brightness or Sobel vertical gradient
        val = np.mean(crop)
        signals[name].append(val)

cap.release()

# Plot the 3 signals
plt.figure(figsize=(12, 6))
time_axis = np.arange(len(signals["A (0.14, 0.76, 0.24, 0.82)"])) / fps
for name, sig in signals.items():
    plt.plot(time_axis, sig, label=name)

plt.xlabel("Time (seconds)")
plt.ylabel("Mean Pixel Intensity")
plt.title("Sample 1: Step Exit ROI Signal Comparison (First 20s)")
plt.legend()
plt.grid(True)
plt.savefig(str(BASE / "output" / "sample1_step_exit_signals.png"))
print("Signals plotted successfully.")
