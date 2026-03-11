"""Tests for app.utils.formatting - pure functions, no mocks needed."""

from app.utils.formatting import format_bytes, format_timestamp, format_time_display, format_time_short


class TestFormatBytes:
    def test_zero_bytes(self):
        assert format_bytes(0) == "0 B"

    def test_small_bytes(self):
        assert format_bytes(512) == "512 B"

    def test_one_byte(self):
        assert format_bytes(1) == "1 B"

    def test_just_below_kb(self):
        assert format_bytes(1023) == "1023 B"

    def test_exactly_1kb(self):
        assert format_bytes(1024) == "1.0 KB"

    def test_kilobytes(self):
        assert format_bytes(1536) == "1.5 KB"

    def test_megabytes(self):
        assert format_bytes(5 * 1024 * 1024) == "5.0 MB"

    def test_gigabytes(self):
        assert format_bytes(2 * 1024 * 1024 * 1024) == "2.00 GB"

    def test_large_gigabytes(self):
        assert format_bytes(10 * 1024 * 1024 * 1024) == "10.00 GB"

    def test_fractional_megabytes(self):
        assert "MB" in format_bytes(1_500_000)


class TestFormatTimestamp:
    def test_zero(self):
        assert format_timestamp(0) == "00:00:00,000"

    def test_one_second(self):
        assert format_timestamp(1.0) == "00:00:01,000"

    def test_fractional_second(self):
        assert format_timestamp(1.5) == "00:00:01,500"

    def test_one_minute(self):
        assert format_timestamp(60.0) == "00:01:00,000"

    def test_one_hour(self):
        assert format_timestamp(3600.0) == "01:00:00,000"

    def test_complex_time(self):
        seconds = 3600 + 23 * 60 + 45.5
        assert format_timestamp(seconds) == "01:23:45,500"

    def test_millisecond_precision(self):
        assert format_timestamp(0.123) == "00:00:00,123"

    def test_large_value(self):
        assert format_timestamp(36000.0) == "10:00:00,000"

    def test_small_fraction(self):
        assert format_timestamp(0.001) == "00:00:00,001"


class TestFormatTimeDisplay:
    def test_negative_returns_calculating(self):
        assert format_time_display(-1) == "calculating..."
        assert format_time_display(-0.5) == "calculating..."

    def test_zero_returns_less_than_1s(self):
        assert format_time_display(0) == "<1s"

    def test_half_second(self):
        assert format_time_display(0.5) == "<1s"

    def test_exactly_one_second(self):
        assert format_time_display(1) == "1s"

    def test_seconds_range(self):
        assert format_time_display(5) == "5s"
        assert format_time_display(59) == "59s"

    def test_one_minute(self):
        assert format_time_display(60) == "1m 0s"

    def test_minutes_and_seconds(self):
        assert format_time_display(150) == "2m 30s"

    def test_one_hour(self):
        assert format_time_display(3600) == "1h 0m"

    def test_hours_and_minutes(self):
        assert format_time_display(3900) == "1h 5m"

    def test_large_value(self):
        assert format_time_display(37800) == "10h 30m"


class TestFormatTimeShort:
    def test_zero(self):
        assert format_time_short(0) == "0:00.0"

    def test_one_second(self):
        assert format_time_short(1.0) == "0:01.0"

    def test_one_minute(self):
        assert format_time_short(60.0) == "1:00.0"

    def test_fractional(self):
        assert format_time_short(65.3) == "1:05.3"

    def test_large_value(self):
        assert format_time_short(630.5) == "10:30.5"
