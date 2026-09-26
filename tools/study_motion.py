import cv2
import matplotlib.pyplot as plt
from pathlib import Path

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")
cap = cv2.VideoCapture(str(BASE / "samples/sample1.mp4"))
fps = cap.get(cv2.CAP_PROP_FPS)

# Let's inspect frames between 3.0s and 10.0s at 0.5s intervals
times = [3.0, 3.8, 4.6, 5.4, 6.2, 7.0, 7.8, 8.6, 9.4, 10.2]
fig, axes = plt.subplots(2, 5, figsize=(20, 8))
axes = axes.flatten()

for i, t in enumerate(times):
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
    ret, frame = cap.read()
    if ret:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Crop athlete lower body & stairs (y: 600 to 1800, x: 100 to 980)
        h, w, _ = frame.shape
        crop = frame_rgb[int(h*0.3):int(h*0.85), int(w*0.1):int(w*0.85)]
        axes[i].imshow(crop)
        axes[i].set_title(f"t={t:.1f}s (f={int(t*fps)})", fontsize=10)
        axes[i].axis("off")

cap.release()
plt.tight_layout()
plt.savefig(str(BASE / "output/sample1_motion_study.jpg"), dpi=150)
print("Saved sample1_motion_study.jpg")
