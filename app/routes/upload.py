"""Upload route with security validation."""

import asyncio
import logging
import uuid
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
    DURATION_EXCEEDED,
    FFMPEG_UNAVAILABLE,
    FILE_TOO_LARGE,
    FILE_TOO_SMALL,
    MAGIC_BYTES_MISMATCH,
    NO_AUDIO_STREAM,
    SYSTEM_CRITICAL,
    TASK_LIMIT_REACHED,
    UNSUPPORTED_FORMAT,
    VIRUS_DETECTED,
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
from app.services.sse import create_event_queue
from app.utils.formatting import format_bytes
from app.utils.security import detect_mime_type, sanitize_filename, validate_file_extension, validate_magic_bytes

logger = logging.getLogger("subtitle-generator")

router = APIRouter(tags=["Upload"])


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
                        FILE_TOO_LARGE, "File too large. Maximum size is 2 GB.", request_id=get_request_id()
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

    # Validate magic bytes (actual file content, not just extension)
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

    # Validate audio stream presence (reject video-only or corrupt files early)
    from app.config import FFPROBE_AVAILABLE, MAX_AUDIO_DURATION

    if FFPROBE_AVAILABLE:
        from app.utils.media import get_audio_duration, has_audio_stream

        if not has_audio_stream(video_path):
            video_path.unlink(missing_ok=True)
            logger.warning(f"UPLOAD [{task_id[:8]}] Rejected: no audio stream in '{safe_filename}'")
            raise HTTPException(
                400,
                detail=api_error(
                    NO_AUDIO_STREAM,
                    "This file has no audio track. Please upload a file with audio.",
                    request_id=get_request_id(),
                ),
            )

        # Validate duration limit
        duration = get_audio_duration(video_path)
        if duration > MAX_AUDIO_DURATION:
            video_path.unlink(missing_ok=True)
            logger.warning(
                f"UPLOAD [{task_id[:8]}] Rejected: duration {duration:.0f}s exceeds "
                f"{MAX_AUDIO_DURATION}s limit for '{safe_filename}'"
            )
            raise HTTPException(
                400,
                detail=api_error(
                    DURATION_EXCEEDED,
                    "File duration exceeds the 4-hour limit. Please upload a shorter file.",
                    request_id=get_request_id(),
                ),
            )

    # ClamAV virus scan (optional — graceful if ClamAV is not installed/running)
    client_ip = request.client.host if request.client else "unknown"
    av_result = scan_with_clamav(str(video_path))
    if not av_result["clean"]:
        log_audit_event(
            "virus_detected", ip=client_ip, filename=safe_filename, size=size, threat=av_result.get("threat")
        )
        quarantine_file(video_path, reason="virus_detected", ip=client_ip, threat=av_result.get("threat"))
        logger.warning(f"UPLOAD [{task_id[:8]}] Rejected: ClamAV detected threat '{av_result.get('threat')}'")
        raise HTTPException(
            400,
            detail=api_error(VIRUS_DETECTED, "File rejected: virus or malware detected.", request_id=get_request_id()),
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

    state.tasks[task_id] = {
        "status": "queued",
        "percent": 0,
        "message": "Upload complete. Starting processing...",
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
        # Standalone: process locally in background thread
        asyncio.create_task(
            asyncio.to_thread(
                process_video,
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
        )

    return {
        "task_id": task_id,
        "model_size": model_size,
        "language": language,
        "word_timestamps": word_timestamps,
        "diarize": diarize,
    }
