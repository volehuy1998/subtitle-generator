"""Subtitle embedding routes - embed subtitles into video files."""

import asyncio
import logging
import re
import uuid
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, Form, HTTPException, UploadFile

from app import state
from app.config import MAX_FILE_SIZE, MIN_FILE_SIZE, OUTPUT_DIR, UPLOAD_DIR
from app.logging_setup import log_task_event
from app.services.sse import emit_event
from app.services.subtitle_embed import (
    STYLE_PRESETS,
    SubtitleStyle,
    hard_burn_subtitles,
    soft_embed_subtitles,
)
from app.utils.security import validate_file_extension, validate_magic_bytes
from app.utils.validation import safe_path

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["Embedding"])

# Strip internal file paths from error messages before they reach users — Shield (Security Engineer)
_PATH_RE = re.compile(r"(/[a-zA-Z0-9_./-]+)+")


def _sanitize_embed_error(exc: Exception) -> str:
    """Remove internal paths from embed error messages."""
    return _PATH_RE.sub("<path>", str(exc))[:200]


@router.get("/embed/presets")
async def list_presets():
    """List available subtitle style presets."""
    result = {}
    for name, style in STYLE_PRESETS.items():
        result[name] = {
            "font_name": style.font_name,
            "font_size": style.font_size,
            "bold": style.bold,
            "position": style.position,
        }
    return {"presets": result}


@router.post("/embed/{task_id}")
async def embed_subtitles(
    task_id: str,
    video: UploadFile,
    mode: Literal["soft", "hard"] = Form("soft"),
    preset: str = Form("default"),
    font_name: Optional[str] = Form(None),
    font_size: Optional[int] = Form(None),
    font_color: Optional[str] = Form(None),
    bold: Optional[bool] = Form(None),
    position: Optional[str] = Form(None),
    background_opacity: Optional[float] = Form(None),
    translate_to: str = Form(""),
):
    """Embed subtitles into an uploaded video file.

    Supports soft (mux) and hard (burn) modes.
    For hard mode, customize styling via preset or individual params.
    """
    from app.config import FFMPEG_AVAILABLE

    if not FFMPEG_AVAILABLE:
        raise HTTPException(503, "FFmpeg is not installed. Subtitle embedding is unavailable.")

    # Note: critical state checks handled by CriticalStateMiddleware
    if task_id not in state.tasks:
        raise HTTPException(404, "Task not found")
    if state.tasks[task_id]["status"] != "done":
        raise HTTPException(400, "Subtitles not ready yet")

    # Validate video file
    ext = validate_file_extension(video.filename or "")
    if ext is None or ext not in (".mp4", ".mkv", ".avi", ".webm", ".mov"):
        raise HTTPException(400, "Please upload a video file (MP4, MKV, AVI, WebM, MOV)")

    # Determine subtitle file path
    srt_path = safe_path(OUTPUT_DIR / f"{task_id}.srt", allowed_dir=OUTPUT_DIR)
    if not srt_path.exists():
        raise HTTPException(404, "Subtitle file not found")

    # Save uploaded video
    embed_id = str(uuid.uuid4())[:12]
    video_path = safe_path(UPLOAD_DIR / f"embed_{embed_id}{ext}", allowed_dir=UPLOAD_DIR)

    size = 0
    with open(video_path, "wb") as f:
        while chunk := await video.read(1024 * 1024):
            # Abort upload if system enters critical state
            if state.system_critical:
                video_path.unlink(missing_ok=True)
                raise HTTPException(503, "Upload aborted — system in critical state.")
            size += len(chunk)
            if size > MAX_FILE_SIZE:
                video_path.unlink(missing_ok=True)
                raise HTTPException(413, "Video file too large (max 2 GB)")
            f.write(chunk)

    if size < MIN_FILE_SIZE:
        video_path.unlink(missing_ok=True)
        raise HTTPException(400, "Video file too small")

    if not validate_magic_bytes(video_path):
        video_path.unlink(missing_ok=True)
        raise HTTPException(400, "File content does not match a video format")

    # Build style
    style = SubtitleStyle()
    if preset in STYLE_PRESETS:
        style = STYLE_PRESETS[preset]
        # Copy to avoid mutating the preset
        style = SubtitleStyle(**{k: getattr(style, k) for k in style.__dataclass_fields__})

    # Override with custom params
    if font_name is not None:
        style.font_name = font_name
    if font_size is not None:
        style.font_size = max(8, min(72, font_size))
    if font_color is not None:
        # Convert HTML hex (#RRGGBB) to ASS format (&HBBGGRR) if needed
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

    # Output path
    out_ext = ".mkv" if mode == "soft" and ext == ".mkv" else ".mp4"
    output_path = safe_path(OUTPUT_DIR / f"embed_{task_id}_{embed_id}{out_ext}", allowed_dir=OUTPUT_DIR)

    # Run embedding in background
    _translate_to = translate_to

    def do_embed():
        try:
            # Check critical state before starting
            if state.system_critical:
                raise RuntimeError("System in critical state — embed aborted")

            effective_srt = srt_path
            # Translate subtitles if requested
            if _translate_to:
                from app.services.translation import translate_segments
                from app.utils.srt import parse_srt, segments_to_srt

                srt_content = srt_path.read_text(encoding="utf-8")
                segments = parse_srt(srt_content)
                source_lang = state.tasks[task_id].get("language", "en")
                translated = translate_segments(segments, source_lang, _translate_to, task_id)
                translated_srt = segments_to_srt(translated, include_speakers=False)
                translated_path = OUTPUT_DIR / f"{task_id}_translated.srt"
                translated_path.write_text(translated_srt, encoding="utf-8")
                effective_srt = translated_path

            if mode == "soft":
                soft_embed_subtitles(
                    video_path,
                    effective_srt,
                    output_path,
                    task_id,
                    language=state.tasks[task_id].get("language", "eng"),
                )
            else:
                hard_burn_subtitles(video_path, effective_srt, output_path, style, task_id)

            state.tasks[task_id]["embedded_video"] = str(output_path.name)
            log_task_event(task_id, "embed_complete", mode=mode, output=output_path.name)
        except Exception as e:
            logger.error(f"EMBED [{task_id[:8]}] Failed: {e}")
            log_task_event(task_id, "embed_error", error=str(e))
        finally:
            video_path.unlink(missing_ok=True)

    asyncio.create_task(asyncio.to_thread(do_embed))

    return {
        "message": f"Embedding started ({mode} mode)",
        "embed_id": embed_id,
        "output": output_path.name,
        "mode": mode,
    }


@router.post("/embed/{task_id}/quick")
async def quick_embed(
    task_id: str,
    mode: Literal["soft", "hard"] = Form("soft"),
    preset: str = Form("default"),
    font_name: Optional[str] = Form(None),
    font_size: Optional[int] = Form(None),
    font_color: Optional[str] = Form(None),
    bold: Optional[bool] = Form(None),
    position: Optional[str] = Form(None),
    background_opacity: Optional[float] = Form(None),
    translate_to: str = Form(""),
):
    """Embed subtitles using the preserved original video (no re-upload needed).

    After transcription of a video file, the original is preserved for deferred embed.
    This endpoint uses that preserved video, so the user doesn't need to re-upload.
    """
    from app.config import FFMPEG_AVAILABLE

    if not FFMPEG_AVAILABLE:
        raise HTTPException(503, "FFmpeg is not installed. Subtitle embedding is unavailable.")

    # Note: critical state checks handled by CriticalStateMiddleware
    if task_id not in state.tasks:
        raise HTTPException(404, "Task not found")

    task = state.tasks[task_id]
    if task["status"] != "done":
        raise HTTPException(400, "Subtitles not ready yet")

    if task.get("embed_in_progress"):
        raise HTTPException(409, "Embedding already in progress. Please wait for it to finish.")

    preserved = task.get("preserved_video")
    if not preserved:
        raise HTTPException(400, "No preserved video available. Use the full embed endpoint with file upload.")

    video_path = UPLOAD_DIR / preserved
    if not video_path.exists():
        raise HTTPException(
            404, "The original video has been cleaned up. Please re-upload the video to embed subtitles."
        )

    # Security check
    if not str(video_path.resolve()).startswith(str(UPLOAD_DIR.resolve())):
        raise HTTPException(403, "Access denied")

    srt_path = OUTPUT_DIR / f"{task_id}.srt"
    if not srt_path.exists():
        raise HTTPException(404, "Subtitle file not found")

    ext = video_path.suffix.lower()

    # Build style
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

    out_ext = ".mkv" if mode == "soft" and ext == ".mkv" else ".mp4"
    output_path = safe_path(OUTPUT_DIR / f"embed_{task_id}{out_ext}", allowed_dir=OUTPUT_DIR)

    task["embed_in_progress"] = True
    _translate_to = translate_to

    def do_embed():
        try:
            # Check critical state before starting
            if state.system_critical:
                raise RuntimeError("System in critical state — embed aborted")

            effective_srt = srt_path
            # Translate subtitles if requested
            if _translate_to:
                from app.services.translation import translate_segments
                from app.utils.srt import parse_srt, segments_to_srt

                srt_content = srt_path.read_text(encoding="utf-8")
                segments = parse_srt(srt_content)
                source_lang = task.get("language", "en")
                translated = translate_segments(segments, source_lang, _translate_to, task_id)
                translated_srt = segments_to_srt(translated, include_speakers=False)
                translated_path = OUTPUT_DIR / f"{task_id}_translated.srt"
                translated_path.write_text(translated_srt, encoding="utf-8")
                effective_srt = translated_path

            emit_event(task_id, "embed_progress", {"message": "Embedding subtitles...", "percent": 100})
            if mode == "soft":
                soft_embed_subtitles(
                    video_path, effective_srt, output_path, task_id, language=task.get("language", "eng")
                )
            else:
                hard_burn_subtitles(video_path, effective_srt, output_path, style, task_id)

            task["embedded_video"] = str(output_path.name)
            log_task_event(task_id, "quick_embed_complete", mode=mode, output=output_path.name)
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
        except Exception as e:
            logger.error("EMBED [%s] Quick embed failed: %s", task_id[:8], e)
            log_task_event(task_id, "embed_error", error=str(e))
            emit_event(task_id, "embed_error", {"message": f"Embedding failed: {_sanitize_embed_error(e)}"})
        finally:
            task.pop("embed_in_progress", None)

    asyncio.create_task(asyncio.to_thread(do_embed))

    return {
        "message": f"Quick embedding started ({mode} mode)",
        "output": output_path.name,
        "mode": mode,
    }


@router.get("/embed/download/{task_id}")
async def download_embedded(task_id: str):
    """Download the video with embedded subtitles."""
    if task_id not in state.tasks:
        raise HTTPException(404, "Task not found")

    embedded = state.tasks[task_id].get("embedded_video")
    if not embedded:
        raise HTTPException(404, "No embedded video found. Run /embed first.")

    path = OUTPUT_DIR / embedded
    if not path.exists():
        raise HTTPException(404, "Embedded video file not found")

    # Security check
    if not str(path.resolve()).startswith(str(OUTPUT_DIR.resolve())):
        raise HTTPException(403, "Access denied")

    from fastapi.responses import FileResponse

    original_stem = Path(state.tasks[task_id]["filename"]).stem
    out_name = f"{original_stem}_subtitled{path.suffix}"
    return FileResponse(path, filename=out_name, media_type="video/mp4")
