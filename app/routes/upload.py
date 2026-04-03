"""Upload route with security validation.

Phase 3 optimization: file save + magic byte validation happen synchronously,
then task_id is returned immediately. Heavy operations (audio probing, ClamAV
scan) run in the background "preparing" phase before the pipeline starts.
— Forge (Sr. Backend Engineer)
"""

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, Form, HTTPException, Request, UploadFile

from app import state
from app.config import (
    MAX_CONCURRENT_TASKS,
    MAX_FILE_SIZE,
    MIN_FILE_SIZE,
    SUPPORTED_LANGUAGES,
    UPLOAD_DIR,
    VALID_MODELS,
)
from app.errors import (
    FFMPEG_UNAVAILABLE,
    FILE_TOO_LARGE,
    FILE_TOO_SMALL,
    MAGIC_BYTES_MISMATCH,
    SYSTEM_CRITICAL,
    TASK_LIMIT_REACHED,
    UNSUPPORTED_FORMAT,
    api_error,
)
from app.logging_setup import get_request_id, log_task_event
from app.routes.metrics import inc
from app.schemas import UploadResponse
from app.services.analytics import record_upload
from app.services.audit import log_audit_event
from app.services.gpu import auto_select_model
from app.services.pipeline import process_video
from app.services.quarantine import quarantine_file, scan_with_clamav
from app.services.sse import create_event_queue, emit_event
from app.utils.formatting import format_bytes
from app.utils.security import detect_mime_type, sanitize_filename, validate_file_extension, validate_magic_bytes

logger = logging.getLogger("subtitle-generator")

router = APIRouter(tags=["Upload"])


def _prepare_and_process(
    task_id: str,
    video_path: Path,
    safe_filename: str,
    client_ip: str,
    size: int,
    model_size: str,
    device: str,
    language: str,
    word_timestamps: bool,
    initial_prompt: str,
    diarize: bool,
    num_speakers: Optional[int],
    max_line_chars: int,
    translate_to_english: bool,
    auto_embed: str,
    translate_to: str,
) -> None:
    """Background preparation + pipeline dispatch.

    Runs in the pipeline thread pool. Handles audio probing and ClamAV scanning
    in a "preparing" phase, emitting SSE events for user feedback. On failure,
    sets task to error status. On success, proceeds to process_video().
    — Forge (Sr. Backend Engineer), Phase 3 Upload Optimization
    """
    task = state.tasks.get(task_id)
    if task is None:
        logger.error(f"PREPARE [{task_id[:8]}] Task not found in state, aborting")
        return

    try:
        # ── Phase: preparing (probe + scan) ──────────────────────────────
        task["status"] = "preparing"
        task["message"] = "Preparing: validating media file..."
        task["percent"] = 0
        emit_event(task_id, "preparing", {"status": "preparing", "message": "Validating media file...", "percent": 0})

        # Audio stream + duration validation (requires ffprobe)
        from app.config import FFPROBE_AVAILABLE, MAX_AUDIO_DURATION

        if FFPROBE_AVAILABLE:
            from app.utils.media import get_audio_duration, has_audio_stream

            emit_event(
                task_id,
                "upload_progress",
                {"status": "preparing", "message": "Probing audio stream...", "percent": 10},
            )

            if not has_audio_stream(video_path):
                video_path.unlink(missing_ok=True)
                logger.warning(f"PREPARE [{task_id[:8]}] Rejected: no audio stream in '{safe_filename}'")
                task["status"] = "error"
                task["message"] = "This file has no audio track. Please upload a file with audio."
                emit_event(
                    task_id,
                    "error",
                    {"status": "error", "message": task["message"], "error_code": "NO_AUDIO_STREAM"},
                )
                return

            emit_event(
                task_id,
                "upload_progress",
                {"status": "preparing", "message": "Checking audio duration...", "percent": 30},
            )

            duration = get_audio_duration(video_path)
            if duration > MAX_AUDIO_DURATION:
                video_path.unlink(missing_ok=True)
                logger.warning(
                    f"PREPARE [{task_id[:8]}] Rejected: duration {duration:.0f}s exceeds "
                    f"{MAX_AUDIO_DURATION}s limit for '{safe_filename}'"
                )
                task["status"] = "error"
                task["message"] = "File duration exceeds the 4-hour limit. Please upload a shorter file."
                emit_event(
                    task_id,
                    "error",
                    {"status": "error", "message": task["message"], "error_code": "DURATION_EXCEEDED"},
                )
                return

        # ClamAV virus scan (optional — graceful if ClamAV is not installed/running)
        emit_event(
            task_id,
            "upload_progress",
            {"status": "preparing", "message": "Scanning for threats...", "percent": 60},
        )

        av_result = scan_with_clamav(str(video_path))
        if not av_result["clean"]:
            log_audit_event(
                "virus_detected", ip=client_ip, filename=safe_filename, size=size, threat=av_result.get("threat")
            )
            quarantine_file(video_path, reason="virus_detected", ip=client_ip, threat=av_result.get("threat"))
            logger.warning(f"PREPARE [{task_id[:8]}] Rejected: ClamAV detected threat '{av_result.get('threat')}'")
            task["status"] = "error"
            task["message"] = "File rejected: virus or malware detected."
            emit_event(
                task_id,
                "error",
                {"status": "error", "message": task["message"], "error_code": "VIRUS_DETECTED"},
            )
            return

        # ── Preparation complete — transition to pipeline ────────────────
        emit_event(
            task_id,
            "upload_progress",
            {"status": "preparing", "message": "Preparation complete. Starting pipeline...", "percent": 100},
        )
        task["status"] = "queued"
        task["message"] = "Preparation complete. Starting processing..."

        process_video(
            task_id,
            video_path,
            model_size,
            device,
            language,
            word_timestamps=word_timestamps,
            initial_prompt=initial_prompt,
            diarize=diarize,
            num_speakers=num_speakers,
            max_line_chars=max_line_chars,
            translate_to_english=translate_to_english,
            auto_embed=auto_embed,
            translate_to=translate_to,
        )

    except Exception as e:
        logger.error(f"PREPARE [{task_id[:8]}] Unexpected error during preparation: {e}")
        if task_id in state.tasks:
            state.tasks[task_id]["status"] = "error"
            state.tasks[task_id]["message"] = f"Preparation failed: {e}"
        emit_event(task_id, "error", {"status": "error", "message": f"Preparation failed: {e}"})


@router.post("/upload", response_model=UploadResponse)
async def upload(
    request: Request,
    file: UploadFile,
    device: Literal["cuda", "cpu"] = Form("cuda"),
    model_size: Literal["auto", "tiny", "base", "small", "medium", "large"] = Form("auto"),
    language: str = Form("auto"),
    word_timestamps: bool = Form(False),
    initial_prompt: str = Form(""),
    diarize: bool = Form(False),
    num_speakers: Optional[int] = Form(None),
    max_line_chars: int = Form(42),
    translate_to_english: bool = Form(False),
    auto_embed: str = Form(""),
    translate_to: str = Form(""),
):
    # Note: shutdown and DB checks are handled by CriticalStateMiddleware

    # Validate language
    if language not in SUPPORTED_LANGUAGES:
        language = "auto"

    # Validate extension
    ext = validate_file_extension(file.filename or "")
    if ext is None:
        logger.warning(f"UPLOAD Rejected: unsupported extension for '{file.filename}'")
        raise HTTPException(
            400,
            detail=api_error(
                UNSUPPORTED_FORMAT,
                "Unsupported format. Allowed: .mp4, .mkv, .avi, .webm, .mov, .mp3, .wav, .flac",
                request_id=get_request_id(),
            ),
        )

    # Reject video files when FFmpeg is not available
    from app.config import FFMPEG_AVAILABLE, VIDEO_EXTENSIONS

    if ext in VIDEO_EXTENSIONS and not FFMPEG_AVAILABLE:
        raise HTTPException(
            503,
            detail=api_error(
                FFMPEG_UNAVAILABLE,
                "FFmpeg is not installed. Video files require FFmpeg for audio extraction. "
                "Please upload an audio file (.mp3, .wav, .flac) instead.",
                request_id=get_request_id(),
            ),
        )

    # Device fallback
    import torch  # noqa: PLC0415  # lazy — avoids top-level GPU init

    if device == "cuda" and not torch.cuda.is_available():
        logger.warning("UPLOAD Device 'cuda' not available, falling back to CPU")
        device = "cpu"

    # Auto-select model
    if model_size == "auto":
        model_size = auto_select_model()
        logger.info(f"UPLOAD Auto-selected model: {model_size}")
    elif model_size not in VALID_MODELS:
        model_size = "medium"

    # Check concurrent task limit
    active = sum(1 for t in state.tasks.values() if t.get("status") not in ("done", "error", "cancelled"))
    if active >= MAX_CONCURRENT_TASKS:
        raise HTTPException(
            429,
            detail=api_error(
                TASK_LIMIT_REACHED,
                f"Too many active tasks ({active}). Please wait for a task to complete.",
                request_id=get_request_id(),
            ),
        )

    task_id = str(uuid.uuid4())
    safe_filename = sanitize_filename(file.filename or "unknown")
    video_path = UPLOAD_DIR / f"{task_id}{ext}"

    create_event_queue(task_id)

    logger.info(f"UPLOAD [{task_id[:8]}] Starting: file='{safe_filename}' model={model_size} device={device}")

    import time

    t0 = time.time()
    size = 0
    with open(video_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            # Abort upload immediately if system enters critical state
            if state.system_critical:
                video_path.unlink(missing_ok=True)
                logger.warning(f"UPLOAD [{task_id[:8]}] Aborted mid-upload: system critical")
                raise HTTPException(
                    503,
                    detail=api_error(
                        SYSTEM_CRITICAL, "Upload aborted — system in critical state.", request_id=get_request_id()
                    ),
                )
            size += len(chunk)
            if size > MAX_FILE_SIZE:
                video_path.unlink(missing_ok=True)
                logger.warning(f"UPLOAD [{task_id[:8]}] Rejected: file too large ({format_bytes(size)})")
                raise HTTPException(
                    413,
                    detail=api_error(
                        FILE_TOO_LARGE,
                        f"File too large ({format_bytes(size)}). Maximum size is {format_bytes(MAX_FILE_SIZE)}.",
                        request_id=get_request_id(),
                    ),
                )
            f.write(chunk)

    # Validate minimum file size
    if size < MIN_FILE_SIZE:
        video_path.unlink(missing_ok=True)
        logger.warning(f"UPLOAD [{task_id[:8]}] Rejected: file too small ({size} bytes)")
        raise HTTPException(
            400,
            detail=api_error(
                FILE_TOO_SMALL,
                f"File too small ({size} bytes). Is this a valid media file?",
                request_id=get_request_id(),
            ),
        )

    # Validate magic bytes (actual file content, not just extension) — fast, sync
    if not validate_magic_bytes(video_path):
        client_ip = request.client.host if request.client else "unknown"
        log_audit_event(
            "suspicious_file", ip=client_ip, filename=safe_filename, size=size, reason="magic_bytes_mismatch"
        )
        quarantine_file(video_path, reason="magic_bytes_mismatch", ip=client_ip)
        logger.warning(f"UPLOAD [{task_id[:8]}] Rejected: magic bytes don't match a media file")
        raise HTTPException(
            400,
            detail=api_error(
                MAGIC_BYTES_MISMATCH,
                "File content does not match a recognized media format.",
                request_id=get_request_id(),
            ),
        )

    upload_time = time.time() - t0
    logger.info(f"UPLOAD [{task_id[:8]}] Saved: {format_bytes(size)} in {upload_time:.1f}s -> {video_path.name}")
    log_task_event(
        task_id,
        "upload",
        filename=safe_filename,
        size=size,
        upload_time_sec=round(upload_time, 2),
        model=model_size,
        device=device,
    )

    # Truncate initial_prompt to prevent unbounded input
    if len(initial_prompt) > 500:
        initial_prompt = initial_prompt[:500]

    # Validate max_line_chars range
    max_line_chars = max(20, min(80, max_line_chars))

    # Get session ID for task ownership
    session_id = getattr(request.state, "session_id", "")

    # Record analytics
    record_upload(language=language, model=model_size, device=device, file_size=size)
    inc("uploads_total")

    from datetime import datetime, timezone

    # Detect MIME type from file content — Forge (Sr. Backend Engineer), Sprint L53
    mime_type = detect_mime_type(video_path)
    from app.config import VIDEO_EXTENSIONS

    is_video = ext in VIDEO_EXTENSIONS

    # Capture client IP before returning (request object won't be available in background)
    client_ip = request.client.host if request.client else "unknown"

    state.tasks[task_id] = {
        "status": "queued",
        "percent": 0,
        "message": "Upload complete. Preparing for processing...",
        "filename": safe_filename,
        "language_requested": language,
        "session_id": session_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "file_size": size,
        "file_extension": ext,
        "mime_type": mime_type,
        "is_video": is_video,
    }

    # Persist new task to DB
    from app.services.task_backend import get_task_backend

    backend = get_task_backend()
    backend.set(task_id, state.tasks[task_id])
    try:
        from app.db.task_backend_db import DatabaseTaskBackend

        if isinstance(backend, DatabaseTaskBackend):
            backend.schedule_persist(task_id, state.tasks[task_id])
    except ImportError:
        logger.debug("DatabaseTaskBackend not available, skipping DB persist")

    # Build translate option
    extra_transcribe_opts = {}
    if translate_to and translate_to in SUPPORTED_LANGUAGES and translate_to != "auto":
        if translate_to == "en":
            # Use Whisper's built-in translate for English target (higher quality)
            translate_to_english = True
            translate_to = ""
    elif translate_to_english:
        extra_transcribe_opts["translate_to_english"] = True

    # Validate auto_embed option
    if auto_embed and auto_embed not in ("soft", "hard"):
        auto_embed = ""

    # Dispatch: Celery (multi-server) or local thread (standalone)
    from app.config import ROLE, STORAGE_BACKEND

    if ROLE == "web":
        # Multi-server: upload to S3 if configured, then dispatch via Celery
        if STORAGE_BACKEND == "s3":
            from app.services.storage import get_storage

            storage = get_storage()
            storage.save_upload_from_path(video_path.name, video_path)

        from app.tasks import transcribe_task

        transcribe_task.delay(
            task_id,
            video_path.name,
            model_size,
            device,
            language,
            word_timestamps=word_timestamps,
            initial_prompt=initial_prompt,
            diarize=diarize,
            num_speakers=num_speakers,
            max_line_chars=max_line_chars,
            translate_to_english=translate_to_english,
            auto_embed=auto_embed,
            translate_to=translate_to,
        )
    else:
        # Standalone: prepare (probe + scan) then process in dedicated pipeline thread pool
        # Audio probing and ClamAV scanning are deferred to background to return task_id faster
        loop = asyncio.get_event_loop()
        if state.pipeline_executor is not None:
            loop.run_in_executor(
                state.pipeline_executor,
                lambda: _prepare_and_process(
                    task_id,
                    video_path,
                    safe_filename,
                    client_ip,
                    size,
                    model_size,
                    device,
                    language,
                    word_timestamps=word_timestamps,
                    initial_prompt=initial_prompt,
                    diarize=diarize,
                    num_speakers=num_speakers,
                    max_line_chars=max_line_chars,
                    translate_to_english=translate_to_english,
                    auto_embed=auto_embed,
                    translate_to=translate_to,
                ),
            )
        else:
            # Fallback if executor not initialized (e.g., during tests)
            asyncio.create_task(
                asyncio.to_thread(
                    _prepare_and_process,
                    task_id,
                    video_path,
                    safe_filename,
                    client_ip,
                    size,
                    model_size,
                    device,
                    language,
                    word_timestamps=word_timestamps,
                    initial_prompt=initial_prompt,
                    diarize=diarize,
                    num_speakers=num_speakers,
                    max_line_chars=max_line_chars,
                    translate_to_english=translate_to_english,
                    auto_embed=auto_embed,
                    translate_to=translate_to,
                )
            )

    return {
        "task_id": task_id,
        "model_size": model_size,
        "language": language,
        "word_timestamps": word_timestamps,
        "diarize": diarize,
    }
