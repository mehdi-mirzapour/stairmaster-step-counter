import sys
from pathlib import Path

BASE_DIR = Path("/home/mehdi/volvo/stairmaster-step-counter")
sys.path.insert(0, str(BASE_DIR))

from src.solution1.video_annotator import render_solution1_annotated_video
from src.solution2.video_annotator import render_solution2_annotated_video
from src.solution4.video_annotator import render_solution4_annotated_video

sample_video = BASE_DIR / "samples/sample1.mp4"
max_dur = 60.0

# 1. Solution 1
print("\n[1/3] Rendering Solution 1 (Sliding VLM)...")
v1_out = BASE_DIR / "output/solution1/sample1_annotated_hud.mp4"
json1 = BASE_DIR / "output/solution1/sample1_step_analysis.json"
render_solution1_annotated_video(
    video_path=sample_video,
    json_path=json1,
    output_video_path=v1_out,
    max_duration_sec=max_dur,
)

# 2. Solution 2
print("\n[2/3] Rendering Solution 2 (YOLOv8-Pose Kinematics)...")
v2_out = BASE_DIR / "output/solution2/sample1_annotated_hud.mp4"
json2 = BASE_DIR / "output/solution2/sample1_yolo_steps.json"
render_solution2_annotated_video(
    video_path=sample_video,
    json_path=json2,
    output_video_path=v2_out,
    max_duration_sec=max_dur,
)

# 3. Solution 4
print("\n[3/3] Rendering Solution 4 (Multimodal Audio-Visual Fusion)...")
v4_out = BASE_DIR / "output/solution4/sample1_annotated_hud.mp4"
json4 = BASE_DIR / "output/solution4/sample1_fusion_steps.json"
wav4 = BASE_DIR / "output/solution4/sample1_audio_temp.wav"
render_solution4_annotated_video(
    video_path=sample_video,
    json_path=json4,
    wav_path=wav4,
    output_video_path=v4_out,
    max_duration_sec=max_dur,
)

print("\n✔ All individual solution videos rendered successfully!")
