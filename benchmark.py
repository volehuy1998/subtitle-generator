#!/usr/bin/env python3
"""
Benchmark script for the Subtitle Generator server.

Tests all combinations of model (tiny, base, small, medium, large) x device (cpu, cuda)
against a sample file via the running server's API at http://localhost:8000.

Usage:
    python benchmark.py [path_to_sample_file]

Defaults to C:\\Users\\voleh\\Downloads\\videoplayback.mp4 if no argument given.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error


# --- Configuration ---

BASE_URL = "http://localhost:8000"
MODELS = ["tiny", "base", "small", "medium", "large"]
DEVICES = ["cpu", "cuda"]
TIMEOUT_SECONDS = 300
POLL_INTERVAL = 2  # seconds between progress polls
DEFAULT_SAMPLE = r"C:\Users\voleh\Downloads\videoplayback.mp4"
LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
TASKS_JSONL = os.path.join(LOGS_DIR, "tasks.jsonl")
RESULTS_FILE = os.path.join(LOGS_DIR, "benchmark_results.json")


# --- Multipart form data helper ---

def build_multipart_formdata(fields, files):
    """
    Build a multipart/form-data body manually.

    fields: dict of {name: value} for text fields
    files: list of (field_name, filename, file_bytes, content_type)

    Returns (body_bytes, content_type_header).
    """
    boundary = "----BenchmarkBoundary%s" % int(time.time() * 1000)
    parts = []

    for name, value in fields.items():
        parts.append(("--%s" % boundary).encode())
        parts.append(
            ('Content-Disposition: form-data; name="%s"' % name).encode()
        )
        parts.append(b"")
        parts.append(value.encode() if isinstance(value, str) else value)

    for field_name, filename, file_bytes, content_type in files:
        parts.append(("--%s" % boundary).encode())
        parts.append(
            (
                'Content-Disposition: form-data; name="%s"; filename="%s"'
                % (field_name, filename)
            ).encode()
        )
        parts.append(("Content-Type: %s" % content_type).encode())
        parts.append(b"")
        parts.append(file_bytes)

    parts.append(("--%s--" % boundary).encode())
    parts.append(b"")

    body = b"\r\n".join(parts)
    content_type = "multipart/form-data; boundary=%s" % boundary
    return body, content_type


# --- HTTP helpers ---

def http_get_json(url):
    """GET a URL and parse JSON response. Returns (data, error_string)."""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode()), None
    except Exception as e:
        return None, str(e)


def http_post_upload(file_path, device, model_size):
    """
    POST to /upload with multipart form data.
    Returns (task_id, error_string).
    """
    filename = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    fields = {"device": device, "model_size": model_size}
    files = [(
        "file",
        filename,
        file_bytes,
        "application/octet-stream",
    )]

    body, content_type = build_multipart_formdata(fields, files)

    req = urllib.request.Request(
        BASE_URL + "/upload",
        data=body,
        headers={"Content-Type": content_type},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
            return data.get("task_id"), None
    except urllib.error.HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode()
        except Exception:
            pass
        return None, "HTTP %d: %s" % (e.code, body_text[:200])
    except Exception as e:
        return None, str(e)


def poll_until_done(task_id, timeout=TIMEOUT_SECONDS):
    """
    Poll /progress/{task_id} until status is done/error/cancelled or timeout.
    Returns (final_progress_data, error_string).
    """
    url = "%s/progress/%s" % (BASE_URL, task_id)
    start = time.time()

    while True:
        elapsed = time.time() - start
        if elapsed > timeout:
            return None, "Timeout after %ds" % timeout

        data, err = http_get_json(url)
        if err:
            return None, "Poll error: %s" % err

        status = data.get("status", "")
        percent = data.get("percent", 0)
        message = data.get("message", "")

        # Print inline progress
        print(
            "    [%3d%%] %s: %s" % (percent, status, message[:80]),
            end="\r",
            flush=True,
        )

        if status == "done":
            print()  # newline after progress
            return data, None
        elif status == "error":
            print()
            return data, "Task error: %s" % message
        elif status == "cancelled":
            print()
            return data, "Task was cancelled"

        time.sleep(POLL_INTERVAL)


# --- Profiling data from tasks.jsonl ---

def load_profiling_data(task_ids):
    """
    Read logs/tasks.jsonl and collect pipeline_summary events for the given task IDs.
    Returns dict of {task_id: pipeline_summary_dict}.
    """
    summaries = {}
    if not os.path.exists(TASKS_JSONL):
        return summaries

    target_ids = set(task_ids)
    try:
        with open(TASKS_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                tid = entry.get("task_id", "")
                if tid in target_ids and entry.get("event") == "pipeline_summary":
                    summaries[tid] = entry
    except Exception as e:
        print("Warning: could not read %s: %s" % (TASKS_JSONL, e))

    return summaries


# --- Formatting helpers ---

def fmt_time(seconds):
    """Format seconds to a human-readable string."""
    if seconds is None:
        return "N/A"
    if seconds < 0:
        return "N/A"
    if seconds < 1:
        return "<1s"
    if seconds < 60:
        return "%.1fs" % seconds
    m = int(seconds // 60)
    s = seconds % 60
    return "%dm %.0fs" % (m, s)


def fmt_mb(mb):
    """Format megabytes."""
    if mb is None:
        return "N/A"
    if mb < 1024:
        return "%.0fMB" % mb
    return "%.1fGB" % (mb / 1024)


# --- Table printing ---

def print_table(headers, rows, col_widths=None):
    """
    Print an ASCII table.
    headers: list of column header strings
    rows: list of lists of cell strings
    col_widths: optional list of minimum widths per column
    """
    num_cols = len(headers)

    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < num_cols:
                widths[i] = max(widths[i], len(str(cell)))

    if col_widths:
        for i, w in enumerate(col_widths):
            if i < num_cols:
                widths[i] = max(widths[i], w)

    # Build format string
    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    fmt = "| " + " | ".join("%%-%ds" % w for w in widths) + " |"

    print(sep)
    print(fmt % tuple(headers))
    print(sep)
    for row in rows:
        # Pad row to have the right number of columns
        padded = list(row) + [""] * (num_cols - len(row))
        print(fmt % tuple(str(c) for c in padded[:num_cols]))
    print(sep)


# --- Main benchmark ---

def run_benchmark(sample_file):
    print("=" * 70)
    print("SUBTITLE GENERATOR BENCHMARK")
    print("=" * 70)
    print("Sample file: %s" % sample_file)
    file_size_mb = os.path.getsize(sample_file) / (1024 * 1024)
    print("File size:   %.1f MB" % file_size_mb)
    print("Server:      %s" % BASE_URL)
    print("Timeout:     %ds per run" % TIMEOUT_SECONDS)
    print("Models:      %s" % ", ".join(MODELS))
    print("Devices:     %s" % ", ".join(DEVICES))
    print("Total runs:  %d" % (len(MODELS) * len(DEVICES)))
    print("=" * 70)
    print()

    # Check server is reachable
    print("Checking server connectivity... ", end="", flush=True)
    data, err = http_get_json(BASE_URL + "/system-info")
    if err:
        print("FAILED")
        print("Error: %s" % err)
        print("Make sure the server is running at %s" % BASE_URL)
        sys.exit(1)
    print("OK")
    if data:
        cuda_available = data.get("cuda_available", False)
        gpu_name = data.get("gpu_name", "N/A")
        print("  CUDA available: %s" % cuda_available)
        if cuda_available:
            print("  GPU: %s (%.1f GB VRAM)" % (gpu_name, data.get("gpu_vram", 0)))
        if not cuda_available:
            print("  NOTE: CUDA not available, cuda runs will fall back to CPU")
    print()

    results = []
    task_ids = []
    run_num = 0
    total_runs = len(MODELS) * len(DEVICES)

    for model in MODELS:
        for device in DEVICES:
            run_num += 1
            print("-" * 70)
            print("[%d/%d] Running: model=%s  device=%s" % (run_num, total_runs, model, device))
            print("-" * 70)

            result = {
                "model": model,
                "device": device,
                "status": "pending",
                "task_id": None,
                "total_time_sec": None,
                "transcribe_time_sec": None,
                "model_load_time_sec": None,
                "speed_x": None,
                "segments": None,
                "language": None,
                "ram_peak_mb": None,
                "gpu_peak_mb": None,
                "error": None,
            }

            wall_start = time.time()

            # Upload
            print("  Uploading file...", end=" ", flush=True)
            task_id, err = http_post_upload(sample_file, device, model)
            if err:
                print("FAILED")
                print("  Error: %s" % err)
                result["status"] = "upload_error"
                result["error"] = err
                results.append(result)
                print()
                continue
            print("OK (task_id=%s)" % task_id[:8])
            result["task_id"] = task_id
            task_ids.append(task_id)

            # Poll
            print("  Processing...")
            progress_data, err = poll_until_done(task_id, timeout=TIMEOUT_SECONDS)

            wall_elapsed = time.time() - wall_start

            if err:
                result["status"] = "error"
                result["error"] = err
                result["total_time_sec"] = round(wall_elapsed, 2)
                print("  FAILED: %s" % err)
            else:
                result["status"] = "done"
                result["total_time_sec"] = round(wall_elapsed, 2)
                result["segments"] = progress_data.get("segments")
                result["language"] = progress_data.get("language")
                result["speed_x"] = progress_data.get("speed_x")
                print("  DONE in %s" % fmt_time(wall_elapsed))
                if progress_data.get("segments"):
                    print(
                        "  Segments: %s | Language: %s"
                        % (progress_data.get("segments"), progress_data.get("language"))
                    )

            results.append(result)
            print()

    # Collect profiling data from tasks.jsonl
    print("=" * 70)
    print("Collecting profiling data from tasks.jsonl...")
    print("=" * 70)

    profiling = load_profiling_data(task_ids)

    for result in results:
        tid = result.get("task_id")
        if tid and tid in profiling:
            summary = profiling[tid]
            step_timings = summary.get("step_timings", {})
            result["transcribe_time_sec"] = step_timings.get("transcribe")
            result["model_load_time_sec"] = step_timings.get("model_load")
            result["extract_audio_time_sec"] = step_timings.get("extract_audio")
            result["probe_time_sec"] = step_timings.get("probe")

            # Transcription profiling
            tx = summary.get("transcription", {})
            if tx:
                result["speed_x"] = tx.get("overall_speed_x")
                result["audio_duration_sec"] = tx.get("audio_duration_sec")
                result["total_segments"] = tx.get("total_segments")

            # System resources from pipeline summary
            sys_end = summary.get("system_end", {})
            result["ram_end_mb"] = sys_end.get("ram_mb")
            gpu_end_mb = sys_end.get("gpu_mb")
            result["gpu_end_mb"] = gpu_end_mb

            # Total pipeline time from server
            result["server_total_sec"] = summary.get("total_time_sec")

    # Also load resource_monitor events for peak values
    if os.path.exists(TASKS_JSONL):
        try:
            with open(TASKS_JSONL, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    tid = entry.get("task_id", "")
                    if entry.get("event") == "resource_monitor":
                        for result in results:
                            if result.get("task_id") == tid:
                                result["ram_peak_mb"] = entry.get("ram_peak_mb")
                                result["gpu_peak_mb"] = entry.get("gpu_peak_mb")
                                result["cpu_avg_percent"] = entry.get("cpu_avg_percent")
                                result["cpu_peak_percent"] = entry.get("cpu_peak_percent")
        except Exception as e:
            print("Warning: error reading resource data: %s" % e)

    # Print comparison table
    print()
    print("=" * 70)
    print("BENCHMARK RESULTS")
    print("=" * 70)
    print()

    headers = [
        "Model",
        "Device",
        "Status",
        "Total",
        "Transcribe",
        "Model Load",
        "Speed",
        "Segments",
        "RAM Peak",
        "GPU Peak",
    ]

    rows = []
    for r in results:
        total_str = fmt_time(r.get("server_total_sec") or r.get("total_time_sec"))
        transcribe_str = fmt_time(r.get("transcribe_time_sec"))
        model_load_str = fmt_time(r.get("model_load_time_sec"))
        speed_str = "%.1fx" % r["speed_x"] if r.get("speed_x") else "N/A"
        seg_str = str(r.get("total_segments") or r.get("segments") or "N/A")
        ram_str = fmt_mb(r.get("ram_peak_mb"))
        gpu_str = fmt_mb(r.get("gpu_peak_mb"))

        status = r.get("status", "?")
        if status == "done":
            status_str = "OK"
        elif status == "error":
            status_str = "FAIL"
        else:
            status_str = status[:6]

        rows.append([
            r["model"],
            r["device"],
            status_str,
            total_str,
            transcribe_str,
            model_load_str,
            speed_str,
            seg_str,
            ram_str,
            gpu_str,
        ])

    print_table(headers, rows)

    # Print error details if any
    errors = [r for r in results if r.get("error")]
    if errors:
        print()
        print("ERRORS:")
        for r in errors:
            print("  %s/%s: %s" % (r["model"], r["device"], r["error"][:120]))

    # Save results
    print()
    os.makedirs(LOGS_DIR, exist_ok=True)
    output = {
        "benchmark_time": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "sample_file": sample_file,
        "file_size_bytes": os.path.getsize(sample_file),
        "timeout_seconds": TIMEOUT_SECONDS,
        "total_runs": total_runs,
        "successful_runs": sum(1 for r in results if r["status"] == "done"),
        "failed_runs": sum(1 for r in results if r["status"] != "done"),
        "results": results,
    }

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("Results saved to: %s" % RESULTS_FILE)
    print()
    print("Benchmark complete.")


# --- Entry point ---

if __name__ == "__main__":
    sample_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SAMPLE

    if not os.path.isfile(sample_file):
        print("ERROR: Sample file not found: %s" % sample_file)
        sys.exit(1)

    try:
        run_benchmark(sample_file)
    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user.")
        sys.exit(1)
