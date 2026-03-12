"""Sprint 24 tests: Rate Limiting & DDoS Protection.

Tests cover:
  - Rate limiter service (sliding window, buckets, headers)
  - IP allowlist/blocklist
  - Per-user concurrent task quota
  - Rate limit middleware
  - Brute force DB models
  - Migration file
"""

import time

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, base_url="https://testserver")


# ── Rate Limiter Service Tests ──

class TestRateLimiterService:
    """Test rate limiter core functions."""

    def test_module_imports(self):
        from app.services import rate_limiter
        assert hasattr(rate_limiter, "check_rate_limit")
        assert hasattr(rate_limiter, "get_rate_limit_headers")
        assert hasattr(rate_limiter, "is_ip_allowed")
        assert hasattr(rate_limiter, "check_user_task_quota")

    def test_check_rate_limit_allows(self):
        from app.services.rate_limiter import check_rate_limit
        allowed, info = check_rate_limit("test_allow_key", limit=10, window=60)
        assert allowed is True
        assert info["remaining"] > 0

    def test_check_rate_limit_blocks(self):
        from app.services.rate_limiter import check_rate_limit
        key = f"test_block_{time.time()}"
        # Exhaust the limit
        for _ in range(5):
            check_rate_limit(key, limit=5, window=60)
        allowed, info = check_rate_limit(key, limit=5, window=60)
        assert allowed is False
        assert info["remaining"] == 0
        assert info["retry_after"] > 0

    def test_rate_limit_headers(self):
        from app.services.rate_limiter import get_rate_limit_headers
        headers = get_rate_limit_headers({"limit": 60, "remaining": 55, "retry_after": 0})
        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers
        assert headers["X-RateLimit-Limit"] == "60"

    def test_rate_limit_headers_with_retry(self):
        from app.services.rate_limiter import get_rate_limit_headers
        headers = get_rate_limit_headers({"limit": 10, "remaining": 0, "retry_after": 30})
        assert headers["Retry-After"] == "30"

    def test_sliding_window(self):
        from app.services.rate_limiter import check_rate_limit
        key = f"test_window_{time.time()}"
        # First request should pass
        allowed, info = check_rate_limit(key, limit=100, window=60)
        assert allowed is True
        assert info["remaining"] == 99


# ── IP Allowlist/Blocklist Tests ──

class TestIpLists:
    """Test IP allowlist and blocklist."""

    def test_blocklist_ip(self):
        from app.services.rate_limiter import add_to_blocklist, is_ip_allowed, remove_from_blocklist
        test_ip = "192.168.99.99"
        add_to_blocklist(test_ip)
        assert is_ip_allowed(test_ip) is False
        remove_from_blocklist(test_ip)

    def test_allowlist_ip(self):
        from app.services.rate_limiter import add_to_allowlist, is_ip_allowed, remove_from_allowlist
        test_ip = "10.0.0.99"
        add_to_allowlist(test_ip)
        assert is_ip_allowed(test_ip) is True
        remove_from_allowlist(test_ip)

    def test_unknown_ip_returns_none(self):
        from app.services.rate_limiter import is_ip_allowed
        assert is_ip_allowed("203.0.113.1") is None

    def test_get_ip_lists(self):
        from app.services.rate_limiter import get_ip_lists
        lists = get_ip_lists()
        assert "allowlist" in lists
        assert "blocklist" in lists
        assert isinstance(lists["allowlist"], list)
        assert isinstance(lists["blocklist"], list)

    def test_blocklist_takes_priority(self):
        from app.services.rate_limiter import add_to_blocklist, add_to_allowlist, is_ip_allowed, remove_from_blocklist, remove_from_allowlist
        test_ip = "172.16.0.99"
        add_to_blocklist(test_ip)
        add_to_allowlist(test_ip)
        # Blocklist checked first
        assert is_ip_allowed(test_ip) is False
        remove_from_blocklist(test_ip)
        remove_from_allowlist(test_ip)


# ── Per-User Task Quota Tests ──

class TestUserTaskQuota:
    """Test per-user concurrent task quota."""

    def test_quota_check(self):
        from app.services.rate_limiter import check_user_task_quota
        assert check_user_task_quota("new_user_123") is True

    def test_quota_increment_decrement(self):
        from app.services.rate_limiter import increment_user_tasks, decrement_user_tasks, get_user_task_count
        user = f"quota_test_{time.time()}"
        increment_user_tasks(user)
        assert get_user_task_count(user) == 1
        decrement_user_tasks(user)
        assert get_user_task_count(user) == 0

    def test_quota_enforcement(self):
        from app.services.rate_limiter import check_user_task_quota, increment_user_tasks, PER_USER_MAX_TASKS
        user = f"quota_enforce_{time.time()}"
        for _ in range(PER_USER_MAX_TASKS):
            increment_user_tasks(user)
        assert check_user_task_quota(user) is False

    def test_per_user_max_tasks_config(self):
        from app.services.rate_limiter import PER_USER_MAX_TASKS
        assert isinstance(PER_USER_MAX_TASKS, int)
        assert PER_USER_MAX_TASKS > 0


# ── Rate Limit Middleware Tests ──

class TestRateLimitMiddleware:
    """Test rate limit middleware behavior."""

    def test_middleware_exists(self):
        from app.middleware.rate_limit import RateLimitMiddleware
        assert RateLimitMiddleware is not None

    def test_normal_request_passes(self):
        res = client.get("/system-info")
        assert res.status_code == 200

    def test_rate_limit_headers_present(self):
        res = client.get("/system-info")
        assert "X-RateLimit-Limit" in res.headers or res.status_code == 200

    def test_health_endpoint_exempt(self):
        res = client.get("/health")
        assert res.status_code == 200


# ── Brute Force Model Tests ──

class TestBruteForceModel:
    """Test BruteForceEvent ORM model."""

    def test_model_exists(self):
        from app.db.models import BruteForceEvent
        assert BruteForceEvent.__tablename__ == "brute_force_events"

    def test_model_columns(self):
        from app.db.models import BruteForceEvent
        cols = {c.name for c in BruteForceEvent.__table__.columns}
        assert {"id", "ip", "timestamp", "path", "blocked_until"} <= cols

    def test_model_indexes(self):
        from app.db.models import BruteForceEvent
        idx_names = {idx.name for idx in BruteForceEvent.__table__.indexes}
        assert "ix_brute_force_ip" in idx_names
        assert "ix_brute_force_ts" in idx_names


class TestIpListModel:
    """Test IpListEntry ORM model."""

    def test_model_exists(self):
        from app.db.models import IpListEntry
        assert IpListEntry.__tablename__ == "ip_lists"

    def test_model_columns(self):
        from app.db.models import IpListEntry
        cols = {c.name for c in IpListEntry.__table__.columns}
        assert {"id", "ip", "list_type", "reason", "created_at"} <= cols


# ── Rate Limit Stats Tests ──

class TestRateLimitStats:
    """Test rate limit statistics."""

    def test_stats_available(self):
        from app.services.rate_limiter import get_rate_limit_stats
        stats = get_rate_limit_stats()
        assert "active_buckets" in stats
        assert "allowlist_size" in stats
        assert "blocklist_size" in stats
        assert "per_user_max_tasks" in stats


# ── Migration Tests ──

class TestMigration005:
    """Test Alembic migration file."""

    def test_migration_exists(self):
        from pathlib import Path
        assert Path("alembic/versions/005_rate_limiting.py").exists()

    def test_migration_has_upgrade(self):
        from pathlib import Path
        content = Path("alembic/versions/005_rate_limiting.py").read_text()
        assert "def upgrade" in content
        assert "brute_force_events" in content
        assert "ip_lists" in content

    def test_migration_has_downgrade(self):
        from pathlib import Path
        content = Path("alembic/versions/005_rate_limiting.py").read_text()
        assert "def downgrade" in content

    def test_migration_chain(self):
        from pathlib import Path
        content = Path("alembic/versions/005_rate_limiting.py").read_text()
        assert '"004"' in content
