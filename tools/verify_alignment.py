import cv2
import json
import numpy as np
from pathlib import Path
from scipy.signal import find_peaks, savgol_filter, butter, filtfilt
import wave

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")

# Load Solution 3 steps
with open(BASE / "output/solution3/sample1_machine_steps.json") as f:
    s3_data = json.load(f)
s3_times = [s["timestamp_sec"] for s in s3_data["steps"]]

# Run Audio 34
wav_path = BASE / "output" / "test_sample1_audio.wav"
with wave.open(str(wav_path), "rb") as wf:
    n_samples = wf.getnframes()
    audio = np.frombuffer(wf.readframes(n_samples), dtype=np.int16).astype(np.float32)

sr = 22050
b, a = butter(4, [60 / (sr / 2), 350 / (sr / 2)], btype='band')
filtered = filtfilt(b, a, audio)
envelope = np.abs(filtered)
window_len = int(sr * 0.10)
smoothed = np.convolve(envelope, np.ones(window_len)/window_len, mode='same')
audio_peaks, _ = find_peaks(smoothed, distance=int(sr * 1.1), prominence=np.max(smoothed) * 0.11)
audio_times = [round(float(p) / sr, 2) for p in audio_peaks]

print(f"Solution 3 (Machine Kymograph): {len(s3_times)} steps")
print(f"Solution 5 (Audio Footfalls):   {len(audio_times)} steps")

# Compare first 10 steps
print("\nStep Alignment Check (First 10 steps):")
print("Step | S3 Machine | S5 Audio | Diff (ms)")
print("---------------------------------------")
for i in range(min(10, len(s3_times), len(audio_times))):
    diff = abs(s3_times[i] - audio_times[i]) * 1000
    print(f"#{i+1:2d}  | {s3_times[i]:6.2f}s    | {audio_times[i]:6.2f}s   | {diff:5.0f} ms")
