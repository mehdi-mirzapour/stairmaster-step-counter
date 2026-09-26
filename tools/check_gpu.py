import torch
from ultralytics import YOLO

print(f"PyTorch Version: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"Device Count: {torch.cuda.device_count()}")
    print(f"Device Name: {torch.cuda.get_device_name(0)}")
else:
    print("CUDA is NOT active in this PyTorch build (CPU only).")

# Check what device YOLO selects by default
model = YOLO("yolov8n-pose.pt")
print(f"Default YOLO Device: {model.device}")
