import cv2
import os

cap = cv2.VideoCapture('samples/sample2.mp4')
fps = cap.get(cv2.CAP_PROP_FPS)
count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
duration = count / fps

print(f"sample2: {w}x{h}, {fps} fps, {count} frames, {duration:.2f} seconds")

# Extract a few frames across sample2
os.makedirs('output/inspect_s2', exist_ok=True)
for sec in [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]:
    frame_idx = int(sec * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(f'output/inspect_s2/frame_{sec:.1f}s.jpg', frame)
cap.release()
print("Saved inspection frames to output/inspect_s2/")
