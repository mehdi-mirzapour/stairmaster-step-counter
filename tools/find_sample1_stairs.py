import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import cv2
import numpy as np

cap = cv2.VideoCapture(str(BASE_DIR / 'samples' / 'sample1.mp4'))
fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

# Read 300 frames between t=10s and t=20s (frames 300 to 600)
cap.set(cv2.CAP_PROP_POS_FRAMES, 300)
diff_accum = None
prev_gray = None

for _ in range(150):
    ret, frame = cap.read()
    if not ret:
        break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if prev_gray is not None:
        diff = cv2.absdiff(gray, prev_gray)
        if diff_accum is None:
            diff_accum = np.zeros_like(diff, dtype=np.float32)
        diff_accum += diff
    prev_gray = gray

cap.release()

# Find motion energy in the bottom half (below y = 1000)
h, w = diff_accum.shape
# Normalize
motion_map = (diff_accum / diff_accum.max() * 255).astype(np.uint8)
cv2.imwrite(str(BASE_DIR / 'samples' / 'sample1_motion.jpg'), motion_map)
print('Motion map saved! Height:', h, 'Width:', w)

# Find coordinates where motion is high below waist (y > 1000)
lower_motion = motion_map[1100:1800, 150:700]
print('Max motion lower:', lower_motion.max(), 'Mean motion:', lower_motion.mean())
