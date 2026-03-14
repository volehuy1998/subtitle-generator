"""Prometheus-compatible /metrics endpoint.

Exposes application metrics in Prometheus text format without requiring
the prometheus_client library (zero additional dependency).
"""

import logging
import time

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app import state
from app.config import OUTPUT_DIR, UPLOAD_DIR

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["System"])

# Simple counters tracked in-memory
_metrics = {
    "requests_total": 0,
    "uploads_total": 0,
    "transcriptions_completed": 0,
    "transcriptions_failed": 0,
    "transcriptions_cancelled": 0,
}

_start_time = time.time()


def inc(metric: str, value: int = 1):
    """Increment a metric counter."""
    _metrics[metric] = _metrics.get(metric, 0) + value


@router.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    """Expose metrics in Prometheus text exposition format."""
    lines = []
    lines.append("# HELP subtitle_generator_uptime_seconds Time since service start")
    lines.append("# TYPE subtitle_generator_uptime_seconds gauge")
    lines.append(f"subtitle_generator_uptime_seconds {time.time() - _start_time:.1f}")

    # Task counts by status
    status_counts = {}
    for t in state.tasks.values():
        s = t.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1

    lines.append("# HELP subtitle_generator_tasks_total Total tasks by status")
    lines.append("# TYPE subtitle_generator_tasks_total gauge")
    for s, count in status_counts.items():
        lines.append(f'subtitle_generator_tasks_total{{status="{s}"}} {count}')

    # Active tasks
    active = sum(1 for t in state.tasks.values() if t.get("status") not in ("done", "error", "cancelled"))
    lines.append("# HELP subtitle_generator_active_tasks Currently processing tasks")
    lines.append("# TYPE subtitle_generator_active_tasks gauge")
    lines.append(f"subtitle_generator_active_tasks {active}")

    # Total tasks ever
    lines.append("# HELP subtitle_generator_tasks_created_total Total tasks created")
    lines.append("# TYPE subtitle_generator_tasks_created_total counter")
    lines.append(f"subtitle_generator_tasks_created_total {len(state.tasks)}")

    # File counts
    try:
        upload_count = sum(1 for f in UPLOAD_DIR.iterdir() if f.is_file())
    except Exception:
        upload_count = 0
    try:
        output_count = sum(1 for f in OUTPUT_DIR.iterdir() if f.is_file())
    except Exception:
        output_count = 0

    lines.append("# HELP subtitle_generator_files_count Files in directories")
    lines.append("# TYPE subtitle_generator_files_count gauge")
    lines.append(f'subtitle_generator_files_count{{dir="uploads"}} {upload_count}')
    lines.append(f'subtitle_generator_files_count{{dir="outputs"}} {output_count}')

    # Counters
    for key, value in _metrics.items():
        prom_name = f"subtitle_generator_{key}"
        lines.append(f"# TYPE {prom_name} counter")
        lines.append(f"{prom_name} {value}")

    # System metrics (if psutil available)
    try:
        import psutil

        lines.append("# HELP subtitle_generator_cpu_percent CPU usage percentage")
        lines.append("# TYPE subtitle_generator_cpu_percent gauge")
        lines.append(f"subtitle_generator_cpu_percent {psutil.cpu_percent()}")

        mem = psutil.virtual_memory()
        lines.append("# HELP subtitle_generator_memory_used_bytes Memory used")
        lines.append("# TYPE subtitle_generator_memory_used_bytes gauge")
        lines.append(f"subtitle_generator_memory_used_bytes {mem.used}")

        lines.append("# HELP subtitle_generator_memory_percent Memory usage percentage")
        lines.append("# TYPE subtitle_generator_memory_percent gauge")
        lines.append(f"subtitle_generator_memory_percent {mem.percent}")
    except Exception:
        pass

    return "\n".join(lines) + "\n"
