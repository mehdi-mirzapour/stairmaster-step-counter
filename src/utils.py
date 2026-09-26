from pathlib import Path
from typing import Optional, Any
import cv2
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent

def resolve_video_path(sample_num: int = 2, custom_path: Optional[str] = None) -> Path:
    """
    Resolves the video path prioritizing explicit paths, local/ folder, 
    and samples/ directory.
    """
    if custom_path:
        p = Path(custom_path)
        if not p.is_absolute():
            p = BASE_DIR / p
        if p.exists():
            return p
        raise FileNotFoundError(f"Requested video not found at: {p}")

    candidates = [
        BASE_DIR / "local" / "samples" / f"sample{sample_num}.mp4",
        BASE_DIR / "samples" / f"sample{sample_num}.mp4",
        BASE_DIR / "docs" / "assets" / "sample2_5s_annotated.mp4",
    ]

    for c in candidates:
        if c.exists():
            return c

    # Fallback explanation
    raise FileNotFoundError(
        f"Video for sample {sample_num} not found. Please place your video file in "
        f"'{BASE_DIR / 'local' / 'samples' / f'sample{sample_num}.mp4'}' "
        f"(git-ignored for privacy and repository lightness) or pass --video <path>."
    )


def anonymize_face(frame: np.ndarray, keypoints: Optional[Any] = None, min_y_cutoff: int = 270) -> np.ndarray:
    """
    Applies privacy-preserving Gaussian blur and anonymization tint to 
    the facial/head region, preventing facial identification in public releases.
    """
    h, w = frame.shape[:2]
    head_pts = []
    if keypoints is not None and len(keypoints) > 0:
        kpts = keypoints[0].cpu().numpy() if hasattr(keypoints[0], 'cpu') else keypoints[0]
        for k_i in range(min(5, len(kpts))):
            pt = kpts[k_i]
            if len(pt) >= 2 and pt[0] > 0 and pt[1] > 0:
                head_pts.append(pt)

    if head_pts:
        xs = [p[0] for p in head_pts]
        ys = [p[1] for p in head_pts]
        x1 = max(0, int(min(xs) - 45))
        x2 = min(w, int(max(xs) + 45))
        y1 = max(0, int(min(ys) - 50))
        y2 = min(h, int(max(ys) + 40))
    else:
        # Standard rear-view 3/4 climber head region fallback
        x1, y1, x2, y2 = 250, 45, 440, 260

    y2 = min(y2, min_y_cutoff)
    roi = frame[y1:y2, x1:x2]
    if roi.size > 0:
        blurred = cv2.GaussianBlur(roi, (51, 51), 30)
        tint = np.full_like(blurred, (20, 25, 35), dtype=np.uint8)
        frame[y1:y2, x1:x2] = cv2.addWeighted(blurred, 0.45, tint, 0.55, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (56, 189, 248), 1, cv2.LINE_AA)
        cv2.putText(frame, "PRIVACY ANONYMIZED", (x1 + 4, y2 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.32, (180, 220, 245), 1, cv2.LINE_AA)

    return frame
