"""Phase Lumen L62 — Advanced brute force protection tests.

Tests window pruning, expiry logic, and middleware response behavior.
— Scout (QA Lead)
"""

import time
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

from app.main import app
from app.middleware.brute_force import (
    MAX_FAILURES,
    WINDOW_SEC,
    _tracker,
    get_brute_force_stats,
    is_ip_blocked,
    record_auth_failure,
)


@pytest.fixture(autouse=True)
def clear_tracker():
    """Clear the brute force tracker between tests."""
    _tracker.clear()
    yield
    _tracker.clear()


# ══════════════════════════════════════════════════════════════════════════════
# WINDOW PRUNING
# ══════════════════════════════════════════════════════════════════════════════


class TestBruteForceWindowPruning:
    """Test that failures outside the window are pruned."""

    def test_old_failures_pruned(self):
        """Failures outside WINDOW_SEC are pruned."""
        ip = "10.0.0.1"
        old_time = time.time() - WINDOW_SEC - 10  # Outside window

        with patch("app.middleware.brute_force.time") as mock_time:
            # Record failures at old time
            mock_time.time.return_value = old_time
            for _ in range(MAX_FAILURES - 1):
                record_auth_failure(ip)

            # Now jump to current time — old failures should be pruned
            mock_time.time.return_value = time.time()
            record_auth_failure(ip)

        # Only 1 failure should remain (the recent one), not blocked
        assert is_ip_blocked(ip) is False
        assert len(_tracker[ip]["failures"]) == 1

    def test_max_minus_one_does_not_block(self):
        """Exactly MAX_FAILURES-1 within window does not block."""
        ip = "10.0.0.2"
        for _ in range(MAX_FAILURES - 1):
            record_auth_failure(ip)

        assert is_ip_blocked(ip) is False

    def test_max_failures_blocks(self):
        """MAX_FAILURES within window blocks IP."""
        ip = "10.0.0.3"
        for _ in range(MAX_FAILURES):
            record_auth_failure(ip)

        assert is_ip_blocked(ip) is True


# ══════════════════════════════════════════════════════════════════════════════
# EXPIRY
# ══════════════════════════════════════════════════════════════════════════════


class TestBruteForceExpiry:
    """Test block expiration logic."""

    def test_expired_block_returns_false(self):
        """IP blocked_until in past -> is_ip_blocked returns False."""
        ip = "10.0.0.4"
        _tracker[ip] = {
            "failures": [],
            "blocked_until": time.time() - 1,  # In the past
        }
        assert is_ip_blocked(ip) is False

    def test_stats_zero_when_all_expired(self):
        """get_brute_force_stats currently_blocked=0 when all blocks expired."""
        _tracker["10.0.0.5"] = {
            "failures": [],
            "blocked_until": time.time() - 100,
        }
        _tracker["10.0.0.6"] = {
            "failures": [],
            "blocked_until": time.time() - 200,
        }
        stats = get_brute_force_stats()
        assert stats["currently_blocked"] == 0
        assert stats["tracked_ips"] == 2


# ══════════════════════════════════════════════════════════════════════════════
# MIDDLEWARE RESPONSE
# ══════════════════════════════════════════════════════════════════════════════


class TestBruteForceMiddlewareResponse:
    """Test the HTTP responses from BruteForceMiddleware."""

    def test_blocked_ip_gets_429(self):
        """429 response body has expected detail message."""
        client = TestClient(app, base_url="https://testserver")

        # Block the testclient IP
        with patch("app.middleware.brute_force.is_ip_blocked", return_value=True):
            resp = client.get("/health")

        assert resp.status_code == 429
        assert resp.json()["detail"] == "Too many failed attempts. Your IP is temporarily blocked for 10 minutes."

    def test_non_blocked_ip_passes(self):
        """Non-blocked IP passes through (200)."""
        client = TestClient(app, base_url="https://testserver")

        with patch("app.middleware.brute_force.is_ip_blocked", return_value=False):
            resp = client.get("/health")

        assert resp.status_code == 200
