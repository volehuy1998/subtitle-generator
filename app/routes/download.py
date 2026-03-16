"""Download route for subtitle files (SRT and VTT).

Supports local filesystem and S3 storage backends.
Also provides subtitle preview and bulk ZIP download.
"""

import json
import logging
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse

from app import state
from app.config import OUTPUT_DIR, STORAGE_BACKEND
from app.logging_setup import log_task_event
from app.utils.access import check_task_access
from app.utils.validation import safe_path

logger = logging.getLogger("subtitle-generator")
router = APIRouter(tags=["Download"])


def _get_task_data(task_id: str) -> dict | None:
    """Get task data from local state or backend."""
    if task_id in state.tasks:
        return state.tasks[task_id]
    from app.config import REDIS_URL

    if REDIS_URL:
        try:
            from app.services.task_backend import get_task_backend

            return get_task_backend().get(task_id)
        except Exception:
            pass
    return None


@router.get("/search/{task_id}")
async def search_subtitles(
    task_id: str, request: Request, q: str = Query(..., min_length=1), limit: int = Query(20, ge=1, le=200)
):
    """Search within a transcription's segments for matching text."""
    task_data = _get_task_data(task_id)
    if task_data is None:
        raise HTTPException(404, "Task not found")
    check_task_access(task_data, request)
    if task_data.get("status") != "done":
        raise HTTPException(400, "Task not yet complete")

    json_path = safe_path(OUTPUT_DIR / f"{task_id}.json", allowed_dir=OUTPUT_DIR)
    if not json_path.exists():
        raise HTTPException(404, "Output file not found")

    with open(json_path, "r", encoding="utf-8") as f:
        segments = json.load(f)

    query_lower = q.lower()
    matches = [s for s in segments if query_lower in s.get("text", "").lower()]

    logger.info(f"SEARCH [{task_id[:8]}] query={q!r} found {len(matches)} match(es)")
    log_task_event(task_id, "searched", query=q, total_matches=len(matches), limit=limit)
    return {
        "task_id": task_id,
        "query": q,
        "total_matches": len(matches),
        "matches": matches[:limit],
    }


@router.get("/download/{task_id}")
async def download(
    task_id: str,
    request: Request,
    format: Literal["srt", "vtt", "json"] = Query("srt"),
    max_line_chars: int = Query(42, ge=20, le=120),
):
    """Download subtitles with optional custom line length.

    When max_line_chars differs from the default (42), SRT and VTT files are
    regenerated on-the-fly from the stored JSON segments with the requested
    line-breaking width. JSON downloads are unaffected by this parameter.
    """
    task_data = _get_task_data(task_id)
    if task_data is None:
        raise HTTPException(404, "Task not found")
    check_task_access(task_data, request)
    if task_data.get("status") != "done":
        raise HTTPException(400, "Subtitles not ready yet")

    original_name = Path(task_data["filename"]).stem + f".{format}"
    media_types = {"srt": "text/plain", "vtt": "text/vtt", "json": "application/json"}
    media_type = media_types.get(format, "text/plain")

    # Sprint L45: On-the-fly regeneration with custom line length — Forge (Sr. Backend Engineer)
    if max_line_chars != 42 and format in ("srt", "vtt"):
        json_path = safe_path(OUTPUT_DIR / f"{task_id}.json", allowed_dir=OUTPUT_DIR)
        if not json_path.exists():
            raise HTTPException(404, "JSON segments file not found for regeneration")

        segments = json.load(open(json_path, "r", encoding="utf-8"))
        from app.utils.srt import segments_to_srt, segments_to_vtt
        from app.utils.subtitle_format import format_segments_with_linebreaks

        formatted = format_segments_with_linebreaks(segments, max_chars=max_line_chars)
        has_speakers = any(s.get("speaker") for s in formatted)
        if format == "srt":
            content = segments_to_srt(formatted, include_speakers=has_speakers)
        else:
            content = segments_to_vtt(formatted, include_speakers=has_speakers)

        logger.info(f"DOWNLOAD [{task_id[:8]}] Regenerated {original_name} with max_line_chars={max_line_chars}")
        log_task_event(task_id, "downloaded", filename=original_name, format=format, max_line_chars=max_line_chars)
        return StreamingResponse(
            iter([content.encode("utf-8")]),
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{original_name}"'},
        )

    # Default: serve pre-generated file
    filename = f"{task_id}.{format}"

    if STORAGE_BACKEND == "s3":
        from app.services.storage import get_storage

        storage = get_storage()
        local_path = storage.get_output_path(filename)
        if local_path is None:
            raise HTTPException(404, f"{format.upper()} file not found")
        sub_path = safe_path(local_path, allowed_dir=OUTPUT_DIR)
    else:
        sub_path = safe_path(OUTPUT_DIR / filename, allowed_dir=OUTPUT_DIR)
        if not sub_path.exists():
            raise HTTPException(404, f"{format.upper()} file not found")

    logger.info(f"DOWNLOAD [{task_id[:8]}] Serving {original_name}")
    log_task_event(task_id, "downloaded", filename=original_name, format=format)
    return FileResponse(
        sub_path,
        filename=original_name,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{original_name}"'},
    )


@router.get("/preview/{task_id}")
async def preview_subtitles(task_id: str, request: Request, limit: int = Query(10, ge=1, le=100)):
    """Preview first N segments of a completed transcription."""
    task_data = _get_task_data(task_id)
    if task_data is None:
        raise HTTPException(404, "Task not found")
    check_task_access(task_data, request)
    if task_data.get("status") != "done":
        raise HTTPException(400, "Task not yet complete")

    json_path = safe_path(OUTPUT_DIR / f"{task_id}.json", allowed_dir=OUTPUT_DIR)
    if not json_path.exists():
        raise HTTPException(404, "Output file not found")

    with open(json_path, "r", encoding="utf-8") as f:
        segments = json.load(f)

    logger.info(f"PREVIEW [{task_id[:8]}] Serving {limit} of {len(segments)} segments")
    log_task_event(task_id, "previewed", limit=limit, total_segments=len(segments))
    return {
        "task_id": task_id,
        "total_segments": len(segments),
        "preview_limit": limit,
        "segments": segments[:limit],
    }


@router.get("/download/{task_id}/all")
async def download_all_formats(task_id: str, request: Request):
    """Download all available subtitle formats (SRT, VTT, JSON) as a ZIP archive."""
    task_data = _get_task_data(task_id)
    if task_data is None:
        raise HTTPException(404, "Task not found")
    check_task_access(task_data, request)
    if task_data.get("status") != "done":
        raise HTTPException(400, "Task not yet complete")

    original_name = task_data.get("filename", task_id)
    stem = Path(original_name).stem

    buf = BytesIO()
    files_added = 0
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for ext in ("srt", "vtt", "json"):
            path = safe_path(OUTPUT_DIR / f"{task_id}.{ext}", allowed_dir=OUTPUT_DIR)
            if path.exists():
                zf.write(path, f"{stem}.{ext}")
                files_added += 1

    if files_added == 0:
        raise HTTPException(404, "No output files found")

    buf.seek(0)
    archive_name = f"{stem}_subtitles.zip"
    logger.info(f"DOWNLOAD [{task_id[:8]}] Serving ZIP with {files_added} format(s)")
    log_task_event(task_id, "downloaded_all", filename=archive_name, formats=files_added)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{archive_name}"'},
    )
