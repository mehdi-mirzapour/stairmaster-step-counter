import cv2
import numpy as np
from pathlib import Path

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")
cap = cv2.VideoCapture(str(BASE / "samples" / "sample1.mp4"))
fps = 30.0
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

x1, y1 = int(w * 0.14), int(h * 0.75)
x2, y2 = int(w * 0.24), int(h * 0.83)

# Let's save crops from frame 160 (5.33s) to frame 220 (7.33s) every 5 frames
crops = []
for f in range(160, 221, 5):
    cap.set(cv2.CAP_PROP_POS_FRAMES, f)
    ret, frame = cap.read()
    if ret:
        cr = frame[y1:y2, x1:x2].copy()
        # Draw frame number and time
        cv2.putText(cr, f"f={f} ({f/fps:.2f}s)", (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        crops.append(cr)

cap.release()

# Stack 2 rows of 6
row1 = np.hstack(crops[:6])
row2 = np.hstack(crops[6:12])
sheet = np.vstack([row1, row2])
cv2.imwrite(str(BASE / "output" / "sample1_exit_tread_frames.jpg"), sheet)
print("Saved exit tread frames.")
