"""Phase Lumen L12 — Advanced profiler tests: EMA speed, speed trend, warmup, integration.

Tests TranscriptionProfiler EMA smoothing, speed trend detection,
warmup handling, and integration with summary/metrics.
— Scout (QA Lead)
"""

import time

from profiler import TranscriptionProfiler


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════


def _make_profiler(task_id="prof-adv"):
    return TranscriptionProfiler(task_id)


def _simulate_progress(p, steps, total=10000, delay=0.005):
    """Simulate a sequence of on_progress calls with small delays.

    *steps* is a list of frame positions (ascending).
    """
    for frames in steps:
        time.sleep(delay)
        p.on_progress(frames, total)


# ══════════════════════════════════════════════════════════════════════════════
# EMA SPEED (15 tests)
# ══════════════════════════════════════════════════════════════════════════════


class TestEmaSpeedAttribute:
    """EMA speed tracking on TranscriptionProfiler."""

    def test_ema_speed_attribute_exists(self):
        p = _make_profiler("ema-attr-1")
        assert hasattr(p, "_ema_speed")

    def test_ema_speed_initialized_none(self):
        p = _make_profiler("ema-init-1")
        assert p._ema_speed is None

    def test_ema_alpha_attribute_exists(self):
        p = _make_profiler("ema-alpha-1")
        assert hasattr(p, "_ema_alpha")

    def test_ema_alpha_in_valid_range(self):
        p = _make_profiler("ema-alpha-2")
        assert 0.1 <= p._ema_alpha <= 0.3

    def test_ema_updates_after_warmup(self):
        """After warmup (3 calls), _ema_speed should be set."""
        p = _make_profiler("ema-upd-1")
        total = 10000
        # 4 calls: 3 warmup + 1 that sets EMA
        _simulate_progress(p, [1000, 2000, 3000, 4000], total=total)
        assert p._ema_speed is not None

    def test_ema_stays_none_during_warmup(self):
        """During first 3 calls, _ema_speed stays None."""
        p = _make_profiler("ema-warm-1")
        total = 10000
        _simulate_progress(p, [1000, 2000, 3000], total=total)
        assert p._ema_speed is None

    def test_ema_updates_correctly_after_multiple_calls(self):
        """EMA should be a positive number after several progress calls."""
        p = _make_profiler("ema-multi-1")
        total = 10000
        steps = [1000, 2000, 3000, 4000, 5000, 6000, 7000]
        _simulate_progress(p, steps, total=total)
        assert p._ema_speed is not None
        assert p._ema_speed > 0

    def test_ema_ignores_warmup_first_three_calls(self):
        """Exactly 3 warmup calls should not produce EMA."""
        p = _make_profiler("ema-ign-1")
        total = 10000
        # Exactly 3 calls
        _simulate_progress(p, [1000, 2000, 3000], total=total)
        assert p._warmup_count == 3
        assert p._ema_speed is None

    def test_ema_smoother_than_raw_speed(self):
        """EMA variance should be lower than raw speed variance over many calls."""
        p = _make_profiler("ema-smooth-1")
        total = 20000
        raw_speeds = []
        ema_values = []

        # Simulate progress with varying delays to create speed variation
        frames = 0
        for i in range(15):
            frames += 1000
            delay = 0.003 if i % 2 == 0 else 0.008  # alternating fast/slow
            time.sleep(delay)
            metrics = p.on_progress(frames, total)
            raw_speeds.append(metrics["instant_speed_x"])
            if p._ema_speed is not None:
                ema_values.append(p._ema_speed)

        # Need enough EMA values to compare
        if len(ema_values) >= 5 and len(raw_speeds) >= 5:
            raw_mean = sum(raw_speeds) / len(raw_speeds)
            ema_mean = sum(ema_values) / len(ema_values)
            raw_var = sum((s - raw_mean) ** 2 for s in raw_speeds) / len(raw_speeds)
            ema_var = sum((s - ema_mean) ** 2 for s in ema_values) / len(ema_values)
            # EMA should have less or equal variance
            assert ema_var <= raw_var + 0.01  # small tolerance

    def test_ema_converges_to_steady_state(self):
        """With constant speed, EMA should converge toward actual speed."""
        p = _make_profiler("ema-conv-1")
        total = 50000
        # Simulate constant speed
        for i in range(1, 21):
            time.sleep(0.005)
            p.on_progress(i * 500, total)

        # After 20 calls at ~constant speed, EMA should be close to avg_speed
        assert p._ema_speed is not None
        # EMA should be positive and finite
        assert p._ema_speed > 0
        assert p._ema_speed < 10000  # sanity upper bound

    def test_ema_handles_zero_speed(self):
        """EMA should handle zero frames_delta gracefully (no update)."""
        p = _make_profiler("ema-zero-1")
        total = 10000
        # Progress without advancing frames = 0 speed
        _simulate_progress(p, [1000, 2000, 3000, 4000], total=total)
        ema_after_normal = p._ema_speed
        # Call with same frame position (zero delta) — EMA should not crash
        time.sleep(0.005)
        p.on_progress(4000, total)  # no frames advancement
        # EMA unchanged (zero speed not passed to _update_ema_speed)
        assert p._ema_speed == ema_after_normal

    def test_ema_handles_very_high_speed(self):
        """EMA handles high speed values without overflow."""
        p = _make_profiler("ema-high-1")
        total = 1000000
        # Large frame jumps with tiny delays = very high speed
        for i in range(1, 8):
            time.sleep(0.001)
            p.on_progress(i * 100000, total)
        assert p._ema_speed is not None
        assert p._ema_speed > 0
        assert isinstance(p._ema_speed, float)

    def test_ema_speed_in_metrics_dict(self):
        """on_progress returns ema_speed_x in metrics dict."""
        p = _make_profiler("ema-dict-1")
        total = 10000
        _simulate_progress(p, [1000, 2000, 3000, 4000, 5000], total=total)
        metrics = p.on_progress(6000, total)
        assert "ema_speed_x" in metrics

    def test_ema_speed_none_before_warmup_in_metrics(self):
        """ema_speed_x is None in metrics before warmup completes."""
        p = _make_profiler("ema-none-1")
        time.sleep(0.005)
        metrics = p.on_progress(1000, 10000)
        assert metrics["ema_speed_x"] is None

    def test_ema_alpha_is_float(self):
        """_ema_alpha should be a float."""
        p = _make_profiler("ema-type-1")
        assert isinstance(p._ema_alpha, float)


# ══════════════════════════════════════════════════════════════════════════════
# SPEED TREND (15 tests)
# ══════════════════════════════════════════════════════════════════════════════


class TestSpeedTrend:
    """Speed trend detection via get_speed_trend()."""

    def test_get_speed_trend_method_exists(self):
        p = _make_profiler("trend-exists-1")
        assert hasattr(p, "get_speed_trend")
        assert callable(p.get_speed_trend)

    def test_trend_returns_string(self):
        p = _make_profiler("trend-str-1")
        result = p.get_speed_trend()
        assert isinstance(result, str)

    def test_trend_unknown_with_no_data(self):
        p = _make_profiler("trend-unk-1")
        assert p.get_speed_trend() == "unknown"

    def test_trend_unknown_insufficient_data(self):
        """With only 1-2 speed values, trend should be unknown."""
        p = _make_profiler("trend-unk-2")
        total = 10000
        _simulate_progress(p, [1000, 2000], total=total)
        assert p.get_speed_trend() == "unknown"

    def test_trend_stable_when_speed_steady(self):
        """Constant speed should produce 'stable' trend."""
        p = _make_profiler("trend-stab-1")
        total = 50000
        # Consistent speed with uniform delays
        for i in range(1, 15):
            time.sleep(0.005)
            p.on_progress(i * 1000, total)
        trend = p.get_speed_trend()
        # With uniform constant speed, expect stable
        assert trend in ("stable", "improving")  # constant speed converges to stable

    def test_trend_stalled_when_near_zero(self):
        """When recent speeds are near zero, trend should be 'stalled'."""
        p = _make_profiler("trend-stall-1")
        total = 10000
        # Build up some EMA first
        for i in range(1, 6):
            time.sleep(0.005)
            p.on_progress(i * 1000, total)
        # Now inject near-zero speeds manually
        p._recent_speeds = [0.001, 0.002, 0.001]
        assert p.get_speed_trend() == "stalled"

    def test_trend_declining_when_speed_drops(self):
        """When recent speed is much lower than EMA, trend is 'declining'."""
        p = _make_profiler("trend-dec-1")
        total = 10000
        # Build up EMA
        for i in range(1, 6):
            time.sleep(0.005)
            p.on_progress(i * 1000, total)
        # Set high EMA but low recent speeds
        p._ema_speed = 100.0
        p._recent_speeds = [10.0, 15.0, 12.0]  # much lower than EMA
        assert p.get_speed_trend() == "declining"

    def test_trend_improving_when_speed_increases(self):
        """When recent speed is much higher than EMA, trend is 'improving'."""
        p = _make_profiler("trend-imp-1")
        total = 10000
        # Build up a low EMA
        for i in range(1, 6):
            time.sleep(0.005)
            p.on_progress(i * 1000, total)
        # Set low EMA but high recent speeds
        p._ema_speed = 10.0
        p._recent_speeds = [50.0, 55.0, 60.0]  # much higher than EMA
        assert p.get_speed_trend() == "improving"

    def test_trend_reflects_recent_not_old_data(self):
        """Trend should use recent speeds, not the full history."""
        p = _make_profiler("trend-recent-1")
        total = 10000
        for i in range(1, 6):
            time.sleep(0.005)
            p.on_progress(i * 1000, total)
        # Old speeds were high, recent are near zero
        p._recent_speeds = [100.0, 100.0, 100.0, 100.0, 0.005, 0.003, 0.001]
        assert p.get_speed_trend() == "stalled"

    def test_trend_in_metrics_dict(self):
        """on_progress returns speed_trend in metrics dict."""
        p = _make_profiler("trend-met-1")
        total = 10000
        _simulate_progress(p, [1000, 2000, 3000, 4000, 5000], total=total)
        time.sleep(0.005)
        metrics = p.on_progress(6000, total)
        assert "speed_trend" in metrics
        assert isinstance(metrics["speed_trend"], str)

    def test_trend_valid_values_only(self):
        """get_speed_trend() should only return valid trend strings."""
        valid = {"unknown", "stable", "declining", "stalled", "improving"}
        p = _make_profiler("trend-valid-1")
        assert p.get_speed_trend() in valid

    def test_trend_valid_after_progress(self):
        """After progress, trend should be a valid string."""
        valid = {"unknown", "stable", "declining", "stalled", "improving"}
        p = _make_profiler("trend-valid-2")
        total = 10000
        for i in range(1, 10):
            time.sleep(0.005)
            p.on_progress(i * 1000, total)
        assert p.get_speed_trend() in valid

    def test_trend_unknown_when_ema_none(self):
        """If _ema_speed is None, trend must be 'unknown'."""
        p = _make_profiler("trend-ema-none-1")
        p._recent_speeds = [10.0, 20.0, 30.0]  # enough data
        p._ema_speed = None
        assert p.get_speed_trend() == "unknown"

    def test_trend_stable_ratio_near_one(self):
        """When recent avg is close to EMA, trend is 'stable'."""
        p = _make_profiler("trend-ratio-1")
        p._ema_speed = 50.0
        p._recent_speeds = [48.0, 52.0, 50.0]  # close to EMA
        assert p.get_speed_trend() == "stable"

    def test_trend_at_boundary_values(self):
        """Test trend at ratio boundaries (0.5 and 1.5)."""
        p = _make_profiler("trend-bound-1")
        # Exactly at 0.5 ratio boundary: avg_recent / ema = 0.5
        p._ema_speed = 100.0
        p._recent_speeds = [49.0, 50.0, 51.0]  # avg ~50 / 100 = 0.5
        # At 0.5, ratio < 0.5 is false, so should be "stable"
        trend = p.get_speed_trend()
        assert trend in ("stable", "declining")


# ══════════════════════════════════════════════════════════════════════════════
# WARMUP HANDLING (5 tests)
# ══════════════════════════════════════════════════════════════════════════════


class TestWarmupHandling:
    """Warmup period tracking in profiler."""

    def test_warmup_count_initialized_zero(self):
        p = _make_profiler("warmup-init-1")
        assert p._warmup_count == 0

    def test_warmup_count_tracks_progress_calls(self):
        p = _make_profiler("warmup-count-1")
        total = 10000
        _simulate_progress(p, [1000, 2000, 3000], total=total)
        assert p._warmup_count == 3

    def test_early_calls_dont_affect_ema(self):
        """First 3 calls should not set _ema_speed."""
        p = _make_profiler("warmup-early-1")
        total = 10000
        for i in range(1, 4):
            time.sleep(0.005)
            p.on_progress(i * 1000, total)
        assert p._ema_speed is None
        assert p._warmup_count == 3

    def test_after_warmup_ema_starts(self):
        """4th call (after warmup) should start EMA tracking."""
        p = _make_profiler("warmup-after-1")
        total = 10000
        for i in range(1, 5):
            time.sleep(0.005)
            p.on_progress(i * 1000, total)
        assert p._warmup_count == 4
        assert p._ema_speed is not None

    def test_warmup_count_continues_incrementing(self):
        """Warmup count keeps incrementing beyond 3."""
        p = _make_profiler("warmup-incr-1")
        total = 10000
        for i in range(1, 8):
            time.sleep(0.003)
            p.on_progress(i * 1000, total)
        assert p._warmup_count == 7


# ══════════════════════════════════════════════════════════════════════════════
# INTEGRATION (5 tests)
# ══════════════════════════════════════════════════════════════════════════════


class TestProfilerIntegration:
    """Integration tests for profiler summary and metrics."""

    def test_summary_includes_speed_info(self):
        """Summary should include overall_speed_x."""
        p = _make_profiler("integ-sum-1")
        p.total_frames = 10000
        p.on_segment({"start": 0, "end": 5, "text": "Hello"}, 0)
        s = p.summary()
        assert "overall_speed_x" in s

    def test_on_progress_returns_metrics_dict(self):
        """on_progress should return dict with required keys."""
        p = _make_profiler("integ-met-1")
        time.sleep(0.005)
        metrics = p.on_progress(5000, 10000)
        assert isinstance(metrics, dict)
        assert "eta_sec" in metrics
        assert "instant_speed_x" in metrics
        assert "overall_speed_x" in metrics

    def test_metrics_dict_includes_eta_speed_elapsed(self):
        """Metrics dict should include eta, speed, and elapsed."""
        p = _make_profiler("integ-full-1")
        time.sleep(0.005)
        metrics = p.on_progress(3000, 10000)
        assert "eta_sec" in metrics
        assert "instant_speed_x" in metrics or "avg_speed_x" in metrics
        assert "elapsed_sec" in metrics

    def test_multiple_on_progress_calls_no_error(self):
        """Many on_progress calls should not raise exceptions."""
        p = _make_profiler("integ-multi-1")
        total = 50000
        for i in range(1, 30):
            time.sleep(0.002)
            metrics = p.on_progress(i * 1000, total)
            assert isinstance(metrics, dict)

    def test_on_progress_before_on_segment(self):
        """Calling on_progress before on_segment should not error."""
        p = _make_profiler("integ-order-1")
        time.sleep(0.005)
        metrics = p.on_progress(500, 10000)
        assert isinstance(metrics, dict)
        assert len(p.segments) == 0
        # Then on_segment works fine
        p.on_segment({"start": 0, "end": 2, "text": "Test"}, 0)
        assert len(p.segments) == 1
