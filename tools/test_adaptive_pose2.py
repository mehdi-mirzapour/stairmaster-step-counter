import numpy as np
import json
from pathlib import Path
from scipy.signal import find_peaks, savgol_filter

# Let's test with the saved keypoints from task-928
# In task-928, raw_la_y and raw_ra_y were collected
print("Running adaptive test...")
