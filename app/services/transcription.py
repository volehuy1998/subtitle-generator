"""Whisper transcription with progress tracking and segment streaming."""

import logging
import time

from app import state
from app.config import MEL_SAMPLE_RATE, SECONDS_PER_MEL_FRAME
from app.exceptions import CancelledError, CriticalAbortError
from app.services.gpu import check_vram_for_model
from app.services.sse import emit_event
from app.utils.formatting import format_bytes, format_time_display, format_time_short
from profiler import TranscriptionProfiler

logger = logging.getLogger("subtitle-generator")


def get_optimal_transcribe_options(
    device: str, model_size: str, language: str = "auto", word_timestamps: bool = False, initial_prompt: str = ""
) -> dict:
    """Get optimal faster-whisper transcription settings."""
    opts = {
        "vad_filter": True,
        "vad_parameters": dict(min_silence_duration_ms=500),
        "word_timestamps": word_timestamps,
    }
    # Language: None means auto-detect in faster-whisper
    if language and language != "auto":
        opts["language"] = language
    # Custom vocabulary / domain prompt
    if initial_prompt and initial_prompt.strip():
        opts["initial_prompt"] = initial_prompt.strip()
    if device == "cuda":
        vram_check = check_vram_for_model(model_size)
        if vram_check.get("tight") or not vram_check.get("fits", True):
            opts["beam_size"] = 1
            logger.info(f"OPTS VRAM tight for {model_size}, using beam_size=1 (greedy)")
        else:
            opts["beam_size"] = 5
    else:
        if model_size in ("large", "medium"):
            opts["beam_size"] = 3
        else:
            opts["beam_size"] = 5
    return opts


def transcribe_with_progress(
    model,
    audio_path: str,
    task_id: str,
    device: str,
    model_size: str,
    total_duration: float,
    language: str = "auto",
    word_timestamps: bool = False,
    initial_prompt: str = "",
    translate_to_english: bool = False,
) -> dict:
    """Transcribe using faster-whisper with real-time segment streaming."""
    task = state.tasks[task_id]
    task["segments_preview"] = []
    task["transcribe_start_time"] = time.time()

    total_frames = int(total_duration / SECONDS_PER_MEL_FRAME) if total_duration > 0 else 0

    profiler = TranscriptionProfiler(task_id)
    profiler.total_frames = total_frames
    task["transcription_profiler"] = profiler

    emit_event(
        task_id,
        "transcribe_start",
        {
            "total_frames": total_frames,
            "audio_duration_sec": round(total_duration, 1),
            "word_timestamps": word_timestamps,
        },
    )

    opts = get_optimal_transcribe_options(device, model_size, language, word_timestamps, initial_prompt)
    if translate_to_english:
        opts["task"] = "translate"
        logger.info(f"WHISPER [{task_id[:8]}] Translate mode enabled (-> English)")
    logger.info(f"WHISPER [{task_id[:8]}] Transcribe options: {opts} (engine=faster-whisper)")

    segments_iter, info = model.transcribe(audio_path, **opts)
    all_segments = []

    for segment in segments_iter:
        # Critical state check
        if state.system_critical:
            reasons = "; ".join(state.system_critical_reasons) if state.system_critical_reasons else "Unknown"
            logger.warning(f"WHISPER [{task_id[:8]}] Aborting — system critical: {reasons}")
            raise CriticalAbortError(f"System critical — processing halted: {reasons}")

        # Cancel check
        if task.get("cancel_requested"):
            logger.info(f"WHISPER [{task_id[:8]}] Cancel requested at segment #{len(all_segments) + 1}")
            raise CancelledError("Task cancelled by user")

        # Pause check
        pause_event = task.get("pause_event")
        if pause_event and not pause_event.is_set():
            logger.info(f"WHISPER [{task_id[:8]}] Paused at segment #{len(all_segments) + 1}")
            task["status"] = "paused"
            old_msg = task.get("message", "")
            task["message"] = "Paused - " + old_msg
            emit_event(task_id, "paused", {"status": "paused", "message": task["message"]})
            pause_event.wait()
            logger.info(f"WHISPER [{task_id[:8]}] Resumed")
            task["status"] = "transcribing"
            emit_event(task_id, "resumed", {"status": "transcribing"})

        seg_dict = {
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip(),
        }
        # Capture word-level timestamps if enabled
        if word_timestamps and hasattr(segment, "words") and segment.words:
            seg_dict["words"] = [
                {
                    "word": w.word,
                    "start": round(w.start, 3),
                    "end": round(w.end, 3),
                    "probability": round(w.probability, 3),
                }
                for w in segment.words
            ]
        all_segments.append(seg_dict)

        seg_count = len(all_segments)
        seg_preview = {
            **seg_dict,
            "start_fmt": format_time_short(segment.start),
            "end_fmt": format_time_short(segment.end),
        }
        task["segments_preview"].append(seg_preview)
        profiler.on_segment(seg_preview, seg_count)

        # Progress calculation
        current_frames = min(int(segment.end / SECONDS_PER_MEL_FRAME), total_frames) if total_frames > 0 else 0
        metrics = profiler.on_progress(current_frames, total_frames) if total_frames > 0 else {}

        ratio = min(segment.end / total_duration, 1.0) if total_duration > 0 else 0
        percent = 15 + int(ratio * 75)

        processed_sec = segment.end
        bytes_processed = int(segment.end * MEL_SAMPLE_RATE * 2)
        bytes_total = int(total_duration * MEL_SAMPLE_RATE * 2)

        eta_sec = metrics.get("eta_sec", -1)
        elapsed_sec = metrics.get("elapsed_sec", 0)

        progress_data = {
            "percent": min(percent, 90),
            "processed_sec": round(processed_sec, 1),
            "total_sec": round(total_duration, 1),
            "bytes_processed": bytes_processed,
            "bytes_total": bytes_total,
            "bytes_processed_fmt": format_bytes(bytes_processed),
            "bytes_total_fmt": format_bytes(bytes_total),
            "eta": format_time_display(eta_sec),
            "elapsed": format_time_display(elapsed_sec),
            "speed_x": metrics.get("avg_speed_x", 0),
            "instant_speed_x": metrics.get("instant_speed_x", 0),
            "message": (
                f"Transcribing: {format_time_display(processed_sec)} / {format_time_display(total_duration)} "
                f"| {format_bytes(bytes_processed)} / {format_bytes(bytes_total)} "
                f"| ETA: {format_time_display(eta_sec)}"
            ),
        }

        task.update(progress_data)
        emit_event(task_id, "progress", progress_data)
        emit_event(task_id, "segment", {"segment": seg_preview, "segment_count": seg_count})

    return {"segments": all_segments, "language": info.language}
