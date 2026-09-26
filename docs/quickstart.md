# 🚀 Quickstart Guide & CLI Reference

Get up and running with the Stairmaster AI Step Counter suite in under 2 minutes.

---

## 📦 1. Installation

This project is built for Python 3.10+ and optimized for [Astral `uv`](https://github.com/astral-sh/uv).

### Option A: Using `uv` (Recommended - Lightning Fast)
```bash
git clone https://github.com/username/stairmaster-step-counter.git
cd stairmaster-step-counter

# Install dependencies into isolated virtualenv automatically:
uv sync
```

### Option B: Using Standard Python `pip`
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

---

## ⚡ 2. Quick CLI Usage

The repository provides a unified command-line entry point: `stairmaster` (or `python -m src.cli`).

### 📊 Run the Telemetry Benchmark Suite
Evaluates and benchmarks all local computer vision pipelines on the sample:
```bash
uv run stairmaster --benchmark
```
*Outputs: Formatted comparison table with steps detected, cadence (SPM), processing FPS, and the Biomechanical Dual-Metric Insight ($\Delta_{\text{drift}}$).*

---

### 🏃 Run Solution 2 (Edge YOLOv8-Pose Kinematics)
Runs real-time 2D pose tracking on CPU or GPU:
```bash
# Run analysis on 5-second sprint:
uv run stairmaster --solution 2 --duration 5.0

# Generate annotated video with real-time sports telemetry HUD & face anonymization:
uv run stairmaster --solution 2 --duration 5.0 --save-video
```
*Outputs: `output/solution2/sample2_yolo_steps.json` and `output/solution2/sample2_annotated_hud.mp4`.*

---

### ⚙️ Run Solution 3 (Physical Machine Step Tracker)
Sub-millisecond spatio-temporal optical kymograph tracking revolving stair treads:
```bash
uv run stairmaster --solution 3 --duration 5.0 --save-video
```
*Outputs: `output/solution3/sample2_machine_steps.json` and `output/solution3/sample2_annotated_hud.mp4`.*

---

### 🎬 Run on Custom Video Files
You can analyze any custom gym video recorded on your phone:
```bash
# Place your video into the git-ignored local/samples folder:
mkdir -p local/samples
cp /path/to/my_workout.mp4 local/samples/my_workout.mp4

# Run analysis:
uv run stairmaster --video local/samples/my_workout.mp4 --solution 2 --save-video
```

---

## 🛠️ CLI Flag Reference

| Flag | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `--benchmark` | Flag | `False` | Run multi-solution performance & latency comparison table |
| `--solution` | String | `2` | Choose pipeline: `1` (VLM), `2` (Pose), `3` (Kymograph), `4` (Fusion), `5` (Audio), or `all` |
| `--video` | Path | `None` | Custom input video path (prioritizes `local/samples/` if omitted) |
| `--sample` | Int | `2` | Benchmark sample index (`2` = standard 5s sprint clip) |
| `--duration` | Float | `5.0` | Maximum video duration to process in seconds |
| `--save-video` | Flag | `False` | Render broadcast HUD annotated video with live telemetry overlays |

---

## 📁 Output Artifacts Structure

Processed results are exported in structured JSON format under `output/`:
```json
{
  "solution": "Solution 2: Edge-Native YOLOv8-Pose Kinematics",
  "total_steps": 11,
  "left_steps": 6,
  "right_steps": 5,
  "cadence_spm": 132.0,
  "duration_sec": 5.0,
  "fps_processing": 70.4,
  "steps": [
    {
      "step_id": 1,
      "frame": 7,
      "timestamp_sec": 0.233,
      "leg": "right",
      "time_str": "00:00.23"
    },
    ...
  ]
}
```
