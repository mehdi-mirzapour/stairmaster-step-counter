import asyncio
import time
import json
import argparse
from pathlib import Path
from typing import Optional

from .config import config
from .models import CompleteVideoAnalysis
from .frame_extractor import FrameExtractor
from .window_chunker import WindowChunker
from .vlm_client import VLMAnalyzer
from .overlap_reconciler import OverlapReconciler
from .logger import (
    console,
    print_banner,
    log_info,
    log_success,
    log_warning,
    log_error,
    log_step,
    log_window_result,
    print_metrics_table,
    print_steps_timeline,
)
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn


async def run_pipeline(
    video_path: Path,
    frames_dir: Path,
    output_json_path: Path,
    max_duration_sec: Optional[float] = None,
    model: Optional[str] = None,
) -> CompleteVideoAnalysis:
    """
    Executes the end-to-end Solution 1 pipeline on a single video file.
    """
    start_time = time.time()
    selected_model = model or config.openai_model
    video_path = Path(video_path).resolve()
    frames_dir = Path(frames_dir).resolve()
    output_json_path = Path(output_json_path).resolve()
    output_json_path.parent.mkdir(parents=True, exist_ok=True)

    print_banner(
        title=f"PROCESSING: {video_path.name.upper()}",
        subtitle=f"Model: {selected_model} | Target FPS: {config.sample_fps} | Output: {output_json_path.name}"
    )

    # -------------------------------------------------------------
    # Step 1: Video Ingestion & Frame Extraction
    # -------------------------------------------------------------
    log_step(1, "Frame Extraction & Downsampling")
    extractor = FrameExtractor(
        target_fps=config.sample_fps,
        max_dimension=config.image_max_size,
        jpeg_quality=config.image_jpeg_quality,
    )
    frames_meta = extractor.extract_frames(
        video_path=video_path,
        output_folder=frames_dir,
        max_duration_sec=max_duration_sec,
    )

    if not frames_meta:
        raise ValueError(f"No frames extracted from {video_path}")

    analyzed_duration = frames_meta[-1]["timestamp_sec"]

    # -------------------------------------------------------------
    # Step 2: Overlapping Window Chunking
    # -------------------------------------------------------------
    log_step(2, "Temporal Window Slicing with Overlap")
    chunker = WindowChunker(
        window_duration_sec=config.window_duration_sec,
        stride_sec=config.stride_sec,
    )
    chunks = chunker.create_chunks(frames_meta)
    log_info(
        f"Generated [bold yellow]{len(chunks)} overlapping windows[/bold yellow] "
        f"(Duration: {config.window_duration_sec}s, Stride: {config.stride_sec}s, Overlap: {config.overlap_sec}s)"
    )

    # -------------------------------------------------------------
    # Step 3: Parallel OpenAI Vision Inference
    # -------------------------------------------------------------
    log_step(3, f"Parallel VLM Inference via OpenAI ({selected_model})")
    analyzer = VLMAnalyzer(
        api_key=config.openai_api_key,
        model=selected_model,
        max_concurrency=config.max_concurrency,
    )

    raw_window_results = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="cyan", finished_style="bold green"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(f"[bold cyan]Submitting {len(chunks)} windows...", total=len(chunks))

        async def process_chunk(c):
            res = await analyzer.analyze_window(c)
            progress.advance(task)
            moving_leg = res.boundary_end.dominant_moving_leg.value if res.boundary_end else "N/A"
            log_window_result(
                window_id=c.window_id,
                start_sec=c.start_sec,
                end_sec=c.end_sec,
                steps_count=res.total_steps_in_window,
                moving_leg=moving_leg,
            )
            return res

        # Run concurrent batch
        raw_window_results = await asyncio.gather(*(process_chunk(c) for c in chunks))

    # Sort window results by ID
    raw_window_results.sort(key=lambda x: x.window_id)

    # -------------------------------------------------------------
    # Step 4: Overlap Reconciliation & Boundary Stitching
    # -------------------------------------------------------------
    log_step(4, "Boundary Deduplication & Step Reconciliation")
    reconciler = OverlapReconciler(
        coincidence_threshold_sec=config.overlap_coincidence_threshold_sec
    )
    deduplicated_steps, metrics = reconciler.reconcile(
        window_results=raw_window_results,
        total_duration_sec=analyzed_duration,
    )

    # -------------------------------------------------------------
    # Step 5: Structured JSON Export & Reporting
    # -------------------------------------------------------------
    log_step(5, "Structured JSON Export & Analytics")
    total_runtime = round(time.time() - start_time, 2)

    complete_analysis = CompleteVideoAnalysis(
        video_name=video_path.name,
        video_path=str(video_path),
        video_duration_sec=round(analyzed_duration, 2),
        analyzed_duration_sec=round(analyzed_duration, 2),
        total_frames_extracted=len(frames_meta),
        sampling_fps=config.sample_fps,
        windows_processed=len(chunks),
        window_duration_sec=config.window_duration_sec,
        overlap_duration_sec=config.overlap_sec,
        metrics=metrics,
        deduplicated_steps=deduplicated_steps,
        raw_window_results=raw_window_results,
        execution_time_sec=total_runtime,
    )

    # Save highly structured JSON
    with open(output_json_path, "w", encoding="utf-8") as f:
        f.write(complete_analysis.model_dump_json(indent=2))
    log_success(f"Saved complete structured JSON to: [bold underline cyan]{output_json_path}[/bold underline cyan]")

    # Also save a human-readable Markdown report
    report_md_path = output_json_path.with_suffix(".md")
    write_markdown_report(complete_analysis, report_md_path)
    log_success(f"Saved executive markdown report to: [bold underline green]{report_md_path}[/bold underline green]")

    # -------------------------------------------------------------
    # Display Rich Terminal Tables
    # -------------------------------------------------------------
    print_metrics_table(complete_analysis)
    print_steps_timeline(complete_analysis.deduplicated_steps, max_display=12)

    return complete_analysis


def write_markdown_report(analysis: CompleteVideoAnalysis, path: Path):
    """Writes an executive Markdown report for easy sharing and review."""
    m = analysis.metrics
    lines = [
        f"# Stairmaster Step Counter Analysis: {analysis.video_name}",
        f"",
        f"**Date/Time of Analysis:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Architecture:** Solution 1 — Overlapping Sliding-Window Multimodal VLM",
        f"",
        f"## 📊 Executive Summary",
        f"",
        f"| Metric | Value | Interpretation |",
        f"| :--- | :--- | :--- |",
        f"| **Total Steps** | **{m.total_steps}** | Verified stair ascents |",
        f"| **Left Leg Steps** | {m.left_steps} | Left foot plants |",
        f"| **Right Leg Steps** | {m.right_steps} | Right foot plants |",
        f"| **Cadence** | **{m.cadence_spm:.1f} SPM** | Steps per minute |",
        f"| **Mean Interval** | {m.mean_step_interval_sec:.2f} s | Avg time per step |",
        f"| **Bilateral Balance** | {m.symmetry_ratio:.2f} | 1.0 = Symmetrical |",
        f"| **Duration Analyzed** | {analysis.analyzed_duration_sec:.1f} s | Window duration: {analysis.window_duration_sec}s (overlap {analysis.overlap_duration_sec}s) |",
        f"| **Runtime** | {analysis.execution_time_sec:.2f} s | Parallel OpenAI processing |",
        f"",
        f"## ⏱️ Step-by-Step Chronological Timeline",
        f"",
        f"| Step # | Video Timestamp | Leg | Confidence | Windows | Visual Cue Description |",
        f"| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for s in analysis.deduplicated_steps:
        lines.append(
            f"| {s.global_step_id} | `{s.video_time_str}` | **{s.active_leg.value.upper()}** | {s.confidence*100:.0f}% | {s.source_window_ids} | {s.visual_cue} |"
        )

    lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Stairmaster Step Counter — Solution 1 VLM Pipeline")
    parser.add_argument(
        "--sample",
        choices=["1", "2", "all"],
        default="2",
        help="Which sample to run: 1 (sample1.mp4), 2 (sample2.mp4), or all",
    )
    parser.add_argument(
        "--max-duration",
        type=float,
        default=None,
        help="Optional max duration in seconds to analyze (useful for quick evaluation)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=config.openai_model,
        help="OpenAI model name (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--save-video",
        action="store_true",
        help="Generate annotated video with telemetry HUD",
    )

    args = parser.parse_args()

    samples_dir = config.samples_dir
    output_dir = config.output_dir

    tasks_to_run = []
    if args.sample in ["2", "all"]:
        tasks_to_run.append({
            "sample_num": "2",
            "video": samples_dir / "sample2.mp4",
            "frames": samples_dir / "frames2",
            "output": output_dir / "sample2_step_analysis.json",
            "video_out": output_dir / "solution1" / "sample2_annotated_hud.mp4" if args.save_video else None,
            "max_duration": args.max_duration,
        })
    if args.sample in ["1", "all"]:
        tasks_to_run.append({
            "sample_num": "1",
            "video": samples_dir / "sample1.mp4",
            "frames": samples_dir / "frames1",
            "output": output_dir / "sample1_step_analysis.json",
            "video_out": output_dir / "solution1" / "sample1_annotated_hud.mp4" if args.save_video else None,
            "max_duration": args.max_duration,
        })

    for t in tasks_to_run:
        res = asyncio.run(
            run_pipeline(
                video_path=t["video"],
                frames_dir=t["frames"],
                output_json_path=t["output"],
                max_duration_sec=t["max_duration"],
                model=args.model,
            )
        )
        if t["video_out"]:
            from .video_annotator import render_solution1_annotated_video
            render_solution1_annotated_video(
                video_path=t["video"],
                json_path=t["output"],
                output_video_path=t["video_out"],
                max_duration_sec=t["max_duration"],
            )


if __name__ == "__main__":
    main()
