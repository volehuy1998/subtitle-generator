"""
Comprehensive profiling and logging module for Subtitle Generator.

Tracks:
- System resources: CPU%, RAM, disk I/O
- GPU: utilization, VRAM, temperature
- Per-step timing with nanosecond precision
- Per-segment transcription metrics
- I/O throughput (upload, ffmpeg, disk writes)
- Aggregated statistics and summaries
"""

import logging
import time
import threading

import psutil
import torch

logger = logging.getLogger("subtitle-generator")

# ---------------------------------------------------------------------------
# System snapshot
# ---------------------------------------------------------------------------

def snapshot_system() -> dict:
    """Capture a point-in-time snapshot of system resources."""
    proc = psutil.Process()
    mem = psutil.virtual_memory()
    cpu_freq = psutil.cpu_freq()

    snap = {
        "timestamp": time.time(),
        # CPU
        "cpu_percent": psutil.cpu_percent(interval=0),
        "cpu_freq_mhz": round(cpu_freq.current, 0) if cpu_freq else None,
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        # Process
        "proc_cpu_percent": proc.cpu_percent(interval=0),
        "proc_rss_mb": round(proc.memory_info().rss / 1024 / 1024, 1),
        "proc_vms_mb": round(proc.memory_info().vms / 1024 / 1024, 1),
        "proc_threads": proc.num_threads(),
        # System RAM
        "ram_total_gb": round(mem.total / 1024**3, 1),
        "ram_used_gb": round(mem.used / 1024**3, 1),
        "ram_available_gb": round(mem.available / 1024**3, 1),
        "ram_percent": mem.percent,
    }

    # Disk I/O counters
    try:
        disk = psutil.disk_io_counters()
        if disk:
            snap["disk_read_mb"] = round(disk.read_bytes / 1024**2, 1)
            snap["disk_write_mb"] = round(disk.write_bytes / 1024**2, 1)
    except Exception:
        pass

    # GPU
    if torch.cuda.is_available():
        snap.update(snapshot_gpu())

    return snap


def snapshot_gpu() -> dict:
    """Capture GPU-specific metrics."""
    if not torch.cuda.is_available():
        return {}
    try:
        allocated = torch.cuda.memory_allocated(0)
        reserved = torch.cuda.memory_reserved(0)
        total = torch.cuda.get_device_properties(0).total_memory
        return {
            "gpu_allocated_mb": round(allocated / 1024**2, 1),
            "gpu_reserved_mb": round(reserved / 1024**2, 1),
            "gpu_total_mb": round(total / 1024**2, 1),
            "gpu_free_mb": round((total - allocated) / 1024**2, 1),
            "gpu_utilization_percent": round(allocated / total * 100, 1) if total > 0 else 0,
        }
    except Exception:
        return {}


def format_snapshot_short(snap: dict) -> str:
    """One-line summary of a snapshot."""
    parts = [
        f"CPU={snap.get('cpu_percent', '?')}%",
        f"RAM={snap.get('ram_used_gb', '?')}/{snap.get('ram_total_gb', '?')}GB({snap.get('ram_percent', '?')}%)",
        f"Proc={snap.get('proc_rss_mb', '?')}MB",
    ]
    if "gpu_allocated_mb" in snap:
        parts.append(
            f"GPU={snap['gpu_allocated_mb']}/"
            f"{snap['gpu_total_mb']}MB({snap['gpu_utilization_percent']}%)"
        )
    return " | ".join(parts)


# ---------------------------------------------------------------------------
# Step Timer - high precision timing for pipeline steps
# ---------------------------------------------------------------------------

class StepTimer:
    """Track timing for a named step with resource snapshots."""

    def __init__(self, task_id: str, step_name: str, task_log_func=None):
        self.task_id = task_id
        self.step_name = step_name
        self.task_log_func = task_log_func
        self.start_time = None
        self.end_time = None
        self.start_snap = None
        self.end_snap = None
        self.sub_timings = {}  # sub-step -> duration
        self._sub_start = None
        self._sub_name = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        self.start_snap = snapshot_system()
        logger.info(
            f"STEP [{self.task_id[:8]}] >>> {self.step_name} started | "
            f"{format_snapshot_short(self.start_snap)}"
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.end_snap = snapshot_system()
        elapsed = self.end_time - self.start_time

        # Resource deltas
        ram_delta = (self.end_snap.get("proc_rss_mb", 0) - self.start_snap.get("proc_rss_mb", 0))
        gpu_delta = (self.end_snap.get("gpu_allocated_mb", 0) - self.start_snap.get("gpu_allocated_mb", 0))

        status = "FAILED" if exc_type else "OK"
        msg = (
            f"STEP [{self.task_id[:8]}] <<< {self.step_name} {status} "
            f"({elapsed:.3f}s) | "
            f"RAM delta={ram_delta:+.1f}MB | "
            f"{format_snapshot_short(self.end_snap)}"
        )
        if gpu_delta:
            msg += f" | GPU delta={gpu_delta:+.1f}MB"

        if exc_type:
            logger.error(msg + f" | Error: {exc_val}")
        else:
            logger.info(msg)

        # Log structured event
        if self.task_log_func:
            event_data = {
                "step": self.step_name,
                "duration_sec": round(elapsed, 4),
                "status": status,
                "ram_before_mb": self.start_snap.get("proc_rss_mb"),
                "ram_after_mb": self.end_snap.get("proc_rss_mb"),
                "ram_delta_mb": round(ram_delta, 1),
                "cpu_percent": self.end_snap.get("cpu_percent"),
            }
            if "gpu_allocated_mb" in self.end_snap:
                event_data["gpu_before_mb"] = self.start_snap.get("gpu_allocated_mb")
                event_data["gpu_after_mb"] = self.end_snap.get("gpu_allocated_mb")
                event_data["gpu_delta_mb"] = round(gpu_delta, 1)
            if self.sub_timings:
                event_data["sub_timings"] = self.sub_timings
            if exc_type:
                event_data["error"] = str(exc_val)
            self.task_log_func(self.task_id, f"step_{self.step_name}", **event_data)

        return False  # don't suppress exceptions

    @property
    def elapsed(self):
        if self.start_time is None:
            return 0
        end = self.end_time if self.end_time else time.perf_counter()
        return end - self.start_time

    def mark_sub(self, name: str):
        """Start a sub-step timer."""
        now = time.perf_counter()
        if self._sub_name and self._sub_start:
            self.sub_timings[self._sub_name] = round(now - self._sub_start, 4)
        self._sub_name = name
        self._sub_start = now

    def end_sub(self):
        """End current sub-step timer."""
        if self._sub_name and self._sub_start:
            self.sub_timings[self._sub_name] = round(time.perf_counter() - self._sub_start, 4)
            self._sub_name = None
            self._sub_start = None


# ---------------------------------------------------------------------------
# Transcription Profiler - per-segment metrics
# ---------------------------------------------------------------------------

class TranscriptionProfiler:
    """Tracks per-segment timing and resource usage during transcription."""

    def __init__(self, task_id: str):
        self.task_id = task_id
        self.segments = []  # list of segment metric dicts
        self.start_time = time.perf_counter()
        self.last_update_time = time.perf_counter()
        self.last_frames = 0
        self.total_frames = 0
        self.frame_times = []  # (frames_delta, time_delta) for throughput calc
        self._milestone_logged = set()

    def on_progress(self, current_frames: int, total_frames: int) -> dict:
        """Called on each tqdm update. Returns metrics dict."""
        now = time.perf_counter()
        self.total_frames = total_frames

        frames_delta = current_frames - self.last_frames
        time_delta = now - self.last_update_time

        if time_delta > 0 and frames_delta > 0:
            self.frame_times.append((frames_delta, time_delta))

        self.last_frames = current_frames
        self.last_update_time = now

        elapsed = now - self.start_time
        ratio = current_frames / total_frames if total_frames > 0 else 0
        audio_processed_sec = current_frames * 0.01  # SECONDS_PER_MEL_FRAME
        audio_total_sec = total_frames * 0.01

        # Instantaneous throughput (last update)
        instant_throughput = (frames_delta * 0.01) / time_delta if time_delta > 0 else 0

        # Rolling average throughput (last 10 updates)
        recent = self.frame_times[-10:]
        if recent:
            total_f = sum(f for f, _ in recent)
            total_t = sum(t for _, t in recent)
            avg_throughput = (total_f * 0.01) / total_t if total_t > 0 else 0
        else:
            avg_throughput = 0

        # Overall throughput
        overall_throughput = audio_processed_sec / elapsed if elapsed > 0 else 0

        # ETA from rolling average
        remaining_sec = audio_total_sec - audio_processed_sec
        eta = remaining_sec / avg_throughput if avg_throughput > 0 else -1

        metrics = {
            "ratio": ratio,
            "audio_processed_sec": round(audio_processed_sec, 1),
            "audio_total_sec": round(audio_total_sec, 1),
            "elapsed_sec": round(elapsed, 1),
            "eta_sec": round(eta, 1) if eta > 0 else -1,
            "instant_speed_x": round(instant_throughput, 2),
            "avg_speed_x": round(avg_throughput, 2),
            "overall_speed_x": round(overall_throughput, 2),
        }

        # Log at 10% milestones with resource snapshot
        pct_10 = int(ratio * 10)
        if pct_10 > 0 and pct_10 not in self._milestone_logged:
            self._milestone_logged.add(pct_10)
            snap = snapshot_system()
            logger.info(
                f"PERF [{self.task_id[:8]}] {pct_10*10}% | "
                f"audio={metrics['audio_processed_sec']:.0f}/{metrics['audio_total_sec']:.0f}s | "
                f"speed: instant={instant_throughput:.1f}x avg={avg_throughput:.1f}x overall={overall_throughput:.1f}x | "
                f"elapsed={elapsed:.1f}s eta={metrics['eta_sec']:.0f}s | "
                f"{format_snapshot_short(snap)}"
            )

        return metrics

    def on_segment(self, segment: dict, segment_index: int):
        """Called when a new subtitle segment is produced."""
        now = time.perf_counter()
        elapsed = now - self.start_time
        seg_duration = segment.get("end", 0) - segment.get("start", 0)
        text_len = len(segment.get("text", "").strip())

        seg_metrics = {
            "index": segment_index,
            "start": segment.get("start", 0),
            "end": segment.get("end", 0),
            "duration_sec": round(seg_duration, 2),
            "text_length": text_len,
            "wall_time_sec": round(elapsed, 2),
        }
        self.segments.append(seg_metrics)

        logger.debug(
            f"SEG [{self.task_id[:8]}] #{segment_index} "
            f"[{segment.get('start_fmt', '?')} -> {segment.get('end_fmt', '?')}] "
            f"dur={seg_duration:.1f}s chars={text_len} "
            f"wall={elapsed:.1f}s | \"{segment.get('text', '').strip()[:60]}\""
        )

    def summary(self) -> dict:
        """Generate transcription profiling summary."""
        elapsed = time.perf_counter() - self.start_time
        audio_total = self.total_frames * 0.01

        # Segment statistics
        seg_durations = [s["duration_sec"] for s in self.segments]
        text_lengths = [s["text_length"] for s in self.segments]

        summary = {
            "total_segments": len(self.segments),
            "audio_duration_sec": round(audio_total, 2),
            "wall_time_sec": round(elapsed, 2),
            "overall_speed_x": round(audio_total / elapsed, 2) if elapsed > 0 else 0,
            "total_mel_frames": self.total_frames,
        }

        if seg_durations:
            summary["seg_duration_avg"] = round(sum(seg_durations) / len(seg_durations), 2)
            summary["seg_duration_min"] = round(min(seg_durations), 2)
            summary["seg_duration_max"] = round(max(seg_durations), 2)

        if text_lengths:
            summary["seg_text_avg_chars"] = round(sum(text_lengths) / len(text_lengths), 1)
            summary["seg_text_total_chars"] = sum(text_lengths)

        # Throughput stability (coefficient of variation of frame times)
        if len(self.frame_times) > 5:
            speeds = [(f * 0.01) / t for f, t in self.frame_times if t > 0]
            if speeds:
                mean_speed = sum(speeds) / len(speeds)
                variance = sum((s - mean_speed) ** 2 for s in speeds) / len(speeds)
                std_speed = variance ** 0.5
                summary["speed_mean_x"] = round(mean_speed, 2)
                summary["speed_std_x"] = round(std_speed, 2)
                summary["speed_cv"] = round(std_speed / mean_speed, 3) if mean_speed > 0 else 0
                summary["speed_min_x"] = round(min(speeds), 2)
                summary["speed_max_x"] = round(max(speeds), 2)

        # Anomaly detection for transcription
        anomalies = []

        # Slower than real-time
        overall_speed = audio_total / elapsed if elapsed > 0 else 0
        if overall_speed < 1.0 and audio_total > 10:
            anomalies.append({
                "type": "slower_than_realtime",
                "severity": "critical",
                "message": f"Transcription at {overall_speed:.2f}x realtime (slower than real-time). "
                           f"Consider using a smaller model or different device.",
                "speed_x": round(overall_speed, 2),
            })

        # Very long segments (possible hallucination)
        if seg_durations:
            long_segs = [s for s in self.segments if s["duration_sec"] > 25]
            if long_segs:
                anomalies.append({
                    "type": "long_segments",
                    "severity": "warning",
                    "message": f"{len(long_segs)} segment(s) longer than 25s detected (possible hallucination).",
                    "segments": [s["index"] for s in long_segs],
                })

        # Very short segments with little text (noise)
        if self.segments:
            noise_segs = [s for s in self.segments if s["duration_sec"] < 0.5 and s["text_length"] < 5]
            if len(noise_segs) > 2:
                anomalies.append({
                    "type": "noise_segments",
                    "severity": "info",
                    "message": f"{len(noise_segs)} very short segments (<0.5s) with little text detected.",
                })

        # Speed instability
        if summary.get("speed_cv", 0) > 0.5:
            anomalies.append({
                "type": "speed_unstable",
                "severity": "warning",
                "message": f"High speed variability (CV={summary['speed_cv']:.2f}). "
                           f"Range: {summary.get('speed_min_x', '?')}x - {summary.get('speed_max_x', '?')}x.",
            })

        if anomalies:
            summary["anomalies"] = anomalies
            for a in anomalies:
                log_level = logging.WARNING if a["severity"] in ("critical", "warning") else logging.INFO
                logger.log(log_level, f"ANOMALY [{self.task_id[:8]}] [{a['severity'].upper()}] {a['message']}")

        return summary


# ---------------------------------------------------------------------------
# Pipeline Summary
# ---------------------------------------------------------------------------

class PipelineSummary:
    """Collects timing from all steps and produces a final summary."""

    def __init__(self, task_id: str, filename: str, model_size: str, device: str):
        self.task_id = task_id
        self.filename = filename
        self.model_size = model_size
        self.device = device
        self.pipeline_start = time.perf_counter()
        self.step_timings = {}  # step_name -> duration_sec
        self.start_snap = snapshot_system()
        self.file_size = 0
        self.audio_duration = 0.0
        self.audio_size = 0
        self.srt_size = 0
        self.transcription_summary = {}

    def record_step(self, name: str, duration: float):
        self.step_timings[name] = round(duration, 4)

    def finalize(self, status: str = "complete") -> dict:
        """Generate final pipeline summary."""
        total = time.perf_counter() - self.pipeline_start
        end_snap = snapshot_system()

        summary = {
            "task_id": self.task_id,
            "status": status,
            "filename": self.filename,
            "model": self.model_size,
            "device": self.device,
            "total_time_sec": round(total, 3),
            "step_timings": self.step_timings,
            "file_size_bytes": self.file_size,
            "audio_duration_sec": round(self.audio_duration, 2),
            "audio_size_bytes": self.audio_size,
            "srt_size_bytes": self.srt_size,
            "system_start": {
                "ram_mb": self.start_snap.get("proc_rss_mb"),
                "gpu_mb": self.start_snap.get("gpu_allocated_mb"),
            },
            "system_end": {
                "ram_mb": end_snap.get("proc_rss_mb"),
                "gpu_mb": end_snap.get("gpu_allocated_mb"),
            },
        }

        if self.transcription_summary:
            summary["transcription"] = self.transcription_summary

        # Compute time breakdown percentages
        if total > 0 and self.step_timings:
            breakdown = {}
            for name, dur in self.step_timings.items():
                breakdown[name] = f"{dur:.2f}s ({dur/total*100:.1f}%)"
            summary["time_breakdown"] = breakdown

        # Log the summary
        logger.info("=" * 70)
        logger.info(f"SUMMARY [{self.task_id[:8]}] Pipeline {status.upper()}")
        logger.info(f"  File:       {self.filename} ({format_bytes_simple(self.file_size)})")
        logger.info(f"  Audio:      {self.audio_duration:.1f}s ({format_bytes_simple(self.audio_size)})")
        logger.info(f"  Model:      {self.model_size} on {self.device.upper()}")
        logger.info(f"  Total time: {total:.2f}s")
        logger.info("  Breakdown:")
        for name, dur in self.step_timings.items():
            pct = dur / total * 100 if total > 0 else 0
            bar = "#" * int(pct / 2) + "." * (50 - int(pct / 2))
            logger.info(f"    {name:20s} {dur:8.3f}s ({pct:5.1f}%) [{bar}]")
        if self.transcription_summary:
            ts = self.transcription_summary
            logger.info("  Transcription:")
            logger.info(f"    Segments:     {ts.get('total_segments', '?')}")
            logger.info(f"    Speed:        {ts.get('overall_speed_x', '?')}x realtime")
            if "speed_mean_x" in ts:
                logger.info(f"    Speed range:  {ts['speed_min_x']}x - {ts['speed_max_x']}x (avg={ts['speed_mean_x']}x, cv={ts['speed_cv']})")
        logger.info("  Resources:")
        logger.info(f"    RAM:  {self.start_snap.get('proc_rss_mb', '?')}MB -> {end_snap.get('proc_rss_mb', '?')}MB")
        if "gpu_allocated_mb" in end_snap:
            logger.info(f"    VRAM: {self.start_snap.get('gpu_allocated_mb', '?')}MB -> {end_snap.get('gpu_allocated_mb', '?')}MB")
        logger.info("=" * 70)

        return summary


def format_bytes_simple(b: int) -> str:
    if b < 1024:
        return f"{b}B"
    elif b < 1024 * 1024:
        return f"{b/1024:.1f}KB"
    elif b < 1024**3:
        return f"{b/1024**2:.1f}MB"
    else:
        return f"{b/1024**3:.2f}GB"


# ---------------------------------------------------------------------------
# Background resource monitor (optional, for continuous sampling)
# ---------------------------------------------------------------------------

class ResourceMonitor:
    """Background thread that samples system resources at intervals."""

    def __init__(self, task_id: str, interval: float = 2.0):
        self.task_id = task_id
        self.interval = interval
        self.samples = []
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name=f"monitor-{self.task_id[:8]}")
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run(self):
        while not self._stop.is_set():
            try:
                snap = snapshot_system()
                snap["sample_time"] = time.perf_counter()
                self.samples.append(snap)
            except Exception:
                pass
            self._stop.wait(self.interval)

    def summary(self) -> dict:
        """Summarize collected samples with anomaly detection."""
        if not self.samples:
            return {}

        def avg(key):
            vals = [s[key] for s in self.samples if key in s]
            return round(sum(vals) / len(vals), 1) if vals else None

        def peak(key):
            vals = [s[key] for s in self.samples if key in s]
            return round(max(vals), 1) if vals else None

        def min_val(key):
            vals = [s[key] for s in self.samples if key in s]
            return round(min(vals), 1) if vals else None

        result = {
            "sample_count": len(self.samples),
            "duration_sec": round(self.samples[-1].get("sample_time", 0) - self.samples[0].get("sample_time", 0), 1) if len(self.samples) > 1 else 0,
            "cpu_avg_percent": avg("cpu_percent"),
            "cpu_peak_percent": peak("cpu_percent"),
            "ram_avg_mb": avg("proc_rss_mb"),
            "ram_peak_mb": peak("proc_rss_mb"),
            "ram_min_mb": min_val("proc_rss_mb"),
            "gpu_avg_mb": avg("gpu_allocated_mb"),
            "gpu_peak_mb": peak("gpu_allocated_mb"),
        }

        # Anomaly detection
        anomalies = []

        # Check for VRAM overflow
        gpu_total = peak("gpu_total_mb")
        gpu_peak = peak("gpu_allocated_mb")
        if gpu_total and gpu_peak and gpu_peak > gpu_total:
            anomalies.append({
                "type": "vram_overflow",
                "severity": "critical",
                "message": f"GPU VRAM overflow: {gpu_peak}MB allocated vs {gpu_total}MB total. "
                           f"Model is spilling to system RAM, causing severe performance degradation.",
                "peak_mb": gpu_peak,
                "total_mb": gpu_total,
            })

        # Check for excessive RAM usage (>80% of system)
        ram_peak_pct = peak("ram_percent")
        if ram_peak_pct and ram_peak_pct > 80:
            anomalies.append({
                "type": "high_ram_usage",
                "severity": "warning",
                "message": f"System RAM usage peaked at {ram_peak_pct}%.",
            })

        # Check for CPU saturation
        cpu_peak_pct = peak("cpu_percent")
        if cpu_peak_pct and cpu_peak_pct > 95:
            anomalies.append({
                "type": "cpu_saturation",
                "severity": "warning",
                "message": f"CPU usage peaked at {cpu_peak_pct}%, possible bottleneck.",
            })

        # Check for large RAM swings (instability)
        ram_vals = [s["proc_rss_mb"] for s in self.samples if "proc_rss_mb" in s]
        if len(ram_vals) > 3:
            ram_range = max(ram_vals) - min(ram_vals)
            if ram_range > 1000:
                anomalies.append({
                    "type": "ram_instability",
                    "severity": "info",
                    "message": f"Process RAM fluctuated by {ram_range:.0f}MB during execution.",
                })

        if anomalies:
            result["anomalies"] = anomalies
            for a in anomalies:
                log_level = logging.WARNING if a["severity"] in ("critical", "warning") else logging.INFO
                logger.log(log_level, f"ANOMALY [{self.task_id[:8]}] [{a['severity'].upper()}] {a['message']}")

        return result
