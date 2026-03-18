"""Video processing pipeline: orchestrates probe -> extract -> load -> transcribe -> SRT."""

import dataclasses
import logging
import os
import re
import threading
import time as _time
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app import state
from app.config import MAX_AUDIO_DURATION, OUTPUT_DIR
from app.exceptions import CancelledError, CriticalAbortError
from app.logging_setup import log_task_event
from app.routes.metrics import inc
from app.services.analytics import record_cancellation, record_completion, record_error_category, record_failure
from app.services.diarization import assign_speakers_to_segments, diarize_audio, is_diarization_available
from app.services.gpu import check_vram_for_model
from app.services.model_manager import get_compute_type, get_model
from app.services.sse import emit_event
from app.services.task_backend import get_task_backend
from app.services.transcription import transcribe_with_progress
from app.utils.formatting import format_bytes, format_time_display
from app.utils.media import extract_audio, get_audio_duration, get_file_size
from app.utils.srt import segments_to_json, segments_to_srt, segments_to_vtt
from app.utils.subtitle_format import format_segments_with_linebreaks, validate_timing
from profiler import PipelineSummary, ResourceMonitor, StepTimer

logger = logging.getLogger("subtitle-generator")

# Known exception patterns → user-friendly messages — Forge (Senior Backend Engineer)
# Order matters: more specific patterns must come before general ones.
# Sprint L9: Error Handling Hardening — expanded with Lumen-quality messages — Forge (Sr. Backend Engineer)
_ERROR_MAP: list[tuple[str, str]] = [
    # Disk/storage errors (check before general IOError patterns)
    ("No space left on device", "Storage is full. Please free space or reduce file size."),
    ("ENOSPC", "Storage is full. Please free space or reduce file size."),
    ("disk quota exceeded", "Storage is full. Please free space or reduce file size."),
    # Memory errors (specific before general)
    ("CUDA out of memory", "GPU memory exhausted. Please try a smaller model."),
    ("out of memory", "Not enough memory for this model. Please try a smaller model or reduce file size."),
    ("MemoryError", "Not enough memory for this model. Please try a smaller model or reduce file size."),
    ("Cannot allocate memory", "Not enough memory for this model. Please try a smaller model or reduce file size."),
    # Model loading errors (specific before general "model" match)
    ("Model loading timed out", "Model loading timed out. The server may be overloaded. Please try again later."),
    ("failed to load model", "The transcription model could not be loaded. Please try a smaller model."),
    ("model download", "The transcription model could not be downloaded. Please try a smaller model."),
    ("model", "Failed to load the transcription model. Please try again."),
    # Media/ffmpeg errors (specific before general)
    ("Invalid data found when processing input", "This file appears to be damaged or is not a supported media format."),
    ("Decoder", "This file appears to be damaged or is not a supported media format."),
    ("decode", "This file appears to be damaged or is not a supported media format."),
    ("corrupt", "This file appears to be damaged or is not a supported media format."),
    ("moov atom not found", "This file appears to be damaged or is not a supported media format."),
    ("ffmpeg", "Media processing failed. The file may be corrupted or unsupported."),
    ("codec", "Unsupported media codec. Try converting to a standard format."),
    # File/permission errors
    ("No such file or directory", "A required file could not be found. Please try again."),
    ("Permission denied", "Server encountered a file permission error."),
    # Network errors
    ("Connection refused", "A required service is unavailable. Please try again later."),
    ("Connection timed out", "A required service is unavailable. Please try again later."),
    ("timed out", "The operation timed out. Please try again."),
]

_PATH_PATTERN = re.compile(r"(/[a-zA-Z0-9_./-]+)+")


def _sanitize_error_for_user(exc: Exception) -> str:
    """Map raw exceptions to user-friendly messages, stripping paths and internals.

    Handles errno-based OSError (e.g., ENOSPC) and pattern matching.
    Detailed errors remain in logs. — Forge (Sr. Backend Engineer)
    """
    import errno

    # Handle errno-based OSError directly — Forge (Sr. Backend Engineer)
    if isinstance(exc, OSError) and hasattr(exc, "errno") and exc.errno is not None:
        if exc.errno == errno.ENOSPC:
            return "Storage is full. Please free space or reduce file size."
        if exc.errno == errno.ENOMEM:
            return "Not enough memory for this model. Please try a smaller model or reduce file size."

    # Handle MemoryError type directly
    if isinstance(exc, MemoryError):
        return "Not enough memory for this model. Please try a smaller model or reduce file size."

    raw = str(exc)
    # Check known patterns
    raw_lower = raw.lower()
    for pattern, friendly in _ERROR_MAP:
        if pattern.lower() in raw_lower:
            return friendly
    # Strip file paths from unknown errors
    sanitized = _PATH_PATTERN.sub("<path>", raw)
    # Truncate to reasonable length
    if len(sanitized) > 200:
        sanitized = sanitized[:200] + "..."
    return sanitized if sanitized.strip() else "An unexpected error occurred. Please try again."


# Tasks that failed to persist to DB — retried on next successful persist
_pending_db_persists: list[tuple[str, dict]] = []
_pending_lock = threading.Lock()


@dataclasses.dataclass
class _PipelineContext:
    """Carries all state through pipeline step functions. — Forge (Sr. Backend Engineer)"""

    task_id: str
    video_path: Path
    model_size: str
    device: str
    language: str
    word_timestamps: bool
    initial_prompt: str
    diarize: bool
    num_speakers: int | None
    max_line_chars: int
    translate_to_english: bool
    auto_embed: str
    translate_to: str
    task: dict
    pipeline: object  # PipelineSummary
    monitor: object  # ResourceMonitor
    is_video_file: bool
    audio_path: Path
    m: object = None  # loaded model, set by _step_load_model
    duration: float = 0.0
    file_size: int = 0
    audio_size: int = 0
    detected_lang: str = "unknown"
    segments: list = dataclasses.field(default_factory=list)
    num_segments: int = 0
    transcribe_elapsed: float = 0.0
    probe_elapsed: float = 0.0
    extract_elapsed: float = 0.0
    translate_elapsed: float = 0.0
    srt_elapsed: float = 0.0
    speed_factor: float = 0.0


def _step_probe(ctx: _PipelineContext) -> None:
    """Step 1: Probe duration and file size. — Forge (Sr. Backend Engineer)"""
    with StepTimer(ctx.task_id, "probe", task_log_func=log_task_event) as step_probe:
        # Sprint L14: Log probe cache status — Forge (Sr. Backend Engineer)
        from app.utils.media import _probe_file_cached

        logger.debug(f"PIPELINE [{ctx.task_id[:8]}] Probe cache info: {_probe_file_cached.cache_info()}")
        ctx.duration = get_audio_duration(ctx.video_path)
        ctx.file_size = get_file_size(ctx.video_path)
        duration_str = format_time_display(ctx.duration) if ctx.duration > 0 else "unknown"
        ctx.task["duration"] = duration_str
        ctx.task["audio_duration"] = round(ctx.duration, 2)
        ctx.task["file_size"] = ctx.file_size
        ctx.task["file_size_fmt"] = format_bytes(ctx.file_size)
        ctx.pipeline.file_size = ctx.file_size
        ctx.pipeline.audio_duration = ctx.duration
    ctx.probe_elapsed = step_probe.elapsed
    ctx.pipeline.record_step("probe", step_probe.elapsed)
    emit_event(
        ctx.task_id,
        "probe_done",
        {
            "duration": duration_str,
            "file_size": ctx.file_size,
            "file_size_fmt": format_bytes(ctx.file_size),
        },
    )

    # Validate duration
    if ctx.duration > MAX_AUDIO_DURATION:
        raise ValueError(
            f"Audio too long ({format_time_display(ctx.duration)}). "
            f"Maximum is {format_time_display(MAX_AUDIO_DURATION)}."
        )
    if ctx.duration <= 0:
        logger.warning(f"TASK [{ctx.task_id[:8]}] Could not determine audio duration, proceeding anyway")


def _step_extract(ctx: _PipelineContext) -> None:
    """Step 2: Extract audio from video (or skip if already WAV). — Forge (Sr. Backend Engineer)"""
    duration_str = format_time_display(ctx.duration) if ctx.duration > 0 else "unknown"
    ctx.task["status"] = "extracting"
    ctx.task["current_step"] = 1
    ctx.task["percent"] = 5
    ctx.task["message"] = f"Extracting audio ({duration_str}, {format_bytes(ctx.file_size)})..."
    ctx.task["step_timing"] = {"upload": round(ctx.probe_elapsed, 2)}
    log_task_event(ctx.task_id, "step_start", step=1, name="extract", status="extracting")
    emit_event(
        ctx.task_id,
        "step_change",
        {
            "step": 1,
            "status": "extracting",
            "percent": 5,
            "message": ctx.task["message"],
            "step_timing": ctx.task["step_timing"],
            "step_started_at": _time.time(),
        },
    )

    with StepTimer(ctx.task_id, "extract_audio", task_log_func=log_task_event) as step_extract:
        # Sprint L13: Skip extraction when input is already WAV — Forge (Sr. Backend Engineer)
        input_ext = os.path.splitext(str(ctx.video_path))[1].lower()
        if input_ext == ".wav":
            ctx.audio_path = ctx.video_path
            logger.info(f"PIPELINE [{ctx.task_id[:8]}] Input is WAV, skipping extraction")
            log_task_event(ctx.task_id, "extract_skipped", reason="input_is_wav")
        else:
            extract_audio(ctx.video_path, ctx.audio_path, task_id=ctx.task_id)
        ctx.audio_size = get_file_size(ctx.audio_path)
        ctx.task["audio_size_fmt"] = format_bytes(ctx.audio_size)
        ctx.pipeline.audio_size = ctx.audio_size
    ctx.extract_elapsed = step_extract.elapsed
    ctx.pipeline.record_step("extract_audio", step_extract.elapsed)
    emit_event(
        ctx.task_id,
        "extract_done",
        {
            "audio_size": ctx.audio_size,
            "audio_size_fmt": format_bytes(ctx.audio_size),
            "extract_time_sec": round(step_extract.elapsed, 2),
        },
    )

    ctx.task["percent"] = 15
    ctx.task["message"] = f"Audio extracted ({format_bytes(ctx.audio_size)}). Loading model..."


def _step_load_model(ctx: _PipelineContext) -> None:
    """Step 3: Load transcription model. — Forge (Sr. Backend Engineer)"""
    ctx.task["status"] = "transcribing"
    ctx.task["current_step"] = 2
    compute_type = get_compute_type(ctx.device, ctx.model_size)
    from app import state as _state

    _model_cached = (ctx.model_size, ctx.device) in _state.loaded_models

    # Sprint L11: Sub-stage SSE — loading_model substage — Forge (Sr. Backend Engineer)
    ctx.task["message"] = (
        f"Starting transcription with {ctx.model_size} model..."
        if _model_cached
        else f"Loading {ctx.model_size} model on {ctx.device.upper()} ({compute_type})..."
    )
    ctx.task["step_timing"] = {"upload": round(ctx.probe_elapsed, 2), "extract": round(ctx.extract_elapsed, 2)}
    log_task_event(
        ctx.task_id,
        "step_start",
        step=2,
        name="transcribe",
        status="transcribing",
        model=ctx.model_size,
        device=ctx.device,
    )
    emit_event(
        ctx.task_id,
        "step_change",
        {
            "step": 2,
            "status": "loading_model",
            "substage": "loading_model",
            "percent": 15,
            "message": f"Loading {ctx.model_size} model..."
            if not _model_cached
            else f"Loading {ctx.model_size} model (cached)...",
            "step_timing": ctx.task["step_timing"],
            "step_started_at": _time.time(),
            "model_size": ctx.model_size,
            "device": ctx.device.upper(),
        },
    )

    with StepTimer(ctx.task_id, "model_load", task_log_func=log_task_event) as step_model:
        ctx.m = get_model(ctx.model_size, ctx.device)
    ctx.task["model"] = ctx.model_size
    ctx.pipeline.record_step("model_load", step_model.elapsed)
    emit_event(
        ctx.task_id,
        "model_loaded",
        {
            "model": ctx.model_size,
            "device": ctx.device.upper(),
            "compute_type": compute_type,
            "load_time_sec": round(step_model.elapsed, 2),
        },
    )


def _step_transcribe(ctx: _PipelineContext) -> None:
    """Step 4: Transcribe audio. — Forge (Sr. Backend Engineer)"""
    compute_type = get_compute_type(ctx.device, ctx.model_size)

    # Sprint L11: Sub-stage SSE — transcribing substage — Forge (Sr. Backend Engineer)
    ctx.task["message"] = f"Transcribing on {ctx.device.upper()} ({ctx.model_size} model, {compute_type})..."
    emit_event(
        ctx.task_id,
        "step_change",
        {
            "step": 2,
            "status": "transcribing",
            "substage": "transcribing",
            "percent": 15,
            "message": ctx.task["message"],
            "step_started_at": _time.time(),
            "model_size": ctx.model_size,
            "device": ctx.device.upper(),
        },
    )

    with StepTimer(ctx.task_id, "transcribe", task_log_func=log_task_event) as step_transcribe:
        result = transcribe_with_progress(
            ctx.m,
            str(ctx.audio_path),
            ctx.task_id,
            ctx.device,
            ctx.model_size,
            ctx.duration,
            ctx.language,
            word_timestamps=ctx.word_timestamps,
            initial_prompt=ctx.initial_prompt,
            translate_to_english=ctx.translate_to_english,
        )
    ctx.transcribe_elapsed = step_transcribe.elapsed
    ctx.pipeline.record_step("transcribe", step_transcribe.elapsed)

    ctx.segments = result["segments"]
    ctx.detected_lang = result.get("language", "unknown")

    # Sprint L9: Log zero-segments detection early — Forge (Sr. Backend Engineer)
    if not ctx.segments:
        logger.info(f"TASK [{ctx.task_id[:8]}] No speech segments detected in audio")
        log_task_event(ctx.task_id, "no_speech_detected", audio_duration_sec=round(ctx.duration, 2))
        emit_event(ctx.task_id, "warning", {"message": "No speech detected in this file."})

    ctx.num_segments = len(ctx.segments)
    ctx.speed_factor = ctx.duration / ctx.transcribe_elapsed if ctx.transcribe_elapsed > 0 else 0

    tx_profiler = ctx.task.get("transcription_profiler")
    if tx_profiler:
        tx_summary = tx_profiler.summary()
        ctx.pipeline.transcription_summary = tx_summary
        log_task_event(ctx.task_id, "transcription_profile", **tx_summary)

    log_task_event(
        ctx.task_id,
        "transcription_complete",
        segments=ctx.num_segments,
        language=ctx.detected_lang,
        transcribe_time_sec=round(ctx.transcribe_elapsed, 2),
        speed_factor=round(ctx.speed_factor, 2),
        audio_duration_sec=round(ctx.duration, 2),
    )


def _step_diarize(ctx: _PipelineContext) -> None:
    """Step 4b: Speaker diarization (no-op if disabled). — Forge (Sr. Backend Engineer)"""
    if not ctx.diarize or not is_diarization_available()["available"]:
        return
    ctx.task["message"] = "Identifying speakers..."
    emit_event(ctx.task_id, "step_change", {"status": "diarizing", "message": ctx.task["message"]})
    with StepTimer(ctx.task_id, "diarize", task_log_func=log_task_event) as step_diarize:
        speaker_turns = diarize_audio(ctx.audio_path, ctx.task_id, num_speakers=ctx.num_speakers)
        ctx.segments = assign_speakers_to_segments(ctx.segments, speaker_turns)
        ctx.task["speakers"] = len(set(t["speaker"] for t in speaker_turns)) if speaker_turns else 0
    ctx.pipeline.record_step("diarize", step_diarize.elapsed)


def _step_translate(ctx: _PipelineContext) -> None:
    """Step 4d: Translation (no-op if not translating). — Forge (Sr. Backend Engineer)"""
    if not ctx.translate_to or ctx.translate_to == "en" or ctx.translate_to == ctx.detected_lang:
        return

    from app.services.translation import translate_segments as do_translate

    ctx.task["status"] = "translating"
    ctx.task["message"] = f"Translating subtitles to {ctx.translate_to}..."
    emit_event(
        ctx.task_id,
        "step_change",
        {
            "step": 2,
            "status": "translating",
            "percent": 90,
            "message": ctx.task["message"],
        },
    )
    with StepTimer(ctx.task_id, "translate", task_log_func=log_task_event) as step_translate:
        ctx.segments = do_translate(ctx.segments, ctx.detected_lang, ctx.translate_to, ctx.task_id)
    ctx.translate_elapsed = step_translate.elapsed
    ctx.pipeline.record_step("translate", ctx.translate_elapsed)
    # Re-apply line-breaking on translated text (different word lengths)
    ctx.segments = format_segments_with_linebreaks(ctx.segments, max_chars=ctx.max_line_chars)
    ctx.task["translated_to"] = ctx.translate_to
    # Update live preview with translated segments
    from app.utils.formatting import format_time_short

    for seg in ctx.segments:
        emit_event(
            ctx.task_id,
            "segment",
            {
                "segment": {
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"],
                    "start_fmt": format_time_short(seg["start"]),
                    "end_fmt": format_time_short(seg["end"]),
                    "speaker": seg.get("speaker"),
                },
                "translated": True,
            },
        )


def _step_validate_timing(ctx: _PipelineContext) -> None:
    """Validate timing quality of segments. — Forge (Sr. Backend Engineer)"""
    timing_issues = 0
    for seg in ctx.segments:
        diag = validate_timing(seg["start"], seg["end"], seg["text"])
        if not diag["valid"]:
            timing_issues += 1
    if timing_issues > 0:
        logger.info(
            f"TASK [{ctx.task_id[:8]}] Subtitle quality: {timing_issues}/{len(ctx.segments)} segments have timing issues"
        )


def _step_finalize(ctx: _PipelineContext) -> None:
    """Step 5: Write SRT/VTT/JSON output files. — Forge (Sr. Backend Engineer)"""
    ctx.task["status"] = "writing"
    ctx.task["current_step"] = 3
    ctx.task["percent"] = 95
    ctx.task["message"] = "Generating subtitle file..."
    ctx.task["step_timing"] = {
        "upload": round(ctx.probe_elapsed, 2),
        "extract": round(ctx.extract_elapsed, 2),
        "transcribe": round(ctx.transcribe_elapsed, 2),
    }
    log_task_event(
        ctx.task_id,
        "step_start",
        step=3,
        name="finalize",
        status="writing",
        segments=ctx.num_segments,
        language=ctx.detected_lang,
    )
    emit_event(
        ctx.task_id,
        "step_change",
        {
            "step": 3,
            "status": "writing",
            "percent": 95,
            "message": "Generating subtitle file...",
            "step_timing": ctx.task["step_timing"],
            "step_started_at": _time.time(),
        },
    )

    has_speakers = any("speaker" in s for s in ctx.segments)

    with StepTimer(ctx.task_id, "write_srt", task_log_func=log_task_event) as step_srt:
        # Sprint L9: Generate valid subtitle files even with 0 segments — Forge (Sr. Backend Engineer)
        if not ctx.segments:
            # Write SRT with a header comment indicating no speech was detected
            srt_content = "1\n00:00:00,000 --> 00:00:01,000\n[No speech detected in this file.]\n"
            vtt_content = "WEBVTT\nNOTE No speech detected in this file.\n\n1\n00:00:00.000 --> 00:00:01.000\n[No speech detected in this file.]\n"
            json_content = segments_to_json([])
        else:
            srt_content = segments_to_srt(ctx.segments, include_speakers=has_speakers)
            vtt_content = segments_to_vtt(ctx.segments, include_speakers=has_speakers)
            json_content = segments_to_json(ctx.segments)

        srt_path = OUTPUT_DIR / f"{ctx.task_id}.srt"
        vtt_path = OUTPUT_DIR / f"{ctx.task_id}.vtt"
        json_path = OUTPUT_DIR / f"{ctx.task_id}.json"

        # Sprint L13: Write all output formats in parallel — Forge (Sr. Backend Engineer)
        def _write_output(path, content):
            path.write_text(content, encoding="utf-8")

        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [
                pool.submit(_write_output, srt_path, srt_content),
                pool.submit(_write_output, vtt_path, vtt_content),
                pool.submit(_write_output, json_path, json_content),
            ]
            for f in futures:
                f.result()

        srt_size = get_file_size(srt_path)
        ctx.pipeline.srt_size = srt_size
    ctx.srt_elapsed = step_srt.elapsed
    ctx.pipeline.record_step("write_srt", step_srt.elapsed)

    # Upload outputs to S3 if configured
    from app.config import STORAGE_BACKEND

    if STORAGE_BACKEND == "s3":
        try:
            from app.services.storage import get_storage

            storage = get_storage()
            for out_ext in ("srt", "vtt", "json"):
                out_file = OUTPUT_DIR / f"{ctx.task_id}.{out_ext}"
                if out_file.exists():
                    storage.save_output_from_path(out_file.name, out_file)
            logger.info(f"TASK [{ctx.task_id[:8]}] Outputs uploaded to S3")
        except Exception as e:
            logger.error(f"TASK [{ctx.task_id[:8]}] S3 upload failed: {e}")


def _retry_pending_persists():
    """Try to persist any tasks that previously failed to write to DB."""
    if not _pending_db_persists:
        return
    backend = get_task_backend()
    try:
        from app.db.task_backend_db import DatabaseTaskBackend

        if not isinstance(backend, DatabaseTaskBackend):
            return
    except ImportError:
        return

    with _pending_lock:
        pending = list(_pending_db_persists)

    succeeded = []
    for task_id, task_data in pending:
        try:
            backend.schedule_persist(task_id, task_data)
            succeeded.append((task_id, task_data))
            logger.info(f"TASK [{task_id[:8]}] DB persist retry succeeded")
        except Exception as e:
            logger.debug("DB persist retry failed, will try again later: %s", e)
            break  # DB probably still down

    if succeeded:
        with _pending_lock:
            for item in succeeded:
                if item in _pending_db_persists:
                    _pending_db_persists.remove(item)


def _check_critical(task_id: str):
    """Abort the pipeline if the system has entered critical state."""
    if state.system_critical:
        reasons = "; ".join(state.system_critical_reasons) if state.system_critical_reasons else "Unknown"
        raise CriticalAbortError(f"System critical — processing halted: {reasons}")


def _auto_embed_subtitles(task_id: str, video_path: Path, mode: str, language: str):
    """Auto-embed subtitles into the original video after transcription."""
    from app.services.subtitle_embed import STYLE_PRESETS, SubtitleStyle, hard_burn_subtitles, soft_embed_subtitles

    srt_path = OUTPUT_DIR / f"{task_id}.srt"
    if not srt_path.exists():
        logger.warning(f"TASK [{task_id[:8]}] Auto-embed skipped: no SRT file")
        return

    task = state.tasks.get(task_id, {})
    emit_event(task_id, "embed_progress", {"message": "Embedding subtitles into video...", "percent": 100})

    ext = video_path.suffix
    out_ext = ".mkv" if mode == "soft" and ext == ".mkv" else ".mp4"
    output_path = OUTPUT_DIR / f"embed_{task_id}{out_ext}"

    if mode == "hard":
        style = STYLE_PRESETS.get("youtube_white", SubtitleStyle())
        hard_burn_subtitles(video_path, srt_path, output_path, style, task_id)
    else:
        soft_embed_subtitles(video_path, srt_path, output_path, task_id, language=language)

    task["embedded_video"] = str(output_path.name)
    log_task_event(task_id, "auto_embed_complete", mode=mode, output=output_path.name)
    emit_event(
        task_id,
        "embed_done",
        {
            "message": f"Subtitles embedded ({mode} mode)",
            "download_url": f"/embed/download/{task_id}",
            "output": output_path.name,
            "mode": mode,
        },
    )
    logger.info(f"TASK [{task_id[:8]}] Auto-embed complete: {output_path.name}")


def _persist_task(task_id: str, task: dict):
    """Persist task to DB (mandatory). Queues for retry if DB write fails."""
    # First, try to flush any previously failed persists
    _retry_pending_persists()

    backend = get_task_backend()
    try:
        from app.db.task_backend_db import DatabaseTaskBackend

        if isinstance(backend, DatabaseTaskBackend):
            backend.schedule_persist(task_id, task)
            return
    except ImportError:
        logger.debug("DatabaseTaskBackend not available, using JSON fallback")
    except Exception as e:
        logger.error(f"TASK [{task_id[:8]}] DB persist failed, queued for retry: {e}")
        with _pending_lock:
            _pending_db_persists.append((task_id, dict(task)))
    # Fallback to legacy JSON persistence
    state.save_task_history()


def process_video(
    task_id: str,
    video_path: Path,
    model_size: str,
    device: str,
    language: str = "auto",
    word_timestamps: bool = False,
    initial_prompt: str = "",
    diarize: bool = False,
    num_speakers: int = None,
    max_line_chars: int = 42,
    translate_to_english: bool = False,
    auto_embed: str = "",
    translate_to: str = "",
) -> None:
    """Main processing pipeline. Runs in a background thread.

    Refactored Sprint L61: orchestrator delegates to _step_* functions
    via _PipelineContext. Zero behavior change. — Forge (Sr. Backend Engineer)
    """
    # Acquire concurrency semaphore
    sem = state.get_task_semaphore()
    sem.acquire()

    audio_path = video_path.with_suffix(".wav")

    pause_event = threading.Event()
    pause_event.set()
    # Ensure task exists in local state (may come from Redis on worker nodes)
    if task_id not in state.tasks:
        state.tasks[task_id] = {"status": "queued", "percent": 0, "message": "Starting..."}
    task = state.tasks[task_id]
    task["pause_event"] = pause_event
    task["cancel_requested"] = False
    task["_thread_id"] = threading.current_thread().ident
    task["device"] = device.upper()
    task["model_size"] = model_size
    task["language_requested"] = language
    task["word_timestamps"] = word_timestamps
    task["diarize"] = diarize
    task["segments_preview"] = []

    # Track whether input is a video file (for deferred embed)
    VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".webm", ".mov"}
    is_video_file = video_path.suffix.lower() in VIDEO_EXTENSIONS
    task["is_video"] = is_video_file

    pipeline = PipelineSummary(task_id, task.get("filename", "unknown"), model_size, device)
    monitor = ResourceMonitor(task_id, interval=2.0)
    monitor.start()

    logger.info(
        f"TASK [{task_id[:8]}] Pipeline started: file={task.get('filename')} model={model_size} device={device}"
    )
    log_task_event(task_id, "pipeline_start", filename=task.get("filename"), model=model_size, device=device)
    task["current_step"] = 0
    emit_event(task_id, "pipeline_start", {"status": "queued", "model": model_size, "device": device.upper()})
    emit_event(task_id, "step_change", {"step": 0, "status": "uploading", "percent": 0, "message": "Analysing file..."})

    # VRAM warning
    if device == "cuda":
        vram_check = check_vram_for_model(model_size)
        if not vram_check.get("fits", True):
            logger.warning(
                f"TASK [{task_id[:8]}] VRAM WARNING: {model_size} requires ~{vram_check.get('required_gb')}GB "
                f"but only {vram_check.get('free_gb')}GB free."
            )
            log_task_event(task_id, "vram_warning", **vram_check)
            emit_event(
                task_id,
                "warning",
                {
                    "message": f"Model '{model_size}' may not fit in VRAM ({vram_check.get('free_gb')}GB free, ~{vram_check.get('required_gb')}GB needed).",
                },
            )

    # Build pipeline context — Forge (Sr. Backend Engineer)
    ctx = _PipelineContext(
        task_id=task_id,
        video_path=video_path,
        model_size=model_size,
        device=device,
        language=language,
        word_timestamps=word_timestamps,
        initial_prompt=initial_prompt,
        diarize=diarize,
        num_speakers=num_speakers,
        max_line_chars=max_line_chars,
        translate_to_english=translate_to_english,
        auto_embed=auto_embed,
        translate_to=translate_to,
        task=task,
        pipeline=pipeline,
        monitor=monitor,
        is_video_file=is_video_file,
        audio_path=audio_path,
    )

    try:
        # Step 1: Probe
        _step_probe(ctx)

        if task.get("cancel_requested"):
            raise CancelledError("Task cancelled by user")
        _check_critical(task_id)

        # Step 2: Extract audio
        _step_extract(ctx)
        audio_path = ctx.audio_path  # sync for cleanup handlers

        if task.get("cancel_requested"):
            raise CancelledError("Task cancelled by user")
        _check_critical(task_id)

        # Step 3: Load model
        _step_load_model(ctx)

        if task.get("cancel_requested"):
            raise CancelledError("Task cancelled by user")
        _check_critical(task_id)

        # Step 4: Transcribe
        _step_transcribe(ctx)

        # Step 4b: Speaker diarization (guarded, no-op if disabled)
        _step_diarize(ctx)

        # Step 4c: Apply line-breaking rules
        ctx.segments = format_segments_with_linebreaks(ctx.segments, max_chars=max_line_chars)

        # Step 4d: Translation (guarded, no-op if not translating)
        _step_translate(ctx)

        # Validate timing quality
        _step_validate_timing(ctx)

        if task.get("cancel_requested"):
            raise CancelledError("Task cancelled by user")
        _check_critical(task_id)

        # Step 5: Generate SRT/VTT/JSON (finalize)
        _step_finalize(ctx)

        # Step 6: Done — completion block stays in orchestrator
        monitor.stop()
        monitor_summary = monitor.summary()
        if monitor_summary:
            log_task_event(task_id, "resource_monitor", **monitor_summary)

        pipeline_summary = pipeline.finalize(status="complete")
        pipeline_summary.pop("task_id", None)
        log_task_event(task_id, "pipeline_summary", **pipeline_summary)

        task["status"] = "done"
        task["percent"] = 100
        # Sprint L54: Store wall-clock duration on task — Forge (Sr. Backend Engineer)
        task["total_time_sec"] = round(pipeline_summary.get("total_time_sec", 0), 2)
        done_suffix = ""
        if translate_to and translate_to != "en" and translate_to != ctx.detected_lang:
            done_suffix = f", translated to {translate_to}"
        task["message"] = (
            f"Done! {ctx.num_segments} subtitles generated "
            f"(language: {ctx.detected_lang}, {device.upper()}, took {format_time_display(ctx.transcribe_elapsed)}{done_suffix})"
        )
        task["segments"] = ctx.num_segments
        task["language"] = ctx.detected_lang
        final_step_timing = {
            "upload": round(ctx.probe_elapsed, 2),
            "extract": round(ctx.extract_elapsed, 2),
            "transcribe": round(ctx.transcribe_elapsed, 2),
            "finalize": round(ctx.srt_elapsed, 2),
        }
        if ctx.translate_elapsed > 0:
            final_step_timing["translate"] = round(ctx.translate_elapsed, 2)
        task["step_timing"] = final_step_timing
        task["step_timings"] = final_step_timing  # alias used by progress API schema

        done_data = {
            "status": "done",
            "percent": 100,
            "message": task["message"],
            "segments": ctx.num_segments,
            "language": ctx.detected_lang,
            "model": ctx.model_size,
            "total_time_sec": round(pipeline_summary.get("total_time_sec", 0), 2),
            "speed_factor": round(ctx.speed_factor, 2),
            "step_timings": task["step_timings"],
            "is_video": is_video_file,
        }
        if task.get("translated_to"):
            done_data["translated_to"] = task["translated_to"]
        emit_event(task_id, "done", done_data)

        # Record analytics
        total_time = pipeline_summary.get("total_time_sec", 0)
        record_completion(total_time, model=model_size)
        inc("transcriptions_completed")

        # Sprint L13: Don't delete audio if it IS the original WAV input — Forge (Sr. Backend Engineer)
        if audio_path != video_path:
            audio_path.unlink(missing_ok=True)

        # Auto-embed subtitles if requested
        if auto_embed and video_path.exists():
            try:
                _auto_embed_subtitles(task_id, video_path, auto_embed, ctx.detected_lang)
            except Exception as e:
                logger.error("TASK [%s] Auto-embed failed: %s", task_id[:8], e)
                emit_event(task_id, "embed_error", {"message": f"Auto-embed failed: {_sanitize_error_for_user(e)}"})
            finally:
                video_path.unlink(missing_ok=True)
        elif is_video_file and video_path.exists():
            # Preserve video for deferred embed (user can embed after reviewing subtitles)
            task["preserved_video"] = str(video_path.name)
            logger.info(f"TASK [{task_id[:8]}] Video preserved for deferred embed: {video_path.name}")
        else:
            video_path.unlink(missing_ok=True)

        _persist_task(task_id, task)

    except CancelledError:
        monitor.stop()
        pipeline_summary = pipeline.finalize(status="cancelled")
        pipeline_summary.pop("task_id", None)
        log_task_event(task_id, "pipeline_summary", **pipeline_summary)
        task["status"] = "cancelled"
        # Keep last known percent so task queue shows how far it got
        task["message"] = "Task cancelled by user."
        logger.warning(f"TASK [{task_id[:8]}] CANCELLED")
        emit_event(task_id, "cancelled", {"status": "cancelled", "message": "Task cancelled by user."})
        record_cancellation()
        inc("transcriptions_cancelled")
        video_path.unlink(missing_ok=True)
        if audio_path != video_path:
            audio_path.unlink(missing_ok=True)
        _persist_task(task_id, task)

    except CriticalAbortError as e:
        monitor.stop()
        pipeline_summary = pipeline.finalize(status="aborted")
        pipeline_summary.pop("task_id", None)
        log_task_event(task_id, "pipeline_summary", **pipeline_summary)
        reasons = "; ".join(state.system_critical_reasons) if state.system_critical_reasons else "System critical"
        task["status"] = "error"
        # Keep last known percent so task queue shows how far it got
        task["message"] = f"Processing halted — {reasons}"
        logger.error(f"TASK [{task_id[:8]}] CRITICAL ABORT: {e}")
        log_task_event(task_id, "critical_abort", error=str(e), reasons=state.system_critical_reasons)
        emit_event(
            task_id,
            "critical_abort",
            {
                "status": "error",
                "message": task["message"],
                "critical": True,
                "reasons": list(state.system_critical_reasons),
            },
        )
        record_failure()
        record_error_category("CriticalAbort")
        inc("transcriptions_failed")
        video_path.unlink(missing_ok=True)
        if audio_path != video_path:
            audio_path.unlink(missing_ok=True)
        _persist_task(task_id, task)

    except Exception as e:
        monitor.stop()
        pipeline_summary = pipeline.finalize(status="error")
        pipeline_summary.pop("task_id", None)
        log_task_event(task_id, "pipeline_summary", **pipeline_summary)
        task["status"] = "error"
        # Keep last known percent so task queue shows how far it got
        user_msg = _sanitize_error_for_user(e)
        task["message"] = user_msg
        logger.error("TASK [%s] ERROR: %s\n%s", task_id[:8], e, traceback.format_exc())
        log_task_event(task_id, "error", error=str(e), traceback=traceback.format_exc())
        emit_event(task_id, "error", {"status": "error", "message": user_msg})
        record_failure()
        record_error_category(type(e).__name__)
        inc("transcriptions_failed")
        video_path.unlink(missing_ok=True)
        if audio_path != video_path:
            audio_path.unlink(missing_ok=True)
        _persist_task(task_id, task)

    finally:
        task.pop("_thread_id", None)
        sem.release()
