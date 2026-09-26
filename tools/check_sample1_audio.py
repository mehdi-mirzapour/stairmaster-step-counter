import wave
import subprocess
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.signal import butter, filtfilt, find_peaks

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")
wav_path = BASE / "output" / "test_sample1_audio.wav"

cmd = [
    "ffmpeg", "-y", "-i", str(BASE / "samples" / "sample1.mp4"),
    "-vn", "-ac", "1", "-ar", "22050", "-t", "60",
    str(wav_path)
]
subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

with wave.open(str(wav_path), "rb") as wf:
    n_samples = wf.getnframes()
    audio = np.frombuffer(wf.readframes(n_samples), dtype=np.int16).astype(np.float32)

sr = 22050
# Bandpass 80-600 Hz (stair thud frequency)
b, a = butter(4, [80 / (sr / 2), 600 / (sr / 2)], btype='band')
filtered = filtfilt(b, a, audio)
envelope = np.abs(filtered)
window_len = int(sr * 0.04) # 40ms smoothing
smoothed = np.convolve(envelope, np.ones(window_len)/window_len, mode='same')

# Peak detection
peaks, props = find_peaks(smoothed, distance=int(sr * 0.40), prominence=np.max(smoothed) * 0.12)
impact_times = peaks / sr

print(f"Total Audio Impact Peaks (first 60s): {len(peaks)}")
print(f"Mean Peak Interval: {np.mean(np.diff(impact_times)):.3f}s")
print(f"Calculated Audio Cadence: {len(peaks) / 60.0 * 60.0:.1f} Steps/Min")

# Plot first 15 seconds
plt.figure(figsize=(14, 5))
t_ax = np.arange(int(sr * 15)) / sr
plt.plot(t_ax, smoothed[:len(t_ax)], color='magenta', label="Smoothed Audio Footstrike Envelope")
p_15 = [p for p in peaks if p < sr * 15]
plt.plot(np.array(p_15) / sr, smoothed[p_15], 'ro', label=f"Detected Impacts ({len(p_15)} in 15s)")
plt.xlabel("Time (s)")
plt.ylabel("Audio Amplitude (80-600Hz)")
plt.title("Sample 1: Audio Footstrike Impacts")
plt.legend()
plt.grid(True)
plt.savefig(str(BASE / "output" / "sample1_audio_peaks_test.png"))
print("Saved audio peaks plot.")
