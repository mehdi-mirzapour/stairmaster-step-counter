from typing import List, Dict, Any
from pydantic import BaseModel, Field


class WindowChunk(BaseModel):
    """Represents an overlapping temporal window of video frames."""
    window_id: int
    start_sec: float
    end_sec: float
    frames: List[Dict[str, Any]]
    frame_count: int
    overlap_prev_sec: float = 0.0
    overlap_next_sec: float = 0.0
    is_first: bool = False
    is_last: bool = False


class WindowChunker:
    """Slices sequential video frames into overlapping temporal windows."""

    def __init__(self, window_duration_sec: float = 3.0, stride_sec: float = 2.0):
        self.window_duration = window_duration_sec
        self.stride = stride_sec
        self.overlap = max(0.0, window_duration_sec - stride_sec)

    def create_chunks(self, frames: List[Dict[str, Any]]) -> List[WindowChunk]:
        """
        Groups frames into overlapping windows based on timestamps.
        """
        if not frames:
            return []

        total_duration = frames[-1]["timestamp_sec"]
        chunks: List[WindowChunk] = []

        window_start = 0.0
        window_idx = 0

        while window_start < total_duration:
            window_end = window_start + self.window_duration
            
            # Select all frames whose timestamp falls inside [window_start, window_end]
            window_frames = [
                f for f in frames
                if window_start <= f["timestamp_sec"] <= window_end
            ]

            # In case the video ends and we have very few frames, ensure at least 2 frames
            if len(window_frames) >= 2:
                chunk = WindowChunk(
                    window_id=window_idx,
                    start_sec=round(window_start, 3),
                    end_sec=round(min(window_end, total_duration), 3),
                    frames=window_frames,
                    frame_count=len(window_frames),
                    overlap_prev_sec=round(self.overlap, 3) if window_idx > 0 else 0.0,
                    overlap_next_sec=round(self.overlap, 3) if (window_start + self.stride < total_duration) else 0.0,
                    is_first=(window_idx == 0),
                    is_last=(window_start + self.stride >= total_duration),
                )
                chunks.append(chunk)

            if window_start + self.stride >= total_duration:
                break

            window_start += self.stride
            window_idx += 1

        if chunks:
            chunks[-1].is_last = True

        return chunks
