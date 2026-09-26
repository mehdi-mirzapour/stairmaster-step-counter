from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from typing import List
from .models import CompleteVideoAnalysis, DeduplicatedStep

console = Console()


def print_banner(title: str = "STAIRMASTER VLM STEP COUNTER", subtitle: str = "Solution 1: Overlapping Sliding-Window Multimodal Inference"):
    """Prints a stylish, high-tech banner."""
    content = Text()
    content.append("⚡ ", style="bold yellow")
    content.append(title, style="bold cyan")
    content.append("\n" + subtitle, style="dim white")
    
    panel = Panel(
        content,
        box=box.DOUBLE_EDGE,
        border_style="bright_blue",
        padding=(1, 2),
    )
    console.print(panel)


def log_info(msg: str):
    console.print(f"[bold cyan]ℹ [INFO][/bold cyan] {msg}")


def log_success(msg: str):
    console.print(f"[bold green]✔ [SUCCESS][/bold green] {msg}")


def log_warning(msg: str):
    console.print(f"[bold yellow]⚠ [WARNING][/bold yellow] {msg}")


def log_error(msg: str):
    console.print(f"[bold red]✖ [ERROR][/bold red] {msg}")


def log_step(step_num: int, title: str):
    console.print(f"\n[bold magenta]─── STEP {step_num}: {title.upper()} ───[/bold magenta]")


def log_window_result(window_id: int, start_sec: float, end_sec: float, steps_count: int, moving_leg: str):
    console.print(
        f"  [dim]Window #{window_id:02d}[/dim] "
        f"[cyan][{start_sec:5.2f}s ➜ {end_sec:5.2f}s][/cyan] "
        f"Steps: [bold green]{steps_count}[/bold green] | "
        f"Active: [yellow]{moving_leg}[/yellow]"
    )


def print_metrics_table(analysis: CompleteVideoAnalysis):
    """Prints a beautiful summary table of the video analysis."""
    table = Table(
        title=f"📊 Workout Telemetry & Cadence: {analysis.video_name}",
        box=box.ROUNDED,
        header_style="bold bright_cyan",
        border_style="blue",
    )

    table.add_column("Metric", style="bold white", width=28)
    table.add_column("Value", style="bold green", width=22)
    table.add_column("Interpretation / Benchmark", style="dim white", width=36)

    m = analysis.metrics
    table.add_row("Total Steps Counted", f"[bold yellow]{m.total_steps} steps[/bold yellow]", "Total completed stair ascents")
    table.add_row("Left Foot Steps", f"{m.left_steps} steps", "Left leg drive cycles")
    table.add_row("Right Foot Steps", f"{m.right_steps} steps", "Right leg drive cycles")
    table.add_row("Bilateral Symmetry", f"{m.symmetry_ratio:.2f}", "1.00 = Perfect balance (L/R)")
    table.add_row("Workout Cadence", f"[bold cyan]{m.cadence_spm:.1f} SPM[/bold cyan]", "Steps Per Minute (Norm: 40-120)")
    table.add_row("Mean Step Interval", f"{m.mean_step_interval_sec:.2f} s", "Time between consecutive foot plants")
    table.add_row("Analyzed Duration", f"{analysis.analyzed_duration_sec:.1f} s", f"Extracted from {analysis.video_duration_sec:.1f}s")
    table.add_row("Windows Evaluated", f"{analysis.windows_processed}", f"Duration {analysis.window_duration_sec}s, Overlap {analysis.overlap_duration_sec}s")
    table.add_row("Inference Runtime", f"[magenta]{analysis.execution_time_sec:.2f} s[/magenta]", "Parallel async OpenAI execution")

    console.print(table)


def print_steps_timeline(steps: List[DeduplicatedStep], max_display: int = 15):
    """Prints a formatted timeline table of the detected steps."""
    table = Table(
        title="⏱️ Reconciled Step Timeline (First Sequence)",
        box=box.SIMPLE_HEAVY,
        header_style="bold bright_yellow",
        border_style="dim blue",
    )

    table.add_column("#", style="dim", width=4)
    table.add_column("Timestamp", style="bold cyan", width=12)
    table.add_column("Leg", style="bold", width=8)
    table.add_column("Confidence", style="green", width=12)
    table.add_column("Source Windows", style="dim", width=16)
    table.add_column("Visual Kinematic Cue", style="white", width=42)

    for step in steps[:max_display]:
        leg_color = "bright_blue" if step.active_leg.value == "left" else "bright_magenta"
        leg_str = f"[{leg_color}]{step.active_leg.value.upper()}[/{leg_color}]"
        
        table.add_row(
            f"{step.global_step_id:02d}",
            f"{step.video_time_str}",
            leg_str,
            f"{step.confidence * 100:.0f}%",
            f"W: {step.source_window_ids}",
            step.visual_cue[:40] + ("..." if len(step.visual_cue) > 40 else ""),
        )

    if len(steps) > max_display:
        table.add_row("...", "...", "...", "...", "...", f"[dim]+ {len(steps) - max_display} more steps logged in JSON[/dim]")

    console.print(table)
