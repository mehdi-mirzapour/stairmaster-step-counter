import cv2
import numpy as np
from pathlib import Path

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")
frame = cv2.imread(str(BASE / "output" / "sample1_frame_test.jpg"))
h, w = frame.shape[:2]

# Let's test a few candidate ROIs in normalized coordinates (x1, y1, x2, y2)
# The previous ROI was (0.20, 0.65, 0.40, 0.82) -> in pixels: x: [216, 432], y: [1248, 1574]
# Notice in Image 2, the step is further down and to the left!
# Look at the step around x: 0.12 - 0.28, y: 0.50 - 0.70? Or lower: y: 0.55 - 0.65?
# Let's draw a grid on a zoomed-in crop of the machine base:
# x from 0.05 to 0.45, y from 0.45 to 0.85

vis = frame.copy()

# Draw grid lines every 0.05 (5% of width/height)
for ny in np.arange(0.45, 0.85, 0.02):
    y = int(ny * h)
    cv2.line(vis, (0, y), (int(0.5 * w), y), (100, 100, 100), 1)
    cv2.putText(vis, f"y={ny:.2f}", (10, y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

for nx in np.arange(0.05, 0.45, 0.05):
    x = int(nx * w)
    cv2.line(vis, (x, int(0.45 * h)), (x, int(0.85 * h)), (100, 100, 100), 1)
    cv2.putText(vis, f"x={nx:.2f}", (x + 4, int(0.47 * h)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

crop = vis[int(0.45 * h):int(0.85 * h), 0:int(0.50 * w)]
cv2.imwrite(str(BASE / "output" / "sample1_grid_inspection.jpg"), crop)
print("Grid inspection image saved.")
