import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.signal import find_peaks
from rich.console import Console
from rich.panel import Panel

console = Console()

BASE_DIR = Path(__file__).resolve().parent.parent
VIDEO_PATH = BASE_DIR / "samples" / "sample2.mp4"
OUTPUT_DIR = BASE_DIR / "output" / "verification"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def analyze_machine_kymograph():
    """
    Builds a Spatio-Temporal slice (Kymograph) across the stairs to count
    the physical revolving stair steps of the machine.
    """
    cap = cv2.VideoCapture(str(VIDEO_PATH))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    console.print(Panel(
        f"[bold cyan]ANALYZING PHYSICAL MACHINE STAIR STEPS[/bold cyan]\n"
        f"Video: {VIDEO_PATH.name} ({width}x{height}, {fps} FPS, {total_frames} frames)"
    ))
    
    # In sample2.mp4 (720x1280), the descending stair treads are clearly visible around:
    stair_x_min, stair_x_max = int(width * 0.48), int(width * 0.58)
    y_start, y_end = int(height * 0.46), int(height * 0.58) # y in [588, 742]
    
    kymograph = [] # Shape: (time, y_span)
    
    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        col_slice = gray[y_start:y_end, stair_x_min:stair_x_max].mean(axis=1)
        kymograph.append(col_slice)
        frame_idx += 1
        
    cap.release()
    kymo_arr = np.array(kymograph).T # Shape: (y_pixels, time_frames)
    
    # Track the periodic passage of step edges across a fixed horizontal reference line
    ref_y_idx = kymo_arr.shape[0] // 2
    temporal_profile = kymo_arr[ref_y_idx, :]
    
    # Smooth temporal profile
    from scipy.signal import savgol_filter
    temp_smooth = savgol_filter(temporal_profile, window_length=9, polyorder=2)
    
    # Peak detection of step edges crossing the reference line
    peaks, props = find_peaks(temp_smooth, distance=9, prominence=4)
    
    machine_steps_count = len(peaks)
    
    console.print(Panel(
        f"⚙️ [bold green]MACHINE PHYSICAL STEPS RESULT[/bold green]\n"
        f"• Total Physical Machine Steps Rotated: [bold yellow]{machine_steps_count}[/bold yellow] steps\n"
        f"• Video Duration: {total_frames/fps:.2f} s\n"
        f"• Machine Speed / Step Rate: [bold cyan]{(machine_steps_count / (total_frames/fps)) * 60:.1f} Steps/Min[/bold cyan]",
        border_style="green"
    ))
    
    # Plot Kymograph and Edge Crossing Signal
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    
    # Kymograph plot
    im = ax1.imshow(kymo_arr, cmap='gray', aspect='auto', extent=[0, total_frames/fps, y_end, y_start])
    ax1.axhline(y_start + ref_y_idx, color='red', linestyle='--', label='Virtual Machine Trigger Line')
    ax1.set_title("Machine Stairs Spatio-Temporal Kymograph (Diagonal Stripes = Descending Steps)", fontsize=13, fontweight='bold')
    ax1.set_ylabel("Vertical Pixel Y (Stairs Region)")
    ax1.legend(loc="upper right")
    
    # Edge Crossing Signal
    times = np.linspace(0, total_frames/fps, total_frames)
    ax2.plot(times, temp_smooth, color='blue', label="Luminance / Edge Profile at Trigger Line")
    ax2.scatter(times[peaks], temp_smooth[peaks], color='red', s=80, marker='x', label=f"Detected Machine Steps ({machine_steps_count})")
    ax2.set_title("Physical Step Edge Crossing Detections", fontsize=12)
    ax2.set_xlabel("Time (seconds)")
    ax2.set_ylabel("Intensity")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper right")
    
    plt.tight_layout()
    plot_path = OUTPUT_DIR / "sample2_machine_steps_kymograph.png"
    plt.savefig(plot_path, dpi=150)
    console.print(f"📊 Saved machine kymograph plot to: [bold underline]{plot_path}[/bold underline]")
    
    return machine_steps_count, peaks


if __name__ == "__main__":
    analyze_machine_kymograph()
