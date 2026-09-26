import cv2
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

base_dir = Path("/home/mehdi/volvo/stairmaster-step-counter")
art_dir = Path("/mnt/c/Users/33749/.gemini/antigravity-ide/brain/e0ba1fb5-ac66-4b4d-b06b-7b887bd5e915")
docs_assets = base_dir / "docs" / "assets"

def get_frame(gif_path, frame_idx=32):
    cap = cv2.VideoCapture(str(gif_path))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, fr = cap.read()
    cap.release()
    if fr is not None:
        return cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
    return None

f_pose = get_frame(docs_assets / "demo.gif", 32)
f_kymo = get_frame(docs_assets / "kymograph_demo.gif", 32)
f_acou = get_frame(docs_assets / "acoustic_demo.gif", 32)

W_CANVAS, H_CANVAS = 1200, 675
img = Image.new("RGB", (W_CANVAS, H_CANVAS), (11, 15, 25))
draw = ImageDraw.Draw(img)

# Load fonts
font_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
font_regular = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

f_title = ImageFont.truetype(font_bold, 20)
f_sub = ImageFont.truetype(font_regular, 13)
f_badge = ImageFont.truetype(font_bold, 11)
f_card_title = ImageFont.truetype(font_bold, 13)
f_card_sub = ImageFont.truetype(font_regular, 11)
f_metric_title = ImageFont.truetype(font_bold, 15)
f_metric_sub = ImageFont.truetype(font_regular, 12)

# Top Bar background
draw.rectangle([(0, 0), (W_CANVAS, 105)], fill=(16, 23, 38))
draw.line([(0, 105), (W_CANVAS, 105)], fill=(38, 55, 85), width=1)

# Header Title & Subtitle
draw.text((35, 25), "STAIRMASTER AI: MULTI-MODAL COMPUTER VISION & BIOMECHANICS", fill=(255, 255, 255), font=f_title)
draw.text((35, 62), "Edge YOLOv8-Pose Kinematics  •  Spatio-Temporal Machine Kymography  •  Acoustic Impact Fusion", fill=(148, 163, 184), font=f_sub)

# Badge (top right)
badge_box = [(W_CANVAS - 265, 25), (W_CANVAS - 35, 60)]
draw.rectangle(badge_box, fill=(24, 36, 56), outline=(56, 189, 248), width=1)
draw.ellipse([(W_CANVAS - 252, 38), (W_CANVAS - 242, 48)], fill=(16, 185, 129))
draw.text((W_CANVAS - 232, 36), "LOCAL EDGE AI | $0.00 CLOUD", fill=(56, 189, 248), font=f_badge)

# 3 Snapshot Panels
panel_w, panel_h = 360, 440
panels = [
    (f_pose, "SOLUTION 2: POSE KINEMATICS", "Skeletal Ankle Apex (70+ FPS Edge)", (56, 189, 248)),
    (f_kymo, "SOLUTION 3: OPTICAL KYMOGRAPH", "Stair Tread Bounding Box (>500 FPS)", (16, 220, 140)),
    (f_acou, "SOLUTION 4: MULTIMODAL FUSION", "22.05 kHz Audio Transient + Vision (30 FPS)", (240, 120, 210))
]

x_start = 35
gap = 25

for i, (fr_rgb, p_title, p_sub, col) in enumerate(panels):
    px = x_start + i * (panel_w + gap)
    py = 122
    
    # Outer border
    draw.rectangle([(px - 1, py - 1), (px + panel_w + 1, py + panel_h + 1)], outline=(30, 45, 68), width=1)
    
    if fr_rgb is not None:
        pil_frame = Image.fromarray(fr_rgb).resize((panel_w, panel_h - 52), Image.Resampling.LANCZOS)
        img.paste(pil_frame, (px, py))
    
    # Card Footer
    foot_y1 = py + panel_h - 52
    foot_y2 = py + panel_h
    draw.rectangle([(px, foot_y1), (px + panel_w, foot_y2)], fill=(15, 21, 35))
    draw.line([(px, foot_y1), (px + panel_w, foot_y1)], fill=col, width=2)
    
    draw.text((px + 14, foot_y1 + 10), p_title, fill=col, font=f_card_title)
    draw.text((px + 14, foot_y1 + 28), p_sub, fill=(203, 213, 225), font=f_card_sub)

# Bottom Telemetry Bar
bot_y1 = H_CANVAS - 85
draw.rectangle([(0, bot_y1), (W_CANVAS, H_CANVAS)], fill=(16, 23, 38))
draw.line([(0, bot_y1), (W_CANVAS, bot_y1)], fill=(38, 55, 85), width=1)

metrics = [
    ("LATENCY: 0.37ms", "Sub-millisecond optical kymography"),
    ("ZERO HEAD LEAKS", "100% anonymized edge privacy"),
    ("DUAL CADENCE SYNC", "Machine treads vs. human stride sync"),
    ("OPEN SOURCE SUITE", "Full docs, CLI & benchmark suite")
]

cell_w = W_CANVAS // 4
for idx, (m_top, m_bot) in enumerate(metrics):
    mx = idx * cell_w + 35
    draw.text((mx, bot_y1 + 18), m_top, fill=(255, 255, 255), font=f_metric_title)
    draw.text((mx, bot_y1 + 42), m_bot, fill=(148, 163, 184), font=f_metric_sub)
    if idx > 0:
        draw.line([(idx * cell_w, bot_y1 + 14), (idx * cell_w, H_CANVAS - 14)], fill=(38, 55, 85), width=1)

# Save
out_docs = docs_assets / "linkedin_showcase.png"
img.save(str(out_docs), quality=95)
img.save(str(art_dir / "linkedin_showcase.png"), quality=95)
print(f"✔ Rendered crystal-clear LinkedIn banner: {out_docs}")
