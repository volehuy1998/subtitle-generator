"""Analytics service: collects per-task metrics, maintains time-series data.

Provides:
  - Event recording (task start, complete, error, cancel)
  - Counters (uploads, completions, errors, by language/model/device)
  - Time-series ring buffer (minute-resolution, 24h retention)
  - Summary statistics (totals, rates, averages, distributions)
"""

import asyncio
import json
import logging
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

from app.config import LOG_DIR

logger = logging.getLogger("subtitle-generator")

_lock = threading.Lock()

# ── Counters ──
_counters = {
    "uploads_total": 0,
    "completed_total": 0,
    "failed_total": 0,
    "cancelled_total": 0,
}

# ── Distributions ──
_language_counts: dict[str, int] = defaultdict(int)
_model_counts: dict[str, int] = defaultdict(int)
_device_counts: dict[str, int] = defaultdict(int)

# ── Processing time tracking ──
_processing_times: deque[float] = deque(maxlen=1000)  # last 1000 task durations
_processing_times_by_model: dict[str, deque] = defaultdict(lambda: deque(maxlen=200))
_file_sizes: deque[int] = deque(maxlen=1000)

# ── Time-series ring buffer (minute-resolution, 24h = 1440 points) ──
_TIMESERIES_MAX = 1440  # 24 hours of minute-resolution data


class _TimeSeriesPoint:
    __slots__ = ("timestamp", "uploads", "completed", "failed", "cancelled",
                 "total_processing_sec", "task_count")

    def __init__(self, timestamp: int):
        self.timestamp = timestamp  # unix epoch (floored to minute)
        self.uploads = 0
        self.completed = 0
        self.failed = 0
        self.cancelled = 0
        self.total_processing_sec = 0.0
        self.task_count = 0

    @property
    def avg_processing_sec(self) -> float:
        return self.total_processing_sec / self.task_count if self.task_count > 0 else 0.0

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "time": datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat(),
            "uploads": self.uploads,
            "completed": self.completed,
            "failed": self.failed,
            "cancelled": self.cancelled,
            "avg_processing_sec": round(self.avg_processing_sec, 2),
        }


_timeseries: deque[_TimeSeriesPoint] = deque(maxlen=_TIMESERIES_MAX)
# ── Request Tracking ──
_request_counts: deque[dict] = deque(maxlen=10000)  # last 10K requests for user tracking
_error_categories: dict[str, int] = defaultdict(int)  # error type -> count
_user_agents: dict[str, int] = defaultdict(int)  # user agent category -> count
_client_ips: dict[str, int] = defaultdict(int)  # IP -> request count (for unique user tracking)

_start_time = time.time()


def _schedule_db_write(coro):
    """Schedule an async DB write from sync context (thread-safe)."""
    from app import state
    loop = state.main_event_loop
    if loop is not None and not loop.is_closed():
        asyncio.run_coroutine_threadsafe(coro, loop)


def _current_minute() -> int:
    """Get current time floored to the minute (unix epoch)."""
    return int(time.time()) // 60 * 60


def _get_or_create_point(minute_ts: int) -> _TimeSeriesPoint:
    """Get or create a time-series point for the given minute."""
    if _timeseries and _timeseries[-1].timestamp == minute_ts:
        return _timeseries[-1]
    point = _TimeSeriesPoint(minute_ts)
    _timeseries.append(point)
    return point


# ── Public API ──

def record_upload(language: str = "auto", model: str = "medium",
                  device: str = "cpu", file_size: int = 0):
    """Record a new upload event."""
    with _lock:
        _counters["uploads_total"] += 1
        _language_counts[language] += 1
        _model_counts[model] += 1
        _device_counts[device] += 1
        if file_size > 0:
            _file_sizes.append(file_size)
        point = _get_or_create_point(_current_minute())
        point.uploads += 1
    # Persist to PostgreSQL
    from app.services import analytics_pg
    minute_dt = datetime.fromtimestamp(_current_minute(), tz=timezone.utc)
    _schedule_db_write(analytics_pg.update_daily_stats(uploads=1, file_size=file_size))
    _schedule_db_write(analytics_pg.upsert_timeseries_point(minute_dt, uploads=1))
    _schedule_db_write(analytics_pg.record_event("upload", {
        "language": language, "model": model, "device": device, "file_size": file_size,
    }))


def record_completion(processing_time_sec: float, model: str = "medium"):
    """Record a successful task completion."""
    with _lock:
        _counters["completed_total"] += 1
        _processing_times.append(processing_time_sec)
        _processing_times_by_model[model].append(processing_time_sec)
        point = _get_or_create_point(_current_minute())
        point.completed += 1
        point.total_processing_sec += processing_time_sec
        point.task_count += 1
    # Persist to PostgreSQL
    from app.services import analytics_pg
    minute_dt = datetime.fromtimestamp(_current_minute(), tz=timezone.utc)
    _schedule_db_write(analytics_pg.update_daily_stats(
        completed=1, processing_sec=processing_time_sec,
    ))
    _schedule_db_write(analytics_pg.upsert_timeseries_point(
        minute_dt, completed=1, processing_sec=processing_time_sec, task_count=1,
    ))
    _schedule_db_write(analytics_pg.record_event("completion", {
        "processing_time_sec": round(processing_time_sec, 2), "model": model,
    }))


def record_failure():
    """Record a task failure."""
    with _lock:
        _counters["failed_total"] += 1
        point = _get_or_create_point(_current_minute())
        point.failed += 1
    # Persist to PostgreSQL
    from app.services import analytics_pg
    minute_dt = datetime.fromtimestamp(_current_minute(), tz=timezone.utc)
    _schedule_db_write(analytics_pg.update_daily_stats(failed=1))
    _schedule_db_write(analytics_pg.upsert_timeseries_point(minute_dt, failed=1))


def record_cancellation():
    """Record a task cancellation."""
    with _lock:
        _counters["cancelled_total"] += 1
        point = _get_or_create_point(_current_minute())
        point.cancelled += 1
    # Persist to PostgreSQL
    from app.services import analytics_pg
    minute_dt = datetime.fromtimestamp(_current_minute(), tz=timezone.utc)
    _schedule_db_write(analytics_pg.update_daily_stats(cancelled=1))
    _schedule_db_write(analytics_pg.upsert_timeseries_point(minute_dt, cancelled=1))


def record_request(client_ip: str = "", user_agent: str = ""):
    """Record an incoming request for user tracking."""
    with _lock:
        if client_ip:
            _client_ips[client_ip] += 1
        # Categorize user agent
        ua_lower = user_agent.lower()
        if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
            category = "mobile"
        elif "bot" in ua_lower or "crawler" in ua_lower or "spider" in ua_lower:
            category = "bot"
        elif "curl" in ua_lower or "python" in ua_lower or "httpx" in ua_lower:
            category = "api"
        else:
            category = "browser"
        _user_agents[category] += 1


def record_error_category(error_type: str):
    """Record a categorized error."""
    with _lock:
        _error_categories[error_type] += 1


def get_user_stats() -> dict:
    """Get user tracking statistics."""
    with _lock:
        unique_ips = len(_client_ips)
        total_requests = sum(_client_ips.values())
        return {
            "unique_users": unique_ips,
            "total_requests": total_requests,
            "user_agents": dict(_user_agents),
            "top_users": dict(sorted(_client_ips.items(), key=lambda x: x[1], reverse=True)[:10]),
            "error_categories": dict(_error_categories),
        }


def get_summary() -> dict:
    """Get analytics summary with totals, rates, averages, distributions."""
    with _lock:
        total = _counters["uploads_total"]
        completed = _counters["completed_total"]
        failed = _counters["failed_total"]
        cancelled = _counters["cancelled_total"]

        uptime_sec = time.time() - _start_time
        uptime_hours = uptime_sec / 3600 if uptime_sec > 0 else 1

        # Processing time stats
        avg_processing = (sum(_processing_times) / len(_processing_times)) if _processing_times else 0
        p95_processing = sorted(_processing_times)[int(len(_processing_times) * 0.95)] if len(_processing_times) >= 20 else avg_processing

        # Per-model averages
        model_avg = {}
        for model, times in _processing_times_by_model.items():
            model_avg[model] = round(sum(times) / len(times), 2) if times else 0

        # File size stats
        avg_file_size = int(sum(_file_sizes) / len(_file_sizes)) if _file_sizes else 0

        # Top languages
        top_languages = sorted(_language_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # Success rate
        processed = completed + failed
        success_rate = (completed / processed * 100) if processed > 0 else 100.0
        error_rate = (failed / processed * 100) if processed > 0 else 0.0

        return {
            "counters": {
                "uploads_total": total,
                "completed_total": completed,
                "failed_total": failed,
                "cancelled_total": cancelled,
            },
            "rates": {
                "success_rate": round(success_rate, 1),
                "error_rate": round(error_rate, 1),
                "uploads_per_hour": round(total / uptime_hours, 1),
                "completions_per_hour": round(completed / uptime_hours, 1),
            },
            "processing": {
                "avg_sec": round(avg_processing, 2),
                "p95_sec": round(p95_processing, 2),
                "total_processed": processed,
                "by_model": model_avg,
            },
            "distributions": {
                "top_languages": dict(top_languages),
                "models": dict(_model_counts),
                "devices": dict(_device_counts),
            },
            "files": {
                "avg_size_bytes": avg_file_size,
                "total_uploaded": total,
            },
            "uptime_sec": round(uptime_sec, 1),
        }


def get_timeseries(minutes: int = 60) -> list[dict]:
    """Get time-series data points for the last N minutes."""
    with _lock:
        cutoff = _current_minute() - (minutes * 60)
        return [p.to_dict() for p in _timeseries if p.timestamp >= cutoff]


def export_analytics_csv() -> str:
    """Export time-series data as CSV."""
    points = get_timeseries(minutes=1440)
    lines = ["timestamp,uploads,completed,failed,cancelled,avg_processing_sec"]
    for p in points:
        lines.append(f"{p['time']},{p['uploads']},{p['completed']},{p['failed']},{p['cancelled']},{p['avg_processing_sec']}")
    return "\n".join(lines)


def save_analytics_snapshot():
    """Save current analytics state to disk for persistence across restarts."""
    try:
        snapshot = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "counters": dict(_counters),
            "language_counts": dict(_language_counts),
            "model_counts": dict(_model_counts),
            "device_counts": dict(_device_counts),
        }
        path = LOG_DIR / "analytics_snapshot.json"
        path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to save analytics snapshot: {e}")


async def load_analytics_from_db():
    """Load analytics counters from PostgreSQL on startup."""
    try:
        from app.services import analytics_pg
        summary = await analytics_pg.get_summary_from_db()
        if summary:
            with _lock:
                for key in ("uploads_total", "completed_total", "failed_total", "cancelled_total"):
                    if summary.get(key, 0) > _counters.get(key, 0):
                        _counters[key] = summary[key]
            logger.info(f"Loaded analytics from DB: {summary}")
            return True
    except Exception as e:
        logger.error(f"Failed to load analytics from DB: {e}")
    return False


def load_analytics_snapshot():
    """Load analytics state from disk on startup (legacy fallback)."""
    path = LOG_DIR / "analytics_snapshot.json"
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        with _lock:
            for k, v in data.get("counters", {}).items():
                if k in _counters:
                    _counters[k] = v
            for k, v in data.get("language_counts", {}).items():
                _language_counts[k] = v
            for k, v in data.get("model_counts", {}).items():
                _model_counts[k] = v
            for k, v in data.get("device_counts", {}).items():
                _device_counts[k] = v
        logger.info(f"Loaded analytics snapshot: {data.get('counters', {})}")
    except Exception as e:
        logger.error(f"Failed to load analytics snapshot: {e}")
