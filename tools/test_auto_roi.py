import cv2
import numpy as np
from pathlib import Path
from scipy.signal import find_peaks, savgol_filter

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")

def evaluate_roi_quality(cap, roi_norm, max_frames=180):
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    x1, y1 = int(w * roi_norm[0]), int(h * roi_norm[1])
    x2, y2 = int(w * roi_norm[2]), int(h * roi_norm[3])
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    signals = []
    for _ in range(max_frames):
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        crop = gray[y1:y2, x1:x2]
        signals.append(np.mean(crop))
        
    if len(signals) < 15:
        return 0.0, 0
        
    sig = np.array(signals)
    smooth = savgol_filter(sig, min(9, len(sig)//2*2-1), 2)
    peaks, props = find_peaks(smooth, distance=8, prominence=2.0)
    
    # Quality score: variance of periodic signal * prominence
    if len(peaks) >= 1:
        prom = np.mean(props["prominences"])
        snr = np.std(smooth) * prom
        return snr, len(peaks)
    return 0.0, 0

# Candidate regions:
# Profile exit (Sample 1): (0.14, 0.75, 0.24, 0.83)
# Rear central tread (Sample 2): (0.46, 0.46, 0.58, 0.60)

for s_num in [1, 2]:
    video_p = BASE / "samples" / f"sample{s_num}.mp4"
    cap = cv2.VideoCapture(str(video_p))
    score_exit, p_exit = evaluate_roi_quality(cap, (0.14, 0.75, 0.24, 0.83))
    score_rear, p_rear = evaluate_roi_quality(cap, (0.46, 0.46, 0.58, 0.60))
    cap.release()
    print(f"Sample {s_num}:")
    print(f"  Side-Exit ROI Score: {score_exit:.2f} (peaks: {p_exit})")
    print(f"  Rear-Central ROI Score: {score_rear:.2f} (peaks: {p_rear})")
    best = "Side-Exit" if score_exit > score_rear else "Rear-Central"
    print(f"  => Auto-Selected ROI: {best}\n")
