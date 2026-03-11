"""
Log Analysis Tool for Subtitle Generator.

Reads structured logs (tasks.jsonl) and produces detailed reports on:
- Pipeline timing breakdown per step
- Per-segment transcription metrics
- Resource usage (CPU, RAM, GPU) over time
- Throughput analysis and bottleneck identification
- Anomaly detection (slow segments, resource spikes)

Usage:
    python analyze.py                     # Analyze most recent task
    python analyze.py <task_id>           # Analyze specific task
    python analyze.py --all               # Summary of all tasks
    python analyze.py --export <task_id>  # Export to JSON report
"""

import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent / "logs"
TASKS_LOG = LOG_DIR / "tasks.jsonl"
APP_LOG = LOG_DIR / "app.log"


def load_task_events(task_id: str = None) -> list[dict]:
    """Load events from tasks.jsonl, optionally filtered by task_id."""
    if not TASKS_LOG.exists():
        print("No task log found.")
        return []
    events = []
    with open(TASKS_LOG, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if task_id is None or entry.get("task_id", "").startswith(task_id):
                    events.append(entry)
            except json.JSONDecodeError:
                continue
    return events


def get_all_task_ids() -> list[str]:
    """Get unique task IDs from log."""
    ids = []
    seen = set()
    events = load_task_events()
    for e in events:
        tid = e.get("task_id", "")
        if tid and tid not in seen:
            seen.add(tid)
            ids.append(tid)
    return ids


def find_latest_task_id() -> str | None:
    """Find the most recent task ID."""
    ids = get_all_task_ids()
    return ids[-1] if ids else None


# ─────────────────────────────────────────────────────────────────────
# Report formatting helpers
# ─────────────────────────────────────────────────────────────────────

def fmt_time(sec: float) -> str:
    if sec < 0:
        return "N/A"
    if sec < 1:
        return f"{sec*1000:.0f}ms"
    if sec < 60:
        return f"{sec:.2f}s"
    m = int(sec // 60)
    s = sec % 60
    return f"{m}m {s:.1f}s"


def fmt_bytes(b: int) -> str:
    if b < 1024:
        return f"{b}B"
    elif b < 1024**2:
        return f"{b/1024:.1f}KB"
    elif b < 1024**3:
        return f"{b/1024**2:.1f}MB"
    else:
        return f"{b/1024**3:.2f}GB"


def bar_chart(value: float, total: float, width: int = 40) -> str:
    if total <= 0:
        return "." * width
    ratio = min(value / total, 1.0)
    filled = int(ratio * width)
    return "#" * filled + "." * (width - filled)


def separator(char="-", width=70):
    print(char * width)


def header(text: str, width=70):
    print()
    separator("=", width)
    print(f"  {text}")
    separator("=", width)


# ─────────────────────────────────────────────────────────────────────
# Analysis: Single task
# ─────────────────────────────────────────────────────────────────────

def analyze_task(task_id: str):
    """Full analysis of a single task."""
    events = load_task_events(task_id)
    if not events:
        print(f"No events found for task: {task_id}")
        return

    # Organize events by type
    by_event = defaultdict(list)
    for e in events:
        by_event[e["event"]].append(e)

    # Basic info
    upload = by_event.get("upload", [{}])[0]
    summary = by_event.get("pipeline_summary", [{}])[0]
    tx_profile = by_event.get("transcription_profile", [{}])[0]
    resource_mon = by_event.get("resource_monitor", [{}])[0]

    header(f"TASK ANALYSIS: {task_id[:8]}...")

    # ── Overview ──
    print(f"\n  File:          {upload.get('filename', '?')}")
    print(f"  Size:          {fmt_bytes(upload.get('size', 0))}")
    print(f"  Model:         {upload.get('model', '?')}")
    print(f"  Device:        {upload.get('device', '?').upper()}")
    print(f"  Status:        {summary.get('status', '?').upper()}")
    print(f"  Total Time:    {fmt_time(summary.get('total_time_sec', 0))}")
    print(f"  Audio:         {fmt_time(summary.get('audio_duration_sec', 0))}")
    print(f"  Upload Time:   {fmt_time(upload.get('upload_time_sec', 0))}")
    print(f"  Timestamp:     {upload.get('timestamp', '?')}")

    # ── Pipeline Breakdown ──
    step_timings = summary.get("step_timings", {})
    total_time = summary.get("total_time_sec", 0)
    if step_timings:
        header("PIPELINE BREAKDOWN")
        print(f"\n  {'Step':<20} {'Time':>10} {'%':>7}  {'Bar'}")
        separator()
        for step, dur in step_timings.items():
            pct = dur / total_time * 100 if total_time > 0 else 0
            print(f"  {step:<20} {fmt_time(dur):>10} {pct:>6.1f}%  [{bar_chart(dur, total_time)}]")
        separator()
        print(f"  {'TOTAL':<20} {fmt_time(total_time):>10} {'100.0':>6}%")

    # ── Step Resource Deltas ──
    step_events = [e for e in events if e["event"].startswith("step_")]
    if step_events:
        header("RESOURCE IMPACT PER STEP")
        print(f"\n  {'Step':<20} {'Duration':>10} {'RAM Delta':>10} {'GPU Delta':>10} {'CPU%':>7}")
        separator()
        for se in step_events:
            step_name = se.get("step", "?")
            dur = se.get("duration_sec", 0)
            ram_d = se.get("ram_delta_mb", 0)
            gpu_d = se.get("gpu_delta_mb", 0)
            cpu = se.get("cpu_percent", 0)
            ram_str = f"{ram_d:+.1f}MB"
            gpu_str = f"{gpu_d:+.1f}MB" if gpu_d else "--"
            print(f"  {step_name:<20} {fmt_time(dur):>10} {ram_str:>10} {gpu_str:>10} {cpu:>6.1f}%")
        separator()
        # Total RAM change
        if len(step_events) >= 2:
            ram_start = step_events[0].get("ram_before_mb", 0)
            ram_end = step_events[-1].get("ram_after_mb", 0)
            print(f"  RAM: {ram_start:.0f}MB -> {ram_end:.0f}MB (Delta {ram_end-ram_start:+.0f}MB)")

    # ── Transcription Profiling ──
    if tx_profile:
        header("TRANSCRIPTION ANALYSIS")
        print(f"\n  Segments:         {tx_profile.get('total_segments', '?')}")
        print(f"  Audio Duration:   {fmt_time(tx_profile.get('audio_duration_sec', 0))}")
        print(f"  Wall Time:        {fmt_time(tx_profile.get('wall_time_sec', 0))}")
        print(f"  Overall Speed:    {tx_profile.get('overall_speed_x', '?')}x realtime")
        print(f"  Mel Frames:       {tx_profile.get('total_mel_frames', '?')}")

        if "seg_duration_avg" in tx_profile:
            print("\n  Segment Duration:")
            print(f"    Average:        {tx_profile['seg_duration_avg']:.2f}s")
            print(f"    Min:            {tx_profile.get('seg_duration_min', '?')}s")
            print(f"    Max:            {tx_profile.get('seg_duration_max', '?')}s")

        if "seg_text_avg_chars" in tx_profile:
            print("\n  Text Output:")
            print(f"    Avg chars/seg:  {tx_profile['seg_text_avg_chars']:.0f}")
            print(f"    Total chars:    {tx_profile.get('seg_text_total_chars', '?')}")

        if "speed_mean_x" in tx_profile:
            print("\n  Throughput Stability:")
            print(f"    Mean speed:     {tx_profile['speed_mean_x']}x")
            print(f"    Speed range:    {tx_profile.get('speed_min_x', '?')}x -- {tx_profile.get('speed_max_x', '?')}x")
            print(f"    Std deviation:  {tx_profile.get('speed_std_x', '?')}x")
            cv = tx_profile.get("speed_cv", 0)
            stability = "Stable" if cv < 0.15 else "Moderate" if cv < 0.30 else "Unstable"
            print(f"    CV:             {cv:.3f} ({stability})")

    # ── Resource Monitor Summary ──
    if resource_mon and resource_mon.get("sample_count"):
        header("RESOURCE MONITORING")
        print(f"\n  Samples:          {resource_mon['sample_count']}")
        print(f"  Duration:         {fmt_time(resource_mon.get('duration_sec', 0))}")
        print("\n  CPU:")
        print(f"    Average:        {resource_mon.get('cpu_avg_percent', '?')}%")
        print(f"    Peak:           {resource_mon.get('cpu_peak_percent', '?')}%")
        print("\n  RAM (process):")
        print(f"    Average:        {resource_mon.get('ram_avg_mb', '?')}MB")
        print(f"    Peak:           {resource_mon.get('ram_peak_mb', '?')}MB")
        if resource_mon.get("gpu_peak_mb"):
            print("\n  GPU VRAM:")
            print(f"    Average:        {resource_mon.get('gpu_avg_mb', '?')}MB")
            print(f"    Peak:           {resource_mon.get('gpu_peak_mb', '?')}MB")

    # ── Bottleneck Analysis ──
    if step_timings and total_time > 0:
        header("BOTTLENECK ANALYSIS")
        sorted_steps = sorted(step_timings.items(), key=lambda x: x[1], reverse=True)
        bottleneck = sorted_steps[0]
        pct = bottleneck[1] / total_time * 100
        print(f"\n  Biggest bottleneck: {bottleneck[0]} ({pct:.1f}% of total)")

        if bottleneck[0] == "model_load" and pct > 30:
            print("  -> Model loading is dominant. For repeated use, the model")
            print("    stays cached. First run is slower due to download/load.")
        elif bottleneck[0] == "transcribe":
            audio_dur = summary.get("audio_duration_sec", 0)
            speed = audio_dur / bottleneck[1] if bottleneck[1] > 0 else 0
            print(f"  -> Transcription speed: {speed:.1f}x realtime")
            if upload.get("device", "").lower() == "cpu":
                print("  -> Consider using GPU (CUDA) for faster transcription")
            if upload.get("model", "") in ("large", "medium"):
                print("  -> Smaller model (tiny/base) is faster but less accurate")
        elif bottleneck[0] == "extract_audio" and pct > 20:
            print("  -> Audio extraction is slow -- large video or complex codec")

        # Overhead percentage (non-transcription time)
        overhead = total_time - step_timings.get("transcribe", 0)
        overhead_pct = overhead / total_time * 100
        print(f"\n  Pipeline overhead: {fmt_time(overhead)} ({overhead_pct:.1f}%)")
        print(f"  Pure transcription: {fmt_time(step_timings.get('transcribe', 0))} ({100-overhead_pct:.1f}%)")

    # ── Per-Segment Details ──
    # Load segment info from app.log SEG lines
    segments_from_log = load_segments_from_applog(task_id[:8])
    if segments_from_log:
        header("SEGMENT DETAILS")
        print(f"\n  {'#':<4} {'Time Range':<22} {'Duration':>8} {'Chars':>6}  {'Text (preview)'}")
        separator()
        for seg in segments_from_log:
            print(f"  {seg['index']:<4} [{seg['start']} -> {seg['end']}] {seg['duration']:>7.1f}s {seg['chars']:>5}  {seg['text'][:50]}")
        separator()
        print(f"  Total: {len(segments_from_log)} segments")

    print()


def load_segments_from_applog(short_id: str) -> list[dict]:
    """Parse SEG lines from app.log for a given task."""
    if not APP_LOG.exists():
        return []
    segments = []
    import re
    seg_pattern = re.compile(
        rf"SEG \[{re.escape(short_id)}\] #(\d+) "
        rf"\[(.+?) -> (.+?)\] dur=([\d.]+)s chars=(\d+) .+?\| \"(.+?)\""
    )
    with open(APP_LOG, "r", encoding="utf-8") as f:
        for line in f:
            m = seg_pattern.search(line)
            if m:
                segments.append({
                    "index": int(m.group(1)),
                    "start": m.group(2),
                    "end": m.group(3),
                    "duration": float(m.group(4)),
                    "chars": int(m.group(5)),
                    "text": m.group(6),
                })
    return segments


# ─────────────────────────────────────────────────────────────────────
# Analysis: All tasks summary
# ─────────────────────────────────────────────────────────────────────

def analyze_all():
    """Summary table of all tasks."""
    all_ids = get_all_task_ids()
    if not all_ids:
        print("No tasks found in log.")
        return

    header(f"ALL TASKS SUMMARY ({len(all_ids)} tasks)")
    print(f"\n  {'ID':<10} {'File':<25} {'Model':<8} {'Device':<6} {'Status':<10} {'Time':>8} {'Audio':>8} {'Speed':>7}")
    separator("-", 100)

    for tid in all_ids:
        events = load_task_events(tid)
        by_event = defaultdict(list)
        for e in events:
            by_event[e["event"]].append(e)

        upload = by_event.get("upload", [{}])[0]
        summary = by_event.get("pipeline_summary", [{}])[0]
        tx = by_event.get("transcription_complete", [{}])[0]

        filename = upload.get("filename", "?")[:24]
        model = upload.get("model", "?")
        device = upload.get("device", "?")
        status = summary.get("status", "?")
        total = summary.get("total_time_sec", 0)
        audio = summary.get("audio_duration_sec", 0)
        speed = tx.get("speed_factor", 0)

        print(
            f"  {tid[:8]:<10} {filename:<25} {model:<8} {device:<6} "
            f"{status:<10} {fmt_time(total):>8} {fmt_time(audio):>8} {speed:>6.1f}x"
        )
    separator("-", 100)


# ─────────────────────────────────────────────────────────────────────
# Export to JSON
# ─────────────────────────────────────────────────────────────────────

def export_task(task_id: str):
    """Export all events for a task as a structured JSON report."""
    events = load_task_events(task_id)
    if not events:
        print(f"No events for task: {task_id}")
        return

    report_path = LOG_DIR / f"report_{task_id[:8]}.json"
    report = {
        "task_id": task_id,
        "generated_at": datetime.now().isoformat(),
        "events": events,
        "segments": load_segments_from_applog(task_id[:8]),
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Report exported to: {report_path}")
    print(f"Events: {len(events)}, Segments: {len(report['segments'])}")


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]

    if not args:
        # Analyze most recent task
        tid = find_latest_task_id()
        if tid:
            analyze_task(tid)
        else:
            print("No tasks found. Run a transcription first.")
    elif args[0] == "--all":
        analyze_all()
    elif args[0] == "--export":
        tid = args[1] if len(args) > 1 else find_latest_task_id()
        if tid:
            export_task(tid)
        else:
            print("No task found.")
    else:
        analyze_task(args[0])


if __name__ == "__main__":
    main()
