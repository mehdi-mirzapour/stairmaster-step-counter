import base64
import asyncio
from pathlib import Path
from typing import List
from openai import AsyncOpenAI
from .models import WindowAnalysisResult
from .window_chunker import WindowChunk
from .logger import log_info, log_error, log_warning


class VLMAnalyzer:
    """Sends image frame sequences to OpenAI Vision with Structured Outputs."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", max_concurrency: int = 6):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.semaphore = asyncio.Semaphore(max_concurrency)

    @staticmethod
    def encode_image(image_path: str) -> str:
        """Reads and base64 encodes an image file."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    async def analyze_window(self, chunk: WindowChunk) -> WindowAnalysisResult:
        """
        Submits an overlapping window of frames to OpenAI Vision.
        """
        async with self.semaphore:
            # Build multi-image content
            content = [
                {
                    "type": "text",
                    "text": (
                        f"You are an expert biomechanics computer vision analyzer. "
                        f"You are observing an athlete on a continuous stair climber / Stairmaster. "
                        f"This window contains {chunk.frame_count} sequential frames spanning from "
                        f"{chunk.start_sec:.2f}s to {chunk.end_sec:.2f}s (sampled at {chunk.frame_count / max(chunk.end_sec - chunk.start_sec, 0.1):.1f} FPS).\n\n"
                        f"CRITICAL BIOMECHANICAL DEFINITIONS & ACCURATE CADENCE COUNTING:\n"
                        f"1. A STEP occurs whenever a foot finishes swinging forward/up and makes NEW CONTACT / PLANT on a descending stair step.\n"
                        f"2. ATHLETE CADENCE: This athlete is performing rapid cardio climbing at high speed (~120 to 150 steps per minute, or ~6 to 8 steps per 3-second window!). "
                        f"A step occurs roughly every 0.40 to 0.45 seconds.\n"
                        f"3. Alternation: Steps strictly alternate between LEFT and RIGHT foot (Left -> Right -> Left -> Right).\n"
                        f"4. For each genuine NEW foot plant, identify the exact frame_index and timestamp.\n"
                        f"5. Report boundary_start and boundary_end limb postures accurately to enable seamless stitching with adjacent windows."
                    )
                }
            ]

            for idx, frame_meta in enumerate(chunk.frames):
                b64_data = self.encode_image(frame_meta["file_path"])
                t_sec = frame_meta["timestamp_sec"] - chunk.start_sec
                content.append({
                    "type": "text",
                    "text": f"Frame #{idx} [t=+{t_sec:.2f}s | video_t={frame_meta['timestamp_sec']:.2f}s]:"
                })
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{b64_data}",
                        "detail": "low"  # low detail is fast, cost-effective and highly accurate for posture
                    }
                })

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = await self.client.beta.chat.completions.parse(
                        model=self.model,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are a strict, precise biomechanics sports tracking system. "
                                    "Analyze the provided image frames and return structured data conforming to the schema."
                                )
                            },
                            {
                                "role": "user",
                                "content": content
                            }
                        ],
                        response_format=WindowAnalysisResult,
                        temperature=0.1,
                    )
                    
                    parsed: WindowAnalysisResult = response.choices[0].message.parsed
                    # Enforce window IDs and timestamps match our chunk
                    parsed.window_id = chunk.window_id
                    parsed.window_start_sec = chunk.start_sec
                    parsed.window_end_sec = chunk.end_sec
                    parsed.frame_count = chunk.frame_count
                    return parsed

                except Exception as e:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        log_warning(f"Retry {attempt + 1}/{max_retries} for Window #{chunk.window_id}: {str(e)[:80]}")
                    else:
                        log_error(f"Failed to analyze Window #{chunk.window_id}: {e}")
                        raise e
