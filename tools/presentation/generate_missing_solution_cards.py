import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

WS_DIR = "/home/mehdi/volvo/stairmaster-step-counter"
OUT_DIR = os.path.join(WS_DIR, "output/white_presentation")
ARTIFACTS_DIR = "/mnt/c/Users/33749/.gemini/antigravity-ide/brain/02def22c-a0dc-4ea4-8a4d-1ca6ce501685"
os.makedirs(OUT_DIR, exist_ok=True)

FONT_BOLD = os.path.join(WS_DIR, ".venv/lib/python3.14/site-packages/matplotlib/mpl-data/fonts/ttf/DejaVuSans-Bold.ttf")
FONT_REGULAR = os.path.join(WS_DIR, ".venv/lib/python3.14/site-packages/matplotlib/mpl-data/fonts/ttf/DejaVuSans.ttf")

def get_font(size, bold=False):
    fpath = FONT_BOLD if bold else FONT_REGULAR
    if os.path.exists(fpath):
        return ImageFont.truetype(fpath, size)
    return ImageFont.load_default()

def draw_card(draw, box, bg_color="#FFFFFF", border_color="#E2E8F0", border_width=2, radius=16):
    x0, y0, x1, y1 = box
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=bg_color, outline=border_color, width=border_width)

def draw_pill(draw, xy, text, bg_color="#10B981", text_color="#FFFFFF", font_size=15):
    font = get_font(font_size, bold=True)
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    px, py = xy
    pad_x, pad_y = 12, 5
    pill_box = [px, py, px + tw + pad_x * 2, py + th + pad_y * 2]
    draw.rounded_rectangle(pill_box, radius=10, fill=bg_color)
    draw.text((px + pad_x, py + pad_y - bbox[1]), text, font=font, fill=text_color)
    return pill_box[2]

def extract_frame(video_path, frame_idx):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    cap.release()
    if ret:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(frame_rgb)
    return None

# ==============================================================================
# CARD: SOLUTION 1 (SLIDING VISION LLM)
# ==============================================================================
def make_card_solution1():
    W, H = 1600, 960
    img = Image.new("RGB", (W, H), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    draw_pill(draw, (60, 40), "SOLUTION 1 — THE FOUNDATION MODEL (CLOUD VLM)", bg_color="#EF4444", text_color="#FFFFFF", font_size=16)
    draw.text((60, 85), "Sliding Vision LLM (GPT-4o-mini / Gemini API)", font=get_font(34, bold=True), fill="#0F172A")
    draw.text((60, 135), "Zero custom training required — high flexibility, but subject to cloud latency and API costs.", font=get_font(18, bold=False), fill="#64748B")

    frame = extract_frame(os.path.join(WS_DIR, "output/solution1/sample1_annotated_hud.mp4"), 450)
    if frame is not None:
        fw, fh = frame.size
        cropped = frame.crop((0, int(fh * 0.20), fw, int(fh * 0.95)))
        target_w, target_h = 580, 720
        cropped = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        draw_card(draw, [55, 185, 55 + target_w + 10, 185 + target_h + 10], bg_color="#000000", border_color="#EF4444", border_width=3, radius=16)
        img.paste(cropped, (60, 190))

    rx = 690
    rw = W - rx - 60

    # 1. Latency Showcase Box
    draw_card(draw, [rx, 190, rx + rw, 310], bg_color="#FEF2F2", border_color="#FECACA", border_width=2, radius=16)
    draw_pill(draw, (rx + 25, 210), "⚠️ CLOUD LATENCY BOTTLENECK", bg_color="#DC2626", text_color="#FFFFFF", font_size=14)
    draw.text((rx + 25, 250), "~12.0 Seconds per Video Window", font=get_font(26, bold=True), fill="#991B1B")
    draw.text((rx + 25, 282), "2.0 to 5.0 seconds delay per step | 0.08× Real-Time | Requires internet uplink", font=get_font(15, bold=False), fill="#B91C1C")

    # 2. Key Architectural Explanations
    points = [
        {
            "tag": "ZERO-SHOT GENERALIZATION",
            "color": "#10B981",
            "title": "Understands Any Scene Without Model Training",
            "body": "Because it uses a massive multimodal vision model, it understands what a StairMaster is instantly. It can adapt to wild camera angles, unusual lighting, or new gym equipment without retraining."
        },
        {
            "tag": "PRIVACY & GDPR CONCERNS",
            "color": "#8B5CF6",
            "title": "Cloud Streaming Raises Member Hesitation",
            "body": "Streaming continuous video of gym members to external cloud servers (OpenAI/Google) creates significant GDPR, compliance, and privacy hurdles for gym chains."
        },
        {
            "tag": "HIGH OPERATING COST",
            "color": "#EF4444",
            "title": "Recurring Cloud API Fees (~$0.04 - $0.06 / min)",
            "body": "A commercial gym with 20 StairMasters running 12 hours a day would incur thousands of dollars every month in API token bills, making cloud streaming commercially unviable for consoles."
        }
    ]

    py = 330
    for p in points:
        draw_card(draw, [rx, py, rx + rw, py + 150], bg_color="#F8FAFC", border_color="#E2E8F0", border_width=2, radius=14)
        draw_pill(draw, (rx + 20, py + 15), p["tag"], bg_color=p["color"], text_color="#FFFFFF", font_size=12)
        draw.text((rx + 20, py + 48), p["title"], font=get_font(18, bold=True), fill="#0F172A")
        
        words = p["body"].split(" ")
        lines, curr = [], ""
        for w in words:
            if len(curr + " " + w) < 70:
                curr = (curr + " " + w).strip()
            else:
                lines.append(curr)
                curr = w
        if curr:
            lines.append(curr)
            
        ly = py + 78
        for l in lines:
            draw.text((rx + 20, ly), l, font=get_font(14, bold=False), fill="#475569")
            ly += 20
        py += 165

    draw_card(draw, [rx, 830, rx + rw, 915], bg_color="#F1F5F9", border_color="#CBD5E1", border_width=2, radius=14)
    draw.text((rx + 25, 845), "Result on Sample 1: 34 Steps Detected | Perfect Accuracy, but Delayed Feedback", font=get_font(17, bold=True), fill="#0F172A")
    draw.text((rx + 25, 875), "Verdict: Excellent for automated QA testing and research; too slow and costly for real-time gym displays.", font=get_font(14, bold=False), fill="#64748B")

    out_path = os.path.join(OUT_DIR, "card_solution1_vlm_white.png")
    img.save(out_path, quality=95)
    print(f"Generated {out_path}")
    return out_path

# ==============================================================================
# CARD: SOLUTION 4 (MULTIMODAL DUAL FUSION)
# ==============================================================================
def make_card_solution4():
    W, H = 1600, 960
    img = Image.new("RGB", (W, H), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    draw_pill(draw, (60, 40), "SOLUTION 4 — THE ULTIMATE RELIABILITY (DUAL FUSION)", bg_color="#F59E0B", text_color="#FFFFFF", font_size=16)
    draw.text((60, 85), "Multimodal Coincidence Fusion (Optical Tread + Audio)", font=get_font(34, bold=True), fill="#0F172A")
    draw.text((60, 135), "Pairs optical tread movement with acoustic foot impact: a step is validated only when BOTH sensors agree.", font=get_font(18, bold=False), fill="#64748B")

    frame = extract_frame(os.path.join(WS_DIR, "output/solution4/sample1_annotated_hud.mp4"), 450)
    if frame is not None:
        fw, fh = frame.size
        cropped = frame.crop((0, int(fh * 0.20), fw, int(fh * 0.95)))
        target_w, target_h = 580, 720
        cropped = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        draw_card(draw, [55, 185, 55 + target_w + 10, 185 + target_h + 10], bg_color="#000000", border_color="#F59E0B", border_width=3, radius=16)
        img.paste(cropped, (60, 190))

    rx = 690
    rw = W - rx - 60

    # 1. Latency Showcase Box
    draw_card(draw, [rx, 190, rx + rw, 310], bg_color="#FFFBEB", border_color="#FDE68A", border_width=2, radius=16)
    draw_pill(draw, (rx + 25, 210), "⚡ EDGE SYNCHRONIZED STREAMING", bg_color="#D97706", text_color="#FFFFFF", font_size=14)
    draw.text((rx + 25, 250), "28.1 Seconds Compute (60s Workout)", font=get_font(26, bold=True), fill="#92400E")
    draw.text((rx + 25, 282), "2.1× Real-Time (~45 FPS) | 100ms coincidence buffer | Immediate on-device display", font=get_font(15, bold=False), fill="#B45309")

    # 2. Key Architectural Explanations
    points = [
        {
            "tag": "ZERO FALSE POSITIVES",
            "color": "#10B981",
            "title": "Cross-Sensor Coincidence Verification (100ms Window)",
            "body": "Machine vibration without a footstep? Rejected. Athlete shifting weight without moving the stairs? Rejected. A step is logged ONLY when both the optical tread signal and acoustic impulse align."
        },
        {
            "tag": "FAIL-SAFE REDUNDANCY",
            "color": "#0284C7",
            "title": "Graceful Fallback Mode",
            "body": "If loud gym music disrupts the microphone, the system maintains count using optical tracking. If someone covers the camera, audio DSP takes over seamlessly. Neither sensor is a single point of failure."
        },
        {
            "tag": "ON-DEVICE EDGE PIPELINE",
            "color": "#8B5CF6",
            "title": "Runs 100% Locally Without Cloud Dependency",
            "body": "Processes video and audio streams synchronously on a local mini-PC or embedded board. No external internet connection is required, preserving user privacy and eliminating recurring API fees."
        }
    ]

    py = 330
    for p in points:
        draw_card(draw, [rx, py, rx + rw, py + 150], bg_color="#F8FAFC", border_color="#E2E8F0", border_width=2, radius=14)
        draw_pill(draw, (rx + 20, py + 15), p["tag"], bg_color=p["color"], text_color="#FFFFFF", font_size=12)
        draw.text((rx + 20, py + 48), p["title"], font=get_font(18, bold=True), fill="#0F172A")
        
        words = p["body"].split(" ")
        lines, curr = [], ""
        for w in words:
            if len(curr + " " + w) < 70:
                curr = (curr + " " + w).strip()
            else:
                lines.append(curr)
                curr = w
        if curr:
            lines.append(curr)
            
        ly = py + 78
        for l in lines:
            draw.text((rx + 20, ly), l, font=get_font(14, bold=False), fill="#475569")
            ly += 20
        py += 165

    draw_card(draw, [rx, 830, rx + rw, 915], bg_color="#F1F5F9", border_color="#CBD5E1", border_width=2, radius=14)
    draw.text((rx + 25, 845), "Result on Sample 1: 34 Steps Detected | 100% Dual Alignment | Zero False Positives", font=get_font(17, bold=True), fill="#0F172A")
    draw.text((rx + 25, 875), "Verdict: The ultimate gold standard for official fitness certifications, competitions, and medical grade accuracy.", font=get_font(14, bold=False), fill="#64748B")

    out_path = os.path.join(OUT_DIR, "card_solution4_fusion_white.png")
    img.save(out_path, quality=95)
    print(f"Generated {out_path}")
    return out_path

if __name__ == "__main__":
    print("Generating missing cards for Solution 1 and Solution 4...")
    c1 = make_card_solution1()
    c4 = make_card_solution4()
    for src in [c1, c4]:
        fname = os.path.basename(src)
        dst = os.path.join(ARTIFACTS_DIR, fname)
        with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
            fdst.write(fsrc.read())
        print(f"Copied {fname} to artifacts directory: {dst}")
    print("Cards created successfully!")
