import cv2
import json
from pathlib import Path
from ultralytics import YOLO

model = YOLO("yolov8n-pose.pt")
cap = cv2.VideoCapture("samples/sample2.mp4")
fps = cap.get(cv2.CAP_PROP_FPS)

head_kpts_list = []
frame_idx = 0
while cap.isOpened() and frame_idx < 150: # 5 seconds
    ret, frame = cap.read()
    if not ret:
        break
    res = model(frame, verbose=False)[0]
    if res.keypoints is not None and len(res.keypoints.xy) > 0:
        kpts = res.keypoints.xy[0].cpu().numpy()
        # 0: nose, 1: left_eye, 2: right_eye, 3: left_ear, 4: right_ear
        head_pts = kpts[0:5]
        valid_head = [pt for pt in head_pts if pt[0] > 0 and pt[1] > 0]
        if valid_head:
            min_x = min(p[0] for p in valid_head)
            max_x = max(p[0] for p in valid_head)
            min_y = min(p[1] for p in valid_head)
            max_y = max(p[1] for p in valid_head)
            head_kpts_list.append((frame_idx, min_x, max_x, min_y, max_y))
    frame_idx += 1
cap.release()

print(f"Inspected {frame_idx} frames. Found head in {len(head_kpts_list)} frames.")
if head_kpts_list:
    overall_min_x = min(x[1] for x in head_kpts_list)
    overall_max_x = max(x[2] for x in head_kpts_list)
    overall_min_y = min(x[3] for x in head_kpts_list)
    overall_max_y = max(x[4] for x in head_kpts_list)
    print(f"Head bounds across 5s: X: [{overall_min_x:.1f}, {overall_max_x:.1f}], Y: [{overall_min_y:.1f}, {overall_max_y:.1f}]")
