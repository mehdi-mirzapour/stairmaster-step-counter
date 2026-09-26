"""
Solution 5: Acoustic Impact Step Counter (Audio DSP).
Detects footstrike transients via bandpass filtering (60-350Hz) and adaptive envelope analysis.
"""

from .pipeline import AudioStepCounter
from .video_annotator import render_solution5_annotated_video

__all__ = ["AudioStepCounter", "render_solution5_annotated_video"]
