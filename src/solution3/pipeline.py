import json
import time
import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from src.machine_step_tracker import MachineStepTracker

console = Console()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SAMPLES_DIR = BASE_DIR / "samples"
OUTPUT_DIR = BASE_DIR / "output" / "solution3"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_solution3(video_path: Path, output_json: Path, max_duration_sec: float = None):
    tracker = MachineStepTracker()
    start_time = time.time()
    res = tracker.count_machine_steps(video_path=video_path, max_duration_sec=max_duration_sec)
    runtime = round(time.time() - start_time, 3)
    res["solution"] = "Solution 3: Physical Machine Step Tracker (Kymograph)"
    res["runtime_sec"] = runtime

    table = Table(title=f"⚙️ Solution 3 (Physical Machine Steps): {video_path.name}", border_style="green")
    table.add_column("Step #", style="bold white", width=8)
    table.add_column("Frame", style="yellow", width=12)
    table.add_column("Timestamp", style="bold green", width=14)
    table.add_column("Time Str", style="cyan", width=12)

    for s in res["steps"][:15]:
        table.add_row(f"{s['machine_step_id']:02d}", f"Frame #{s['frame']:03d}", f"{s['timestamp_sec']}s", s["time_str"])
    if len(res["steps"]) > 15:
        table.add_row("...", "...", "...", f"+ {len(res['steps'])-15} more logged")

    console.print(table)

    console.print(Panel(
        f"🏁 [bold green]SOLUTION 3 SUMMARY: {video_path.name}[/bold green]\n"
        f"• Machine Physical Steps Counted: [bold yellow]{res['total_machine_steps']}[/bold yellow] steps\n"
        f"• Machine Cadence: [bold cyan]{res['cadence_spm']} Steps/Min[/bold cyan]\n"
        f"• Duration: {res['duration_sec']} s\n"
        f"• Processing Time: [bold magenta]{runtime:.3f} s[/bold magenta] (ultra-fast edge)",
        border_style="green"
    ))

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    console.print(f"[bold green]✔ Saved structured JSON to:[/bold green] {output_json}")
    return res


from src.utils import resolve_video_path

def main():
    parser = argparse.ArgumentParser(description="Solution 3: Physical Machine Step Tracker")
    parser.add_argument("--video", type=str, default=None, help="Custom path to input video file")
    parser.add_argument("--sample", choices=["1", "2"], default="2", help="Standard sample index (default: 2)")
    parser.add_argument("--max-duration", type=float, default=5.0, help="Max duration in seconds (default: 5.0)")
    parser.add_argument("--save-video", action="store_true", help="Generate annotated video with telemetry HUD")

    args = parser.parse_args()

    video_file = resolve_video_path(sample_num=int(args.sample), custom_path=args.video)
    json_out = OUTPUT_DIR / f"sample{args.sample}_machine_steps.json"
    video_out = OUTPUT_DIR / f"sample{args.sample}_annotated_hud.mp4" if args.save_video else None

    run_solution3(video_file, json_out, args.max_duration)
    if video_out:
        from .video_annotator import render_solution3_annotated_video
        render_solution3_annotated_video(
            video_path=video_file,
            json_path=json_out,
            output_video_path=video_out,
            max_duration_sec=args.max_duration,
        )


if __name__ == "__main__":
    main()
