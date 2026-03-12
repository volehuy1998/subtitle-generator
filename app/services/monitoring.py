"""Monitoring & observability service.

Provides business metrics, alerting rules, performance profiling,
and health aggregation for operational visibility.
"""

import json
import logging
import os
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from urllib.request import Request, urlopen

logger = logging.getLogger("subtitle-generator")

# ── Business Metrics (in-memory counters) ──

_metrics_lock = threading.Lock()
_business_metrics = {
    "uploads_per_hour": deque(maxlen=3600),  # timestamps
    "completions_per_hour": deque(maxlen=3600),
    "failures_per_hour": deque(maxlen=3600),
    "processing_times": deque(maxlen=1000),  # durations in seconds
    "embed_count": 0,
    "embed_soft_count": 0,
    "embed_hard_count": 0,
}


def record_upload():
    """Record an upload event."""
    with _metrics_lock:
        _business_metrics["uploads_per_hour"].append(time.time())


def record_completion(processing_time: float = 0):
    """Record a successful transcription completion."""
    with _metrics_lock:
        _business_metrics["completions_per_hour"].append(time.time())
        if processing_time > 0:
            _business_metrics["processing_times"].append(processing_time)


def record_failure():
    """Record a transcription failure."""
    with _metrics_lock:
        _business_metrics["failures_per_hour"].append(time.time())


def record_embed(mode: str = "soft"):
    """Record an embed operation."""
    with _metrics_lock:
        _business_metrics["embed_count"] += 1
        if mode == "soft":
            _business_metrics["embed_soft_count"] += 1
        else:
            _business_metrics["embed_hard_count"] += 1


def get_business_metrics() -> dict:
    """Get current business metrics snapshot."""
    now = time.time()
    hour_ago = now - 3600

    with _metrics_lock:
        uploads_1h = sum(1 for t in _business_metrics["uploads_per_hour"] if t > hour_ago)
        completions_1h = sum(1 for t in _business_metrics["completions_per_hour"] if t > hour_ago)
        failures_1h = sum(1 for t in _business_metrics["failures_per_hour"] if t > hour_ago)
        total = completions_1h + failures_1h
        success_rate = (completions_1h / total * 100) if total > 0 else 100.0

        proc_times = list(_business_metrics["processing_times"])
        avg_processing = sum(proc_times) / len(proc_times) if proc_times else 0.0
        p95_processing = sorted(proc_times)[int(len(proc_times) * 0.95)] if len(proc_times) > 1 else 0.0

        return {
            "uploads_per_hour": uploads_1h,
            "completions_per_hour": completions_1h,
            "failures_per_hour": failures_1h,
            "success_rate_pct": round(success_rate, 1),
            "avg_processing_sec": round(avg_processing, 2),
            "p95_processing_sec": round(p95_processing, 2),
            "embed_total": _business_metrics["embed_count"],
            "embed_soft": _business_metrics["embed_soft_count"],
            "embed_hard": _business_metrics["embed_hard_count"],
        }


# ── Alert History ──

_alert_history: deque = deque(maxlen=200)
_previous_alert_keys: set = set()
_alert_history_lock = threading.Lock()


def get_alert_history() -> list:
    """Return the full alert history (last 200 entries)."""
    with _alert_history_lock:
        return list(_alert_history)


def _notify_webhook(alert: dict):
    """POST alert payload to WEBHOOK_ALERT_URL if configured."""
    url = os.environ.get("WEBHOOK_ALERT_URL", "")
    if not url:
        return
    try:
        body = json.dumps({
            "text": f"🚨 *SubForge Alert* [{alert.get('severity', '?').upper()}] {alert.get('alert', '')} — {alert.get('message', '')}",
            "alert": alert,
        }).encode()
        req = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        urlopen(req, timeout=5)
    except Exception:
        pass  # Never block on webhook failure


# ── Alerting Rules ──

_alert_thresholds = {
    "error_rate_pct": float(os.environ.get("ALERT_ERROR_RATE", "5.0")),
    "queue_depth_max": int(os.environ.get("ALERT_QUEUE_DEPTH", "10")),
    "disk_free_min_gb": float(os.environ.get("ALERT_DISK_FREE_GB", "1.0")),
    "latency_max_sec": float(os.environ.get("ALERT_LATENCY_SEC", "300")),
    "memory_pct_max": float(os.environ.get("ALERT_MEMORY_PCT", "90")),
}


def get_alert_thresholds() -> dict:
    """Get current alert threshold configuration."""
    return dict(_alert_thresholds)


def set_alert_threshold(name: str, value: float):
    """Update an alert threshold."""
    if name in _alert_thresholds:
        _alert_thresholds[name] = value


def check_alerts() -> list[dict]:
    """Check all alert conditions. Returns list of triggered alerts."""
    alerts = []
    metrics = get_business_metrics()

    # Error rate
    total = metrics["completions_per_hour"] + metrics["failures_per_hour"]
    if total > 0:
        error_rate = (metrics["failures_per_hour"] / total) * 100
        if error_rate > _alert_thresholds["error_rate_pct"]:
            alerts.append({
                "alert": "high_error_rate",
                "severity": "warning",
                "value": round(error_rate, 1),
                "threshold": _alert_thresholds["error_rate_pct"],
                "message": f"Error rate {error_rate:.1f}% exceeds threshold {_alert_thresholds['error_rate_pct']}%",
            })

    # Processing latency
    if metrics["p95_processing_sec"] > _alert_thresholds["latency_max_sec"]:
        alerts.append({
            "alert": "high_latency",
            "severity": "warning",
            "value": metrics["p95_processing_sec"],
            "threshold": _alert_thresholds["latency_max_sec"],
            "message": f"P95 processing time {metrics['p95_processing_sec']}s exceeds {_alert_thresholds['latency_max_sec']}s",
        })

    # Disk space
    try:
        import shutil
        from app.config import OUTPUT_DIR
        usage = shutil.disk_usage(OUTPUT_DIR)
        free_gb = usage.free / (1024**3)
        if free_gb < _alert_thresholds["disk_free_min_gb"]:
            alerts.append({
                "alert": "disk_low",
                "severity": "critical",
                "value": round(free_gb, 2),
                "threshold": _alert_thresholds["disk_free_min_gb"],
                "message": f"Disk free space {free_gb:.1f}GB below {_alert_thresholds['disk_free_min_gb']}GB",
            })
    except Exception:
        pass

    # Record new alerts into history and fire webhooks
    global _previous_alert_keys
    current_keys = {a["alert"] for a in alerts}
    new_keys = current_keys - _previous_alert_keys
    _previous_alert_keys = current_keys

    now_iso = datetime.now(timezone.utc).isoformat()
    with _alert_history_lock:
        for alert in alerts:
            if alert["alert"] in new_keys:
                entry = {
                    "timestamp": now_iso,
                    "alert": alert["alert"],
                    "severity": alert.get("severity", "warning"),
                    "message": alert.get("message", ""),
                    "resolved": False,
                }
                _alert_history.append(entry)
                _notify_webhook(entry)

    return alerts


# ── Performance Profiling ──

_profile_data: dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
_profile_lock = threading.Lock()


def start_timer() -> float:
    """Start a performance timer. Returns start timestamp."""
    return time.time()


def record_timing(category: str, start: float, task_id: str = ""):
    """Record a timing measurement for a processing stage."""
    duration = time.time() - start
    with _profile_lock:
        _profile_data[category].append({
            "duration_sec": round(duration, 4),
            "task_id": task_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })


def get_performance_profile() -> dict:
    """Get performance profiling summary by category."""
    result = {}
    with _profile_lock:
        for category, timings in _profile_data.items():
            durations = [t["duration_sec"] for t in timings]
            if durations:
                result[category] = {
                    "count": len(durations),
                    "avg_sec": round(sum(durations) / len(durations), 4),
                    "min_sec": round(min(durations), 4),
                    "max_sec": round(max(durations), 4),
                    "p95_sec": round(sorted(durations)[int(len(durations) * 0.95)], 4) if len(durations) > 1 else round(durations[0], 4),
                    "last": timings[-1] if timings else None,
                }
    return result


# ── Health Aggregation ──

def get_health_dashboard() -> dict:
    """Get comprehensive health dashboard data (Grafana-compatible)."""
    business = get_business_metrics()
    alerts = check_alerts()
    profile = get_performance_profile()

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "degraded" if alerts else "healthy",
        "business_metrics": business,
        "alerts": alerts,
        "alert_count": len(alerts),
        "performance": profile,
        "thresholds": get_alert_thresholds(),
    }
