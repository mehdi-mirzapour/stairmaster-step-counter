import wave
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.signal import butter, filtfilt, find_peaks

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")
wav_path = BASE / "output" / "test_sample1_audio.wav"

with wave.open(str(wav_path), "rb") as wf:
    n_samples = wf.getnframes()
    audio = np.frombuffer(wf.readframes(n_samples), dtype=np.int16).astype(np.float32)

sr = 22050
# StairMaster mechanical impact filter: 60-350 Hz (deep thud of foot landing on rubber step)
b, a = butter(4, [60 / (sr / 2), 350 / (sr / 2)], btype='band')
filtered = filtfilt(b, a, audio)
envelope = np.abs(filtered)
window_len = int(sr * 0.10) # 100ms smoothing
smoothed = np.convolve(envelope, np.ones(window_len)/window_len, mode='same')

# For 34 steps in 60s, interval is ~1.76s (40-50 frames at 30fps)
# Minimum distance between steps is ~1.1s to 1.3s
for dist_sec in [1.0, 1.1, 1.2, 1.3, 1.4]:
    dist_samples = int(sr * dist_sec)
    for p_fac in [0.08, 0.10, 0.12, 0.15]:
        peaks, _ = find_peaks(smoothed, distance=dist_samples, prominence=np.max(smoothed) * p_fac)
        print(f"dist={dist_sec:.1f}s, prom={p_fac:.2f} -> Audio Steps: {len(peaks):2d} (Cadence: {len(peaks):.1f} SPM)")
