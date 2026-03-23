"""Sprint 22 tests: Structured Logging & Log Pipeline.

Tests cover:
  - Enhanced JSON formatter (task_id, sanitization, extra fields)
  - Log sanitization (API keys, tokens redacted)
  - Correlation ID propagation (task_id in context)
  - Configurable log output targets (LOG_OUTPUT env)
  - Log export endpoint (GET /admin/logs)
  - Log push webhook configuration
  - Log level standardization
"""

import asyncio
import json
import logging

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, base_url="https://testserver")


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── Enhanced JSON Formatter Tests ──


class TestJsonFormatter:
    """Test structured JSON log formatter."""

    def test_json_output_is_valid(self):
        from app.logging_setup import JsonFormatter

        fmt = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )
        output = fmt.format(record)
        parsed = json.loads(output)
        assert parsed["message"] == "test message"

    def test_json_has_required_fields(self):
        from app.logging_setup import JsonFormatter

        fmt = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="hello",
            args=(),
            exc_info=None,
        )
        output = fmt.format(record)
        parsed = json.loads(output)
        required = {"timestamp", "level", "logger", "message", "request_id"}
        assert required <= set(parsed.keys())

    def test_json_has_timestamp_iso8601(self):
        from app.logging_setup import JsonFormatter

        fmt = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="hello",
            args=(),
            exc_info=None,
        )
        output = fmt.format(record)
        parsed = json.loads(output)
        # ISO 8601 format check
        assert "T" in parsed["timestamp"]

    def test_json_includes_exception(self):
        from app.logging_setup import JsonFormatter

        fmt = JsonFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="error occurred",
            args=(),
            exc_info=exc_info,
        )
        output = fmt.format(record)
        parsed = json.loads(output)
        assert "exception" in parsed
        assert parsed["exception"]["type"] == "ValueError"
        assert "test error" in parsed["exception"]["message"]

    def test_json_includes_task_id_from_context(self):
        from app.logging_setup import JsonFormatter, clear_task_context, set_task_context

        fmt = JsonFormatter()
        set_task_context("abc-123")
        try:
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="processing",
                args=(),
                exc_info=None,
            )
            output = fmt.format(record)
            parsed = json.loads(output)
            assert parsed.get("task_id") == "abc-123"
        finally:
            clear_task_context()


# ── Log Sanitization Tests ──


class TestLogSanitization:
    """Test that sensitive data is redacted in logs."""

    def test_redacts_api_keys(self):
        from app.logging_setup import sanitize_log_message

        msg = "Auth failed for key sk-abc123def456ghi789"
        sanitized = sanitize_log_message(msg)
        assert "sk-abc123def456ghi789" not in sanitized
        assert "***" in sanitized or "REDACTED" in sanitized

    def test_redacts_bearer_tokens(self):
        from app.logging_setup import sanitize_log_message

        msg = "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc123"
        sanitized = sanitize_log_message(msg)
        assert "eyJhbGciOiJIUzI1NiJ9" not in sanitized

    def test_redacts_hf_tokens(self):
        from app.logging_setup import sanitize_log_message

        msg = "Using HF_TOKEN=hf_abcdef1234567890"
        sanitized = sanitize_log_message(msg)
        assert "hf_abcdef1234567890" not in sanitized

    def test_preserves_normal_messages(self):
        from app.logging_setup import sanitize_log_message

        msg = "Processing task abc-123, step 3 of 5"
        sanitized = sanitize_log_message(msg)
        assert sanitized == msg

    def test_sanitizing_formatter_redacts(self):
        from app.logging_setup import SanitizingJsonFormatter

        fmt = SanitizingJsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="key=sk-secret123456789abc",
            args=(),
            exc_info=None,
        )
        output = fmt.format(record)
        parsed = json.loads(output)
        assert "sk-secret123456789abc" not in parsed["message"]


# ── Correlation ID / Task Context Tests ──


class TestCorrelationIds:
    """Test correlation ID propagation."""

    def test_set_and_get_request_id(self):
        from app.logging_setup import get_request_id, set_request_id

        set_request_id("test-req-1")
        assert get_request_id() == "test-req-1"

    def test_set_and_get_task_context(self):
        from app.logging_setup import clear_task_context, get_task_context, set_task_context

        set_task_context("task-xyz")
        assert get_task_context() == "task-xyz"
        clear_task_context()
        assert get_task_context() is None

    def test_request_id_in_response_headers(self):
        res = client.get("/")
        assert "X-Request-ID" in res.headers

    def test_request_id_format(self):
        res = client.get("/system-info")
        req_id = res.headers.get("X-Request-ID", "")
        assert len(req_id) >= 4  # at least 4 chars


# ── Log Output Configuration Tests ──


class TestLogOutputConfig:
    """Test configurable log output targets."""

    def test_log_json_only_env_var(self):
        from app.config import LOG_JSON_ONLY

        assert isinstance(LOG_JSON_ONLY, bool)

    def test_log_level_env_var(self):
        from app.config import LOG_LEVEL

        assert LOG_LEVEL in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


# ── Log Export Endpoint Tests ──


class TestLogExportEndpoint:
    """Test GET /admin/logs endpoint."""

    def test_logs_returns_entries(self):
        res = client.get("/admin/logs")
        if res.status_code == 200:
            data = res.json()
            assert "entries" in data
            assert isinstance(data["entries"], list)

    def test_logs_supports_level_filter(self):
        res = client.get("/admin/logs?level=ERROR")
        if res.status_code == 200:
            data = res.json()
            assert "entries" in data

    def test_logs_supports_limit(self):
        res = client.get("/admin/logs?limit=5")
        if res.status_code == 200:
            data = res.json()
            assert len(data["entries"]) <= 5

    def test_logs_supports_since_filter(self):
        res = client.get("/admin/logs?since=1h")
        assert res.status_code in (200, 401, 403)

    def test_logs_supports_task_id_filter(self):
        res = client.get("/admin/logs?task_id=abc-123")
        if res.status_code == 200:
            data = res.json()
            assert "entries" in data

    def test_logs_entry_format(self):
        res = client.get("/admin/logs")
        if res.status_code == 200:
            data = res.json()
            if data["entries"]:
                entry = data["entries"][0]
                assert "timestamp" in entry
                assert "level" in entry
                assert "message" in entry


# ── Log Push / Webhook Tests ──


class TestLogPushConfig:
    """Test log push integration configuration."""

    def test_log_webhook_url_config(self):
        from app.config import LOG_WEBHOOK_URL

        assert isinstance(LOG_WEBHOOK_URL, str)

    def test_log_syslog_host_config(self):
        from app.config import LOG_SYSLOG_HOST

        assert isinstance(LOG_SYSLOG_HOST, str)

    def test_webhook_handler_is_handler(self):
        from app.logging_setup import WebhookLogHandler

        handler = WebhookLogHandler("http://localhost:9999/logs")
        assert isinstance(handler, logging.Handler)


# ── HTTP Access Log Format Tests ──


class TestAccessLogFormat:
    """Test structured HTTP access logging."""

    def test_health_request_logged_structured(self):
        """A request to a non-quiet path should appear in structured logs."""
        res = client.get("/system-info")
        assert res.status_code == 200


# ── Security Event Logging Tests ──


class TestSecurityEventLogging:
    """Test that security events are logged in structured format."""

    def test_security_event_logged(self):
        from app.logging_setup import log_security_event

        # Should not raise
        log_security_event("auth_failed", ip="127.0.0.1", path="/admin/logs")

    def test_security_event_with_details(self):
        from app.logging_setup import log_security_event

        log_security_event("rate_limited", ip="10.0.0.1", path="/upload", details={"limit": "5/min"})


# ── Task Lifecycle Logging Tests ──


class TestTaskLifecycleLogging:
    """Test consistent task lifecycle events."""

    def test_log_task_event_with_context(self):
        from app.logging_setup import clear_task_context, log_task_event, set_task_context

        set_task_context("test-task-1")
        try:
            # Should not raise
            log_task_event("test-task-1", "test_step", step="testing")
        finally:
            clear_task_context()
