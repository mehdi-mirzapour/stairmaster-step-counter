import cv2
import json
import numpy as np
from pathlib import Path
from scipy.signal import find_peaks, savgol_filter

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")
cap = cv2.VideoCapture(str(BASE / "samples/sample1.mp4"))
fps = cap.get(cv2.CAP_PROP_FPS)
cap.release()

# Let's inspect the json output from task-947
s2_json = BASE / "output/sample1_yolo_steps.json"
if not s2_json.exists():
    s2_json = BASE / "output/solution2/sample1_yolo_steps.json"

with open(s2_json) as f:
    d = json.load(f)

print(f"Current JSON steps: {d.get('total_steps')} steps")
print("Steps list length:", len(d.get("steps", [])))
