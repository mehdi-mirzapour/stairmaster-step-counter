import json
from pathlib import Path

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")
with open(BASE / "output/solution3/sample1_machine_steps.json") as f:
    s3 = json.load(f)
with open(BASE / "output/solution2/sample1_yolo_steps.json") as f:
    s2 = json.load(f)

s3_times = [s["timestamp_sec"] for s in s3["steps"]]
s2_times = [s["timestamp_sec"] for s in s2["steps"]]

print("S3 (34 steps):", s3_times)
print("\nS2 (30 steps):", s2_times)
