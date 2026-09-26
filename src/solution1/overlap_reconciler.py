from typing import List, Dict, Any
from .models import (
    WindowAnalysisResult,
    DeduplicatedStep,
    VideoCadenceMetrics,
    Leg,
)
from .logger import log_info, log_success


def format_seconds_to_time_str(seconds: float) -> str:
    """Formats float seconds to MM:SS.SS"""
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins:02d}:{secs:05.2f}"


class OverlapReconciler:
    """
    Reconciles, stitches, and deduplicates step events detected across
    adjacent, overlapping temporal windows.
    """

    def __init__(self, coincidence_threshold_sec: float = 0.35):
        self.coincidence_threshold = coincidence_threshold_sec

    def reconcile(
        self,
        window_results: List[WindowAnalysisResult],
        total_duration_sec: float,
    ) -> (List[DeduplicatedStep], VideoCadenceMetrics):
        """
        Takes raw results from all windows and produces a unified, deduplicated
        sequence of global steps with calculated cadence metrics.
        """
        # Collect all raw step events with absolute timestamps
        candidates = []
        for w in window_results:
            for step in w.steps_detected:
                abs_t = round(w.window_start_sec + step.relative_timestamp_sec, 3)
                candidates.append({
                    "window_id": w.window_id,
                    "absolute_timestamp_sec": abs_t,
                    "active_leg": step.active_leg,
                    "action": step.action,
                    "confidence": step.confidence,
                    "visual_cue": step.visual_cue,
                })

        # Sort all candidates strictly chronologically
        candidates.sort(key=lambda x: x["absolute_timestamp_sec"])

        deduplicated: List[DeduplicatedStep] = []
        global_step_counter = 1

        for cand in candidates:
            t = cand["absolute_timestamp_sec"]
            leg = cand["active_leg"]
            conf = cand["confidence"]
            w_id = cand["window_id"]
            cue = cand["visual_cue"]

            if not deduplicated:
                # First step registered
                deduplicated.append(
                    DeduplicatedStep(
                        global_step_id=global_step_counter,
                        timestamp_sec=t,
                        video_time_str=format_seconds_to_time_str(t),
                        active_leg=leg,
                        confidence=conf,
                        source_window_ids=[w_id],
                        visual_cue=cue,
                    )
                )
                global_step_counter += 1
                continue

            last_step = deduplicated[-1]
            time_diff = abs(t - last_step.timestamp_sec)

            # Check if this candidate is a duplicate from an overlapping window
            is_same_leg = (leg == last_step.active_leg) or (leg == Leg.AMBIGUOUS) or (last_step.active_leg == Leg.AMBIGUOUS)
            
            # Deduplication rules for rapid cadence (up to 150 SPM, ~0.4s between alternating steps):
            # 1. Same leg detected within 0.28s in overlapping windows -> DUPLICATE of same foot plant
            # 2. Any detection within 0.18s of previous step -> DUPLICATE (physiological minimum for distinct steps)
            is_duplicate = (is_same_leg and time_diff <= 0.28) or (time_diff < 0.18)
            
            if is_duplicate:
                # Merge duplicate step event across window boundary
                if w_id not in last_step.source_window_ids:
                    last_step.source_window_ids.append(w_id)
                # Weighted or higher confidence update
                if conf > last_step.confidence:
                    last_step.confidence = conf
                    last_step.timestamp_sec = round((last_step.timestamp_sec + t) / 2.0, 3)
                    last_step.video_time_str = format_seconds_to_time_str(last_step.timestamp_sec)
                    if leg != Leg.AMBIGUOUS:
                        last_step.active_leg = leg
                    last_step.visual_cue = cue
            else:
                # Verified new distinct step
                deduplicated.append(
                    DeduplicatedStep(
                        global_step_id=global_step_counter,
                        timestamp_sec=t,
                        video_time_str=format_seconds_to_time_str(t),
                        active_leg=leg,
                        confidence=conf,
                        source_window_ids=[w_id],
                        visual_cue=cue,
                    )
                )
                global_step_counter += 1

        # Calculate Cadence and Biomechanical Metrics
        total_steps = len(deduplicated)
        left_steps = sum(1 for s in deduplicated if s.active_leg == Leg.LEFT)
        right_steps = sum(1 for s in deduplicated if s.active_leg == Leg.RIGHT)
        ambiguous_steps = sum(1 for s in deduplicated if s.active_leg == Leg.AMBIGUOUS)

        duration = max(total_duration_sec, 0.1)
        cadence_spm = round((total_steps / duration) * 60.0, 2)
        mean_interval = round(duration / total_steps, 3) if total_steps > 0 else 0.0
        symmetry = round(left_steps / right_steps, 2) if right_steps > 0 else 1.0

        metrics = VideoCadenceMetrics(
            total_steps=total_steps,
            left_steps=left_steps,
            right_steps=right_steps,
            ambiguous_steps=ambiguous_steps,
            duration_analyzed_sec=round(duration, 2),
            cadence_spm=cadence_spm,
            mean_step_interval_sec=mean_interval,
            symmetry_ratio=symmetry,
        )

        log_success(
            f"Reconciliation Complete: {len(candidates)} raw window events deduplicated into "
            f"[bold green]{total_steps} verified global steps[/bold green] "
            f"([cyan]{left_steps} Left[/cyan], [magenta]{right_steps} Right[/magenta], Cadence: {cadence_spm} SPM)"
        )

        return deduplicated, metrics
