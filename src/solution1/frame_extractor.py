import cv2
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image
from .logger import log_info, log_success, console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn


class FrameExtractor:
    """Extracts decimated frames from video files into designated directories."""

    def __init__(self, target_fps: float = 4.0, max_dimension: int = 640, jpeg_quality: int = 85):
        self.target_fps = target_fps
        self.max_dimension = max_dimension
        self.jpeg_quality = jpeg_quality

    def extract_frames(
        self,
        video_path: Path,
        output_folder: Path,
        max_duration_sec: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Extracts frames at target_fps and stores them in output_folder.
        Returns a list of dictionaries with frame metadata.
        """
        video_path = Path(video_path)
        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise FileNotFoundError(f"Could not open video file: {video_path}")

        native_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_native_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        native_duration_sec = total_native_frames / native_fps if native_fps > 0 else 0.0

        limit_duration = min(native_duration_sec, max_duration_sec) if max_duration_sec else native_duration_sec
        log_info(
            f"Extracting frames from [bold cyan]{video_path.name}[/bold cyan] "
            f"({native_fps:.1f} native FPS, total duration {native_duration_sec:.1f}s, analyzing {limit_duration:.1f}s) "
            f"at target [bold green]{self.target_fps:.1f} FPS[/bold green]"
        )

        frame_step = native_fps / self.target_fps
        extracted_metadata: List[Dict[str, Any]] = []

        target_timestamps = []
        t = 0.0
        while t < limit_duration:
            target_timestamps.append(t)
            t += 1.0 / self.target_fps

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="green", finished_style="bold green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"[cyan]Extracting to {output_folder.name}/", total=len(target_timestamps))

            current_target_idx = 0
            native_frame_idx = 0

            while cap.isOpened() and current_target_idx < len(target_timestamps):
                ret, frame = cap.read()
                if not ret:
                    break

                current_time = native_frame_idx / native_fps
                target_time = target_timestamps[current_target_idx]

                if current_time >= target_time:
                    # Convert BGR (OpenCV) to RGB (PIL)
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(frame_rgb)

                    # Resize maintaining aspect ratio
                    w, h = pil_img.size
                    if max(w, h) > self.max_dimension:
                        if w > h:
                            new_w = self.max_dimension
                            new_h = int(h * (self.max_dimension / w))
                        else:
                            new_h = self.max_dimension
                            new_w = int(w * (self.max_dimension / h))
                        pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

                    frame_filename = f"frame_{current_target_idx + 1:05d}.jpg"
                    frame_filepath = output_folder / frame_filename
                    pil_img.save(frame_filepath, "JPEG", quality=self.jpeg_quality)

                    extracted_metadata.append({
                        "frame_id": current_target_idx + 1,
                        "native_frame_index": native_frame_idx,
                        "timestamp_sec": round(target_time, 3),
                        "file_path": str(frame_filepath),
                        "width": pil_img.width,
                        "height": pil_img.height,
                    })

                    current_target_idx += 1
                    progress.advance(task)

                native_frame_idx += 1

        cap.release()
        log_success(f"Extracted {len(extracted_metadata)} frames to [bold yellow]{output_folder}[/bold yellow]")
        return extracted_metadata
