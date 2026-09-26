import json
from pathlib import Path
from src.machine_step_tracker import MachineStepTracker

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")
tracker = MachineStepTracker(min_peak_distance_frames=20, prominence_threshold=4.0)

res = tracker.count_machine_steps(
    video_path=BASE / "samples" / "sample1.mp4",
    stair_roi_norm=(0.14, 0.75, 0.24, 0.83),
    max_duration_sec=60.0
)

print(f"Total Machine Revolving Treads: {res['total_machine_steps']}")
print(f"Cadence: {res['cadence_spm']} Steps/Min")
print(f"Mean Step Interval: {res['mean_step_interval_sec']} s")
print("First 10 steps:")
for s in res["steps"][:10]:
    print(f"  Step #{s['machine_step_id']:02d}: {s['timestamp_sec']}s ({s['time_str']}) - Frame #{s['frame']}")
