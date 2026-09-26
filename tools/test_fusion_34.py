import json
from pathlib import Path

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")

# Load Solution 3 (Machine ground truth 34 steps)
with open(BASE / "output/solution3/sample1_machine_steps.json") as f:
    s3 = json.load(f)

# Load Solution 5 (Audio 34 steps)
with open(BASE / "output/solution5/sample1_audio_steps.json") as f:
    s5 = json.load(f)

print(f"Machine Steps: {len(s3['steps'])}")
print(f"Audio Steps:   {len(s5['steps'])}")
