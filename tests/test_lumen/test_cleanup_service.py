"""Phase Lumen L9 — File cleanup service tests.

Tests automatic file cleanup: retention period enforcement, active
task file preservation, dry-run mode, and configuration.
— Scout (QA Lead)
"""

import time

from app.services.cleanup import (
    CLEANUP_INTERVAL_SECONDS,
    DEFAULT_RETENTION_SECONDS,
    cleanup_old_files,
)

# ══════════════════════════════════════════════════════════════════════════════
# CLEANUP OLD FILES
# ══════════════════════════════════════════════════════════════════════════════


class TestCleanupOldFiles:
    """Test cleanup_old_files function."""

    def test_cleanup_empty_directory(self, tmp_path):
        result = cleanup_old_files(tmp_path, max_age_seconds=3600)
        assert result["checked"] == 0
        assert result["removed"] == 0
        assert result["errors"] == 0

    def test_cleanup_nonexistent_directory(self, tmp_path):
        nonexistent = tmp_path / "does_not_exist"
        result = cleanup_old_files(nonexistent, max_age_seconds=3600)
        assert result["checked"] == 0
        assert result["removed"] == 0

    def test_cleanup_removes_old_file(self, tmp_path):
        old_file = tmp_path / "old_file.srt"
        old_file.write_text("old content")
        # Set mtime to 2 hours ago
        old_mtime = time.time() - 7200
        import os

        os.utime(old_file, (old_mtime, old_mtime))
        result = cleanup_old_files(tmp_path, max_age_seconds=3600)
        assert result["removed"] == 1
        assert not old_file.exists()

    def test_cleanup_preserves_recent_file(self, tmp_path):
        recent_file = tmp_path / "recent_file.srt"
        recent_file.write_text("recent content")
        result = cleanup_old_files(tmp_path, max_age_seconds=3600)
        assert result["removed"] == 0
        assert recent_file.exists()

    def test_cleanup_result_has_directory(self, tmp_path):
        result = cleanup_old_files(tmp_path, max_age_seconds=3600)
        assert "directory" in result

    def test_cleanup_result_has_checked(self, tmp_path):
        result = cleanup_old_files(tmp_path, max_age_seconds=3600)
        assert "checked" in result

    def test_cleanup_result_has_freed_bytes(self, tmp_path):
        result = cleanup_old_files(tmp_path, max_age_seconds=3600)
        assert "freed_bytes" in result

    def test_cleanup_counts_checked_files(self, tmp_path):
        for i in range(5):
            (tmp_path / f"file_{i}.txt").write_text("data")
        result = cleanup_old_files(tmp_path, max_age_seconds=3600)
        assert result["checked"] == 5

    def test_cleanup_skips_directories(self, tmp_path):
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        result = cleanup_old_files(tmp_path, max_age_seconds=3600)
        assert result["checked"] == 0
        assert subdir.exists()

    def test_cleanup_frees_bytes(self, tmp_path):
        old_file = tmp_path / "big_file.wav"
        old_file.write_bytes(b"\x00" * 1024)
        import os

        old_mtime = time.time() - 7200
        os.utime(old_file, (old_mtime, old_mtime))
        result = cleanup_old_files(tmp_path, max_age_seconds=3600)
        assert result["freed_bytes"] >= 1024

    def test_cleanup_multiple_old_files(self, tmp_path):
        import os

        old_mtime = time.time() - 7200
        for i in range(3):
            f = tmp_path / f"old_{i}.srt"
            f.write_text("old")
            os.utime(f, (old_mtime, old_mtime))
        result = cleanup_old_files(tmp_path, max_age_seconds=3600)
        assert result["removed"] == 3

    def test_cleanup_mixed_old_and_new(self, tmp_path):
        import os

        old_mtime = time.time() - 7200
        old_f = tmp_path / "old.srt"
        old_f.write_text("old")
        os.utime(old_f, (old_mtime, old_mtime))
        new_f = tmp_path / "new.srt"
        new_f.write_text("new")
        result = cleanup_old_files(tmp_path, max_age_seconds=3600)
        assert result["removed"] == 1
        assert result["checked"] == 2
        assert not old_f.exists()
        assert new_f.exists()


# ══════════════════════════════════════════════════════════════════════════════
# DRY RUN MODE
# ══════════════════════════════════════════════════════════════════════════════


class TestCleanupDryRun:
    """Test dry_run mode (report without deleting)."""

    def test_dry_run_does_not_delete(self, tmp_path):
        import os

        old_file = tmp_path / "dry_run_test.srt"
        old_file.write_text("keep me")
        old_mtime = time.time() - 7200
        os.utime(old_file, (old_mtime, old_mtime))
        result = cleanup_old_files(tmp_path, max_age_seconds=3600, dry_run=True)
        assert result["removed"] == 1  # reports as removed
        assert old_file.exists()  # but file still exists

    def test_dry_run_reports_freed_bytes(self, tmp_path):
        import os

        old_file = tmp_path / "dry_run_size.wav"
        old_file.write_bytes(b"\x00" * 512)
        old_mtime = time.time() - 7200
        os.utime(old_file, (old_mtime, old_mtime))
        result = cleanup_old_files(tmp_path, max_age_seconds=3600, dry_run=True)
        assert result["freed_bytes"] >= 512

    def test_dry_run_preserves_recent(self, tmp_path):
        recent = tmp_path / "recent_dry.txt"
        recent.write_text("recent")
        result = cleanup_old_files(tmp_path, max_age_seconds=3600, dry_run=True)
        assert result["removed"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# RETENTION CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════


class TestRetentionConfiguration:
    """Test retention period configuration."""

    def test_default_retention_24_hours(self):
        assert DEFAULT_RETENTION_SECONDS == 24 * 3600

    def test_cleanup_interval_30_minutes(self):
        assert CLEANUP_INTERVAL_SECONDS == 30 * 60

    def test_custom_retention_short(self, tmp_path):
        import os

        f = tmp_path / "short_retention.txt"
        f.write_text("data")
        old_mtime = time.time() - 120  # 2 minutes old
        os.utime(f, (old_mtime, old_mtime))
        result = cleanup_old_files(tmp_path, max_age_seconds=60)
        assert result["removed"] == 1

    def test_custom_retention_long(self, tmp_path):
        import os

        f = tmp_path / "long_retention.txt"
        f.write_text("data")
        old_mtime = time.time() - 3600  # 1 hour old
        os.utime(f, (old_mtime, old_mtime))
        result = cleanup_old_files(tmp_path, max_age_seconds=86400)
        assert result["removed"] == 0

    def test_exact_boundary_not_removed(self, tmp_path):
        # File exactly at boundary should not be removed (age == max_age)
        f = tmp_path / "boundary.txt"
        f.write_text("data")
        # File is 0 seconds old, max_age is 1 second
        result = cleanup_old_files(tmp_path, max_age_seconds=1)
        assert result["removed"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# ERROR HANDLING
# ══════════════════════════════════════════════════════════════════════════════


class TestCleanupErrorHandling:
    """Test cleanup error handling."""

    def test_errors_counted(self, tmp_path):
        # A directory that exists but all files are normal should have 0 errors
        f = tmp_path / "normal.txt"
        f.write_text("data")
        result = cleanup_old_files(tmp_path, max_age_seconds=3600)
        assert result["errors"] == 0

    def test_result_always_has_all_keys(self, tmp_path):
        result = cleanup_old_files(tmp_path, max_age_seconds=3600)
        assert "directory" in result
        assert "checked" in result
        assert "removed" in result
        assert "freed_bytes" in result
        assert "errors" in result
