import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

BASE = Path("/home/mehdi/volvo/stairmaster-step-counter")
cap = cv2.VideoCapture(str(BASE / "samples" / "sample1.mp4"))
fps = 30.0
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Let's inspect the exact pixel window of the step exit:
# The user second image zoomed into the step exit:
# Let's look at a few narrower windows:
# Window 1: x: [0.16, 0.22], y: [0.76, 0.82] (just the opening where the tread passes)
# Window 2: x: [0.14, 0.24], y: [0.75, 0.83]
# Window 3: x: [0.17, 0.23], y: [0.74, 0.80]

w1 = (int(0.16 * w), int(0.76 * h), int(0.22 * w), int(0.82 * h))
w2 = (int(0.14 * w), int(0.75 * h), int(0.24 * w), int(0.83 * h))
w3 = (int(0.17 * w), int(0.74 * h), int(0.23 * w), int(0.80 * h))

sig1, sig2, sig3 = [], [], []

for f in range(150, 450): # 10 seconds: 5.0s to 15.0s
    cap.set(cv2.CAP_PROP_POS_FRAMES, f)
    ret, frame = cap.read()
    if not ret:
        break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    sig1.append(np.mean(gray[w1[1]:w1[3], w1[0]:w1[2]]))
    sig2.append(np.mean(gray[w2[1]:w2[3], w2[0]:w2[2]]))
    sig3.append(np.mean(gray[w3[1]:w3[3], w3[0]:w3[2]]))

cap.release()

t_axis = np.arange(len(sig1)) / fps + 5.0
plt.figure(figsize=(12, 6))
plt.plot(t_axis, sig1, label="W1 (0.16-0.22, 0.76-0.82)")
plt.plot(t_axis, sig2, label="W2 (0.14-0.24, 0.75-0.83)")
plt.plot(t_axis, sig3, label="W3 (0.17-0.23, 0.74-0.80)")
plt.xlabel("Time (s)")
plt.ylabel("Mean Intensity")
plt.title("Sample 1: Step Exit High-Res Signal (5s - 15s)")
plt.legend()
plt.grid(True)
plt.savefig(str(BASE / "output" / "sample1_highres_exit_sig.png"))
print("High-res exit signal plotted.")
