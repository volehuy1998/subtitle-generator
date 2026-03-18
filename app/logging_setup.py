"""Logging configuration: structured JSON logging for log analysis integration.

Provides configurable log sinks:
  1. Console: Human-readable format for development
  2. app.log: Rotating file with structured messages
  3. app.jsonl: Structured JSON lines for log analysis tools (ELK, Grafana, etc.)
  4. error.log: Errors only, rotating
  5. tasks.jsonl: Structured task pipeline events
  6. Webhook: HTTP POST to external log aggregator (optional)
  7. Syslog: Remote syslog forwarding (optional)
"""

import json
import logging
import logging.handlers
import re
import sys
import threading
import uuid
from datetime import datetime, timezone

from app.config import LOG_DIR, LOG_JSON_ONLY, LOG_LEVEL, LOG_OUTPUT, LOG_SYSLOG_HOST, LOG_WEBHOOK_URL

logger = logging.getLogger("subtitle-generator")
task_log_path = LOG_DIR / "tasks.jsonl"
json_log_path = LOG_DIR / "app.jsonl"

# ── Thread-local context for correlation IDs ──

_request_id = threading.local()
_task_context = threading.local()


def get_request_id() -> str:
    return getattr(_request_id, "id", "system")


def set_request_id(rid: str = None):
    _request_id.id = rid or str(uuid.uuid4())[:8]


def get_task_context() -> str | None:
    return getattr(_task_context, "task_id", None)


def set_task_context(task_id: str):
    _task_context.task_id = task_id


def clear_task_context():
    _task_context.task_id = None


# ── Log sanitization ──

_SENSITIVE_PATTERNS = [
    (re.compile(r"\bsk-[A-Za-z0-9]{10,}\b"), "[REDACTED_API_KEY]"),
    (re.compile(r"\bhf_[A-Za-z0-9]{10,}\b"), "[REDACTED_HF_TOKEN]"),
    (re.compile(r"Bearer\s+[A-Za-z0-9\._\-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)(api[_-]?key|token|secret|password|authorization)\s*[=:]\s*\S+"), r"\1=[REDACTED]"),
]


def sanitize_log_message(msg: str) -> str:
    """Redact sensitive tokens and keys from log messages."""
    for pattern, replacement in _SENSITIVE_PATTERNS:
        msg = pattern.sub(replacement, msg)
    return msg


# ── Formatters ──


class JsonFormatter(logging.Formatter):
    """Structured JSON log formatter for log analysis tool integration."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "thread": record.threadName,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "request_id": get_request_id(),
        }
        task_id = get_task_context()
        if task_id:
            entry["task_id"] = task_id
        if record.exc_info and record.exc_info[0]:
            entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }
        return json.dumps(entry, ensure_ascii=False, default=str)


class SanitizingJsonFormatter(JsonFormatter):
    """JSON formatter that redacts sensitive data before output."""

    def format(self, record: logging.LogRecord) -> str:
        output = super().format(record)
        parsed = json.loads(output)
        parsed["message"] = sanitize_log_message(parsed["message"])
        if "exception" in parsed and "traceback" in parsed["exception"]:
            parsed["exception"]["traceback"] = sanitize_log_message(parsed["exception"]["traceback"])
        return json.dumps(parsed, ensure_ascii=False, default=str)


# ── Webhook log handler ──


class WebhookLogHandler(logging.Handler):
    """Send log entries to an HTTP endpoint via POST."""

    def __init__(self, url: str, level=logging.WARNING):
        super().__init__(level)
        self.url = url
        self._formatter = SanitizingJsonFormatter()

    def emit(self, record):
        try:
            import urllib.request

            data = self._formatter.format(record).encode("utf-8")
            req = urllib.request.Request(
                self.url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5)  # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected  # URL is operator-configured LOG_WEBHOOK_URL env-var, not user input  # fmt: skip
        except Exception:
            pass  # Never let log delivery failure crash the app


# ── Security event logging ──


def log_security_event(event_type: str, ip: str = "", path: str = "", details: dict = None):
    """Log a security-related event in structured format."""
    extra_info = {
        "security_event": event_type,
        "ip": ip,
        "path": path,
    }
    if details:
        extra_info["details"] = details
    logger.warning(f"SECURITY [{event_type}] ip={ip} path={path} {details or ''}")
    # Also write to task log for audit trail
    entry = {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "event": f"security_{event_type}",
        "request_id": get_request_id(),
        **extra_info,
    }
    try:
        with open(task_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass


# ── Setup ──


def setup_logging():
    """Configure the application logger with configurable handlers."""
    log_level = getattr(logging, LOG_LEVEL, logging.INFO)
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers on reload
    if logger.handlers:
        return

    console_format = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s [%(threadName)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler (stdout for Docker)
    if LOG_OUTPUT in ("stdout", "both"):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        if LOG_JSON_ONLY:
            console_handler.setFormatter(SanitizingJsonFormatter())
        else:
            console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)

    # File handlers
    if LOG_OUTPUT in ("file", "both"):
        # Human-readable rotating log
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_DIR / "app.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(console_format)
        logger.addHandler(file_handler)

        # Error file: errors only
        error_handler = logging.handlers.RotatingFileHandler(
            LOG_DIR / "error.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(console_format)
        logger.addHandler(error_handler)

    # JSON-only mode (for Docker/k8s structured logging to stdout)
    if LOG_OUTPUT == "json":
        json_console = logging.StreamHandler(sys.stdout)
        json_console.setLevel(log_level)
        json_console.setFormatter(SanitizingJsonFormatter())
        logger.addHandler(json_console)

    # JSON Lines file: always enabled for log analysis tools
    json_handler = logging.handlers.RotatingFileHandler(
        json_log_path,
        maxBytes=20 * 1024 * 1024,
        backupCount=20,
        encoding="utf-8",
    )
    json_handler.setLevel(logging.DEBUG)
    json_handler.setFormatter(SanitizingJsonFormatter())
    logger.addHandler(json_handler)

    # Webhook handler (if configured)
    if LOG_WEBHOOK_URL:
        webhook_handler = WebhookLogHandler(LOG_WEBHOOK_URL, level=logging.WARNING)
        logger.addHandler(webhook_handler)

    # Syslog handler (if configured)
    if LOG_SYSLOG_HOST:
        try:
            parts = LOG_SYSLOG_HOST.split(":")
            host = parts[0]
            port = int(parts[1]) if len(parts) > 1 else 514
            syslog_handler = logging.handlers.SysLogHandler(address=(host, port))
            syslog_handler.setLevel(logging.WARNING)
            syslog_handler.setFormatter(SanitizingJsonFormatter())
            logger.addHandler(syslog_handler)
        except Exception as e:
            logger.error(f"Failed to configure syslog handler: {e}")


def log_task_event(task_id: str, event: str, **kwargs):
    """Append a structured JSON event for a task to tasks.jsonl."""
    entry = {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "task_id": task_id,
        "event": event,
        "request_id": get_request_id(),
        **kwargs,
    }
    try:
        with open(task_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception as e:
        logger.error(f"Failed to write task log: {e}")

    # Also log to main logger for unified log stream
    level = logging.WARNING if event in ("error", "cancel_requested", "vram_warning") else logging.INFO
    logger.log(
        level, f"TASK_EVENT [{task_id[:8]}] {event} {kwargs}" if kwargs else f"TASK_EVENT [{task_id[:8]}] {event}"
    )


def log_system_info(system_info: dict):
    """Legacy system info logger - now handled by system_capability module."""
    pass  # Replaced by detect_system_capabilities + log_capabilities
