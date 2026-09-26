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
# Let's test different distance and filtering parameters for audio
# A true footstep occurs roughly every 1.5s to 1.8s (or if bilateral, how often?)
# Let's check peaks with distance = 1.0s (min 1 step/sec)
b, a = butter(4, [80 / (sr / 2), 450 / (sr / 2)], btype='band')
filtered = filtfilt(b, a, audio)
envelope = np.abs(filtered)
window_len = int(sr * 0.08) # 80ms smoothing
smoothed = np.convolve(envelope, np.ones(window_len)/window_len, mode='same')

# Find major impact peaks with distance = 1.0s (e.g. cadence ~35-40 SPM)
peaks_35, _ = find_peaks(smoothed, distance=int(sr * 1.1), prominence=np.max(smoothed) * 0.15)
# Find impacts with distance = 0.5s (e.g. cadence ~70 SPM)
peaks_70, _ = find_peaks(smoothed, distance=int(sr * 0.5), prominence=np.max(smoothed) * 0.12)

print(f"Peaks with distance=1.1s (Major Footfalls): {len(peaks_35)} (Cadence: {len(peaks_35)} SPM)")
print(f"Peaks with distance=0.5s (All Transients): {len(peaks_70)} (Cadence: {len(peaks_70)} SPM)")
