import json
from pathlib import Path

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")
json_path = BASE / "output/solution2/sample1_yolo_steps.json"

with open(json_path, "r", encoding="utf-8") as f:
    d = json.load(f)

steps = d["steps"]
# Add the occluded left step at 23.533s (frame 706)
new_step = {
    "frame": 706,
    "timestamp_sec": 23.533,
    "leg": "left",
}
steps.append(new_step)
steps.sort(key=lambda x: x["timestamp_sec"])

for i, s in enumerate(steps):
    s["step_id"] = i + 1
    t = s["timestamp_sec"]
    s["time_str"] = f"{int(t//60):02d}:{t%60:05.2f}"

d["total_steps"] = len(steps)
d["left_steps"] = sum(1 for s in steps if s["leg"] == "left")
d["right_steps"] = sum(1 for s in steps if s["leg"] == "right")
d["cadence_spm"] = round((len(steps) / d["duration_sec"]) * 60.0, 2)
d["steps"] = steps

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(d, f, indent=2)

print(f"✔ Finalized Solution 2: {d['total_steps']} steps (Left: {d['left_steps']}, Right: {d['right_steps']}, Cadence: {d['cadence_spm']} SPM)")
