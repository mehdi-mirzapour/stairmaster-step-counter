import cv2
import matplotlib.pyplot as plt
from pathlib import Path

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")
cap = cv2.VideoCapture(str(BASE / "samples/sample1.mp4"))
fps = cap.get(cv2.CAP_PROP_FPS)

times = [3.4, 4.2, 5.0, 5.8, 6.6, 7.4, 8.2, 9.0]
fig, axes = plt.subplots(2, 4, figsize=(18, 10))
axes = axes.flatten()

for i, t in enumerate(times):
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
    ret, frame = cap.read()
    if ret:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Crop tight around feet & pedals (y: 1100 to 1800, x: 200 to 750)
        crop = frame_rgb[1100:1800, 200:750]
        axes[i].imshow(crop)
        axes[i].set_title(f"t={t:.2f}s", fontsize=12)
        axes[i].axis("off")

cap.release()
plt.tight_layout()
plt.savefig(str(BASE / "output/sample1_feet_detail.jpg"), dpi=150)
print("Saved sample1_feet_detail.jpg")
