import json
from pathlib import Path

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")
with open(BASE / "output/solution3/sample1_machine_steps.json") as f:
    s3 = json.load(f)
with open(BASE / "output/solution2/sample1_yolo_steps.json") as f:
    s2 = json.load(f)

print("--- SOLUTION 3 (Machine Treads) First 10 ---")
for s in s3["steps"][:10]:
    print(f"Machine Tread #{s['machine_step_id']:2d}: {s['timestamp_sec']:5.2f}s (frame {s['frame']})")

print("\n--- SOLUTION 2 (Pose Ankle Peaks) First 20 ---")
for s in s2["steps"][:20]:
    print(f"Footstep #{s['step_id']:2d} ({s['leg']:5s}): {s['timestamp_sec']:5.2f}s (frame {s['frame']})")
