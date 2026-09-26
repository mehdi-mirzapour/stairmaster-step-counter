import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Solution1Config(BaseSettings):
    """Configuration for Solution 1: Overlapping Sliding-Window Multimodal VLM"""

    # OpenAI Settings
    openai_api_key: str = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", "")
    )
    openai_model: str = Field(
        default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    )

    # Sampling & Temporal Window Settings
    sample_fps: float = Field(
        default=8.0,
        description="Sampling rate in frames per second. 8 FPS captures rapid cardio up to 160 SPM.",
    )
    window_duration_sec: float = Field(
        default=3.0,
        description="Length of each temporal window in seconds (24 frames at 8 FPS).",
    )
    stride_sec: float = Field(
        default=2.0,
        description="Time shift between successive windows (8 frames at 4 FPS).",
    )
    overlap_sec: float = Field(
        default=1.0,
        description="Overlap between adjacent windows (4 frames at 4 FPS).",
    )

    # Concurrency & Image Quality
    max_concurrency: int = Field(
        default=6,
        description="Maximum concurrent OpenAI API requests.",
    )
    image_max_size: int = Field(
        default=640,
        description="Max dimension for frames to optimize API token cost and latency.",
    )
    image_jpeg_quality: int = Field(
        default=85,
        description="JPEG compression quality for API payload.",
    )

    # Reconciliation Settings
    overlap_coincidence_threshold_sec: float = Field(
        default=0.35,
        description="Time tolerance to merge duplicate step detections in the overlap zone.",
    )

    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent.parent
    samples_dir: Path = base_dir / "samples"
    output_dir: Path = base_dir / "output"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


config = Solution1Config()
