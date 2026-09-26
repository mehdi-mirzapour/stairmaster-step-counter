import sys
import json
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from src.machine_step_tracker import MachineStepTracker

console = Console()
BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLES_DIR = BASE_DIR / "samples"
OUTPUT_DIR = BASE_DIR / "output"


def run():
    tracker = MachineStepTracker()
    
    # 1. Run on sample2.mp4
    res2 = tracker.count_machine_steps(SAMPLES_DIR / "sample2.mp4")
    
    table2 = Table(title="⚙️ Machine Physical Steps: sample2.mp4", border_style="cyan")
    table2.add_column("Step #", style="bold white", width=8)
    table2.add_column("Frame", style="yellow", width=12)
    table2.add_column("Timestamp", style="bold green", width=14)
    table2.add_column("Time Str", style="cyan", width=12)
    
    for s in res2["steps"]:
        table2.add_row(f"{s['machine_step_id']:02d}", f"Frame #{s['frame']:03d}", f"{s['timestamp_sec']}s", s["time_str"])
    console.print(table2)
    
    console.print(Panel(
        f"🏁 [bold green]SAMPLE2 RESULT[/bold green]\n"
        f"• Machine Physical Steps Counted: [bold yellow]{res2['total_machine_steps']}[/bold yellow] steps\n"
        f"• Cadence: [bold cyan]{res2['cadence_spm']} Steps/Min[/bold cyan]\n"
        f"• Duration: {res2['duration_sec']} s",
        border_style="green"
    ))
    
    # Save JSON
    with open(OUTPUT_DIR / "sample2_machine_steps.json", "w") as f:
        json.dump(res2, f, indent=2)


if __name__ == "__main__":
    run()
