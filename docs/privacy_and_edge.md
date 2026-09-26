# 🛡️ Privacy-by-Design & Edge Deployment Guide

Commercial fitness clubs and residential gyms operate under strict privacy regulations (such as EU GDPR Article 9 regarding biometric processing and state privacy laws). Deploying computer vision cameras in fitness spaces requires a rigorous **Privacy-by-Design** architecture.

This project was engineered from the ground up to ensure **zero biometric exposure** and **100% local edge processing**.

---

## 🔒 1. Privacy-by-Design Architecture

```
Camera Input (Local RTSP / USB)
       │
       ▼
 [Local RAM Buffer]  ──► (Never written to persistent disk)
       │
       ├──► 1. Keypoint Kinematics (COCO Ankles / Knees)
       │
       ├──► 2. Dynamic Face Anonymization (Gaussian Blur + HUD Matte)
       │
       └──► 3. Mathematical Feature Extraction (Spatio-Temporal Kymograph)
       │
       ▼
 [Telemetry Extraction: Steps, Cadence, SPM, Drift]
       │
       ▼
 (Raw frames instantly discarded from RAM)
```

### Key Privacy Safeguards:
1. **Dynamic Face Anonymization**:
   - Whenever facial or cranial keypoints (COCO $\#0$ to $\#4$: nose, eyes, ears) are detected, a heavy $51\times 51$ Gaussian blur and dark digital vignette are applied on-the-fly before any frame preview or video recording is constructed.
   - The athlete's facial identity is permanently masked.
2. **Rear & Tread-Focused Camera Geometry**:
   - Commercial installations are recommended to position the camera at a **rear $45^\circ$ or $90^\circ$ low side-angle** focused on the stair tread exit rather than the athlete's face.
3. **Ephemeral Frame Lifecycle**:
   - Frames are analyzed in volatile memory (RAM) and immediately discarded.
   - Only non-biometric numerical scalar telemetry (`steps: 11, cadence: 132 SPM, timestamp: 4.67s`) is transmitted to gym management APIs or fitness apps.
4. **Zero Cloud Streaming**:
   - Solutions 2, 3, 4, and 5 run 100% offline with zero external network calls.
   - Solution 1 (Cloud VLM) is an optional audit mode that can be disabled entirely in privacy-restricted environments.

---

## 🖥️ 2. Edge Hardware Deployment Matrix

| Hardware Tier | Recommended Device | Target Solution | Expected Latency | Approx. Cost |
| :--- | :--- | :--- | :---: | :---: |
| **Tier 1: Microcontroller** | ESP32-S3 or Raspberry Pi Zero 2W | Solution 3 (Kymograph) or Solution 5 (Audio) | < 2 ms | $15 – $35 |
| **Tier 2: Single-Board Computer** | Raspberry Pi 5 (8GB) | Solution 3 + Solution 4 (CPU ONNX) | < 30 ms | $80 – $100 |
| **Tier 3: Embedded AI Accelerator** | NVIDIA Jetson Orin Nano (8GB) | Solution 2 (YOLOv8-Pose TensorRT) | < 8 ms | $250 – $300 |
| **Tier 4: Gym Server / Mini-PC** | Intel Core i5 / AMD Ryzen Mini-PC | Multi-Camera Stream (4–8 Stairmasters simultaneously) | < 15 ms / machine | $400 – $600 |

---

## 📐 3. Physical Mounting & Field-of-View Recommendations

```
           [Wall / Ceiling Mount]
                    \
                     \ Camera Angle (~30° - 45° tilt)
                      \
                       ▼
                 [Stairmaster SF-C2]
                    ┌─────────┐
                    │ Console │
                    ├─────────┤
                    │   /\    │ <-- Athlete
                    │  /  \   │
                    ├─────────┤
                    │  STEPS  │ <-- Optimal ROI: Bottom 3 Stair Treads
                    └─────────┘
```

1. **Mounting Height**: $1.2\text{ m} – 1.8\text{ m}$ from floor level.
2. **Mounting Distance**: $1.5\text{ m} – 2.5\text{ m}$ behind or laterally from the climber.
3. **Lighting Requirements**: Minimum 150 lux ambient gym lighting. Backlit LED step strips (present on modern commercial machines) significantly improve tread edge detection in Solution 3.
