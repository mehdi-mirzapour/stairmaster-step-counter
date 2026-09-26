import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")
model = YOLO(str(BASE / "yolov8n-pose.pt"))
cap = cv2.VideoCapture(str(BASE / "samples" / "sample1.mp4"))

left_conf, right_conf = [], []
left_y, right_y = [], []

for f in range(300): # first 10 seconds
    ret, frame = cap.read()
    if not ret:
        break
    res = model(frame, verbose=False)[0]
    if res.keypoints is not None and len(res.keypoints.xy) > 0:
        kpts = res.keypoints.xy[0].cpu().numpy()
        conf = res.keypoints.conf[0].cpu().numpy() if res.keypoints.conf is not None else None
        
        c_la = conf[15] if conf is not None and len(conf) > 15 else 1.0
        c_ra = conf[16] if conf is not None and len(conf) > 16 else 1.0
        
        left_conf.append(c_la)
        right_conf.append(c_ra)
        left_y.append(kpts[15][1])
        right_y.append(kpts[16][1])

cap.release()

print(f"Left Ankle Mean Confidence: {np.mean(left_conf):.2f}")
print(f"Right Ankle Mean Confidence: {np.mean(right_conf):.2f}")
print(f"Frames with Left Ankle Conf < 0.5: {sum(1 for c in left_conf if c < 0.5)} / {len(left_conf)}")
print(f"Frames with Right Ankle Conf < 0.5: {sum(1 for c in right_conf if c < 0.5)} / {len(right_conf)}")
