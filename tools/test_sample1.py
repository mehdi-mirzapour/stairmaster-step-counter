import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
from src.machine_step_tracker import MachineStepTracker

for prom in [0.8, 1.2, 1.5, 2.0]:
    tracker = MachineStepTracker(min_peak_distance_frames=16, prominence_threshold=prom)
    res = tracker.count_machine_steps(
        str(BASE_DIR / 'samples' / 'sample1.mp4'),
        stair_roi_norm=(0.20, 0.65, 0.40, 0.82),
        max_duration_sec=60.0
    )
    print(f"prom={prom}: steps={res['total_machine_steps']}, cadence={res['cadence_spm']}")
