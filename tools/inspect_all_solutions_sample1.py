import json
from pathlib import Path

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")
paths = [
    BASE / "output/solution1/sample1_step_analysis.json",
    BASE / "output/sample1_step_analysis.json",
    BASE / "output/solution2/sample1_yolo_steps.json",
    BASE / "output/solution3/sample1_machine_steps.json",
    BASE / "output/solution4/sample1_fusion_steps.json",
]

for p in paths:
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        s_count = d.get("total_steps") or len(d.get("deduplicated_steps", []))
        cad = d.get("cadence_spm") or d.get("average_cadence_spm")
        print(f"{p.name:35s} -> total_steps: {s_count}, cadence: {cad}")
    else:
        print(f"{p.name:35s} -> NOT FOUND")
