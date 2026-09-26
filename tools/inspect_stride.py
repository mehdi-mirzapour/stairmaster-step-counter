import cv2
import numpy as np
from pathlib import Path

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")
cap = cv2.VideoCapture(str(BASE / "samples" / "sample1.mp4"))
fps = 30.0

# Extract 6 frames between 5.0s (frame 150) and 7.0s (frame 210)
# Step interval was 5.43s to 7.23s (one machine tread cycle)
frames = []
for t in [5.4, 5.7, 6.0, 6.3, 6.6, 6.9, 7.2]:
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
    ret, frame = cap.read()
    if ret:
        # Resize for inspection
        small = cv2.resize(frame, (360, 640))
        cv2.putText(small, f"t={t:.2f}s", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
        frames.append(small)

cap.release()

grid = np.hstack(frames[:4])
grid2 = np.hstack(frames[4:])
# Combine vertically
canvas = np.vstack([
    np.hstack([frames[0], frames[1], frames[2]]),
    np.hstack([frames[3], frames[4], frames[5]])
])
cv2.imwrite(str(BASE / "output" / "sample1_stride_inspection.jpg"), canvas)
print("Stride inspection saved.")
