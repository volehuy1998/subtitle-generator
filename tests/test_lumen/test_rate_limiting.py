"""Phase Lumen L9 — Rate limiting tests.

Tests rate limiter service, middleware behavior, brute force protection,
IP allowlist/blocklist, and rate limit headers.
— Scout (QA Lead)
"""

from app.middleware.brute_force import (
    BLOCK_SEC,
    MAX_FAILURES,
    WINDOW_SEC,
    _tracker,
    get_brute_force_stats,
    is_ip_blocked,
    record_auth_failure,
)
from app.services.rate_limiter import (
    DEFAULT_RATE_LIMIT,
    DEFAULT_WINDOW_SEC,
    UPLOAD_RATE_LIMIT,
    _buckets,
    _user_tasks,
    add_to_allowlist,
    add_to_blocklist,
    check_rate_limit,
    check_user_task_quota,
    decrement_user_tasks,
    get_ip_lists,
    get_rate_limit_headers,
    get_rate_limit_stats,
    get_user_task_count,
    increment_user_tasks,
    is_ip_allowed,
    remove_from_allowlist,
    remove_from_blocklist,
)

# ══════════════════════════════════════════════════════════════════════════════
# RATE LIMITER SERVICE
# ══════════════════════════════════════════════════════════════════════════════


class TestRateLimiterService:
    """Test check_rate_limit and related functions."""

    def test_first_request_allowed(self):
        key = "test_first_req_unique"
        try:
            allowed, info = check_rate_limit(key, limit=10, window=60)
            assert allowed is True
        finally:
            _buckets.pop(key, None)

    def test_remaining_decrements(self):
        key = "test_remaining_dec"
        try:
            _, info1 = check_rate_limit(key, limit=10, window=60)
            _, info2 = check_rate_limit(key, limit=10, window=60)
            assert info2["remaining"] < info1["remaining"]
        finally:
            _buckets.pop(key, None)

    def test_rate_limit_exceeded(self):
        key = "test_exceeded_unique"
        try:
            for _ in range(5):
                check_rate_limit(key, limit=5, window=60)
            allowed, info = check_rate_limit(key, limit=5, window=60)
            assert allowed is False
        finally:
            _buckets.pop(key, None)

    def test_retry_after_positive_when_exceeded(self):
        key = "test_retry_after"
        try:
            for _ in range(3):
                check_rate_limit(key, limit=3, window=60)
            _, info = check_rate_limit(key, limit=3, window=60)
            assert info["retry_after"] > 0
        finally:
            _buckets.pop(key, None)

    def test_retry_after_zero_when_allowed(self):
        key = "test_retry_zero"
        try:
            _, info = check_rate_limit(key, limit=10, window=60)
            assert info["retry_after"] == 0
        finally:
            _buckets.pop(key, None)

    def test_info_has_limit(self):
        key = "test_info_limit"
        try:
            _, info = check_rate_limit(key, limit=42, window=60)
            assert info["limit"] == 42
        finally:
            _buckets.pop(key, None)

    def test_info_has_window(self):
        key = "test_info_window"
        try:
            _, info = check_rate_limit(key, limit=10, window=120)
            assert info["window"] == 120
        finally:
            _buckets.pop(key, None)

    def test_remaining_is_zero_when_exhausted(self):
        key = "test_remaining_zero"
        try:
            for _ in range(5):
                check_rate_limit(key, limit=5, window=60)
            _, info = check_rate_limit(key, limit=5, window=60)
            assert info["remaining"] == 0
        finally:
            _buckets.pop(key, None)


# ══════════════════════════════════════════════════════════════════════════════
# RATE LIMIT HEADERS
# ══════════════════════════════════════════════════════════════════════════════


class TestRateLimitHeaders:
    """Test get_rate_limit_headers."""

    def test_headers_has_limit(self):
        headers = get_rate_limit_headers({"limit": 60, "remaining": 59, "retry_after": 0})
        assert "X-RateLimit-Limit" in headers
        assert headers["X-RateLimit-Limit"] == "60"

    def test_headers_has_remaining(self):
        headers = get_rate_limit_headers({"limit": 60, "remaining": 42, "retry_after": 0})
        assert "X-RateLimit-Remaining" in headers
        assert headers["X-RateLimit-Remaining"] == "42"

    def test_headers_no_retry_when_allowed(self):
        headers = get_rate_limit_headers({"limit": 60, "remaining": 59, "retry_after": 0})
        assert "Retry-After" not in headers

    def test_headers_has_retry_when_exceeded(self):
        headers = get_rate_limit_headers({"limit": 60, "remaining": 0, "retry_after": 30})
        assert "Retry-After" in headers
        assert headers["Retry-After"] == "30"


# ══════════════════════════════════════════════════════════════════════════════
# IP ALLOWLIST / BLOCKLIST
# ══════════════════════════════════════════════════════════════════════════════


class TestIPAllowlistBlocklist:
    """Test IP list management."""

    def test_add_to_blocklist(self):
        ip = "192.168.99.99"
        try:
            add_to_blocklist(ip)
            assert is_ip_allowed(ip) is False
        finally:
            remove_from_blocklist(ip)

    def test_remove_from_blocklist(self):
        ip = "192.168.99.98"
        add_to_blocklist(ip)
        remove_from_blocklist(ip)
        assert is_ip_allowed(ip) is None

    def test_add_to_allowlist(self):
        ip = "10.0.0.99"
        try:
            add_to_allowlist(ip)
            assert is_ip_allowed(ip) is True
        finally:
            remove_from_allowlist(ip)

    def test_remove_from_allowlist(self):
        ip = "10.0.0.98"
        add_to_allowlist(ip)
        remove_from_allowlist(ip)
        # Result depends on whether allowlist is empty
        result = is_ip_allowed(ip)
        assert result is None or result is False

    def test_blocklist_overrides_allowlist(self):
        ip = "172.16.0.99"
        try:
            add_to_allowlist(ip)
            add_to_blocklist(ip)
            assert is_ip_allowed(ip) is False
        finally:
            remove_from_allowlist(ip)
            remove_from_blocklist(ip)

    def test_unknown_ip_returns_none(self):
        assert is_ip_allowed("255.255.255.255") is None

    def test_get_ip_lists_structure(self):
        lists = get_ip_lists()
        assert "allowlist" in lists
        assert "blocklist" in lists
        assert isinstance(lists["allowlist"], list)
        assert isinstance(lists["blocklist"], list)


# ══════════════════════════════════════════════════════════════════════════════
# USER TASK QUOTA
# ══════════════════════════════════════════════════════════════════════════════


class TestUserTaskQuota:
    """Test per-user concurrent task limits."""

    def test_quota_allowed_initially(self):
        uid = "user-quota-test-1"
        try:
            assert check_user_task_quota(uid) is True
        finally:
            _user_tasks.pop(uid, None)

    def test_increment_user_tasks(self):
        uid = "user-quota-test-2"
        try:
            increment_user_tasks(uid)
            assert get_user_task_count(uid) == 1
        finally:
            _user_tasks.pop(uid, None)

    def test_decrement_user_tasks(self):
        uid = "user-quota-test-3"
        try:
            increment_user_tasks(uid)
            increment_user_tasks(uid)
            decrement_user_tasks(uid)
            assert get_user_task_count(uid) == 1
        finally:
            _user_tasks.pop(uid, None)

    def test_decrement_below_zero_stays_at_zero(self):
        uid = "user-quota-test-4"
        try:
            decrement_user_tasks(uid)
            assert get_user_task_count(uid) == 0
        finally:
            _user_tasks.pop(uid, None)

    def test_user_task_count_zero_initially(self):
        uid = "user-quota-test-5"
        assert get_user_task_count(uid) == 0


# ══════════════════════════════════════════════════════════════════════════════
# BRUTE FORCE PROTECTION
# ══════════════════════════════════════════════════════════════════════════════


class TestBruteForceProtection:
    """Test brute force tracking."""

    def test_ip_not_blocked_initially(self):
        assert is_ip_blocked("1.2.3.4") is False

    def test_single_failure_does_not_block(self):
        ip = "1.2.3.100"
        try:
            record_auth_failure(ip)
            assert is_ip_blocked(ip) is False
        finally:
            _tracker.pop(ip, None)

    def test_max_failures_blocks_ip(self):
        ip = "1.2.3.101"
        try:
            for _ in range(MAX_FAILURES):
                record_auth_failure(ip)
            assert is_ip_blocked(ip) is True
        finally:
            _tracker.pop(ip, None)

    def test_brute_force_stats_structure(self):
        stats = get_brute_force_stats()
        assert "tracked_ips" in stats
        assert "currently_blocked" in stats
        assert "max_failures" in stats
        assert "window_sec" in stats
        assert "block_sec" in stats

    def test_brute_force_constants(self):
        assert MAX_FAILURES == 10
        assert WINDOW_SEC == 300
        assert BLOCK_SEC == 600


# ══════════════════════════════════════════════════════════════════════════════
# RATE LIMIT STATS
# ══════════════════════════════════════════════════════════════════════════════


class TestRateLimitStats:
    """Test rate limit statistics."""

    def test_stats_structure(self):
        stats = get_rate_limit_stats()
        assert "active_buckets" in stats
        assert "allowlist_size" in stats
        assert "blocklist_size" in stats
        assert "tracked_users" in stats
        assert "per_user_max_tasks" in stats

    def test_default_rate_limit_value(self):
        assert DEFAULT_RATE_LIMIT == 60

    def test_default_window_value(self):
        assert DEFAULT_WINDOW_SEC == 60

    def test_upload_rate_limit_value(self):
        assert UPLOAD_RATE_LIMIT == 5
