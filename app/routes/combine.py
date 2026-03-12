"""Combine routes - merge user-provided video and subtitle files."""

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse

from app import state
from app.config import (
    UPLOAD_DIR, OUTPUT_DIR, MAX_FILE_SIZE, MIN_FILE_SIZE,
    ALLOWED_SUBTITLE_EXTENSIONS, MAX_SUBTITLE_SIZE,
)
from app.logging_setup import log_task_event
from app.services.subtitle_embed import (
    soft_embed_subtitles, hard_burn_subtitles,
    SubtitleStyle, STYLE_PRESETS,
)
from app.services.sse import create_event_queue, emit_event
from app.utils.security import validate_file_extension, validate_magic_bytes

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["Combine"])

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".webm", ".mov"}


def _validate_subtitle_file(path: Path) -> bool:
    """Validate that a file looks like a valid SRT or VTT subtitle file."""
    try:
        # Read first 1KB to check structure
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            head = f.read(1024)
        head_stripped = head.strip()
        if not head_stripped:
            return False
        # VTT: must start with WEBVTT
        if path.suffix.lower() == ".vtt":
            return head_stripped.startswith("WEBVTT")
        # SRT: must contain --> timestamp markers
        if path.suffix.lower() == ".srt":
            return "-->" in head
        return False
    except Exception:
        return False


def _build_style(
    preset: str,
    font_name: Optional[str],
    font_size: Optional[int],
    font_color: Optional[str],
    bold: Optional[bool],
    position: Optional[str],
    background_opacity: Optional[float],
) -> SubtitleStyle:
    """Build SubtitleStyle from preset + custom overrides."""
    style = SubtitleStyle()
    if preset in STYLE_PRESETS:
        style = STYLE_PRESETS[preset]
        style = SubtitleStyle(**{k: getattr(style, k) for k in style.__dataclass_fields__})

    if font_name is not None:
        style.font_name = font_name
    if font_size is not None:
        style.font_size = max(8, min(72, font_size))
    if font_color is not None:
        c = font_color.strip()
        if c.startswith("#") and len(c) == 7:
            r, g, b = c[1:3], c[3:5], c[5:7]
            style.font_color = f"&H{b}{g}{r}"
        else:
            style.font_color = c
    if bold is not None:
        style.bold = bold
    if position is not None and position in ("top", "center", "bottom"):
        style.position = position
    if background_opacity is not None:
        style.background_opacity = max(0, min(1, background_opacity))

    return style


@router.post("/combine")
async def combine_video_subtitle(
    video: UploadFile,
    subtitle: UploadFile,
    mode: Literal["soft", "hard"] = Form("soft"),
    preset: str = Form("default"),
    font_name: Optional[str] = Form(None),
    font_size: Optional[int] = Form(None),
    font_color: Optional[str] = Form(None),
    bold: Optional[bool] = Form(None),
    position: Optional[str] = Form(None),
    background_opacity: Optional[float] = Form(None),
    language: str = Form("eng"),
):
    """Combine a video file with a subtitle file (SRT/VTT).

    Upload both files, choose soft mux or hard burn mode.
    No transcription needed - bring your own subtitles.
    """
    from app.config import FFMPEG_AVAILABLE
    if not FFMPEG_AVAILABLE:
        raise HTTPException(503, "FFmpeg is not installed. The combine feature is unavailable.")

    # Validate video file extension
    video_ext = validate_file_extension(video.filename or "")
    if video_ext is None or video_ext not in VIDEO_EXTENSIONS:
        raise HTTPException(400, "Please upload a video file (MP4, MKV, AVI, WebM, MOV)")

    # Validate subtitle file extension
    sub_filename = subtitle.filename or ""
    sub_ext = Path(sub_filename).suffix.lower()
    if sub_ext not in ALLOWED_SUBTITLE_EXTENSIONS:
        raise HTTPException(400, "Please upload a subtitle file (SRT or VTT)")

    # Check concurrent task limit
    active = sum(1 for t in state.tasks.values() if t.get("status") in ("combining", "transcribing", "extracting"))
    from app.config import MAX_CONCURRENT_TASKS
    if active >= MAX_CONCURRENT_TASKS:
        raise HTTPException(429, "Too many active tasks. Please wait for current tasks to finish.")

    task_id = str(uuid.uuid4())

    # Save video file with size validation
    video_path = UPLOAD_DIR / f"combine_{task_id}_video{video_ext}"
    video_size = 0
    with open(video_path, "wb") as f:
        while chunk := await video.read(1024 * 1024):
            if state.system_critical:
                video_path.unlink(missing_ok=True)
                raise HTTPException(503, "Upload aborted — system in critical state.")
            video_size += len(chunk)
            if video_size > MAX_FILE_SIZE:
                video_path.unlink(missing_ok=True)
                raise HTTPException(413, "Video file too large (max 2 GB)")
            f.write(chunk)

    if video_size < MIN_FILE_SIZE:
        video_path.unlink(missing_ok=True)
        raise HTTPException(400, "Video file too small")

    if not validate_magic_bytes(video_path):
        video_path.unlink(missing_ok=True)
        raise HTTPException(400, "File content does not match a video format")

    # Save subtitle file with size validation
    sub_path = UPLOAD_DIR / f"combine_{task_id}_sub{sub_ext}"
    sub_size = 0
    with open(sub_path, "wb") as f:
        while chunk := await subtitle.read(1024 * 1024):
            sub_size += len(chunk)
            if sub_size > MAX_SUBTITLE_SIZE:
                sub_path.unlink(missing_ok=True)
                video_path.unlink(missing_ok=True)
                raise HTTPException(413, "Subtitle file too large (max 10 MB)")
            f.write(chunk)

    if sub_size == 0:
        sub_path.unlink(missing_ok=True)
        video_path.unlink(missing_ok=True)
        raise HTTPException(400, "Subtitle file is empty")

    # Validate subtitle content
    if not _validate_subtitle_file(sub_path):
        sub_path.unlink(missing_ok=True)
        video_path.unlink(missing_ok=True)
        raise HTTPException(400, "Invalid subtitle file content. Expected valid SRT or VTT format.")

    # Build style
    style = _build_style(preset, font_name, font_size, font_color, bold, position, background_opacity)

    # Output path
    out_ext = ".mkv" if mode == "soft" and video_ext == ".mkv" else ".mp4"
    output_path = OUTPUT_DIR / f"combine_{task_id}{out_ext}"

    # Initialize task state
    from datetime import datetime, timezone
    state.tasks[task_id] = {
        "status": "combining",
        "percent": 0,
        "message": "Starting combine...",
        "filename": video.filename or "video",
        "mode": mode,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # Create SSE event queue
    create_event_queue(task_id)

    log_task_event(task_id, "combine_started", mode=mode, video=video.filename, subtitle=subtitle.filename)

    def do_combine():
        try:
            if state.system_critical:
                raise RuntimeError("System in critical state — combine aborted")

            emit_event(task_id, "combine_progress", {
                "message": f"Combining video and subtitles ({mode} mode)...",
                "percent": 50,
            })
            state.tasks[task_id]["percent"] = 50
            state.tasks[task_id]["message"] = f"Combining ({mode} mode)..."

            if mode == "soft":
                soft_embed_subtitles(video_path, sub_path, output_path, task_id, language=language)
            else:
                hard_burn_subtitles(video_path, sub_path, output_path, style, task_id)

            state.tasks[task_id]["status"] = "done"
            state.tasks[task_id]["percent"] = 100
            state.tasks[task_id]["message"] = "Combine complete!"
            state.tasks[task_id]["combined_video"] = str(output_path.name)
            log_task_event(task_id, "combine_complete", mode=mode, output=output_path.name)

            emit_event(task_id, "combine_done", {
                "message": f"Video and subtitles combined ({mode} mode)!",
                "download_url": f"/combine/download/{task_id}",
                "output": output_path.name,
                "mode": mode,
            })
        except Exception as e:
            logger.error(f"COMBINE [{task_id[:8]}] Failed: {e}")
            state.tasks[task_id]["status"] = "error"
            state.tasks[task_id]["message"] = str(e)
            log_task_event(task_id, "combine_error", error=str(e))
            emit_event(task_id, "combine_error", {"message": f"Combine failed: {e}"})
        finally:
            video_path.unlink(missing_ok=True)
            sub_path.unlink(missing_ok=True)

    asyncio.create_task(asyncio.to_thread(do_combine))

    return {
        "task_id": task_id,
        "message": f"Combine started ({mode} mode)",
        "mode": mode,
        "output": output_path.name,
    }


@router.get("/combine/download/{task_id}")
async def download_combined(task_id: str):
    """Download the combined video file."""
    if task_id not in state.tasks:
        raise HTTPException(404, "Task not found")

    combined = state.tasks[task_id].get("combined_video")
    if not combined:
        raise HTTPException(404, "No combined video found. Run /combine first.")

    path = OUTPUT_DIR / combined
    if not path.exists():
        raise HTTPException(404, "Combined video file not found")

    # Security: ensure path is within OUTPUT_DIR
    if not str(path.resolve()).startswith(str(OUTPUT_DIR.resolve())):
        raise HTTPException(403, "Access denied")

    original_stem = Path(state.tasks[task_id]["filename"]).stem
    out_name = f"{original_stem}_combined{path.suffix}"
    media_type = "video/x-matroska" if path.suffix.lower() == ".mkv" else "video/mp4"
    return FileResponse(path, filename=out_name, media_type=media_type)


@router.get("/combine/status/{task_id}")
async def combine_status(task_id: str):
    """Get the status of a combine task (polling fallback)."""
    if task_id not in state.tasks:
        raise HTTPException(404, "Task not found")

    task = state.tasks[task_id]
    return {
        "task_id": task_id,
        "status": task.get("status"),
        "percent": task.get("percent", 0),
        "message": task.get("message", ""),
        "mode": task.get("mode"),
        "combined_video": task.get("combined_video"),
    }
