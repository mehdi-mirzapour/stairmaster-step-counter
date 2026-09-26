import wave
import numpy as np
from pathlib import Path
from scipy.signal import butter, filtfilt, find_peaks

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")
wav_path = BASE / "output" / "test_sample1_audio.wav"

with wave.open(str(wav_path), "rb") as wf:
    n_samples = wf.getnframes()
    audio = np.frombuffer(wf.readframes(n_samples), dtype=np.int16).astype(np.float32)

sr = 22050
b, a = butter(4, [80 / (sr / 2), 500 / (sr / 2)], btype='band')
filtered = filtfilt(b, a, audio)
envelope = np.abs(filtered)
window_len = int(sr * 0.08)
smoothed = np.convolve(envelope, np.ones(window_len)/window_len, mode='same')

# Downsample smoothed envelope for fast autocorrelation
factor = 50
env_ds = smoothed[::factor]
sr_ds = sr / factor

# Autocorrelation
env_centered = env_ds - np.mean(env_ds)
corr = np.correlate(env_centered, env_centered, mode='full')
corr = corr[len(corr)//2:]

# Search lag from 0.35s to 3.0s
min_lag = int(0.35 * sr_ds)
max_lag = int(3.0 * sr_ds)
lag_peak = min_lag + np.argmax(corr[min_lag:max_lag])
dominant_period = lag_peak / sr_ds
dominant_spm = 60.0 / dominant_period

print(f"Detected Dominant Step Period: {dominant_period:.2f}s ({dominant_spm:.1f} SPM)")

# Test peak detection using 0.65 * dominant_period as min distance
min_dist_samples = int(sr * dominant_period * 0.65)
prom = np.max(smoothed) * 0.12
peaks, props = find_peaks(smoothed, distance=min_dist_samples, prominence=prom)
print(f"Adaptive Audio Peaks Count: {len(peaks)} (Cadence: {len(peaks) / 60.0 * 60.0:.1f} SPM)")
