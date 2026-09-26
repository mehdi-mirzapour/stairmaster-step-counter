import time
import torch
import cv2
from ultralytics import YOLO

print(f"CUDA: {torch.cuda.is_available()} | Device: {torch.cuda.get_device_name(0)}")

# Load model onto CUDA GPU
model = YOLO("yolov8n-pose.pt")

cap = cv2.VideoCapture("samples/sample2.mp4")
frames = []
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    frames.append(frame)
cap.release()

print(f"Loaded {len(frames)} frames into RAM.")

# Warmup GPU
_ = model(frames[0], device="cuda", verbose=False)

# Benchmark GPU
t0 = time.time()
for f in frames:
    _ = model(f, device="cuda", verbose=False)
t_gpu = time.time() - t0

fps_gpu = len(frames) / t_gpu
print(f"🚀 RTX 3060 GPU Runtime: {t_gpu:.3f} s ({fps_gpu:.1f} FPS)")
