import json
from pathlib import Path

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")
with open(BASE / "output/solution2/sample1_yolo_steps.json") as f:
    d = json.load(f)

steps = d["steps"]
print(f"Total Steps in S2: {len(steps)}")
for i in range(len(steps)-1):
    dt = steps[i+1]["timestamp_sec"] - steps[i]["timestamp_sec"]
    if dt > 2.4:
        print(f"Gap between #{i+1} ({steps[i]['timestamp_sec']}s) and #{i+2} ({steps[i+1]['timestamp_sec']}s): {dt:.2f}s")
