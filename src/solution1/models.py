from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class Leg(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    AMBIGUOUS = "ambiguous"


class StepAction(str, Enum):
    FOOT_PLANT = "foot_plant"
    PEAK_KNEE_LIFT = "peak_knee_lift"
    STEP_DRIVE = "step_drive"


class CyclePhase(str, Enum):
    SWING_UP = "swing_up"
    PEAK_FLEXION = "peak_flexion"
    FOOT_CONTACT = "foot_contact"
    DESCENDING_DRIVE = "descending_drive"
    PLANTED_EXTENSION = "planted_extension"


class WindowStepEvent(BaseModel):
    """A single step event detected within a window."""
    step_number_in_window: int = Field(description="Order of step in this window (1-indexed)")
    frame_index: int = Field(description="0-indexed frame number inside this window where step occurs")
    relative_timestamp_sec: float = Field(description="Time in seconds relative to the start of this window")
    active_leg: Leg = Field(description="Which leg performed the step (left or right)")
    action: StepAction = Field(description="Primary visual trigger detected (foot_plant, peak_knee_lift, step_drive)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")
    visual_cue: str = Field(description="Precise description of limb/step motion seen in this frame")


class BoundaryState(BaseModel):
    """Anatomical phase of the athlete at a window boundary (start or end)."""
    left_leg_phase: CyclePhase = Field(description="Phase of left leg at this boundary frame")
    right_leg_phase: CyclePhase = Field(description="Phase of right leg at this boundary frame")
    dominant_moving_leg: Leg = Field(description="Which leg is actively swinging or transitioning")
    summary: str = Field(description="Concise description of the body state at the boundary")


class WindowAnalysisResult(BaseModel):
    """The structured response schema returned by OpenAI for each temporal window."""
    window_id: int = Field(description="ID of the window analyzed")
    window_start_sec: float = Field(description="Start time of this window in the full video")
    window_end_sec: float = Field(description="End time of this window in the full video")
    frame_count: int = Field(description="Total number of frames passed to this window")
    steps_detected: List[WindowStepEvent] = Field(
        default_factory=list,
        description="List of all distinct steps completed in this window"
    )
    total_steps_in_window: int = Field(
        description="Total count of confirmed steps occurring in this window"
    )
    boundary_start: BoundaryState = Field(
        description="Posture and limb state at the first frame of the window"
    )
    boundary_end: BoundaryState = Field(
        description="Posture and limb state at the last frame of the window"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Any observations regarding camera angle, occlusions, or cadence"
    )


class DeduplicatedStep(BaseModel):
    """A reconciled global step event on the continuous video timeline."""
    global_step_id: int = Field(description="Continuous global step index (1, 2, 3...)")
    timestamp_sec: float = Field(description="Exact timestamp in video when step occurred")
    video_time_str: str = Field(description="Formatted timestamp (e.g. 00:01:23.45)")
    active_leg: Leg = Field(description="Leg that performed the step")
    confidence: float = Field(description="Merged confidence score")
    source_window_ids: List[int] = Field(description="Which window(s) detected this step")
    visual_cue: str = Field(description="Consolidated visual description")


class VideoCadenceMetrics(BaseModel):
    """Cadence and physiological metrics derived from step timestamps."""
    total_steps: int
    left_steps: int
    right_steps: int
    ambiguous_steps: int
    duration_analyzed_sec: float
    cadence_spm: float = Field(description="Average cadence in Steps Per Minute")
    mean_step_interval_sec: float = Field(description="Average seconds between consecutive steps")
    symmetry_ratio: float = Field(description="Ratio of left steps to right steps (1.0 = perfect symmetry)")


class CompleteVideoAnalysis(BaseModel):
    """Final comprehensive output saved to structured JSON."""
    video_name: str
    video_path: str
    video_duration_sec: float
    analyzed_duration_sec: float
    total_frames_extracted: int
    sampling_fps: float
    windows_processed: int
    window_duration_sec: float
    overlap_duration_sec: float
    metrics: VideoCadenceMetrics
    deduplicated_steps: List[DeduplicatedStep]
    raw_window_results: List[WindowAnalysisResult]
    execution_time_sec: float
