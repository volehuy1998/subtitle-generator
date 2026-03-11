"""Tests for the profiler module."""

import time
from unittest.mock import MagicMock
from profiler import (
    snapshot_system, snapshot_gpu, format_snapshot_short,
    StepTimer, TranscriptionProfiler, PipelineSummary,
    ResourceMonitor, format_bytes_simple,
)
import sys


class TestSnapshotSystem:
    def test_returns_expected_keys(self):
        snap = snapshot_system()
        for key in ["timestamp", "cpu_percent", "cpu_freq_mhz", "cpu_count_logical",
                     "cpu_count_physical", "proc_cpu_percent", "proc_rss_mb",
                     "proc_vms_mb", "proc_threads", "ram_total_gb", "ram_used_gb",
                     "ram_available_gb", "ram_percent"]:
            assert key in snap, f"Missing key: {key}"

    def test_cpu_percent_is_numeric(self):
        assert isinstance(snapshot_system()["cpu_percent"], (int, float))

    def test_ram_total_gb_is_positive(self):
        assert snapshot_system()["ram_total_gb"] > 0

    def test_proc_rss_mb_is_positive(self):
        assert snapshot_system()["proc_rss_mb"] > 0

    def test_disk_io_keys_present(self):
        snap = snapshot_system()
        assert "disk_read_mb" in snap
        assert "disk_write_mb" in snap

    def test_timestamp_is_recent(self):
        before = time.time()
        snap = snapshot_system()
        after = time.time()
        assert before <= snap["timestamp"] <= after


class TestSnapshotGpu:
    def test_returns_empty_when_no_cuda(self):
        assert snapshot_gpu() == {}

    def test_returns_gpu_metrics_when_cuda_available(self):
        torch_mod = sys.modules["torch"]
        original = torch_mod.cuda.is_available.return_value
        try:
            torch_mod.cuda.is_available.return_value = True
            torch_mod.cuda.memory_allocated.return_value = 512 * 1024**2
            torch_mod.cuda.memory_reserved.return_value = 1024**3
            props = MagicMock()
            props.total_memory = 8 * 1024**3
            torch_mod.cuda.get_device_properties.return_value = props
            result = snapshot_gpu()
            assert "gpu_allocated_mb" in result
            assert result["gpu_allocated_mb"] == 512.0
        finally:
            torch_mod.cuda.is_available.return_value = original


class TestFormatSnapshotShort:
    def test_basic_output(self):
        snap = {"cpu_percent": 25.0, "ram_used_gb": 8.0, "ram_total_gb": 16.0,
                "ram_percent": 50.0, "proc_rss_mb": 200.0}
        result = format_snapshot_short(snap)
        assert "CPU=25.0%" in result
        assert "Proc=200.0MB" in result

    def test_includes_gpu_when_present(self):
        snap = {"cpu_percent": 10.0, "ram_used_gb": 4.0, "ram_total_gb": 16.0,
                "ram_percent": 25.0, "proc_rss_mb": 100.0,
                "gpu_allocated_mb": 512.0, "gpu_total_mb": 8192.0, "gpu_utilization_percent": 6.3}
        assert "GPU=" in format_snapshot_short(snap)


class TestStepTimer:
    def test_context_manager_measures_time(self):
        with StepTimer("test-task-1234", "test_step") as timer:
            time.sleep(0.05)
        assert timer.elapsed >= 0.04

    def test_elapsed_before_exit(self):
        assert StepTimer("test-task-1234", "test_step").elapsed == 0

    def test_step_name_preserved(self):
        with StepTimer("task123456789", "my_step") as timer:
            pass
        assert timer.step_name == "my_step"

    def test_task_log_func_called(self):
        log_func = MagicMock()
        with StepTimer("task123456789", "probe", task_log_func=log_func):
            pass
        log_func.assert_called_once()
        assert log_func.call_args[0][0] == "task123456789"
        assert log_func.call_args[0][1] == "step_probe"

    def test_sub_timings(self):
        with StepTimer("task123456789", "step") as timer:
            timer.mark_sub("sub_a")
            time.sleep(0.02)
            timer.mark_sub("sub_b")
            time.sleep(0.02)
            timer.end_sub()
        assert "sub_a" in timer.sub_timings
        assert "sub_b" in timer.sub_timings

    def test_does_not_suppress_exceptions(self):
        raised = False
        try:
            with StepTimer("task123456789", "fail_step"):
                raise ValueError("test error")
        except ValueError:
            raised = True
        assert raised

    def test_exception_logged(self):
        log_func = MagicMock()
        try:
            with StepTimer("task123456789", "fail_step", task_log_func=log_func):
                raise RuntimeError("boom")
        except RuntimeError:
            pass
        assert log_func.call_args[1]["status"] == "FAILED"
        assert "boom" in log_func.call_args[1]["error"]


class TestTranscriptionProfiler:
    def test_on_progress_returns_metrics(self):
        p = TranscriptionProfiler("task-abc12345")
        m = p.on_progress(100, 1000)
        assert m["ratio"] == 0.1
        assert "elapsed_sec" in m

    def test_on_progress_ratio_increases(self):
        p = TranscriptionProfiler("task-abc12345")
        m1 = p.on_progress(100, 1000)
        m2 = p.on_progress(500, 1000)
        assert m2["ratio"] > m1["ratio"]

    def test_on_segment_accumulates(self):
        p = TranscriptionProfiler("task-abc12345")
        p.on_segment({"start": 0, "end": 2, "text": "Hello"}, 1)
        p.on_segment({"start": 2, "end": 4.5, "text": "World"}, 2)
        assert len(p.segments) == 2

    def test_on_segment_captures_duration(self):
        p = TranscriptionProfiler("task-abc12345")
        p.on_segment({"start": 1, "end": 3.5, "text": "Test"}, 1)
        assert p.segments[0]["duration_sec"] == 2.5

    def test_on_segment_captures_text_length(self):
        p = TranscriptionProfiler("task-abc12345")
        p.on_segment({"start": 0, "end": 1, "text": "  Hello  "}, 1)
        assert p.segments[0]["text_length"] == 5

    def test_summary_produces_valid_dict(self):
        p = TranscriptionProfiler("task-abc12345")
        p.total_frames = 10000
        p.on_segment({"start": 0, "end": 5, "text": "Test"}, 1)
        s = p.summary()
        assert s["total_segments"] == 1
        assert "audio_duration_sec" in s

    def test_summary_segment_stats(self):
        p = TranscriptionProfiler("task-abc12345")
        p.total_frames = 10000
        p.on_segment({"start": 0, "end": 2, "text": "A"}, 1)
        p.on_segment({"start": 2, "end": 6, "text": "BB"}, 2)
        p.on_segment({"start": 6, "end": 8, "text": "CCC"}, 3)
        s = p.summary()
        assert s["seg_duration_min"] == 2.0
        assert s["seg_duration_max"] == 4.0

    def test_summary_empty_profiler(self):
        p = TranscriptionProfiler("task-abc12345")
        p.total_frames = 0
        s = p.summary()
        assert s["total_segments"] == 0


class TestPipelineSummary:
    def test_record_step(self):
        ps = PipelineSummary("task-123456", "video.mp4", "medium", "cuda")
        ps.record_step("probe", 0.1234)
        assert ps.step_timings["probe"] == 0.1234

    def test_finalize_returns_dict(self):
        ps = PipelineSummary("task-123456", "test.mp4", "small", "cpu")
        ps.record_step("probe", 0.1)
        ps.file_size = 1024 * 1024
        ps.audio_duration = 60.0
        result = ps.finalize(status="complete")
        assert result["status"] == "complete"
        assert "time_breakdown" in result

    def test_finalize_cancelled(self):
        ps = PipelineSummary("task-123456", "test.mp4", "medium", "cuda")
        assert ps.finalize(status="cancelled")["status"] == "cancelled"

    def test_finalize_includes_snapshots(self):
        ps = PipelineSummary("task-123456", "test.mp4", "medium", "cpu")
        result = ps.finalize()
        assert "system_start" in result
        assert "system_end" in result

    def test_finalize_includes_transcription(self):
        ps = PipelineSummary("task-123456", "test.mp4", "medium", "cpu")
        ps.transcription_summary = {"total_segments": 10}
        result = ps.finalize()
        assert result["transcription"]["total_segments"] == 10


class TestResourceMonitor:
    def test_start_stop_lifecycle(self):
        m = ResourceMonitor("task-123456", interval=0.05)
        m.start()
        time.sleep(0.15)
        m.stop()
        assert len(m.samples) > 0

    def test_summary_empty(self):
        assert ResourceMonitor("task-123456").summary() == {}

    def test_summary_after_samples(self):
        m = ResourceMonitor("task-123456", interval=0.05)
        m.start()
        time.sleep(0.15)
        m.stop()
        result = m.summary()
        assert result["sample_count"] > 0

    def test_stop_is_idempotent(self):
        m = ResourceMonitor("task-123456", interval=0.05)
        m.start()
        m.stop()
        m.stop()


class TestFormatBytesSimple:
    def test_zero(self):
        assert format_bytes_simple(0) == "0B"

    def test_bytes(self):
        assert format_bytes_simple(500) == "500B"

    def test_kilobytes(self):
        assert format_bytes_simple(1024) == "1.0KB"

    def test_megabytes(self):
        assert format_bytes_simple(5 * 1024**2) == "5.0MB"

    def test_gigabytes(self):
        assert format_bytes_simple(2 * 1024**3) == "2.00GB"

    def test_no_space(self):
        assert " " not in format_bytes_simple(1024)
